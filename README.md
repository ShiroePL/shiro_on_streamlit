# 1. ShiroAi-chan Takes Over Streamlit 🌸

### Introducing My Anime Waifu Assistant: ShiroAi-chan
Harness the power of ChatGPT API to bring your very own AI-powered anime waifu to life! ShiroAi-chan is a customizable AI assistant designed to offer both written and vocal responses in an endearing manner.

### Her Personality 💖
ShiroAi-chan embodies the persona of a virtual cat-girl fond of anime, manga, light novels, and games. While her personality aligns with my interests, you can easily adapt her character to suit yours. Her dialogues are generated through prompts to the ChatGPT API, offering various 'personality modes' such as 'programmer god,' where she assists with coding queries.

### Platform-Specific Versions of ShiroAi-chan 🖥️📱⌚
1. [Streamlit repo] - The web version, built using [Streamlit].
2. [Desktop repo] - The desktop version featuring a Tkinter-based GUI.
3. [Wearos repo] - The mobile version, optimized for WearOS watches. This version runs on [FastAPI] inside a Docker container. (This version is most personalized, as I was focused on my Galaxy Watch 4)

### GUI
![Screenshot](pictures/gui.png)

- [Features](#Features)
- [Screenshots](#Screenshots)
- [Configuration](#Configuration)


## Features
### 1. Writing ✍️
* ShiroAi-chan utilizes the [ChatGPT API] to respond as an adorable AI cat-girl.

### 2. Her Memory 😍
* MariaDB stores her memories. She remembers the last 4 questions (configurable for more).
* She can also "read" PDFs stored in a Chroma Vector Database, using Huggingface Embeddings.
* Every 'persona' setting has its own table in database and can reset it with button.
  
### 3. Voice 🎤
*  Leveraging Microsoft Azure TTS, she can speak in both English and Polish. English is cuter.

### 4. Communication 🗨️

* Type your query into the input field or use built-in TTS on mobile devices.

### 5. AI Features 🤖 ( examples in screenshots)
  She employs a Langchain Agent to choose tools, which include:

  * Retrieving the last 10 anime/manga list entries from Anilist. (ask about it with agent mode checkbox ON or press button)
  * Updating anime/manga on last 10 anime/manga list, using human-like sentences. 
  * Vector database searches for document-based queries. You can add full pdf books, or other documents, and ask questions to this documents then she will take relevant parts from documents, and answer questions analyzing that parts.
  * Calendar functions to add and retrieve events. Add events based on what information you give her (in normal human sentence!) and retrieve information about events for specified days. (accuracy is like 85%, it's hard to have 100% if event is too detailed) This function is using Caldav, I am using nextcloud API for it.
  * Weather and home sensor data, along with quirky commentary. It's more my personal function, because you need to change code of home assistant API and have sensor in the first place.
  
To use tools, you can just start question with 'agent mode' or 'agent:' or check agent mode check.

### 6. Shared Code 🔄
* The 'shared_code' folder contains code that is common across all versions of ShiroAi-chan.
  * link to repository: https://github.com/ShiroePL/shiro_shared_code


## Screenshots
#### Normal Talking Mode
* Talk to her just like you would with anyone else!

<table>
  <tr>
    <td>
      <br>
      <img src="pictures/shiro_introduces_herself.png" width="500">
    </td>
    <td>
      <br>
      <img src="pictures/normal_talk.png" width="500">
    </td>
  </tr>
</table>
Calendar Functions 🗓️
<table>
  <tr>
    <td>
      <strong>Adding a New Event:</strong><br>
      <img src="pictures/added_plan.png" width="450">
    </td>
    <td>
      <strong>Retrieving Plans for a Specified Day:</strong><br>
      <img src="pictures/retriving_plans.png" width="450">
    </td>
  </tr>
</table>


Vector Database Functions 📚
<table>
  <tr>
    <td>
      <strong>Saving PDFs to Vector Database:</strong><br>
      <img src="pictures/saved_pdf.png" width="450">
    </td>
    <td>
      <strong>PDF Fragment:</strong><br>
      <img src="pictures/pdf_fragment.png" width="600">
      <strong>Asking Questions Based on PDF Content:</strong><br>
      <img src="pictures/vector_db_answer.png" width="600">
    </td>
  </tr>
</table>



Anime/Manga List 📋
* See your latest watched/read anime/manga.

<table>
  <tr>
    <td>
      <br>
      <img src="pictures/anime_list.png" width="450">
    </td>
    <td>
      <br>
      <img src="pictures/manga_list.png" width="450">
    </td>
  </tr>
</table>

* Update list.

<table>
  <tr>
    <td>
      <br>
      <img src="pictures/update_list.png" width="500">
    </td>
    <td>
      <img src="pictures/update_proof.png" width="450">
      <br>
      <strong>It worked, from Anilist site 😊</strong><br><br>
      <img src="pictures/update_on_site.png" width="450">
    </td>
  </tr>
</table>

Room Temperature 🌡️
* Check out the current temperature of your room.

<img src="pictures/temperature_example.png" width="500">





## Configuration
### 8. Configuration and Installation 🛠️



1. You need to add and configure api_keys.py file inside 'shared_code' folder: 

```python
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

# You'll need to manually generate this token by running the 'anilist_api_get_token.py' file in the shared_code/anilist folder if you want to use anime/manga list functions
anilist_access_token = ""

# Required for using the anime/manga list function; obtain these from the AniList site
client_id = ""
client_secret = ""

# Path to the Langchain folder, e.g., 'C:\\example\\folder\\shiro_on_streamlit\\shared_code\\langchain_database\\'
path_to_langchain = ""
```

2. To make sure the application functions properly, you need to add certain API keys to your system's environment variables:
  *  OpenAI API Key:
     *  Add your OpenAI API key to the environment variables and name it ```OPENAI_API_KEY```
  *  Azure Cognitive Speech 
     *  If you intend to use Text-to-Speech (TTS) functionalities, add ```SPEECH_REGION``` and ```SPEECH_KEY``` to the environment variables. Instructions: https://learn.microsoft.com/en-us/azure/ai-services/multi-service-resource?pivots=azportal&tabs=windows#get-the-keys-for-your-resource

3. To configure the device type for PyTorch in the ``shared_code\langchain_database\langchain_vector_db_queries.py`` file, you'll need to modify the device argument in the HuggingFaceInstructEmbeddings function. Here are the steps:

     * Open the file ``shared_code\langchain_database\langchain_vector_db_queries.py``.

     * Locate the following block of code:

   ```python
   if type == "pdf":
       instructor_embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-large", 
                                                           model_kwargs={"device": "cuda"})
   ```


     * Change the value of the device argument depending on your setup:

        * If you have an Nvidia GPU and have installed the CUDA version of PyTorch, you can leave the device value as ``"cuda"``.
        * If you don't have a GPU, or haven't installed the CUDA version of PyTorch, change the device value to ``"cpu"``.
     
4. Installing Dependencies on Windows
   ```bash
   pip install -r requirements.txt
   ```
    #### Python Version Compatibility

    * The code has been tested on Python 3.9.0.
    * If you're using a different Python version, you may need to modify the requirements.txt file to ensure package compatibility.
    * Specifically, Python 3.10.0 may require different package versions, so you might have to install them manually if the provided requirements.txt file doesn't work for you.
  
5. #### Running the Program
   * To launch the application locally, execute the following command in your terminal:
    ```bash
    streamlit run main.py
    ```
   * Accessing from Other Devices on the Same Network
  
      If you want to access the application from a mobile device or another computer within the same local network, you can specify the IP address of your machine using the --server.address flag:
   ```bash
   streamlit run main.py --server.address xxx.xxx.xxx.xxx
   # Replace xxx.xxx.xxx.xxx with the actual IP address of your machine.
   ```

  
## Links 

[ChatGPT API] : https://openai.com/blog/introducing-chatgpt-and-whisper-apis

[Azure TTS] : https://azure.microsoft.com/en-us/products/cognitive-services/text-to-speech/

[Streamlit repo] : https://github.com/ShiroePL/shiro_on_streamlit

[Desktop repo] : https://github.com/ShiroePL/shiro_chan_desktop

[Wearos repo] : https://github.com/ShiroePL/Shiro-AI-Chan-in-container

[ChatGPT API]: https://openai.com/blog/introducing-chatgpt-and-whisper-apis
[Azure TTS]: https://azure.microsoft.com/en-us/products/cognitive-services/text-to-speech/
[Streamlit]: https://streamlit.io/
[Streamlit repo]: https://github.com/ShiroePL/shiro_on_streamlit
[Desktop repo]: https://github.com/ShiroePL/shiro_chan_desktop
[Wearos repo]: https://github.com/ShiroePL/Shiro-AI-Chan-in-container