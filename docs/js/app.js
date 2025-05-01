const API_URL = "https://cf94-75-187-72-180.ngrok-free.app";

class VisionApp {
  constructor() {
    this.video = document.getElementById('video');
    this.canvas = document.getElementById('canvas');
    this.captureButton = document.getElementById('capture');
    this.retakeButton = document.getElementById('retake');
    this.resultDiv = document.getElementById('result');
    this.cameraSelect = document.getElementById('camera-select');
    this.querySection = document.getElementById('query-section');
    this.captureSection = document.getElementById('capture-section');
    this.productName = document.getElementById('product-name');
    this.queryResult = document.getElementById('query-result');
    this.currentStream = null;
    this.languageToggle = document.getElementById('language-toggle');
    this.currentLanguage = localStorage.getItem('language') || 'en';

    this.setupEventListeners();
    this.updateLanguage(this.currentLanguage);
    
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
      this.resultDiv.textContent = this.currentLanguage === 'es' ? 'Error: No se pudieron listar los dispositivos de cámara' : 'Error: Could not list camera devices';
    }
  }

  populateCameraSelect(videoInputs) {
    this.cameraSelect.innerHTML = '';
    this.cameraSelect.add(new Option(this.currentLanguage === 'es' ? 'Cámara predeterminada' : 'Default camera', 'default'));
    this.cameraSelect.add(new Option(this.currentLanguage === 'es' ? 'Frontal (selfie)' : 'Front (selfie)', 'user'));
    this.cameraSelect.add(new Option(this.currentLanguage === 'es' ? 'Trasera' : 'Rear', 'environment'));
    videoInputs.forEach((device, idx) => {
      const label = device.label || (this.currentLanguage === 'es' ? `Cámara ${idx + 1}` : `Camera ${idx + 1}`);
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
        this.resultDiv.textContent = this.currentLanguage === 'es' ? 'Error: No se puede acceder a la cámara' : 'Error: Cannot access camera';
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
    resultText.textContent = this.currentLanguage === 'es' ? 'Procesando...' : 'Processing...';
    this.captureButton.disabled = true;

    try {
      const blob = await new Promise(res => this.canvas.toBlob(res, 'image/jpeg', 0.8));
      const formData = new FormData();
      formData.append('image', blob);
      const resp = await fetch(`${API_URL}/predict`, { method: 'POST', body: formData });
      const data = await resp.json();

      if (data.success) {
        resultText.textContent = this.currentLanguage === 'es' ? `Predicción: ${data.prediction}` : `Predicted: ${data.prediction}`;
        this.showQuerySection(data.prediction);
      } else {
        resultText.textContent = this.currentLanguage === 'es' ? `Error: ${data.error}` : `Error: ${data.error}`;
      }
    } catch (err) {
      console.error(err);
      resultText.textContent = this.currentLanguage === 'es' ? 'Error: No se pudo conectar al servidor' : 'Error: Could not connect to server';
    } finally {
      spinner.style.display = 'none';
      this.captureButton.disabled = false;
    }
  }

  showQuerySection(productName) {
    this.captureSection.style.display = 'none';
    this.querySection.style.display = 'block';
    
    // Save product name and language to localStorage for product-details.html
    localStorage.setItem('productName', productName);
    localStorage.setItem('language', this.currentLanguage);
    
    this.productName.textContent = this.currentLanguage === 'es' ? `Producto: ${productName}` : `Product: ${productName}`;
    this.updateQuerySectionLanguage();
  }

  async fetchQuery(queryType) {
    const productName = this.productName.textContent.replace(this.currentLanguage === 'es' ? 'Producto: ' : 'Product: ', '');
    this.queryResult.textContent = this.currentLanguage === 'es' ? 'Cargando...' : 'Loading...';

    try {
      const response = await fetch(`${API_URL}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_name: productName, query_type: queryType, language: this.currentLanguage })
      });

      const data = await response.json();
      if (data.success) {
        this.queryResult.innerHTML = `
          <p>${queryType}: ${data.details}</p>
          <audio controls>
            <source src="${data.audio_url}" type="audio/mpeg">
            ${this.currentLanguage === 'es' ? 'Su navegador no soporta el elemento de audio.' : 'Your browser does not support the audio element.'}
          </audio>
        `;
      } else {
        this.queryResult.textContent = this.currentLanguage === 'es' ? `Error: ${data.error}` : `Error: ${data.error}`;
      }
    } catch (err) {
      console.error(err);
      this.queryResult.textContent = this.currentLanguage === 'es' ? 'Error: No se pudo obtener el resultado de la consulta' : 'Error: Could not fetch query result';
    }
  }

  retakeImage() {
    this.canvas.classList.remove('show');
    this.video.classList.add('show');
    this.captureButton.style.display = 'inline-block';
    this.retakeButton.style.display = 'none';
    document.getElementById('result-text').textContent = this.currentLanguage === 'es' ? 'Esperando captura...' : 'Awaiting capture...';
  }

  updateLanguage(language) {
    this.currentLanguage = language;
    localStorage.setItem('language', language);
    
    // Update UI text based on language
    if (this.captureButton) {
      this.captureButton.textContent = language === 'es' ? 'Capturar y Predecir' : 'Capture & Predict';
    }
    if (this.retakeButton) {
      this.retakeButton.textContent = language === 'es' ? 'Volver a Tomar' : 'Retake';
    }
    if (document.getElementById('result-text')) {
      document.getElementById('result-text').textContent = language === 'es' ? 'Esperando captura...' : 'Awaiting capture...';
    }
    if (this.languageToggle) {
      this.languageToggle.textContent = language === 'es' ? 'Switch to English' : 'Cambiar a Español';
    }
    
    // If we're in query section, update those texts too
    if (this.querySection && this.querySection.style.display !== 'none') {
      this.updateQuerySectionLanguage();
    }
    
    // Update camera select options
    if (this.cameraSelect && this.cameraSelect.options.length > 0) {
      this.getCameraDevices();
    }
  }
  
  updateQuerySectionLanguage() {
    if (document.getElementById('nutrition-btn')) {
      document.getElementById('nutrition-btn').textContent = this.currentLanguage === 'es' ? 'Información Nutricional' : 'Nutrition Facts';
    }
    if (document.getElementById('allergen-btn')) {
      document.getElementById('allergen-btn').textContent = this.currentLanguage === 'es' ? 'Información de Alergias' : 'Allergen Information';
    }
    if (document.getElementById('price-btn')) {
      document.getElementById('price-btn').textContent = this.currentLanguage === 'es' ? 'Precio' : 'Price';
    }
    if (document.getElementById('go-back-btn')) {
      document.getElementById('go-back-btn').textContent = this.currentLanguage === 'es' ? 'Regresar' : 'Go Back';
    }
  }

  toggleLanguage() {
    const newLanguage = this.currentLanguage === 'en' ? 'es' : 'en';
    this.updateLanguage(newLanguage);
  }

  setupEventListeners() {
    this.captureButton.addEventListener('click', () => this.captureImage());
    this.retakeButton.addEventListener('click', () => this.retakeImage());
    this.cameraSelect.addEventListener('change', () => {
      this.initializeCamera(this.cameraSelect.value);
    });
    
    if (this.languageToggle) {
      this.languageToggle.addEventListener('click', () => this.toggleLanguage());
    }
    
    if (document.getElementById('nutrition-btn')) {
      document.getElementById('nutrition-btn').addEventListener('click', () => this.fetchQuery('nutrition'));
    }
    if (document.getElementById('allergen-btn')) {
      document.getElementById('allergen-btn').addEventListener('click', () => this.fetchQuery('allergen'));
    }
    if (document.getElementById('price-btn')) {
      document.getElementById('price-btn').addEventListener('click', () => this.fetchQuery('price'));
    }
    if (document.getElementById('go-back-btn')) {
      document.getElementById('go-back-btn').addEventListener('click', () => this.goBack());
    }
  }

  goBack() {
    this.querySection.style.display = 'none';
    this.captureSection.style.display = 'block';
  }
}

window.addEventListener('load', () => new VisionApp());