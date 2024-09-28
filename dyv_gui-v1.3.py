import customtkinter
from tkinter import *
from tkinter import filedialog
from tkinter import ttk, messagebox
import subprocess
import os
import re
import yt_dlp
import threading
import math
import requests
import urllib.request
from dotenv import *
import sys

customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("dark-blue")


env_path = os.path.join(os.environ['userprofile'], 'Documents', '.env')

if not os.path.isfile(env_path):
    with open(env_path, 'w') as f:
        f.write('CHECK_UPDATE=\'ON\'')
load_dotenv(dotenv_path=env_path)


def save_checkbox_value():
    global check_var, bottom_checkbox, env_path
    set_key(dotenv_path=env_path, key_to_set="CHECK_UPDATE", value_to_set=check_var.get())
    if update_checkbox.get() == 'ON':
        check_for_updates()

def is_valid_youtube_url(url):
    youtube_regex = r'^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+$'
    return re.match(youtube_regex, url)

def progress_hook(d):
    global status, status_label, progress_bar
    status = None

    if d['status'] == 'downloading':
        total_bytes = d.get('total_bytes', 0)
        downloaded_bytes = d.get('downloaded_bytes', 0)

        if 'fragment_index' in d and d['fragment_index'] > 0:
            progress = math.floor(int(d["fragment_index"])/int(d["fragment_count"])*100)
            status = f'Downloading {d["fragment_index"]}/{d["fragment_count"]} ({progress}%)'
            progress_bar.set(progress/100)

        if total_bytes > 0:
            progress = math.floor(int(downloaded_bytes)/int(total_bytes)*100)
            status = f'Downloading ({progress}%)'
            progress_bar.set(progress/100)

    elif d['status'] == 'finished':
        status = 'Finishing download...'
    else:
        status = d['status']

    status_label.configure(text=status)
    app.update()

def find_file(download_folder, file_name):
    return next((file_ident for file_ident in os.listdir(download_folder) if file_name == os.path.splitext(file_ident)[0]), None)

def start_update(version):
    global update_status_label
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
    print('Checking for updates')
    try:
        current_version = 'v1.3'
        url = 'https://raw.githubusercontent.com/Panos-Jr/yt-dlp-gui/main/version.txt'
        response = requests.get(url)
        
        if response.status_code == 200:
            latest_version = response.text.strip()
            if latest_version == current_version:
                print('no updates')
                messagebox.showinfo(title='No updates', message='No update was found.')
                update_status_label.configure(text='')
                enable_download_button()
            else:
                update = messagebox.askokcancel(title='Update Found!', message='We\'ve found a newer update, would you like to download it?')
                if update:
                    update_status_label.configure(text='Starting Update')
                    start_update(latest_version)
                enable_download_button()
                update_status_label.configure(text='')
        else:
            messagebox.showwarning(title='Checking for Updates', message='An error occured while checking for updates.')

    except Exception as e:
        messagebox.showwarning(title='Checking for Updates', message='An error occured while checking for updates.')

def update_status_labels():
    global input_frame
    status_label = customtkinter.CTkLabel(master=input_frame, text="", font=("Helvetica", 15))
    status_label.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
    return status_label

ILLEGAL_CHARACTERS = r'[\\/:*?"<>|{}$!\'"&%`@+=,;]'

def sanitize_filename(filename):
    sanitized = re.sub(ILLEGAL_CHARACTERS, '', filename)

    sanitized = re.sub(r'[^\x00-\x7F]+', '', sanitized)

    sanitized = re.sub(r'_+', '_', sanitized).strip('_')
    
    return sanitized

def remux_to_target_format(input_file, output_file):
    try:
        subprocess.run(
            ['ffmpeg', '-i', input_file, '-c', 'copy', output_file],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        os.remove(input_file)
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Remuxing Error", f"Failed to remux the file: {e}")

def download_media(url, selection):
    global my_menu, progress_bar, status_label
    try:
        update_checkbox.grid_forget()
        status_label = update_status_labels()
        update_status_label.configure(text='')
        status_label.configure(text=f'Starting download...')
        info = yt_dlp.YoutubeDL().extract_info(url, download=False)
        title = info['title']
        title += '-audio' if selection == 'a' else '-video'

        title = sanitize_filename(title)
        
        file_extension = '.mp3' if selection == 'a' else '.mp4'
        file_types = [('MP3 Files', '*.mp3')] if selection == 'a' else [('MP4 Files', '*.mp4')]
        save_path = filedialog.asksaveasfilename(defaultextension=file_extension, 
                                                 filetypes=file_types, 
                                                 initialfile=title)
        
        if not save_path:
            enable_download_button()
            messagebox.showinfo("Cancelled", "Download cancelled by user.")
            return
        
        ydl_opts = {
            'format': 'bestaudio/best' if selection == 'a' else 'bestvideo+bestaudio/best',
            'progress_hooks': [progress_hook],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }] if selection == 'a' else [],
            'outtmpl': os.path.splitext(save_path)[0] + '.%(ext)s',
            'quiet': True,
            'no_warnings': True
        }
        
        if os.path.isfile(save_path):
            status_label.configure(text='File already exists.')
            return

        ydl = yt_dlp.YoutubeDL(ydl_opts)
        status_label.configure(text='')
        progress_bar = customtkinter.CTkProgressBar(input_frame, orientation=HORIZONTAL, width=400, mode="determinate")
        progress_bar.grid(row=3, column=0, padx=10, pady=10, columnspan=2, sticky="ew")
        progress_bar.set(0)
        ydl.download([url])
        
        downloaded_file = find_downloaded_file(os.path.splitext(save_path)[0])

        user_chosen_extension = os.path.splitext(save_path)[1]

        if downloaded_file and downloaded_file != save_path:
            messagebox.showinfo("Remuxing", f"Converting file to {user_chosen_extension}")
            remux_to_target_format(downloaded_file, save_path)
        else:
            if downloaded_file and downloaded_file != save_path:
                os.rename(downloaded_file, save_path)

        messagebox.showinfo("Success", f'File saved to {save_path}')
        progress_bar.grid_remove()
        status_label.destroy()
        enable_download_button()
        bottom_checkbox()
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
            
def find_downloaded_file(base_name):
    for ext in ['.mp4', '.mkv', '.webm']:
        if os.path.exists(base_name + ext):
            return base_name + ext
    return None

def disable_download_button():
    download_button.configure(state="disabled")

def enable_download_button():
    download_button.configure(state="normal")

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

app = customtkinter.CTk()
app.title('YouTube Downloader')
app.geometry('400x300')
app.resizable(False, False)

input_frame = customtkinter.CTkFrame(master=app, fg_color='transparent')
input_frame.grid(row=0, column=0, padx=10, pady=20, sticky="nsew")

input_frame.grid_columnconfigure(0, weight=1)
input_frame.grid_columnconfigure(1, weight=1)
input_frame.grid_rowconfigure(0, weight=1)
input_frame.grid_rowconfigure(1, weight=1)
input_frame.grid_rowconfigure(2, weight=1)
input_frame.grid_rowconfigure(3, weight=1)

url_entry = customtkinter.CTkEntry(master=input_frame, placeholder_text='Type URL here', width=200)
url_entry.grid(row=0, column=0, columnspan=2, padx=12, pady=5, sticky="ew")

selection_var = StringVar()
selection_var.set('a')
audio_radio = customtkinter.CTkRadioButton(master=input_frame, text="Audio", variable=selection_var, value="a")
video_radio = customtkinter.CTkRadioButton(master=input_frame, text="Video", variable=selection_var, value="v")

audio_radio.grid(row=1, column=0, padx=40, pady=5, sticky="e")
video_radio.grid(row=1, column=1, padx=35, pady=5, sticky="w")

download_button = customtkinter.CTkButton(master=input_frame, text="Download", font=('', 15), command=download_video)
download_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

update_status_label = customtkinter.CTkLabel(master=input_frame, text='', font=('Helvetica', 12), fg_color='transparent', text_color=('#ffffff'))
update_status_label.grid(row=3, column=0, columnspan=2, pady=10, sticky="ew")

def bottom_checkbox():
    global update_checkbox, check_var
    check_var = customtkinter.StringVar(value=os.environ['CHECK_UPDATE'])
    update_checkbox = customtkinter.CTkCheckBox(master=input_frame, text='Check for updates', font=("Helvetica", 12), command=save_checkbox_value, variable=check_var, onvalue="ON", offvalue="OFF")
    update_checkbox.grid(row=4, column=0, sticky="w")

bottom_checkbox()

app.grid_columnconfigure(0, weight=1)
app.grid_rowconfigure(0, weight=1)

if update_checkbox.get() == 'ON':
    disable_download_button()
    update_status_label.configure(text='Checking for updates...', font=('', 15))
    app.after(100, lambda: check_for_updates())

app.mainloop()
