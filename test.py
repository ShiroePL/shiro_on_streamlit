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
from langchain_database.answer_with_chromadb_huggingface_embedd import search_chroma_db
from langchain_database.test_wszystkiego import add_event_from_shiro
import base64
import pandas as pd
# Add a selectbox to the sidebar:
import connect_to_phpmyadmin
import request_voice_tts
import chatgpt_api
from st_custom_components import st_audiorec
import os
from PIL import Image
import numpy as np
from audiorecorder import audiorecorder
from io import BytesIO
import streamlit.components.v1 as components
from audio_recorder_streamlit import audio_recorder
import shared_code.anilist.anilist_api_requests as anilist_api_requests
from shiro_agent import CustomToolsAgent
from shared_code.home_assistant import ha_api_requests, open_weather_api

#conn= st.experimental_connection('mysql', type='sql')

conn = None
tts_or_not = False
show_history_variable = False
name = "normal"
agent_reply = ""
agent_mode_variable = False

col11, col22 = st.columns(2)
with col11:
    progress_label = st.empty()
    progress_label.text('Log...')
with col22:
    show_history = st.checkbox('Show history')

    if show_history:
        show_history_variable = True

    

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

def show_history_in_table():
    #show_history_variable = True
    if show_history_variable == True:
        df = pd.DataFrame(connect_to_phpmyadmin.retrieve_chat_history_from_database("normal"))
        st.dataframe(df)

#@st.cache_data
def chech_user_in_database(name):
    connect_to_phpmyadmin.check_user_in_database(name)
    history = connect_to_phpmyadmin.retrieve_chat_history_from_database(name)
    return history




@st.cache_data
def search_chroma_db(query):
    instructor_embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-large", 
                                                        model_kwargs={"device": "cpu"})
    persist_directory = './langchain_database/db_streamlit'
    embedding = instructor_embeddings

    vectordb2 = Chroma(persist_directory=persist_directory, 
                    embedding_function=embedding,
                    collection_name="personal"
                    )

    retriever = vectordb2.as_retriever(search_kwargs={"k": 4})
    
    # Set up the turbo LLM
    turbo_llm = ChatOpenAI(
        temperature=1,
        model_name='gpt-3.5-turbo'
    )
    #progress_label.text('loaded model')
    
    # create the chain to answer questions 
    qa_chain = RetrievalQA.from_chain_type(llm=turbo_llm, 
                                    chain_type="stuff", 
                                    retriever=retriever, 
                                    return_source_documents=True)

    ## Cite sources
    def process_llm_response(llm_response):
        #print(llm_response['result'])
        #print('full llm response:' + str(llm_response))
        #print('\n\nSources:')
        # for source in llm_response["source_documents"]:
        #     print(source.metadata['source'])
        
        return llm_response['result']    
    llm_response = qa_chain(query)
    print(str(llm_response))
    answer_from_database = process_llm_response(llm_response)
    #print(answer_from_database)
    return answer_from_database



    

selected_language = st.sidebar.selectbox(
    'What language should i speak?',
    ('English', 'Polish')
)

with st.sidebar:
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
    st.image(image)

# Store the initial value of widgets in session state
if "visibility" not in st.session_state:
    st.session_state.visibility = "visible"
    st.session_state.disabled = False

question = st.text_input( # INPUT FOR QUESTION
    "Ask me anything 👇",
    label_visibility=st.session_state.visibility,
)

st.write('Debug: Current value of selected_language is: ', selected_language)

    
my_bar = st.progress(0) #progress bar
button1 = st.button('do it') # BUTTON TO iniciate the process with question from input

answer_area = st.empty()
answer_area.text_area('Answer', placeholder="Here will be answer")
progress_label.text('checking...')

 # create table in there isnt and get history

    # Get all punctuation but leave colon ':'
punctuation_without_colon = "".join([ch for ch in string.punctuation if ch != ":"])
question = question.translate(str.maketrans("", "", punctuation_without_colon)).strip().lower()

if button1: # this is like my voice_control function in shiro tkinter
    messages =  chech_user_in_database(name)
    
    
    if question.lower().startswith("agent:") or agent_mode_variable == True or question.lower().startswith("agent mode"):
            print("---------agent mode ENTERED---------")
            my_bar.progress(10, text="agent checking question...")
            question = question.replace("agent:", "").strip()
            question = question.replace("agent mode", "").strip()

            agent_reply = agent_shiro(question)
            my_bar.progress(20, text="agent replied: " + agent_reply)
            
            print("Agent: " + agent_reply)
            print("----------agent mode EXIT-----------")


    if question.lower().startswith("plan:") or "add_event_to_calendar" in agent_reply:
        query = question.replace("plan:", "").strip()

        messages.append({"role": "user", "content": query})
            # use chain to add event to calendar
        answer, prompt_tokens, completion_tokens, total_tokens, formatted_query_to_calendar = add_event_from_shiro(query)

        my_bar.progress(60, text="event added")
        
        # print_response_label("I added event with this info: \n" + formatted_query_to_calendar)
        answer_area.text_area('Answer', "I added event with this info: \n" + formatted_query_to_calendar)

        connect_to_phpmyadmin.insert_message_to_database(name, query, answer, messages) #insert to Azure DB to user table    
        connect_to_phpmyadmin.add_pair_to_general_table(name, answer) #to general table with all  questions and answers
        connect_to_phpmyadmin.send_chatgpt_usage_to_database(prompt_tokens, completion_tokens, total_tokens) #to A DB with usage stats
        
        
        my_bar.progress(100, text="done")
        # running = False
        # progress(100,"showed, done")    
    
    elif question.lower().startswith("schedule:") or "retrieve_event_from_calendar" in agent_reply:
        query = question.replace("schedule:", "").strip()
        query = "Madrus: " + query
        messages.append({"role": "user", "content": query})

        # use function chain to add event to calendar
        answer, prompt_tokens, completion_tokens, total_tokens = retrieve_plans_for_days(query)

            # sending schedule to shiro to add personality to raw schedule
        question = f"""can you summarize my plans ? what i have for that days. tell me like assistant tells plans for her boss when he has little time to listen. In 'your words', not just plain date's. and please order it by dates. here are my plans: '{answer}"""
        
        messages.append({"role": "user", "content": question})
                
        print("messages: " + str(messages))
        logger.info("messages: " + str(messages))
        personalized_answer, prompt_tokens2, completion_tokens2, total_tokens2 = chatgpt_api.send_to_openai(messages)

        prompt_tokens += prompt_tokens2
        completion_tokens += completion_tokens2
        total_tokens += total_tokens2

        
        print("answer: " + answer)
        logger.info("answer: " + answer)
        tts_answer = "these are your plans:"
        request_voice.request_voice_fn(tts_answer)
        connect_to_phpmyadmin.insert_message_to_database(name, question, answer, messages) #insert to Azure DB to user table    
        connect_to_phpmyadmin.add_pair_to_general_table(name, answer) #to general table with all  questions and answers
        connect_to_phpmyadmin.send_chatgpt_usage_to_database(prompt_tokens, completion_tokens, total_tokens) #to A DB with usage stats
        print("-----addded tokens to db--------")
        logger.info("-----addded tokens to db--------")
        return personalized_answer


    elif question.lower().startswith("db:") or "database_search" in agent_reply or "personal_db_search" in agent_reply:
        query = question.replace("db:", "").strip()
        messages.append({"role": "user", "content": query})
        answer = search_chroma_db(query)
        
        my_bar.progress(60, text="got answer")
        answer_area.text_area('Answer', answer)
        
        connect_to_phpmyadmin.insert_message_to_database(name, query, answer, messages) #insert to Azure DB to user table    
        connect_to_phpmyadmin.add_pair_to_general_table(name, answer) #to general table with all  questions and answers
        if tts_or_not == True:
            if selected_language == 'Polish':
                request_voice_tts.request_voice_fn(answer, True) #request Azure TTS to for answer
            else:
                request_voice_tts.request_voice_fn(answer)
            autoplay_question("response.wav") #play audio with answer
            autoplay_beep("cute_beep.wav") # end of answer beep
        show_history_in_table()    

    elif question.lower().startswith("ha:") or "home_assistant" in agent_reply:
        query = question.replace("ha:", "").strip()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S %A")
        query = f"[current time: {current_time}] {query}"
        # use function chain to add event to calendar
        answer_from_ha = ha_api_requests.room_temp()
        print("answer from api: " + answer_from_ha)

        
        query2 = f"[current time: {current_time}] Madrus: {query}. shiro: Retriving informations from her sensors... Done! Info from sensors:{answer_from_ha}°C. Weather outside: 25°C.| (please say °C in your answer) | Shiro:"
        messages.append({"role": "user", "content": query2})
                
        print("messages: " + str(messages))
        #logger.info("messages: " + str(messages))
        personalized_answer, prompt_tokens, completion_tokens, total_tokens = chatgpt_api.send_to_openai(messages)

        print("answer: " + personalized_answer)
        #logger.info("answer: " + personalized_answer)
        
        my_bar.progress(60, text="got answer")
        answer_area.text_area('Answer', personalized_answer)

        connect_to_phpmyadmin.insert_message_to_database(name, question, personalized_answer, messages) #insert to Azure DB to user table    
        connect_to_phpmyadmin.add_pair_to_general_table(name, personalized_answer) #to general table with all  questions and answers
        connect_to_phpmyadmin.send_chatgpt_usage_to_database(prompt_tokens, completion_tokens, total_tokens) #to A DB with usage stats
        print("-----addded tokens to db--------")
        #logger.info("-----addded tokens to db--------")
        if tts_or_not == True:
            if selected_language == 'Polish':
                request_voice_tts.request_voice_fn("temperatura podana kończę na dziś", True) #request Azure TTS to for answer
            else:
                request_voice_tts.request_voice_fn(personalized_answer)
            autoplay_question("response.wav") #play audio with answer
            autoplay_beep("cute_beep.wav") # end of answer beep    
        show_history_in_table() 

    else:
        question = f"Madrus: {question}"
        print("question from user:" + question)
        messages.append({"role": "user", "content": question})

        #txt = st.text_area('Answer', search_chroma_db(text_input), placeholder = "Here will be answer")
        #st.write('write of text area:', testujemy(txt))
        #st.write('wartosc zmiennej txt:', txt)
        #my_bar.progress(100, text="done")
    ##################################################################
            # send to open ai for answer
        # progress(40,"sending to openAI...") 
        print("messages: " + str(messages))
        answer, prompt_tokens, completion_tokens, total_tokens = chatgpt_api.send_to_openai(messages) 
        #txt = st.text_area('Answer', answer)
        answer_area.text_area('Answer', answer)
        my_bar.progress(60, text="got answerr")

        # if tts_or_not == "Yes": #IF YES THEN WITH VOICE
        #     request_voice.request_voice_fn(answer) #request Azure TTS to for answer
        #     progress(70,"got voice")
        #     play_audio_fn("response") dd
            
        # print("ShiroAi-chan: " + answer)
        
        if profanity.contains_profanity(answer) == True:
            answer = profanity.censor(answer)                    
        my_bar.progress(60, text="saving to DB...")
        connect_to_phpmyadmin.insert_message_to_database(name, question, answer, messages) #insert to DB to user table    
        connect_to_phpmyadmin.add_pair_to_general_table(name, answer) #to general table with all  questions and answers
        connect_to_phpmyadmin.send_chatgpt_usage_to_database(prompt_tokens, completion_tokens, total_tokens) #to A DB with usage stats
        my_bar.progress(80, text="saved to DB")
        if tts_or_not == True:
            request_voice_tts.request_voice_fn(answer) #request Azure TTS to for answer
            autoplay_question("response.wav") #play audio with answer
            autoplay_beep("cute_beep.wav") # end of answer beep
        show_history_in_table() 
        print("---------------------------------")

       





col1, col2, col3 = st.columns(3)

with col1:
    anime_button = st.button("show anime history")

with col2:
    manga_button = st.button("show manga history")

with col3:
    history_in_db_button = st.button("show history of chatting")

col4, col5, col6 = st.columns(3)

with col4:
    clean_history_button = st.button('clean history')

with col5:
    show_room_temp_button = st.button('show room temp')

if anime_button:
    media_list,_ = anilist_api_requests.get_10_newest_entries("ANIME")
    answer_area.text_area('Answer', media_list)
    show_history_variable = True
    show_history_in_table() 
    show_history_variable = False

if manga_button:
    media_list,_ = anilist_api_requests.get_10_newest_entries("MANGA")
    answer_area.text_area('Answer', media_list)
    show_history_variable = True
    show_history_in_table() 
    show_history_variable = False

if history_in_db_button:
    history = chech_user_in_database(name)
    show_history_variable = True
    show_history_in_table() 
    show_history_variable = False


if show_room_temp_button:
    messages =  chech_user_in_database(name)
    query = "what temperature is in my room?"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S %A")
    query = f"[current time: {current_time}] {query}"
    # use function chain to add event to calendar
    answer_from_ha = ha_api_requests.room_temp()
    print("answer from api: " + answer_from_ha)
    outside_temp =open_weather_api.current_temperature()

    
    query2 = f"[current time: {current_time}] Madrus: {query}. shiro: Retriving informations from her sensors... Done! Info from sensors:{answer_from_ha}°C. Weather outside: {outside_temp}°C.| (please say °C in your answer) | Shiro:"
    messages.append({"role": "user", "content": query2})
            
    print("messages: " + str(messages))
    #logger.info("messages: " + str(messages))
    personalized_answer, prompt_tokens, completion_tokens, total_tokens = chatgpt_api.send_to_openai(messages)

    print("answer: " + personalized_answer)
    #logger.info("answer: " + personalized_answer)
    
    my_bar.progress(60, text="got answer")
    answer_area.text_area('Answer', personalized_answer)

    connect_to_phpmyadmin.insert_message_to_database(name, query, personalized_answer, messages) #insert to Azure DB to user table    
    connect_to_phpmyadmin.add_pair_to_general_table(name, personalized_answer) #to general table with all  questions and answers
    connect_to_phpmyadmin.send_chatgpt_usage_to_database(prompt_tokens, completion_tokens, total_tokens) #to A DB with usage stats
    print("-----addded tokens to db--------")
    #logger.info("-----addded tokens to db--------")
    if tts_or_not == True:
        if selected_language == 'Polish':
            request_voice_tts.request_voice_fn("temperatura podana kończę na dziś", True) #request Azure TTS to for answer
        else:
            request_voice_tts.request_voice_fn(personalized_answer)
        autoplay_question("response.wav") #play audio with answer
        autoplay_beep("cute_beep.wav") # end of answer beep    



progress_label.text('Done!')
my_bar.progress(100, text="Done!")
print("-------end of code---------")

if clean_history_button:
    connect_to_phpmyadmin.reset_chat_history(name)
    connect_to_phpmyadmin.check_user_in_database(name)
    progress_label.text('History cleaned!')
    autoplay_beep("cute_beep.wav")

# wav_audio_data = st_audiorec()

# if wav_audio_data is not None:
#     # display audio data as received on the backend
#     st.audio(wav_audio_data, format='audio/wav')

# st.title("Audio Recorder")
# audio = audiorecorder("Click to record", "Recording...")

# if len(audio) > 0:
#     # To play audio in frontend:
#     st.audio(audio.tobytes())
    
#     # To save audio to a file:
#     wav_file = open("audio.mp3", "wb")
#     wav_file.write(audio.tobytes())

# Use pandas DataFrame to structure your data
# if show_history_variable == True:
#         df = pd.DataFrame(connect_to_phpmyadmin.retrieve_chat_history_from_database("normal"))
#         st.dataframe(df)

 # BUTTON TO iniciate the process with question from input
    
    #answer = testujemy(text_input)
    #answer2 = search_chroma_db(text_input)
    #st.write("Answer: ", answer2)
    