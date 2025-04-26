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
        this.initializeCamera(); // Start with default camera first
        this.getCameraDevices();
    }

    async getCameraDevices() {
        try {
            // We need to have active media stream before enumerateDevices will work properly
            if (!this.currentStream) {
                await this.initializeCamera();
            }
            
            const devices = await navigator.mediaDevices.enumerateDevices();
            this.availableDevices = devices.filter(device => device.kind === 'videoinput');
            
            this.populateCameraSelect();
        } catch (err) {
            console.error('Error enumerating devices:', err);
            this.resultDiv.textContent = 'Error: Could not access camera devices';
        }
    }

    populateCameraSelect() {
        this.cameraSelect.innerHTML = '';
        
        // Add option for front camera (user-facing)
        this.cameraSelect.add(new Option('Front Camera', 'user'));
        
        // Add option for rear camera (environment-facing)
        this.cameraSelect.add(new Option('Rear Camera', 'environment'));
        
        // Also add any specific devices we found
        this.availableDevices.forEach((device, index) => {
            this.cameraSelect.add(new Option(
                device.label || `Camera ${index + 1}`,
                device.deviceId
            ));
        });
    }

    async initializeCamera(deviceIdOrMode = 'user') {
        // Stop any existing stream
        if (this.currentStream) {
            this.currentStream.getTracks().forEach(track => track.stop());
        }
        
        try {
            const constraints = {
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                }
            };
            
            // Handle special cases for front/rear
            if (deviceIdOrMode === 'user' || deviceIdOrMode === 'environment') {
                constraints.video.facingMode = { exact: deviceIdOrMode };
            } else {
                constraints.video.deviceId = { exact: deviceIdOrMode };
            }
            
            const stream = await navigator.mediaDevices.getUserMedia(constraints);
            this.video.srcObject = stream;
            this.currentStream = stream;
            
            // Refresh device list now that we have permission
            if (this.availableDevices.length === 0) {
                this.getCameraDevices();
            }
        } catch (err) {
            console.error('Camera error:', err);
            this.resultDiv.textContent = 'Error: Camera access - ' + err.message;
            
            // Try fallback to basic video if specific mode fails
            if (deviceIdOrMode === 'user' || deviceIdOrMode === 'environment') {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                    this.video.srcObject = stream;
                    this.currentStream = stream;
                } catch (fallbackErr) {
                    console.error('Fallback camera error:', fallbackErr);
                }
            }
        }
    }

    async captureImage() {
        const canvas = document.createElement('canvas');
        canvas.width = this.video.videoWidth;
        canvas.height = this.video.videoHeight;
        canvas.getContext('2d').drawImage(this.video, 0, 0);

        const spinner = document.getElementById('spinner');
        const resultText = document.getElementById('result-text');

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
                spinner.style.display = 'none';
                this.captureButton.disabled = false;
            }
        }, 'image/jpeg');
    }

    setupEventListeners() {
        this.captureButton.addEventListener('click', () => this.captureImage());
        this.cameraSelect.addEventListener('change', () => {
            this.initializeCamera(this.cameraSelect.value);
        });
    }
}

window.addEventListener('load', () => {
    new VisionApp();
});