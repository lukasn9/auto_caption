# AutoCaption
This project is a desktop application for generating subtitles from videos using OpenAI's Whisper model. You can use the GUI built with PySide6, to easily generate `.srt` subtitle files.

## Features
- Supports multiple formats (`.mp4`, `.avi`, `.mkv`, `.mov`).
- Automatically generates subtitles using the Whisper model.
- Prints error messages for easy debugging.

## Requirements
- Python >= 3.8
- Installed `ffmpeg`
- Installed `PySide6`, `Whisper`, `MoviePy`

### Installation of Dependencies
```
pip install PySide6 openai-whisper moviepy ffmpeg
```

## Usage
1. Run the application:
```
python gen_subs.py
```
2. Click the "Select Video" button to choose a video.
3. The application will process the video and generate an .srt subtitle file in the same directory as the video.

## Notes
- Whisper supports different models (`tiny`, `base`, `small`, `medium`, `large`). The app currently uses the `base` model for a balance between speed and accuracy, but you can change this in code.