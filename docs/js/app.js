/* docs/js/app.js */

const API_URL = "https://f9cf-75-187-72-180.ngrok-free.app";

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

    this.setupEventListeners();
    this.initializeCamera()
      .then(() => this.getCameraDevices())
      .then(() => {
        const isMobile = /Mobi|Android/i.test(navigator.userAgent);
        const defaultCam = isMobile ? 'environment' : 'default';
        this.cameraSelect.value = defaultCam;
        return this.initializeCamera(defaultCam);
      });
  }

  /* … all your existing VisionApp methods unchanged … */

  setupEventListeners() {
    if (this.captureButton) {
      this.captureButton.addEventListener('click', () => this.captureImage());
    }
    if (this.retakeButton) {
      this.retakeButton.addEventListener('click', () => this.retakeImage());
    }
    if (this.cameraSelect) {
      this.cameraSelect.addEventListener('change', () => {
        this.initializeCamera(this.cameraSelect.value);
      });
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
}

window.addEventListener('load', () => new VisionApp());

document.addEventListener('DOMContentLoaded', () => {
  // The toggle button only exists on index.html
  const languageToggle = document.getElementById('language-toggle');
  // Persisted language, default to English
  let currentLanguage = localStorage.getItem('language') || 'en';

  const updateLanguage = (language) => {
    // 1) Translate every element with data-lang-en
    document.querySelectorAll('[data-lang-en]').forEach(el => {
      el.textContent = language === 'es'
        ? el.getAttribute('data-lang-es')
        : el.getAttribute('data-lang-en');
    });
    // 2) If we have a toggle button, update its label
    if (languageToggle) {
      languageToggle.textContent = language === 'es'
        ? 'Switch to English'
        : 'Switch to Spanish';
    }
    localStorage.setItem('language', language);
  };

  // Apply language on page load
  updateLanguage(currentLanguage);

  // Only hook up the click if the button exists
  if (languageToggle) {
    languageToggle.addEventListener('click', () => {
      currentLanguage = currentLanguage === 'en' ? 'es' : 'en';
      updateLanguage(currentLanguage);
    });
  }
});
