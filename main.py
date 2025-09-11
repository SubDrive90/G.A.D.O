import speech_recognition as sr 
import pyAudio
import pyttsx3
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from my_window_ui import Ui_MainWindow

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()

        #inicialização da interface
        self.setupUi(self)

        #Conecta o sinal 'clicked' do botão a uma função (slot)
        #O nome do botão é 'pushButton', que foi o nome padrão entrege pelo designer
        self.pushButton.clicked.connect(self.on_button_clicked)
    
    def on_button_clicked(self):
        """ Função (slot) que será executada quando o botão for clicado."""
        QMessageBox.information(self,"Ação", "Você clicou no botão")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

#sistema de fala
engine = pyttsx3.init()

voices = engine.getProperty('voices')
engine.setProperty('voice', voices[-3].id)


def speak(text):
    """ Fala o texto em voz alta"""
    engine.say(text)
    engine.runAndWait()

r = sr.Recognizer()

#atribuição da IA
def gemma_response(user_text):
    """ 
    Aqui enviarei user_text para o modelo Gemma 2.0B
    e receberia a resposta. 
    """
    resposta = modelo_gerador_resposta(user_text)
    return resposta

#ajusta o ruido ao redor
with sr.Microphone() as source:
    print("Ajustando para o ruido ambiente...")
    r.adjust_for_ambient_noise(source, duration=5)
    print("Pronto Pode falar agora:")

    audio = r.listen(source)


    try:
        #converte o Audio para texto
        user_input = r.recognize_google(audio, language='pt-BR')
        print(user_input)

        print("Estou pensando")
        pyttsx3.say("Estou pensando...")
        pyttsx3.runAndWait()
        #obtem a resposta da IA
        resposta = gemma_response(user_input)
        print("Assistente:", resposta)
        
        #fala a resposta
        pyttsx3.say(resposta)
        pyttsx3.runAndWait()

    except sr.UnKnownValueErroe:
        print("Não entendi o que você disse.")
    except sr.RequestError:
        print("Erro ao se conectar com o serviço de reconhecimento.")

    #pip install pyttsx3
    #pip install pyqt6 pyqt6-tools
