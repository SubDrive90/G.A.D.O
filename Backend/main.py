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
db = None  # Inicializa db como None para ser usado em `chat()`
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    key_file_path = os.path.join(current_dir, 'firebase-key.json')

    if not os.path.exists(key_file_path):
        print(f"Erro: O arquivo {key_file_path} não foi encontrado. Verifique se ele está na pasta correta.")
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
    chat_prompt = f"Você é um assistente virtual útil e amigável. Responda à seguinte pergunta do usuário de forma completa e natural: '{prompt_text}'"
    
    input_ids = tokenizer(chat_prompt, return_tensors="pt")
    outputs = model.generate(**input_ids, max_new_tokens=150)
    response = tokenizer.decode(outputs[0])
    
    # Limpa a resposta
    if chat_prompt in response:
        cleaned_response = response.split(chat_prompt)[-1].strip()
    else:
        cleaned_response = response.strip()

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

        # Verifica se a mensagem contém o nome do usuário para salvar
        user_name = None
        if "me chamo" in user_message.lower():
            try:
                # Tenta extrair o nome
                parts = user_message.lower().split("me chamo")
                if len(parts) > 1:
                    user_name = parts[1].strip()
            except Exception as e:
                print(f"Erro ao extrair o nome: {e}")
        
        # --- Salva o nome do usuário no Firestore ---
        if db and user_name:
            user_ref = db.collection('users').document('user_info')
            user_ref.set({'name': user_name})
            print(f"Nome do usuário '{user_name}' salvo com sucesso!")

        # Constrói um prompt mais completo para a IA
        # Tenta buscar o nome do usuário, se já estiver salvo
        user_name_from_db = None
        if db:
            user_ref = db.collection('users').document('user_info')
            user_doc = user_ref.get()
            if user_doc.exists and 'name' in user_doc.to_dict():
                user_name_from_db = user_doc.to_dict()['name']
        
        if user_name_from_db:
            prompt_with_name = f"O usuário se chama {user_name_from_db}. {user_message}"
        else:
            prompt_with_name = user_message
        
        # Pega a resposta da IA com o prompt atualizado
        ai_response = get_gemma_response(prompt_with_name)
        
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