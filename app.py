import os
import requests
import streamlit as st
from supabase import create_client, Client

# Configuração da página
st.set_page_config(
    page_title="J.A.R.V.I.S.",
    page_icon="🤖",
    layout="centered"
)

# Estilização CSS HUD Futurista
st.markdown("""
<style>
    /* Importação de fonte futurista */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@500;600;700&display=swap');

    /* Fundo geral e remoção de elementos brancos */
    .stApp, [data-testid="stHeader"], [data-testid="stBottom"] {
        background-color: #050811 !important;
        color: #00f0ff !important;
    }
    
    body {
        font-family: 'Rajdhani', sans-serif;
    }

    /* Cabeçalho HUD */
    .hud-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 3rem;
        font-weight: 900;
        text-align: center;
        color: #00f0ff;
        text-shadow: 0 0 20px rgba(0, 240, 255, 0.8), 0 0 40px rgba(0, 240, 255, 0.3);
        letter-spacing: 4px;
        margin-top: -20px;
    }
    
    .hud-subtitle {
        font-family: 'Orbitron', sans-serif;
        text-align: center;
        color: #ffb703;
        font-size: 0.75rem;
        letter-spacing: 3px;
        margin-bottom: 30px;
        opacity: 0.9;
    }

    /* Estilo das caixas de mensagem do chat */
    [data-testid="stChatMessage"] {
        background: rgba(10, 20, 38, 0.7) !important;
        border: 1px solid rgba(0, 240, 255, 0.2) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        margin-bottom: 12px !important;
    }

    /* Mensagem do Assistente (Jarvis) */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        border-left: 4px solid #00f0ff !important;
        box-shadow: -5px 0 15px rgba(0, 240, 255, 0.2);
    }

    /* Mensagem do Utilizador */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        border-right: 4px solid #ffb703 !important;
        box-shadow: 5px 0 15px rgba(255, 183, 3, 0.2);
    }

    /* Personalização do gravador de áudio */
    [data-testid="stAudioInput"] {
        background-color: rgba(10, 20, 38, 0.8) !important;
        border: 1px solid rgba(0, 240, 255, 0.3) !important;
        border-radius: 12px !important;
        padding: 8px !important;
    }

    /* Campo de entrada de texto */
    [data-testid="stChatInput"] {
        border-radius: 12px !important;
        border: 1px solid rgba(0, 240, 255, 0.4) !important;
        background-color: #0a1426 !important;
    }

    /* Esconde marca d'água e menus do Streamlit */
    #MainMenu, footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Título HUD
st.markdown('<div class="hud-title">J.A.R.V.I.S.</div>', unsafe_allow_html=True)
st.markdown('<div class="hud-subtitle">MARK VII // SYSTEM ONLINE</div>', unsafe_allow_html=True)

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        pass

def load_history():
    if supabase:
        try:
            response = supabase.table("chat_history").select("role, content").order("id", desc=False).execute()
            return response.data if response.data else []
        except Exception:
            pass
    return []

def save_message(role: str, content: str):
    if supabase:
        try:
            supabase.table("chat_history").insert({"role": role, "content": content}).execute()
        except Exception:
            pass

if "messages" not in st.session_state:
    st.session_state.messages = load_history()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def query_jarvis(user_input: str):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    save_message("user", user_input)

    system_prompt = {
        "role": "system",
        "content": "O teu nome é Jarvis. Tu és um assistente virtual de inteligência avançada, refinado, direto e leal ao teu criador. Responde sempre em português com elegância e clareza."
    }
    
    formatted_messages = [system_prompt] + [
        {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
    ]

    with st.chat_message("assistant"):
        with st.spinner("Analisando dados..."):
            try:
                response = requests.post(
                    "https://text.pollinations.ai/",
                    json={"messages": formatted_messages, "model": "openai"},
                    timeout=30
                )

                try:
                    data = response.json()
                    bot_response = data.get("content", data.get("response", str(data))) if isinstance(data, dict) else str(data)
                except Exception:
                    bot_response = response.text

                if not bot_response or bot_response.strip() == "{}":
                    bot_response = "Sistemas operacionais indisponíveis no momento. Repita a instrução, mestre."

            except Exception as e:
                bot_response = f"Erro nos sensores: {e}"

            st.markdown(bot_response)
            st.session_state.messages.append({"role": "assistant", "content": bot_response})
            save_message("assistant", bot_response)

# Microfone
audio_input = st.audio_input("🎙️ Comando de Voz")
if audio_input is not None:
    audio_bytes = audio_input.read()
    if "last_audio" not in st.session_state or st.session_state.last_audio != audio_bytes:
        st.session_state.last_audio = audio_bytes
        with st.spinner("Descodificando frequência de voz..."):
            try:
                files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
                res = requests.post("https://text.pollinations.ai/transcribe", files=files, timeout=30)
                transcribed_text = res.text.strip()

                if transcribed_text and not transcribed_text.startswith("Error"):
                    query_jarvis(transcribed_text)
                    st.rerun()
            except Exception:
                pass

# Caixa de Entrada
if prompt := st.chat_input("Instrução do sistema..."):
    query_jarvis(prompt)