// Global Toast Notification System
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return; // Fail gracefully if not in layout

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let icon = 'fa-circle-info';
    let title = 'Information';
    
    if (type === 'success') {
        icon = 'fa-circle-check'; title = 'Success';
    } else if (type === 'error') {
        icon = 'fa-triangle-exclamation'; title = 'Error';
    }

    toast.innerHTML = `
        <i class="fa-solid ${icon}"></i>
        <div class="toast-body">
            <h4>${title}</h4>
            <p>${message}</p>
        </div>
    `;

    container.appendChild(toast);

    // Auto remove after 4 seconds
    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.3s forwards';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

document.addEventListener('DOMContentLoaded', () => {
    
    // Scanner Upload Elements
    const uploadBox = document.getElementById('upload-box');
    const imageInput = document.getElementById('image-input');
    const browseBtn = document.getElementById('browse-btn');
    if(!uploadBox) return; // Exit if not on the scanner page
    
    const previewContainer = document.getElementById('preview-container');
    const imagePreview = document.getElementById('image-preview');
    const removeBtn = document.getElementById('remove-btn');
    const analyzeBtn = document.getElementById('analyze-btn');
    
    const loadingState = document.getElementById('loading-state');
    const resultContainer = document.getElementById('result-container');
    const resetBtn = document.getElementById('reset-btn');
    
    let currentFile = null;

    // Trigger file input
    browseBtn.addEventListener('click', () => {
        imageInput.click();
    });

    // Handle file selection
    imageInput.addEventListener('change', (e) => {
        if(e.target.files.length) {
            handleFile(e.target.files[0]);
        }
    });

    // Drag and Drop
    uploadBox.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadBox.classList.add('dragover');
    });

    uploadBox.addEventListener('dragleave', () => {
        uploadBox.classList.remove('dragover');
    });

    uploadBox.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadBox.classList.remove('dragover');
        if(e.dataTransfer.files.length) {
            handleFile(e.dataTransfer.files[0]);
            imageInput.files = e.dataTransfer.files; // update input
        }
    });

    function handleFile(file) {
        if(!file.type.startsWith('image/')) {
            showToast('Please upload a valid image file.', 'error');
            return;
        }
        currentFile = file;
        
        const reader = new FileReader();
        reader.onload = (e) => {
            imagePreview.src = e.target.result;
            uploadBox.classList.add('hidden');
            previewContainer.classList.remove('hidden');
            showToast('Retinal image loaded successfully.', 'success');
        };
        reader.readAsDataURL(file);
    }

    // Remove Image
    removeBtn.addEventListener('click', () => {
        currentFile = null;
        imageInput.value = '';
        previewContainer.classList.add('hidden');
        uploadBox.classList.remove('hidden');
    });

    // Analyze Image
    analyzeBtn.addEventListener('click', async () => {
        if(!currentFile) return;

        // UI State Switch
        previewContainer.classList.add('hidden');
        loadingState.classList.remove('hidden');
        document.getElementById('scanner-line').classList.add('hidden');

        try {
            const formData = new FormData();
            formData.append('file', currentFile);

            const res = await fetch('/api/predict', {
                method: 'POST',
                body: formData
            });

            const data = await res.json();
            
            if(data.success) {
                // Show the image again
                previewContainer.classList.remove('hidden');
                document.getElementById('remove-btn').parentElement.classList.add('hidden'); // Hide buttons
                
                // Render results
                document.getElementById('res-disease').textContent = data.diagnosis;
                
                // Set Tooltip Data based on Diagnosis
                const descriptionBox = document.getElementById('disease-description');
                let tooltipText = "Specific details are currently unavailable for this condition.";
                if (data.diagnosis.toLowerCase().includes('glaucoma')) {
                    tooltipText = "Glaucoma damages the optic nerve and requires immediate review to prevent vision loss.";
                } else if (data.diagnosis.toLowerCase().includes('diabetic')) {
                    tooltipText = "Damage to the retinal blood vessels caused by diabetes. Referral to an endocrinologist recommended.";
                } else if (data.diagnosis.toLowerCase().includes('cataract')) {
                    tooltipText = "Clouding of the eye lens has been detected. Consider scheduling an extraction surgery.";
                } else if (data.diagnosis.toLowerCase().includes('normal')) {
                    tooltipText = "Scan structural parameters fall within normal clinical baselines.";
                }
                if(descriptionBox) descriptionBox.textContent = tooltipText;

                const confidencePercent = (data.confidence * 100).toFixed(1);
                document.getElementById('res-confidence').textContent = `${confidencePercent}%`;
                
                // Animate progress bar
                setTimeout(() => {
                    document.getElementById('res-confidence-bar').style.width = `${confidencePercent}%`;
                }, 300);

                // Show AI Heatmap Simulation if disease detected
                if (!data.diagnosis.toLowerCase().includes('normal')) {
                    document.getElementById('heatmap-overlay').classList.remove('hidden');
                    showToast('Pathology signatures detected. Review Heatmap.', 'error');
                } else {
                    showToast('Analysis complete. Retina classified as Normal.', 'success');
                }

                // UI State Switch
                loadingState.classList.add('hidden');
                resultContainer.classList.remove('hidden');
            } else {
                showToast(`Server Error: ${data.error}`, 'error');
                resetUI();
            }

        } catch (err) {
            console.error(err);
            showToast('Network error while connecting to neural node. Please try again.', 'error');
            resetUI();
        }
    });

    // Reset Flow
    resetBtn.addEventListener('click', () => {
        resetUI();
    });

    function resetUI() {
        currentFile = null;
        imageInput.value = '';
        resultContainer.classList.add('hidden');
        loadingState.classList.add('hidden');
        previewContainer.classList.add('hidden');
        uploadBox.classList.remove('hidden');
        document.getElementById('remove-btn').parentElement.classList.remove('hidden');
        document.getElementById('res-confidence-bar').style.width = '0%';
        document.getElementById('heatmap-overlay').classList.add('hidden');
    }
});
