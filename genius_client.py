import lyricsgenius
import os 
import re
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("GENIUS_ACCESS_TOKEN")
genius = lyricsgenius.Genius(token)

def clean_lyrics(lyrics):
    if not lyrics:
        return ""
    # Remove lines that are only [bracketed] or (parenthetical)
    lyrics = re.sub(r'^\s*\[.*?\]\s*$','', lyrics, flags=re.MULTILINE)
    lyrics = re.sub(r'^\s*\(.*?\)\s*$','', lyrics, flags=re.MULTILINE)
    # Remove common footer markers if still present
    for marker in ["You might also like", "Embed"]:
        if marker in lyrics:
            lyrics = lyrics.split(marker)[0]
    # Collapse multiple blank lines to a single blank line
    lyrics = re.sub(r'\n\s*\n+', '\n\n', lyrics)
    return lyrics.strip()


# Look up lyrics for a given artist and song
def get_song_lyrics(song_title, artist):
    song = genius.search_song(song_title, artist)
    if not song:
        return (f"Lyrics for {song_title} not found")
    
    # Use the song object's metadata when available
    title = getattr(song, "title", song_title) or song_title
    artist_name = getattr(song, "artist", artist) or artist
    lyrics = getattr(song, "lyrics", "") or ""

    # Clean up footer noise
    lyrics = lyrics.strip()
    lyrics = clean_lyrics(lyrics)
    
    # Nicely formatted output
    formatted = f"{title} — {artist_name}\n" + "-" * (len(title) + 3 + len(artist_name)) + "\n\n" + lyrics
    return formatted
