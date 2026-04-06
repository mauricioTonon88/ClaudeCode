"""
BytePlus Video Generation API Wrapper

Simple wrapper around the BytePlus ModelArk video generation API.
Supports text-to-video and image-to-video generation.

Usage:
    from byteplus_video import BytePlusVideo

    client = BytePlusVideo(api_key="your-api-key")

    # Text-to-video
    task = client.create_task("A cat walking on the moon --duration 5")

    # Image-to-video
    task = client.create_task(
        "Camera slowly zooms in --duration 5",
        image_url="https://example.com/photo.png"
    )

    # Wait for result and download
    result = client.wait_for_result(task["id"])
    client.download_video(result, "output.mp4")
"""

import os
import sys
import time
import argparse
import requests


BASE_URL = "https://ark.ap-southeast.bytepluses.com/api/v3/contents/generations/tasks"
DEFAULT_MODEL = "seedance-1-5-pro-251215"


class BytePlusVideo:
    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or os.environ.get("ARK_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key required. Pass api_key= or set ARK_API_KEY environment variable."
            )
        self.model = model or DEFAULT_MODEL
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def create_task(self, prompt, image_url=None, duration=5, camera_fixed=False):
        """Create a video generation task.

        Args:
            prompt: Text description of the video to generate.
            image_url: Optional image URL for image-to-video generation.
            duration: Video duration in seconds (default: 5).
            camera_fixed: Whether to fix the camera (default: False).

        Returns:
            Task dict with 'id' and other metadata.
        """
        text = f"{prompt}  --duration {duration} --camerafixed {str(camera_fixed).lower()}"

        content = [{"type": "text", "text": text}]

        if image_url:
            content.append({
                "type": "image_url",
                "image_url": {"url": image_url},
            })

        payload = {
            "model": self.model,
            "content": content,
        }

        resp = requests.post(BASE_URL, headers=self.headers, json=payload)
        resp.raise_for_status()
        return resp.json()

    def get_task(self, task_id):
        """Query the status of a video generation task.

        Args:
            task_id: The task ID returned by create_task.

        Returns:
            Task dict with status and result info.
        """
        url = f"{BASE_URL}/{task_id}"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def wait_for_result(self, task_id, poll_interval=10, timeout=600):
        """Poll a task until it completes or times out.

        Args:
            task_id: The task ID to poll.
            poll_interval: Seconds between polls (default: 10).
            timeout: Max seconds to wait (default: 600).

        Returns:
            Completed task dict.

        Raises:
            TimeoutError: If the task doesn't complete within timeout.
            RuntimeError: If the task fails.
        """
        start = time.time()
        while True:
            result = self.get_task(task_id)

            status = result.get("status", "")
            if status == "succeeded":
                return result
            if status in ("failed", "cancelled"):
                error_msg = result.get("error", {}).get("message", "Unknown error")
                raise RuntimeError(f"Task {task_id} {status}: {error_msg}")

            elapsed = time.time() - start
            if elapsed >= timeout:
                raise TimeoutError(
                    f"Task {task_id} did not complete within {timeout}s (last status: {status})"
                )

            print(f"  Status: {status} ({int(elapsed)}s elapsed, polling every {poll_interval}s)")
            time.sleep(poll_interval)

    def download_video(self, task_result, output_path):
        """Download the generated video from a completed task.

        Args:
            task_result: The completed task dict from get_task/wait_for_result.
            output_path: Local file path to save the video.

        Returns:
            The output file path.
        """
        # Navigate the response to find the video URL
        content = task_result.get("content", {})
        if isinstance(content, list):
            for item in content:
                if item.get("type") == "video_url":
                    video_url = item.get("video_url", {}).get("url")
                    break
            else:
                raise ValueError(f"No video URL found in task result: {task_result}")
        elif isinstance(content, dict):
            video_url = content.get("video_url", {}).get("url")
        else:
            raise ValueError(f"Unexpected content format in task result: {task_result}")

        if not video_url:
            raise ValueError(f"No video URL found in task result: {task_result}")

        print(f"Downloading video from: {video_url}")
        resp = requests.get(video_url, stream=True)
        resp.raise_for_status()

        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"Saved to: {output_path}")
        return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate videos using BytePlus ModelArk API"
    )
    parser.add_argument("prompt", help="Text prompt describing the video")
    parser.add_argument(
        "--image", "-i", help="Image URL for image-to-video generation"
    )
    parser.add_argument(
        "--duration", "-d", type=int, default=5, help="Video duration in seconds (default: 5)"
    )
    parser.add_argument(
        "--camera-fixed", action="store_true", help="Fix the camera position"
    )
    parser.add_argument(
        "--output", "-o", default="output.mp4", help="Output file path (default: output.mp4)"
    )
    parser.add_argument(
        "--model", "-m", default=DEFAULT_MODEL, help=f"Model name (default: {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "--api-key", help="API key (or set ARK_API_KEY env var)"
    )
    parser.add_argument(
        "--no-wait", action="store_true", help="Submit task and exit without waiting"
    )
    parser.add_argument(
        "--poll-interval", type=int, default=10, help="Seconds between status checks (default: 10)"
    )
    parser.add_argument(
        "--timeout", type=int, default=600, help="Max seconds to wait (default: 600)"
    )
    parser.add_argument(
        "--status", help="Check status of an existing task ID instead of creating one"
    )

    args = parser.parse_args()

    client = BytePlusVideo(api_key=args.api_key, model=args.model)

    # Status check mode
    if args.status:
        result = client.get_task(args.status)
        print_task_info(result)
        return

    # Create task
    print(f"Creating video generation task...")
    if args.image:
        print(f"  Mode: image-to-video")
        print(f"  Image: {args.image}")
    else:
        print(f"  Mode: text-to-video")
    print(f"  Prompt: {args.prompt}")
    print(f"  Duration: {args.duration}s")

    task = client.create_task(
        prompt=args.prompt,
        image_url=args.image,
        duration=args.duration,
        camera_fixed=args.camera_fixed,
    )

    task_id = task.get("id")
    print(f"  Task ID: {task_id}")

    if args.no_wait:
        print(f"\nTask submitted. Check status later with:")
        print(f"  python byteplus_video.py --status {task_id} dummy")
        return

    # Wait and download
    print(f"\nWaiting for video generation...")
    result = client.wait_for_result(
        task_id, poll_interval=args.poll_interval, timeout=args.timeout
    )

    print(f"\nVideo generation complete!")
    client.download_video(result, args.output)


def print_task_info(task):
    """Print task details in a readable format."""
    print(f"Task ID: {task.get('id')}")
    print(f"Status:  {task.get('status')}")
    if task.get("error"):
        print(f"Error:   {task['error'].get('message', 'Unknown')}")
    if task.get("content"):
        print(f"Content: {task['content']}")


if __name__ == "__main__":
    main()
