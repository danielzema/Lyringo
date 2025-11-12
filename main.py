import re
import spotify_client
import genius_client
import translate_client

def main():
    print("+-----------------------------------------------------------------------------------+")
    print("|                                                                                   |")
    print("| Welcome to Lyringo!                                                               |")
    print("|                                                                                   |")
    print("| Learn new languages by translating your favourite songs.                          |")
    print("|                                                                                   |")
    print("+-----------------------------------------------------------------------------------+")
    print("")
    print("There are two alternatives for selecting a song:")
    print("")
    print('Input: "1" - Let Lyringo choose a random song from your playlist')
    print('Input: "2" - Manually search for a song')
    print("")
    choice = input("Input: ").strip()

    if choice == "2":
        # Manual entry: ask for title and artist and construct a minimal song dict
        track = input("Song title: ").strip()
        artist_input = input("Artist name: ").strip()
        if not track:
            print("No song title provided. Exiting.")
            return
        primary_artist = artist_input or ""
        random_song = {"track_name": track, "artist_names": [primary_artist] if primary_artist else []}
    else:
        # Playlist flow (default)
        token = spotify_client.get_token()
        print("")
        print("Paste the link here and press ENTER:")
        link = input()
        print("")
        print("+-----------------------------------------------------------------------------------+")
        print("|                                                                                   |")
        print("| Choosing a random song from your playlist...                                      |")
        print("|                                                                                   |")
        random_song = spotify_client.get_random_song_from_playlist(token, link)
        track = random_song.get("track_name")
        artists = random_song.get("artist_names", [])
        primary_artist = artists[0] if artists else ""

    # Fetch lyrics and metadata (get_song_lyrics now returns a dict with
    # keys 'formatted' and 'language'). We prefer the language reported by
    # the provider instead of doing automatic detection.
    lyrics_info = genius_client.get_song_lyrics(track, primary_artist)
    formatted_lyrics = None
    lyrics_language = None
    if isinstance(lyrics_info, dict):
        formatted_lyrics = lyrics_info.get("formatted")
        lyrics_language = lyrics_info.get("language")
    else:
        # fallback for older return shape
        formatted_lyrics = lyrics_info

    #if lyrics_language:
        # convert returned code/name to a friendly display name
        #display = translate_client.code_to_display_name(lyrics_language)
        # print(f"The song is in {display}")
    #else:
        #print("Song language not provided by lyrics metadata.")
    
    print("")
    print("+-----------------------------------------------------------------------------------+")
    print("|                                                                                   |")
    print("| What language do you want to translate the song to?                               |")
    print("|                                                                                   |")
    print("| e.g english, swedish, spanish...                                                  |")
    print("|                                                                                   |")
    print("+-----------------------------------------------------------------------------------+")
    print("")
    print("Type your language below: ")
    user_lang = input().strip()
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
    print("| 2. Try to translate to your chosen language (press ENTER when you are done).      |")
    print("| 3. Compare you answer with the actual translation.                                |")
    print("| 4. Press ENTER to display the next line of lyrics.                                |")
    print("|                                                                                   |")
    print("| Leave blank to skip a line.                                                       |")
    print("| Press Ctrl+C to quit early.                                                       |")
    print("|                                                                                   |")
    print("+-----------------------------------------------------------------------------------+")
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
            input("Press Enter to continue...")
        except (KeyboardInterrupt, EOFError):
            print("\nInterrupted. Exiting the game.")
            break



if __name__ == "__main__":
    main()