const micBtn = document.querySelector('.mic-btn');
const chatBody = document.querySelector('.chat-body');


const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;


if (SpeechRecognition) {
    const recognition = new SpeechRecognition();
    recognition.lang = 'pt-BR'; 
    recognition.continuous = false; 
    recognition.interimResults = false; 


    let isListening = false;

  
    micBtn.addEventListener('click', () => {
        if (!isListening) {
            recognition.start();
            isListening = true;
            micBtn.textContent = '🔴'; 
            adicionarMensagem('user', 'Ouvindo...');
        } else {
            recognition.stop();
            isListening = false;
            micBtn.textContent = '🎤';
        }
    });

    
    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        adicionarMensagem('user', transcript); 
        enviarParaAPI(transcript); 
    };

 
    recognition.onend = () => {
        isListening = false;
        micBtn.textContent = '🎤'; 
    };


    recognition.onerror = (event) => {
        console.error('Erro no reconhecimento de voz:', event.error);
        adicionarMensagem('ia', 'Desculpe, houve um erro no microfone. Tente novamente.');
        isListening = false;
        micBtn.textContent = '🎤';
    };

} else {

    micBtn.style.display = 'none';
    adicionarMensagem('ia', 'Seu navegador não suporta reconhecimento de voz.');
}


function adicionarMensagem(autor, texto) {
    const messageContainer = document.createElement('div');
    messageContainer.classList.add('message-container', autor);

    const message = document.createElement('div');
    message.classList.add('message');
    message.textContent = texto;

    messageContainer.appendChild(message);
    chatBody.appendChild(messageContainer);

    chatBody.scrollTop = chatBody.scrollHeight;
}


async function enviarParaAPI(texto) {

    const pensandoMsg = adicionarMensagem('ia', 'Pensando...');
    
    try {
        const response = await fetch('http://127.0.0.1:5000/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: texto })
        });
        
        const data = await response.json();
        
        if (response.ok) {
 
            pensandoMsg.remove();
            adicionarMensagem('ia', data.response);
        } else {
            pensandoMsg.remove();
            adicionarMensagem('ia', 'Houve um erro no servidor. Por favor, tente novamente.');
            console.error('Erro na API:', data.error);
        }
    } catch (error) {
        pensandoMsg.remove();
        adicionarMensagem('ia', 'Não foi possível conectar ao servidor. Verifique se ele está rodando.');
        console.error('Erro de conexão:', error);
    }
}