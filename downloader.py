import yt_dlp
import os
import ffmpeg

class Downloader:
    def __init__(self):
        self.status = ''
        self.count = 0

    def remux_to_target_format(self, input_file, output_file):
        try:
            (
                ffmpeg.input(input_file)
                .output(output_file)
                .run()
            )
            os.remove(input_file)
        except Exception as e:
            print(f"Remuxing failed: {e}")

    def download(self, url, selection, save_path, extension, progress_hook=None):
        ydl_opts = {
            'format': 'bestaudio/best' if selection == 'a' else 'bestvideo+bestaudio/best',
            'progress_hooks': [progress_hook] if progress_hook else [],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredquality': '192',
            }] if selection == 'a' else [],
            'outtmpl': os.path.splitext(save_path)[0] + extension,
            'noplaylist': True,
            'quiet': True,
        }

        if os.path.isfile(save_path):
            raise FileExistsError("File already exists.")

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except:
            ydl_opts['outtmpl'] = os.path.splitext(save_path)[0] + '.%(ext)s'
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            download_dir = os.listdir(os.path.dirname(save_path))
            for file in download_dir:
                if file.startswith(os.path.splitext(os.path.basename(save_path))[0]) and not file.endswith(extension):
                    input_file = os.path.join(os.path.dirname(save_path), file)
                    self.remux_to_target_format(input_file, save_path)
                    break