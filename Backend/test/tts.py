# Substitua a seção de 'SÍNTESE DE FALA' por este código
import os
from gtts import gTTS
from playsound import playsound

def speak(text):
    """Converte o texto em fala usando o Google TTS."""
    print(f"IA: {text}")
    try:
        # O Google TTS escolhe a voz automaticamente com base no idioma,
        # e as vozes masculinas e femininas variam de acordo com o texto.
        tts = gTTS(text=text, lang='pt', slow=False)
        
        # Salva e reproduz o arquivo de áudio
        tts.save("response.mp3")
        playsound("response.mp3")
        os.remove("response.mp3")
    except Exception as e:
        print(f"Erro ao gerar ou reproduzir o áudio: {e}")