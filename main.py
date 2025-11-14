import re
import api.spotify as spotify_client
import api.genius as genius_client
import api.translate as translate_client
import requests
import time

import cli

def main():

    cli.welcome()

    # Keep asking until the user provides a valid choice (no default).
    while True:
        choice = input("Input (1 or 2): ").strip()
        if choice in ("1", "2"): break
        cli.print_in_box("Invalid input. Please enter 1 or 2.")

    if choice == "2":
        # Manual entry: ask for title and artist and construct a minimal song dict
        cli.print_in_box([
            "Search for your song, and make sure to type carefully.",
            "A random song may be selected if your input is not recognized.",
        ])
        track = input("Song title: ").strip()
        artist_input = input("Artist name: ").strip()
        if not track:
            cli.print_in_box("No song title provided. Exiting.")
            return
        primary_artist = artist_input or ""
        print("")
        random_song = {"track_name": track, "artist_names": [primary_artist] if primary_artist else []}
        manual_mode = True
    else:
        # Playlist flow (default)
        token = spotify_client.get_token()
        cli.print_in_box([
            "How to get the link of a playlist in Spotify:",
            "",
            "1. Go to your playlist and press the three dots.",
            "2. Press 'Share' -> 'Copy playlist link'.",
        ])
        # Prompt until a plausible Spotify playlist link/URI is provided and a song can be fetched.
        while True:
            link = input("Paste your link here: ").strip()
            if not link:
                cli.print_in_box("Paste a link here. Please try again.")
                print("")
                continue
            if not ("spotify" in link and ("playlist" in link or link.startswith("spotify:"))):
                cli.print_in_box("Invalid Spotify playlist link. Please try again.")
                print("")
                continue
            cli.print_in_box("Choosing a random song from your playlist...")
            try:
                random_song = spotify_client.get_random_song_from_playlist(token, link)
            except Exception as e:
                cli.print_in_box([
                    f"Error reading playlist: {e}",
                    "Please check the link and your internet connection, then try again."
                ])
                continue

            if not random_song:
                cli.print_in_box("Could not find a song in that playlist. Try another playlist link.")
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
    max_attempts = 3

    # If we're in playlist mode and the chosen song has no lyrics, try a few
    # other random songs from the same playlist before giving up.
    no_lyrics_attempts = 0
    max_no_lyrics_attempts = 3

    while True:
        lyrics_info = None
        for attempt in range(1, max_attempts + 1):
            try:
                # Only show the "Searching for your song..." banner when the user
                # manually searched (option 2). For playlist flow we avoid the
                # duplicate-looking prompt but still fetch lyrics.
                if 'manual_mode' in locals() and manual_mode:
                    print("Searching for your song...")
                lyrics_info = genius_client.get_song_lyrics(track, primary_artist)
                break
            except requests.exceptions.Timeout:
                if attempt < max_attempts:
                    cli.print_in_box(f"Search timed out (attempt {attempt}/{max_attempts}). Retrying...")
                    time.sleep(1.5 * attempt)
                    continue
                else:
                    cli.print_in_box("Search timed out after multiple attempts. Please check your internet connection and try again later.")
                    return
            except requests.exceptions.RequestException as e:
                cli.print_in_box(f"Network error while searching for song: {e}")
                return
            except Exception as e:
                # Unexpected error from the lyrics provider; show a friendly message.
                cli.print_in_box(f"Error while searching for song: {e}")
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

        # If there are no lyrics in the returned formatted text, decide what
        # to do next. For manual searches we keep previous behaviour and
        # quit. For playlist flow, try another random song (up to a limit).
        if not (body and body.strip()):
            if 'manual_mode' in locals() and manual_mode:
                # Manual search: if nothing was returned at all, the song was
                # not found. If a formatted header exists but the body is empty,
                # report that there are no lyrics.
                if not formatted_lyrics:
                    cli.print_in_box("no song named that found")
                    return
                else:
                    cli.print_in_box("no lyrics, quitting")
                    return
            else:
                # Playlist flow: inform the user and try another random song.
                display_song = header if header else (f"{track} - {primary_artist}" if primary_artist else f"{track}")
                cli.print_in_box(f"{display_song} has no lyrics. Choosing another random song...")
                no_lyrics_attempts += 1
                if no_lyrics_attempts >= max_no_lyrics_attempts:
                    # After several attempts, ask the user for another playlist
                    # link so they can provide a playlist that actually has
                    # lyrics. Allow the user to press ENTER to quit.
                    cli.print_in_box("Tried several songs in this playlist but couldn't find lyrics.")
                    cli.print_in_box("Please paste another playlist link (or press ENTER to exit):")
                    while True:
                        print("")
                        new_link = input("link: ").strip()
                        if not new_link:
                            cli.print_in_box("No new playlist provided. Exiting.")
                            return
                        if not ("spotify" in new_link and ("playlist" in new_link or new_link.startswith("spotify:"))):
                            cli.print_in_box("Invalid Spotify playlist link. Please try again or press ENTER to quit.")
                            continue
                        # try to select a random song from the newly provided playlist
                        try:
                            new_song = spotify_client.get_random_song_from_playlist(token, new_link)
                        except Exception as e:
                            cli.print_in_box(f"Error reading new playlist: {e}")
                            cli.print_in_box("Please try another link or press ENTER to quit.")
                            continue

                        if not new_song:
                            cli.print_in_box("Could not find a song in that playlist. Try another playlist link or press ENTER to quit.")
                            continue

                        # Adopt the new playlist and reset attempts
                        link = new_link
                        random_song = new_song
                        track = random_song.get("track_name")
                        artists = random_song.get("artist_names", [])
                        primary_artist = artists[0] if artists else ""
                        no_lyrics_attempts = 0
                        break

                # attempt to pick another random song from the same playlist
                try:
                    # `token` and `link` are set in the playlist branch above.
                    new_song = spotify_client.get_random_song_from_playlist(token, link)
                except Exception as e:
                    cli.print_in_box(f"Error selecting another song from playlist: {e}")
                    return

                if not new_song:
                    cli.print_in_box("Could not find another song in the playlist. Exiting.")
                    return

                random_song = new_song
                track = random_song.get("track_name")
                artists = random_song.get("artist_names", [])
                primary_artist = artists[0] if artists else ""
                # loop back and try fetching lyrics for the new song
                continue

        # If we reach here body contains lyrics — exit the retry loop and
        # continue to the gameplay.
        break

    # Display the song chosen by the program. Prefer the provider's header
    # (which contains the canonical title and artist) when available.
    if header:
        display_song = header
    else:
        display_song = f"{track} - {primary_artist}" if primary_artist else f"{track}"
    print("")
    cli.print_in_box(f"Your song is: {display_song}")
    print("")
    cli.print_in_box([
        "What language do you want to translate the song to?",
        "",
        "e.g english, swedish, spanish...",
    ])
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
            cli.print_in_box(f"'{user_lang}' is an unknown language, defaulting to English.")
            print("")
            code = "en"

    # make sure a song was actually chosen
    if not random_song:
        cli.print_in_box("No song selected. Exiting.")
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
    
    cli.print_in_box([
        "How to play:",
        "",
        "1. Examine the displayed line of lyrics.",
        "2. Try to translate to your chosen language, press ENTER when you are done.",
        "3. Compare you answer with the actual translation.",
        "4. When you are done, press ENTER to display the next line of lyrics.",
        "",
        "Leave blank to skip a line.",
        "Press Ctrl+C to quit early.",
    ])
    cli.print_in_box([
        "Press ENTER whenever you are ready to start!",
        "Remember that translations may be inaccurate.",
    ])
    # Wait for the user to press Enter before starting the game
    try:
        input("")
    except (KeyboardInterrupt, EOFError):
        cli.print_in_box("Interrupted. Exiting.")
        return
    for orig in lines:
        orig_strip = orig.strip()
        if not orig_strip:
            # keep paragraph breaks but don't quiz blank lines
            continue

        total += 1
        cli.print_in_box(f"Original: {orig_strip}")
        answer = input("Translate: ").strip()

        # Get the expected translation from the translate client.
        try:
            expected_full = translate_client.translate_song(orig_strip, code)
        except Exception:
            expected_full = orig_strip

        # extract body in case the translator wrapped headers
        _, expected_body = translate_client._extract_header(expected_full)

        cli.print_in_box(f"Answer: {expected_body}")
        # Wait for the user to press Enter before showing the next lyrics line.
        # This ensures a line-by-line flow: translate -> see correct answer -> press Enter -> next line.
        try:
            input("")
        except (KeyboardInterrupt, EOFError):
            print("Exiting the game.")
            break



if __name__ == "__main__":
    main()

# TODO Now that 2 works, fix 1.
