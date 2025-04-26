const API_URL = "https://i6dxtr.pythonanywhere.com";

class VisionApp {
    constructor() {
        this.video = document.getElementById('video');
        this.captureButton = document.getElementById('capture');
        this.resultDiv = document.getElementById('result');
        this.cameraSelect = document.getElementById('camera-select');
        this.availableDevices = [];
        this.currentStream = null;
        
        this.setupEventListeners();
        this.getCameraDevices();
    }

    async getCameraDevices() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            this.availableDevices = devices.filter(device => device.kind === 'videoinput');
            
            this.cameraSelect.innerHTML = '<option value="">Select Camera...</option>';
            this.availableDevices.forEach((device, index) => {
                this.cameraSelect.innerHTML += `
                    <option value="${device.deviceId}">${device.label || `Camera ${index + 1}`}</option>
                `;
            });
            
            // If only one camera is available, select it automatically
            if (this.availableDevices.length === 1) {
                this.cameraSelect.value = this.availableDevices[0].deviceId;
                this.initializeCamera(this.availableDevices[0].deviceId);
            }
        } catch (err) {
            console.error('Error enumerating devices:', err);
            this.resultDiv.textContent = 'Error: Could not access camera devices';
        }
    }

    async initializeCamera(deviceId) {
        // Stop any existing stream
        if (this.currentStream) {
            this.currentStream.getTracks().forEach(track => track.stop());
        }
        
        try {
            const constraints = {
                video: {
                    deviceId: deviceId ? { exact: deviceId } : undefined,
                    facingMode: deviceId ? undefined : 'user' // Default to front camera if no deviceId
                }
            };
            
            const stream = await navigator.mediaDevices.getUserMedia(constraints);
            this.video.srcObject = stream;
            this.currentStream = stream;
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

        // Get references to the elements
        const spinner = document.getElementById('spinner');
        const resultText = document.getElementById('result-text');

        // Show spinner and disable button
        this.captureButton.disabled = true;
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
                this.captureButton.disabled = false;
            }
        }, 'image/jpeg');
    }

    setupEventListeners() {
        this.captureButton.addEventListener('click', () => this.captureImage());
        this.cameraSelect.addEventListener('change', () => {
            if (this.cameraSelect.value) {
                this.initializeCamera(this.cameraSelect.value);
            }
        });
    }
}

window.addEventListener('load', () => {
    new VisionApp();
});