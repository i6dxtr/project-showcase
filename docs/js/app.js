/* app.js - Complete Version with Spanish Translation Support */
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

    this.product_images = {
      'product-a': './stock/pb.png',
      'product-b': './stock/cookies.png',
      'product-c': './stock/salt.png',
      'product-d': './stock/cracker.png',
    };

    // Product mapping - Define it here so it's available throughout the class
    this.product_mapping = {
      'product-a': 'Kroger Creamy Peanut Butter',
      'product-b': 'Great Value Twist and Shout Cookies',
      'product-c': 'Morton Coarse Kosher Salt',
      'product-d': 'Unknown Product',
      // Add more mappings as needed
    };

    // Add Spanish translations for product names
    this.product_translations = {
      'Kroger Creamy Peanut Butter': 'Mantequilla de Maní Cremosa Kroger',
      'Great Value Twist and Shout Cookies': 'Galletas Twist and Shout Great Value',
      'Morton Coarse Kosher Salt': 'Sal Kosher Gruesa Morton',
      'Unknown Product': 'Producto Desconocido'
      // Add more translations as needed
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
      this.resultDiv.textContent = this.currentLanguage === 'es' 
        ? 'Error: No se pudieron enumerar los dispositivos de cámara' 
        : 'Error: Could not list camera devices';
    }
  }

  populateCameraSelect(videoInputs) {
    this.cameraSelect.innerHTML = '';
    
    // Translate camera options based on current language
    const defaultText = this.currentLanguage === 'es' ? 'Cámara predeterminada' : 'Default camera';
    const frontText = this.currentLanguage === 'es' ? 'Frontal (selfie)' : 'Front (selfie)';
    const rearText = this.currentLanguage === 'es' ? 'Trasera' : 'Rear';
    
    this.cameraSelect.add(new Option(defaultText, 'default'));
    this.cameraSelect.add(new Option(frontText, 'user'));
    this.cameraSelect.add(new Option(rearText, 'environment'));
    
    videoInputs.forEach((device, idx) => {
      const label = device.label || (this.currentLanguage === 'es' 
        ? `Cámara ${idx + 1}` 
        : `Camera ${idx + 1}`);
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
        this.resultDiv.textContent = this.currentLanguage === 'es' 
          ? 'Error: No se puede acceder a la cámara' 
          : 'Error: Cannot access camera';
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
    resultText.textContent = this.currentLanguage === 'es' ? 'Procesando…' : 'Processing…';
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
        
        // Translate product name if Spanish is selected
        let translatedName = displayName;
        if (this.currentLanguage === 'es' && this.product_translations[displayName]) {
          translatedName = this.product_translations[displayName];
        }
        
        const predictedText = this.currentLanguage === 'es' 
          ? `Producto identificado: ${translatedName}` 
          : `Predicted: ${translatedName}`;
          
        resultText.textContent = predictedText;
        
        this.showQuerySection(data.prediction);
      } else {
        resultText.textContent = this.currentLanguage === 'es'
          ? `Error: ${data.error || 'Error desconocido'}`
          : `Error: ${data.error || 'Unknown error'}`;
      }
    } catch (err) {
      console.error(err);
      resultText.textContent = this.currentLanguage === 'es'
        ? 'Error: No se pudo conectar al servidor'
        : 'Error: Could not connect to server';
    } finally {
      spinner.style.display = 'none';
      this.captureButton.disabled = false;
    }
  }

  /* ---------- UI helpers ---------------------------------------------------- */

  showQuerySection(productCode) {
    this.captureSection.style.display = 'none';
    this.querySection.style.display = 'block';
    
    // Apply the product mapping to get friendly name
    const displayName = this.product_mapping[productCode.toLowerCase()] || productCode;
    
    // Translate product name if Spanish is selected
    let translatedName = displayName;
    if (this.currentLanguage === 'es' && this.product_translations[displayName]) {
        translatedName = this.product_translations[displayName];
    }
    
    // Get the image path
    const imagePath = this.product_images[productCode.toLowerCase()] || '/images/default-product.jpg';
    
    // Create the product display with image and name
    this.productNameEl.innerHTML = `
        <div class="product-display">
            <img src="${imagePath}" alt="${translatedName}" class="product-image">
            <p>${this.currentLanguage === 'es' ? 'Producto: ' : 'Product: '} ${translatedName}</p>
        </div>
    `;
  }


  async fetchQuery(queryType) {
    // Get the original product code for API call
    const productCode = localStorage.getItem('rawProductCode') || localStorage.getItem('productName');
    const language = this.currentLanguage;
    
    this.queryResult.style.display = 'block';
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
          <audio controls autoplay>
            <source src="${API_URL}${data.audio_url}" type="audio/wav">
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
    
    // Update camera select options when language changes
    if (this.cameraSelect) {
      const currentValue = this.cameraSelect.value;
      this.getCameraDevices().then(() => {
        this.cameraSelect.value = currentValue;
      });
    }
    
    localStorage.setItem('language', language);
    this.currentLanguage = language;
    
    // Update any current content in the query result
    if (this.queryResult && this.queryResult.style.display !== 'none') {
      this.refreshCurrentQuery();
    }
  }
  
  /**
   * Refresh the current query with the updated language
   * Useful when language is changed while a result is displayed
   */
  refreshCurrentQuery() {
    // Only refresh if there's already a result showing
    if (!this.queryResult || this.queryResult.style.display === 'none') {
      return;
    }
    
    // Find which button is currently active (based on which query was last fetched)
    const buttons = ['nutrition-btn', 'allergen-btn', 'price-btn'];
    const activeButton = buttons.find(id => document.getElementById(id).classList.contains('active'));
    
    if (activeButton) {
      // Re-fetch the same query type with the new language
      const queryType = activeButton.replace('-btn', '');
      this.fetchQuery(queryType);
    }
  }

  /* ---------- Listeners ----------------------------------------------------- */

  setupEventListeners() {
    this.captureButton.addEventListener('click', () => this.captureImage());
    this.retakeButton.addEventListener('click', () => this.retakeImage());
    this.cameraSelect.addEventListener('change', () => this.initializeCamera(this.cameraSelect.value));

    // Add active class handling to track which button was last clicked
    const queryButtons = ['nutrition-btn', 'allergen-btn', 'price-btn'];
    
    queryButtons.forEach(btnId => {
      const btn = document.getElementById(btnId);
      btn.addEventListener('click', () => {
        // Remove active class from all buttons
        queryButtons.forEach(id => document.getElementById(id).classList.remove('active'));
        // Add active class to clicked button
        btn.classList.add('active');
        
        // Get query type from button ID
        const queryType = btnId.replace('-btn', '');
        this.fetchQuery(queryType);
      });
    });
    
    document.getElementById('go-back-btn').addEventListener('click', () => this.goBack());
    
    // language toggle listener
    document.getElementById('language-toggle').addEventListener('click', () => {
      this.currentLanguage = this.currentLanguage === 'en' ? 'es' : 'en';
      this.updateLanguage(this.currentLanguage);
    });
  }

  goBack() {
    this.querySection.style.display = 'none';
    this.captureSection.style.display = 'block';
    
    // Clear active state from all query buttons
    const queryButtons = ['nutrition-btn', 'allergen-btn', 'price-btn'];
    queryButtons.forEach(id => document.getElementById(id).classList.remove('active'));
    
    // Hide query result
    this.queryResult.style.display = 'none';
  }
}

window.addEventListener('load', () => new VisionApp());