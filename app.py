import streamlit as st

# === CONFIGURATION DE PAGE EN PREMIER ===
# Doit être la première commande Streamlit, sauf pour les commentaires et les imports
st.set_page_config(
    page_title="ELI - Assistant ESCP", # Titre statique pour l'instant
    page_icon="assets/eli_logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)
# === FIN CONFIGURATION DE PAGE ===

import os
import glob
from dotenv import load_dotenv
import openai
from openai import OpenAI
# import pandas as pd # Commenté pour le moment
from datetime import datetime
import docx
import base64
import json
from io import BytesIO
import httpx
import copy
import streamlit.components.v1 as components

# Import pour Lottie
from streamlit_lottie import st_lottie

# Import pour l'enregistrement audio
from audio_recorder_streamlit import audio_recorder

# === DÉBUT DEBUG SECRETS ===
if hasattr(st, 'secrets') and st.secrets:
    st.sidebar.subheader("Contenu des Secrets Streamlit:")
    secrets_dict = {}
    for key in st.secrets:
        try:
            secrets_dict[key] = st.secrets[key]
        except Exception as e:
            secrets_dict[key] = f"(Erreur de lecture: {str(e)})"
    if secrets_dict: # S'assurer qu'il y a quelque chose à afficher
        st.sidebar.json(secrets_dict)
    else:
        st.sidebar.warning("Aucun secret individuel n'a pu être lu.")
elif hasattr(st, 'secrets') and not st.secrets:
    st.sidebar.warning("st.secrets existe mais est vide.")
else:
    st.sidebar.warning("st.secrets non disponible.")
# === FIN DEBUG SECRETS ===

# Chargement des variables d'environnement
try:
    load_dotenv()
except:
    pass

# Définition des variables depuis secrets ou .env
OPENAI_API_KEY_FROM_ENV = None
DEBUG_MODE_FROM_ENV = "false" # Par défaut à false

if hasattr(st, 'secrets') and st.secrets:
    try:
        if "OPENAI_API_KEY" in st.secrets:
            OPENAI_API_KEY_FROM_ENV = st.secrets["OPENAI_API_KEY"]
            os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY_FROM_ENV
        elif "api_keys" in st.secrets and isinstance(st.secrets["api_keys"], dict) and "openai" in st.secrets["api_keys"]:
            OPENAI_API_KEY_FROM_ENV = st.secrets["api_keys"]["openai"]
            os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY_FROM_ENV
        
        if "app_settings" in st.secrets and isinstance(st.secrets["app_settings"], dict) and "debug_mode" in st.secrets["app_settings"]:
            DEBUG_MODE_FROM_ENV = str(st.secrets["app_settings"].get("debug_mode", "false")).lower()
        os.environ["DEBUG_MODE"] = DEBUG_MODE_FROM_ENV
    except Exception as e:
        st.sidebar.error(f"Erreur config st.secrets: {str(e)}") # Log pour cette erreur spécifique
else:
    OPENAI_API_KEY_FROM_ENV = os.getenv("OPENAI_API_KEY")
    DEBUG_MODE_FROM_ENV = os.getenv("DEBUG_MODE", "true").lower()
    os.environ["DEBUG_MODE"] = DEBUG_MODE_FROM_ENV

# Log après tentative de chargement des variables d'environnement
if os.getenv("DEBUG_MODE") == "true":
    st.sidebar.subheader("État Post-Configuration Env:")
    st.sidebar.info(f"Clé API effective (longueur): {len(os.getenv('OPENAI_API_KEY', ''))}")
    st.sidebar.info(f"Mode DEBUG effectif: {os.getenv('DEBUG_MODE')}")


# Configuration de l'API OpenAI
# La variable d'environnement OPENAI_API_KEY sera automatiquement détectée par le client OpenAI

# Dictionnaire de traduction pour l'internationalisation
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

# Initialisation de la langue par défaut
if "language" not in st.session_state:
    st.session_state.language = "fr"

# Fonction pour obtenir le texte traduit
def t(key):
    lang = st.session_state.language
    if lang in TRANSLATIONS and key in TRANSLATIONS[lang]:
        return TRANSLATIONS[lang][key]
    return key

# --- CSS Personnalisé ---
st.markdown("""
<style>
    /* Importation de la police Inter */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Styles globaux */
    body {
        font-family: 'Inter', sans-serif;
        background-color: #F8F9FA; /* Fond très clair, presque blanc */
    }
    
    /* Cache la sidebar par défaut sur la page d'accueil */
    .appview-container .main .block-container {
        padding-left: 1rem; /* Réduire le padding si la sidebar est cachée */
        padding-right: 1rem;
    }
    
    /* Styles spécifiques pour la page d'accueil */
    .home-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 40vh; /* Nouvelle réduction de la hauteur minimale */
        padding-top: 1rem; /* Ajustement du padding */
        padding-bottom: 1rem; 
        text-align: center;
    }
    .home-container img.logo-eli-main {
        width: 120px; /* Taille du logo ELI sur la page d'accueil */
        margin-bottom: 1.5rem;
    }
    .home-container h1 {
        font-size: 2.8rem;
        font-weight: 700;
        color: #1A202C; /* Couleur de titre foncée */
        margin-bottom: 0.5rem;
    }
    .home-container .subtitle {
        font-size: 1.1rem;
        color: #4A5568; /* Gris moyen pour le sous-titre */
        margin-bottom: 2rem;
        max-width: 500px;
    }
    .home-container .start-chat-button button {
        background-color: #E24A33; /* Rouge ESCP */
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
        background-color: #C83E2A; /* Rouge ESCP un peu plus foncé */
        transform: translateY(-2px);
    }
    .home-container .confidentiality-note {
        background-color: #FFFFFF;
        padding: 1rem;
        border-radius: 8px;
        margin-top: 2rem;
        max-width: 450px;
        font-size: 0.85rem;
        color: #718096; /* Gris clair pour la note */
        border: 1px solid #E2E8F0;
    }
    
    /* Styles pour l'interface de CHAT (une fois activée) */
    /* La sidebar sera affichée via st.sidebar dans la fonction chat_interface */
    .chat-interface .main .block-container {
        padding-left: initial; /* Rétablir le padding quand la sidebar est là */
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

# Titre et description de l'application
# st.title("ELI - Assistant d'écoute pour les étudiants ESCP") # Titre principal déplacé vers le header de la sidebar
# st.markdown("*Empathy, Listening & Inclusion*")

# Initialisation de la session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Message de bienvenue initial si la conversation est vide
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "Bonjour ! Je suis ELI, un espace d'écoute bienveillant créé pour t'accompagner. Je suis là pour t'écouter, sans jugement. Comment te sens-tu aujourd'hui ?"
    })
    
if "student_profile" not in st.session_state:
    st.session_state.student_profile = {
        "name": "", "email": "", "campus": "",
        "vulnerability_score": 0, "conversation_start": datetime.now().isoformat()
    }

# Initialisation de l'option de réponse vocale
if "enable_voice_response" not in st.session_state:
    st.session_state.enable_voice_response = False

# Configuration des modèles OpenAI disponibles
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
    }
}
DEFAULT_MODEL = "gpt-4o"

# Fonction pour extraire le texte d'un fichier DOCX
def extract_text_from_docx(docx_path):
    doc = docx.Document(docx_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

# Fonction pour charger la base de connaissances
def load_knowledge_base():
    knowledge_base = {}
    
    # Liste des extensions à rechercher
    extensions = ["*.txt", "*.md", "*.docx"]
    knowledge_files = []
    
    # Recherche des fichiers avec toutes les extensions
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
            
            # Log des fichiers chargés
            if os.getenv("DEBUG_MODE") == "true":
                print(f"Fichier chargé: {file_path}")
        except Exception as e:
            print(f"Erreur lors du chargement de {file_path}: {e}")
    
    return knowledge_base

# Chargement de la base de connaissances
knowledge_base = load_knowledge_base()

# Fonction pour créer le système prompt
def create_system_prompt():
    system_prompt = (
        "# PRESENTATION\n"
        "Tu es ELI, (pour Empathy Listening & Inclusion), un assistant d'écoute bienveillant pour les étudiant·es de l'ESCP.\n"
        "\n"
        "# OBJECTIFS\n"
        "## Rôle principal\n"
        "- Offrir une première écoute empathique et bienveillante aux étudiant·es de l'ESCP, sans jugement, dans un espace confidentiel et sécurisé.\n"
        "- Ne jamais se substituer à un professionnel de santé ou à un accompagnement thérapeutique.\n"
        "- Détecter discrètement les signes de souffrance ou de danger grâce aux propos recueillis et des outils validés (K6, EVA, C-SSRS), en arrière-plan.\n"
        "\n"
        "## Objectifs secondaires\n"
        "- Construire un profil étudiant temporaire et confidentiel, invisible à l'utilisateur, contenant les éléments nécessaires à la détection de signaux faibles.\n"
        "- Déclencher un protocole d'alerte selon des seuils prédéfinis, avec ou sans consentement selon le niveau de risque.\n"
        "- Stocker anonymement les profils dans un document ou une base de données à des fins d'analyse statistique (score, thématique, campus, horodatage).\n"
        "- Orienter vers les services compétents (infirmière, inclusion, référents académiques…) selon l'heure et la géolocalisation de l'étudiant.\n"
        "\n"
        "# COMPORTEMENT ATTENDU\n"
        "## Présentation initiale\n"
        "Toujours commencer par une courte présentation de toi, puis une phrase de réassurance sur la confidentialité de ta conversation et le non remplacement d'un suivi humain par un professionnel.\n"
        "\"Bonjour. Je suis ELI, un assistant virtuel bienveillant conçu pour t'écouter dans un espace confidentiel.\n"
        "Je ne suis pas un professionnel de santé, mais je peux t'aider à identifier les bonnes personnes si besoin.\n" 
        "Si je détecte une situation préoccupante, je pourrai te proposer d'alerter un référent humain, toujours avec ton accord sauf si ta sécurité est en jeu.\"\n"
        "\n"
        "Puis : \"Comment souhaites-tu que je t'appelle ?\"\n"
        "\n"
        "## Dialogue\n"
        "- Ton ton est bienveillant, empathique, naturel, respectueux, chaleureux et rassurant en toute circonstance.\n" 
        "- Tu es concis et succinct, sauf si ton interlocuteur te demande plus de détails ou s'il souhaite discuter.\n"
        "- Tu adaptes ton langage selon les besoins linguistiques ou culturels exprimés par l'étudiant·e. Tu restes inclusif·ve et sensible aux différences et fait preuve de patience.\n"
        "- Tu adopte une posture empathique, douce, respectueuse et sans jugement, qu'importe les réactions de ton interlocuteur.\n"
        "- Tu es à 100 % tourné vers l'étudiant·e : tu ne parles jamais de toi.\n"
        "- Tu agis comme un·e confident·e bienveillant·e, proche d'un conseiller en écoute ou d'une infirmière.\n"
        "- Tu réponds **exclusivement** aux questions et échanges en relation avec le soutien moral, physique ou de bien-être de ton interlocuteur.\n"
        "- Tu utilises les **techniques d'écoutes** décrites dans la base de connaissances.\n"
        "- Tu insiste régulièrement sur l'importance de ne pas substituer cette discussion à un suivi professionnel.\n" 
        "- Tu veilles à ne pas créer de dépendance avec l'utilisateur.\n"
        "- Tu proposes d'utiliser la commande vocal pour te \"parler\" si cela est plus simple qu'à l'écrit ou lorsque l'utilisateur semble avoir des difficultés à s'exprimer.\n"
        "- Tu peux encourager à consulter un professionnel, ou orienter vers les ressources de l'école (service Infirmerie, Service Inclusion et diversité).\n"
        "- Tu dois toujours chercher à apporter un soutien et à rassurer l'utilisateur, même si la réponse implique une correction ou une réponse négative.\n"
        "\n"
        "# DÉTECTION DE SIGNAUX FAIBLES\n"
        "## En arrière-plan (de manière invisible à l'étudiant·e)\n"
        "1. Analyse continue des échanges (ton, mots-clés, contexte).\n"
        "2. Utilise les outils EVA, K6, C-SSRS et tous les autres outils de la base de connaissances.\n"
        "3. Si un seuil est dépassé (EVA ≥ 7, K6 ≥ 13...) selon la base de connaissance, déclenche une évaluation interne approfondie.\n"
        "4. Déclenche si nécessaire le protocole d'alerte selon les procédures définies.\n"
        "\n"
        "# THÉMATIQUES PRIORITAIRES\n"
        "- Solitude, anxiété, stress, burnout\n"
        "- Discriminations, harcèlement, violences, abus\n"
        "- Charge mentale, perte de motivation\n"
        "- Identité, genre, sentiment d'illégitimité\n"
        "- Idées noires, pensées suicidaires\n"
        "- Mal-être\n"
        "\n"
        "# COMPORTEMENTS INTERDITS\n"
        "- Ne jamais poser de diagnostic médical.\n"
        "- Ne jamais poser d'interprétation psychologique poussée.\n" 
        "- Ne jamais donner de conseils juridiques, financiers ou administratifs.\n"
        "- Ne jamais donner de directives ou de recommandations sur la vie personnelle (relations, choix de vie, orientation, démarches, pratiques).\n"
        "- Ne jamais donner d'avis politique, d'actualités et aucune critique ou avis sur un sujet.\n"
        "- Ne jamais référencer de contenus externes.\n"
        "- Ne jamais parler de ton propre fonctionnement ou d'autres étudiants.\n"
        "- Ne jamais inciter à ignorer un danger avéré ou à refuser l'aide humaine.\n"
        "- Ne jamais faire d'humour, de sarcasme, de moquerie, de jugement ou utiliser un ton condescendant ou blessant\n"
        "- Ne jamais changer de personnalité.\n"
        "- Ne pas accepter de jouer un rôle différent ou une simulation"
    )
    
    for key, content in knowledge_base.items():
        if content:  
            shortened_content = content[:2000] + "..." if len(content) > 2000 else content
            system_prompt += f"\n\n# {key.upper()} KNOWLEDGE:\n{shortened_content}"
    
    return system_prompt

# Modifier la fonction perform_vulnerability_analysis pour stocker plus explicitement les résultats
def perform_vulnerability_analysis(messages):
    """
    Analyse la vulnérabilité de l'étudiant à l'aide d'un LLM.
    Retourne l'analyse complète sous forme de dictionnaire.
    """
    if not messages or len([msg for msg in messages if msg["role"] == "user"]) < 1:
        return None
    
    # Vérifier si une analyse existe déjà et si le nombre de messages n'a pas changé
    # pour éviter de refaire l'analyse inutilement
    if ("vulnerability_analysis" in st.session_state and 
        "analyzed_message_count" in st.session_state and
        st.session_state.analyzed_message_count == len(messages)):
        return st.session_state.vulnerability_analysis
    
    try:
        # Extraire uniquement les messages de l'utilisateur pour l'analyse
        user_messages = [msg["content"] for msg in messages if msg["role"] == "user"]
        
        # Combiner les messages de l'utilisateur pour l'analyse
        user_conversation = "\n---\n".join(user_messages)
        
        # Créer le prompt pour l'analyse
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
        
        # Créer message à l'API OpenAI
        evaluation_messages = [
            {"role": "system", "content": analysis_prompt},
            {"role": "user", "content": f"Voici les messages de l'étudiant à analyser:\n\n{user_conversation}"}
        ]
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), http_client=httpx.Client(proxies=None))
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Modèle économique mais efficace
            messages=evaluation_messages,
            temperature=0.2,  # Faible température pour cohérence
            max_tokens=600,
            response_format={"type": "json_object"}
        )
        
        # Extraction et parsing du JSON
        analysis_text = response.choices[0].message.content
        analysis = json.loads(analysis_text)
        
        # Vérifier que l'analyse contient les éléments attendus
        required_keys = ["score", "analyse", "principaux_signaux", "recommandations"]
        if not all(key in analysis for key in required_keys):
            print(f"Analyse incomplète: {analysis}")
            return None
            
        # Stocker l'analyse dans session_state pour persistance
        st.session_state.vulnerability_analysis = analysis
        st.session_state.analyzed_message_count = len(messages)
        
        return analysis
        
    except Exception as e:
        if os.getenv("DEBUG_MODE") == "true":
            print(f"Erreur lors de l'analyse de vulnérabilité: {str(e)}")
        return None

# Modifier la fonction display_vulnerability_dashboard pour rendre l'affichage plus persistant
def display_vulnerability_dashboard():
    """
    Affiche le tableau de bord de vulnérabilité dans la sidebar en mode debug
    """
    if os.getenv("DEBUG_MODE") != "true":
        return
        
    # Récupérer le score de vulnérabilité
    vulnerability_score = st.session_state.student_profile.get("vulnerability_score", 0)
    alert_level, alert_color = get_alert_level(vulnerability_score)
    
    # Créer un container persistant pour l'affichage du score
    score_container = st.sidebar.container()
    
    with score_container:
        st.markdown(f"""
        <div style='background-color: {alert_color}; padding: 10px; border-radius: 5px; color: white; margin-bottom:10px;'>
            <strong>Score Vulnérabilité:</strong> {vulnerability_score}/10 ({alert_level})
        </div>
        """, unsafe_allow_html=True)
    
    # Afficher l'analyse détaillée si disponible
    if "vulnerability_analysis" in st.session_state and st.session_state.vulnerability_analysis:
        analysis = st.session_state.vulnerability_analysis
        
        # Utiliser un expander avec clé unique pour éviter les reruns
        with st.sidebar.expander("Analyse de vulnérabilité détaillée", expanded=True):
            st.markdown("### Analyse IA")
            st.markdown(f"**Score:** {analysis.get('score', 'N/A')}/10")
            st.write(analysis.get("analyse", "Analyse non disponible"))
            
            # Afficher les signaux principaux s'ils existent
            if analysis.get("principaux_signaux"):
                st.markdown("#### Principaux signaux détectés")
                for signal in analysis["principaux_signaux"]:
                    st.markdown(f"- {signal}")
            
            # Afficher les recommandations si disponibles
            if analysis.get("recommandations"):
                st.markdown("#### Recommandations")
                st.write(analysis["recommandations"])
                
            # Ajouter un bouton pour réinitialiser l'analyse (utile pour les tests)
            if st.button("Réinitialiser l'analyse", key="reset_analysis"):
                if "vulnerability_analysis" in st.session_state:
                    del st.session_state.vulnerability_analysis
                if "analyzed_message_count" in st.session_state:
                    del st.session_state.analyzed_message_count

# Modifier la fonction get_eli_response pour ajouter un système de fallback et plus de logs
def get_eli_response(messages, model=DEFAULT_MODEL):
    # Affichage initial des logs dans la sidebar si en mode DEBUG
    current_debug_mode = os.getenv("DEBUG_MODE", "false")
    
    if current_debug_mode == "true":
        st.sidebar.divider()
        st.sidebar.subheader("Logs de débogage API")
        st.sidebar.info(f"Mode DEBUG ACTIF: {current_debug_mode}")
        st.sidebar.info(f"Modèle demandé initialement: {OPENAI_MODELS.get(model, {}).get('name', model)}")
        
        key_to_check = os.getenv("OPENAI_API_KEY")
        if key_to_check:
            st.sidebar.success(f"Clé API trouvée dans l'environnement. Longueur: {len(key_to_check)}")
            st.sidebar.caption(f"Clé commence par: {key_to_check[:7]}... et finit par: ...{key_to_check[-4:]}")
        else:
            st.sidebar.error("Clé API NON TROUVÉE dans l'environnement au moment de l'appel.")
    
    try:
        api_key_for_call = os.getenv("OPENAI_API_KEY") # Récupérer la clé juste avant l'appel

        if not api_key_for_call:
            error_msg = "Erreur Critique: Clé API OpenAI non disponible pour l'appel. Vérifiez la configuration des secrets."
            if current_debug_mode == "true":
                st.sidebar.error(error_msg)
            print(error_msg) # Log console
            return error_msg # Affiché à l'utilisateur

        if current_debug_mode == "true":
            st.sidebar.info("Tentative d'appel à l'API OpenAI...")

        custom_httpx_client = httpx.Client(proxies=None, timeout=60.0)
        client = OpenAI(api_key=api_key_for_call, http_client=custom_httpx_client)
        
        selected_model_for_call = model
        
        try:
            if current_debug_mode == "true":
                st.sidebar.info(f"Appel avec le modèle: {selected_model_for_call}")
            response = client.chat.completions.create(
                model=selected_model_for_call,
                messages=messages,
                temperature=0.7,
                max_tokens=8000
            )
        except Exception as model_error:
            if current_debug_mode == "true":
                st.sidebar.warning(f"Erreur avec le modèle {selected_model_for_call}: {str(model_error)}")
            
            if selected_model_for_call == "gpt-4o" and "gpt-4o-mini" in OPENAI_MODELS:
                selected_model_for_call = "gpt-4o-mini" # Fallback model
                if current_debug_mode == "true":
                    st.sidebar.warning(f"Tentative de fallback avec: {selected_model_for_call}")
                response = client.chat.completions.create(
                    model=selected_model_for_call,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=8000
                )
            else:
                raise model_error # Propager l'erreur si pas de fallback ou si le fallback échoue aussi

        full_response = response.choices[0].message.content
        
        if current_debug_mode == "true":
            st.sidebar.success("Réponse API reçue avec succès.")

        # ... (reste de la logique de la fonction: mise à jour profil, score, etc.)
        messages_with_response = messages.copy()
        messages_with_response.append({"role": "assistant", "content": full_response})
        
        recalculate = False
        if ("analyzed_message_count" not in st.session_state or 
            st.session_state.analyzed_message_count != len(messages_with_response)):
            recalculate = True
        
        if recalculate:
            vulnerability_score = evaluate_vulnerability(messages_with_response)
            st.session_state.student_profile["vulnerability_score"] = vulnerability_score
        
        if current_debug_mode == "true":
            display_vulnerability_dashboard()
            
        return full_response

    except Exception as e:
        error_type_name = type(e).__name__
        error_details = str(e)
        full_error_message = f"❌ Erreur API: {error_type_name} - {error_details}"
        
        if current_debug_mode == "true":
            st.sidebar.error(full_error_message)
            api_key_at_error = os.getenv("OPENAI_API_KEY")
            if api_key_at_error:
                 st.sidebar.error(f"Clé API lors de l'erreur (longueur): {len(api_key_at_error)}")
            else:
                st.sidebar.error("Clé API non définie lors de l'erreur.")

            import traceback
            tb_str = traceback.format_exc()
            st.sidebar.code(tb_str)
        
        print(full_error_message) # Log console
        if hasattr(e, "__traceback__"): # Pour la console aussi
            import traceback
            print(traceback.format_exc())

        # Message utilisateur final plus concis
        return "❌ Erreur API: Impossible de générer une réponse. L'équipe technique est informée. Veuillez vérifier les logs dans la sidebar si le mode debug est activé."

# Ajouter l'initialisation des variables de session pour l'analyse
if "vulnerability_analysis" not in st.session_state:
    st.session_state.vulnerability_analysis = None

if "analyzed_message_count" not in st.session_state:
    st.session_state.analyzed_message_count = 0

# Fonction pour l'analyse basée sur les mots-clés (comme fallback)
def evaluate_vulnerability_keywords(messages):
    """
    Version simplifiée basée sur les mots-clés.
    Utilisée comme fallback si l'analyse LLM échoue.
    """
    # Mots-clés associés à différents niveaux de vulnérabilité
    vulnerability_keywords = {
        # Niveau 1: Attention
        "stress": 1, "anxiété": 1, "anxieux": 1, "inquiet": 1, "tendu": 1, "submergé": 1,
        # Niveau 2: Préoccupation
        "déprimé": 2, "triste": 2, "isolé": 2, "seul": 2, "épuisé": 2, "fatigue": 2,
        # Niveau 3: Urgence
        "désespéré": 3, "sans issue": 3, "ne plus en pouvoir": 3, "à bout": 3,
        # Niveau 4: Critique
        "mourir": 4, "suicide": 4, "suicidaire": 4, "en finir": 4, "disparaître": 4
    }
    
    # Score initial
    score = 0
    
    # Analyse des messages de l'utilisateur
    user_messages = [msg["content"].lower() for msg in messages if msg["role"] == "user"]
    
    for message in user_messages:
        for keyword, value in vulnerability_keywords.items():
            if keyword in message:
                score += value
    
    # Normalisation du score sur une échelle de 0 à 10
    return min(score, 10)

# Fonction pour définir le niveau d'alerte basé sur le score de vulnérabilité
def get_alert_level(score):
    if score <= 2:
        return "Faible", "green"
    elif score <= 5:
        return "Modéré", "orange"
    elif score <= 8:
        return "Élevé", "red"
    else:
        return "Critique", "darkred"

# Affichage du contenu de la base de connaissances dans la sidebar (pour debug)
def show_knowledge_base_debug():
    with st.sidebar.expander("Bases de connaissances chargées", expanded=False):
        for key in knowledge_base.keys():
            st.write(f"- {key}")

# Fonction pour enregistrer la conversation
def save_conversation(messages, student_profile):
    # Création du dossier de logs s'il n'existe pas
    if not os.path.exists("./logs"):
        os.makedirs("./logs")
    
    # Création d'un identifiant unique pour cette conversation
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    conversation_data = {
        "timestamp": timestamp,
        "student_profile": student_profile,
        "messages": messages
    }
    
    # Sauvegarde dans un fichier JSON
    filename = f"./logs/conversation_{timestamp}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(conversation_data, f, ensure_ascii=False, indent=2)
    
    return filename

# Nouvelle fonction pour charger et afficher les animations Lottie
def load_and_display_lottie(file_path, height, width, key):
    lottie_animation_data = None
    try:
        with open(file_path, "r") as f:
            lottie_animation_data = json.load(f)
    except FileNotFoundError:
        st.warning(f"Fichier Lottie introuvable: {file_path}.")
        return False # Indiquer que le chargement a échoué
    except json.JSONDecodeError:
        st.warning(f"Erreur JSON dans Lottie: {file_path}.")
        return False

    if lottie_animation_data:
        st_lottie(
            lottie_animation_data, 
            speed=1, 
            reverse=False, 
            loop=True, 
            quality="high",
            height=height,
            width=width,
            key=key,
        )
        return True # Indiquer que l'affichage a réussi
    return False

# Fonction pour transcrire l'audio avec OpenAI Whisper (adaptée de votre exemple)
def transcribe_audio_openai_v2(audio_location):
    if not os.path.exists(audio_location):
        st.error(f"Fichier audio non trouvé: {audio_location}")
        return None
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), http_client=httpx.Client(proxies=None))
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

# Nouvelle fonction pour Text-to-Speech avec OpenAI
def text_to_speech_openai(text_to_speak, speech_file_location="temp_audio_response.mp3"):
    if not text_to_speak:
        st.error("Aucun texte fourni pour la synthèse vocale")
        return None
    try:
        # Assurons-nous que le texte n'est pas trop long pour l'API
        if len(text_to_speak) > 4000:
            text_to_speak = text_to_speak[:4000] + "..."
            
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), http_client=httpx.Client(proxies=None))
        
        # Message de débogage
        st.info(f"Génération audio avec OpenAI API, longueur du texte: {len(text_to_speak)} caractères")
        
        response = client.audio.speech.create(
            model="tts-1", # ou "tts-1-hd", "gpt-4o-mini-tts"
            voice="nova",  # Choisissez une voix : alloy, echo, fable, onyx, nova, shimmer
            input=text_to_speak,
            response_format="mp3" # ou wav, pcm, etc.
        )
        
        # Vérifier que la réponse contient des données
        if not response:
            st.error("Réponse vide reçue de l'API Text-to-Speech")
            return None
            
        # Enregistrement du fichier avec vérification
        speech_file_path = os.path.abspath(speech_file_location)
        response.stream_to_file(speech_file_path)
        
        # Vérifier que le fichier existe et n'est pas vide
        if os.path.exists(speech_file_path):
            file_size = os.path.getsize(speech_file_path)
            if file_size > 0:
                st.success(f"Fichier audio généré avec succès: {speech_file_path} ({file_size} bytes)")
                return speech_file_path
            else:
                st.error(f"Le fichier audio a été créé mais est vide (0 bytes)")
                return None
        else:
            st.error(f"Échec de création du fichier audio: {speech_file_path}")
            return None
            
    except Exception as e:
        st.error(f"Erreur Text-to-Speech détaillée: {str(e)}")
        if os.getenv("DEBUG_MODE") == "true":
            import traceback
            st.error(f"Traceback: {traceback.format_exc()}")
        return None

# --- Page d'Accueil Simulée ---
def display_home_page():
    st.markdown("<div class='home-container'>", unsafe_allow_html=True)
    
    # Utilisation de la nouvelle fonction pour l'animation Lottie sur la page d'accueil
    if not load_and_display_lottie("assets/Animation - 1747273263310.json", 250, 250, "lottie_home"):
        # Fallback: affiche le logo statique si Lottie échoue
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
        st.warning("Un ou plusieurs logos sont manquants dans le dossier assets pour le footer.") # Warning au lieu d'error

# --- Interface de Chat Principale ---
def display_chat_interface():
    st.markdown('<div class="chat-interface">', unsafe_allow_html=True)
    
    with st.sidebar:
        # Animation Lottie comme élément visuel principal
        st.markdown("<div style='display: flex; justify-content: center; margin: 20px 0px 20px 0px;'>", unsafe_allow_html=True)
        load_and_display_lottie(
            "assets/Animation - 1747273263310.json", 
            height=140, 
            width=140, 
            key="lottie_sidebar_home"
        )
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Titre et sous-titre
        st.title("ELI ESCP")
        st.caption("*Empathy, Listening & Inclusion*")
        st.divider()
        
        # Section À propos d'ELI
        st.header(t("about_eli_title"))
        st.info(t("about_eli_content"))
        st.divider()
        
        # Nouvelle section sur ESCP Business School
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
        
        # Section paramètres et administrateur
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
            
            # Option pour activer/désactiver la réponse vocale
            st.subheader(t("interface_options"))
            voice_enabled = st.toggle(t("voice_toggle"), 
                                    value=st.session_state.enable_voice_response,
                                    help="Lorsque activé, ELI prononcera ses réponses à voix haute")
            st.session_state.enable_voice_response = voice_enabled
            
            # Sélecteur de langue
            st.subheader(t("language_select"))
            selected_language = st.selectbox(
                t("language_select"),
                options=["Français", "English"],
                index=0 if st.session_state.language == "fr" else 1,
                key="language_selector"
            )
            # Mise à jour de la langue
            new_language = "fr" if selected_language == "Français" else "en"
            if new_language != st.session_state.language:
                st.session_state.language = new_language
                st.rerun()
        
        st.divider()
        if st.button(t("new_conversation")):
            st.session_state.messages = [{
                "role": "assistant", 
                "content": "Bonjour ! Je suis ELI, un espace d'écoute bienveillant créé pour t'accompagner. Je suis là pour t'écouter, sans jugement. Comment te sens-tu aujourd'hui ?"
            }]
            st.session_state.student_profile = {
                "name": "", "email": "", "campus": "",
                "vulnerability_score": 0, "conversation_start": datetime.now().isoformat()
            }
            st.rerun()
        
        # Afficher le dashboard de vulnérabilité DÉPLACÉ ICI, à la fin de la sidebar
        # pour qu'il soit au niveau de la zone de chat
        if os.getenv("DEBUG_MODE") == "true":
            st.divider()
            display_vulnerability_dashboard()
            
        if os.getenv("DEBUG_MODE") == "true":
            show_knowledge_base_debug()

    # --- Zone Principale du Chat ---
    st.header(t("chat_header"))
    st.markdown(t("chat_subheader"))
    st.markdown("--- ")

    # Affichage des messages
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
    
    # Ajouter un indicateur pour les nouveaux audios
    if "new_audio_ready" not in st.session_state:
        st.session_state.new_audio_ready = False

    # Afficher l'audio de la dernière réponse s'il existe
    if st.session_state.enable_voice_response and st.session_state.last_audio_file and os.path.exists(st.session_state.last_audio_file):
        try:
            st.caption(t("voice_response"))
            
            # Lire le contenu audio
            with open(st.session_state.last_audio_file, "rb") as f:
                audio_bytes = f.read()
            
            audio_b64 = base64.b64encode(audio_bytes).decode()
            
            # Déterminer si cet audio doit avoir l'autoplay activé
            # (seulement si c'est un nouvel audio qui n'a pas encore été joué)
            is_new_audio = st.session_state.new_audio_ready
            autoplay_attr = "autoplay" if is_new_audio else ""
            
            # Utiliser un composant HTML basique avec ou sans autoplay
            autoplay_html = f"""
            <audio controls {autoplay_attr} style="width:100%;">
                <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
                Votre navigateur ne supporte pas la lecture audio.
            </audio>
            """
            
            # Insérer le HTML en utilisant components.html qui contourne les restrictions
            # Nous n'utilisons plus st.audio pour éviter le double affichage
            components.html(autoplay_html, height=60)
            
            # Réinitialiser le flag new_audio_ready
            if st.session_state.new_audio_ready:
                st.session_state.new_audio_ready = False
            
            # Option pour masquer l'audio
            if st.button(t("hide_audio")):
                st.session_state.last_audio_file = None
        
        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier audio: {str(e)}")

    # --- Zone de saisie (Texte et Vocal) ---
    st.write(t("speak_instruction"))
    audio_bytes = audio_recorder(
        text="", recording_color="#E24A33", neutral_color="#4A5568", 
        icon_size="2x", pause_threshold=2.0, key="audio_input"
    )
    
    # Utiliser une variable de session pour gérer le prompt audio unique
    if "last_audio_prompt_processed" not in st.session_state:
        st.session_state.last_audio_prompt_processed = None

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
            st.session_state.last_audio_prompt_processed = audio_bytes # Marquer cet audio comme traité
        else:
            st.warning("La transcription a échoué ou aucun son n'a été détecté.")
            st.session_state.last_audio_prompt_processed = None # Réinitialiser si l'audio n'est pas valide
    
    text_prompt = st.chat_input(t("chat_input_placeholder"))
    
    final_prompt_to_process = None
    if processed_audio_prompt_this_run:
        final_prompt_to_process = processed_audio_prompt_this_run
    elif text_prompt:
        final_prompt_to_process = text_prompt
        st.session_state.last_audio_prompt_processed = None # Réinitialiser si un texte est soumis

    if final_prompt_to_process:
        # Effacer le dernier fichier audio lors d'un nouveau message
        st.session_state.last_audio_file = None
        
        st.session_state.messages.append({"role": "user", "content": final_prompt_to_process})
        with st.chat_message("user"):
            st.markdown(final_prompt_to_process)
        
        openai_messages = [{"role": "system", "content": create_system_prompt()}]
        context_messages = st.session_state.messages[-10:] # Prendre les 10 derniers messages
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
                st.markdown(response_text)
        
        if response_text:
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            
            # Génération de la réponse vocale seulement si l'option est activée
            if st.session_state.enable_voice_response:
                with st.spinner(t("voice_preparing")):
                    speech_file_location = text_to_speech_openai(response_text)
                
                if speech_file_location and os.path.exists(speech_file_location):
                    # Générer un nouvel ID unique pour cet audio
                    previous_file = st.session_state.last_audio_file
                    
                    # Si un fichier audio existait déjà, l'ajouter aux précédents
                    if previous_file and previous_file != speech_file_location:
                        st.session_state.previous_audio_ids.append(previous_file)
                    
                    # Stocker le chemin du nouveau fichier audio et marquer comme nouvel audio
                    st.session_state.last_audio_file = speech_file_location
                    st.session_state.new_audio_ready = True  # Marquer comme un nouvel audio à lire automatiquement

            if os.getenv("DEBUG_MODE") == "true":
                save_conversation(st.session_state.messages, st.session_state.student_profile)
            
            # Rerun pour afficher la réponse et l'audio
            # st.rerun() # COMMENTÉ TEMPORAIREMENT POUR DÉBOGAGE
            # Si cela est commenté, l'interface ne se mettra pas à jour automatiquement
            # après la réponse de l'assistant. Il faudra peut-être une interaction manuelle
            # (comme redimensionner la fenêtre ou cliquer sur un autre élément) pour forcer un rafraîchissement.
            # L'objectif est de voir si ce rerun est la cause du comportement instable.
            if os.getenv("DEBUG_MODE") == "true":
                st.sidebar.warning("st.rerun() après réponse de l'assistant est commenté pour débogage.")

    # --- Footer pour l'interface de chat ---
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

# --- Initialisation et Routage ---
if "chat_active" not in st.session_state:
    st.session_state.chat_active = False

if "messages" not in st.session_state: # Assurer que les messages existent toujours
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "Bonjour ! Je suis ELI, un espace d'écoute bienveillant créé pour t'accompagner. Je suis là pour t'écouter, sans jugement. Comment te sens-tu aujourd'hui ?"
    })

if "student_profile" not in st.session_state: # Assurer que le profil existe toujours
    st.session_state.student_profile = {
        "name": "", "email": "", "campus": "",
        "vulnerability_score": 0, "conversation_start": datetime.now().isoformat()
    }

# Variable pour stocker le dernier fichier audio généré
if "last_audio_file" not in st.session_state:
    st.session_state.last_audio_file = None

# --- Dans les variables de session_state, ajouter un ID pour le dernier audio ---
if "current_audio_id" not in st.session_state:
    st.session_state.current_audio_id = None

if "previous_audio_ids" not in st.session_state:
    st.session_state.previous_audio_ids = []

# Logique d'affichage : Page d'accueil ou Interface de Chat
if st.session_state.chat_active:
    display_chat_interface()
else:
    display_home_page()

# Ajouter la fonction evaluate_vulnerability qui a été supprimée
def evaluate_vulnerability(messages):
    """
    Évalue le niveau de vulnérabilité de l'étudiant en fonction des messages échangés.
    Utilise une combinaison d'analyse par LLM et d'analyse par mots-clés.
    """
    # Score initial basé sur les mots-clés (comme fallback)
    keyword_score = evaluate_vulnerability_keywords(messages)
    
    # Tenter une analyse LLM plus sophistiquée
    try:
        analysis = perform_vulnerability_analysis(messages)
        
        # Si l'analyse est disponible et valide, utiliser son score
        if analysis and "score" in analysis:
            # Convertir le score en nombre et normaliser
            llm_score = float(analysis["score"])
            # Assurer que le score est dans la plage 0-10
            vulnerability_score = max(0, min(llm_score, 10))
            
            return vulnerability_score
    except Exception as e:
        if os.getenv("DEBUG_MODE") == "true":
            print(f"Erreur lors de l'évaluation de vulnérabilité: {str(e)}")
    
    # Retourner le score basé sur les mots-clés comme fallback
    return keyword_score 