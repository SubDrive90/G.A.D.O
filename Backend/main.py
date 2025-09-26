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

# --- Inicialização do Modelo de IA ---
try:
    # Alterado o ID do modelo para o Llama 3 8B Instruct
    model_id = "meta-llama/Meta-Llama-3-8B-Instruct"
    print("Carregando o modelo Llama 3 8B...")
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16,
        low_cpu_mem_usage=True
    )
    print("Modelo Llama 3 8B carregado com sucesso para a API!")
except Exception as e:
    print(f"Erro ao carregar o modelo Llama 3 8B: {e}")
    exit()

# --- Função de Geração de Resposta da IA ---
def get_gemma_response(prompt_text):
    """Gera uma resposta da IA a partir do texto do usuário."""
    # O Llama 3 usa um formato de prompt específico para chat
    chat = [
        {"role": "user", "content": prompt_text},
    ]
    
    # Aplica o formato de template do Llama 3
    prompt = tokenizer.apply_chat_template(
        chat,
        tokenize=False,
        add_generation_prompt=True
    )
    
    input_ids = tokenizer(prompt, return_tensors="pt")
    
    outputs = model.generate(
        **input_ids,
        max_new_tokens=150
    )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # O Llama 3 retorna todo o histórico (inclusive o prompt). Pegamos apenas a parte da resposta.
    # Esta é uma simplificação e pode ser refinada.
    ai_response = response.split("<|end_of_turn|>")[-1].strip()
    
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
        current_date = datetime.datetime.now().strftime("%d/%m/%Y")
        prompt_with_date = f"Hoje é dia {current_date}. {user_message}"
        
        ai_response = get_gemma_response(prompt_with_date)
        
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