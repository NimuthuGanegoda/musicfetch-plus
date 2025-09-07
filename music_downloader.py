
import os
import sys
import yt_dlp
import requests
from lyricsgenius import Genius
from spotdl import Spotdl

# Set your Genius API token here
GENIUS_API_TOKEN = "10225840"
genius = Genius(GENIUS_API_TOKEN)

def download_youtube_audio(url, output_dir="downloads"):
    os.makedirs(output_dir, exist_ok=True)
    ffmpeg_path = r"C:\\Tools\\ffmpeg-7.1.1-full_build\\bin\\ffmpeg.exe"
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'flac',
            'preferredquality': '0',
        }],
        'writethumbnail': False,
        'writeinfojson': False,
        'embedthumbnail': False,
        'ffmpeg_location': ffmpeg_path,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
    return info

def download_spotify_audio(url, output_dir="downloads"):
    os.makedirs(output_dir, exist_ok=True)
    spotdl = Spotdl(format='flac')
    print(f"Downloading from Spotify: {url}")
    result = spotdl.download(url)
    if not result:
        print("Download failed.")
        return None
    return result[0]['file_path']

def get_album_art(info, output_dir="downloads"):
    thumbnail_url = info.get('thumbnail')
    if thumbnail_url:
        print(f"Downloading album art from {thumbnail_url}")
        response = requests.get(thumbnail_url)
        content = response.content
        mime = response.headers.get('content-type', 'image/jpeg')
        print(f"Image MIME type: {mime}")
        # Convert WebP to JPEG for better compatibility
        if 'webp' in mime.lower():
            from PIL import Image
            from io import BytesIO
            img = Image.open(BytesIO(content))
            buffer = BytesIO()
            img.convert('RGB').save(buffer, format='JPEG')
            content = buffer.getvalue()
            mime = 'image/jpeg'
            print("Converted WebP to JPEG")
        filename = os.path.join(output_dir, f"{info['title']}_album_art.jpg")
        with open(filename, 'wb') as f:
            f.write(content)
        print(f"Saved album art to {filename}")
        return filename, mime
    else:
        print("No thumbnail URL found.")
    return None, None

def get_lyrics(song_title, artist=None):
    try:
        song = genius.search_song(song_title, artist)
        if song:
            return song.lyrics
    except Exception as e:
        print(f"Error fetching lyrics: {e}")
    return None

def main():
    url = input("Enter Spotify or YouTube/YouTube Music URL: ").strip()
    output_dir = os.path.join(os.getcwd(), "downloads")
    if "music.youtube.com" in url:
        print("WARNING: YouTube Music is not directly supported. Please use a regular YouTube link for best results.")
        print("Tip: Search for the same song on youtube.com and use that link instead.")
        return
    if "youtube.com" in url or "youtu.be" in url:
        info = download_youtube_audio(url, output_dir)
        print(f"Downloaded: {info['title']}")
        print(f"Artist: {info.get('artist', 'Unknown')}")
        print(f"Album: {info.get('album', 'Unknown')}")
        art_path, mime = get_album_art(info, output_dir)
        if art_path:
            print(f"Album art saved to: {art_path}")
        lyrics = get_lyrics(info['title'], info.get('artist'))
    elif "spotify.com" in url:
        file_path = download_spotify_audio(url, output_dir)
        if not file_path:
            sys.exit(1)
        # spotdl saves metadata in the filename and tags
        from mutagen.flac import FLAC
        audio = FLAC(file_path)
        title = audio.get('TITLE', ['Unknown'])[0]
        artist = audio.get('ARTIST', ['Unknown'])[0]
        album = audio.get('ALBUM', ['Unknown'])[0]
        pictures = audio.pictures
        album_art = pictures[0].data if pictures else None
        print(f"Downloaded: {title}")
        print(f"Artist: {artist}")
        print(f"Album: {album}")
        if album_art:
            art_path = os.path.join(output_dir, f"{title}_album_art.jpg")
            with open(art_path, 'wb') as f:
                f.write(album_art)
            print(f"Album art saved to: {art_path}")
            mime = 'image/jpeg'  # Assume JPEG for FLAC pictures
        lyrics = get_lyrics(title, artist)
    else:
        print("Unsupported URL. Please provide a Spotify or YouTube/YouTube Music link.")
        return
    # Embed album art and lyrics into the FLAC file
    from mutagen.flac import FLAC, Picture
    import time
    flac_file = None
    # Wait for FLAC file to appear (in case postprocessing is slow)
    for _ in range(20):  # Increased to 20 seconds
        flac_files = [f for f in os.listdir(output_dir) if f.lower().endswith('.flac')]
        if flac_files:
            # Use the newest FLAC file
            flac_file = os.path.join(output_dir, sorted(flac_files, key=lambda x: os.path.getmtime(os.path.join(output_dir, x)), reverse=True)[0])
            break
        time.sleep(1)
    if flac_file and os.path.exists(flac_file):
        try:
            print(f"Processing file: {flac_file}")
            audio = FLAC(flac_file)
            # Embed album art
            if 'art_path' in locals() and art_path and os.path.exists(art_path):
                with open(art_path, 'rb') as img:
                    image = Picture()
                    image.data = img.read()
                    image.type = 3
                    image.mime = mime or 'image/jpeg'
                    image.desc = 'Cover'
                    audio.clear_pictures()
                    audio.add_picture(image)
                print("Album art embedded.")
            else:
                print("Album art file not found or not set.")
            # Embed lyrics
            if lyrics:
                audio['LYRICS'] = lyrics
                print("Lyrics embedded.")
            else:
                print("No lyrics to embed.")
            audio.save()
            print(f"Embedded metadata into {flac_file}")
            # Keep the separate album art file
        except Exception as e:
            print(f"Failed to embed metadata: {e}")
    else:
        print("FLAC file not found for embedding. Please check the downloads folder.")

if __name__ == "__main__":
    main()
