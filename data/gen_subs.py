import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                             QWidget, QLabel, QProgressBar, QFileDialog)
from PySide6.QtCore import Qt, QThread, Signal
import whisper
from moviepy import VideoFileClip
import tempfile

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
        self.setMinimumSize(400, 200)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.status_label = QLabel("Select a video to generate subtitles")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()

        self.select_button = QPushButton("Select Video")
        self.select_button.clicked.connect(self.select_video)

        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.select_button)

    def select_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video File",
            "",
            "Video Files (*.mp4 *.avi *.mkv *.mov)"
        )
        print(f"Selected file path: {file_path}")
        
        if file_path:
            self.process_video(file_path)

    def process_video(self, video_path):
        self.select_button.setEnabled(False)
        self.progress_bar.show()
        self.status_label.setText("Processing video...")

        self.worker = SubtitleGenerator(video_path)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def on_finished(self, srt_path):
        self.status_label.setText(f"Subtitles generated successfully!\nSaved to: {srt_path}")
        self.select_button.setEnabled(True)
        self.progress_bar.hide()

    def on_error(self, error_message):
        self.status_label.setText(f"Error: {error_message}")
        self.select_button.setEnabled(True)
        self.progress_bar.hide()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()