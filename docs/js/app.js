// docs/js/app.js

const API_URL = "https://i6dxtr.pythonanywhere.com"; // do not change this

class VisionApp {
    constructor() {
        this.video = document.getElementById('video');
        this.captureButton = document.getElementById('capture');
        this.resultDiv = document.getElementById('result');
        
        this.setupCamera();
        this.setupEventListeners();
    }

    async captureImage() {
        this.resultDiv.textContent = 'Processing...';
        
        try {
            const canvas = document.createElement('canvas');
            canvas.width = this.video.videoWidth;
            canvas.height = this.video.videoHeight;
            canvas.getContext('2d').drawImage(this.video, 0, 0);
    
            // img size reduction
            const scaledCanvas = document.createElement('canvas');
            scaledCanvas.width = 224;  // matches model input size
            scaledCanvas.height = 224;
            scaledCanvas.getContext('2d').drawImage(canvas, 0, 0, 224, 224);
    
            scaledCanvas.toBlob(async (blob) => {
                const formData = new FormData();
                formData.append('image', blob, 'webcam.jpg');
    
                try {
                    // timeout
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), 25000); // 25 second timeout
    
                    const response = await fetch('https://i6dxtr.pythonanywhere.com/predict', {
                        method: 'POST',
                        body: formData,
                        signal: controller.signal
                    });
                    
                    clearTimeout(timeoutId);
    
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    
                    const data = await response.json();
                    this.resultDiv.textContent = `Predicted: ${data.prediction}`;
                } catch (error) {
                    console.error('Error:', error);
                    if (error.name === 'AbortError') {
                        this.resultDiv.textContent = 'Request timed out';
                    } else {
                        this.resultDiv.textContent = `Error: ${error.message}`;
                    }
                }
            }, 'image/jpeg', 0.8);
        } catch (error) {
            console.error('Capture error:', error);
            this.resultDiv.textContent = 'Error capturing image';
        }
    }

    setupEventListeners() {
        this.captureButton.addEventListener('click', () => this.captureImage());
    }

    async captureImage() {
        const canvas = document.createElement('canvas');
        canvas.width = this.video.videoWidth;
        canvas.height = this.video.videoHeight;
        canvas.getContext('2d').drawImage(this.video, 0, 0);

        canvas.toBlob(async (blob) => {
            const formData = new FormData();  // proper scope
            formData.append('image', blob);

            try {
                const response = await fetch(`${API_URL}/predict`, {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                this.resultDiv.textContent = `Predicted: ${data.prediction}`;
            } catch (error) {
                console.error('Error:', error);
                this.resultDiv.textContent = 'Error: Could not connect to server';
            }
        }, 'image/jpeg');
    }
}

window.addEventListener('load', () => {
    new VisionApp();
});