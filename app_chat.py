import time
import os
import joblib
import streamlit as st
import google.generativeai as genai
GOOGLE_API_KEY=os.environ.get('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

new_chat_id = f'{time.time()}'
MODEL_ROLE = 'ai'
AI_AVATAR_ICON = '✨'

# Create a data/ folder if it doesn't already exist
try:
    os.mkdir('data/')
except:
    # data/ folder already exists
    pass

# Load past chats (if available)
try:
    past_chats: dict = joblib.load('data/past_chats_list')
except:
    past_chats = {}

st.set_page_config(page_title="Gemini", layout="wide")

st.markdown("""
    <style>
        .reportview-container {
            margin-top: -2em;
        }
        .stDeployButton {display:none;}
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)


def load_chat_history(chat_id):
    try:
        st.session_state.messages = joblib.load(f'data/{chat_id}-st_messages')
        st.session_state.gemini_history = joblib.load(f'data/{chat_id}-gemini_messages')
    except FileNotFoundError:
        st.session_state.messages = []
        st.session_state.gemini_history = []


def start_new_chat():
    st.session_state.chat_id = new_chat_id
    st.session_state.messages = []
    st.session_state.gemini_history = []


def generate_chat_title(input_text):
    words = input_text.split()
    # Use the first four words or the entire text if it's shorter
    return ' '.join(words[:4])


with st.sidebar:
    st.write('# Chat Sessions')
    # New Chat button
    if st.button('New Chat'):
        start_new_chat()
        
    for chat_id, chat_title in past_chats.items():
        if st.sidebar.button(chat_title):
            # Load the selected chat
            st.session_state.chat_id = chat_id
            st.session_state.chat_title = chat_title
            load_chat_history(chat_id)
            


st.write('# Chat with Gemini')

# Chat history (allows to ask multiple questions)
try:
    st.session_state.messages = joblib.load(
        f'data/{st.session_state.chat_id}-st_messages'
    )
    st.session_state.gemini_history = joblib.load(
        f'data/{st.session_state.chat_id}-gemini_messages'
    )
except:
    st.session_state.messages = []
    st.session_state.gemini_history = []
st.session_state.model = genai.GenerativeModel('gemini-pro')
st.session_state.chat = st.session_state.model.start_chat(
    history=st.session_state.gemini_history,
)

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(
        name=message['role'],
        avatar=message.get('avatar'),
    ):
        st.markdown(message['content'])

# React to user input
if prompt := st.chat_input('Your message here...'):
    # Save this as a chat for later
    st.session_state.chat_id = st.session_state.chat_id or new_chat_id

    # Display user message in chat message container
    with st.chat_message('user'):
        st.markdown(prompt)

    ## Send message to AI
    response = st.session_state.chat.send_message(
        prompt,
        stream=True,
    )
    # Display assistant response in chat message container
    with st.chat_message(
        name=MODEL_ROLE,
        avatar=AI_AVATAR_ICON,
    ):
        message_placeholder = st.empty()
        full_response = ''
        assistant_response = response
        # Streams in a chunk at a time
        for chunk in response:
            # Simulate stream of chunk
            # TODO: Chunk missing `text` if API stops mid-stream ("safety"?)
            for ch in chunk.text.split(' '):
                full_response += ch + ' '
                time.sleep(0.05)
                # Rewrites with a cursor at end
                message_placeholder.write(full_response + '▌')
        # Write full message with placeholder
        message_placeholder.write(full_response)


    # Add user message to chat history
    if st.session_state.chat_id not in past_chats.keys():
        past_chats[st.session_state.chat_id] = generate_chat_title(prompt)
        joblib.dump(past_chats, 'data/past_chats_list')
        
    st.session_state.messages.append(
        dict(
            role='user',
            content=prompt,
        )
    )
    # Add assistant response to chat history
    st.session_state.messages.append(
        dict(
            role=MODEL_ROLE,
            content=st.session_state.chat.history[-1].parts[0].text,
            avatar=AI_AVATAR_ICON,
        )
    )
    st.session_state.gemini_history = st.session_state.chat.history
    # Save to file
    joblib.dump(
        st.session_state.messages,
        f'data/{st.session_state.chat_id}-st_messages',
    )
    joblib.dump(
        st.session_state.gemini_history,
        f'data/{st.session_state.chat_id}-gemini_messages',
    )
    