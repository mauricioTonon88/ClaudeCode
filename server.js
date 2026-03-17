const express = require("express");
const multer = require("multer");
const fs = require("fs");
const path = require("path");
const https = require("https");

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

    const result = await apiRequest("POST", endpoint, payload);
    res.json(result.data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/extend - Extend a previously generated video
app.post("/api/extend", async (req, res) => {
  try {
    const { request_id, prompt, duration, quality } = req.body;
    const result = await apiRequest("POST", "/seedance-v2.0-extend", {
      request_id,
      prompt: prompt || "",
      duration: duration || 5,
      quality: quality || "basic",
    });
    res.json(result.data);
  } catch (err) {
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
    res.json(result.data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/upload - Upload a reference image (returns a served URL)
app.post("/api/upload", upload.single("image"), (req, res) => {
  if (!req.file) return res.status(400).json({ error: "No file uploaded" });
  const fileUrl = `/uploads/${req.file.filename}`;
  res.json({ url: fileUrl });
});

app.listen(PORT, () => {
  console.log(`Seedance Video AI UI running at http://localhost:${PORT}`);
});
