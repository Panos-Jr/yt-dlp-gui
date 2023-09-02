import os
import yt_dlp

url = 'https://youtu.be/10Mj_Pd9pfU'

info = yt_dlp.YoutubeDL().extract_info(url, download=False)
title = info['title']
desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
download_folder = os.path.join(desktop, 'downloads')

def find_file(download_folder, file_name):
    files_in_folder = os.listdir(download_folder)
    for file_ident in files_in_folder:
        name, ext = os.path.splitext(file_ident)
        if file_name == name:
            return file_ident
        

if __name__ == '__main__':
    file_name = find_file(download_folder, title)
    if file_name:
        print('Found it!', file_name)