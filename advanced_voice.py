# ==========================================
# ADVANCED VOICE - JARVIS PRO (ELEVENLABS NATURAL VOICE)
# ==========================================
import requests
from config import ELEVENLABS_API_KEY, VOICE_ID, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

def generate_natural_audio(text):
    """Gera áudio natural via ElevenLabs API."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2", # Modelo que fala Português perfeitamente
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            return response.content # Retorna os bytes do áudio MP3
        else:
            print(f"[VOICE ERROR] ElevenLabs Status: {response.status_code}")
            return None
    except Exception as e:
        print(f"[VOICE EXCEPTION] {e}")
        return None

def send_voice_alert(title, message):
    """Gera o áudio e envia para o Telegram como um arquivo de voz."""
    
    # Monta a frase natural
    full_text = f"{title}. {message}"
    
    audio_bytes = generate_natural_audio(full_text)
    
    if audio_bytes:
        try:
            url_send_audio = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVoice"
            files = {'voice': ('alert.mp3', audio_bytes, 'audio/mpeg')}
            data = {'chat_id': TELEGRAM_CHAT_ID}
            
            r = requests.post(url_send_audio, files=files, data=data)
            if r.status_code == 200:
                print("[VOICE] Áudio natural enviado com sucesso.")
            else:
                print(f"[TELEGRAM VOICE ERROR] {r.text}")
        except Exception as e:
            print(f"[SEND VOICE ERROR] {e}")

if __name__ == "__main__":
    # Teste rápido
    send_voice_alert("Sistema Iniciado", "A Sexta-Feira Advanced está pronta para operar com voz natural.")