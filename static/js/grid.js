// app/static/js/grid.js
class GridGenerator {
    constructor() {
        // Check if we're on the grid page before initializing
        if (this.isOnGridPage()) {
            this.initializeEventListeners();
            this.updateTotalFaces();
            this.updateResolutionGrid();
        }
    }

    isOnGridPage() {
        return document.getElementById('gridForm') !== null;
    }

    initializeEventListeners() {
        // Grid size changes
        const rowsSelect = document.getElementById('rowsSelect');
        const colsSelect = document.getElementById('colsSelect');
        
        if (rowsSelect && colsSelect) {
            rowsSelect.addEventListener('change', () => this.updateTotalFaces());
            colsSelect.addEventListener('change', () => this.updateTotalFaces());

            rowsSelect.addEventListener('change', () => this.updateResolutionGrid());
            colsSelect.addEventListener('change', () => this.updateResolutionGrid());
        }
        
        // Truncation slider - check if element exists
        const truncationSlider = document.getElementById('gridTruncationSlider');
        const truncationValue = document.getElementById('gridTruncationValue');
        
        if (truncationSlider && truncationValue) {
            truncationSlider.addEventListener('input', (e) => {
                truncationValue.textContent = e.target.value;
            });
        }

        // Form submission
        const gridForm = document.getElementById('gridForm');
        if (gridForm) {
            gridForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.generateGrid();
            });
        }

        // Download button
        const downloadBtn = document.getElementById('downloadGridBtn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => {
                this.downloadAllImages();
            });
        }
    }

    updateTotalFaces() {
        const rows = parseInt(document.getElementById('rowsSelect').value);
        const cols = parseInt(document.getElementById('colsSelect').value);
        document.getElementById('totalFaces').textContent = rows * cols;
    }

    updateResolutionGrid() {
        const rows = parseInt(document.getElementById('rowsSelect').value);
        const cols = parseInt(document.getElementById('colsSelect').value);
        
        // Calculate grid dimensions
        const faceResolution = 1024;
        const totalWidth = faceResolution * (cols + 1);
        const totalHeight = faceResolution * (rows + 1);
        
        // Update the resolution display
        document.getElementById('gridResolution').textContent = `${totalWidth}×${totalHeight}`;
    }

    async generateGrid() {
        const rows = parseInt(document.getElementById('rowsSelect').value);
        const cols = parseInt(document.getElementById('colsSelect').value);
        const truncation = parseFloat(document.getElementById('gridTruncationSlider').value);
        const enhance = document.getElementById('gridEnhanceToggle').checked;

        // Generate random seeds for rows and columns
        const rowSeeds = Array.from({length: rows}, () => Math.floor(Math.random() * 10000) + 1);
        const colSeeds = Array.from({length: cols}, () => Math.floor(Math.random() * 10000) + 10000);

        this.showGridLoadingState();

        const startTime = Date.now();

        try {
            // Use POST method with proper error handling
            const response = await fetch('/api/v1/generate/style-mix', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    row_seeds: rowSeeds,
                    col_seeds: colSeeds,
                    truncation: truncation
                })
            });
            
            if (!response.ok) {
                let errorMessage = 'Grid generation failed';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorMessage;
                } catch (parseError) {
                    errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                }
                throw new Error(errorMessage);
            }

            const result = await response.json();
            const endTime = Date.now();
            const generationTime = ((endTime - startTime) / 1000).toFixed(1);
            
            this.displayGridResult(result, generationTime, rowSeeds, colSeeds);
            
        } catch (error) {
            console.error('Grid generation error details:', error);
            this.showError('Failed to generate grid: ' + error.message);
        }
    }

    showGridLoadingState() {
        document.getElementById('gridEmptyState').classList.add('hidden');
        document.getElementById('gridResults').classList.add('hidden');
        document.getElementById('gridLoadingState').classList.remove('hidden');
        document.getElementById('downloadGridBtn').classList.add('hidden');
        document.getElementById('gridInfo').classList.add('hidden');

        this.hideError();
    }

    showError(message) {
        this.hideError();
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4';
        errorDiv.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-exclamation-triangle mr-2"></i>
                <span>${message}</span>
            </div>
        `;
        errorDiv.id = 'grid-error-message';
        
        const gridContainer = document.getElementById('gridResults').parentNode;
        gridContainer.insertBefore(errorDiv, document.getElementById('gridResults'));
    }

    hideError() {
        const existingError = document.getElementById('grid-error-message');
        if (existingError) {
            existingError.remove();
        }
    }

    displayGridResult(result, generationTime, rowSeeds, colSeeds) {
        const gridContainer = document.getElementById('facesGrid');
        gridContainer.innerHTML = '';

        // Create a grid layout based on rows and columns
        const rows = rowSeeds.length;
        const cols = colSeeds.length;
        
        // For simplicity, we'll display the single grid image
        const gridItem = document.createElement('div');
        gridItem.className = 'col-span-full flex justify-center';
        gridItem.innerHTML = `
            <div class="max-w-4xl">
                <img src="${result.url}?t=${new Date().getTime()}" 
                    alt="Generated face grid"
                    class="w-full h-auto rounded-lg shadow-lg">
                <div class="mt-4 text-center text-sm text-gray-600">
                    Grid: ${rows}×${cols} | Seeds: Rows [${rowSeeds.join(', ')}] × Cols [${colSeeds.join(', ')}]
                </div>
            </div>
        `;
        gridContainer.appendChild(gridItem);

        // Update info
        document.getElementById('generatedCount').textContent = rows * cols;
        document.getElementById('generationTime').textContent = generationTime;

        // Store results for download
        this.currentGridResult = result;
        this.rowSeeds = rowSeeds;
        this.colSeeds = colSeeds;

        document.getElementById('gridLoadingState').classList.add('hidden');
        document.getElementById('gridResults').classList.remove('hidden');
        document.getElementById('downloadGridBtn').classList.remove('hidden');
        document.getElementById('gridInfo').classList.remove('hidden');
    }
    
    async downloadAllImages() {
        if (!this.currentGridResult) return;

        this.showLoading('Preparing download...');

        try {
            // Use the cached grid image URL directly
            const response = await fetch(this.currentGridResult.url);
            
            if (!response.ok) {
                throw new Error('Download failed');
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `face_grid_${new Date().getTime()}.png`;
            
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            
            this.showSuccess('Downloaded grid image');
            
        } catch (error) {
            console.error('Download failed:', error);
            this.showError('Download failed. Please try again.');
        } finally {
            this.hideLoading();
        }
    }

    showLoading(message = 'Loading...') {
        this.hideLoading();
        
        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'global-loading';
        loadingDiv.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        loadingDiv.innerHTML = `
            <div class="bg-white rounded-lg p-6 flex items-center space-x-3">
                <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                <span class="text-gray-700">${message}</span>
            </div>
        `;
        
        document.body.appendChild(loadingDiv);
    }

    hideLoading() {
        const existingLoading = document.getElementById('global-loading');
        if (existingLoading) {
            existingLoading.remove();
        }
    }

    showSuccess(message) {
        this.showNotification(message, 'green');
    }

    showError(message) {
        this.showNotification(message, 'red');
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

// Initialize grid generator
document.addEventListener('DOMContentLoaded', () => {
    new GridGenerator();
});