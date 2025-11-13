from dotenv import load_dotenv
import os 
import base64
import requests
import json
import random 

load_dotenv()

spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID")
spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

REDIRECT_URI = "http://localhost:5000/callback"
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
SPOTIFY_SEARCH_URL = "https://api.spotify.com/v1/search"

# Get access token
def get_token():
    auth_string = spotify_client_id + ":" + spotify_client_secret 
    # Base64 requires bytes
    auth_bytes = auth_string.encode("utf-8")
    # HTTP headers can only contain text, so we turn back to string
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")
    # Send request to: 
    # HTTP POST headers: 
    headers = {
        "Authorization": "Basic " + auth_base64, 
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    result = requests.post(SPOTIFY_TOKEN_URL, headers=headers, data=data)

    # Parse result to get token
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token 

def search_for_artist(token, artist_name: str):
    params = {
        "q": artist_name, 
        "type": "artist",
        "limit": 1
    }
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(SPOTIFY_SEARCH_URL, params = params, headers = headers) 
    if response.status_code != 200:
        print(f"Request failed with status code: {response.status_code}")
        return None
    result = response.json()

    # Return first found artist
    artist_field = result["artists"]["items"][0]
    if artist_field:
        artist = artist_field.get("name")
        # For some reason when you mash your keyboard (i.e "hfeifehkjfhdie") it 
        # always defaults to "Hooja".
        if artist == "Hooja":
            return None
        return artist
    else: 
        print(f"No artist named {artist_name} found")

# Extract the needed part to search for the songs in a playlist
# Helper function to get_playlist_by_link
def extract_playlist_id(playlist_link):    
    if "playlist/" in playlist_link:
        # Take everything after "playlist/"
        #xxxxxxxxxxxxxxxx?si=0ec7299ffa1a419a
        part = playlist_link.split("playlist/")[1]
        # Remove the ?si= part
        #xxxxxxxxxxxxxxxx
        playlist_id = part.split("?")[0]
        return playlist_id

    # Other format of url from API
    elif "spotify:playlist:" in playlist_link:
        return playlist_link.split("spotify:playlist:")[1]
    else:
        # Assume the user already pasted the ID directly
        return playlist_link.strip()
    
def get_playlist_by_link(token, playlist_link):
    link = extract_playlist_id(playlist_link)
    url = f"https://api.spotify.com/v1/playlists/{link}/tracks"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    params = {
        # Tracks name, artists name and next page
        "fields": "items(track(name, artists(name))),next",
        "limit": 100
    } 

    result = requests.get(url, headers=headers, params=params)
    data = result.json()

    all_tracks_in_playlist = []

    while True:
        for item in data.get("items", []):
            track = item.get("track")
            if not track: 
                # Skip unavailable tracks
                continue

            track_name = track.get("name")
            artist_names = [artist.get("name") for artist in track.get("artists", []) if artist.get("name")]
            all_tracks_in_playlist.append({
                "track_name": track_name, "artist_names": artist_names
            })

        next_url = data.get("next")
        if not next_url:
            break 

        resp = requests.get(next_url, headers=headers)
        data = resp.json()

    return all_tracks_in_playlist

# Choose a random song from a playlist
def get_random_song_from_playlist(token, playlist_link):
    # Get all songs from a playlist
    all_tracks = get_playlist_by_link(token, playlist_link)

    # No songs in playlist
    if not all_tracks:
        print("No tracks in this playlist")
        return None 
    
    random_song = random.choice(all_tracks)

    # Announce which song was chosen
    track_name = random_song.get("track_name") or "Unknown track"
    artist_names = random_song.get("artist_names", [])
    artists = ", ".join(artist_names) if artist_names else "Unknown artist"
    print("")
    print(f"Chosen song: {track_name} - {artists}")
    print("")
    return random_song

# TODO Write a function that pads Chosen song to the right width
# TODO Add a flag when the entire song is over asking to play the game again
# TODO Instead of sending request to tgranslate after user inputs, send request before and then print