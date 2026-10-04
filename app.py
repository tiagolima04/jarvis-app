import os
import requests
import streamlit as st
from supabase import create_client, Client

# Configuração da página e tema visual futurista (Dark / Jarvis Tech Style)
st.set_page_config(
    page_title="JARVIS AI",
    page_icon="🤖",
    layout="centered"
)

# Estilização CSS customizada
st.markdown("""
<style>
    /* Fundo geral escuro tech */
    .stApp {
        background-color: #0b0f19;
        color: #e0e6ed;
    }
    
    /* Título com brilho azul ciano */
    .jarvis-title {
        font-family: 'Trebuchet MS', sans-serif;
        font-size: 2.8rem;
        font-weight: 800;
        text-align: center;
        color: #00d2ff;
        text-shadow: 0px 0px 15px rgba(0, 210, 255, 0.6);
        margin-bottom: 5px;
    }
    
    .jarvis-subtitle {
        text-align: center;
        color: #8a9ba8;
        font-size: 0.95rem;
        margin-bottom: 25px;
        letter-spacing: 1px;
    }

    /* Estilo das caixas de mensagem do usuário e assistente */
    [data-testid="stChatMessage"] {
        background-color: #131a29;
        border: 1px solid #1f2a3e;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 10px;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.3);
    }

    /* Destaque para caixa do assistente (Jarvis) */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        border-left: 4px solid #00d2ff;
        background-color: #0e1626;
    }

    /* Destaque para caixa do utilizador */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        border-right: 4px solid #ffb703;
    }
</style>
""", unsafe_allow_html=True)

# Título do App
st.markdown('<div class="jarvis-title">🤖 J.A.R.V.I.S.</div>', unsafe_allow_html=True)
st.markdown('<div class="jarvis-subtitle">SISTEMA INTELIGENTE DE ASSISTÊNCIA PESSOAL</div>', unsafe_allow_html=True)

# Conexão ao Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.warning(f"Aviso: Não foi possível conectar ao Supabase: {e}")

# Função para carregar histórico do Supabase
def load_history():
    if supabase:
        try:
            response = supabase.table("chat_history").select("role, content").order("id", desc=False).execute()
            return response.data if response.data else []
        except Exception as e:
            st.error(f"Erro ao carregar histórico: {e}")
    return []

# Função para salvar mensagens no Supabase
def save_message(role: str, content: str):
    if supabase:
        try:
            supabase.table("chat_history").insert({"role": role, "content": content}).execute()
        except Exception as e:
            st.error(f"Erro ao salvar mensagem no Supabase: {e}")

# Inicialização do histórico de mensagens
if "messages" not in st.session_state:
    st.session_state.messages = load_history()

# Exibe o histórico de mensagens
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Função para enviar a consulta para o Pollinations AI
def query_jarvis(user_input: str):
    # Regista a mensagem do utilizador
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    save_message("user", user_input)

    # Prepara o prompt de sistema e mensagens
    system_prompt = {
        "role": "system",
        "content": "O teu nome é Jarvis (J.A.R.V.I.S.). Tu és um assistente virtual pessoal altamente inteligente, educado, refinado e prestativo, exatamente como a IA do Homem de Ferro. Responde sempre em português do Brasil/Portugal de forma clara, natural e elegante. Quando te perguntarem quem és, confirma orgulhosamente que és o Jarvis."
    }
    
    formatted_messages = [system_prompt] + [
        {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
    ]

    # Processa a resposta
    with st.chat_message("assistant"):
        with st.spinner("Processando dados, mestre..."):
            try:
                response = requests.post(
                    "https://text.pollinations.ai/",
                    json={
                        "messages": formatted_messages,
                        "model": "openai"
                    },
                    timeout=30
                )

                try:
                    data = response.json()
                    if isinstance(data, dict):
                        bot_response = data.get("content", data.get("response", str(data)))
                    else:
                        bot_response = str(data)
                except Exception:
                    bot_response = response.text

                if not bot_response or bot_response.strip() == "{}":
                    bot_response = "Desculpe, mestre. Ocorreu um pequeno ruído na comunicação. Pode repetir a instrução?"

            except Exception as e:
                bot_response = f"Erro na conexão do sistema: {e}"

            st.markdown(bot_response)
            st.session_state.messages.append({"role": "assistant", "content": bot_response})
            save_message("assistant", bot_response)

# --- ENTRADA POR ÁUDIO (MICROFONE) ---
st.write("---")
audio_input = st.audio_input("🎙️ Gravar mensagem de voz")

if audio_input is not None:
    # Evita reprocessar o mesmo áudio ao atualizar a página
    audio_bytes = audio_input.read()
    if "last_audio" not in st.session_state or st.session_state.last_audio != audio_bytes:
        st.session_state.last_audio = audio_bytes
        with st.spinner("Transcrevendo áudio..."):
            try:
                # Transcrição enviando o arquivo para a API de fala do Pollinations
                files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
                res = requests.post("https://text.pollinations.ai/transcribe", files=files, timeout=30)
                transcribed_text = res.text.strip()

                if transcribed_text and not transcribed_text.startswith("Error"):
                    st.info(f"🗣️ **Voz identificada:** *\"{transcribed_text}\"*")
                    query_jarvis(transcribed_text)
                    st.rerun()
                else:
                    st.error("Não foi possível transcrever o áudio com clareza.")
            except Exception as e:
                st.error(f"Erro ao processar áudio: {e}")

# --- ENTRADA POR TEXTO ---
if prompt := st.chat_input("Insira o seu comando, mestre..."):
    query_jarvis(prompt)