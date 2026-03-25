/**
 * AgriBot Upload Module
 * Gestion de l'upload de documents avec drag & drop et progression.
 */

const Upload = {
    /**
     * Ouvre le modal d'upload
     */
    openModal() {
        document.getElementById('uploadModal').classList.add('active');
    },

    /**
     * Ferme le modal d'upload
     */
    closeModal() {
        document.getElementById('uploadModal').classList.remove('active');
        document.getElementById('uploadProgress').innerHTML = '';
        document.getElementById('uploadProgress').classList.remove('active');
    },

    /**
     * Initialise le drag & drop
     */
    init() {
        const dropZone = document.getElementById('dropZone');

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('drag-over');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.uploadFile(files[0]);
            }
        });

        // Cliquer sur le modal overlay (en dehors) pour fermer
        document.getElementById('uploadModal').addEventListener('click', (e) => {
            if (e.target === document.getElementById('uploadModal')) {
                this.closeModal();
            }
        });
    },

    /**
     * Gère la sélection de fichier via input
     */
    handleFile(event) {
        const file = event.target.files[0];
        if (file) {
            this.uploadFile(file);
        }
        event.target.value = ''; // reset
    },

    /**
     * Upload un fichier vers le backend
     */
    async uploadFile(file) {
        const progressContainer = document.getElementById('uploadProgress');
        progressContainer.classList.add('active');

        // Déterminer l'icône du fichier
        const ext = file.name.split('.').pop().toLowerCase();
        const icons = { pdf: 'file-text', docx: 'file-check-2', md: 'file-code', txt: 'file' };
        const iconName = icons[ext] || 'file';

        // Créer l'élément de progression
        const progressItem = document.createElement('div');
        progressItem.className = 'progress-item';
        progressItem.innerHTML = `
            <span class="progress-icon">
                <i data-lucide="${iconName}" class="lucide-icon-sm"></i>
            </span>
            <div class="progress-info">
                <div class="progress-name">${file.name}</div>
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
            </div>
            <span class="progress-status" id="progressStatus">Envoi...</span>
        `;
        progressContainer.innerHTML = '';
        progressContainer.appendChild(progressItem);
        
        if (window.lucide) window.lucide.createIcons({ root: progressItem });

        // Simuler la progression
        const fill = document.getElementById('progressFill');
        const status = document.getElementById('progressStatus');

        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress > 85) progress = 85;
            fill.style.width = `${progress}%`;
        }, 200);

        try {
            status.innerHTML = `<i data-lucide="loader-2" class="lucide-icon-xs spin" style="vertical-align: middle;"></i> Indexation...`;
            if (window.lucide) window.lucide.createIcons({ root: status });
            
            const response = await API.uploadDocument(file);

            clearInterval(interval);
            fill.style.width = '100%';
            status.innerHTML = `<i data-lucide="check-circle-2" class="lucide-icon-xs" style="vertical-align: middle;"></i> ${response.chunks_created} chunks`;
            if (window.lucide) window.lucide.createIcons({ root: status });
            status.className = 'progress-status success';

            App.showToast(response.message || `Document indexé (${response.chunks_created} chunks)`, 'success');

            // Rafraîchir la liste des documents
            App.loadDocuments();

        } catch (error) {
            clearInterval(interval);
            fill.style.width = '100%';
            fill.style.background = 'var(--error)';
            status.textContent = 'Erreur';
            status.className = 'progress-status error';

            App.showToast(`Erreur: ${error.message}`, 'error');
        }
    }
};
