from vosk import Model, KaldiRecognizer
import os
import pyaudio
import pyttsx3
import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

model_id = "google/gemma-2b-it"

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16
)

def get_gemma_response(prompt_text):

    chat_prompt = f"O usuario diz: {prompt_text}. Responda á pergunta do usuario."

    input_ids = tokenizer(chat_prompt, return_tensors="pt")

    outputs = model.generate(**input_ids, max_new_tokens=150)

    response = tokenizer.decode(outputs[0])

    response = response.split(chat_prompt)[-1].strip()

    return response

#sintese de fala
engine = pyttsx3.init()

voices = engine.getproperty('voices')
engine.setProperty('voice',voices[-2].id)


def speak(text):
    engine.say(text)
    engine.runAndWait()

model = Model("model")
rec = KaldiRecognizer(model, 16000)

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
stream.start_stream()

while True:
    data = stream.read(4000,exception_on_overflow=False)
    if len(data) == 0:
        break
    if rec.AcceptWaveform(data):
        result = json.loads(rec.Result())
        text = result['text']
        if text:
            print(f"Você disse: {text}")

            ia_response = get_gemma_response(text)

            print(f"IA respondeu: {ia_response}")
            speak(ia_response)


#https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip
#pip install transformers accelerate