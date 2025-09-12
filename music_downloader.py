
import os
import sys
import yt_dlp
import requests
from lyricsgenius import Genius
from spotdl import Spotdl

# Set your Genius API token here
GENIUS_API_TOKEN = "10225840"
genius = Genius(GENIUS_API_TOKEN)

def download_youtube_audio(url, output_dir="downloads", preferred_format="flac"):
    os.makedirs(output_dir, exist_ok=True)
    ffmpeg_path = r"C:\\Tools\\ffmpeg-7.1.1-full_build\\bin\\ffmpeg.exe"
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': preferred_format,
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

def download_spotify_audio(url, output_dir="downloads", preferred_format="flac"):
    os.makedirs(output_dir, exist_ok=True)
    spotdl = Spotdl(format=preferred_format)
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
    def input_cover_path():
        cover_path = input('Enter the Path to the album art (or press Enter to skip): ')
        if not cover_path:
            return None
        if os.path.isfile(cover_path) and (cover_path.endswith('png') or cover_path.endswith('jpg')):
            return cover_path
        else:
            print('Wrong Path Entered, TRY AGAIN!')
            return input_cover_path()

    def embed_custom_cover_art(audio_path, cover_path, format='mp3'):
        ext = format.lower()
        if cover_path:
            try:
                if ext == 'mp3':
                    from mutagen.mp3 import MP3
                    from mutagen.id3 import ID3, APIC, error
                    audio = MP3(audio_path, ID3=ID3)
                    try:
                        audio.add_tags()
                    except error:
                        pass
                    mime_type = 'image/png' if cover_path.endswith('png') else 'image/jpeg'
                    audio.tags.add(APIC(mime=mime_type, type=3, desc=u'Cover-Art', data=open(cover_path, 'rb').read()))
                    audio.save()
                    print("Custom cover art embedded in MP3.")
                elif ext == 'flac':
                    from mutagen.flac import FLAC, Picture
                    audio = FLAC(audio_path)
                    image = Picture()
                    image.data = open(cover_path, 'rb').read()
                    image.type = 3
                    image.mime = 'image/png' if cover_path.endswith('png') else 'image/jpeg'
                    image.desc = 'Cover-Art'
                    audio.clear_pictures()
                    audio.add_picture(image)
                    audio.save()
                    print("Custom cover art embedded in FLAC.")
                elif ext in ['m4a', 'alac', 'aac']:
                    from mutagen.mp4 import MP4, MP4Cover
                    audio = MP4(audio_path)
                    img_bytes = open(cover_path, 'rb').read()
                    cover = MP4Cover(img_bytes, imageformat=MP4Cover.FORMAT_JPEG if cover_path.endswith('jpg') else MP4Cover.FORMAT_PNG)
                    audio.tags['covr'] = [cover]
                    audio.save()
                    print("Custom cover art embedded in MP4-based file.")
                elif ext == 'ogg':
                    from mutagen.oggvorbis import OggVorbis
                    audio = OggVorbis(audio_path)
                    audio['metadata_block_picture'] = [open(cover_path, 'rb').read().hex()]
                    audio.save()
                    print("Custom cover art embedded in OGG.")
                elif ext == 'wma':
                    from mutagen.asf import ASF
                    audio = ASF(audio_path)
                    audio.pictures = [open(cover_path, 'rb').read()]
                    audio.save()
                    print("Custom cover art embedded in WMA.")
                elif ext == 'aiff':
                    from mutagen.aiff import AIFF
                    audio = AIFF(audio_path)
                    audio.pictures = [open(cover_path, 'rb').read()]
                    audio.save()
                    print("Custom cover art embedded in AIFF.")
                elif ext == 'wav':
                    print("Note: WAV format does not support embedded cover art with mutagen. Use FFmpeg for WAV cover art embedding.")
                else:
                    print(f"Custom cover art embedding not supported for format: {format}")
            except Exception as e:
                print(f"Failed to embed custom cover art: {e}")
    # Helper: Scrape and embed cover art
    # Removed Google Images scraping. Only user-supplied cover art is supported.
    device = input("What device is this song for? (e.g., Audi, iPhone, phone, PC, tablet): ").strip().lower()
    # Suggest formats based on device
    if device == "audi":
        allowed_formats = ["mp3", "wma", "m4a"]
        print("Audi supports: mp3, wma, m4a")
        preferred_format = ""
        while preferred_format not in allowed_formats:
            preferred_format = input(f"What is your preferred audio format? ({', '.join(allowed_formats)}): ").strip().lower()
            if preferred_format not in allowed_formats:
                print(f"Please choose one of: {', '.join(allowed_formats)}")
    elif device == "iphone":
        allowed_formats = ["aac", "alac", "mp3", "wav", "aiff"]
        print("iPhone supports: aac, alac, mp3, wav, aiff")
        preferred_format = ""
        while preferred_format not in allowed_formats:
            preferred_format = input(f"What is your preferred audio format? ({', '.join(allowed_formats)}): ").strip().lower()
            if preferred_format not in allowed_formats:
                print(f"Please choose one of: {', '.join(allowed_formats)}")
    elif device == "android":
        allowed_formats = ["aac", "flac", "mp3", "ogg", "wav"]
        print("Android supports: aac, flac, mp3, ogg, wav")
        preferred_format = ""
        while preferred_format not in allowed_formats:
            preferred_format = input(f"What is your preferred audio format? ({', '.join(allowed_formats)}): ").strip().lower()
            if preferred_format not in allowed_formats:
                print(f"Please choose one of: {', '.join(allowed_formats)}")
    else:
        preferred_format = "mp3"
        print("Other device detected. Defaulting to mp3 format.")
    url = input("Enter Spotify or YouTube/YouTube Music URL: ").strip()
    output_dir = input("Enter the destination folder for downloads (press Enter for default 'downloads'): ").strip()
    if not output_dir:
        output_dir = os.path.join(os.getcwd(), "downloads")
    else:
        output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    print(f"Selected device: {device}")
    print(f"Preferred format: {preferred_format}")
    if "music.youtube.com" in url:
        print("WARNING: YouTube Music is not directly supported. Please use a regular YouTube link for best results.")
        print("Tip: Search for the same song on youtube.com and use that link instead.")
        return
    converted_file_path = None
    if "youtube.com" in url or "youtu.be" in url:
        info = download_youtube_audio(url, output_dir, preferred_format)
        print(f"Downloaded: {info['title']}")
        print(f"Artist: {info.get('artist', 'Unknown')}")
        print(f"Album: {info.get('album', 'Unknown')}")
        lyrics = get_lyrics(info['title'], info.get('artist'))
        # Find the downloaded FLAC file
        from glob import glob
        flac_files = glob(os.path.join(output_dir, '*.flac'))
        if flac_files:
            source_file = flac_files[-1]
            # Convert to preferred format if needed
            if preferred_format != 'flac':
                converted_file_path = os.path.splitext(source_file)[0] + f'.{preferred_format}'
                ffmpeg_path = r"C:\\Tools\\ffmpeg-7.1.1-full_build\\bin\\ffmpeg.exe"
                os.system(f'"{ffmpeg_path}" -y -i "{source_file}" "{converted_file_path}"')
                print(f"Converted to {preferred_format}: {converted_file_path}")
            else:
                converted_file_path = source_file
            # Ask user for custom cover art
            cover_path = input_cover_path()
            if cover_path:
                embed_custom_cover_art(converted_file_path, cover_path, preferred_format)
    elif "spotify.com" in url:
        file_path = download_spotify_audio(url, output_dir, preferred_format)
        if not file_path:
            sys.exit(1)
        # spotdl saves metadata in the filename and tags
        from mutagen.flac import FLAC
        audio = FLAC(file_path)
        title = audio.get('TITLE', ['Unknown'])[0]
        artist = audio.get('ARTIST', ['Unknown'])[0]
        album = audio.get('ALBUM', ['Unknown'])[0]
        print(f"Downloaded: {title}")
        print(f"Artist: {artist}")
        print(f"Album: {album}")
        lyrics = get_lyrics(title, artist)
        # Convert to preferred format if needed
        if preferred_format != 'flac':
            converted_file_path = os.path.splitext(file_path)[0] + f'.{preferred_format}'
            ffmpeg_path = r"C:\\Tools\\ffmpeg-7.1.1-full_build\\bin\\ffmpeg.exe"
            os.system(f'"{ffmpeg_path}" -y -i "{file_path}" "{converted_file_path}"')
            print(f"Converted to {preferred_format}: {converted_file_path}")
        else:
            converted_file_path = file_path
        # Ask user for custom cover art
        cover_path = input_cover_path()
        if cover_path:
            embed_custom_cover_art(converted_file_path, cover_path, preferred_format)
    else:
        print("Unsupported URL. Please provide a Spotify or YouTube/YouTube Music link.")
        return
    # ...existing code...

if __name__ == "__main__":
    main()
