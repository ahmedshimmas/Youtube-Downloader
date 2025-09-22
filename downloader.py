import yt_dlp
import argparse
import sys

def list_formats(url):
    """Fetch available video formats for the given URL"""
    ydl_opts = {"quiet": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = info.get("formats", [])
        video_formats = []
        for f in formats:
            if f.get("vcodec") != "none" and f.get("ext") == "mp4":
                res = f.get("format_note") or f.get("resolution")
                fps = f.get("fps", "")
                acodec = f.get("acodec", "none")
                has_audio = acodec != "none"
                video_formats.append({
                    "format_id": f["format_id"],
                    "resolution": res,
                    "fps": fps,
                    "has_audio": has_audio
                })
        return video_formats, info["title"]

def download_video(url, resolution, out_dir):
    """Download the video at given resolution"""
    formats, title = list_formats(url)

    # Try to find the requested resolution
    chosen_format = None
    for f in formats:
        if f["resolution"] == resolution:
            chosen_format = f["format_id"]
            break

    if not chosen_format:
        print(f"❌ Resolution {resolution} not found. Available options:")
        for f in formats:
            audio_status = "🎵+Audio" if f["has_audio"] else "🎥 Video-only"
            print(f"- {f['resolution']} ({audio_status})")
        sys.exit(1)

    ydl_opts = {
        "format": f"{chosen_format}+bestaudio/best",  # ensures audio
        "outtmpl": f"{out_dir}/%(title)s.%(ext)s",
        "merge_output_format": "mp4"
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        print(f"✅ Download complete: {info['title']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YouTube Video Downloader CLI")
    parser.add_argument("--url", required=True, help="YouTube video URL")
    parser.add_argument("--res", required=True, help="Resolution (e.g. 360p, 720p, 1080p)")
    parser.add_argument("--out", default="videos", help="Output directory (default: videos)")

    args = parser.parse_args()

    download_video(args.url, args.res, args.out)