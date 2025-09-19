import os
import json
import torch
import datetime
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
    print(f"Erro ao inicializar o Firebase: {e}")
    db = None

# --- Inicialização do Modelo de IA ---
try:
    model_id = "google/gemma-2b-it"
    print("Carregando o modelo Gemma...")
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        dtype=torch.bfloat16
    )
    print("Modelo Gemma carregado com sucesso para a API!")
except Exception as e:
    print(f"Erro ao carregar o modelo Gemma: {e}")
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
        # Pega a data e a hora atual
        current_date = datetime.datetime.now().strftime("%d/%m/%Y")
        # Envia apenas a mensagem do usuário para a função da IA
        ai_response = get_gemma_response(user_message)
        
        # Garante que a resposta seja uma string não vazia
        if not ai_response:
            ai_response = "Desculpe, não consegui gerar uma resposta para isso."
        
        print(f"Resposta da IA: {ai_response}")

        # --- Salva a conversa no Firestore ---
        if db:
            chat_data = {
                'user_message': user_message,
                'ai_response': ai_response,
                'timestamp': datetime.datetime.now()
            }
            doc_ref = db.collection('chat_history').add(chat_data)
            print(f"Conversa salva com sucesso! ID do documento: {doc_ref[1].id}")

        return jsonify({"response": ai_response})
    
    except Exception as e:
        print(f"Erro ao processar a resposta da IA ou salvar no Firestore: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)

    """huggingface-cli login"""
    """pip install firebase-admin"""