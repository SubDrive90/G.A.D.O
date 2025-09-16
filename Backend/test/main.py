import os
import json
import pyaudio
import torch
import pygame
from transformers import AutoTokenizer, AutoModelForCausalLM
from vosk import Model, KaldiRecognizer
from gtts import gTTS

# --- 1. CONFIGURAÇÃO E INICIALIZAÇÃO DA IA ---
# Certifique-se de que você já aceitou a licença do modelo no Hugging Face.
# Se você ainda não fez o login, execute no terminal: `huggingface-cli login`
try:
    model_id = "google/gemma-2b-it"
    print("Carregando o modelo Gemma do Hugging Face. Isso pode levar alguns minutos na primeira vez.")
    
    # Carrega o tokenizer e o modelo da IA
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16
    )
    print("Modelo Gemma carregado com sucesso!")
except Exception as e:
    print(f"Erro ao carregar o modelo Gemma: {e}")
    print("Possíveis causas: falha na conexão, ou você não aceitou a licença do modelo no Hugging Face ou não está autenticado.")
    exit()

def get_gemma_response(prompt_text):
    """Gera uma resposta da IA a partir do texto do usuário."""
    chat_prompt = f"O usuario diz: {prompt_text}. Responda à pergunta do usuario."
    input_ids = tokenizer(chat_prompt, return_tensors="pt")
    
    # Gera a resposta da IA
    outputs = model.generate(**input_ids, max_new_tokens=150)
    response = tokenizer.decode(outputs[0])
    
    # Limpa a resposta para remover o prompt inicial
    response = response.split(chat_prompt)[-1].strip()
    return response

# --- 2. SÍNTESE DE FALA (TTS - TEXT-TO-SPEECH) ---
def speak(text):
    """Converte o texto em fala usando o Google TTS e o reproduz."""
    print(f"IA: {text}")
    try:
        tts = gTTS(text=text, lang='pt', slow=False)
        tts.save("response.mp3")

        # Inicializa o mixer do pygame e toca o arquivo
        pygame.mixer.init()
        pygame.mixer.music.load("response.mp3")
        pygame.mixer.music.play()

        # Espera a reprodução terminar antes de encerrar
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        # Encerra o mixer e remove o arquivo temporário
        pygame.mixer.quit()
        os.remove("response.mp3")

    except Exception as e:
        print(f"Erro ao gerar ou reproduzir o áudio: {e}")

# --- 3. RECONHECIMENTO DE FALA (VOSK) ---
# Altere o nome da pasta do modelo para o que você baixou
vosk_model_path = "vosk-model-pt-fb-v0.1.1-20220516_2113"

if not os.path.exists(vosk_model_path):
    print(f"Erro: A pasta do modelo Vosk '{vosk_model_path}' não foi encontrada.")
    print("Verifique se a pasta descompactada está no mesmo diretório do seu arquivo .py.")
    exit(1)

vosk_model = Model(vosk_model_path)
rec = KaldiRecognizer(vosk_model, 16000)

p = pyaudio.PyAudio()

try:
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
    stream.start_stream()
    print("Ouvindo... Fale algo para a IA. Pressione Ctrl+C para sair.")
except OSError as e:
    print(f"Erro ao inicializar o áudio: {e}")
    speak("Desculpe, ocorreu um erro no áudio. O programa será encerrado.")
    exit()

# --- 4. LOOP PRINCIPAL DE INTERAÇÃO ---
try:
    while True:
        data = stream.read(4000, exception_on_overflow=False)

        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            text = result['text']

            if text:
                print(f"Você disse: {text}")
                ia_response = get_gemma_response(text)
                
                # --- Limpa a resposta da IA antes de falar ---
                ia_response_limpa = ia_response.replace('***', '').replace('**', '').replace('*', '')
                
                # Reproduz a resposta da IA
                speak(ia_response_limpa)

except KeyboardInterrupt:
    print("\nEncerrando o programa.")
except Exception as e:
    print(f"Erro inesperado: {e}")
    speak("Desculpe, um erro inesperado ocorreu.")
finally:
    stream.stop_stream()
    stream.close()
    p.terminate()

#pip install pypiwin32
#https://huggingface.co/google/gemma-2b-it
#https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip
#pip install transformers accelerate