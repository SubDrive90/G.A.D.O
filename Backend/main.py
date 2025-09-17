
from flask import Flask, request, jsonify
from flask_cors import CORS
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import os
from gtts import gTTS


app = Flask(__name__)
CORS(app) 


try:
    model_id = "google/gemma-2b-it"
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
    
    chat_prompt = f"O usuario diz: {prompt_text}. Responda à pergunta do usuario."
    input_ids = tokenizer(chat_prompt, return_tensors="pt")
    
    outputs = model.generate(**input_ids, max_new_tokens=150)
    response = tokenizer.decode(outputs[0])
    
   
    response = response.split(chat_prompt)[-1].strip()
    return response


@app.route('/Frontend/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')

    if not user_message:
        return jsonify({"error": "Mensagem não encontrada no corpo da requisição"}), 400

    print(f"Mensagem recebida: {user_message}")

   
    ai_response = get_gemma_response(user_message)
    
    
    cleaned_response = ai_response.replace('***', '').replace('**', '').replace('*', '')

    
    return jsonify({"response": cleaned_response})

if __name__ == '__main__':
    
    app.run(host='0.0.0.0', port=5000, debug=True)