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
    const texto = messageInput.value.trim();
    if (texto !== '') {
        adicionarMensagem('user', texto);
        enviarParaAPI(texto);
        messageInput.value = '';
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
    
    return messageContainer;
}

// Função para enviar o texto do usuário para a API Python
async function enviarParaAPI(texto) {
    // Desabilita o input e o botão para evitar múltiplas mensagens
    messageInput.disabled = true;
    sendBtn.disabled = true;

    // Cria a mensagem de "pensando" e armazena a referência
    const pensandoMsg = adicionarMensagem('ia', 'Pensando...');
    
    try {
        const response = await fetch('http://127.0.0.1:8000/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: texto })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Remove a mensagem de "pensando" da tela
            pensandoMsg.remove();
            
            // Adiciona a resposta da IA à interface
            adicionarMensagem('ia', data.response);
        } else {
            // Em caso de erro do servidor
            pensandoMsg.remove();
            adicionarMensagem('ia', 'Houve um erro no servidor. Por favor, tente novamente.');
            console.error('Erro na API:', data.error);
        }
    } catch (error) {
        // Em caso de erro de conexão
        pensandoMsg.remove();
        adicionarMensagem('ia', 'Não foi possível conectar ao servidor. Verifique se ele está rodando.');
        console.error('Erro de conexão:', error);
    } finally {
        // Habilita o input e o botão novamente, independentemente do resultado
        messageInput.disabled = false;
        sendBtn.disabled = false;
        messageInput.focus();
    }
}