// Chatbot Component
document.addEventListener('DOMContentLoaded', function() {
    // Chatbot state
    const chatState = {
        isOpen: false,
        currentStep: 'welcome',
        userData: {},
        conversation: [],
        unreadMessages: 0,
        isTyping: false
    };

    // Chatbot UI elements
    const chatContainer = document.createElement('div');
    const chatHeader = document.createElement('div');
    const chatMessages = document.createElement('div');
    const chatInputContainer = document.createElement('div');
    const chatInput = document.createElement('input');
    const chatSendButton = document.createElement('button');
    const chatToggle = document.createElement('button');

    // Initialize chatbot UI
    function initChatbot() {
        // Chat container
        chatContainer.id = 'chatbot-container';
        chatContainer.className = 'fixed bottom-6 right-6 w-full max-w-md bg-white dark:bg-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col z-50 transition-all duration-300 ease-in-out';
        chatContainer.style.height = '600px';
        chatContainer.style.opacity = '0';
        chatContainer.style.transform = 'translateY(20px)';
        chatContainer.style.pointerEvents = 'none';

        // Chat header
        chatHeader.className = 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-4 flex justify-between items-center';
        chatHeader.innerHTML = `
            <div class="flex items-center">
                <div class="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center mr-3">
                    <span class="text-xl">🤖</span>
                </div>
                <div>
                    <h3 class="font-semibold">Asistente huntRED®</h3>
                    <p class="text-xs opacity-80">En línea</p>
                </div>
            </div>
            <button id="minimize-chat" class="text-white/80 hover:text-white">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
                </svg>
            </button>
        `;

        // Chat messages container
        chatMessages.className = 'flex-1 overflow-y-auto p-4 space-y-4';
        chatMessages.innerHTML = `
            <div class="flex justify-start mb-4">
                <div class="bg-slate-100 dark:bg-slate-700 rounded-2xl rounded-tl-none p-4 max-w-[80%]">
                    <p class="text-slate-800 dark:text-slate-200">¡Hola! Soy tu asistente virtual de huntRED®. ¿En qué puedo ayudarte hoy?</p>
                </div>
            </div>
        `;

        // Chat input container
        chatInputContainer.className = 'border-t border-slate-200 dark:border-slate-700 p-4 bg-white dark:bg-slate-800';
        
        chatInput.type = 'text';
        chatInput.placeholder = 'Escribe tu mensaje...';
        chatInput.className = 'w-full px-4 py-3 rounded-full border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent';
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        chatSendButton.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L12.586 11H5a1 1 0 110-2h7.586l-2.293-2.293a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
        `;
        chatSendButton.className = 'absolute right-2 top-1/2 transform -translate-y-1/2 bg-indigo-600 hover:bg-indigo-700 text-white p-2 rounded-full transition-colors duration-200';
        chatSendButton.onclick = sendMessage;

        const inputWrapper = document.createElement('div');
        inputWrapper.className = 'relative';
        inputWrapper.appendChild(chatInput);
        inputWrapper.appendChild(chatSendButton);
        chatInputContainer.appendChild(inputWrapper);

        // Chat toggle button
        chatToggle.innerHTML = `
            <div class="relative">
                <div class="w-14 h-14 rounded-full bg-gradient-to-r from-indigo-600 to-purple-600 flex items-center justify-center text-white shadow-lg">
                    <span class="text-2xl">💬</span>
                </div>
                <span class="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs font-medium text-white">1</span>
            </div>
        `;
        chatToggle.className = 'fixed bottom-6 right-6 z-50 focus:outline-none';
        chatToggle.onclick = toggleChat;

        // Assemble chat container
        chatContainer.appendChild(chatHeader);
        chatContainer.appendChild(chatMessages);
        chatContainer.appendChild(chatInputContainer);

        // Add elements to the page
        document.body.appendChild(chatContainer);
        document.body.appendChild(chatToggle);

        // Add event listeners
        document.getElementById('minimize-chat').addEventListener('click', toggleChat);
    }


    // Toggle chat visibility
    function toggleChat() {
        chatState.isOpen = !chatState.isOpen;
        
        if (chatState.isOpen) {
            // Reset unread counter when opening chat
            chatState.unreadMessages = 0;
            updateUnreadBadge();
            
            chatContainer.style.opacity = '1';
            chatContainer.style.transform = 'translateY(0)';
            chatContainer.style.pointerEvents = 'auto';
            chatToggle.style.opacity = '0';
            chatToggle.style.pointerEvents = 'none';
            chatInput.focus();
        } else {
            chatContainer.style.opacity = '0';
            chatContainer.style.transform = 'translateY(20px)';
            chatContainer.style.pointerEvents = 'none';
            chatToggle.style.opacity = '1';
            chatToggle.style.pointerEvents = 'auto';
        }
    }
    
    // Update unread badge
    function updateUnreadBadge() {
        const badge = chatToggle.querySelector('.unread-badge');
        if (chatState.unreadMessages > 0) {
            if (!badge) {
                const newBadge = document.createElement('span');
                newBadge.className = 'unread-badge absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs font-medium text-white';
                newBadge.textContent = chatState.unreadMessages > 9 ? '9+' : chatState.unreadMessages;
                chatToggle.querySelector('div.relative').appendChild(newBadge);
            } else {
                badge.textContent = chatState.unreadMessages > 9 ? '9+' : chatState.unreadMessages;
            }
        } else if (badge) {
            badge.remove();
        }
    }
    
    // Show typing indicator
    function showTypingIndicator() {
        chatState.isTyping = true;
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'typing-indicator flex items-center space-x-1';
        typingIndicator.innerHTML = `
            <div class="typing-dot w-2 h-2 bg-indigo-400 rounded-full animate-bounce"></div>
            <div class="typing-dot w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
            <div class="typing-dot w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style="animation-delay: 0.4s"></div>
        `;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'flex justify-start mb-4';
        messageDiv.innerHTML = `
            <div class="typing-message bg-slate-100 dark:bg-slate-700 rounded-2xl rounded-tl-none p-4 max-w-[80%]">
                <div class="typing-indicator flex items-center space-x-1">
                    <div class="typing-dot w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
                    <div class="typing-dot w-2 h-2 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                    <div class="typing-dot w-2 h-2 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0.4s"></div>
                </div>
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return messageDiv;
    }
    
    // Hide typing indicator
    function hideTypingIndicator(typingElement) {
        if (typingElement && typingElement.parentNode) {
            typingElement.parentNode.removeChild(typingElement);
        }
        chatState.isTyping = false;
    }

    // Send message function
    function sendMessage() {
        const messageText = chatInput.value.trim();
        if (!messageText || chatState.isTyping) return;

        // Add user message to chat
        addMessage('user', messageText);
        chatInput.value = '';
        
        // Show typing indicator
        const typingElement = showTypingIndicator();

        // Simulate bot response (in a real app, this would be an API call)
        setTimeout(() => {
            hideTypingIndicator(typingElement);
            const botResponse = getBotResponse(messageText);
            addMessage('bot', botResponse);
            
            // Show notification if chat is closed
            if (!chatState.isOpen) {
                chatState.unreadMessages++;
                updateUnreadBadge();
                
                // Show desktop notification if supported
                if (Notification.permission === 'granted') {
                    new Notification('Nuevo mensaje', {
                        body: 'Tienes una nueva respuesta del asistente',
                        icon: '/static/images/logo.png'
                    });
                }
            }
        }, 1500 + Math.random() * 1000); // Random delay for more natural feel
    }

    // Add message to chat
    function addMessage(sender, text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `flex ${sender === 'user' ? 'justify-end' : 'justify-start'} mb-4`;
        
        const messageBubble = document.createElement('div');
        messageBubble.className = sender === 'user' 
            ? 'bg-indigo-600 text-white rounded-2xl rounded-tr-none p-4 max-w-[80%]' 
            : 'bg-slate-100 dark:bg-slate-700 text-slate-800 dark:text-slate-200 rounded-2xl rounded-tl-none p-4 max-w-[80%]';
        
        messageBubble.textContent = text;
        messageDiv.appendChild(messageBubble);
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Add to conversation history
        chatState.conversation.push({ sender, text });
    }

    // Simple bot response logic (would be replaced with actual NLP in production)
    function getBotResponse(message) {
        const lowerMessage = message.toLowerCase();
        
        if (lowerMessage.includes('hola') || lowerMessage.includes('buenos días') || lowerMessage.includes('buenas tardes')) {
            return '¡Hola! Soy tu asistente virtual de huntRED®. ¿En qué puedo ayudarte hoy? Puedo ayudarte con información sobre nuestras unidades de negocio, procesos de reclutamiento o programar una asesoría.';
        } else if (lowerMessage.includes('unidad') || lowerMessage.includes('negocio')) {
            return 'En huntRED® contamos con 4 unidades de negocio especializadas:\n\n' +
                   '1. huntRED® Executive: Para altos ejecutivos\n' +
                   '2. huntRED®: Para posiciones gerenciales\n' +
                   '3. huntU: Para recién egresados\n' +
                   '4. Amigro: Para movilidad laboral internacional\n\n' +
                   '¿Te gustaría más información sobre alguna en particular?';
        } else if (lowerMessage.includes('proceso') || lowerMessage.includes('contratación')) {
            return 'Nuestro proceso de contratación consta de las siguientes etapas:\n\n' +
                   '1. Evaluación de perfil\n' +
                   '2. Entrevista inicial\n' +
                   '3. Pruebas técnicas/psicométricas\n' +
                   '4. Entrevista con el área contratante\n' +
                   '5. Oferta y contratación\n\n' +
                   '¿Te gustaría programar una asesoría personalizada?';
        } else if (lowerMessage.includes('gracias')) {
            return '¡De nada! 😊 Si tienes más preguntas, no dudes en decírmelo. Estoy aquí para ayudarte.';
        } else if (lowerMessage.includes('adiós') || lowerMessage.includes('chao') || lowerMessage.includes('hasta luego')) {
            setTimeout(toggleChat, 1000);
            return '¡Hasta luego! Si necesitas más ayuda, aquí estaré. ¡Que tengas un excelente día!';
        } else {
            return 'Entiendo que quieres saber sobre: ' + message + '. ' +
                   '¿Te gustaría que te proporcione más información sobre nuestros servicios de reclutamiento, ' +
                   'desarrollo organizacional o consultoría en gestión del talento?';
        }
    }

        // Initialize the chatbot when the page loads
    initChatbot();
    
    // Request notification permission
    if ('Notification' in window) {
        if (Notification.permission !== 'denied') {
            Notification.requestPermission().then(permission => {
                console.log('Notification permission:', permission);
            });
        }
    }
    
    // Listen for new messages from other tabs/windows
    window.addEventListener('storage', (event) => {
        if (event.key === 'new_chat_message' && event.newValue) {
            try {
                const message = JSON.parse(event.newValue);
                if (message.sender !== 'current_tab') {
                    addMessage('bot', message.text);
                    
                    if (!chatState.isOpen) {
                        chatState.unreadMessages++;
                        updateUnreadBadge();
                        
                        // Show desktop notification
                        if (Notification.permission === 'granted') {
                            new Notification('Nuevo mensaje', {
                                body: message.text.substring(0, 100) + (message.text.length > 100 ? '...' : ''),
                                icon: '/static/images/logo.png'
                            });
                        }
                    }
                }
            } catch (e) {
                console.error('Error processing storage event:', e);
            }
        }
    });
    
    // Listen for visibility changes
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible' && chatState.unreadMessages > 0) {
            // Reset unread counter when tab becomes visible
            chatState.unreadMessages = 0;
            updateUnreadBadge();
        }
    });
    
    // Expose chat toggle globally for notifications
    window.toggleChat = toggleChat;
});

// WebSocket integration for real-time chat
function initChatWebSocket() {
    if (!('WebSocket' in window)) return;
    
    const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    const wsUrl = protocol + window.location.host + '/ws/chat/';
    
    const socket = new WebSocket(wsUrl);
    
    socket.onopen = function(e) {
        console.log('WebSocket connection established');
    };
    
    socket.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            if (data.type === 'NEW_MESSAGE' && window.addMessage) {
                window.addMessage('bot', data.message);
                
                // Show notification if chat is closed
                if (window.chatState && !window.chatState.isOpen) {
                    window.chatState.unreadMessages++;
                    window.updateUnreadBadge && window.updateUnreadBadge();
                    
                    // Show desktop notification
                    if (Notification.permission === 'granted') {
                        new Notification('Nuevo mensaje', {
                            body: data.message.substring(0, 100) + (data.message.length > 100 ? '...' : ''),
                            icon: '/static/images/logo.png'
                        });
                    }
                }
            }
        } catch (e) {
            console.error('Error processing WebSocket message:', e);
        }
    };
    
    socket.onclose = function(event) {
        console.log('WebSocket connection closed, reconnecting...');
        setTimeout(initChatWebSocket, 5000);
    };
    
    socket.onerror = function(error) {
        console.error('WebSocket error:', error);
    };
    
    // Store send function for later use
    window.sendChatMessage = function(message) {
        if (socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
                type: 'SEND_MESSAGE',
                message: message
            }));
            return true;
        }
        return false;
    };
}

// Initialize WebSocket connection when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initChatWebSocket);
} else {
    initChatWebSocket();
}
