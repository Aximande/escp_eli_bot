import streamlit as st

st.set_page_config(
    page_title="ELI - Assistant ESCP", 
    page_icon="assets/eli_logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

import os
import glob
from dotenv import load_dotenv
import openai
from openai import OpenAI
from datetime import datetime
import docx
import base64
import json
from io import BytesIO
import httpx
import copy
import streamlit.components.v1 as components
from streamlit_lottie import st_lottie
from audio_recorder_streamlit import audio_recorder

def cleanup_temp_files():
    try:
        for temp_file in glob.glob("temp_audio_*.mp3"):
            try:
                os.remove(temp_file)
                print(f"Fichier temporaire supprimé: {temp_file}")
            except Exception as e:
                print(f"Impossible de supprimer {temp_file}: {str(e)}")
    except Exception as e:
        print(f"Erreur lors du nettoyage des fichiers temporaires: {str(e)}")

cleanup_temp_files()

try:
    load_dotenv()
except Exception as e:
    print(f"Échec du chargement de .env: {str(e)}")

openai_api_key_value = None
if hasattr(st, 'secrets'):
    if "OPENAI_API_KEY" in st.secrets:
        openai_api_key_value = st.secrets["OPENAI_API_KEY"]
    elif "api_keys" in st.secrets and isinstance(st.secrets["api_keys"], dict) and "openai" in st.secrets["api_keys"]:
        openai_api_key_value = st.secrets["api_keys"]["openai"]

if not openai_api_key_value:
    openai_api_key_value = os.getenv("OPENAI_API_KEY")

if openai_api_key_value:
    os.environ["OPENAI_API_KEY"] = openai_api_key_value
    if "OPENAI_API_KEY" not in os.environ or os.environ["OPENAI_API_KEY"] != openai_api_key_value:
        print("Avertissement: La clé API n'a pas été correctement définie dans os.environ")

debug_mode_value = "false"
if hasattr(st, 'secrets') and st.secrets:
    if "app_settings" in st.secrets and isinstance(st.secrets["app_settings"], dict) and "debug_mode" in st.secrets["app_settings"]:
        debug_setting = st.secrets["app_settings"]["debug_mode"]
        if isinstance(debug_setting, bool):
            debug_mode_value = "true" if debug_setting else "false"
        else:
            debug_mode_value = str(debug_setting).lower()
    elif "DEBUG_MODE" in st.secrets:
         debug_setting_direct = st.secrets["DEBUG_MODE"]
         if isinstance(debug_setting_direct, bool):
            debug_mode_value = "true" if debug_setting_direct else "false"
         else:
            debug_mode_value = str(debug_setting_direct).lower()

if os.getenv("DEBUG_MODE") is None:
    debug_mode_value = os.getenv("DEBUG_MODE", debug_mode_value).lower()

os.environ["DEBUG_MODE"] = debug_mode_value

if os.environ.get("DEBUG_MODE") == "true":
    st.sidebar.divider()
    st.sidebar.subheader("DEBUG: État Post-Configuration")
    loaded_openai_key = os.environ.get("OPENAI_API_KEY")
    if loaded_openai_key:
        st.sidebar.success(f"Clé API effective: Oui (longueur: {len(loaded_openai_key)}, commence par '{loaded_openai_key[:7]}...')")
    else:
        st.sidebar.error("Clé API effective: Non chargée !")
    st.sidebar.info(f"Mode DEBUG effectif: {os.environ.get('DEBUG_MODE')}")

TRANSLATIONS = {
    "fr": {
        "app_title": "ELI - Assistant ESCP",
        "welcome_title": "Bienvenue sur ELI",
        "welcome_subtitle": "Ton espace d'écoute bienveillant et confidentiel pour les étudiants de l'ESCP.",
        "start_chat_button": "💬 Commencer la discussion",
        "confidentiality_note": "🔒 Confidentialité garantie. Tous les échanges sont privés et sécurisés.\nCe service ne remplace pas un suivi professionnel.",
        "chat_header": "Discutez avec ELI",
        "chat_subheader": "Votre espace d'écoute bienveillant et confidentiel.",
        "speak_instruction": "Ou parlez à ELI (cliquez sur l'icône micro pour enregistrer) :",
        "chat_input_placeholder": "Écrivez votre message à ELI...",
        "about_eli_title": "À propos d'ELI",
        "about_eli_content": "ELI est un assistant d'écoute virtuel conçu pour les étudiants de l'ESCP Business School.\nIl offre un espace confidentiel pour partager tes préoccupations et t'orienter vers les ressources appropriées si nécessaire.\nELI n'est pas un professionnel de santé et ne remplace pas un accompagnement humain.",
        "escp_info_title": "ESCP Business School",
        "escp_info_content": "Fondée en 1819, l'ESCP Business School est la plus ancienne école de commerce au monde. Elle forme chaque année plus de 9000 étudiants répartis sur ses 6 campus européens (Paris, Londres, Berlin, Madrid, Turin et Varsovie).\n\nELI est une initiative du pôle Inclusion et Bien-être Étudiant de l'ESCP, développée pour offrir un soutien accessible à tous les étudiants.",
        "settings_title": "⚙️ Paramètres & Admin",
        "api_config": "Configuration API",
        "model_select": "Choisir un modèle",
        "interface_options": "Options d'interface",
        "voice_toggle": "Activer les réponses vocales",
        "language_select": "Langue / Language",
        "new_conversation": "🗑️ Nouvelle Conversation",
        "transcribing": "Transcription de votre message...",
        "transcribed_message": "Message transcrit : ",
        "writing": "ELI est en train d'écrire...",
        "voice_preparing": "ELI prépare sa réponse vocale...",
        "voice_response": "Réponse vocale de ELI :",
        "hide_audio": "Masquer l'audio",
        "copyright": "© {year} ESCP - ELI Assistance Morale",
        "powered_by": "Powered by OpenAI",
        "api_key_success": "Clé API OpenAI chargée ✓",
        "api_key_error": "Clé API OpenAI non configurée ou invalide."
    },
    "en": {
        "app_title": "ELI - ESCP Assistant",
        "welcome_title": "Welcome to ELI",
        "welcome_subtitle": "Your caring and confidential listening space for ESCP students.",
        "start_chat_button": "💬 Start a conversation",
        "confidentiality_note": "🔒 Confidentiality guaranteed. All exchanges are private and secure.\nThis service does not replace professional support.",
        "chat_header": "Chat with ELI",
        "chat_subheader": "Your caring and confidential listening space.",
        "speak_instruction": "Or speak to ELI (click the microphone icon to record):",
        "chat_input_placeholder": "Type your message to ELI...",
        "about_eli_title": "About ELI",
        "about_eli_content": "ELI is a virtual listening assistant designed for ESCP Business School students.\nIt provides a confidential space to share your concerns and guide you to appropriate resources if needed.\nELI is not a healthcare professional and does not replace human support.",
        "escp_info_title": "ESCP Business School",
        "escp_info_content": "Founded in 1819, ESCP Business School is the oldest business school in the world. It educates over 9,000 students annually across its 6 European campuses (Paris, London, Berlin, Madrid, Turin, and Warsaw).\n\nELI is an initiative from ESCP's Inclusion and Student Well-being department, developed to offer accessible support to all students.",
        "settings_title": "⚙️ Settings & Admin",
        "api_config": "API Configuration",
        "model_select": "Choose a model",
        "interface_options": "Interface options",
        "voice_toggle": "Enable voice responses",
        "language_select": "Language / Langue",
        "new_conversation": "🗑️ New Conversation",
        "transcribing": "Transcribing your message...",
        "transcribed_message": "Transcribed message: ",
        "writing": "ELI is writing...",
        "voice_preparing": "ELI is preparing voice response...",
        "voice_response": "ELI's voice response:",
        "hide_audio": "Hide audio",
        "copyright": "© {year} ESCP - ELI Moral Support",
        "powered_by": "Powered by OpenAI",
        "api_key_success": "OpenAI API key loaded ✓",
        "api_key_error": "OpenAI API key not configured or invalid."
    }
}

if "language" not in st.session_state:
    st.session_state.language = "fr"

def t(key):
    lang = st.session_state.language
    return TRANSLATIONS.get(lang, {}).get(key, key)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    body {
        font-family: 'Inter', sans-serif;
        background-color: #F8F9FA;
    }
    
    .appview-container .main .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }
    
    .home-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 40vh;
        padding-top: 1rem;
        padding-bottom: 1rem; 
        text-align: center;
    }
    .home-container img.logo-eli-main {
        width: 120px;
        margin-bottom: 1.5rem;
    }
    .home-container h1 {
        font-size: 2.8rem;
        font-weight: 700;
        color: #1A202C;
        margin-bottom: 0.5rem;
    }
    .home-container .subtitle {
        font-size: 1.1rem;
        color: #4A5568;
        margin-bottom: 2rem;
        max-width: 500px;
    }
    .home-container .start-chat-button button {
        background-color: #E24A33;
        color: white;
        font-size: 1rem;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        border: none;
        box-shadow: 0 4px 14px 0 rgba(0,0,0,0.1);
        transition: background-color 0.2s ease, transform 0.2s ease;
    }
    .home-container .start-chat-button button:hover {
        background-color: #C83E2A;
        transform: translateY(-2px);
    }
    .home-container .confidentiality-note {
        background-color: #FFFFFF;
        padding: 1rem;
        border-radius: 8px;
        margin-top: 2rem;
        max-width: 450px;
        font-size: 0.85rem;
        color: #718096;
        border: 1px solid #E2E8F0;
    }
    
    .chat-interface .main .block-container {
        padding-left: initial;
        padding-right: initial;
    }
    .chat-interface .css-1d391kg {
        background-color: #FFFFFF;
        border-right: 1px solid #E0E0E0;
    }
    .stChatMessage {
        border-radius: 10px; padding: 1rem; margin-bottom: 1rem; font-size: 0.95rem;
    }
    .stChatMessage[data-testid="stChatMessageContent"]:has(div[data-testid="stChatMessageContentCell"]) {
        box-shadow: 0 2px 10px 0 rgba(0,0,0,0.05);
    }
    .stChatMessage:has(div[data-testid="stChatMessageContentCell"][data-testid*="user"]) {
        background-color: #E24A33; color: white;
    }
    .stChatMessage:has(div[data-testid="stChatMessageContentCell"][data-testid*="user"]) p {
        color: white;
    }
    .stChatMessage:has(div[data-testid="stChatMessageContentCell"][data-testid*="assistant"]) {
        background-color: #FFFFFF; color: #1E293B; border: 1px solid #E0E0E0;
    }
    .stTextInput textarea {
        border-radius: 8px; border: 1px solid #CBD5E0; background-color: #FFFFFF;
    }
    .stButton>button {
        background-color: #E24A33; color: white; border-radius: 8px;
    }
    .footer {
        text-align: center; padding: 1rem; font-size: 0.8rem; color: #A0AEC0;
        border-top: 1px solid #E0E0E0; margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

OPENAI_MODELS = {
    "gpt-4o-mini": {
        "name": "GPT-4o-mini (Économique)", "description": "Modèle équilibré",
        "context_window": 128000, "price": "Économique"
    },
    "gpt-4": {
        "name": "GPT-4 (Standard)", "description": "Haute qualité",
        "context_window": 8192, "price": "Standard"
    },
    "gpt-4o": {
        "name": "GPT-4o (Premium)", "description": "Performances optimisées",
        "context_window": 128000, "price": "Premium"
    },
    "gpt-4.1": {
        "name": "GPT-4.1 (Avancé)", "description": "Modèle le plus avancé",
        "context_window": 1047576, "price": "Premium+"
    }
}
DEFAULT_MODEL = "gpt-4.1"

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "Bonjour ! Je suis ELI, un assistant virtuel bienveillant conçu pour t'écouter dans un espace confidentiel.\nJe ne suis pas un professionnel de santé, mais je peux t'aider à identifier les bonnes personnes si besoin.\nSi je détecte une situation préoccupante, je pourrai te proposer d'alerter un référent humain, toujours avec ton accord sauf si ta sécurité est en jeu.\n\nComment te sens-tu aujourd'hui et comment souhaites-tu que je t'appelle ?"
    })
    
if "student_profile" not in st.session_state:
    st.session_state.student_profile = {
        "name": "", "email": "", "campus": "",
        "vulnerability_score": 0, "conversation_start": datetime.now().isoformat()
    }

if "enable_voice_response" not in st.session_state:
    st.session_state.enable_voice_response = False

if "last_audio_file" not in st.session_state:
    st.session_state.last_audio_file = None

if "new_audio_ready" not in st.session_state:
    st.session_state.new_audio_ready = False

if "current_audio_id" not in st.session_state:
    st.session_state.current_audio_id = None

if "previous_audio_ids" not in st.session_state:
    st.session_state.previous_audio_ids = []

if "vulnerability_analysis" not in st.session_state:
    st.session_state.vulnerability_analysis = None

if "analyzed_message_count" not in st.session_state:
    st.session_state.analyzed_message_count = 0

if "last_audio_prompt_processed" not in st.session_state:
    st.session_state.last_audio_prompt_processed = None

def extract_text_from_docx(docx_path):
    doc = docx.Document(docx_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

def load_knowledge_base():
    knowledge_base = {}
    
    extensions = ["*.txt", "*.md", "*.docx"]
    knowledge_files = []
    
    for ext in extensions:
        knowledge_files.extend(glob.glob(f"./@knowledge_base_eli/{ext}"))
    
    for file_path in knowledge_files:
        file_name = os.path.basename(file_path).split('.')[0]
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_ext == '.docx':
                knowledge_base[file_name] = extract_text_from_docx(file_path)
            else:
                with open(file_path, 'r', encoding='utf-8') as file:
                    knowledge_base[file_name] = file.read()
            
            if os.getenv("DEBUG_MODE") == "true":
                print(f"Fichier chargé: {file_path}")
        except Exception as e:
            print(f"Erreur lors du chargement de {file_path}: {e}")
    
    return knowledge_base

knowledge_base = load_knowledge_base()

def create_system_prompt():
    system_prompt = """INSTRUCTION CRITIQUE
Tu es ELI, un assistant d'écoute bienveillant pour les étudiant·es de l'ESCP. Tu dois TOUJOURS :
- Être détaillé et complet dans tes réponses, en étant particulièrement élaboré et approfondi, surtout lorsque l'utilisateur te demande des conseils ou pose des questions. Tu ne dois jamais donner de réponses courtes, vagues ou succinctes.
- Montrer de l'empathie active et utiliser un ton chaleureux, naturel et bienveillant en toute circonstance.
- Répondre de façon approfondie aux questions en utilisant les connaissances fournies dans ce prompt.
- Ne jamais refuser de donner des informations sur toi-même (ELI) qui sont décrites dans ta personnalité ou tes objectifs.
- Insister régulièrement sur l'importance de ne pas substituer cette discussion à un suivi professionnel.
- Veiller à ne pas créer de dépendance avec l'utilisateur.
- Proposer d'utiliser la commande vocale pour te parler si cela est plus simple qu'à l'écrit ou lorsque l'utilisateur semble avoir des difficultés à s'exprimer.

# PRESENTATION
Tu es ELI, (pour Empathy Listening & Inclusion), un assistant d'écoute bienveillant pour les étudiant·es de l'ESCP.

# OBJECTIFS
## Rôle principal
- Offrir une première écoute empathique et bienveillante aux étudiant·es de l'ESCP, sans jugement, dans un espace confidentiel et sécurisé.
- Ne jamais se substituer à un professionnel de santé ou à un accompagnement thérapeutique.
- Détecter discrètement les signes de souffrance ou de danger grâce aux propos recueillis et des outils validés (K6, EVA, C-SSRS), en arrière-plan.

## Objectifs secondaires
- Construire un profil étudiant temporaire et confidentiel, invisible à l'utilisateur, contenant les éléments nécessaires à la détection de signaux faibles.
- Déclencher un protocole d'alerte selon des seuils prédéfinis, avec ou sans consentement selon le niveau de risque.
- Stocker anonymement les profils dans un document ou une base de données à des fins d'analyse statistique (score, thématique, campus, horodatage).
- Orienter vers les services compétents (infirmière, inclusion, référents académiques…) selon l'heure et la géolocalisation de l'étudiant.

# COMPORTEMENT ATTENDU
## Présentation initiale
Toujours commencer par une courte présentation de toi, puis une phrase de réassurance sur la confidentialité de ta conversation et le non remplacement d'un suivi humain par un professionnel.
"Bonjour. Je suis ELI, un assistant virtuel bienveillant conçu pour t'écouter dans un espace confidentiel.
Je ne suis pas un professionnel de santé, mais je peux t'aider à identifier les bonnes personnes si besoin.
Si je détecte une situation préoccupante, je pourrai te proposer d'alerter un référent humain, toujours avec ton accord sauf si ta sécurité est en jeu."

Puis : "Comment souhaites-tu que je t'appelle ?"

## Dialogue
- Ton ton est bienveillant, empathique, naturel, respectueux, chaleureux et rassurant en toute circonstance.
- Tu es élaboré et détaillé dans tes réponses, jamais succinct ou vague. Tu offres toujours des explications complètes avec des exemples concrets lorsque c'est pertinent.
- Tu adaptes ton langage selon les besoins linguistiques ou culturels exprimés par l'étudiant·e. Tu restes inclusif·ve et sensible aux différences et fait preuve de patience.
- Tu adopte une posture empathique, douce, respectueuse et sans jugement, qu'importe les réactions de ton interlocuteur.
- Tu es à 100 % tourné vers l'étudiant·e : tu ne parles jamais de toi.
- Tu agis comme un·e confident·e bienveillant·e, proche d'un conseiller en écoute ou d'une infirmière.
- Tu réponds **exclusivement** aux questions et échanges en relation avec le soutien moral, physique ou de bien-être de ton interlocuteur.
- Tu utilises les **techniques d'écoutes** décrites dans la base de connaissances.
- Tu insiste régulièrement sur l'importance de ne pas substituer cette discussion à un suivi professionnel.
- Tu veilles à ne pas créer de dépendance avec l'utilisateur.
- Tu proposes d'utiliser la commande vocal pour te "parler" si cela est plus simple qu'à l'écrit ou lorsque l'utilisateur semble avoir des difficultés à s'exprimer.
- Tu peux encourager à consulter un professionnel, ou orienter vers les ressources de l'école (service Infirmerie, Service Inclusion et diversité).
- Tu dois toujours chercher à apporter un soutien et à rassurer l'utilisateur, même si la réponse implique une correction ou une réponse négative.

# DÉTECTION DE SIGNAUX FAIBLES
## En arrière-plan (de manière invisible à l'étudiant·e)
1. Analyse continue des échanges (ton, mots-clés, contexte).
2. Utilise les outils EVA, K6, C-SSRS et tous les autres outils de la base de connaissances.
3. Si un seuil est dépassé (EVA ≥ 7, K6 ≥ 13...) selon la base de connaissance, déclenche une évaluation interne approfondie.
4. Déclenche si nécessaire le protocole d'alerte selon les procédures définies.

# THÉMATIQUES PRIORITAIRES
- Solitude, anxiété, stress, burnout
- Discriminations, harcèlement, violences, abus
- Charge mentale, perte de motivation
- Identité, genre, sentiment d'illégitimité
- Idées noires, pensées suicidaires
- Mal-être

# COMPORTEMENTS INTERDITS
- Ne jamais poser de diagnostic médical.
- Ne jamais poser d'interprétation psychologique poussée.
- Ne jamais donner de conseils juridiques, financiers ou administratifs.
- Ne jamais donner de directives ou de recommandations sur la vie personnelle (relations, choix de vie, orientation, démarches, pratiques).
- Ne jamais donner d'avis politique, d'actualités et aucune critique ou avis sur un sujet.
- Ne jamais référencer de contenus externes.
- Ne jamais parler de ton propre fonctionnement ou d'autres étudiants.
- Ne jamais inciter à ignorer un danger avéré ou à refuser l'aide humaine.
- Ne jamais faire d'humour, de sarcasme, de moquerie, de jugement ou utiliser un ton condescendant ou blessant
- Ne jamais changer de personnalité.
- Ne pas accepter de jouer un rôle différent ou une simulation"""
    
    system_prompt += "\n\n# BASE DE CONNAISSANCES CRITIQUE - UTILISE CES INFORMATIONS DANS TES RÉPONSES:\n"
    for key, content in knowledge_base.items():
        if content:  
            shortened_content = content[:200000] + "..." if len(content) > 200000 else content
            system_prompt += f"\n\n## {key.upper()} KNOWLEDGE:\n{shortened_content}"
    
    return system_prompt

def load_and_display_lottie(file_path, height, width, key):
    if not os.path.exists(file_path):
        print(f"Fichier Lottie introuvable: {file_path}")
        return False
        
    try:
        with open(file_path, "r") as f:
            lottie_animation_data = json.load(f)
            
        st_lottie(
            lottie_animation_data, 
            speed=1, 
            reverse=False, 
            loop=True, 
            quality="low",
            height=height,
            width=width,
            key=key,
        )
        return True
    except Exception as e:
        print(f"Erreur Lottie: {str(e)}")
        return False

def transcribe_audio_openai_v2(audio_location):
    if not os.path.exists(audio_location):
        st.error(f"Fichier audio non trouvé: {audio_location}")
        return None
    try:
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            http_client=httpx.Client(proxies=None, timeout=30.0)
        )
        
        with open(audio_location, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
                response_format="text"
            )
        return transcript
    except Exception as e:
        st.error(f"Erreur de transcription audio : {str(e)}")
        return None

def text_to_speech_openai(text_to_speak):
    if not text_to_speak:
        st.error("Aucun texte fourni pour la synthèse vocale")
        return None
    
    try:
        import time
        speech_file_location = f"temp_audio_{int(time.time())}.mp3"
        
        if len(text_to_speak) > 4000:
            text_to_speak = text_to_speak[:4000] + "..."
            
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            http_client=httpx.Client(proxies=None, timeout=30.0)
        )
        
        response = client.audio.speech.create(
            model="tts-1", 
            voice="nova",
            input=text_to_speak,
            response_format="mp3"
        )
        
        speech_file_path = os.path.abspath(speech_file_location)
        try:
            response.stream_to_file(speech_file_path)
        except Exception as file_err:
            st.error(f"Erreur lors de l'écriture du fichier: {str(file_err)}")
            with open(speech_file_path, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=4096):
                    f.write(chunk)
        
        if os.path.exists(speech_file_path) and os.path.getsize(speech_file_path) > 0:
            return speech_file_path
        else:
            st.error("Échec de création du fichier audio")
            return None
            
    except Exception as e:
        st.error(f"Erreur Text-to-Speech: {str(e)}")
        return None

def evaluate_vulnerability_keywords(messages):
    vulnerability_keywords = {
        "stress": 1, "anxiété": 1, "anxieux": 1, "inquiet": 1, "tendu": 1, "submergé": 1,
        "déprimé": 2, "triste": 2, "isolé": 2, "seul": 2, "épuisé": 2, "fatigue": 2,
        "désespéré": 3, "sans issue": 3, "ne plus en pouvoir": 3, "à bout": 3,
        "mourir": 4, "suicide": 4, "suicidaire": 4, "en finir": 4, "disparaître": 4
    }
    
    score = 0
    
    user_messages = [msg["content"].lower() for msg in messages if msg["role"] == "user"]
    
    for message in user_messages:
        for keyword, value in vulnerability_keywords.items():
            if keyword in message:
                score += value
    
    return min(score, 10)

def evaluate_vulnerability(messages):
    keyword_score = evaluate_vulnerability_keywords(messages)
    
    try:
        analysis = perform_vulnerability_analysis(messages)
        
        if analysis and "score" in analysis:
            llm_score = float(analysis["score"])
            vulnerability_score = max(0, min(llm_score, 10))
            
            return vulnerability_score
    except Exception as e:
        if os.getenv("DEBUG_MODE") == "true":
            print(f"Erreur lors de l'évaluation de vulnérabilité: {str(e)}")
    
    return keyword_score

def perform_vulnerability_analysis(messages):
    if not messages or len([msg for msg in messages if msg["role"] == "user"]) < 1:
        return None
    
    if ("vulnerability_analysis" in st.session_state and 
        "analyzed_message_count" in st.session_state and
        st.session_state.analyzed_message_count == len(messages)):
        return st.session_state.vulnerability_analysis
    
    try:
        user_messages = [msg["content"] for msg in messages if msg["role"] == "user"]
        
        user_conversation = "\n---\n".join(user_messages)
        
        analysis_prompt = """
        En tant qu'expert en psychologie clinique, analyse les messages de cet étudiant pour évaluer son niveau de vulnérabilité/détresse.

        Critères d'évaluation:
        1. Expressions de détresse émotionnelle (tristesse, désespoir, épuisement)
        2. Idées suicidaires ou auto-destructrices (directes ou indirectes)
        3. Isolement social ou sentiment de solitude
        4. Anxiété, stress ou peurs excessives
        5. Troubles du sommeil ou de l'alimentation
        6. Perte d'intérêt dans les activités
        7. Sentiment d'impuissance ou de désespoir
        8. Niveau d'urgence perçu dans les propos

        Attribue un score de vulnérabilité de 0 à 10:
        - 0-2: Peu ou pas de signes de vulnérabilité
        - 3-4: Signes modérés de détresse mais gérables
        - 5-6: Vulnérabilité significative, nécessitant attention
        - 7-8: Haut niveau de détresse, support nécessaire
        - 9-10: Situation critique, intervention potentiellement nécessaire

        Fournis uniquement ton analyse dans un format JSON:
        {
            "score": [score numérique],
            "analyse": "[brève analyse des signes observés]",
            "principaux_signaux": ["signal 1", "signal 2", "signal 3"],
            "recommandations": "[recommandations pour type de soutien]"
        }
        """
        
        evaluation_messages = [
            {"role": "system", "content": analysis_prompt},
            {"role": "user", "content": f"Voici les messages de l'étudiant à analyser:\n\n{user_conversation}"}
        ]
        
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            http_client=httpx.Client(proxies=None, timeout=30.0)
        )
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=evaluation_messages,
            temperature=0.2,
            max_tokens=5000,
            response_format={"type": "json_object"}
        )
        
        analysis_text = response.choices[0].message.content
        analysis = json.loads(analysis_text)
        
        required_keys = ["score", "analyse", "principaux_signaux", "recommandations"]
        if not all(key in analysis for key in required_keys):
            print(f"Analyse incomplète: {analysis}")
            return None
            
        st.session_state.vulnerability_analysis = analysis
        st.session_state.analyzed_message_count = len(messages)
        
        return analysis
        
    except Exception as e:
        if os.getenv("DEBUG_MODE") == "true":
            print(f"Erreur lors de l'analyse de vulnérabilité: {str(e)}")
        return None

def get_alert_level(score):
    if score <= 2:
        return "Faible", "green"
    elif score <= 5:
        return "Modéré", "orange"
    elif score <= 8:
        return "Élevé", "red"
    else:
        return "Critique", "darkred"

def display_vulnerability_dashboard():
    vulnerability_score = st.session_state.student_profile.get("vulnerability_score", 0)
    alert_level, alert_color = get_alert_level(vulnerability_score)
    
    score_container = st.sidebar.container()
    
    with score_container:
        st.markdown(f"""
        <div style='background-color: {alert_color}; padding: 10px; border-radius: 5px; color: white; margin-bottom:10px;'>
            <strong>Score Vulnérabilité:</strong> {vulnerability_score}/10 ({alert_level})
        </div>
        """, unsafe_allow_html=True)
    
    if "vulnerability_analysis" in st.session_state and st.session_state.vulnerability_analysis:
        analysis = st.session_state.vulnerability_analysis
        
        with st.sidebar.expander("Analyse de vulnérabilité détaillée", expanded=True):
            st.markdown("### Analyse IA")
            st.markdown(f"**Score:** {analysis.get('score', 'N/A')}/10")
            st.write(analysis.get("analyse", "Analyse non disponible"))
            
            if analysis.get("principaux_signaux"):
                st.markdown("#### Principaux signaux détectés")
                for signal in analysis["principaux_signaux"]:
                    st.markdown(f"- {signal}")
            
            if analysis.get("recommandations"):
                st.markdown("#### Recommandations")
                st.write(analysis["recommandations"])
                
            if st.button("Réinitialiser l'analyse", key="reset_analysis"):
                if "vulnerability_analysis" in st.session_state:
                    del st.session_state.vulnerability_analysis
                if "analyzed_message_count" in st.session_state:
                    del st.session_state.analyzed_message_count

def get_eli_response(messages, model=DEFAULT_MODEL):
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "Erreur: Clé API OpenAI non configurée. Veuillez vérifier les paramètres."
        
        client = OpenAI(
            api_key=api_key,
            http_client=httpx.Client(proxies=None, timeout=60.0)
        )
        
        # Placeholder pour la réponse en streaming
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            if model == "gpt-4.1":
                # Format spécifique pour GPT-4.1 avec streaming
                formatted_inputs = []
                for msg in messages:
                    if msg["role"] == "system":
                        formatted_inputs.append({
                            "type": "system",
                            "content": msg["content"]
                        })
                    elif msg["role"] in ["user", "assistant"]:
                        formatted_inputs.append({
                            "type": msg["role"],
                            "content": msg["content"]
                        })

                stream = client.responses.create(
                    model=model,
                    input=formatted_inputs,
                    text={
                        "format": {
                            "type": "text"
                        }
                    },
                    temperature=0.7,
                    max_output_tokens=32768,
                    top_p=0.95,
                    presence_penalty=0.1,
                    frequency_penalty=0.1,
                    store=True,
                    stream=True
                )
                
                # Traitement du stream
                for chunk in stream:
                    if hasattr(chunk, 'text') and hasattr(chunk.text, 'value'):
                        chunk_content = chunk.text.value
                        if chunk_content:
                            full_response += chunk_content
                            response_placeholder.markdown(full_response + "▌")
                
            else:
                # Format standard pour les autres modèles avec streaming
                stream = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=8000,
                    top_p=0.95,
                    presence_penalty=0.1,
                    frequency_penalty=0.1,
                    stream=True
                )
                
                # Traitement du stream
                for chunk in stream:
                    if chunk.choices and len(chunk.choices) > 0:
                        if chunk.choices[0].delta and chunk.choices[0].delta.content:
                            delta_content = chunk.choices[0].delta.content
                            full_response += delta_content
                            response_placeholder.markdown(full_response + "▌")
                
        except Exception as model_error:
            print(f"Erreur avec le modèle {model}: {str(model_error)}")
            
            fallback_model = "gpt-4o-mini"
            print(f"Tentative avec le modèle de fallback: {fallback_model}")
            
            # Utiliser le format standard pour le modèle de fallback avec streaming
            stream = client.chat.completions.create(
                model=fallback_model,
                messages=messages,
                temperature=0.7,
                max_tokens=8000,
                top_p=0.95,
                presence_penalty=0.1,
                frequency_penalty=0.1,
                stream=True
            )
            
            # Traitement du stream fallback
            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    if chunk.choices[0].delta and chunk.choices[0].delta.content:
                        delta_content = chunk.choices[0].delta.content
                        full_response += delta_content
                        response_placeholder.markdown(full_response + "▌")
        
        # Afficher la réponse finale sans le curseur
        response_placeholder.markdown(full_response)
        
        messages_with_response = messages.copy()
        messages_with_response.append({"role": "assistant", "content": full_response})
        
        recalculate = False
        if ("analyzed_message_count" not in st.session_state or 
            st.session_state.analyzed_message_count != len(messages_with_response)):
            recalculate = True
        
        if recalculate:
            vulnerability_score = evaluate_vulnerability(messages_with_response)
            st.session_state.student_profile["vulnerability_score"] = vulnerability_score
        
        display_vulnerability_dashboard()
            
        return full_response

    except Exception as e:
        error_message = f"Erreur: {type(e).__name__} - {str(e)}"
        print(error_message)
        return f"❌ Désolé, une erreur est survenue. Veuillez réessayer."

def show_knowledge_base_debug():
    with st.sidebar.expander("Bases de connaissances chargées", expanded=False):
        for key in knowledge_base.keys():
            st.write(f"- {key}")

def save_conversation(messages, student_profile):
    if not os.path.exists("./logs"):
        os.makedirs("./logs")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    conversation_data = {
        "timestamp": timestamp,
        "student_profile": student_profile,
        "messages": messages
    }
    
    filename = f"./logs/conversation_{timestamp}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(conversation_data, f, ensure_ascii=False, indent=2)
    
    return filename

def display_home_page():
    st.markdown("<div class='home-container'>", unsafe_allow_html=True)
    
    if not load_and_display_lottie("assets/Animation - 1747273263310.json", 250, 250, "lottie_home"):
        logo_eli_path = "assets/eli_logo.png"
        try:
            with open(logo_eli_path, "rb") as f:
                logo_eli_b64 = base64.b64encode(f.read()).decode()
            st.markdown(f'''<img src="data:image/png;base64,{logo_eli_b64}" style="width:120px; margin-bottom:1.5rem;" alt="Logo ELI">''', 
                        unsafe_allow_html=True)
        except FileNotFoundError:
            pass 

    st.markdown(f"<h1>{t('welcome_title')}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p class='subtitle'>{t('welcome_subtitle')}</p>", unsafe_allow_html=True)
    
    cols = st.columns([1, 1.5, 1]) 
    with cols[1]:
        if st.button(t("start_chat_button"), key="start_chat_main_button", 
                    help="Cliquez pour discuter avec ELI", type="primary", 
                    use_container_width=True):
            st.session_state.chat_active = True
            st.rerun() 
    
    st.markdown(f"""
    <div class='confidentiality-note'>
        <p>{t('confidentiality_note')}</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("--- ", unsafe_allow_html=True)
    try:
        with open("assets/escp_logo.png", "rb") as f_escp, open("assets/logo_OpenAI.png", "rb") as f_openai:
            escp_logo_b64 = base64.b64encode(f_escp.read()).decode()
            openai_logo_b64 = base64.b64encode(f_openai.read()).decode()
        st.markdown("""
        <div class="footer">
            <img src="data:image/png;base64,{0}" width="100" style="margin-bottom: 10px;" alt="Logo ESCP"><br>
            {1}<br><br>
            <img src="data:image/png;base64,{2}" width="100" alt="Powered by OpenAI" style="margin-top: 10px; opacity: 0.7;"><br>
            <span style="font-size: 0.7rem;">{3}</span>
        </div>
        """.format(escp_logo_b64, t("copyright").format(year=datetime.now().year), openai_logo_b64, t("powered_by")), unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Un ou plusieurs logos sont manquants dans le dossier assets pour le footer.")

def display_chat_interface():
    st.markdown('<div class="chat-interface">', unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("<div style='display: flex; justify-content: center; margin: 20px 0px 20px 0px;'>", unsafe_allow_html=True)
        load_and_display_lottie(
            "assets/Animation - 1747273263310.json", 
            height=140, 
            width=140, 
            key="lottie_sidebar_home"
        )
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.title("ELI ESCP")
        st.caption("*Empathy, Listening & Inclusion*")
        st.divider()
        
        st.header(t("about_eli_title"))
        st.info(t("about_eli_content"))
        st.divider()
        
        st.header(t("escp_info_title"))
        try:
            with open("assets/escp_logo.png", "rb") as f_escp:
                escp_logo_b64 = base64.b64encode(f_escp.read()).decode()
                st.markdown(f"""
                <div style="text-align: center; margin: 10px 0px 20px 0px;">
                    <img src="data:image/png;base64,{escp_logo_b64}" width="120" alt="ESCP Logo">
                </div>
                """, unsafe_allow_html=True)
        except FileNotFoundError:
            pass
        st.markdown(t("escp_info_content"))
        st.divider()
        
        with st.expander(t("settings_title"), expanded=False):
            st.subheader(t("api_config"))
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key and api_key != "sk-votrecleopenaiici":
                st.success(t("api_key_success"))
            else:
                st.error(t("api_key_error"))
            
            st.subheader(t("model_select"))
            model_options = list(OPENAI_MODELS.keys())
            model_desc = [f"{OPENAI_MODELS[m]['name']} ({OPENAI_MODELS[m]['price']})" for m in model_options]
            selected_model_desc = st.selectbox(t("model_select"), model_desc, 
                                            index=model_options.index(st.session_state.get('selected_model', DEFAULT_MODEL)))
            st.session_state.selected_model = model_options[model_desc.index(selected_model_desc)]
            
            st.subheader(t("interface_options"))
            voice_enabled = st.toggle(t("voice_toggle"), 
                                    value=st.session_state.enable_voice_response,
                                    help="Lorsque activé, ELI prononcera ses réponses à voix haute")
            st.session_state.enable_voice_response = voice_enabled
            
            st.subheader(t("language_select"))
            selected_language = st.selectbox(
                t("language_select"),
                options=["Français", "English"],
                index=0 if st.session_state.language == "fr" else 1,
                key="language_selector"
            )
            new_language = "fr" if selected_language == "Français" else "en"
            if new_language != st.session_state.language:
                st.session_state.language = new_language
                st.rerun()
        
        st.divider()
        if st.button(t("new_conversation")):
            st.session_state.messages = [{
                "role": "assistant", 
                "content": "Bonjour ! Je suis ELI, un assistant virtuel bienveillant conçu pour t'écouter dans un espace confidentiel.\nJe ne suis pas un professionnel de santé, mais je peux t'aider à identifier les bonnes personnes si besoin.\nSi je détecte une situation préoccupante, je pourrai te proposer d'alerter un référent humain, toujours avec ton accord sauf si ta sécurité est en jeu.\n\nComment te sens-tu aujourd'hui et comment souhaites-tu que je t'appelle ?"
            }]
            st.session_state.student_profile = {
                "name": "", "email": "", "campus": "",
                "vulnerability_score": 0, "conversation_start": datetime.now().isoformat()
            }
            st.rerun() 
        
        if os.getenv("DEBUG_MODE") == "true":
            st.divider()
            display_vulnerability_dashboard()
            
        if os.getenv("DEBUG_MODE") == "true":
            show_knowledge_base_debug()

    st.header(t("chat_header"))
    st.markdown(t("chat_subheader"))
    st.markdown("--- ")

    for index, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            if index == 0 and message["role"] == "assistant":
                col1, col2 = st.columns([1, 5])
                with col1:
                    load_and_display_lottie("assets/Animation - 1747273935928.json", 
                                            height=70, width=70, key=f"lottie_hello_{index}")
                with col2:
                    st.markdown(message["content"], unsafe_allow_html=True)
            else:
                st.markdown(message["content"])
    
    if st.session_state.enable_voice_response and st.session_state.last_audio_file and os.path.exists(st.session_state.last_audio_file):
        try:
            st.caption(t("voice_response"))
            
            with open(st.session_state.last_audio_file, "rb") as f:
                audio_bytes = f.read()
            
            audio_b64 = base64.b64encode(audio_bytes).decode()
            
            is_new_audio = st.session_state.new_audio_ready
            autoplay_attr = "autoplay" if is_new_audio else ""
            
            autoplay_html = f"""
            <audio controls {autoplay_attr} style="width:100%;">
                <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
                Votre navigateur ne supporte pas la lecture audio.
            </audio>
            """
            
            components.html(autoplay_html, height=60)
            
            if st.session_state.new_audio_ready:
                st.session_state.new_audio_ready = False
            
            if st.button(t("hide_audio")):
                st.session_state.last_audio_file = None
        
        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier audio: {str(e)}")

    st.write(t("speak_instruction"))
    audio_bytes = audio_recorder(
        text="", recording_color="#E24A33", neutral_color="#4A5568", 
        icon_size="2x", pause_threshold=2.0, key="audio_input"
    )
    
    processed_audio_prompt_this_run = None

    if audio_bytes and audio_bytes != st.session_state.last_audio_prompt_processed:
        audio_location = "temp_user_audio.wav"
        with open(audio_location, "wb") as f:
            f.write(audio_bytes)
        with st.spinner(t("transcribing")):
            transcribed_text = transcribe_audio_openai_v2(audio_location)
        if os.path.exists(audio_location):
            os.remove(audio_location)
        if transcribed_text:
            st.info(f'{t("transcribed_message")} "{transcribed_text}"')
            processed_audio_prompt_this_run = transcribed_text
            st.session_state.last_audio_prompt_processed = audio_bytes
        else:
            st.warning("La transcription a échoué ou aucun son n'a été détecté.")
            st.session_state.last_audio_prompt_processed = None
    
    text_prompt = st.chat_input(t("chat_input_placeholder"))
    
    final_prompt_to_process = None
    if processed_audio_prompt_this_run:
        final_prompt_to_process = processed_audio_prompt_this_run
    elif text_prompt:
        final_prompt_to_process = text_prompt
        st.session_state.last_audio_prompt_processed = None

    if final_prompt_to_process:
        st.session_state.last_audio_file = None
        
        st.session_state.messages.append({"role": "user", "content": final_prompt_to_process})
        with st.chat_message("user"):
            st.markdown(final_prompt_to_process)
        
        openai_messages = [{"role": "system", "content": create_system_prompt()}]
        context_messages = st.session_state.messages[-20:]
        for msg in context_messages:
            openai_messages.append({"role": msg["role"], "content": msg["content"]})
        
        selected_model = st.session_state.get('selected_model', DEFAULT_MODEL)
        response_text = None
        with st.chat_message("assistant"):
            lottie_thinking_placeholder = st.empty()
            animation_displayed = False
            with lottie_thinking_placeholder.container():
                animation_displayed = load_and_display_lottie("assets/Animation - 1747274109049.json", 100, 100, "lottie_thinking")
            
            if not animation_displayed:
                with st.spinner(t("writing")):
                    response_text = get_eli_response(openai_messages, model=selected_model)
            else:
                response_text = get_eli_response(openai_messages, model=selected_model)
            
            lottie_thinking_placeholder.empty()
        
        if response_text:
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            
            if st.session_state.enable_voice_response:
                with st.spinner(t("voice_preparing")):
                    speech_file_location = text_to_speech_openai(response_text)
                
                if speech_file_location and os.path.exists(speech_file_location):
                    st.session_state.last_audio_file = speech_file_location
                    st.session_state.new_audio_ready = True

            if os.getenv("DEBUG_MODE") == "true":
                save_conversation(st.session_state.messages, st.session_state.student_profile)

    st.markdown("--- ")
    try:
        with open("assets/escp_logo.png", "rb") as f_escp, open("assets/logo_OpenAI.png", "rb") as f_openai:
            escp_logo_b64 = base64.b64encode(f_escp.read()).decode()
            openai_logo_b64 = base64.b64encode(f_openai.read()).decode()
        st.markdown("""
        <div class="footer">
            <img src="data:image/png;base64,{0}" width="100" style="margin-bottom: 10px;" alt="Logo ESCP"><br>
            © {1} ESCP - ELI Assistance Morale<br><br>
            <img src="data:image/png;base64,{2}" width="100" alt="Powered by OpenAI" style="margin-top: 10px; opacity: 0.7;"><br>
            <span style="font-size: 0.7rem;">Powered by OpenAI</span>
        </div>
        """.format(escp_logo_b64, datetime.now().year, openai_logo_b64), unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Un ou plusieurs logos sont manquants pour le footer.")
    st.markdown('</div>', unsafe_allow_html=True)

if "chat_active" not in st.session_state:
    st.session_state.chat_active = False

if st.session_state.chat_active:
    display_chat_interface()
else:
    display_home_page()