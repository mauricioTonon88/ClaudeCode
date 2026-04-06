"""
BytePlus Image-to-Video Wrapper

Generates 4 videos from an image + text prompt.
Fixed settings: 720p, 5 seconds, no sound, no draft, online generation.

Usage:
    python byteplus_video.py "A drone flies through the scene" https://example.com/photo.png
    python byteplus_video.py "Gentle camera zoom" /path/to/local/image.png -o my_video
"""

import os
import sys
import time
import base64
import mimetypes
import argparse
import concurrent.futures
import requests


API_URL = "https://ark.ap-southeast.bytepluses.com/api/v3/contents/generations/tasks"
API_KEY = "ba7d09d1-86eb-43d5-8109-f13be369ddb2"
MODEL = "seedance-1-5-pro-251215"
NUM_VIDEOS = 4

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}",
}


def image_to_data_url(path):
    """Convert a local image file to a base64 data URL."""
    mime, _ = mimetypes.guess_type(path)
    if not mime:
        mime = "image/png"
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    return f"data:{mime};base64,{encoded}"


def create_task(prompt, image_url):
    """Submit one image-to-video generation task."""
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
    """Query the status of a task."""
    resp = requests.get(f"{API_URL}/{task_id}", headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def wait_for_task(task_id, label, poll_interval=10, timeout=600):
    """Poll a task until done. Returns the completed task dict."""
    start = time.time()
    while True:
        result = get_task(task_id)
        status = result.get("status", "")

        if status == "succeeded":
            print(f"  [{label}] Done!")
            return result
        if status in ("failed", "cancelled"):
            msg = result.get("error", {}).get("message", "Unknown error")
            print(f"  [{label}] {status}: {msg}")
            return None

        elapsed = int(time.time() - start)
        if elapsed >= timeout:
            print(f"  [{label}] Timed out after {timeout}s")
            return None

        print(f"  [{label}] {status} ({elapsed}s)")
        time.sleep(poll_interval)


def download_video(task_result, output_path):
    """Download the video from a completed task result."""
    content = task_result.get("content", [])
    video_url = None
    if isinstance(content, list):
        for item in content:
            if item.get("type") == "video_url":
                video_url = item.get("video_url", {}).get("url")
                break
    if not video_url:
        print(f"  Warning: no video URL found in result")
        return None

    resp = requests.get(video_url, stream=True)
    resp.raise_for_status()
    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    return output_path


def generate(prompt, image_source, output_prefix="output"):
    """Generate 4 videos from an image + prompt.

    Args:
        prompt: Text description of the desired video motion/action.
        image_source: URL or local file path to the source image.
        output_prefix: Prefix for output files (produces prefix_1.mp4 ... prefix_4.mp4).
    """
    # Resolve image URL
    if os.path.isfile(image_source):
        print(f"Converting local image to data URL: {image_source}")
        image_url = image_to_data_url(image_source)
    else:
        image_url = image_source

    # Submit 4 tasks
    print(f"Submitting {NUM_VIDEOS} video generation tasks...")
    tasks = []
    for i in range(NUM_VIDEOS):
        label = f"Video {i + 1}/{NUM_VIDEOS}"
        result = create_task(prompt, image_url)
        task_id = result.get("id")
        print(f"  [{label}] Task ID: {task_id}")
        tasks.append((task_id, label))

    # Wait for all tasks in parallel
    print(f"\nWaiting for all {NUM_VIDEOS} videos to complete...")
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_VIDEOS) as pool:
        futures = {
            pool.submit(wait_for_task, tid, label): (tid, label)
            for tid, label in tasks
        }
        for future in concurrent.futures.as_completed(futures):
            tid, label = futures[future]
            results.append((label, future.result()))

    # Download completed videos
    results.sort(key=lambda x: x[0])
    print(f"\nDownloading videos...")
    downloaded = []
    for i, (label, result) in enumerate(results):
        if result is None:
            print(f"  [{label}] Skipped (failed or timed out)")
            continue
        path = f"{output_prefix}_{i + 1}.mp4"
        if download_video(result, path):
            print(f"  [{label}] Saved: {path}")
            downloaded.append(path)

    print(f"\nDone! {len(downloaded)}/{NUM_VIDEOS} videos saved.")
    return downloaded


def main():
    parser = argparse.ArgumentParser(description="Generate 4 videos from image + prompt")
    parser.add_argument("prompt", help="Text prompt describing the video motion")
    parser.add_argument("image", help="Image URL or local file path")
    parser.add_argument("--output", "-o", default="output", help="Output file prefix (default: output)")
    args = parser.parse_args()

    generate(args.prompt, args.image, args.output)


if __name__ == "__main__":
    main()
