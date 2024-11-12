import customtkinter
from tkinter import *
from tkinter import filedialog
from tkinter import ttk, messagebox
import os
import re
import yt_dlp
import threading
import math
import requests
import urllib.request
from dotenv import *
import sys
import ffmpeg

customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("dark-blue")

progress_bar = None
status = None
status_label = None
check_var = None
update_checkbox = None
count = 0
env_path = os.path.join(os.environ['userprofile'], 'Documents', '.env')

if not os.path.isfile(env_path):
    with open(env_path, 'w') as f:
        f.write('CHECK_UPDATE=\'ON\'')
load_dotenv(dotenv_path=env_path)

def bottom_checkbox():
    global update_checkbox, check_var
    check_var = customtkinter.StringVar(value=os.environ['CHECK_UPDATE'])
    update_checkbox = customtkinter.CTkCheckBox(master=input_frame, text='Check for updates', font=("Helvetica", 12), command=save_checkbox_value, variable=check_var, onvalue="ON", offvalue="OFF")
    update_checkbox.grid(row=4, column=0, sticky="w")

def save_checkbox_value():
    global check_var, bottom_checkbox, env_path
    set_key(dotenv_path=env_path, key_to_set="CHECK_UPDATE", value_to_set=check_var.get())
    if update_checkbox.get() == 'ON':
        check_for_updates()

def is_valid_youtube_url(url):
    youtube_regex = r'^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+$'
    return re.match(youtube_regex, url)

def init_progress_bar():
    global progress_bar
    progress_bar = customtkinter.CTkProgressBar(input_frame, orientation=HORIZONTAL, width=400, mode="determinate")
    progress_bar.grid(row=3, column=0, padx=10, pady=10, columnspan=2, sticky="ew")
    progress_bar.set(0)

def progress_hook(d):
    global status, status_label, progress_bar, count

    if not count:
        init_progress_bar()
        status_label.configure(text='')


    if d['status'] == 'downloading':
        total_bytes = d.get('total_bytes', 0)
        downloaded_bytes = d.get('downloaded_bytes', 0)

        if 'fragment_index' in d and d['fragment_index'] > 0:
            progress = math.floor(int(d["fragment_index"])/int(d["fragment_count"])*100)
            status = f'Downloading {d["fragment_index"]}/{d["fragment_count"]} ({progress}%)'
            count +=1
            progress_bar.set(progress/100)

        if total_bytes > 0:
            progress = math.floor(int(downloaded_bytes)/int(total_bytes)*100)
            status = f'Downloading ({progress}%)'
            count +=1
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
    global check_update_label
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
    global check_update_label
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
                check_update_label.configure(text='')
                enable_download_button()
            else:
                update = messagebox.askokcancel(title='Update Found!', message='We\'ve found a newer update, would you like to download it?')
                if update:
                    check_update_label.configure(text='Starting Update')
                    start_update(latest_version)
                enable_download_button()
                check_update_label.configure(text='')
        else:
            messagebox.showwarning(title='Checking for Updates', message='An error occured while checking for updates.')

    except Exception as e:
        messagebox.showwarning(title='Checking for Updates', message='An error occured while checking for updates.')

def update_status_labels():
    global input_frame, status_label
    status_label = customtkinter.CTkLabel(master=input_frame, text="", font=("Helvetica", 15))
    status_label.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

ILLEGAL_CHARACTERS = r'[\\/:*?"<>|{}$!\'"&%`@+=,;]'

def sanitize_filename(filename):
    sanitized = re.sub(ILLEGAL_CHARACTERS, '', filename)

    sanitized = re.sub(r'[^\x00-\x7F]+', '', sanitized)

    sanitized = re.sub(r'_+', '_', sanitized).strip('_')
    
    return sanitized

def remux_to_target_format(input_file, output_file):
    try:
        (
            ffmpeg.input(input_file)
            .output(output_file)
            .run()
        )
        os.remove(input_file)
    except Exception as e:
        messagebox.showerror("Remuxing Error", f"Failed to remux the file: {e}")

def download_media(url, selection):
    global my_menu, progress_bar, status_label, count
    try:
        count = 0
        update_checkbox.grid_forget()
        update_status_labels()
        status_label.configure(text='Starting download...')
        info = yt_dlp.YoutubeDL().extract_info(url, download=False)
        title = info['title']
        title += '-audio' if selection == 'a' else '-video'

        title = sanitize_filename(title)
        
        file_extension = '.mp3' if selection == 'a' else '.mp4'
        file_types = [('MP3 Files', '*.mp3')] if selection == 'a' else [('MP4 Files', '*.mp4')]
        save_path = filedialog.asksaveasfilename(defaultextension=file_extension, 
                                                 filetypes=file_types, 
                                                 initialfile=title)
        print(save_path)
        if not save_path:
            enable_download_button()
            status_label.configure(text='')
            messagebox.showinfo("Cancelled", "Download cancelled by user.")
            return
        
        ydl_opts = {
            'format': 'bestaudio/best' if selection == 'a' else 'bestvideo+bestaudio/best',
            'progress_hooks': [progress_hook],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
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
        
        ydl.download([url])
        
        downloaded_file = find_downloaded_file(save_path)
        
        print('we got it', downloaded_file)

        user_chosen_extension = os.path.splitext(save_path)[1]

        if downloaded_file:
            status_label.configure(text=f"Remuxing to {user_chosen_extension}")
            remux_to_target_format(downloaded_file, save_path)

        messagebox.showinfo("Success", f'File saved to {os.path.dirname(save_path)} as {os.path.basename(save_path).split('/')[-1]}')
        progress_bar.grid_remove()
        status_label.destroy()
        enable_download_button()
        bottom_checkbox()
    except Exception as e:
        messagebox.showerror("Error", f"An download error occurred: {e}")
            
def find_downloaded_file(base_name):
    folder = os.path.dirname(base_name)
    for files in os.listdir(folder):
        if os.path.join(folder, files) == base_name:
            return None
        if os.path.splitext(files)[0] == os.path.splitext(os.path.basename(base_name).split('/')[-1])[0]:
            return os.path.join(folder, files)

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
app.title('dyv_gui v1.3')
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

check_update_label = customtkinter.CTkLabel(master=input_frame, text='', font=('Helvetica', 12), fg_color='transparent', text_color=('#ffffff'))
check_update_label.grid(row=3, column=0, columnspan=2, pady=10, sticky="ew")

bottom_checkbox()

app.grid_columnconfigure(0, weight=1)
app.grid_rowconfigure(0, weight=1)

if update_checkbox.get() == 'ON':
    disable_download_button()
    check_update_label.configure(text='Checking for updates...', font=('', 15))
    app.after(100, lambda: check_for_updates())

app.mainloop()
