import json
import os
from datetime import datetime
import pandas as pd

# Fonction pour sauvegarder les conversations
def save_conversation(messages, student_profile):
    """
    Sauvegarde une conversation avec le profil étudiant dans un fichier JSON
    """
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
    
    # Mettre à jour le fichier csv des statistiques
    update_stats(student_profile, len(messages))
    
    return filename

# Fonction pour mettre à jour les statistiques
def update_stats(student_profile, message_count):
    """
    Met à jour les statistiques des conversations
    """
    stats_file = "./logs/conversation_stats.csv"
    
    # Création des données pour cette conversation
    new_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "campus": student_profile.get("campus", "Non spécifié"),
        "vulnerability_score": student_profile.get("vulnerability_score", 0),
        "message_count": message_count,
        "duration_minutes": calculate_duration(student_profile.get("conversation_start", ""))
    }
    
    # Vérification si le fichier existe
    if os.path.exists(stats_file):
        df = pd.read_csv(stats_file)
        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
    else:
        df = pd.DataFrame([new_data])
    
    # Sauvegarde des données
    df.to_csv(stats_file, index=False)

# Fonction pour calculer la durée de la conversation
def calculate_duration(start_time_str):
    """
    Calcule la durée d'une conversation en minutes
    """
    try:
        start_time = datetime.fromisoformat(start_time_str)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() / 60
        return round(duration, 2)
    except:
        return 0

# Fonction pour évaluer le niveau de vulnérabilité
def evaluate_vulnerability(messages):
    """
    Évalue le niveau de vulnérabilité basé sur les messages
    (Ceci est un exemple simplifié - à remplacer par une vraie logique d'évaluation)
    """
    # Mots clés associés à des niveaux de vulnérabilité
    vulnerability_keywords = {
        "anxieux": 1, "stressé": 1, "inquiet": 1, 
        "déprimé": 2, "triste": 2, "seul": 2,
        "désespéré": 3, "suicidaire": 4, "mourir": 4
    }
    
    score = 0
    
    # Analyse des messages utilisateur
    user_messages = [msg["content"] for msg in messages if msg["role"] == "user"]
    
    for message in user_messages:
        message = message.lower()
        for keyword, value in vulnerability_keywords.items():
            if keyword in message:
                score += value
    
    # Limitation du score
    return min(score, 10) 