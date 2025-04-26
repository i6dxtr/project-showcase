// docs/js/app.js

const API_URL = "https://i6dxtr.pythonanywhere.com"; // do not change this

class VisionApp {
    constructor() {
        this.video = document.getElementById('video');
        this.captureButton = document.getElementById('capture');
        this.resultDiv = document.getElementById('result');
        
        this.initializeCamera();
        this.setupEventListeners();
    }

    async initializeCamera() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            this.video.srcObject = stream;
        } catch (err) {
            console.error('Camera error:', err);
            this.resultDiv.textContent = 'Error: Camera access denied';
        }
    }


    async captureImage() {
        const canvas = document.createElement('canvas');
        canvas.width = this.video.videoWidth;
        canvas.height = this.video.videoHeight;
        canvas.getContext('2d').drawImage(this.video, 0, 0);
    
        const captureButton = document.getElementById('capture');
        const spinner = document.getElementById('spinner');
        const resultText = document.getElementById('result-text');
    
        // Show spinner and disable button
        captureButton.disabled = true;
        spinner.style.display = 'inline-block';
        resultText.textContent = 'Processing...';
    
        canvas.toBlob(async (blob) => {
            const formData = new FormData();
            formData.append('image', blob);
    
            try {
                const response = await fetch(`${API_URL}/predict`, {
                    method: 'POST',
                    body: formData
                });
    
                const data = await response.json();
                resultText.textContent = `Predicted: ${data.prediction}`;
            } catch (error) {
                console.error('Error:', error);
                resultText.textContent = 'Error: Could not connect to server';
            } finally {
                // Always hide spinner and enable button
                spinner.style.display = 'none';
                captureButton.disabled = false;
            }
        }, 'image/jpeg');
    }
    

    setupEventListeners() {
        this.captureButton.addEventListener('click', () => this.captureImage());
    }

}

window.addEventListener('load', () => {
    new VisionApp();
});