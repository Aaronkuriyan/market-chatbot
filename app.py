import streamlit as st
from services.crypto import get_bitcoin_price

st.title("My Market Chatbot")

if "messages" not in st.session_state:
    st.session_state.messages = []

user_input = st.chat_input("Ask me about Bitcoin...")

if user_input:
    st.session_state.messages.append(("user", user_input))

    if "bitcoin" in user_input.lower():
        price = get_bitcoin_price()
        reply = f"Bitcoin price is ${price}"
    else:
        reply = "Ask me about Bitcoin price!"

    st.session_state.messages.append(("assistant", reply))

for role, message in st.session_state.messages:
    st.chat_message(role).write(message)