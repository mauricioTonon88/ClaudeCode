# BytePlus Image-to-Video Wrapper

Generates **4 videos** from an image + text prompt using the BytePlus Seedance model.

**Fixed settings:** 720p, 5 seconds, no sound, no draft mode, online generation.

## Setup

```bash
pip install requests
```

## Usage

```bash
# From an image URL
python byteplus_video.py "A drone flies through the scene" https://example.com/photo.png

# From a local image file
python byteplus_video.py "Gentle camera zoom" ./my_photo.png

# Custom output prefix (produces my_video_1.mp4 ... my_video_4.mp4)
python byteplus_video.py "The scene comes alive" ./photo.png -o my_video
```

## Output

Produces 4 files: `output_1.mp4`, `output_2.mp4`, `output_3.mp4`, `output_4.mp4`

## Python Usage

```python
from byteplus_video import generate

videos = generate(
    prompt="Camera slowly pans across the landscape",
    image_source="https://example.com/photo.png",
    output_prefix="my_video"
)
```
