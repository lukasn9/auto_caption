import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                             QWidget, QLabel, QProgressBar, QFileDialog, QFrame)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QPalette
import whisper
from moviepy import VideoFileClip
import tempfile

STYLES = """
QMainWindow {
    background-color: #1e1e1e;
}

QLabel {
    color: #ffffff;
    font-size: 14px;
    padding: 10px;
}

QPushButton {
    background-color: #007acc;
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 6px;
    font-size: 14px;
    min-width: 120px;
}

QPushButton:hover {
    background-color: #0098ff;
}

QPushButton:disabled {
    background-color: #4d4d4d;
    color: #808080;
}

QProgressBar {
    border: none;
    background-color: #333333;
    border-radius: 4px;
    height: 8px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #007acc;
    border-radius: 4px;
}

QFrame#container {
    background-color: #2d2d2d;
    border-radius: 10px;
    padding: 20px;
}
"""

class SubtitleGenerator(QThread):
    progress = Signal(int)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path
        self.model = "base"

    def run(self):
        temp_audio = None
        video = None
        try:
            self.progress.emit(10)
            video = VideoFileClip(self.video_path)

            temp_dir = tempfile.gettempdir()
            temp_audio = os.path.join(temp_dir, "temp_audio.wav")

            video.audio.write_audiofile(temp_audio, logger=None)
            self.progress.emit(30)

            try:
                model = whisper.load_model(self.model)
                self.progress.emit(50)

                result = model.transcribe(temp_audio)
                self.progress.emit(80)

            except Exception as e:
                raise Exception(f"Error during transcription: {str(e)}.")

            srt_content = self._generate_srt(result["segments"])

            srt_path = os.path.splitext(self.video_path)[0] + ".srt"
            with open(srt_path, "w", encoding="utf-8") as f:
                f.write(srt_content)
            
            self.progress.emit(100)
            self.finished.emit(srt_path)

        except Exception as e:
            self.error.emit(str(e))
        
        finally:
            try:
                if video is not None:
                    video.close()
                if temp_audio and os.path.exists(temp_audio):
                    os.remove(temp_audio)
            except Exception as e:
                print(f"Cleanup error: {str(e)}")

    def _generate_srt(self, segments):
        srt_content = ""
        for i, segment in enumerate(segments, start=1):
            start_time = self._format_timestamp(segment["start"])
            end_time = self._format_timestamp(segment["end"])
            
            srt_content += f"{i}\n"
            srt_content += f"{start_time} --> {end_time}\n"
            srt_content += f"{segment['text'].strip()}\n\n"
        
        return srt_content

    def _format_timestamp(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        milliseconds = int((seconds - int(seconds)) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{milliseconds:03d}"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AutoCaption")
        self.setMinimumSize(500, 300)
        self.setStyleSheet(STYLES)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(40, 40, 40, 40)

        container = QFrame()
        container.setObjectName("container")
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(20)

        title_label = QLabel("AutoCaption")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff; padding: 0;")
        
        self.status_label = QLabel("Select a video to generate subtitles")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #cccccc;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        
        self.select_button = QPushButton("Select Video")
        self.select_button.setCursor(Qt.PointingHandCursor)
        self.select_button.clicked.connect(self.select_video)

        container_layout.addWidget(title_label)
        container_layout.addWidget(self.status_label)
        container_layout.addWidget(self.progress_bar)
        container_layout.addWidget(self.select_button, alignment=Qt.AlignCenter)
        container_layout.addStretch()

        main_layout.addWidget(container)

    def select_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video File",
            "",
            "Video Files (*.mp4 *.avi *.mkv *.mov)"
        )
        
        if file_path:
            self.process_video(file_path)

    def process_video(self, video_path):
        self.select_button.setEnabled(False)
        self.progress_bar.show()
        self.status_label.setText("Processing video...")
        self.status_label.setStyleSheet("color: #007acc;")

        self.worker = SubtitleGenerator(video_path)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def on_finished(self, srt_path):
        self.status_label.setText(f"Subtitles generated successfully!\nSaved to: {srt_path}")
        self.status_label.setStyleSheet("color: #6cc644;")
        self.select_button.setEnabled(True)
        self.progress_bar.hide()

    def on_error(self, error_message):
        self.status_label.setText(f"Error: {error_message}")
        self.status_label.setStyleSheet("color: #f14c4c;")
        self.select_button.setEnabled(True)
        self.progress_bar.hide()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()