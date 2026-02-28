import json
import os
import requests

class GeminiClient:
    def __init__(self, api_key=None, enabled=True):
        # Récupère la clé et retire les espaces/sauts de ligne accidentels
        raw_key = api_key or os.getenv("GEMINI_API_KEY")
        self.api_key = raw_key.strip() if raw_key else None
        self.enabled = enabled
        self.history = []  # Stores context: {"role": "user"|"model", "parts": [{"text": ...}]}

    def is_available(self):
        return self.enabled and self.api_key is not None

    def query(self, user_query, context_limit=5):
        if not self.enabled:
            return "AI désactivée (mode --no-ai)."
        if not self.api_key:
            return "Clé API Gemini manquante. Définissez GEMINI_API_KEY dans le fichier .env."

        # Add the new user query to the history
        self.history.append({"role": "user", "parts": [{"text": user_query}]})
        
        # URL et Headers basés sur ton exemple curl fonctionnel
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"
        headers = {
            'Content-Type': 'application/json',
            'X-goog-api-key': self.api_key
        }
        
        # Limite l'historique pour le contexte (Gemini attend une liste d'objets content)
        body = {
            "contents": self.history[-(context_limit*2 + 1):] 
        }

        try:
            response = requests.post(url, headers=headers, json=body, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            # Extraction du texte de la réponse
            try:
                text = data['candidates'][0]['content']['parts'][0]['text']
                self.history.append({"role": "model", "parts": [{"text": text}]})
                return text
            except (KeyError, IndexError):
                return f"Erreur de structure de réponse Gemini: {json.dumps(data)}"
        except Exception as e:
            return f"Erreur Gemini: {e}"
