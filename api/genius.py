import lyricsgenius
import os 
import re
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("GENIUS_ACCESS_TOKEN")
genius = lyricsgenius.Genius(token, verbose=False)

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
        return {"formatted": None, "language": None}
    
    # Use the song object's metadata when available
    title = getattr(song, "title", song_title) or song_title
    artist_name = getattr(song, "artist", artist) or artist
    lyrics = getattr(song, "lyrics", "") or ""

    # Clean up footer noise
    lyrics = lyrics.strip()
    lyrics = clean_lyrics(lyrics)

    # Nicely formatted output
    formatted = f"{title} — {artist_name}\n" + "-" * (len(title) + 3 + len(artist_name)) + "\n\n" + lyrics
    # Try to extract a language field from the song object if present. The
    # lyricsgenius Song object varies across versions; check a few likely
    # attribute names and also inspect internal dicts if available.
    language = None
    # common attribute names on Song objects
    for attr in ("language", "primary_language", "language_code", "lyrics_language", "lang"):
        try:
            val = getattr(song, attr, None)
        except Exception:
            val = None
        if val:
            language = val
            break

    # fallback: inspect internals (some Song implementations expose a _body or __dict__)
    if not language:
        try:
            body = None
            if hasattr(song, "_body") and isinstance(getattr(song, "_body"), dict):
                body = getattr(song, "_body")
            elif hasattr(song, "__dict__"):
                # sometimes the raw JSON is stored in an attribute like _json or _body
                d = getattr(song, "__dict__")
                # look for common container names
                for key in ("_body", "_json", "_response", "body"):
                    if key in d and isinstance(d[key], dict):
                        body = d[key]
                        break

            if isinstance(body, dict):
                for key in ("language", "lang", "language_code"):
                    if key in body and body.get(key):
                        language = body.get(key)
                        break
                # lastly, try any value whose key contains 'lang'
                if not language:
                    for k, v in body.items():
                        if "lang" in k.lower() and v:
                            language = v
                            break
        except Exception:
            # ignore extraction errors and leave language as None
            pass

    return {"formatted": formatted, "language": language}
