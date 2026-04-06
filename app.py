"""
BytePlus Image-to-Video Web UI

Simple Flask app with prompt input, image upload, and video results with download buttons.
"""

import os
import uuid
import time
import threading
import base64
import mimetypes
import concurrent.futures
import requests
from flask import Flask, render_template, request, jsonify, send_from_directory

API_URL = "https://ark.ap-southeast.bytepluses.com/api/v3/contents/generations/tasks"
API_KEY = "ba7d09d1-86eb-43d5-8109-f13be369ddb2"
MODEL = "seedance-1-5-pro-251215"
NUM_VIDEOS = 4

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}",
}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads")
app.config["VIDEO_FOLDER"] = os.path.join(os.path.dirname(__file__), "videos")

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["VIDEO_FOLDER"], exist_ok=True)

# In-memory job tracker: job_id -> {status, tasks, videos}
jobs = {}


def image_to_data_url(path):
    mime, _ = mimetypes.guess_type(path)
    if not mime:
        mime = "image/png"
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    return f"data:{mime};base64,{encoded}"


def create_task(prompt, image_url):
    payload = {
        "model": MODEL,
        "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image_url}},
        ],
        "resolution": "720p",
        "duration": 5,
        "generate_audio": False,
        "draft": False,
        "service_tier": "default",
    }
    resp = requests.post(API_URL, headers=HEADERS, json=payload)
    resp.raise_for_status()
    return resp.json()


def get_task(task_id):
    resp = requests.get(f"{API_URL}/{task_id}", headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def wait_and_download(task_id, output_path, poll_interval=10, timeout=600):
    start = time.time()
    while True:
        result = get_task(task_id)
        status = result.get("status", "")

        if status == "succeeded":
            content = result.get("content", [])
            video_url = None
            if isinstance(content, list):
                for item in content:
                    if item.get("type") == "video_url":
                        video_url = item.get("video_url", {}).get("url")
                        break
            if video_url:
                r = requests.get(video_url, stream=True)
                r.raise_for_status()
                with open(output_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                return "done"
            return "failed"

        if status in ("failed", "cancelled"):
            return "failed"

        if time.time() - start >= timeout:
            return "timeout"

        time.sleep(poll_interval)


def run_job(job_id, prompt, image_path):
    job = jobs[job_id]
    image_url = image_to_data_url(image_path)

    # Submit all tasks
    task_ids = []
    for i in range(NUM_VIDEOS):
        try:
            result = create_task(prompt, image_url)
            task_ids.append(result.get("id"))
            job["tasks"][i]["status"] = "processing"
            job["tasks"][i]["task_id"] = result.get("id")
        except Exception as e:
            job["tasks"][i]["status"] = "failed"
            job["tasks"][i]["error"] = str(e)

    # Wait and download in parallel
    def process_one(i, tid):
        if not tid:
            return
        filename = f"{job_id}_{i + 1}.mp4"
        output_path = os.path.join(app.config["VIDEO_FOLDER"], filename)
        result = wait_and_download(tid, output_path)
        if result == "done":
            job["tasks"][i]["status"] = "done"
            job["tasks"][i]["filename"] = filename
        else:
            job["tasks"][i]["status"] = "failed"

    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_VIDEOS) as pool:
        futures = []
        for i, tid in enumerate(task_ids):
            futures.append(pool.submit(process_one, i, tid))
        concurrent.futures.wait(futures)

    job["status"] = "done"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    prompt = request.form.get("prompt", "").strip()
    image = request.files.get("image")

    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
    if not image or image.filename == "":
        return jsonify({"error": "Image is required"}), 400

    job_id = str(uuid.uuid4())[:8]
    ext = os.path.splitext(image.filename)[1] or ".png"
    image_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{job_id}{ext}")
    image.save(image_path)

    jobs[job_id] = {
        "status": "running",
        "prompt": prompt,
        "tasks": [{"status": "queued"} for _ in range(NUM_VIDEOS)],
        "videos": [],
    }

    thread = threading.Thread(target=run_job, args=(job_id, prompt, image_path))
    thread.daemon = True
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/status/<job_id>")
def status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


@app.route("/videos/<filename>")
def serve_video(filename):
    return send_from_directory(app.config["VIDEO_FOLDER"], filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
