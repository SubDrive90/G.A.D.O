import os
import json
import datetime
import random
import string
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests # Adicionado para baixar o modelo GGUF

# --- IMPORTANTE: Biblioteca para OTIMIZAÇÃO de CPU ---
# Esta biblioteca é usada para carregar modelos no formato GGUF,
# que são quantizados para rodar muito mais rápido na CPU/RAM.
from llama_cpp import Llama 

# --- Configuração do Flask e CORS ---
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

app = Flask(__name__,
            static_folder=os.path.join(basedir, 'Frontend'),
            template_folder=os.path.join(basedir, 'Frontend'))
CORS(app)

# --- Inicialização do Firebase Firestore ---
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    firebase_key_path = os.path.join(current_dir, "firebase-key.json")
    
    cred = credentials.Certificate(firebase_key_path)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Conexão com o Firebase Firestore estabelecida com sucesso!")
except Exception as e:
    print(f"Erro ao conectar ao Firebase Firestore: {e}")
    exit()

def delete_all_messages():
    """Deleta todos os documentos da coleção 'conversations'."""
    try:
        docs = db.collection('conversations').stream()
        for doc in docs:
            doc.reference.delete()
        print("Todos os documentos da coleção 'conversations' foram deletados com sucesso!")
    except Exception as e:
        print(f"Erro ao deletar documentos: {e}")

# Deleta todos os documentos na inicialização
delete_all_messages()

# --- Geração de um ID de Sessão e Nome de Usuário ---
def generate_random_string(length=8):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

session_id = generate_random_string()
user_name = f"usuário_{session_id}"

# --- Inicialização do Modelo de IA (Otimizado GGUF) ---

# O modelo Mistral 7B quantizado em Q4_K_M (excelente equilíbrio)
MODEL_URL = "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
MODEL_PATH = "mistral-7b-instruct-v0.2.Q4_K_M.gguf"

# Função para garantir que o modelo GGUF seja baixado
def ensure_model_downloaded():
    if not os.path.exists(MODEL_PATH):
        print(f"Baixando o modelo GGUF otimizado de: {MODEL_URL}...")
        try:
            response = requests.get(MODEL_URL, stream=True)
            response.raise_for_status() # Lança um erro para códigos de status ruins
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024 # 1 Kibibyte
            downloaded = 0
            
            with open(MODEL_PATH, 'wb') as file:
                for data in response.iter_content(block_size):
                    downloaded += len(data)
                    file.write(data)
                    # Exibindo progresso
                    progress = int(50 * downloaded / total_size)
                    print(f"Progresso: [{'#' * progress}{'-' * (50 - progress)}] {downloaded/ (1024*1024):.2f}MB / {total_size / (1024*1024):.2f}MB", end='\r')
            print("\nDownload do modelo concluído!")
        except Exception as e:
            print(f"\nErro ao baixar o modelo GGUF. Por favor, verifique sua conexão: {e}")
            exit()
    else:
        print("Modelo GGUF já existe. Pulando o download.")

try:
    # Garante que o arquivo GGUF esteja presente
    ensure_model_downloaded()
    
    # Carregando o modelo GGUF otimizado
    print("Carregando o modelo Mistral 7B (Otimizado GGUF)...")
    model = Llama(
        model_path=MODEL_PATH,
        n_ctx=2048, # Contexto maior
        n_gpu_layers=0, # Força CPU (para portabilidade)
        verbose=False
    )
    print("Modelo Mistral 7B Otimizado GGUF carregado com sucesso!")
except Exception as e:
    print(f"Erro ao carregar o modelo GGUF: {e}")
    print("Certifique-se de ter instalado o 'llama-cpp-python' (pip install llama-cpp-python).")
    exit()

# --- Função de Geração de Resposta da IA ---
def get_mistral_gguf_response(prompt_text):
    """Gera uma resposta da IA usando o modelo GGUF otimizado."""
    
    # Obtém a data atual para o contexto
    current_date = datetime.datetime.now().strftime("%d de %B de %Y")
    
    # A instrução de sistema agora inclui a data para contexto, mas pede para o modelo não mencioná-la
    system_instruction = (
        f"Você é um assistente virtual prestativo e amigável. "
        f"A data atual é {current_date}. "
        f"Responda a todas as perguntas(sem excessões) estritamente e somente em português (Brasil). "
        f"Não mencione a data na sua resposta, a menos que seja explicitamente perguntado."
    )
    
    # Formato de prompt específico para o Mistral Instruct, incluindo a instrução de sistema
    prompt_template = f"<s>[INST] {system_instruction} {prompt_text} [/INST]"
    
    output = model(
        prompt_template,
        max_tokens=150,
        temperature=0.7,
        stop=["[INST]", "</s>"], # Garante que a IA não continue a conversa
        echo=False
    )
    
    # O resultado vem como uma lista de texto, pegamos a primeira e limpamos
    ai_response = output['choices'][0]['text'].strip()
    return ai_response

# --- Rota para servir a página HTML principal ---
@app.route('/')
def serve_index():
    return render_template('chat.html')

# --- Rota da API para processar a mensagem do chat ---
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')

    if not user_message:
        return jsonify({"error": "Mensagem não encontrada no corpo da requisição"}), 400

    print(f"Mensagem recebida: {user_message}")

    try:
        # Passa a mensagem do usuário diretamente
        ai_response = get_mistral_gguf_response(user_message)
        
        if not ai_response:
            ai_response = "Desculpe, não consegui gerar uma resposta para isso."

        db.collection("conversations").add({
            "session_id": session_id,
            "user_name": user_name,
            "sender": "user",
            "message": user_message,
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        
        db.collection("conversations").add({
            "session_id": session_id,
            "user_name": user_name,
            "sender": "ai",
            "message": ai_response,
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        
        print(f"Resposta da IA: {ai_response}")
        return jsonify({"response": ai_response, "user_name": user_name})
    
    except Exception as e:
        print(f"Erro ao processar a resposta da IA: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
    """pip install --upgrade huggingface_hub"""
    """huggingface-cli login"""
    """pip install firebase-admin"""