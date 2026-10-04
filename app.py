import os
import streamlit as st
import requests
from supabase import create_client, Client

st.set_page_config(page_title="Jarvis", page_icon="🤖")
st.title("🤖 Jarvis")

# Conectando ao Supabase utilizando as variáveis do ficheiro .env ou do Render
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.warning(f"Aviso: Não foi possível conectar ao Supabase: {e}")

# Função para carregar o histórico gravado no Supabase
def load_history():
    if supabase:
        try:
            response = supabase.table("chat_history").select("role, content").order("id", desc=False).execute()
            return response.data if response.data else []
        except Exception as e:
            st.error(f"Erro ao carregar histórico: {e}")
    return []

# Função para guardar cada nova mensagem no Supabase
def save_message(role: str, content: str):
    if supabase:
        try:
            supabase.table("chat_history").insert({"role": role, "content": content}).execute()
        except Exception as e:
            st.error(f"Erro ao salvar mensagem: {e}")

# Inicializa o histórico na sessão (busca do Supabase se disponível)
if "messages" not in st.session_state:
    st.session_state.messages = load_history()

# Exibe as mensagens na interface do Streamlit
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Caixa de entrada para o utilizador escrever
if prompt := st.chat_input("Como posso ajudar, mestre?"):
    # Regista a pergunta do utilizador
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    save_message("user", prompt)

    # Faz o pedido para a API de IA
    with st.chat_message("assistant"):
        with st.spinner("A pensar..."):
            try:
                # Monta as mensagens para enviar o contexto completo
                formatted_messages = [
                    {"role": m["role"], "content": m["content"]} 
                    for m in st.session_state.messages
                ]
                
                response = requests.post(
                    "https://text.pollinations.ai/",
                    json={
                        "messages": formatted_messages,
                        "model": "openai"
                    },
                    timeout=30
                )

                # Tratamento para garantir que recebemos apenas texto limpo
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        bot_response = data.get("content", data.get("response", str(data)))
                    else:
                        bot_response = str(data)
                except Exception:
                    bot_response = response.text

                # Caso retorne um texto vazio ou nulo
                if not bot_response or bot_response.strip() == "{}":
                    bot_response = "Desculpe, não consegui processar a resposta. Pode tentar perguntar novamente?"

            except Exception as e:
                bot_response = f"Erro na conexão com a IA: {e}"

            # Exibe a resposta e guarda no histórico
            st.markdown(bot_response)
            st.session_state.messages.append({"role": "assistant", "content": bot_response})
            save_message("assistant", bot_response)