import re
import api.spotify as spotify_client
import api.genius as genius_client
import api.translate as translate_client
import requests
import time

def main():
    print("+-----------------------------------------------------------------------------------+")
    print("|                                                                                   |")
    print("| Welcome to Lyringo!                                                               |")
    print("|                                                                                   |")
    print("| Learn new languages by translating your favourite songs.                          |")
    print("|                                                                                   |")
    print("+-----------------------------------------------------------------------------------+")
    print("")
    print("+-----------------------------------------------------------------------------------+")
    print("|                                                                                   |")
    print("| There are two alternatives for selecting a song:                                  |")
    print("|                                                                                   |")
    print('| 1 - Let Lyringo choose a random song from your playlist.                          |')
    print('| 2 - Manually search for a song.                                                   |')
    print("|                                                                                   |")
    print("+-----------------------------------------------------------------------------------+")
    print("")

    # Keep asking until the user provides a valid choice (no default).
    while True:
        choice = input("Input (1 or 2): ").strip()
        if choice in ("1", "2"):
            break
        print("Invalid input. Please enter 1 or 2.")

    if choice == "2":
        # Manual entry: ask for title and artist and construct a minimal song dict
        print("")
        print("+-----------------------------------------------------------------------------------+")
        print("|                                                                                   |")
        print("| Search for your song, and make sure to type carefully.                            |")
        print("| A random song may be selected if your input is not recognized.                    |")
        print("|                                                                                   |")
        print("+-----------------------------------------------------------------------------------+")
        print("")
        track = input("Song title: ").strip()
        artist_input = input("Artist name: ").strip()
        if not track:
            print("No song title provided. Exiting.")
            return
        primary_artist = artist_input or ""
        print("")
        random_song = {"track_name": track, "artist_names": [primary_artist] if primary_artist else []}
        manual_mode = True
    else:
        # Playlist flow (default)
        token = spotify_client.get_token()
        print("")
        print("+-----------------------------------------------------------------------------------+")
        print("|                                                                                   |")
        print("| How to get the link of a playlist in Spotify:                                     |")
        print("|                                                                                   |")
        print("| 1. Go to your playlist and press the three dots.                                  |")
        print("| 2. Press 'Share' -> 'Copy playlist link'.                                         |")
        print("|                                                                                   |")
        print("+-----------------------------------------------------------------------------------+")
        print("")
        # Prompt until a plausible Spotify playlist link/URI is provided and a song can be fetched.
        while True:
            link = input("Paste your link here: ").strip()
            if not link:
                print("")
                print("Cmon bro................")
                print("")
                continue
            if not ("spotify" in link and ("playlist" in link or link.startswith("spotify:"))):
                print("")
                print("Invalid Spotify playlist link. Please try again.")
                print("")
                continue

            print("")
            print("+-----------------------------------------------------------------------------------+")
            print("|                                                                                   |")
            print("| Choosing a random song from your playlist...                                      |")
            print("|                                                                                   |")
            print("+-----------------------------------------------------------------------------------+")
            try:
                random_song = spotify_client.get_random_song_from_playlist(token, link)
            except Exception as e:
                print(f"Error reading playlist: {e}")
                print("Please check the link and your internet connection, then try again.")
                continue

            if not random_song:
                print("Could not find a song in that playlist. Try another playlist link.")
                continue

            track = random_song.get("track_name")
            artists = random_song.get("artist_names", [])
            primary_artist = artists[0] if artists else ""
            manual_mode = False
            break

    # Fetch lyrics and metadata (get_song_lyrics now returns a dict with
    # keys 'formatted' and 'language'). We prefer the language reported by
    # the provider instead of doing automatic detection.
    # Wrap the network call with retries so transient timeouts don't crash.
    lyrics_info = None
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            print("+-----------------------------------------------------------------------------------+")
            print("|                                                                                   |")
            print("| Searching for your song...                                                        |")
            print("|                                                                                   |")
            print("+-----------------------------------------------------------------------------------+")
            lyrics_info = genius_client.get_song_lyrics(track, primary_artist)
            break
        except requests.exceptions.Timeout:
            if attempt < max_attempts:
                print(f"Search timed out (attempt {attempt}/{max_attempts}). Retrying...")
                time.sleep(1.5 * attempt)
                continue
            else:
                print("Search timed out after multiple attempts. Please check your internet connection and try again later.")
                return
        except requests.exceptions.RequestException as e:
            print(f"Network error while searching for song: {e}")
            return
        except Exception as e:
            # Unexpected error from the lyrics provider; show a friendly message.
            print(f"Error while searching for song: {e}")
            return
    formatted_lyrics = None
    lyrics_language = None
    if isinstance(lyrics_info, dict):
        formatted_lyrics = lyrics_info.get("formatted")
        lyrics_language = lyrics_info.get("language")
    else:
        # fallback for older return shape
        formatted_lyrics = lyrics_info
    # Extract header (title — artist) and body once and reuse.
    header, body = translate_client._extract_header(formatted_lyrics or "")

    # If the user manually entered a song, provide clearer feedback.
    if 'manual_mode' in locals() and manual_mode:
        # If no lyrics/formatted output was returned, inform the user.
        if not formatted_lyrics or not (header or body.strip()):
            print("no song named that found")
            return

    # Display the song chosen by the program. Prefer the provider's header
    # (which contains the canonical title and artist) when available.
    if header:
        display_song = header
    else:
        display_song = f"{track} - {primary_artist}" if primary_artist else f"{track}"
    print("")
    print(f"Your song is: {display_song}")
    print("")

    #if lyrics_language:
        # convert returned code/name to a friendly display name
        #display = translate_client.code_to_display_name(lyrics_language)
        # print(f"The song is in {display}")
    #else:
        #print("Song language not provided by lyrics metadata.")
    
    print("+-----------------------------------------------------------------------------------+")
    print("|                                                                                   |")
    print("| What language do you want to translate the song to?                               |")
    print("|                                                                                   |")
    print("| e.g english, swedish, spanish...                                                  |")
    print("|                                                                                   |")
    print("+-----------------------------------------------------------------------------------+")
    print("")
    user_lang = input("Language: ").strip()
    print()
    # convert language name like "english" -> "en" using translate_client helper
    # convert language name like "english" -> "en" using translate_client helper
    code = translate_client.language_name_to_code(user_lang)
    if not code:
        # accept two-letter codes directly
        if len(user_lang) == 2 and user_lang.isalpha():
            code = user_lang.lower()
        else:
            print(f"'{user_lang}' is an unknown language, defaulting to English.")
            print("")
            code = "en"

    # make sure a song was actually chosen
    if not random_song:
        print("No song selected. Exiting.")
        return

    # Start the translation game: for each non-empty line in the lyrics body,
    # ask the user to type the translation into the chosen language. After the
    # user answers, show the correct translation and keep score.
    header, body = translate_client._extract_header(formatted_lyrics or "")
    lines = [line for line in body.splitlines()]

    def _normalize(s: str) -> str:
        # Lowercase, remove punctuation and collapse whitespace for comparison.
        if s is None:
            return ""
        s = s.lower()
        s = re.sub(r"[^a-z0-9\s]", "", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    total = 0
    score = 0
    
    print("+-----------------------------------------------------------------------------------+")
    print("|                                                                                   |")
    print("| How to play:                                                                      |")
    print("|                                                                                   |")
    print("| 1. Examine the displayed line of lyrics.                                          |")
    print("| 2. Try to translate to your chosen language, press ENTER when you are done.       |")
    print("| 3. Compare you answer with the actual translation.                                |")
    print("| 4. When you are done, press ENTER to display the next line of lyrics.             |")
    print("|                                                                                   |")
    print("| Leave blank to skip a line.                                                       |")
    print("| Press Ctrl+C to quit early.                                                       |")
    print("|                                                                                   |")
    print("|                                                                                   |")
    print("|                 +-----------------------------------------------+                 |")
    print("|                 | Press ENTER whenever you are ready to start!  |                 |")
    print("|                 | Remember that translations may be inaccurate. |                 |")
    print("|                 +-----------------------------------------------+                 |")
    print("|                                                                                   |")
    print("|                                                                                   |")
    print("+-----------------------------------------------------------------------------------+")
    # Wait for the user to press Enter before starting the game
    try:
        input("")
    except (KeyboardInterrupt, EOFError):
        print("\nInterrupted. Exiting.")
        return
    for orig in lines:
        orig_strip = orig.strip()
        if not orig_strip:
            # keep paragraph breaks but don't quiz blank lines
            continue

        total += 1
        print(f"\nOriginal:       {orig_strip}")
        answer = input("Translate:      ").strip()

        # Get the expected translation from the translate client.
        try:
            expected_full = translate_client.translate_song(orig_strip, code)
        except Exception:
            expected_full = orig_strip

        # extract body in case the translator wrapped headers
        _, expected_body = translate_client._extract_header(expected_full)

        print(f"Answer:         {expected_body}")
        # Wait for the user to press Enter before showing the next lyrics line.
        # This ensures a line-by-line flow: translate -> see correct answer -> press Enter -> next line.
        try:
            input("")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting the game.")
            break



if __name__ == "__main__":
    main()

# TODO Now that 2 works, fix 1.
