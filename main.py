from datetime import datetime
import streamlit as st
from better_profanity import profanity
from shared_code.langchain_database.langchain_vector_db_queries import search_db_with_llm_response, save_to_db
from shared_code.calendar_functions.test_wszystkiego import add_event_from_shiro, retrieve_plans_for_days
import base64
import pandas as pd
import shared_code.connect_to_phpmyadmin as connect_to_phpmyadmin
import request_voice_tts
import shared_code.chatgpt_api
from PIL import Image
import shared_code.anilist.anilist_api_requests as anilist_api_requests
from shared_code.shiro_agent import CustomToolsAgent
from shared_code.home_assistant import ha_api_requests, open_weather_api
from st_chat_message import message
import re

conn = None
tts_or_not = False
show_history_variable = False
name = "normal"
agent_reply = ""
agent_mode_variable = False
search_vector_db_checkbox = False
update_anime_or_manga_list = False

# Store the initial value of widgets in session state
if "visibility" not in st.session_state:
    st.session_state.visibility = "visible"
    st.session_state.disabled = False

def agent_shiro(query):
    agent = CustomToolsAgent()
    final_answer = agent.run(query)
    return final_answer

def autoplay_audio(file_path: str):
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio autoplay="true">
            <source src="data:audio/wav;base64,{b64}" type="audio/wav">
            </audio>
            """
        st.markdown(
            md,
            unsafe_allow_html=True,
        )

def autoplay_question(file_path: str):
    autoplay_audio(file_path)

@st.cache_data
def autoplay_beep(file_path: str):
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio autoplay="true">
            <source src="data:audio/wav;base64,{b64}" type="audio/wav">
            </audio>
            """
        st.markdown(
            md,
            unsafe_allow_html=True,
        )


def retrieve_chat_history_from_database():
    history = connect_to_phpmyadmin.retrieve_chat_history_from_database("normal")
    return history


#@st.cache_data
def check_user_in_database(name):
    connect_to_phpmyadmin.check_user_in_database(name)
    history = connect_to_phpmyadmin.retrieve_chat_history_from_database(name)
    return history


def show_answer_in_chat(answer, user_question):
    st.session_state.messages.append({"role": "user", "content": user_question})
    
    if isinstance(answer, dict) and 'Summary' in answer and 'Description' in answer:
        formatted_answer = f"**Summary:** {answer['Summary']}<br>" \
                           f"**Description:** {answer['Description']}<br>" \
                           f"**Date:** {answer['Date']}<br>" \
                           f"**End Date:** {answer['End Date']}"
        st.session_state.messages.append({"role": "assistant", "content": formatted_answer})
    else:
        st.session_state.messages.append({"role": "assistant", "content": answer})



def add_anilist_to_db(type):
    
    media_list,_ = anilist_api_requests.get_10_newest_entries("ANIME")
    query = f"show my {type} list"
    database_messages =  check_user_in_database(name)

    connect_to_phpmyadmin.insert_message_to_database(name, query, media_list, database_messages) #insert to Azure DB to user table    
    connect_to_phpmyadmin.add_pair_to_general_table(name, media_list) #to general table with all  questions and answers

# for anime and manga list
def format_as_table(data_str, type:str):
    """Format the data as a table with 3 columns.

    type is anime or manga"""
    entries = data_str.split('\n')
    table_data = []
    pattern = r'^romaji_title:(.*), id:(\d+), read_chapters:(.*)$' if type == "manga" else r'^romaji_title:(.*), id:(\d+), watched_episodes:(.*)$'
    
    for entry in entries:
        if entry.strip():  # Exclude empty strings
            match = re.search(pattern, entry.strip())
            if match:
                title = match.group(1)
                id_str = match.group(2)
                read_chapters = match.group(3)
                #table_data.append({"Title": title, "ID": id_str, "Read Chapters": read_chapters}) if type == "manga" else table_data.append({"Title": title, "ID": id_str, "Watched Episodes": read_chapters})
                if type == "manga":
                    table_data.append({"Title": title, "ID": id_str, "Read Chapters": read_chapters})
                else:
                    table_data.append({"Title": title, "ID": id_str, "Watched Episodes": read_chapters})

    return table_data


def parse_event_info(event_str):
    pattern = r'summary: (.*?)\ndescription: (.*?)\ndate: (.*?)\nend_date: (.*)'
    match = re.search(pattern, event_str)
    if match:
        summary = match.group(1)
        description = match.group(2)
        date = match.group(3)
        end_date = match.group(4)
        return {
            "Summary": summary,
            "Description": description,
            "Date": date,
            "End Date": end_date
        }
    else:
        return None


st.title("Shiro AI Chan 😊")

user_question = st.chat_input("I'm Shiro! Ask me anything!") # placeholder in " " ## chat input for asking question

selected_language = st.sidebar.selectbox(
    'What language should i speak?',
    ('English', 'Polish')
)

with st.sidebar:
    
    my_bar = st.progress(0) #progress bar 
    coll1, coll2 = st.columns(2)
    print("___checkboxes status___")
    with coll1:
        voice_on_off = st.checkbox('Voice on/off')
        if voice_on_off:
            tts_or_not = True
            print("tts checkbox: ON")
        else:
            print("tts checkbox: OFF")
    with coll2:
        agent_mode = st.checkbox('agent_mode on/off')
        if agent_mode:
            agent_mode_variable = True
            print("agent mode checkbox ON")
        else:
            print("agent mode checkbox OFF")    

    col25, col26 = st.columns(2)

    with col25:
        search_vector_db_checkbox = st.checkbox('search vector db')
        if search_vector_db_checkbox:
            search_vector_db_checkbox = True
            print("search vector db checkbox ON")
        else:
            print("search vector db checkbox OFF")
    with col26:
        update_anime_or_manga_list = st.checkbox('update manga/anime')
        if update_anime_or_manga_list:
            update_anime_or_manga_list = True
            print("update manga/anime ON")
        else:
            print("update manga/anime OFF")

    print("___checkboxes status END___")
    
    col3, col4, col5 = st.columns(3)

    with col3:
        anime_button = st.button("show anime history")

    with col4:
        manga_button = st.button("show manga history")

    with col5:
        history_in_db_button = st.button("show history of chatting")

    col6, col7, col8 = st.columns(3)

    with col6:
        clean_history_button = st.button('clean history')

    with col7:
        show_room_temp_button = st.button('show room temp')

    # with col8:
    #     add_text_to_db = st.button('add text to vector db') # to do, not needed now
    with col8:
        
        introduction_button = st.button('What can you do?') ##############to change to introduciton of shiro

    

        # Create a file uploader widget
    uploaded_file = st.file_uploader("Choose a PDF file you want to add to vector db", type=["pdf"])

   



    # Create a submit button
    if st.button('Submit File to vector db'):
        my_bar.progress(10, text="Saving file to disk...")
        if uploaded_file is not None:
            # Get the file's bytes
            bytes_data = uploaded_file.read()
            file_name = uploaded_file.name.replace(".pdf", "")
            # Define the location to save the file
            save_path = f"./shared_code/langchain_database/pdfs/{uploaded_file.name}"  # Replace 'your_file.pdf' with your preferred filename

            # Save the file
            with open(save_path, "wb") as f:
                f.write(bytes_data)

            st.success(f"File saved to {uploaded_file.name}")
        else:
            st.warning("No file uploaded")

        my_bar.progress(50, text="Saving text to vector db...")
        save_to_db("pdf", None, file_name)
        my_bar.progress(100, text=f"Saved pdf {uploaded_file.name} to vector db!")
        


        # shiro avatar at the end of sidebar
    image = Image.open('pictures/avatar_shiro.png') # doesnt work but i dont know why
    st.image(image)



if anime_button:
    my_bar.progress(30, text="getting data from anilist...")
    media_list,_ = anilist_api_requests.get_10_newest_entries("ANIME")
    table_data = format_as_table(media_list, "anime")

        # Create a DataFrame from the table data
    df = pd.DataFrame(table_data)

    show_answer_in_chat(df,"Can you show me my anime list?")
    add_anilist_to_db("anime")
    my_bar.progress(100, text="Here's your list!")
    

if manga_button:
    my_bar.progress(30, text="getting data from anilist...")
    media_list,_ = anilist_api_requests.get_10_newest_entries("MANGA")
    table_data = format_as_table(media_list, "manga")

    # Create a DataFrame from the table data
    df = pd.DataFrame(table_data)
   
    show_answer_in_chat(df, "Can you show me my manga list?")
    add_anilist_to_db("manga")
    my_bar.progress(100, text="Here's your list!")

if history_in_db_button:
    history = check_user_in_database(name)
    

if show_room_temp_button:
    database_messages =  check_user_in_database(name)
    query = "what temperature is in my room?"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S %A")
    query = f"[current time: {current_time}] {query}"
    # use function chain to add event to calendar
    answer_from_ha = ha_api_requests.room_temp()
    print("answer from api: " + answer_from_ha)
    outside_temp =open_weather_api.current_temperature()

    
    query2 = f"[current time: {current_time}] Madrus: {query}. shiro: Retriving informations from her sensors... Done! Info from sensors:{answer_from_ha}°C. Weather outside: {outside_temp}°C.| (please say °C in your answer) | Shiro:"
    database_messages.append({"role": "user", "content": query2})
            
    print("messages: " + str(database_messages))
    
    personalized_answer, prompt_tokens, completion_tokens, total_tokens = shared_code.chatgpt_api.send_to_openai(database_messages)

    print("answer: " + personalized_answer)
    
    
    my_bar.progress(60, text="got answer")
    
    ###############################################################################
    show_answer_in_chat(personalized_answer, "What temperature is in my room?")



    connect_to_phpmyadmin.insert_message_to_database(name, query, personalized_answer, database_messages) #insert to Azure DB to user table    
    connect_to_phpmyadmin.add_pair_to_general_table(name, personalized_answer) #to general table with all  questions and answers
    connect_to_phpmyadmin.send_chatgpt_usage_to_database(prompt_tokens, completion_tokens, total_tokens) #to A DB with usage stats
    print("-----addded tokens to db--------")
    
    if tts_or_not == True:
        if selected_language == 'Polish':
            request_voice_tts.request_voice_fn("temperatura podana kończę na dziś", True) #request Azure TTS to for answer
        else:
            request_voice_tts.request_voice_fn(personalized_answer)
        autoplay_question("response.wav") #play audio with answer
        autoplay_beep("cute_beep.wav") # end of answer beep    
    my_bar.progress(100, text="Here is your room temperature!")

if clean_history_button: 
    connect_to_phpmyadmin.reset_chat_history(name) # clean table
    connect_to_phpmyadmin.check_user_in_database(name) # make fresh table
    my_bar.progress(100, text="History cleaned!")
    
    autoplay_beep("cute_beep.wav")




 

def make_answer(user_question):
    database_messages =  check_user_in_database(name)
    
    
    if user_question.lower().startswith("agent:") or agent_mode_variable == True or user_question.lower().startswith("agent mode"):
            print("---------agent mode ENTERED---------")
            my_bar.progress(10, text="agent checking question...")
            user_question = user_question.replace("agent:", "").strip()
            user_question = user_question.replace("agent mode", "").strip()

            agent_reply = agent_shiro(user_question)
            my_bar.progress(20, text="agent replied: " + agent_reply)
            
            print("Agent: " + agent_reply)
            print("----------agent mode EXIT-----------")
    else:
        agent_reply = ""
        print("---------agent mode not entered---------")
        my_bar.progress(20, text="agent not entered")

    if user_question.lower().startswith("plan:") or "add_event_to_calendar" in agent_reply:
        print("---------plan mode ENTERED---------")
        my_bar.progress(30, text="adding event to calendar...")
        query = user_question.replace("plan:", "").strip()

        database_messages.append({"role": "user", "content": query})
            # use chain to add event to calendar
        answer, prompt_tokens, completion_tokens, total_tokens, formatted_answer = add_event_from_shiro(query)

        print("I added event with this info: \n" + formatted_answer)
        
        answer = "I added event to calendar with this information: \n" + formatted_answer
        
        
        event_info = parse_event_info(formatted_answer)
        print("event info: " + str(event_info))
        show_answer_in_chat(event_info, user_question)

        my_bar.progress(60, text="event added")
        
        connect_to_phpmyadmin.insert_message_to_database(name, query, answer, database_messages) #insert to Azure DB to user table    
        connect_to_phpmyadmin.add_pair_to_general_table(name, answer) #to general table with all  questions and answers
        connect_to_phpmyadmin.send_chatgpt_usage_to_database(prompt_tokens, completion_tokens, total_tokens) #to A DB with usage stats
        
        my_bar.progress(100, text="Event added to calendar!")

    elif user_question.lower().startswith("schedule:") or "retrieve_event_from_calendar" in agent_reply:
        print("---------schedule mode ENTERED---------")
        my_bar.progress(30, text="retrieving event from calendar...")
        query = user_question.replace("schedule:", "").strip()
        query = "Madrus: " + query
        database_messages.append({"role": "user", "content": query})

        # use function chain to add event to calendar
        answer, prompt_tokens, completion_tokens, total_tokens = retrieve_plans_for_days(query)

            # sending schedule to shiro to add personality to raw schedule
        question = f"""can you summarize my plans ? what i have for that days. tell me like assistant tells plans for her boss when he has little time to listen. In 'your words', not just plain date's. and please order it by dates. here are my plans: '{answer}"""
        
        database_messages.append({"role": "user", "content": question})
                
        print("database_messages: " + str(database_messages))
        my_bar.progress(60, text="sending schedule to shiro...")
        personalized_answer, prompt_tokens2, completion_tokens2, total_tokens2 = shared_code.chatgpt_api.send_to_openai(database_messages)

        prompt_tokens += prompt_tokens2
        completion_tokens += completion_tokens2
        total_tokens += total_tokens2

        print("answer: " + answer)
        
        show_answer_in_chat(personalized_answer, user_question)
        
        tts_answer = "these are your plans:"
        if tts_or_not == True:
            if selected_language == 'Polish':
                request_voice_tts.request_voice_fn("To twoje plan:", True) #request Azure TTS to for answer
            else:
                request_voice_tts.request_voice_fn(tts_answer)
            autoplay_question("response.wav") #play audio with answer
            autoplay_beep("cute_beep.wav") # end of answer beep    

        my_bar.progress(100, text="Here's your schedule!")
        connect_to_phpmyadmin.insert_message_to_database(name, user_question, answer, database_messages) #insert to Azure DB to user table    
        connect_to_phpmyadmin.add_pair_to_general_table(name, answer) #to general table with all  questions and answers
        connect_to_phpmyadmin.send_chatgpt_usage_to_database(prompt_tokens, completion_tokens, total_tokens) #to A DB with usage stats
        print("-----addded tokens to db--------")
        
    elif user_question.lower().startswith("db:") or search_vector_db_checkbox == True:
        print("---------vector db mode ENTERED---------")
        query = user_question.replace("db:", "").strip()
        database_messages.append({"role": "user", "content": query})

        my_bar.progress(30, text="Searching db...")
        answer = search_db_with_llm_response(query)
        print("answer from db: " + str(answer))
        my_bar.progress(60, text="Found something!")

        show_answer_in_chat(answer, query)

        connect_to_phpmyadmin.insert_message_to_database(name, query, answer, database_messages) #insert to Azure DB to user table    
        connect_to_phpmyadmin.add_pair_to_general_table(name, answer) #to general table with all  questions and answers
        if tts_or_not == True:
            if selected_language == 'Polish':
                request_voice_tts.request_voice_fn(answer, True) #request Azure TTS to for answer
            else:
                request_voice_tts.request_voice_fn(answer)
            autoplay_question("response.wav") #play audio with answer
            autoplay_beep("cute_beep.wav") # end of answer beep
        my_bar.progress(100, text="I think I got it!")
          

    elif user_question.lower().startswith("ha:") or "home_assistant" in agent_reply:
        print("---------home assistant mode ENTERED---------")
        query = "what temperature is in my room?"
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S %A")
        query = f"[current time: {current_time}] {query}"
        # use function chain to add event to calendar
        answer_from_ha = ha_api_requests.room_temp()
        print("answer from api: " + answer_from_ha)
        outside_temp =open_weather_api.current_temperature()

        
        query2 = f"[current time: {current_time}] Madrus: {query}. shiro: Retriving informations from her sensors... Done! Info from sensors:{answer_from_ha}°C. Weather outside: {outside_temp}°C.| (please say °C in your answer) | Shiro:"
        database_messages.append({"role": "user", "content": query2})
                
        print("messages: " + str(database_messages))
        
        personalized_answer, prompt_tokens, completion_tokens, total_tokens = shared_code.chatgpt_api.send_to_openai(database_messages)

        print("answer: " + personalized_answer)
        
        my_bar.progress(60, text="got answer")
        
        show_answer_in_chat(personalized_answer, "What temperature is in my room?")

        connect_to_phpmyadmin.insert_message_to_database(name, query, personalized_answer, database_messages) #insert to Azure DB to user table    
        connect_to_phpmyadmin.add_pair_to_general_table(name, personalized_answer) #to general table with all  questions and answers
        connect_to_phpmyadmin.send_chatgpt_usage_to_database(prompt_tokens, completion_tokens, total_tokens) #to A DB with usage stats
        print("-----addded tokens to db--------")
        
        if tts_or_not == True:
            if selected_language == 'Polish':
                request_voice_tts.request_voice_fn("temperatura podana kończę na dziś", True) #request Azure TTS to for answer
            else:
                request_voice_tts.request_voice_fn(personalized_answer)
            autoplay_question("response.wav") #play audio with answer
            autoplay_beep("cute_beep.wav") # end of answer beep    
        my_bar.progress(100, text="Here is your room temperature!")


    elif "show_anime_list" in agent_reply or "show_manga_list" in agent_reply:
            
        content_type = "ANIME" if "anime" in agent_reply else "MANGA" 
        my_bar.progress(30, text="getting data from anilist...")   
           
        media_list,_ = anilist_api_requests.get_10_newest_entries(content_type)
        table_data = format_as_table(media_list, "manga") if content_type == "MANGA" else format_as_table(media_list, "anime")

        # Create a DataFrame from the table data
        df = pd.DataFrame(table_data)
    
        show_answer_in_chat(df, user_question)
        if content_type == "MANGA":
            add_anilist_to_db("manga")
        else:
            add_anilist_to_db("anime")
        
        
        if tts_or_not == True:
            if selected_language == 'Polish':
                request_voice_tts.request_voice_fn("Oto twoja lista", True) #request Azure TTS to for answer
            else:
                request_voice_tts.request_voice_fn("Here is your list. *smile*")
            autoplay_question("response.wav") #play audio with answer
            autoplay_beep("cute_beep.wav") # end of answer beep    
        connect_to_phpmyadmin.insert_message_to_database(name, user_question, media_list, database_messages) #insert to Azure DB to user table    
        my_bar.progress(100, text="Here's your list!")
        print("------end of list function--------")

    elif update_anime_or_manga_list == True: # for now doesnt work
        # make shiro find me id of anime/manga
        
        my_bar.progress(30, text="getting data from anilist...")
        content_type = "ANIME" if "anime" in user_question else "MANGA"  # this is risky but for now it works if you say anime in question
        print("content type: " + content_type)
        chapters_or_episodes = "episodes" if content_type == "ANIME" else "chapters"
        media_list,_ = anilist_api_requests.get_10_newest_entries(content_type)
        question = f"Madrus: I will give you list of my 10 most recent watched/read {content_type} from site AniList. Here is this list:{media_list}. I want you to remember this because in next question I will ask you to update episodes/chapters of one of them."
        #print("question from user:" + question)
        database_messages.append({"role": "user", "content": question})

        # send to open ai for answer !!!!!!!! I WONT SEND IT BECOUSE I ALREADY GOT IT FROM reformatting
        answer = "Okay, I will remember it, Madrus. I'm waiting for your next question. Give it to me nyaa."
           
        #database_messages.append({"role": "assistant", "content": answer})   
        database_messages.append({"role": "assistant", "content": answer})
        
        #################################################################################################
        end_question = "I would like you to answer me giving me ONLY THIS: ' title:<title>,id:<id>,"
        extra = " episodes:<episodes>'. Nothing more." if content_type == "ANIME" else " chapters:<chapters>'. Nothing more."
        question = f"Madrus: {user_question}. {end_question}{extra}"

        database_messages.append({"role": "user", "content": question})
        my_bar.progress(40, text="sending to openAI...")
        print("database_messages: " + str(database_messages))
        # send to open ai for answer
        answer, prompt_tokens, completion_tokens, total_tokens = shared_code.chatgpt_api.send_to_openai(database_messages) 
        print("answer from OpenAI: " + answer)
        
            # START find ID and episodes number of updated anime
        # The regex pattern             
        pattern = r"id:\s*(\d+),\s*episodes:\s*(\d+)" if content_type == "ANIME" else r"id:\s*(\d+),\s*chapters:\s*(\d+)"

        # Use re.search to find the pattern in the text
        match = re.search(pattern, answer)
        my_bar.progress(50, text="got answer")
        if match:
            # match.group(1) contains the id, match.group(2) contains the episodes number
            updated_id = match.group(1)
            updated_info = match.group(2)
            print(f"reformatted request: id:{updated_id}, type:{content_type}: ep/chap{updated_info}")
            

            anilist_api_requests.change_progress(updated_id, updated_info,content_type)
            show_answer_in_chat(answer, user_question)
            request_voice_tts.request_voice_fn(f"Done, updated it to {updated_info} {chapters_or_episodes}")

                # Save to database 
            connect_to_phpmyadmin.insert_message_to_database(name, question, answer, database_messages) #insert to Azure DB to user table    
            connect_to_phpmyadmin.send_chatgpt_usage_to_database(prompt_tokens, completion_tokens, total_tokens) #to Azure DB with usage stats
            print("---------saved to db-------------")
            
            
        else:
            print("No match found")
            request_voice_tts.request_voice_fn("Sorry, I couldn't understand your request.")
        # END find ID and episodes number of updated anime/manga
        my_bar.progress(100, text="I updated your list!")
        
        print("-----exited animelist mode--------")
        


    else:
        print("---------normal mode ENTERED---------")
        question = f"Madrus: {user_question}"
        print("question from user:" + question)
        database_messages.append({"role": "user", "content": question})

            # send to open ai for answer
        my_bar.progress(40,"sending to openAI...") 
        print("messages: " + str(database_messages))
        answer, prompt_tokens, completion_tokens, total_tokens = shared_code.chatgpt_api.send_to_openai(database_messages) 
        

        my_bar.progress(60, text="got answerr")

        show_answer_in_chat(answer, user_question)
        
        
        if profanity.contains_profanity(answer) == True:
            answer = profanity.censor(answer)                    
        my_bar.progress(60, text="saving to local db...")
        connect_to_phpmyadmin.insert_message_to_database(name, question, answer, database_messages) #insert to DB to user table    
        connect_to_phpmyadmin.add_pair_to_general_table(name, answer) #to general table with all  questions and answers
        connect_to_phpmyadmin.send_chatgpt_usage_to_database(prompt_tokens, completion_tokens, total_tokens) #to A DB with usage stats
        my_bar.progress(80, text="saved to DB")
        if tts_or_not == True:
            if selected_language == 'Polish':
                request_voice_tts.request_voice_fn(answer, True) #request Azure TTS to for answer
            else:
                request_voice_tts.request_voice_fn(answer)
            autoplay_question("response.wav") #play audio with answer
            autoplay_beep("cute_beep.wav") # end of answer beep   
        
        
        my_bar.progress(100, text="Here's my answer!")


# Capture and process user input
if user_question:
    make_answer(user_question)


if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {"role": "assistant", "content": "Hi, I'm Shiro! Let's talk! :)"}
        ]

st.session_state.messages = [message for message in st.session_state.messages if message["content"] is not None]

# Display previous messages
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         if isinstance(message["content"], pd.DataFrame):
#             st.table(message["content"])
#         else:
#             st.markdown(message["content"], unsafe_allow_html=True)

for message in st.session_state.messages:
    avatar_image = "pictures/avatar_shiro.png" if message["role"] == "assistant" else None
    with st.chat_message(message["role"], avatar=avatar_image):
        if isinstance(message["content"], pd.DataFrame):
            st.table(message["content"])
        else:
            st.markdown(message["content"], unsafe_allow_html=True)

print("-------end of code---------")
