# main.py

import os
import json
import torch
import pygame
from transformers import AutoTokenizer, AutoModelForCausalLM
from flask import Flask, request, jsonify, render_template # Note a mudança aqui
from flask_cors import CORS
from gtts import gTTS

# --- Configuração do Flask e CORS ---
# Obtenha o caminho absoluto do diretório principal do projeto
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Use as pastas padronizadas do Flask: 'templates' e 'static'
# A rota para o template será 'Frontend/chat.html' e os arquivos estáticos serão servidos de 'Frontend'
app = Flask(__name__,
            static_folder=os.path.join(basedir, 'Frontend'),
            template_folder=os.path.join(basedir, 'Frontend'))
CORS(app)

# ... restante do seu código ...

# --- Rota para servir a página HTML principal ---
@app.route('/')
def serve_index():
    # Agora renderizamos o template, o que nos permite usar 'url_for' no HTML
    return render_template('chat.html')

# --- Rota para processar a requisição de fala da API ---
@app.route('/api/chat', methods=['POST'])
def chat():
    # ... o resto do código da API permanece o mesmo
    data = request.json
    user_message = data.get('message', '')

    if not user_message:
        return jsonify({"error": "Mensagem não encontrada no corpo da requisição"}), 400

    print(f"Mensagem recebida: {user_message}")

    ai_response = get_gemma_response(user_message)
    cleaned_response = ai_response.replace('***', '').replace('**', '').replace('*', '')

    return jsonify({"response": cleaned_response})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)