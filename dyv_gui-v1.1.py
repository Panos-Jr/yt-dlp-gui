from tkinter import *
from tkinter import ttk, messagebox
import os
import re
import yt_dlp
import threading
import math
import requests
import urllib.request

def is_valid_youtube_url(url):
    youtube_regex = r'^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+$'
    return re.match(youtube_regex, url)

def progress_hook(d):
    global status, status_label, progress_bar_var
    status = None

    if d['status'] == 'downloading':
        total_bytes = d.get('total_bytes', 0)
        downloaded_bytes = d.get('downloaded_bytes', 0)

        if 'fragment_index' in d and d['fragment_index'] > 0:
            progress = math.floor(int(d["fragment_index"])/int(d["fragment_count"])*100)
            status = f'Downloading {d["fragment_index"]}/{d["fragment_count"]} ({progress}%)'
            progress_bar_var.set(progress)

        if total_bytes > 0:
            progress = math.floor(int(downloaded_bytes)/int(total_bytes)*100)
            status = f'Downloading ({progress}%)'
            progress_bar_var.set(progress)

    elif d['status'] == 'finished':
        status = 'Download completed'
    else:
        status = d['status']

    status_label.config(text=status)
    root.update()

def find_file(download_folder, file_name):
    return next((file_ident for file_ident in os.listdir(download_folder) if file_name == os.path.splitext(file_ident)[0]), None)

def start_update(version):
    url = 'https://raw.githubusercontent.com/Panos-Jr/yt-dlp-gui/main/download_release.txt'
    response = requests.get(url)
        
    if response.status_code == 200:
        file_url = response.text
        file_name = 'dyv_gui-' + version + '.exe'
        desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
        local_path = os.path.join(desktop, file_name)
        

        try:
            urllib.request.urlretrieve(file_url, local_path)
            messagebox.showinfo("Success", f'Update downloaded to \'Desktop\'')
        except:
            messagebox.showerror("Error", f"An error occurred while downloading the file.")
    else:
        messagebox.showerror("Error", f"An error occurred while downloading the file.")

def check_for_updates():
    global update_status_label
    try:
        current_version = 'v1.1'
        url = 'https://raw.githubusercontent.com/Panos-Jr/yt-dlp-gui/main/version.txt'
        response = requests.get(url)
        
        if response.status_code == 200:
            latest_version = response.text.strip()
            if latest_version == current_version:
                update_status_label.config(text='No update available')
            else:
                update_status_label.config(text='Update found!')
                start_update(latest_version)
        else:
            update_status_label.config(text='Failed to check for updates')

    except Exception as e:
        update_status_label.config(text='Error checking for updates')

def update_status_labels():
    global status_progress_frame
    download_status_label = Label(status_progress_frame, text="", font=("Helvetica", 12))
    download_status_label.grid(row=0, column=0, columnspan=2, pady=(10,5))
    status_label = Label(status_progress_frame, text="", font=("Helvetica", 12))
    status_label.grid(row=1, column=0, columnspan=2, pady=(10, 5))
    return download_status_label, status_label

def download_media(url, selection):
    global progress_bar, my_menu, progress_bar_var, status_label
    try:
        progress_bar = None
        my_menu.entryconfigure("Tasks", state="disabled")
        download_status_label, status_label = update_status_labels()
        update_status_label.config(text='')
        download_status_label.config(text=f'Starting download...')
        info = yt_dlp.YoutubeDL().extract_info(url, download=False)
        title = info['title']
        desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
        download_folder = os.path.join(desktop, 'downloads')
        title += '-audio' if selection == 'a' else '-video'
        file_name = find_file(download_folder, title)

        if file_name:
            enable_download_button()
            download_status_label.destroy()
            messagebox.showinfo("File already exists", f'You\'ve already downloaded this.')
            return
        
        ydl_opts = {
            'format': 'bestaudio/best' if selection == 'a' else 'bestvideo+bestaudio/best',
            'progress_hooks': [progress_hook],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }] if selection == 'a' else [],
            'outtmpl': os.path.join(download_folder, f'{title}.%(ext)s'),
            'quiet': True,
            'no_warnings': True
        }
        
        ydl = yt_dlp.YoutubeDL(ydl_opts)
        download_status_label.destroy()
        progress_bar_var = DoubleVar()
        progress_bar = ttk.Progressbar(status_progress_frame, orient=HORIZONTAL, length=300, mode="determinate", variable=progress_bar_var)
        progress_bar.grid()
        ydl.download([url])
        
        if selection == 'a':
            messagebox.showinfo("Success", f'Audio saved in \'downloads\'')
        else:
            messagebox.showinfo("Success", f'Video saved in \'downloads\'')
        
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
    finally:
        if progress_bar:
            progress_bar.grid_remove()
        my_menu.entryconfigure("Tasks", state="normal")
        status_label.destroy()
        enable_download_button()

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
    
    disable_download_button()
    download_thread = threading.Thread(target=lambda: download_media(url, selection))
    download_thread.start()

root = Tk()
root.title("YouTube Downloader")
root.geometry("400x300")
root.resizable(False, False)

input_frame = Frame(root)
input_frame.grid(row=0, column=0, padx=10, pady=20)

url_label = Label(input_frame, text="Enter YouTube URL:")
url_label.grid(row=0, column=0, pady=5)

url_entry = Entry(input_frame, width=40)
url_entry.grid(row=0, column=1, padx=12)

my_menu = Menu(root)
root.config(menu=my_menu)

tasks_menu = Menu(my_menu, tearoff="off")
my_menu.add_cascade(label="Tasks", menu=tasks_menu)
tasks_menu.add_command(label='Check for updates', command=check_for_updates)

selection_var = StringVar()
selection_var.set('a')
audio_radio = Radiobutton(input_frame, text="Audio", variable=selection_var, value="a")
video_radio = Radiobutton(input_frame, text="Video", variable=selection_var, value="v")
audio_radio.grid(row=1, column=0)
video_radio.grid(row=1, column=1)

download_button = Button(input_frame, text="Download", command=download_video)
download_button.grid(row=2, columnspan=2, pady=10)

status_progress_frame = Frame(root)
status_progress_frame.grid(row=1, column=0, padx=10)

updates_frame = Frame(root)
updates_frame.grid(row=3, column=0, columnspan=2, pady=10)

update_status_label = Label(updates_frame, text="", font=("Helvetica", 12))
update_status_label.grid(pady=10)

root.mainloop()
