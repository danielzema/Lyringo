import spotify_client
import genius_client

def main():
    token = spotify_client.get_token()
    #print(genius_client.get_song_lyrics("PUNTO G", "Quevedo"))
    print(spotify_client.search_for_artist(token, "nfeiwjfhwejlfowef"))

if __name__ == "__main__":
    main()