import streamlit as st
from ai.agent import ask_ai

st.title("AI Market Chatbot")

if "messages" not in st.session_state:
    st.session_state.messages = []

user_input = st.chat_input("Ask me anything about markets...")

if user_input:
    st.session_state.messages.append(("user", user_input))

    reply = ask_ai(user_input)

    st.session_state.messages.append(("assistant", reply))

for role, message in st.session_state.messages:
    st.chat_message(role).write(message)