document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('file');
    const uploadArea = document.querySelector('.file-upload-area');
    const uploadButton = document.querySelector('button[type="submit"]');
    
    // File selection feedback
    fileInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            const filename = this.files[0].name;
            uploadArea.style.backgroundColor = '#e8f5e8';
            uploadArea.querySelector('.file-upload-hint p').textContent = `📁 Selected: ${filename}`;
            uploadButton.textContent = `📤 Upload and Process "${filename}"`;
        }
    });
    
    // Form submission feedback
    document.querySelector('.upload-form').addEventListener('submit', function() {
        uploadButton.innerHTML = '<div class="loading">🔄 Processing...</div>';
        uploadButton.disabled = true;
    });
    
    // Drag and drop functionality
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        this.style.backgroundColor = '#f0f8ff';
        this.style.borderColor = '#007bff';
    });
    
    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        this.style.backgroundColor = '';
        this.style.borderColor = '';
    });
    
    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        this.style.backgroundColor = '';
        this.style.borderColor = '';
        
        const files = e.dataTransfer.files;
        if (files.length > 0 && files[0].name.toLowerCase().endsWith('.gpx')) {
            fileInput.files = files;
            fileInput.dispatchEvent(new Event('change'));
        }
    });
});