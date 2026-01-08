import customtkinter as ctk
from tkinter import *
from tkinter import filedialog, messagebox
import requests
import urllib.request
import threading
import os
from dotenv import *
from downloader import Downloader
from utils import sanitize_filename
import yt_dlp
import math

class AppGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")

        self.title('dyv_gui v1.3')
        self.geometry('400x300')

        self.downloader = Downloader()
        self.build_gui()

        self.env_path = os.path.join(os.environ['userprofile'], 'Documents', '.env')
        self.load_env()

    def build_gui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.input_frame = ctk.CTkFrame(master=self, fg_color='transparent')
        self.input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.input_frame.grid_rowconfigure((0, 1, 2, 3, 4), weight=1)

        self.input_frame.grid_columnconfigure((0, 1), weight=1)

        self.url_entry = ctk.CTkEntry(master=self.input_frame, placeholder_text='Type URL here', width=200)
        self.url_entry.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

        self.selection_var = StringVar(value='a')
        ctk.CTkRadioButton(master=self.input_frame, text="Audio", variable=self.selection_var, value="a") \
            .grid(row=1, column=0, padx=40, pady=5, sticky="e")
        ctk.CTkRadioButton(master=self.input_frame, text="Video", variable=self.selection_var, value="v") \
            .grid(row=1, column=1, padx=35, pady=5, sticky="w")

        self.download_button = ctk.CTkButton(master=self.input_frame, text="Download", font=('', 15), command=lambda: threading.Thread(target=self.download_video).start())
        self.download_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")


        self.check_update_label = ctk.CTkLabel(master=self.input_frame, text='', font=('Helvetica', 15), fg_color='transparent', text_color=('#ffffff'))
        self.check_update_label.grid(row=3, column=0, columnspan=2, pady=10, sticky="ew")

    def update_progress(self, d):
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes', 0)
            downloaded_bytes = d.get('downloaded_bytes', 0)

            if 'fragment_index' in d and d['fragment_index'] > 0:
                progress = math.floor(int(d["fragment_index"])/int(d["fragment_count"])*100)
                self.check_update_label.configure(text=f'Downloading {d["fragment_index"]}/{d["fragment_count"]} ({progress}%)')

            if total_bytes > 0:
                progress = math.floor(int(downloaded_bytes)/int(total_bytes)*100)
                self.check_update_label.configure(text=f'Downloading ({progress}%)')

        elif d['status'] == 'finished':
            self.check_update_label.configure(text="Finishing...")
        else:
            self.check_update_label.configure(text=d['status'])

    def download_video(self):
        print("Download button clicked")
        url = self.url_entry.get()
        selection = self.selection_var.get()

        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL.")
            return

        try:
            info = yt_dlp.YoutubeDL().extract_info(url, download=False)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to extract info: {e}")
            return

        file_extension = '.mp3' if selection == 'a' else '.mp4'
        file_types = [('MP3 Files', '*.mp3')] if selection == 'a' else [('MP4 Files', '*.mp4')]
        save_path = filedialog.asksaveasfilename(defaultextension=file_extension, 
                                                 filetypes=file_types, 
                                                 initialfile=sanitize_filename(info['title']))
        if not save_path:
            return

        self.check_update_label.configure(text="Starting download...")
        self.download_button.configure(state="disabled")

        thread = threading.Thread(
            target=self._download_thread,
            args=(url, selection, save_path, file_extension)
        )
        thread.start()

    def _download_thread(self, url, selection, save_path, file_extension):
        try:
            self.downloader.download(url, selection, save_path, file_extension, progress_hook=self.update_progress)
            self.check_update_label.configure(text="Download complete.")
            messagebox.showinfo("Success", f'Downloaded to {save_path}')
        except FileExistsError:
            self.check_update_label.configure(text="File already exists.")
            messagebox.showwarning("Warning", "File already exists.")
        except Exception as e:
            self.check_update_label.configure(text="Download failed.")
            messagebox.showerror("Error", str(e))
        finally:
            self.download_button.configure(state="normal")

    def load_env(self):
        if not os.path.isfile(self.env_path):
            with open(self.env_path, 'w') as f:
                f.write("CHECK_UPDATE='ON'")
        load_dotenv(dotenv_path=self.env_path)

    def save_checkbox_value(self):
        set_key(dotenv_path=self.env_path, key_to_set="CHECK_UPDATE", value_to_set=self.update_checkbox_status.get())
        if self.update_checkbox_status.get() == 'ON':
            self.check_for_updates()

    def bottom_checkbox(self):
        self.update_checkbox_status = ctk.StringVar(value=os.environ['CHECK_UPDATE'])
        self.update_checkbox = ctk.CTkCheckBox(master=self.input_frame, text='Check for updates', font=("Helvetica", 12), command=self.save_checkbox_value, variable=self.update_checkbox_status, onvalue="ON", offvalue="OFF")
        self.update_checkbox.grid(row=4, column=0, sticky="w")


    def check_for_updates(self):
        try:
            current_version = 'v1.4'
            url = 'https://raw.githubusercontent.com/Panos-Jr/yt-dlp-gui/main/version.txt'
            response = requests.get(url)
            
            if response.status_code == 200:
                latest_version = response.text.strip()
                if latest_version == current_version:
                    print('no updates')
                    messagebox.showinfo(title='No updates', message='No update was found.')
                    self.check_update_label.configure(text='')
                    self.enable_download_button()

                else:
                    update = messagebox.askokcancel(title='Update Found!', message='We\'ve found a newer update, would you like to download it?')
                    if update:
                        self.check_update_label.configure(text='Starting Update')
                        self.start_update(latest_version)
                    self.enable_download_button()
                    self.check_update_label.configure(text='')
            else:
                messagebox.showwarning(title='Checking for Updates', message='An error occured while checking for updates.')

        except Exception as e:
            messagebox.showwarning(title='Checking for Updates', message='An error occured while checking for updates.')


    def start_update(self, version):
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

    def disable_download_button(self):
        self.download_button.configure(state="disabled")

    def enable_download_button(self):
        self.download_button.configure(state="normal")

if __name__ == "__main__":
    app = AppGUI()
    app.bottom_checkbox()
    if app.update_checkbox.get() == 'ON':
        app.disable_download_button()
        app.check_update_label.configure(text='Checking for updates...', font=('', 15))
        app.after(100, lambda: app.check_for_updates())
    app.mainloop()
