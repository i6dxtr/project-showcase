const API_URL = "https://i6dxtr.pythonanywhere.com";

class VisionApp {
  constructor() {
    this.video = document.getElementById('video');
    this.canvas = document.getElementById('canvas');
    this.captureButton = document.getElementById('capture');
    this.retakeButton = document.getElementById('retake');
    this.resultDiv = document.getElementById('result');
    this.cameraSelect = document.getElementById('camera-select');
    this.currentStream = null;

    this.setupEventListeners();
    // 1) Prompt for camera permission (default)
    // 2) List devices, choose rear cam on mobile, then re-open that stream
    this.initializeCamera()
      .then(() => this.getCameraDevices())
      .then(() => {
        // simple mobile check
        const isMobile = /Mobi|Android/i.test(navigator.userAgent);
        const defaultCam = isMobile ? 'environment' : 'default';
        this.cameraSelect.value = defaultCam;
        return this.initializeCamera(defaultCam);
      });
  }

  async getCameraDevices() {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const videoInputs = devices.filter(d => d.kind === 'videoinput');
      this.populateCameraSelect(videoInputs);
    } catch (err) {
      console.error('Error enumerating devices:', err);
      this.resultDiv.textContent = 'Error: Could not list camera devices';
    }
  }

  populateCameraSelect(videoInputs) {
    this.cameraSelect.innerHTML = '';
    this.cameraSelect.add(new Option('Default camera', 'default'));
    this.cameraSelect.add(new Option('Front (selfie)', 'user'));
    this.cameraSelect.add(new Option('Rear', 'environment'));
    videoInputs.forEach((device, idx) => {
      const label = device.label || `Camera ${idx + 1}`;
      this.cameraSelect.add(new Option(label, device.deviceId));
    });
  }

  async initializeCamera(selection = 'default') {
    // Stop any old stream
    if (this.currentStream) {
      this.currentStream.getTracks().forEach(t => t.stop());
      this.currentStream = null;
    }

    // Reset UI
    this.video.classList.add('show');
    this.canvas.classList.remove('show');
    this.captureButton.style.display = 'inline-block';
    this.retakeButton.style.display = 'none';

    // Build constraints
    let videoConstraint;
    if (selection === 'default') {
      videoConstraint = { width: { ideal: 1280 }, height: { ideal: 720 } };
    } else if (selection === 'user' || selection === 'environment') {
      videoConstraint = {
        width: { ideal: 1280 },
        height: { ideal: 720 },
        facingMode: { exact: selection }
      };
    } else {
      videoConstraint = {
        width: { ideal: 1280 },
        height: { ideal: 720 },
        deviceId: { exact: selection }
      };
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: videoConstraint });
      this.video.srcObject = stream;
      this.currentStream = stream;
    } catch (err) {
      console.warn('Requested constraints failed, falling back to default:', err);
      try {
        const fallback = await navigator.mediaDevices.getUserMedia({ video: true });
        this.video.srcObject = fallback;
        this.currentStream = fallback;
      } catch (fbErr) {
        console.error('Fallback also failed:', fbErr);
        this.resultDiv.textContent = 'Error: Cannot access camera';
      }
    }
  }

  async captureImage() {
    // size canvas to display size
    this.canvas.width = this.video.clientWidth;
    this.canvas.height = this.video.clientHeight;
    this.canvas.getContext('2d').drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);

    this.video.classList.remove('show');
    this.canvas.classList.add('show');
    this.captureButton.style.display = 'none';
    this.retakeButton.style.display = 'inline-block';

    const spinner = document.getElementById('spinner');
    const resultText = document.getElementById('result-text');
    spinner.style.display = 'inline-block';
    resultText.textContent = 'Processing...';
    this.captureButton.disabled = true;

    try {
      const blob = await new Promise(res => this.canvas.toBlob(res, 'image/jpeg', 0.8));
      const formData = new FormData();
      formData.append('image', blob);
      const resp = await fetch(`${API_URL}/predict`, { method: 'POST', body: formData });
      const data = await resp.json();
      resultText.textContent = `Predicted: ${data.prediction}`;
    } catch (err) {
      console.error(err);
      resultText.textContent = 'Error: Could not connect to server';
    } finally {
      spinner.style.display = 'none';
      this.captureButton.disabled = false;
    }
  }

  retakeImage() {
    this.canvas.classList.remove('show');
    this.video.classList.add('show');
    this.captureButton.style.display = 'inline-block';
    this.retakeButton.style.display = 'none';
    document.getElementById('result-text').textContent = 'Awaiting capture...';
  }

  setupEventListeners() {
    this.captureButton.addEventListener('click', () => this.captureImage());
    this.retakeButton.addEventListener('click', () => this.retakeImage());
    this.cameraSelect.addEventListener('change', () => {
      this.initializeCamera(this.cameraSelect.value);
    });
  }
}

window.addEventListener('load', () => new VisionApp());
