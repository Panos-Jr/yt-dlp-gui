from tkinter import *
from tkinter import messagebox
import os
import re
import yt_dlp
from colorama import Fore as F, Back as B

def is_valid_youtube_url(url):
    youtube_regex = r'^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+$'
    return re.match(youtube_regex, url)

def download_best_audio(url, path):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(path, f'%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def download_best_combined(url, path):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': os.path.join(path, f'%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def find_file(download_folder, file_name):
    files_in_folder = os.listdir(download_folder)
    for file_ident in files_in_folder:
        name, ext = os.path.splitext(file_ident)
        print(name, file_name, 'file_name')
        if file_name == name:
            return file_ident

def download_video():
    url = url_entry.get()
    selection = selection_var.get()
    if not url:
        messagebox.showerror("Error", "Please enter a YouTube URL.")
        return

    if not is_valid_youtube_url(url):
        messagebox.showerror("Error", "Invalid YouTube URL.")
        return

    try:
        info = yt_dlp.YoutubeDL().extract_info(url, download=False)
        title = info['title']
        desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
        download_folder = os.path.join(desktop, 'downloads')

        if selection == 'a':
            download_best_audio(url, download_folder)
            print(f'{B.GREEN}Downloaded{B.BLACK}', title, download_folder)
            file_name = find_file(download_folder, title)
            messagebox.showinfo("Success", f'Audio downloaded as {file_name}')
        else:
            download_best_combined(url, download_folder)
            print(f'{B.GREEN}Downloaded{B.BLACK}', title, download_folder)
            file_name = find_file(download_folder, title)
            messagebox.showinfo("Success", f'Video downloaded as {file_name}')

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

root = Tk()
root.title("YouTube Downloader")
root.geometry("400x200")
root.resizable(False, False)

frame = Frame(root)
frame.pack(pady=20)

label = Label(frame, text="Enter YouTube URL:")
label.grid(row=0, column=0, padx=10, pady=5, sticky="e")

url_entry = Entry(frame, width=40)
url_entry.grid(row=0, column=1, padx=10, pady=5)

selection_var = StringVar()
selection_var.set("a")
audio_radio = Radiobutton(frame, text="Audio", variable=selection_var, value="a")
video_radio = Radiobutton(frame, text="Video", variable=selection_var, value="v")
audio_radio.grid(row=1, column=0, padx=10, pady=5, sticky="w")
video_radio.grid(row=1, column=1, padx=10, pady=5, sticky="w")

download_button = Button(frame, text="Download", command=download_video)
download_button.grid(row=2, columnspan=2, pady=10)

root.mainloop()
