import yt_dlp
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import ttkbootstrap as tb
from PIL import Image, ImageTk
import requests, re
from io import BytesIO
import threading

download_folder = ""
thumbnail_img = None
download_thread = None
cancel_download_flag = False

# ---------------- Functions ---------------- #
def choose_folder():
    global download_folder
    folder = filedialog.askdirectory()
    if folder:
        download_folder = folder
        folder_label.config(text=f"Download to: {download_folder}")

def strip_ansi(text):
    return re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', text)

def my_hook(d):
    global cancel_download_flag
    if cancel_download_flag:
        raise yt_dlp.utils.DownloadError("Download cancelled by user.")

    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '0.0%')
        speed = d.get('_speed_str', 'N/A')
        eta = d.get('_eta_str', 'N/A')

        clean_text = f"Downloading... {percent} | Speed: {speed} | ETA: {eta}"
        progress_label.config(text=strip_ansi(clean_text))

        try:
            progress = float(percent.strip('%'))
            progress_bar['value'] = progress
        except:
            progress_bar['value'] = 0

        root.update_idletasks()

    elif d['status'] == 'finished':
        progress_label.config(text="✅ Download complete, finalizing...")
        progress_bar['value'] = 100

def fetch_video_info():
    url = url_entry.get()
    if not url:
        return

    ydl_opts = {'quiet': True, 'skip_download': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title_label.config(text=info.get('title', 'Unknown Title'))

            thumb_url = info.get('thumbnail')
            if thumb_url:
                response = requests.get(thumb_url, stream=True)
                img_data = response.content
                pil_img = Image.open(BytesIO(img_data)).resize((200, 120))
                global thumbnail_img
                thumbnail_img = ImageTk.PhotoImage(pil_img)
                thumbnail_label.config(image=thumbnail_img)
    except Exception:
        title_label.config(text="❌ Could not fetch video info")

def download_video_thread():
    global cancel_download_flag
    cancel_download_flag = False
    url = url_entry.get()
    selection = quality_var.get()

    if not url:
        messagebox.showerror("Error", "Please enter a YouTube URL.")
        return
    if not download_folder:
        messagebox.showerror("Error", "Please select a download folder first.")
        return

    format_map = {
        "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
        "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
        "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "1080p": "bestvideo[height<=1080]+bestaudio+bestaudio/best[height<=1080]",
        "Best": "bestvideo+bestaudio/best"
    }

    if selection == "Audio Only (MP3)":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{download_folder}/%(title)s.%(ext)s',
            'progress_hooks': [my_hook],
            'postprocessors': [
                {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}
            ],
            'noprogress': True
        }
    else:
        ydl_opts = {
            'format': format_map.get(selection, format_map["Best"]),
            'merge_output_format': 'mp4',
            'outtmpl': f'{download_folder}/%(title)s.%(ext)s',
            'progress_hooks': [my_hook],
            'noprogress': True
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        messagebox.showinfo("Success", f"🎉 Download completed!\nSaved to: {download_folder}")
    except Exception as e:
        if str(e) == "Download cancelled by user.":
            progress_label.config(text="❌ Download cancelled")
        else:
            messagebox.showerror("Error", f"Download failed:\n{str(e)}")
    finally:
        progress_bar['value'] = 0

def start_download():
    global download_thread
    if download_thread and download_thread.is_alive():
        messagebox.showwarning("Download in Progress", "A download is already running!")
        return
    download_thread = threading.Thread(target=download_video_thread)
    download_thread.start()

def cancel_download():
    global cancel_download_flag
    if download_thread and download_thread.is_alive():
        cancel_download_flag = True
    else:
        messagebox.showinfo("No Active Download", "There is no download to cancel.")

# ---------------- GUI ---------------- #
root = tb.Window(themename="darkly")
root.title("YouTube Video Downloader")
root.geometry("650x650")

style = root.style  # TkBootstrap style object

# URL input
ttk.Label(root, text="YouTube URL:").pack(pady=5)
url_entry = ttk.Entry(root, width=70)
url_entry.pack(pady=5)

fetch_btn = ttk.Button(root, text="Fetch Video Info", command=fetch_video_info, bootstyle="info")
fetch_btn.pack(pady=5)

# Title + thumbnail preview
title_label = ttk.Label(root, text="Video title will appear here", font=("Arial", 12, "bold"))
title_label.pack(pady=5)

thumbnail_label = ttk.Label(root)
thumbnail_label.pack(pady=5)

# Quality dropdown
ttk.Label(root, text="Select Quality:").pack(pady=5)
quality_var = tk.StringVar(value="Best")
quality_dropdown = ttk.Combobox(
    root,
    textvariable=quality_var,
    values=["360p", "480p", "720p", "1080p", "Best", "Audio Only (MP3)"]
)
quality_dropdown.pack(pady=5)

# Folder selection
folder_btn = ttk.Button(root, text="Choose Download Folder", command=choose_folder)
folder_btn.pack(pady=5)
folder_label = ttk.Label(root, text="No folder selected")
folder_label.pack(pady=5)

# Theme selection
available_themes = style.theme_names()
selected_theme = tk.StringVar(value="darkly")

def change_theme(event):
    style.theme_use(selected_theme.get())

ttk.Label(root, text="Select Theme:").pack(pady=5)
theme_dropdown = ttk.Combobox(
    root,
    textvariable=selected_theme,
    values=available_themes,
    state="readonly",
    width=20
)
theme_dropdown.bind("<<ComboboxSelected>>", change_theme)
theme_dropdown.pack(pady=5)

# Progress bar + label
progress_bar = ttk.Progressbar(root, length=500, mode='determinate')
progress_bar.pack(pady=10)
progress_label = ttk.Label(root, text="Progress will appear here")
progress_label.pack()

# Download & Cancel buttons
buttons_frame = ttk.Frame(root)
buttons_frame.pack(pady=10)

download_btn = ttk.Button(buttons_frame, text="Download", command=start_download, bootstyle="success")
download_btn.pack(side=tk.LEFT, padx=5)

cancel_btn = ttk.Button(buttons_frame, text="Cancel Download", command=cancel_download, bootstyle="danger")
cancel_btn.pack(side=tk.LEFT, padx=5)

root.mainloop()
