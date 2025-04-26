const API_URL = "https://i6dxtr.pythonanywhere.com";

class VisionApp {
    constructor() {
        this.video = document.getElementById('video');
        this.canvas = document.getElementById('canvas');
        this.captureButton = document.getElementById('capture');
        this.retakeButton = document.getElementById('retake');
        this.resultDiv = document.getElementById('result');
        this.cameraSelect = document.getElementById('camera-select');
        this.availableDevices = [];
        this.currentStream = null;

        // Setup initial states
        this.canvas.classList.remove('show');
        this.video.classList.add('show');
        this.retakeButton.style.display = 'none';

        this.setupEventListeners();
        this.initializeCamera();
        this.getCameraDevices();
    }

    async getCameraDevices() {
        try {
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
        this.cameraSelect.add(new Option('Rear Camera (Default)', 'environment'));
        this.cameraSelect.add(new Option('Front Camera', 'user'));

        this.availableDevices.forEach((device, index) => {
            const label = device.label || `Camera ${index + 1}`;
            this.cameraSelect.add(new Option(label, device.deviceId));
        });
    }

    async initializeCamera(deviceIdOrMode = 'environment') {
        if (this.currentStream) {
            this.currentStream.getTracks().forEach(track => track.stop());
        }

        this.video.classList.add('show');
        this.canvas.classList.remove('show');
        this.retakeButton.style.display = 'none';

        try {
            const constraints = {
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    ...(typeof deviceIdOrMode === 'string' &&
                        (deviceIdOrMode === 'user' || deviceIdOrMode === 'environment') ? {
                        facingMode: { exact: deviceIdOrMode }
                    } : {
                        deviceId: { exact: deviceIdOrMode }
                    })
                }
            };

            const stream = await navigator.mediaDevices.getUserMedia(constraints)
                .catch(async (err) => {
                    if (deviceIdOrMode === 'user' || deviceIdOrMode === 'environment') {
                        return navigator.mediaDevices.getUserMedia({ video: { facingMode: deviceIdOrMode } });
                    }
                    throw err;
                });

            this.video.srcObject = stream;
            this.currentStream = stream;

            await this.getCameraDevices();
        } catch (err) {
            console.error('Camera error:', err);
            this.resultDiv.textContent = 'Error: Camera access - ' + err.message;

            try {
                const fallbackStream = await navigator.mediaDevices.getUserMedia({ video: true });
                this.video.srcObject = fallbackStream;
                this.currentStream = fallbackStream;
                await this.getCameraDevices();
            } catch (fallbackErr) {
                console.error('Fallback camera error:', fallbackErr);
                this.resultDiv.textContent = 'Error: Could not access any camera';
            }
        }
    }

    async captureImage() {
        const displayWidth = this.video.clientWidth;
        const displayHeight = this.video.clientHeight;
    
        this.canvas.width = displayWidth;
        this.canvas.height = displayHeight;
    
        const ctx = this.canvas.getContext('2d');
        ctx.drawImage(this.video, 0, 0, displayWidth, displayHeight);
    
        this.video.classList.remove('show');
        this.canvas.classList.add('show');
    
        this.captureButton.style.display = 'none';
        this.retakeButton.style.display = 'inline-block';
    
        const spinner = document.getElementById('spinner');
        const resultText = document.getElementById('result-text');
    
        this.captureButton.disabled = true;
        this.retakeButton.disabled = true; // ✨ Disable retake while processing
        spinner.style.display = 'inline-block';
        resultText.textContent = 'Processing...';
    
        try {
            const blob = await new Promise((resolve) => {
                this.canvas.toBlob(resolve, 'image/jpeg', 0.8);
            });
    
            const formData = new FormData();
            formData.append('image', blob);
    
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
            this.retakeButton.disabled = false; // ✨ Re-enable retake after done
        }
    }
    

    retakeImage() {
        this.canvas.classList.remove('show');
        this.video.classList.add('show');

        this.captureButton.style.display = 'inline-block';
        this.retakeButton.style.display = 'none';

        const resultText = document.getElementById('result-text');
        resultText.textContent = 'Awaiting capture...';
    }

    setupEventListeners() {
        this.captureButton.addEventListener('click', () => this.captureImage());
        this.retakeButton.addEventListener('click', () => this.retakeImage());
        this.cameraSelect.addEventListener('change', () => {
            this.initializeCamera(this.cameraSelect.value);
        });
    }
}

window.addEventListener('load', () => {
    new VisionApp();
});
