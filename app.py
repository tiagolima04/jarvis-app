import streamlit as st
import requests

st.set_page_config(page_title="Jarvis AI", page_icon="🤖")
st.title("🤖 Jarvis")

# Histórico de mensagens
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe mensagens anteriores
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Campo de entrada do usuário
if prompt := st.chat_input("Como posso ajudar, mestre?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Resposta via Pollinations.ai (API gratuita sem chave)
    with st.chat_message("assistant"):
        url = f"https://text.pollinations.ai/{prompt}?system=Você é o Jarvis, um assistente pessoal inteligente e direto."
        
        try:
            response = requests.get(url)
            answer = response.text
        except Exception as e:
            answer = "Desculpe, mestre. Tive um problema ao conectar ao meu servidor."

        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})