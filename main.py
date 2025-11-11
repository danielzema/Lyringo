import spotify_client
import genius_client

def main():
    token = spotify_client.get_token()
    #print(genius_client.get_song_lyrics("PUNTO G", "Quevedo"))
    #print(spotify_client.search_for_artist(token, "nfeiwjfhwejlfowef"))
    random_song = spotify_client.get_random_song_from_playlist(token, "https://open.spotify.com/playlist/7DLEUo99U5nzyn0bvW0hD5?si=1543e8d7e82a44d7")

    track = random_song.get("track_name")
    artists = random_song.get("artist_names", [])
    primary_artist = artists[0]

    lyrics = genius_client.get_song_lyrics(track, primary_artist)
    print(lyrics)

if __name__ == "__main__":
    main()