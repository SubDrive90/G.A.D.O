# our main file

import speech_recognition as sr

# cria um reconhecedor
r = sr.Recognizer()

#abrir microfone para captura 

with sr.Microphone() as source:
    audio = r.listen(source) # define microfone como fonte de audio

    print(r.recognize_google(audio, language="pt-BR"))