# SpotifyRecommendation
Use Spotify API to create a list of n recommended songs using another playlist.
Use UV to initialize the project with a virtual environment: https://docs.astral.sh/uv/
---
macOS and Linux install
`wget -qO- https://astral.sh/uv/install.sh | sh`
Windows
`powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex`
---
Initialize the project using `uv init` within the directory for the repository then run the program using `uv run ./main.py`

### Note
There is still a known bug with the database connection closing imporperly such that data cannot be accessed. Current workaround is to reinitialize it with fake data.
Second bug is that the recommender cannot be initialized with an empty DataFrame.