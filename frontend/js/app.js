/**
 * AgriBot App — Main Application
 * Initialisation, thème, sidebar, chargement des données.
 */

const App = {
    /**
     * Initialisation de l'application
     */
    init() {
        // Charger le thème sauvegardé
        const savedTheme = localStorage.getItem('agribot-theme') || 'light';
        this.setTheme(savedTheme);

        // Initialiser l'upload drag & drop
        Upload.init();

        // Charger les données
        this.loadDocuments();
        this.loadStatus();

        // Vérifier la connectivité backend
        this.checkBackend();

        // Focus sur l'input
        document.getElementById('messageInput').focus();

        // Initialiser les icônes Lucide
        if (window.lucide) {
            window.lucide.createIcons();
        }

        console.log('🌾 AgriBot initialisé');
    },

    /**
     * Change le thème (light/dark)
     */
    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('agribot-theme', theme);

        // Mettre à jour les boutons
        document.getElementById('lightBtn').classList.toggle('active', theme === 'light');
        document.getElementById('darkBtn').classList.toggle('active', theme === 'dark');
    },

    /**
     * Toggle sidebar (mobile)
     */
    toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        const backdrop = document.getElementById('sidebarBackdrop');

        sidebar.classList.toggle('open');
        backdrop.classList.toggle('active');

        backdrop.onclick = () => {
            sidebar.classList.remove('open');
            backdrop.classList.remove('active');
        };
    },

    /**
     * Charger la liste des documents
     */
    async loadDocuments() {
        const docList = document.getElementById('docList');

        try {
            const data = await API.getDocuments();

            if (!data.documents || data.documents.length === 0) {
                docList.innerHTML = `
                    <div class="doc-item" style="justify-content: center; color: var(--text-tertiary); font-size: var(--text-sm);">
                        Aucun document indexé
                    </div>
                `;
                return;
            }

            docList.innerHTML = data.documents.map(doc => {
                const ext = doc.filename.split('.').pop().toLowerCase();
                const iconClass = ['pdf', 'md', 'docx', 'txt'].includes(ext) ? ext : 'txt';
                const icons = { pdf: 'file-text', md: 'file-code', docx: 'file-check-2', txt: 'file' };
                const iconName = icons[ext] || 'file';

                return `
                    <div class="doc-item">
                        <div class="doc-icon ${iconClass}">
                            <i data-lucide="${iconName}" class="lucide-icon-sm"></i>
                        </div>
                        <div class="doc-details">
                            <div class="doc-name">${doc.filename}</div>
                            <div class="doc-meta">${doc.chunks_count} chunks</div>
                        </div>
                        <button class="doc-delete" onclick="App.deleteDocument('${doc.filename}')" title="Supprimer">
                            <i data-lucide="trash-2" class="lucide-icon-sm"></i>
                        </button>
                    </div>
                `;
            }).join('');

            // Mettre à jour les stats
            document.getElementById('statDocs').textContent = data.documents_count;
            document.getElementById('statChunks').textContent = data.total_chunks;
            
            // Render new icons
            if (window.lucide) window.lucide.createIcons();

        } catch (error) {
            docList.innerHTML = `
                <div class="doc-item" style="justify-content: center; color: var(--text-tertiary); font-size: var(--text-sm);">
                    ⚠️ Erreur de chargement
                </div>
            `;
        }
    },

    /**
     * Charger le statut du système
     */
    async loadStatus() {
        try {
            const status = await API.getStatus();
            document.getElementById('statModel').textContent = status.model || '-';

            const badge = document.getElementById('statusBadge');
            badge.innerHTML = `<span class="status-dot"></span><span>En ligne</span>`;
            badge.style.color = 'var(--success)';
        } catch {
            const badge = document.getElementById('statusBadge');
            badge.innerHTML = `<span class="status-dot" style="background: var(--error);"></span><span>Hors ligne</span>`;
            badge.style.color = 'var(--error)';
        }
    },

    /**
     * Supprimer un document
     */
    async deleteDocument(filename) {
        if (!confirm(`Supprimer "${filename}" de l'index ?`)) return;

        try {
            await API.deleteDocument(filename);
            this.showToast(`Document "${filename}" supprimé`, 'success');
            this.loadDocuments();
        } catch (error) {
            this.showToast(`Erreur: ${error.message}`, 'error');
        }
    },

    /**
     * Vérifie le backend
     */
    async checkBackend() {
        const online = await API.healthCheck();

        if (!online) {
            const badge = document.getElementById('statusBadge');
            badge.innerHTML = `<span class="status-dot" style="background: var(--warning); animation: none;"></span><span>Backend arrêté</span>`;
            badge.style.color = 'var(--warning)';

            this.showToast('⚠️ Le backend n\'est pas lancé. Exécutez: python app.py', 'error');
        }
    },

    /**
     * Affiche un toast de notification
     */
    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const icons = { success: 'check-circle-2', error: 'alert-circle', info: 'info' };
        const iconName = icons[type] || 'info';

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <span class="toast-icon">
                <i data-lucide="${iconName}" class="lucide-icon-sm"></i>
            </span>
            <span class="toast-text">${message}</span>
        `;

        container.appendChild(toast);
        
        // Render icon
        if (window.lucide) window.lucide.createIcons({ root: toast });

        // Auto-remove après 4 secondes
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(50px)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }
};

// === Lancement ===
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
