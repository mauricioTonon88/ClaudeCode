# BytePlus Video Generation Wrapper

Simple wrapper around the BytePlus ModelArk video generation API (Seedance model).

## Setup

```bash
pip install -r requirements.txt
export ARK_API_KEY="your-api-key-here"
```

## Command Line Usage

**Text-to-video:**
```bash
python byteplus_video.py "A cat walking on the moon" -o cat_moon.mp4
```

**Image-to-video:**
```bash
python byteplus_video.py "Camera slowly zooms in" --image "https://example.com/photo.png" -o result.mp4
```

**Options:**
```
--image, -i       Image URL for image-to-video mode
--duration, -d    Video duration in seconds (default: 5)
--camera-fixed    Fix camera position
--output, -o      Output file path (default: output.mp4)
--no-wait         Submit task without waiting for completion
--status TASK_ID  Check status of an existing task
--timeout         Max wait time in seconds (default: 600)
```

## Python Usage

```python
from byteplus_video import BytePlusVideo

client = BytePlusVideo(api_key="your-key")

# Text-to-video
task = client.create_task("A drone flying through a canyon --duration 5")
result = client.wait_for_result(task["id"])
client.download_video(result, "output.mp4")

# Image-to-video
task = client.create_task(
    "The scene comes alive with gentle motion",
    image_url="https://example.com/photo.png",
    duration=5
)
result = client.wait_for_result(task["id"])
client.download_video(result, "output.mp4")
```
