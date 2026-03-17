const express = require("express");
const multer = require("multer");
const fs = require("fs");
const path = require("path");
const https = require("https");
const http = require("http");

// Load .env manually (no dotenv dependency)
try {
  const envFile = fs.readFileSync(path.join(__dirname, ".env"), "utf8");
  for (const line of envFile.split("\n")) {
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith("#")) {
      const idx = trimmed.indexOf("=");
      if (idx > 0) {
        const key = trimmed.slice(0, idx).trim();
        const val = trimmed.slice(idx + 1).trim();
        if (!process.env[key]) process.env[key] = val;
      }
    }
  }
} catch {}

const app = express();
const PORT = process.env.PORT || 3000;
const API_KEY = process.env.MUAPI_API_KEY;
const API_BASE = "https://api.muapi.ai/api/v1";

app.use(express.json({ limit: "50mb" }));
app.use(express.static(path.join(__dirname, "public")));

// Upload directory for reference images
const uploadDir = path.join(__dirname, "uploads");
if (!fs.existsSync(uploadDir)) fs.mkdirSync(uploadDir);

const upload = multer({
  storage: multer.diskStorage({
    destination: uploadDir,
    filename: (req, file, cb) =>
      cb(null, Date.now() + "-" + file.originalname),
  }),
  limits: { fileSize: 20 * 1024 * 1024 },
  fileFilter: (req, file, cb) => {
    const allowed = /\.(jpg|jpeg|png|gif|webp)$/i;
    cb(null, allowed.test(file.originalname));
  },
});

// Serve uploaded files
app.use("/uploads", express.static(uploadDir));

// Helper: make HTTPS request to muapi
function apiRequest(method, urlPath, body) {
  return new Promise((resolve, reject) => {
    const url = new URL(API_BASE + urlPath);
    const options = {
      hostname: url.hostname,
      path: url.pathname + url.search,
      method,
      headers: {
        "x-api-key": API_KEY,
        "Content-Type": "application/json",
      },
    };

    const req = https.request(options, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => {
        try {
          resolve({ status: res.statusCode, data: JSON.parse(data) });
        } catch {
          resolve({ status: res.statusCode, data: { raw: data } });
        }
      });
    });

    req.on("error", reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

// POST /api/generate - Submit a video generation job
app.post("/api/generate", async (req, res) => {
  try {
    const { mode, prompt, images_list, aspect_ratio, duration, quality } =
      req.body;

    let endpoint;
    let payload = {};

    if (mode === "i2v") {
      endpoint = "/seedance-v2.0-i2v";
      payload = {
        prompt: prompt || "",
        images_list: images_list || [],
        aspect_ratio: aspect_ratio || "16:9",
        duration: duration || 5,
        quality: quality || "basic",
      };
    } else {
      endpoint = "/seedance-v2.0-t2v";
      payload = {
        prompt,
        aspect_ratio: aspect_ratio || "16:9",
        duration: duration || 5,
        quality: quality || "basic",
      };
    }

    console.log(`[GENERATE] Mode: ${mode}, Endpoint: ${endpoint}`);
    console.log(`[GENERATE] Payload:`, JSON.stringify(payload, null, 2));

    const result = await apiRequest("POST", endpoint, payload);

    console.log(`[GENERATE] Response status: ${result.status}`);
    console.log(`[GENERATE] Response:`, JSON.stringify(result.data, null, 2));

    res.json(result.data);
  } catch (err) {
    console.error(`[GENERATE] ERROR:`, err.message);
    res.status(500).json({ error: err.message });
  }
});

// POST /api/extend - Extend a previously generated video
app.post("/api/extend", async (req, res) => {
  try {
    const { request_id, prompt, duration, quality } = req.body;
    console.log(`[EXTEND] Request ID: ${request_id}`);
    const result = await apiRequest("POST", "/seedance-v2.0-extend", {
      request_id,
      prompt: prompt || "",
      duration: duration || 5,
      quality: quality || "basic",
    });
    console.log(`[EXTEND] Response status: ${result.status}`);
    console.log(`[EXTEND] Response:`, JSON.stringify(result.data, null, 2));
    res.json(result.data);
  } catch (err) {
    console.error(`[EXTEND] ERROR:`, err.message);
    res.status(500).json({ error: err.message });
  }
});

// GET /api/result/:id - Poll for result
app.get("/api/result/:id", async (req, res) => {
  try {
    const result = await apiRequest(
      "GET",
      `/predictions/${req.params.id}/result`
    );
    console.log(`[POLL] ID: ${req.params.id} — Status: ${result.status} — Result:`, JSON.stringify(result.data).slice(0, 200));
    res.json(result.data);
  } catch (err) {
    console.error(`[POLL] ERROR:`, err.message);
    res.status(500).json({ error: err.message });
  }
});

// Helper: upload a file to litterbox.catbox.moe (temporary public hosting, 1h)
function uploadToCatbox(filePath) {
  return new Promise((resolve, reject) => {
    const boundary = "----CatboxBoundary" + Date.now();
    const fileName = path.basename(filePath);
    const fileData = fs.readFileSync(filePath);

    const prefix = Buffer.from(
      `--${boundary}\r\nContent-Disposition: form-data; name="reqtype"\r\n\r\nfileupload\r\n` +
      `--${boundary}\r\nContent-Disposition: form-data; name="time"\r\n\r\n1h\r\n` +
      `--${boundary}\r\nContent-Disposition: form-data; name="fileToUpload"; filename="${fileName}"\r\n` +
      `Content-Type: application/octet-stream\r\n\r\n`
    );
    const suffix = Buffer.from(`\r\n--${boundary}--\r\n`);
    const body = Buffer.concat([prefix, fileData, suffix]);

    const options = {
      hostname: "litterbox.catbox.moe",
      path: "/resources/internals/api.php",
      method: "POST",
      headers: {
        "Content-Type": `multipart/form-data; boundary=${boundary}`,
        "Content-Length": body.length,
      },
    };

    const req = https.request(options, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => {
        const url = data.trim();
        if (url.startsWith("http")) {
          resolve(url);
        } else {
          reject(new Error("Catbox upload failed: " + data));
        }
      });
    });
    req.on("error", reject);
    req.write(body);
    req.end();
  });
}

// POST /api/upload - Upload a reference image, then host it publicly
app.post("/api/upload", upload.single("image"), async (req, res) => {
  if (!req.file) {
    console.log(`[UPLOAD] No file received`);
    return res.status(400).json({ error: "No file uploaded" });
  }
  console.log(`[UPLOAD] File saved: ${req.file.filename} (${(req.file.size / 1024).toFixed(1)} KB)`);

  try {
    console.log(`[UPLOAD] Uploading to catbox.moe for public URL...`);
    const publicUrl = await uploadToCatbox(req.file.path);
    console.log(`[UPLOAD] Public URL: ${publicUrl}`);
    res.json({ url: `/uploads/${req.file.filename}`, publicUrl });
  } catch (err) {
    console.error(`[UPLOAD] Catbox upload failed:`, err.message);
    res.status(500).json({ error: "Failed to create public URL: " + err.message });
  }
});

app.listen(PORT, () => {
  console.log(`Seedance Video AI UI running at http://localhost:${PORT}`);
});
