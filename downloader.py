import yt_dlp
import os
import ffmpeg

class Downloader:
    def __init__(self):
        pass

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
        print('save path', save_path)
        file_container = extension.lstrip('.')
        ydl_opts = {
            'format': f'bestaudio[ext={file_container}]/best' if selection == 'a' else f'bestvideo[ext={file_container}]+bestaudio/best[ext=mp4]/best',
            'progress_hooks': [progress_hook] if progress_hook else [],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredquality': '192'
            }] if selection == 'a' else [],
            'outtmpl': os.path.splitext(save_path)[0] + '.%(ext)s',
            'noplaylist': True,
            'quiet': True,
        }

        if os.path.isfile(save_path):
            raise FileExistsError("File already exists.")

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            print("Download completed successfully.")
        except:
            print('oops, trying alternative method...')
            ydl_opts['format'] = 'bestaudio/best' if selection == 'a' else 'bestvideo+bestaudio/best'
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            download_dir = os.listdir(os.path.dirname(save_path))
            print('download dir', download_dir)
            for file in download_dir:
                if os.path.splitext(os.path.basename(save_path))[0] in file and not extension in os.path.splitext(file)[1]:
                    input_file = os.path.join(os.path.dirname(save_path), file)
                    print('remuxing', input_file, 'to', save_path)
                    self.remux_to_target_format(input_file, save_path)
                    break