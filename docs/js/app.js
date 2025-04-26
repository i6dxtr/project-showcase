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
        this.initializeCamera(); // Start with rear camera first
        this.getCameraDevices();
    }

    async getCameraDevices() {
        try {
            // First ensure we have camera permissions by getting a stream
            if (!this.currentStream) {
                await this.initializeCamera();
            }
            
            // Now enumerate devices
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
        
        // Changed order and labels to prioritize rear camera
        this.cameraSelect.add(new Option('Rear Camera (Default)', 'environment'));
        this.cameraSelect.add(new Option('Front Camera', 'user'));
        
        // Add specific devices if available
        this.availableDevices.forEach((device, index) => {
            // In Safari, device labels are often blank until used
            const label = device.label || `Camera ${index + 1}`;
            this.cameraSelect.add(new Option(label, device.deviceId));
        });
    }
    
    async initializeCamera(deviceIdOrMode = 'environment') {
        // Stop any existing stream
        if (this.currentStream) {
            this.currentStream.getTracks().forEach(track => track.stop());
        }
        
        // Make sure video is visible and canvas is hidden
        this.video.style.display = 'block';
        document.getElementById('canvas').style.display = 'none';
        
        try {
            const constraints = {
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    // For iOS Safari, we need to be more specific
                    ...(typeof deviceIdOrMode === 'string' && 
                        (deviceIdOrMode === 'user' || deviceIdOrMode === 'environment') ? {
                        facingMode: { exact: deviceIdOrMode }
                    } : {
                        deviceId: { exact: deviceIdOrMode }
                    })
                }
            };
    
            // For iOS, we might need to try different approaches
            const stream = await navigator.mediaDevices.getUserMedia(constraints)
                .catch(async (err) => {
                    // Fallback to more generic constraints if specific mode fails
                    if (deviceIdOrMode === 'user' || deviceIdOrMode === 'environment') {
                        return navigator.mediaDevices.getUserMedia({
                            video: {
                                facingMode: deviceIdOrMode
                            }
                        });
                    }
                    throw err;
                });
    
            this.video.srcObject = stream;
            this.currentStream = stream;
            
            // Refresh device list now that we have permission
            await this.getCameraDevices();
        } catch (err) {
            console.error('Camera error:', err);
            this.resultDiv.textContent = 'Error: Camera access - ' + err.message;
            
            // Try complete fallback
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                this.video.srcObject = stream;
                this.currentStream = stream;
                await this.getCameraDevices();
            } catch (fallbackErr) {
                console.error('Fallback camera error:', fallbackErr);
                this.resultDiv.textContent = 'Error: Could not access any camera';
                
                // Ensure UI is in correct state
                this.video.style.display = 'block';
                document.getElementById('canvas').style.display = 'none';
            }
        }
    }

    async captureImage() {
        const video = this.video;
        const canvas = document.getElementById('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0);
    
        // Show canvas (paused image) and hide video
        canvas.style.display = 'block';
        video.style.display = 'none';
    
        const spinner = document.getElementById('spinner');
        const resultText = document.getElementById('result-text');
    
        this.captureButton.disabled = true;
        spinner.style.display = 'inline-block';
        resultText.textContent = 'Processing...';
    
        try {
            const blob = await new Promise((resolve) => {
                canvas.toBlob(resolve, 'image/jpeg');
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
            
            // Hide canvas and show video again
            canvas.style.display = 'none';
            video.style.display = 'block';
        }
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