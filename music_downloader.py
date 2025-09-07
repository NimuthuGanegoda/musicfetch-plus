import os
import sys
from spotdl import Spotdl
from geniuslyrics import Genius
import requests

def download_song(url):
    spotdl = Spotdl()
    print(f"Downloading: {url}")
    result = spotdl.download(url)
    if not result:
        print("Download failed.")
        return None
    return result[0]['file_path']

def get_metadata(file_path):
    # spotdl saves metadata in the filename and tags
    from mutagen.easyid3 import EasyID3
    from mutagen.id3 import ID3
    audio = EasyID3(file_path)
    tags = ID3(file_path)
    metadata = {
        'title': audio.get('title', ['Unknown'])[0],
        'artist': audio.get('artist', ['Unknown'])[0],
        'album': audio.get('album', ['Unknown'])[0],
        'album_art': None
    }
    # Extract album art
    for tag in tags.values():
        if tag.FrameID == 'APIC':
            metadata['album_art'] = tag.data
            break
    return metadata

def save_album_art(album_art, output_path):
    if album_art:
        with open(output_path, 'wb') as f:
            f.write(album_art)
        print(f"Album art saved to {output_path}")
    else:
        print("No album art found.")

def get_lyrics(title, artist):
    genius = Genius()
    lyrics = genius.search_song(title, artist)
    if lyrics:
        return lyrics.lyrics
    return "Lyrics not found."

def main():
    url = input("Enter Spotify or YouTube URL: ").strip()
    file_path = download_song(url)
    if not file_path:
        sys.exit(1)
    metadata = get_metadata(file_path)
    print("Metadata:", metadata)
    if metadata['album_art']:
        save_album_art(metadata['album_art'], 'album_art.jpg')
    lyrics = get_lyrics(metadata['title'], metadata['artist'])
    with open('lyrics.txt', 'w', encoding='utf-8') as f:
        f.write(lyrics)
    print("Lyrics saved to lyrics.txt")

if __name__ == "__main__":
    main()
