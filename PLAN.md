# Screen Recorder App — Implementation Plan

## Overview
A lightweight desktop screen recorder that captures a user-selected region of the screen at native resolution and frame rate, saves the output as a video file to a user-chosen folder.

## Tech Stack
- **Language**: Python 3
- **GUI Framework**: PyQt6 (cross-platform, supports transparent overlay windows)
- **Screen Capture**: `mss` (fast, cross-platform screenshot library)
- **Video Encoding**: OpenCV (`cv2`) with `VideoWriter` (MP4 via FFMPEG backend)
- **Packaging**: Single script + `requirements.txt`

## Architecture

```
screen_recorder/
├── main.py              # Entry point
├── recorder.py          # Screen capture + video writing logic
├── region_selector.py   # Transparent overlay for selecting screen region
├── ui.py                # Main control window (Record/Stop buttons)
├── requirements.txt     # Dependencies
└── README.md            # Usage instructions
```

## Implementation Steps

### Step 1 — Project scaffolding
- Create `requirements.txt` with: `PyQt6`, `mss`, `opencv-python`, `numpy`
- Create `main.py` entry point

### Step 2 — Region selector (`region_selector.py`)
- Full-screen transparent overlay window (semi-transparent dark tint)
- Click-and-drag to draw a rectangle selecting the capture area
- Show pixel coordinates & dimensions while dragging
- On release, return the selected region `(x, y, width, height)` and close overlay
- ESC key cancels selection

### Step 3 — Screen capture & recording engine (`recorder.py`)
- Use `mss` to grab frames from the selected region
- Run capture in a background thread to keep UI responsive
- Write frames via `cv2.VideoWriter` (MP4V codec → `.mp4`)
- Capture at native screen FPS (query display refresh rate, default 30 fps)
- Handle start/stop lifecycle cleanly (release writer on stop)

### Step 4 — Main control UI (`ui.py`)
- Small always-on-top window with:
  1. **"Select Region"** button → opens the region selector overlay
  2. **"Record"** button → opens a folder picker dialog (`QFileDialog`), then starts recording
  3. **"Stop"** button → stops recording, finalizes video file
- Show recording status (duration, file path)
- Disable buttons appropriately during each state (idle / region-selected / recording)

### Step 5 — Wire everything together (`main.py`)
- Initialize `QApplication`
- Instantiate the control UI
- Connect signals: region selection → enable record, record → folder pick → start capture, stop → finalize

### Step 6 — Testing & polish
- Test on the current Linux environment
- Ensure clean shutdown (no zombie threads, temp files)
- Add basic error handling (no region selected, write permission errors)

## Output Behavior
1. User launches app → small control window appears
2. Clicks **Select Region** → screen dims, user drags a rectangle
3. Clicks **Record** → folder picker opens → user picks save location
4. Recording starts immediately, status shown in control window
5. Clicks **Stop** → video saved as `recording_YYYYMMDD_HHMMSS.mp4` in chosen folder

## Key Design Decisions
- **mss over Pillow/scrot**: Much faster frame grabbing (important for real-time FPS)
- **Background thread for capture**: Keeps GUI responsive during recording
- **PyQt6**: Modern, well-maintained, supports transparent windows needed for region selection
- **MP4V codec**: Widely compatible, no extra codec installs needed
