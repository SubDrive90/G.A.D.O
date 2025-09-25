import os
import json
import torch
import datetime
import random
import string
import firebase_admin
from firebase_admin import credentials, firestore
from transformers import AutoTokenizer, AutoModelForCausalLM
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# --- Configuração do Flask e CORS ---
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

app = Flask(__name__,
            static_folder=os.path.join(basedir, 'Frontend'),
            template_folder=os.path.join(basedir, 'Frontend'))
CORS(app)

# --- Configuração do Firebase ---
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    key_file_path = os.path.join(current_dir, 'firebase-key.json')

    if not os.path.exists(key_file_path):
        print(f"Erro: O arquivo {key_file_path} não foi encontrado. Verifique se ele está na pasta correta.")
        cred = None
        db = None
    else:
        cred = credentials.Certificate(key_file_path)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("Firebase inicializado e Firestore conectado com sucesso!")
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

# --- Inicialização do Modelo de IA ---
try:
    # Definindo o ID do modelo para o Mistral 7B
    model_id = "mistralai/Mistral-7B-Instruct-v0.2"
    print("Carregando o modelo Mistral 7B...")
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16,
        low_cpu_mem_usage=True
    )
    print("Modelo Mistral 7B carregado com sucesso para a API!")
except Exception as e:
    print(f"Erro ao carregar o modelo Mistral 7B: {e}")
    exit()

# --- Função de Geração de Resposta da IA ---
def get_gemma_response(prompt_text):
    """Gera uma resposta da IA a partir do texto do usuário."""
    # Novo prompt para garantir que a IA não confunda a data com a resposta
    chat_prompt = f"Você é um assistente virtual útil e amigável. Por favor, responda à seguinte pergunta do usuário de forma completa e natural: '{prompt_text}'"
    
    input_ids = tokenizer(chat_prompt, return_tensors="pt")
    outputs = model.generate(**input_ids, max_new_tokens=150)
    response = tokenizer.decode(outputs[0])
    
    # Remove a parte do prompt da resposta da IA
    if chat_prompt in response:
        cleaned_response = response.split(chat_prompt)[-1].strip()
    else:
        cleaned_response = response.strip()

    # Limpa tags extras que a IA pode gerar
    cleaned_response = cleaned_response.replace('<bos>', '').replace('<eos>', '')
    
    return cleaned_response

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
        current_date = datetime.datetime.now().strftime("%d/%m/%Y")
        # Envia apenas a mensagem do usuário para a função da IA
        ai_response = get_gemma_response(user_message)
        
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

    """huggingface-cli login"""
    """pip install --upgrade huggingface_hub"""
    """huggingface-cli login"""
    """pip install firebase-admin"""