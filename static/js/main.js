// app/static/js/main.js
class FaceGenerator {
    constructor() {
        if (this.isOnSingleFacePage()) {
            this.initializeEventListeners();
        }
    }

    isOnSingleFacePage() {
        return document.getElementById('generateForm') !== null;
    }

    initializeEventListeners() {
        // Truncation slider - check if element exists
        const truncationSlider = document.getElementById('truncationSlider');
        const truncationValue = document.getElementById('truncationValue');
        
        if (truncationSlider && truncationValue) {
            truncationSlider.addEventListener('input', (e) => {
                truncationValue.textContent = e.target.value;
            });
        }

        // Form submission - check if element exists
        const generateForm = document.getElementById('generateForm');
        if (generateForm) {
            generateForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.generateFace();
            });
        }

        // Download button - check if element exists
        const downloadBtn = document.getElementById('downloadBtn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => {
                this.downloadImage();
            });
        }

        // Close modal when clicking outside or on close button
        this.setupModalEvents();
    }

    setupModalEvents() {
        // Close modal when clicking outside the image
        document.addEventListener('click', (e) => {
            const modal = document.getElementById('imageModal');
            if (e.target === modal) {
                this.closeModal();
            }
        });

        // Close modal when pressing Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });
    }

    async generateFace() {
        const seedInput = document.getElementById('seedInput');
        const truncationSlider = document.getElementById('truncationSlider');
        const enhanceToggle = document.getElementById('enhanceToggle');
        
        const seed = seedInput.value ? parseInt(seedInput.value) : undefined;
        const truncation = parseFloat(truncationSlider.value);
        const enhance = enhanceToggle.checked;

        this.showLoadingState();

        try {
            const response = await fetch('/api/v1/generate/single', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    seed: seed,
                    truncation: truncation,
                    enhance_face: enhance
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Generation failed');
            }

            const result = await response.json();
            this.displayResult(result);
            
        } catch (error) {
            this.showError('Failed to generate face: ' + error.message);
            console.error('Generation error:', error);
        }
    }

    showLoadingState() {
        document.getElementById('emptyState').classList.add('hidden');
        document.getElementById('resultsState').classList.add('hidden');
        document.getElementById('loadingState').classList.remove('hidden');
        document.getElementById('downloadBtn').classList.add('hidden');
    }

    displayResult(result) {
        const image = document.getElementById('generatedImage');
        // Use the URL from the API response directly
        image.src = result.url + '?t=' + new Date().getTime(); // Cache bust
        
        // Add click event to image for preview
        image.onclick = () => this.openModal(result.url);
        
        document.getElementById('infoSeed').textContent = result.seed;
        document.getElementById('infoTruncation').textContent = result.truncation_psi;
        document.getElementById('infoEnhancement').textContent = result.enhancement;
        document.getElementById('infoTime').textContent = new Date(result.timestamp).toLocaleTimeString();

        // Store result for download
        this.currentResult = result;

        document.getElementById('loadingState').classList.add('hidden');
        document.getElementById('resultsState').classList.remove('hidden');
        document.getElementById('downloadBtn').classList.remove('hidden');
    }

    openModal(imageUrl) {
        // Create modal if it doesn't exist
        let modal = document.getElementById('imageModal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'imageModal';
            modal.className = 'fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center z-50 hidden';
            modal.innerHTML = `
                <div class="relative max-w-4xl max-h-full">
                    <button id="modalClose" class="absolute -top-12 right-0 text-white text-2xl hover:text-gray-300 transition-colors">
                        <i class="fas fa-times"></i>
                    </button>
                    <button id="modalDownload" class="absolute -top-12 right-12 text-white text-xl hover:text-gray-300 transition-colors" title="Download">
                        <i class="fas fa-download"></i>
                    </button>
                    <img id="modalImage" src="" alt="Preview" class="max-w-full max-h-screen object-contain">
                </div>
            `;
            document.body.appendChild(modal);

            // Add event listeners for modal buttons
            document.getElementById('modalClose').addEventListener('click', () => this.closeModal());
            document.getElementById('modalDownload').addEventListener('click', () => this.downloadFromModal());
        }

        // Set the image source and show modal
        document.getElementById('modalImage').src = imageUrl;
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden'; // Prevent scrolling
    }

    closeModal() {
        const modal = document.getElementById('imageModal');
        if (modal) {
            modal.classList.add('hidden');
            document.body.style.overflow = ''; // Restore scrolling
        }
    }

    downloadFromModal() {
        if (this.currentResult) {
            this.downloadImage();
        }
    }

    async downloadImage() {
        if (!this.currentResult) return;

        try {
            // Use the fast download endpoint that serves cached files
            const response = await fetch(`/api/v1/generate/single/download?seed=${this.currentResult.seed}`);
            
            if (!response.ok) {
                throw new Error('Download failed');
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `face_${this.currentResult.seed}.png`;
            
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            
            this.showSuccess(`Downloaded face_${this.currentResult.seed}.png`);
            
        } catch (error) {
            console.error('Download failed:', error);
            this.showError('Download failed. Please try again.');
        }
    }

    showError(message) {
        this.showNotification(message, 'red');
    }

    showSuccess(message) {
        this.showNotification(message, 'green');
    }

    showNotification(message, color = 'blue') {
        const colors = {
            green: 'bg-green-500 text-white',
            red: 'bg-red-500 text-white',
            blue: 'bg-blue-500 text-white'
        };

        // Remove existing notifications
        const existingNotifications = document.querySelectorAll('.notification-toast');
        existingNotifications.forEach(notif => notif.remove());

        const notification = document.createElement('div');
        notification.className = `notification-toast fixed top-4 right-4 ${colors[color]} px-6 py-3 rounded-lg shadow-lg z-50 transform transition-transform duration-300 translate-x-full`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 10);
        
        // Remove after 5 seconds
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 5000);
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    new FaceGenerator();
});