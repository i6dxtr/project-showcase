// docs/js/app.js
class VisionApp {
    constructor() {
        this.video = document.getElementById('video');
        this.captureButton = document.getElementById('capture');
        this.resultDiv = document.getElementById('result');
        
        this.setupCamera();
        this.setupEventListeners();
    }

    async setupCamera() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            this.video.srcObject = stream;
        } catch (err) {
            console.error('Error accessing camera:', err);
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
            const formData = new FormData();
            formData.append('image', blob);

            try {
                const response = await fetch('http://localhost:5000/predict', {
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