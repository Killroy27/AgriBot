/**
 * AgriBot API Client
 * Gestion centralisée des appels API vers le backend FastAPI.
 */

const API = {
    BASE_URL: 'http://localhost:8000',

    /**
     * Appel API générique
     */
    async request(endpoint, options = {}) {
        const url = `${this.BASE_URL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: response.statusText }));
                throw new Error(error.detail || `Erreur ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                throw new Error('Impossible de contacter le serveur. Vérifiez que le backend est lancé sur le port 8000.');
            }
            throw error;
        }
    },

    /**
     * Envoie un message au chatbot
     */
    async chat(message) {
        return this.request('/api/chat', {
            method: 'POST',
            body: JSON.stringify({ message }),
        });
    },

    /**
     * Upload un document
     */
    async uploadDocument(file) {
        const formData = new FormData();
        formData.append('file', file);

        const url = `${this.BASE_URL}/api/upload`;
        const response = await fetch(url, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(error.detail || `Erreur ${response.status}`);
        }

        return await response.json();
    },

    /**
     * Liste les documents indexés
     */
    async getDocuments() {
        return this.request('/api/documents');
    },

    /**
     * Supprime un document
     */
    async deleteDocument(sourceName) {
        return this.request(`/api/documents/${encodeURIComponent(sourceName)}`, {
            method: 'DELETE',
        });
    },

    /**
     * Statut du système
     */
    async getStatus() {
        return this.request('/api/status');
    },

    /**
     * Vérifie si le backend est accessible
     */
    async healthCheck() {
        try {
            await this.request('/api/status');
            return true;
        } catch {
            return false;
        }
    }
};
