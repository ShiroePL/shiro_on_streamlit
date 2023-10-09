from datetime import datetime
import streamlit as st
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.llms import OpenAI
from langchain.document_loaders import TextLoader
from langchain.document_loaders import PyPDFLoader
from langchain.document_loaders import DirectoryLoader
from InstructorEmbedding import INSTRUCTOR
from langchain.embeddings import HuggingFaceInstructEmbeddings
from better_profanity import profanity
import string
from shared_code.langchain_database.langchain_vector_db_queries import search_db_with_llm_response
from shared_code.calendar_functions.test_wszystkiego import add_event_from_shiro, retrieve_plans_for_days
import base64
import pandas as pd
import shared_code.connect_to_phpmyadmin as connect_to_phpmyadmin
import request_voice_tts
import shared_code.chatgpt_api
from PIL import Image
import numpy as np
from io import BytesIO
import streamlit.components.v1 as components
import shared_code.anilist.anilist_api_requests as anilist_api_requests
from shared_code.shiro_agent import CustomToolsAgent
from shared_code.home_assistant import ha_api_requests, open_weather_api
from langchain.agents import initialize_agent, AgentType
from langchain.callbacks import StreamlitCallbackHandler
from langchain.tools import DuckDuckGoSearchRun
from st_chat_message import message

conn = None
tts_or_not = False
show_history_variable = False
name = "normal"
agent_reply = ""
agent_mode_variable = False

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


def show_answer_in_chat(answer, user_question = None):  # Added user_question as a parameter
    # Initialize session state for storing messages if it doesn't exist
    # if "messages" not in st.session_state:
    #     st.session_state["messages"] = [
    #         {"role": "assistant", "content": "Hi, I'm Shiro! Let's talk! :)"}
    #     ]
    
    # Append user's question to the state
    st.session_state.messages.append({"role": "user", "content": user_question})
    
    # Append bot's answer to the state
    st.session_state.messages.append({"role": "assistant", "content": answer})

    # # Display previous messages
    # for message in st.session_state.messages:
    #     with st.chat_message(message["role"]):
    #         st.markdown(message["content"])

    # # Display bot's answer
    # with st.chat_message("assistant"):
    #     st.markdown(answer)
        
    
def add_anilist_to_db(type):
    
    media_list,_ = anilist_api_requests.get_10_newest_entries("ANIME")
    query = f"show my my {type} list"
    database_messages =  check_user_in_database(name)

    connect_to_phpmyadmin.insert_message_to_database(name, query, media_list, database_messages) #insert to Azure DB to user table    
    connect_to_phpmyadmin.add_pair_to_general_table(name, media_list) #to general table with all  questions and answers




st.title("Shiro AI Chan")


# Initialize session state for storing messages
# if "messages" not in st.session_state:
#     st.session_state["messages"] = [
#         #{"role": "assistant", "content": "Hi, I'm Shiro! Let's talk! :)"}
#     ]

user_question = st.chat_input("I'm Shiro! Ask me anything!") # placeholder in " " ## chat input for asking question




col11, col22 = st.columns(2)
with col11:
    progress_label = st.empty()
    progress_label.text('Log...')


    

selected_language = st.sidebar.selectbox(
    'What language should i speak?',
    ('English', 'Polish')
)

with st.sidebar:
    my_bar = st.progress(0) #progress bar 
    coll1, coll2 = st.columns(2)
    with coll1:
        voice_on_off = st.checkbox('Voice on/off')
        if voice_on_off:
            tts_or_not = True
            st.write('Great!!')
    with coll2:
        #pass
        agent_mode = st.checkbox('agent_mode on/off')
        if agent_mode:
            agent_mode_variable = True
            st.write('Agent mode on!')                               
    image = Image.open('pictures/avatar_shiro.png')
    
    
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

    with col8:
        add_text_to_db = st.button('add text to vector db')


    add_pdf_to_db = st.button('add text to vector dbs')
    st.image(image)



progress_label.text('checking...')

 # create table in there isnt and get history

    # Get all punctuation but leave colon ':'
# punctuation_without_colon = "".join([ch for ch in string.punctuation if ch != ":"])
# user_question = user_question.translate(str.maketrans("", "", punctuation_without_colon)).strip().lower()


# col1, col2, col3 = st.columns(3)

# with col1:
#     anime_button = st.button("show anime history")

# with col2:
#     manga_button = st.button("show manga history")

# with col3:
#     history_in_db_button = st.button("show history of chatting")

# col4, col5, col6 = st.columns(3)

# with col4:
#     clean_history_button = st.button('clean history')

# with col5:
#     show_room_temp_button = st.button('show room temp')

# with col6:
#     add_text_to_db = st.button('add text to vector db')


#add_pdf_to_db = st.button('add text to vector dbs')


if anime_button:
    media_list,_ = anilist_api_requests.get_10_newest_entries("ANIME")
    show_answer_in_chat(media_list)
    add_anilist_to_db("anime")
    

if manga_button:
    media_list,_ = anilist_api_requests.get_10_newest_entries("MANGA")
    show_answer_in_chat(media_list)
    add_anilist_to_db("manga")
    

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
    show_answer_in_chat(personalized_answer)



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


if clean_history_button: 
    connect_to_phpmyadmin.reset_chat_history(name) # clean table
    connect_to_phpmyadmin.check_user_in_database(name) # make fresh table
    progress_label.text('History cleaned!')
    autoplay_beep("cute_beep.wav")

if add_text_to_db:
    pass
    #to do



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
        my_bar.progress(10, text="agent not entered")

    if user_question.lower().startswith("plan:") or "add_event_to_calendar" in agent_reply:
        query = user_question.replace("plan:", "").strip()

        database_messages.append({"role": "user", "content": query})
            # use chain to add event to calendar
        answer, prompt_tokens, completion_tokens, total_tokens, formatted_query_to_calendar = add_event_from_shiro(query)

        my_bar.progress(60, text="event added")
        
        connect_to_phpmyadmin.insert_message_to_database(name, query, answer, database_messages) #insert to Azure DB to user table    
        connect_to_phpmyadmin.add_pair_to_general_table(name, answer) #to general table with all  questions and answers
        connect_to_phpmyadmin.send_chatgpt_usage_to_database(prompt_tokens, completion_tokens, total_tokens) #to A DB with usage stats
        
        my_bar.progress(100, text="done")
        show_answer_in_chat(answer, user_question)
    
    elif user_question.lower().startswith("schedule:") or "retrieve_event_from_calendar" in agent_reply:
        query = user_question.replace("schedule:", "").strip()
        query = "Madrus: " + query
        database_messages.append({"role": "user", "content": query})

        # use function chain to add event to calendar
        answer, prompt_tokens, completion_tokens, total_tokens = retrieve_plans_for_days(query)

            # sending schedule to shiro to add personality to raw schedule
        question = f"""can you summarize my plans ? what i have for that days. tell me like assistant tells plans for her boss when he has little time to listen. In 'your words', not just plain date's. and please order it by dates. here are my plans: '{answer}"""
        
        database_messages.append({"role": "user", "content": question})
                
        print("database_messages: " + str(database_messages))
        
        personalized_answer, prompt_tokens2, completion_tokens2, total_tokens2 = shared_code.chatgpt_api.send_to_openai(database_messages)

        prompt_tokens += prompt_tokens2
        completion_tokens += completion_tokens2
        total_tokens += total_tokens2

        
        print("answer: " + answer)
        my_bar.progress(60, text="got answer")
        show_answer_in_chat(personalized_answer, user_question)
        

        tts_answer = "these are your plans:"
        if tts_or_not == True:
            if selected_language == 'Polish':
                request_voice_tts.request_voice_fn("To twoje plan:", True) #request Azure TTS to for answer
            else:
                request_voice_tts.request_voice_fn(tts_answer)
            autoplay_question("response.wav") #play audio with answer
            autoplay_beep("cute_beep.wav") # end of answer beep    


        connect_to_phpmyadmin.insert_message_to_database(name, user_question, answer, database_messages) #insert to Azure DB to user table    
        connect_to_phpmyadmin.add_pair_to_general_table(name, answer) #to general table with all  questions and answers
        connect_to_phpmyadmin.send_chatgpt_usage_to_database(prompt_tokens, completion_tokens, total_tokens) #to A DB with usage stats
        print("-----addded tokens to db--------")
        
        


    elif user_question.lower().startswith("db:") or "database_search" in agent_reply or "personal_db_search" in agent_reply:
        query = user_question.replace("db:", "").strip()
        database_messages.append({"role": "user", "content": query})
        answer = search_db_with_llm_response(query)
        
        my_bar.progress(60, text="got answer")

        show_answer_in_chat(answer, user_question)

        connect_to_phpmyadmin.insert_message_to_database(name, query, answer, database_messages) #insert to Azure DB to user table    
        connect_to_phpmyadmin.add_pair_to_general_table(name, answer) #to general table with all  questions and answers
        if tts_or_not == True:
            if selected_language == 'Polish':
                request_voice_tts.request_voice_fn(answer, True) #request Azure TTS to for answer
            else:
                request_voice_tts.request_voice_fn(answer)
            autoplay_question("response.wav") #play audio with answer
            autoplay_beep("cute_beep.wav") # end of answer beep
          

    elif user_question.lower().startswith("ha:") or "home_assistant" in agent_reply:
        query = user_question.replace("ha:", "").strip()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S %A")
        query = f"[current time: {current_time}] {query}"
        # use function chain to add event to calendar
        answer_from_ha = ha_api_requests.room_temp()
        print("answer from api: " + answer_from_ha)

        
        query2 = f"[current time: {current_time}] Madrus: {query}. shiro: Retriving informations from her sensors... Done! Info from sensors:{answer_from_ha}°C. Weather outside: 25°C.| (please say °C in your answer) | Shiro:"
        database_messages.append({"role": "user", "content": query2})
                
        print("messages: " + str(database_messages))
        
        personalized_answer, prompt_tokens, completion_tokens, total_tokens = shared_code.chatgpt_api.send_to_openai(database_messages)

        print("answer: " + personalized_answer)
        
        
        my_bar.progress(60, text="got answer")
        show_answer_in_chat(personalized_answer, user_question)

        connect_to_phpmyadmin.insert_message_to_database(name, user_question, personalized_answer, database_messages) #insert to Azure DB to user table    
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
        
    #  elif "show_anime_list" in agent_reply or "show_manga_list" in agent_reply:
            
    #     content_type = "anime" if "anime" in agent_reply else "manga" 
        
    #     list_content, _ = anilist_api_requests.get_10_newest_entries("ANIME") if content_type == "anime" else anilist_api_requests.get_10_newest_entries("MANGA")  # assuming this method exists        
            
    #     question = f"Madrus: I will give you list of my 10 most recent watched/read {content_type} from site AniList. Here is this list:{list_content}. I want you to remember this because in next question I will ask you to update episodes/chapters of one of them."
    #     #print("question from user:" + question)
    #     messages.append({"role": "user", "content": question})

    #     # send to open ai for answer !!!!!!!! I WONT SEND IT BECOUSE I ALREADY GOT IT FROM reformatting
    #     answer = "Okay, I will remember it, Madrus. I'm waiting for your next question. Give it to me nyaa."
    #     answer_to_app = f"Here is your list of most recent anime/manga.{list_content}" # this goes 

    #     logging.info("requested list: \n" + answer_to_app)
    #     print("requested list: \n" + answer_to_app)
    #     logger.info("requested list: \n" + answer_to_app)
    #     request_voice.request_voice_fn("Here is your list. *smile*") #request Azure TTS to for answer
           
        
    #     connect_to_phpmyadmin.insert_message_to_database(name, question, answer, messages) #insert to Azure DB to user table    
    #     print("------end of list function--------")
    #     logging.info("-----end of list function------")
    #     content_type_mode = content_type
        
    #     return answer_to_app
        

        
    # elif checkbox_update: # she is in animelist mode, so she rebebmers list i gave her 
        
       
        
    #     # make shiro find me id of anime/manga
          
    #     content_type = content_type_mode   
    #     chapters_or_episodes = "episodes" if content_type == "anime" else "chapters"

    #     end_question = "I would like you to answer me giving me ONLY THIS: ' title:<title>,id:<id>,"
    #     extra = " episodes:<episodes>'. Nothing more." if content_type == "anime" else " chapters:<chapters>'. Nothing more."
    #     question = f"Madrus: {question}. {end_question}{extra}"

    #     #print("question from user:" + question)
    #     messages.append({"role": "user", "content": question})
        
    #     # send to open ai for answer
        
    #     answer, prompt_tokens, completion_tokens, total_tokens = shared_code.chatgpt_api.send_to_openai(messages) 
    #     print("answer from OpenAI: " + answer)
    #     logger.info("answer from OpenAI: " + answer)
    #         # START find ID and episodes number of updated anime
    #     # The regex pattern             
    #     pattern = r"id:\s*(\d+),\s*episodes:\s*(\d+)" if content_type == "anime" else r"id:\s*(\d+),\s*chapters:\s*(\d+)"

    #     # Use re.search to find the pattern in the text
    #     match = re.search(pattern, answer)
        

    #     if match:
    #         # match.group(1) contains the id, match.group(2) contains the episodes number
    #         updated_id = match.group(1)
            
    #         updated_info = match.group(2)
    #         print(f"reformatted request: id:{updated_id}, type:{content_type}: ep/chap{updated_info}")
    #         logger.info(f"reformatted request: id:{updated_id}, type:{content_type}: ep/chap{updated_info}")

    #         anilist_api_requests.change_progress(updated_id, updated_info,content_type)

    #         request_voice.request_voice_fn(f"Done, updated it to {updated_info} {chapters_or_episodes}")

    #             # Save to database 
    #         connect_to_phpmyadmin.insert_message_to_database(name, question, answer, messages) #insert to Azure DB to user table    
    #         connect_to_phpmyadmin.send_chatgpt_usage_to_database(prompt_tokens, completion_tokens, total_tokens) #to Azure DB with usage stats
    #         print("---------saved to db-------------")
    #         logger.info("---------saved to db-------------")
    #         answer_to_app = f"Done, updated it to {updated_info} {chapters_or_episodes}"
    #     else:
    #         print("No match found")
    #         logger.info("No match found")
    #         request_voice.request_voice_fn("Sorry, I couldn't understand your request.")
    #         answer_to_app = "Sorry, I couldn't understand your request."
    #     # END find ID and episodes number of updated anime/manga

        
        
        
    #     print("exited animelist mode")
    #     logger.info("----updated anime/manga----")
    #     return answer_to_app




    else:
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
        my_bar.progress(60, text="saving to DB...")
        connect_to_phpmyadmin.insert_message_to_database(name, question, answer, database_messages) #insert to DB to user table    
        connect_to_phpmyadmin.add_pair_to_general_table(name, answer) #to general table with all  questions and answers
        connect_to_phpmyadmin.send_chatgpt_usage_to_database(prompt_tokens, completion_tokens, total_tokens) #to A DB with usage stats
        my_bar.progress(80, text="saved to DB")
        if tts_or_not == True:
            if selected_language == 'Polish':
                request_voice_tts.request_voice_fn("temperatura podana kończę na dziś", True) #request Azure TTS to for answer
            else:
                request_voice_tts.request_voice_fn(answer)
            autoplay_question("response.wav") #play audio with answer
            autoplay_beep("cute_beep.wav") # end of answer beep   
        
        print("---------------------------------")


# Capture and process user input
if user_question:
    
    
    

    # Generate bot's answer (Replace this with real logic if needed)

    #############################################################################################################
                                            # HERE ANSWER FROM SHIRO 
    make_answer(user_question)

    #############################################################################################################
    
    


if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {"role": "assistant", "content": "Hi, I'm Shiro! Let's talk! :)"}
        ]
# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

 
progress_label.text('Done!')

my_bar.progress(100, text="Done!")
print("-------end of code---------")
