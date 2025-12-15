Docker image for running index.py (Python 3.9+)

Build

Open a terminal in this folder and run:

```powershell
docker build -t alex-assistant:latest .
```

Run

The container requires access to audio devices and a browser if you want Selenium features. For simple runs that fallback to text-input, run:

```powershell
docker run --rm -it alex-assistant:latest python index.py
```

Notes

- This Dockerfile installs Chromium and Chromium driver so Selenium can run headless inside the container. If you want to control a host browser (on Windows), run the script outside Docker.
- Microphone access inside Docker on Windows is non-trivial. The script falls back to text input when a microphone isn't available.
- If you need microphone support and audio playback, consider running natively on the host or use specialized containers with PulseAudio/socket forwarding.

# Web bán hàng quần áo (Flask)

Chạy nhanh trên máy:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Mở trình duyệt tới http://localhost:5000 để xem shop demo.

