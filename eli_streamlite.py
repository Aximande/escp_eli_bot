import streamlit as st
import openai

# Définir la clé API OpenAI
openai.api_key = "votre_clé_api_openai"  # Remplacez par votre clé API

# Configurer la page Streamlit
st.set_page_config(page_title="Assistant ELI", layout="wide")

# ---- CSS personnalisé ----
st.markdown("""
    <style>
    body {
        background-color: #E0ECFF;
    }
    .stButton > button {
        background-color: #0080FF;
        color: white;
        border-radius: 8px;
        padding: 0.5em 1em;
        font-size: 1.2em;
    }
    .chat-container {
        max-width: 600px;
        margin: 0 auto;
        background-color: white;
        border-radius: 10px;
        padding: 2em;
    }
    .chat-message {
        display: flex;
        margin-bottom: 15px;
    }
    .chat-message.user {
        justify-content: flex-end;
    }
    .chat-message.assistant {
        justify-content: flex-start;
    }
    .chat-bubble {
        padding: 10px 20px;
        border-radius: 15px;
        max-width: 80%;
        font-size: 1.1em;
        background-color: #E0ECFF;
    }
    .chat-bubble.user {
        background-color: #8C61FF;
        color: white;
    }
    .chat-bubble.assistant {
        background-color: #0080FF;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# ---- Page d'Accueil ----
def home_page():
    st.title("Bienvenue sur ELI")
    st.write("""
        Votre assistant de soutien moral et psychologique confidentiel.
        Cliquez sur le bouton ci-dessous pour commencer à discuter avec ELI.
    """)

    # Bouton pour démarrer le chat
    if st.button("Démarrer le Chat"):
        chat_page()

# ---- Interface de Chat avec OpenAI ----
def chat_page():
    st.subheader("Dialogue avec ELI")
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    # Affichage des messages précédents
    for chat in st.session_state.messages:
        if chat['role'] == 'user':
            st.markdown(f'<div class="chat-message user"><div class="chat-bubble user">{chat["content"]}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-message assistant"><div class="chat-bubble assistant">{chat["content"]}</div></div>', unsafe_allow_html=True)

    # Saisie du message utilisateur
    user_input = st.text_input("Votre message", key="user_input")
    
    if user_input:
        # Ajouter le message de l'utilisateur à l'historique
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Appel à l'API OpenAI GPT
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Ou un autre modèle de votre choix
            messages=st.session_state.messages,
            max_tokens=150
        )

        assistant_reply = response['choices'][0]['message']['content']

        # Ajouter la réponse de l'assistant à l'historique
        st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

        # Afficher la réponse de l'assistant
        st.markdown(f'<div class="chat-message assistant"><div class="chat-bubble assistant">{assistant_reply}</div></div>', unsafe_allow_html=True)

    st.divider()

    # ---- EVA (Échelle Visuelle Analogique) ----
    st.subheader("Évaluez votre douleur émotionnelle")
    pain_level = st.slider("Quel est votre niveau de souffrance émotionnelle aujourd'hui ?", 0, 10, 5)
    
    if pain_level < 4:
        st.success("Souffrance légère")
    elif pain_level < 7:
        st.warning("Souffrance modérée")
    else:
        st.error("Souffrance intense")
    
    st.divider()

    # ---- Questionnaire K6 ----
    st.subheader("Questionnaire K6 (extrait)")
    
    with st.form("k6_form"):
        q1 = st.selectbox("Dernièrement, vous êtes-vous senti(e) très nerveux(se) ?", ["Jamais", "Rarement", "Parfois", "Souvent", "Très souvent"])
        q2 = st.selectbox("Avez-vous eu des difficultés à vous détendre ?", ["Jamais", "Rarement", "Parfois", "Souvent", "Très souvent"])
        submitted = st.form_submit_button("Soumettre")
        
        if submitted:
            st.success("Merci pour vos réponses. Elles seront prises en compte de façon anonyme.")
    
    st.divider()

    # ---- Alerte de détresse ----
    st.subheader("Alerte urgente")
    
    if st.button("Envoyer une alerte de détresse"):
        st.warning("Une alerte a été envoyée à un référent de confiance.")

# --- Lancement de la page d'accueil ou du chat ----
if st.session_state.get("chat_started", False):
    chat_page()
else:
    home_page()
