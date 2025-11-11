import lyricsgenius
import os 
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("GENIUS_ACCESS_TOKEN")
genius = lyricsgenius.Genius(token)

# Look up lyrics for a given artist and song
def get_song_lyrics(song_title, artist):
    song = genius.search_song(song_title, artist)
    if song:
        lyrics = genius.lyrics(song)
        return lyrics
    else: 
        return (f"Lyrics for {song_title} not found")
