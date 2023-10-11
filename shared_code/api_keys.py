# These are mandatory for connecting to MariaDB
user_name = ""
db_password = ""
host_name = ""  # IP address of MariaDB instance
db_name = ""

# These three are optional and are only needed if you plan to use the temperature function
token = ""  # Home Assistant token
server_ip = ""  # IP address of Home Assistant instance
weather_api = ""  # OpenWeatherMap API key needed for temperature function

# These are for adding/retrieving plans from the calendar
calendar_username = ""  # CalDAV username
calendar_password = ""  # CalDAV password
nextcloud_url = ""  # Nextcloud URL for DAV functions, e.g., https://example.com/remote.php/dav

# This is not used in code, but you'll need to manually generate this token by running the 'anilist_api_get_token.py' file in the shared_code/anilist folder if you want to use anime/manga list functions
anilist_access_token = ""

# Required for using the anime/manga list function; obtain these from the AniList site
client_id = ""
client_secret = ""

# Path to the Langchain folder, e.g., 'C:\\example\\folder\\shiro_on_streamlit\\shared_code\\langchain_database\\'
path_to_langchain = ""
