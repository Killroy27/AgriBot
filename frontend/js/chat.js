/**
 * AgriBot Chat Module
 * Gestion de l'interface de chat : messages, envoi, réception, affichage.
 */

const Chat = {
    isProcessing: false,

    /**
     * Envoie le message saisi
     */
    async send() {
        const input = document.getElementById('messageInput');
        const message = input.value.trim();

        if (!message || this.isProcessing) return;

        // Masquer l'écran de bienvenue
        const welcome = document.getElementById('welcomeScreen');
        if (welcome) welcome.style.display = 'none';

        // Afficher le message utilisateur
        this.addMessage(message, 'user');
        input.value = '';
        this.autoResize(input);

        // Montrer l'indicateur de typing
        this.showTyping();
        this.isProcessing = true;
        this.updateSendButton();

        try {
            const response = await API.chat(message);
            this.hideTyping();
            this.addAssistantMessage(response);
        } catch (error) {
            this.hideTyping();
            this.addErrorMessage(error.message);
        } finally {
            this.isProcessing = false;
            this.updateSendButton();
        }
    },

    /**
     * Envoie une suggestion prédéfinie
     */
    sendSuggestion(text) {
        const input = document.getElementById('messageInput');
        input.value = text;
        this.send();
    },

    /**
     * Ajoute un message utilisateur
     */
    addMessage(text, type) {
        const container = document.getElementById('chatContainer');
        const time = new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });

        const avatarIcon = type === 'user' ? 'user' : 'wheat';

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i data-lucide="${avatarIcon}" class="lucide-icon-sm"></i>
            </div>
            <div class="message-content">
                <div class="message-bubble">${this.formatText(text)}</div>
                <div class="message-meta">
                    <span class="message-time">${time}</span>
                </div>
            </div>
        `;

        container.appendChild(messageDiv);
        if (window.lucide) window.lucide.createIcons({ root: messageDiv });
        this.scrollToBottom();
    },

    /**
     * Ajoute un message assistant avec sources
     */
    addAssistantMessage(response) {
        const container = document.getElementById('chatContainer');
        const time = new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });

        // Confidence level
        const confidence = response.confidence || 0;
        const confLevel = confidence >= 0.7 ? 'high' : confidence >= 0.4 ? 'medium' : 'low';
        const confPercent = Math.round(confidence * 100);

        // Sources HTML
        let sourcesHtml = '';
        if (response.sources && response.sources.length > 0) {
            const uniqueSources = [...new Set(response.sources.map(s => s.document))];
            sourcesHtml = `
                <div class="sources-container">
                    <div class="sources-title">
                        <i data-lucide="paperclip" class="lucide-icon-xs"></i>
                        Sources
                    </div>
                    ${uniqueSources.map(s => `<span class="source-tag"><i data-lucide="file-text" class="lucide-icon-xs"></i> ${s}</span>`).join('')}
                </div>
            `;
        }

        // Confidence bar HTML
        let confidenceHtml = '';
        if (response.model_used && response.model_used !== 'orchestrator') {
            confidenceHtml = `
                <div class="confidence-bar">
                    <span class="confidence-label">Confiance</span>
                    <div class="confidence-track">
                        <div class="confidence-fill ${confLevel}" style="width: ${confPercent}%"></div>
                    </div>
                    <span class="confidence-value ${confLevel}">${confPercent}%</span>
                </div>
            `;
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant';
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i data-lucide="wheat" class="lucide-icon-sm"></i>
            </div>
            <div class="message-content">
                <div class="message-bubble">${this.formatText(response.answer)}</div>
                ${sourcesHtml}
                ${confidenceHtml}
                <div class="message-meta">
                    <span class="message-time">${time}</span>
                    ${response.model_used ? `<span class="message-model">${response.model_used}</span>` : ''}
                    ${response.processing_time ? `<span class="message-time"><i data-lucide="zap" class="lucide-icon-xs" style="vertical-align: middle;"></i> ${response.processing_time}s</span>` : ''}
                </div>
            </div>
        `;

        container.appendChild(messageDiv);
        if (window.lucide) window.lucide.createIcons({ root: messageDiv });
        this.scrollToBottom();
    },

    /**
     * Message d'erreur
     */
    addErrorMessage(errorText) {
        const container = document.getElementById('chatContainer');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant';
        messageDiv.innerHTML = `
            <div class="message-avatar" style="background: var(--error); box-shadow: none;">
                <i data-lucide="alert-triangle" class="lucide-icon-sm" style="color: white;"></i>
            </div>
            <div class="message-content">
                <div class="message-bubble" style="border-color: var(--error); background: var(--error-bg);">
                    <strong style="color: var(--error);">Erreur :</strong> ${this.escapeHtml(errorText)}
                </div>
            </div>
        `;
        container.appendChild(messageDiv);
        if (window.lucide) window.lucide.createIcons({ root: messageDiv });
        this.scrollToBottom();
    },

    /**
     * Formate le texte (markdown simple)
     */
    formatText(text) {
        let html = this.escapeHtml(text);

        // Bold
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        // Italic
        html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');

        // Code inline
        html = html.replace(/`(.*?)`/g, '<code>$1</code>');

        // Lists
        html = html.replace(/^- (.*)/gm, '<li>$1</li>');
        html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

        // Numbered lists
        html = html.replace(/^\d+\. (.*)/gm, '<li>$1</li>');

        // Headers
        html = html.replace(/^### (.*)/gm, '<strong>$1</strong>');
        html = html.replace(/^## (.*)/gm, '<strong style="font-size: 1.1em;">$1</strong>');

        // Line breaks
        html = html.replace(/\n/g, '<br>');

        // Clean up nested ul
        html = html.replace(/<\/ul><br><ul>/g, '');
        html = html.replace(/<br><ul>/g, '<ul>');
        html = html.replace(/<\/ul><br>/g, '</ul>');

        return html;
    },

    /**
     * Échappe le HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    /**
     * Indicateur de typing
     */
    showTyping() {
        const container = document.getElementById('chatContainer');
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typingIndicator';
        typingDiv.className = 'message assistant typing-indicator';
        typingDiv.innerHTML = `
            <div class="message-avatar">
                <i data-lucide="wheat" class="lucide-icon-sm"></i>
            </div>
            <div class="message-content">
                <div class="message-bubble" style="display: flex; align-items: center; gap: 12px;">
                    <div class="typing-dots">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                    <span class="typing-text">AgriBot réfléchit...</span>
                </div>
            </div>
        `;
        container.appendChild(typingDiv);
        if (window.lucide) window.lucide.createIcons({ root: typingDiv });
        this.scrollToBottom();
    },

    hideTyping() {
        const typing = document.getElementById('typingIndicator');
        if (typing) typing.remove();
    },

    /**
     * Auto-resize du textarea
     */
    autoResize(el) {
        el.style.height = 'auto';
        el.style.height = Math.min(el.scrollHeight, 120) + 'px';
    },

    /**
     * Gestion du clavier
     */
    handleKeydown(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            this.send();
        }
    },

    /**
     * Update send button state
     */
    updateSendButton() {
        const btn = document.getElementById('sendBtn');
        btn.disabled = this.isProcessing;
        btn.innerHTML = this.isProcessing ? '<div class="spinner"></div>' : '<i data-lucide="send" class="lucide-icon"></i>';
        if (window.lucide && !this.isProcessing) window.lucide.createIcons({ root: btn });
    },

    /**
     * Scroll en bas du chat
     */
    scrollToBottom() {
        const chatArea = document.getElementById('chatArea');
        setTimeout(() => {
            chatArea.scrollTop = chatArea.scrollHeight;
        }, 50);
    },

    /**
     * Nouvelle conversation
     */
    clearChat() {
        const container = document.getElementById('chatContainer');
        container.innerHTML = '';

        // Re-afficher le welcome screen
        const welcome = document.createElement('div');
        welcome.className = 'welcome-screen';
        welcome.id = 'welcomeScreen';
        welcome.innerHTML = `
            <div class="welcome-icon">
                <i data-lucide="wheat" class="lucide-icon-xl"></i>
            </div>
            <h2 class="welcome-title">Bienvenue sur AgriBot</h2>
            <p class="welcome-subtitle">
                Votre assistant IA interne Limagrain. Je réponds à vos questions à partir de la documentation de l'entreprise.
            </p>
            <div class="suggestion-grid">
                <div class="suggestion-card" onclick="Chat.sendSuggestion('Quelles sont les valeurs de Limagrain ?')">
                    <i data-lucide="lightbulb" class="card-icon lucide-icon"></i>
                    <div>
                        <div class="card-text">Valeurs de Limagrain</div>
                        <div class="card-hint">Audace, Coopération, Progrès...</div>
                    </div>
                </div>
                <div class="suggestion-card" onclick="Chat.sendSuggestion('Quelle est la stratégie Ambition 2030 ?')">
                    <i data-lucide="target" class="card-icon lucide-icon"></i>
                    <div>
                        <div class="card-text">Ambition 2030</div>
                        <div class="card-hint">Stratégie et axes prioritaires</div>
                    </div>
                </div>
                <div class="suggestion-card" onclick="Chat.sendSuggestion('Comment le Pôle Data & IA est-il organisé ?')">
                    <i data-lucide="brain-circuit" class="card-icon lucide-icon"></i>
                    <div>
                        <div class="card-text">Pôle Data & IA</div>
                        <div class="card-hint">Organisation DSI et projets IA</div>
                    </div>
                </div>
                <div class="suggestion-card" onclick="Chat.sendSuggestion('Quels sont les cas d\\'usage IA en production ?')">
                    <i data-lucide="zap" class="card-icon lucide-icon"></i>
                    <div>
                        <div class="card-text">Cas d'usage IA</div>
                        <div class="card-hint">Copilote agronomique, supply chain...</div>
                    </div>
                </div>
            </div>
        `;
        container.appendChild(welcome);
        if (window.lucide) window.lucide.createIcons({ root: welcome });

        App.showToast('Nouvelle conversation démarrée', 'info');
    }
};
