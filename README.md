# SpotifyRecommendation

Use Spotify API to create a list of n recommended songs using another playlist.
Use UV to initialize the project with a virtual environment: https://docs.astral.sh/uv/

---
macOS and Linux install

`wget -qO- https://astral.sh/uv/install.sh | sh`

Windows

`powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex`

---


Initialize the project using `uv init` within the directory for the repository.

## Spotify API Key
This project uses the `dotenv` library to load the API credentials into the program to then be used for accessing the Spotify API. To get your own credentials, make an app on the spotify [website](https://developer.spotify.com/)
![{48E3169A-271C-4B25-8CCF-7A3829BDB065}](https://github.com/user-attachments/assets/10c335fb-cf39-4f60-8d40-edd46dda80ce)

Then copy your Client ID and Secret into a your `.env` file in the directory of your project in the form:
```
CLIENT_ID="XXX"
CLIENT_SECRET="YYY"
SECRET_KEY="ZZZ"
```
Your secret key can be a randomly generated 64 byte string.

You can then run the program using `uv run ./main.py`

### Note
There is still a known bug with the database connection closing imporperly such that data cannot be accessed. Current workaround is to reinitialize it with fake data.

Second bug is that the recommender cannot be initialized with an empty DataFrame. If your database is empty, copy the `example.db` database and rename it to `lyrics.db`.
