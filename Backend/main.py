import os
import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# --- Configuração do Flask e CORS ---
# Obtenha o caminho absoluto do diretório principal do projeto
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Configure o Flask para servir os arquivos HTML, CSS e JS da pasta 'Frontend'
app = Flask(__name__,
            static_folder=os.path.join(basedir, 'Frontend'),
            template_folder=os.path.join(basedir, 'Frontend'))
CORS(app)

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
    chat_prompt = f"O usuario diz: {prompt_text}. Responda à pergunta do usuario."
    input_ids = tokenizer(chat_prompt, return_tensors="pt")
    
    outputs = model.generate(**input_ids, max_new_tokens=150)
    response = tokenizer.decode(outputs[0])
    
    # Remove o prompt do início da resposta
    response = response.split(chat_prompt)[-1].strip()
    # Limpa caracteres extras que a IA pode gerar
    cleaned_response = response.replace('<bos>', '').replace('<eos>', '')
    
    return cleaned_response

# --- Rota para servir a página HTML principal ---
@app.route('/')
def serve_index():
    # Renderiza o arquivo chat.html
    return render_template('chat.html')

# --- Rota da API para processar a mensagem do chat ---
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')

    if not user_message:
        return jsonify({"error": "Mensagem não encontrada no corpo da requisição"}), 400

    print(f"Mensagem recebida: {user_message}")

    ai_response = get_gemma_response(user_message)

    return jsonify({"response": ai_response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)