import os
import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS


basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

app = Flask(__name__,
            static_folder=os.path.join(basedir, 'Frontend'),
            template_folder=os.path.join(basedir, 'Frontend'))
CORS(app)

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


def get_gemma_response(prompt_text):
    """Gera uma resposta da IA a partir do texto do usuário."""
    chat_prompt = f"Você é um assistente virtual útil e amigável. O usuario diz: {prompt_text}. Responda à pergunta do usuario."
    input_ids = tokenizer(chat_prompt, return_tensors="pt")
    
    outputs = model.generate(**input_ids, max_new_tokens=150)
    response = tokenizer.decode(outputs[0])
    

    response = response.split(chat_prompt)[-1].strip()

    cleaned_response = response.replace('<bos>', '').replace('<eos>', '')
    
    return cleaned_response


@app.route('/')
def serve_index():

    return render_template('chat.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')

    if not user_message:
        return jsonify({"error": "Mensagem não encontrada no corpo da requisição"}), 400

    print(f"Mensagem recebida: {user_message}")

    ai_response = get_gemma_response(user_message)
    print(ai_response)
    return jsonify({"response": ai_response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)

    """huggingface-cli login"""