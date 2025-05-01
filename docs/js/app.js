/* app.js - Corrected Version */
const API_URL = "https://cd4d-75-187-72-180.ngrok-free.app";

class VisionApp {
  constructor() {
    this.video          = document.getElementById('video');
    this.canvas         = document.getElementById('canvas');
    this.captureButton  = document.getElementById('capture');
    this.retakeButton   = document.getElementById('retake');
    this.resultDiv      = document.getElementById('result');
    this.cameraSelect   = document.getElementById('camera-select');
    this.querySection   = document.getElementById('query-section');
    this.captureSection = document.getElementById('capture-section');
    this.productNameEl  = document.getElementById('product-name');
    this.queryResult    = document.getElementById('query-result');
    this.currentStream  = null;

    // Product mapping - Define it here so it's available throughout the class
    this.product_mapping = {
      'product-a': 'Kroger Creamy Peanut Butter',
      'product-b': 'Great Value Twist and Shout Cookies',
      'product-c': 'Morton Coarse Kosher Salt',
      'product-d': 'Kroger Extra Virgin Olive Oil',
      // Add more mappings as needed
    };

    this.setupEventListeners();

    // Prompt, list cameras and default to rear on mobile
    this.initializeCamera()
      .then(() => this.getCameraDevices())
      .then(() => {
        const isMobile   = /Mobi|Android/i.test(navigator.userAgent);
        const defaultCam = isMobile ? 'environment' : 'default';
        this.cameraSelect.value = defaultCam;
        return this.initializeCamera(defaultCam);
      });

    // Language init
    this.currentLanguage = localStorage.getItem('language') || 'en';
    this.updateLanguage(this.currentLanguage);
  }

  /* ---------- Camera helpers ------------------------------------------------ */

  async getCameraDevices() {
    try {
      const devices     = await navigator.mediaDevices.enumerateDevices();
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
    // Stop previous stream
    if (this.currentStream) {
      this.currentStream.getTracks().forEach(t => t.stop());
      this.currentStream = null;
    }

    /* Reset UI */
    this.video.classList.add('show');
    this.canvas.classList.remove('show');
    this.captureButton.style.display = 'inline-block';
    this.retakeButton.style.display  = 'none';

    /* Build constraints */
    let videoConstraint;
    if (selection === 'default') {
      videoConstraint = { width: { ideal: 1280 }, height: { ideal: 720 } };
    } else if (selection === 'user' || selection === 'environment') {
      videoConstraint = {
        width:  { ideal: 1280 },
        height: { ideal: 720 },
        facingMode: { exact: selection }
      };
    } else {
      videoConstraint = {
        width:  { ideal: 1280 },
        height: { ideal: 720 },
        deviceId: { exact: selection }
      };
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: videoConstraint });
      this.video.srcObject = stream;
      this.currentStream   = stream;
    } catch (err) {
      console.warn('Requested constraints failed, falling back to default:', err);
      try {
        const fallback = await navigator.mediaDevices.getUserMedia({ video: true });
        this.video.srcObject = fallback;
        this.currentStream   = fallback;
      } catch (fbErr) {
        console.error('Fallback also failed:', fbErr);
        this.resultDiv.textContent = 'Error: Cannot access camera';
      }
    }
  }

  /* ---------- Capture + prediction ----------------------------------------- */

  async captureImage() {
    // Draw the video frame to canvas
    this.canvas.width  = this.video.clientWidth;
    this.canvas.height = this.video.clientHeight;
    this.canvas.getContext('2d').drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);

    /* Swap UI */
    this.video.classList.remove('show');
    this.canvas.classList.add('show');
    this.captureButton.style.display = 'none';
    this.retakeButton.style.display  = 'inline-block';

    const spinner    = document.getElementById('spinner');
    const resultText = document.getElementById('result-text');
    spinner.style.display = 'inline-block';
    resultText.textContent = 'Processing…';
    this.captureButton.disabled = true;

    try {
      const blob = await new Promise(res => this.canvas.toBlob(res, 'image/jpeg', 0.8));
      const fd   = new FormData();
      fd.append('image', blob);

      const resp = await fetch(`${API_URL}/predict`, { method: 'POST', body: fd });
      const data = await resp.json();

      if (data.success) {
        // Store both raw product code and image for use on both pages
        localStorage.setItem('productName', data.prediction); // Keep for backward compatibility
        localStorage.setItem('rawProductCode', data.prediction); // Store raw code explicitly
        localStorage.setItem('capturedImage', this.canvas.toDataURL('image/jpeg'));
        
        // Get display name from mapping for showing to user
        const displayName = this.product_mapping[data.prediction.toLowerCase()] || data.prediction;
        resultText.textContent = `Predicted: ${displayName}`;
        
        this.showQuerySection(data.prediction);
      } else {
        resultText.textContent = `Error: ${data.error}`;
      }
    } catch (err) {
      console.error(err);
      resultText.textContent = 'Error: Could not connect to server';
    } finally {
      spinner.style.display = 'none';
      this.captureButton.disabled = false;
    }
  }

  /* ---------- UI helpers ---------------------------------------------------- */

  showQuerySection(productCode) {
    this.captureSection.style.display = 'none';
    this.querySection.style.display   = 'block';
    
    // Apply the product mapping to get friendly name
    const displayName = this.product_mapping[productCode.toLowerCase()] || productCode;
    this.productNameEl.textContent = `Product: ${displayName}`;
  }

  async fetchQuery(queryType) {
    // Get the original product code for API call
    const productCode = localStorage.getItem('rawProductCode') || localStorage.getItem('productName');
    const language = this.currentLanguage;
    
    this.queryResult.textContent = language === 'es' ? 'Cargando...' : 'Loading...';

    try {
      const response = await fetch(`${API_URL}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          product_name: productCode, // Use raw product code for API
          query_type: queryType, 
          language 
        })
      });

      const data = await response.json();
      if (data.success) {
        this.queryResult.innerHTML = `
          <p>${data.details}</p>
          <audio controls>
            <source src="${data.audio_url}" type="audio/mpeg">
            ${language === 'es' 
              ? 'Su navegador no soporta el elemento de audio.'
              : 'Your browser does not support the audio element.'}
          </audio>`;
      } else {
        this.queryResult.textContent = language === 'es'
          ? `Error: No se pudo obtener el resultado`
          : `Error: Could not fetch query result`;
      }
    } catch (err) {
      console.error(err);
      this.queryResult.textContent = language === 'es'
        ? 'Error: No se pudo conectar al servidor'
        : 'Error: Could not connect to server';
    }
  }

  retakeImage() {
    this.canvas.classList.remove('show');
    this.video.classList.add('show');
    this.captureButton.style.display = 'inline-block';
    this.retakeButton.style.display  = 'none';
    document.getElementById('result-text').textContent = this.currentLanguage === 'es' 
      ? 'Esperando captura...' 
      : 'Awaiting capture...';
  }

  updateLanguage(language) {
    document.querySelectorAll('[data-lang-en]').forEach(el => {
      el.textContent = language === 'es' 
        ? el.getAttribute('data-lang-es') 
        : el.getAttribute('data-lang-en');
    });
    localStorage.setItem('language', language);
    this.currentLanguage = language;
  }

  /* ---------- Listeners ----------------------------------------------------- */

  setupEventListeners() {
    this.captureButton.addEventListener('click', () => this.captureImage());
    this.retakeButton .addEventListener('click', () => this.retakeImage());
    this.cameraSelect.addEventListener('change', () => this.initializeCamera(this.cameraSelect.value));

    document.getElementById('nutrition-btn').addEventListener('click', () => this.fetchQuery('nutrition'));
    document.getElementById('allergen-btn').addEventListener('click', () => this.fetchQuery('allergen'));
    document.getElementById('price-btn')   .addEventListener('click', () => this.fetchQuery('price'));
    document.getElementById('go-back-btn') .addEventListener('click', () => this.goBack());
    
    // language toggle listener
    document.getElementById('language-toggle').addEventListener('click', () => {
      this.currentLanguage = this.currentLanguage === 'en' ? 'es' : 'en';
      this.updateLanguage(this.currentLanguage);
    });
  }

  goBack() {
    this.querySection.style.display = 'none';
    this.captureSection.style.display = 'block';
  }
}

window.addEventListener('load', () => new VisionApp());