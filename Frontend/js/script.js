// Seleciona os elementos da interface
const chatBody = document.querySelector('.chat-body');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');

// Adiciona o evento de clique ao botão de envio
sendBtn.addEventListener('click', () => {
    enviarMensagem();
});

// Permite enviar a mensagem pressionando 'Enter'
messageInput.addEventListener('keypress', (event) => {
    if (event.key === 'Enter') {
        enviarMensagem();
    }
});

function enviarMensagem() {
    const texto = messageInput.value.trim(); // Pega o texto e remove espaços extras
    if (texto !== '') {
        adicionarMensagem('user', texto); // Exibe a mensagem do usuário
        enviarParaAPI(texto); // Envia para o backend Python
        messageInput.value = ''; // Limpa o campo de entrada
    }
}

// Função para adicionar uma mensagem à interface de chat
function adicionarMensagem(autor, texto) {
    const messageContainer = document.createElement('div');
    messageContainer.classList.add('message-container', autor);

    const message = document.createElement('div');
    message.classList.add('message');
    message.textContent = texto;

    messageContainer.appendChild(message);
    chatBody.appendChild(messageContainer);
    // Rola para a última mensagem
    chatBody.scrollTop = chatBody.scrollHeight;
}

// Função para enviar o texto do usuário para a API Python
async function enviarParaAPI(texto) {
    // Mensagem de "pensando" enquanto a IA processa
    const pensandoMsg = adicionarMensagem('ia', 'Pensando...');
    
    try {
        const response = await fetch('http://127.0.0.1:8000/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: texto })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Remove a mensagem de "pensando" e adiciona a resposta da IA
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