const http = require("http");
const https = require("https");
const fs = require("fs");
const path = require("path");
const { exec } = require("child_process");

const PORT = 3777;
const API_BASE = "https://api.muapi.ai/api/v1";
const HTML_FILE = path.join(__dirname, "seedance-standalone.html");

// Serve the HTML file and proxy API requests -- zero dependencies
const server = http.createServer((req, res) => {
  // CORS headers for all responses
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, x-api-key");

  if (req.method === "OPTIONS") {
    res.writeHead(204);
    res.end();
    return;
  }

  // Serve the HTML UI
  if (req.url === "/" || req.url === "/index.html") {
    fs.readFile(HTML_FILE, (err, data) => {
      if (err) {
        res.writeHead(500);
        res.end("Could not load seedance-standalone.html");
        return;
      }
      res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
      res.end(data);
    });
    return;
  }

  // Proxy API requests: /api/muapi/* -> https://api.muapi.ai/api/v1/*
  if (req.url.startsWith("/api/muapi/")) {
    const apiPath = req.url.replace("/api/muapi", "");
    let body = "";

    req.on("data", chunk => (body += chunk));
    req.on("end", () => {
      const url = new URL(API_BASE + apiPath);
      const options = {
        hostname: url.hostname,
        path: url.pathname + url.search,
        method: req.method,
        headers: {
          "Content-Type": "application/json",
        },
      };

      // Forward the API key from the request
      if (req.headers["x-api-key"]) {
        options.headers["x-api-key"] = req.headers["x-api-key"];
      }

      const ts = new Date().toLocaleTimeString();
      console.log(`[${ts}] ${req.method} ${apiPath}`);

      const proxyReq = https.request(options, proxyRes => {
        let data = "";
        proxyRes.on("data", chunk => (data += chunk));
        proxyRes.on("end", () => {
          console.log(`[${new Date().toLocaleTimeString()}] Response ${proxyRes.statusCode}: ${data.substring(0, 200)}`);
          res.writeHead(proxyRes.statusCode, { "Content-Type": "application/json" });
          res.end(data);
        });
      });

      proxyReq.on("error", err => {
        console.error(`[${new Date().toLocaleTimeString()}] Proxy error: ${err.message}`);
        res.writeHead(502);
        res.end(JSON.stringify({ error: "Proxy error: " + err.message }));
      });

      if (body) proxyReq.write(body);
      proxyReq.end();
    });
    return;
  }

  // 404 for everything else
  res.writeHead(404);
  res.end("Not found");
});

server.listen(PORT, () => {
  console.log(`\n  Seedance Video AI running at http://localhost:${PORT}\n`);
  console.log(`  Opening browser...\n`);

  // Open browser automatically
  const url = `http://localhost:${PORT}`;
  const platform = process.platform;
  if (platform === "win32") exec(`start ${url}`);
  else if (platform === "darwin") exec(`open ${url}`);
  else exec(`xdg-open ${url}`);
});
