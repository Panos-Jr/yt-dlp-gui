from tkinter import *
from tkinter import ttk, messagebox
import os
import re
import yt_dlp
import threading
import math

def is_valid_youtube_url(url):
    youtube_regex = r'^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+$'
    return re.match(youtube_regex, url)

# def progress_hook(d):
#     if d['status'] == 'downloading':
#         if 'fragment_index' in d:
#             status = f'Downloading {d["fragment_index"]}/{d["fragment_count"]} fragments'
#         else:
#             status = 'Downloading'
#     elif d['status'] == 'finished':
#         status = 'Download completed'
#     else:
#         status = d['status']
#     downloaded = d.get('downloaded_bytes', 0)
#     total = d.get('total_bytes', 0)
#     if total > 0:
#         progress = math.floor(int((downloaded / total) * 100))
#         progress_bar['value'] = progress
#     status_label.config(text=status)

def progress_hook(d):
    global status
    status = None
    if d['status'] == 'downloading':
        if 'fragment_index' in d and d['fragment_index'] > 0:
                progress = math.floor(int(d["fragment_index"])/int(d["fragment_count"])*100)
                status = f'Downloading {d["fragment_index"]}/{d["fragment_count"]} ({progress}%)'
                progress_bar_var.set(progress)
    elif d['status'] == 'finished':
        status = 'Download completed'
    else:
        status = d['status']
    status_label.config(text=status)

    root.update()



def download_best_audio(url, ydl):
    ydl.download([url])

def download_best_combined(url, ydl):
    ydl.download([url])

def find_file(download_folder, file_name):
    files_in_folder = os.listdir(download_folder)
    for file_ident in files_in_folder:
        name, ext = os.path.splitext(file_ident)
        if file_name == name:
            return file_ident

def disable_download_button():
    download_button.config(state="disabled")

def enable_download_button():
    download_button.config(state="normal")

def download_video():
    url = url_entry.get()
    selection = selection_var.get()
    
    if not url:
        messagebox.showerror("Error", "Please enter a YouTube URL.")
        return

    if not is_valid_youtube_url(url):
        messagebox.showerror("Error", "Invalid YouTube URL.")
        return

    def download():
        try:
            download_status_label.config(text=f'Starting download...')
            info = yt_dlp.YoutubeDL().extract_info(url, download=False)
            title = info['title']
            desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
            download_folder = os.path.join(desktop, 'downloads')
            file_name = find_file(download_folder, title)
            if file_name:
                enable_download_button()
                download_status_label.destroy()
                messagebox.showinfo("File already exists", f'You\'ve already downloaded this.')
                return
            progress_bar.grid()

            if selection == 'a':
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'progress_hooks': [progress_hook],
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'outtmpl': os.path.join(download_folder, f'%(title)s.%(ext)s'),
                    'quiet': True,
                    'no_warnings': True
                }

                ydl = yt_dlp.YoutubeDL(ydl_opts)
                download_status_label.destroy()
                download_best_audio(url, ydl)
                messagebox.showinfo("Success", f'Audio saved in \'downloads\'')
            else:
                ydl_opts = {
                    'format': 'bestvideo+bestaudio/best',
                    'progress_hooks': [progress_hook],
                    'outtmpl': os.path.join(download_folder, f'%(title)s.%(ext)s'),
                    'quiet': True,
                    'no_warnings': True
                }

                ydl = yt_dlp.YoutubeDL(ydl_opts)
                download_status_label.destroy()
                download_best_combined(url, ydl)
                messagebox.showinfo("Success", f'Video saved in \'downloads\'')


        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
        finally:
            progress_bar.grid_remove()
            status_label.destroy()
        enable_download_button()

    disable_download_button()

    download_thread = threading.Thread(target=download)
    download_thread.start()

root = Tk()
root.title("YouTube Downloader")
root.geometry("400x300")
root.resizable(False, False)

input_frame = Frame(root)
input_frame.pack(pady=20)

url_label = Label(input_frame, text="Enter YouTube URL:")
url_label.grid(row=0, column=0, padx=10, pady=5)

url_entry = Entry(input_frame, width=40)
url_entry.grid(row=0, column=1)

selection_var = StringVar()
selection_var.set('a')
audio_radio = Radiobutton(input_frame, text="Audio", variable=selection_var, value="a")
video_radio = Radiobutton(input_frame, text="Video", variable=selection_var, value="v")
audio_radio.grid(row=1, column=0)
video_radio.grid(row=1, column=1)

download_button = Button(input_frame, text="Download", command=download_video)
download_button.grid(row=2, columnspan=2, pady=10)

status_progress_frame = Frame(root)
status_progress_frame.pack(pady=10)

status_label = Label(status_progress_frame, text="", font=("Helvetica", 12))
status_label.grid(row=1, column=0, columnspan=2, pady=(10, 5))

download_status_label = Label(status_progress_frame, text="", font=("Helvetica", 12))
download_status_label.grid(row=0, column=0, columnspan=2, pady=(10,5))

progress_bar_var = DoubleVar()
progress_bar = ttk.Progressbar(status_progress_frame, orient=HORIZONTAL, length=300, mode="determinate", variable=progress_bar_var)
progress_bar.grid(row=2, column=0, columnspan=2, pady=(10, 5))
progress_bar.grid_remove()


root.mainloop()
