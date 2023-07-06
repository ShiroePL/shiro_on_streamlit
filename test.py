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

# Add a selectbox to the sidebar:
import connect_to_phpmyadmin

import chatgpt_api

name = "normal"
progress_label = st.empty()
progress_label.text('Log...')
agent_reply = ""


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


def testujemy(text_input):
    st.write("You entered: ", text_input)
    #print("to sie pokazalo")
    return "cos"
    

add_selectbox = st.sidebar.selectbox(
    'How would you like to be contacted?',
    ('tets', 'fsdf', 'Mobile phone')
)

# Store the initial value of widgets in session state
if "visibility" not in st.session_state:
    st.session_state.visibility = "visible"
    st.session_state.disabled = False

question = st.text_input( # INPUT FOR QUESTION
    "Ask me anything 👇",
    label_visibility=st.session_state.visibility,
)

st.write('Debug: Current value of text_input is: ', question)

    
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
    if question == "costam":
        pass

    elif question.lower().startswith("plan:") or "add_event_to_calendar" in agent_reply:
        query = question.replace("plan:", "").strip()

        messages.append({"role": "user", "content": query})
            # use chain to add event to calendar
        answer, prompt_tokens, completion_tokens, total_tokens, formatted_query_to_calendar = add_event_from_shiro(query)

        my_bar.progress(60, text="event added")
        
        # print_response_label("I added event with this info: \n" + formatted_query_to_calendar)
        answer_area.text_area('Answer', "I added event with this info: \n" + formatted_query_to_calendar)

        connect_to_phpmyadmin.insert_message_to_database(name, question, answer, messages) #insert to Azure DB to user table    
        connect_to_phpmyadmin.add_pair_to_general_table(name, answer) #to general table with all  questions and answers
        connect_to_phpmyadmin.send_chatgpt_usage_to_database(prompt_tokens, completion_tokens, total_tokens) #to A DB with usage stats
        
        
        my_bar.progress(100, text="done")
        # running = False
        # progress(100,"showed, done")    
        
    elif question.lower().startswith("db:") or "database_search" in agent_reply:
        query = question.replace("db:", "").strip()
        messages.append({"role": "user", "content": query})
        answer = search_chroma_db(query)
        
        my_bar.progress(60, text="got answer")
        answer_area.text_area('Answer', answer)
        
        connect_to_phpmyadmin.insert_message_to_database(name, question, answer, messages) #insert to Azure DB to user table    
        connect_to_phpmyadmin.add_pair_to_general_table(name, answer) #to general table with all  questions and answers


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
        print("---------------------------------")

        # beep = "cute_beep" #END OF ANSWER
        # play_audio_fn(beep)

        #     #show history in text widget
        # progress(90,"showing in text box...")
        # #show_history_from_db_widget.delete('1.0', 'end')
        # display_messages_from_database_only(take_history_from_database())
        
        # running = False
        # progress(100,"saved to DB, done")











progress_label.text('Done!')
my_bar.progress(100, text="Done!")
print("-------end of code---------")










 # BUTTON TO iniciate the process with question from input
    
    #answer = testujemy(text_input)
    #answer2 = search_chroma_db(text_input)
    #st.write("Answer: ", answer2)
    