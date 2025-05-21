import streamlit as st
from src.config.style import set_style
import google.generativeai as genai
from PIL import Image
from io import BytesIO
import base64
import requests
from src.config import settings
from src.utils.api_helpers import generate_stable_diffusion_image

# ========== CONFIGURAÇÃO INICIAL ==========
st.set_page_config(page_title="Assistente IA", layout="centered")
set_style()  # Aplica o CSS personalizado

# Configure a API do Gemini
genai.configure(api_key=settings.GOOGLE_API_KEY)

# Verifica se as chaves de API estão configuradas
if not settings.STABILITY_API_KEY:
    st.warning("Chave da API do Stability AI não encontrada. A geração de imagens não funcionará.")

# ========== FUNÇÕES AUXILIARES ==========
def load_image(image_path, size=(300, 300)):
    """Carrega imagem local ou URL e retorna como base64 ou None se falhar"""
    try:
        if image_path.startswith(('http://', 'https://')):
            response = requests.get(image_path)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))
        elif image_path.startswith('data:image'):
            header, data = image_path.split(',', 1)
            img = Image.open(BytesIO(base64.b64decode(data)))
        else:
            img = Image.open(image_path)

        img = img.convert("RGBA").resize(size, Image.LANCZOS)
        buffered = BytesIO()
        img.save(buffered, format="PNG", quality=95)
        return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode()}"
    except Exception as e:
        st.error(f"Erro ao carregar imagem: {str(e)}")
        return None

# Avatares
USER_AVATAR = "https://static.wikia.nocookie.net/chiikawa/images/4/43/YahaUsagi.png/revision/latest?cb=20240709065537"
BOT_AVATAR = "https://static.wikia.nocookie.net/chiikawa/images/2/2c/AdorableCutieChiikawa.png/revision/latest?cb=20240709065538"

# ========== INTERFACE ==========
chiikawa_img = load_image("src/assets/imagens/chiikawa.webp", size=(150, 150))
if chiikawa_img:
    st.image(chiikawa_img)

modo = st.selectbox("Escolha o modo:", ["Chatbot de texto", "Geração de imagem"])

# ========== MODO CHAT ==========
if modo == "Chatbot de texto":
    st.title("💬 Chatbot da Vivi")

    user_avatar = load_image(USER_AVATAR, size=(300, 300))
    bot_avatar = load_image(BOT_AVATAR, size=(450, 450))

    if "messages" not in st.session_state:
        st.session_state.messages = []

    with st.container():
        st.markdown("<div style='max-height: 400px; overflow-y: auto; padding: 10px;'>", unsafe_allow_html=True)

        for msg in st.session_state.messages:
            avatar = user_avatar if msg["role"] == "user" else bot_avatar
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

        st.markdown("</div>", unsafe_allow_html=True)

    if prompt := st.chat_input("Digite sua pergunta..."):
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.spinner("Pensando..."):
            try:
                model = genai.GenerativeModel("models/gemini-1.5-flash-latest")
                response = model.generate_content(prompt)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                st.rerun()
            except Exception as e:
                st.error(f"Erro: {str(e)}")

# ========== MODO IMAGEM ==========
else:
    st.title("🖼️ Gerador de Imagens")

    if "generated_image" not in st.session_state:
        st.session_state.generated_image = None

    with st.form("image_form"):
        prompt = st.text_area("Descreva a imagem:")
        col1, col2 = st.columns(2)
        width = col1.selectbox("Largura", [512, 768, 1024])
        height = col2.selectbox("Altura", [512, 768, 1024])
        style_preset = st.selectbox("Estilo (Opcional)", ["Nenhum"] + list(settings.STYLE_PRESETS.keys()))
        selected_style = settings.STYLE_PRESETS.get(style_preset) if style_preset != "Nenhum" else None

        submitted = st.form_submit_button("Gerar Imagem")
        if submitted:
            if prompt:
                with st.spinner("Criando imagem..."):
                    try:
                        image = generate_stable_diffusion_image(
                            prompt,
                            width,
                            height,
                            style_preset=selected_style
                        )
                        st.session_state.generated_image = image
                        st.success("Imagem gerada com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao gerar imagem: {str(e)}")
            else:
                st.warning("Digite um prompt para gerar a imagem!")

    # Exibe imagem e botão de download fora do form
    if st.session_state.generated_image:
        st.image(
            st.session_state.generated_image,
            caption="Imagem gerada pela IA",
            use_container_width=True
        )

        buf = BytesIO()
        st.session_state.generated_image.save(buf, format="PNG")
        st.download_button(
            label="📥 Baixar imagem",
            data=buf.getvalue(),
            file_name="imagem_gerada.png",
            mime="image/png"
        )
