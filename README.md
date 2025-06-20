# speech-recognition-on-ctrl

This project enables speech-to-text transcription and automatic keyboard input by holding the Ctrl key. It is primarily designed for **Wayland** users, where `evdev` is the only practical solution for monitoring keyboard events.

## Features

- Record audio by holding or Right Ctrl.
- Transcribe speech using NVIDIA NeMo Parakeet ASR models (parakeet-tdt-0.6b-v2).
- Automatically type the recognized text wherever your cursor is.

## Requirements

- Python 3.10+
- A supported NVIDIA GPU (for NeMo ASR)
- Wayland session (X11 may work, but there are more cleaner and easier ways to implement this feature for it so DIY=])
- `sudo` privileges (required for evdev access)

## Installation

1. Clone this repository:

    ```bash
    git clone https://github.com/yourusername/speech-recognition-on-ctrl.git
    cd speech-recognition-on-ctrl
    ```

2. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

> **Note:** You must run the script with `sudo` to access keyboard events via `evdev`.

```bash
sudo python3 main.py
```

- **Hold Right Ctrl** to start recording.
- **Release Ctrl** to stop recording and transcribe.
- **Press ESC** to exit.

## Notes

- This tool is intended for Wayland users, as `evdev` is the only reliable way to monitor keyboard events for Wayland applications.
- Make sure your microphone is set up and accessible.
- The script will create a virtual keyboard device to type the recognized text.
- The model is stored in /root/.cache/huggingface folder