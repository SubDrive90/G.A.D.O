import pyttsx3
engine = pyttsx3.init()


voices = enine.getproperty('voices')

engine.setProperty('voice',voices[-2].id)

engine.say("Eu vou falar esse texto")
engine.runAndWait()