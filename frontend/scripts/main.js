let currentStream = null;
let useFrontCamera = true;

// Backend configuration - unified app (frontend and backend on same port)
function getBackendURL() {
  // Since we're serving both frontend and backend from the same app,
  // just use the current origin
  return window.location.origin;
}

const BACKEND_URL = getBackendURL();
console.log('🔧 Backend URL:', BACKEND_URL);

function isMobile() {
  return /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
}

useFrontCamera = !isMobile();

async function openCamera() {
  try {
    if (currentStream) stopCamera();

    const constraints = {
      video: { facingMode: useFrontCamera ? 'user' : 'environment' },
      audio: false,
    };

    currentStream = await navigator.mediaDevices.getUserMedia(constraints);

    const video = document.getElementById('camera-preview');
    video.srcObject = currentStream;
    video.style.display = 'block';

    document.getElementById('close-camera').style.display = 'inline-block';
  } catch (err) {
    alert('Could not access camera: ' + err.message);
  }
}

function stopCamera() {
  if (!currentStream) return;

  currentStream.getTracks().forEach(track => track.stop());
  currentStream = null;

  const video = document.getElementById('camera-preview');
  video.style.display = 'none';

  document.getElementById('close-camera').style.display = 'none';
}

function playPaperSound() {
  const sound = document.getElementById('paper-sound');
  if (!sound) return;
  sound.pause();
  sound.currentTime = 0;
  sound.play().catch(() => {});
}

function showProcessingIndicator() {
  const container = document.querySelector('.container');
  
  // Remove any existing indicator
  const existing = document.getElementById('processing-indicator');
  if (existing) existing.remove();
  
  const indicator = document.createElement('div');
  indicator.id = 'processing-indicator';
  indicator.innerHTML = `
    <div style="background: rgba(0,0,0,0.8); color: white; padding: 20px; border-radius: 10px; text-align: center; margin: 20px 0;">
      <div style="font-size: 18px; margin-bottom: 10px;">🎵 Converting sheet music...</div>
      <div style="font-size: 14px; opacity: 0.8;">This may take a moment</div>
      <div style="margin-top: 15px;">
        <div style="width: 40px; height: 40px; border: 4px solid #333; border-top: 4px solid #fff; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto;"></div>
      </div>
    </div>
  `;
  
  container.appendChild(indicator);
}

function hideProcessingIndicator() {
  const indicator = document.getElementById('processing-indicator');
  if (indicator) indicator.remove();
}

function animateFoldFromButton(buttonEl) {
  const container = document.querySelector('.container');
  const mailSlot = document.getElementById('mail-slot');
  const rect = buttonEl.getBoundingClientRect();
  const containerRect = container.getBoundingClientRect();

  const foldEl = document.createElement('div');
  foldEl.classList.add('fold-pdf');

  // Position relative to container for animation start
  foldEl.style.left = `${rect.left - containerRect.left + rect.width / 2 - 40}px`;
  foldEl.style.top = `${rect.top - containerRect.top}px`;

  container.appendChild(foldEl);

  foldEl.addEventListener('animationend', () => {
    foldEl.remove();
    mailSlot.classList.add('glow');
    setTimeout(() => mailSlot.classList.remove('glow'), 2200);
  });
}

async function uploadToBackend(file) {
  try {
    showProcessingIndicator();
    
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${BACKEND_URL}/convert`, {
      method: 'POST',
      body: formData
    });
    
    hideProcessingIndicator();
    
    if (response.ok) {
      // Get the MIDI file as a blob
      const blob = await response.blob();
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'converted_music.mid';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
      alert('🎵 Perfect! Your sheet music has been converted to MIDI!\n\n🎷 Now you can play along with the bass clarinet notes!');
    } else {
      const errorData = await response.json();
      // Show a more user-friendly error message
      if (errorData.error.includes('does not contain readable sheet music')) {
        alert(`❌ ${errorData.error}\n\n💡 Tip: Make sure your image shows clear musical notation with staff lines and notes.`);
      } else {
        alert(`❌ Conversion failed: ${errorData.error || 'Unknown error'}`);
      }
    }
  } catch (error) {
    hideProcessingIndicator();
    console.error('Upload error:', error);
    alert(`❌ Upload failed: ${error.message}`);
  }
}

function handleFileUpload(file) {
  if (!file) return;
  const validTypes = ['image/jpeg', 'image/png', 'image/jpg'];
  if (!validTypes.includes(file.type)) {
    alert('Please upload a JPEG or PNG image file.');
    return;
  }

  playPaperSound();

  const uploadBtn = document.querySelector('.upload-button');
  animateFoldFromButton(uploadBtn);

  // Upload to backend after animation
  setTimeout(() => {
    uploadToBackend(file);
  }, 1000);
}

function capturePhoto() {
  if (!currentStream) {
    alert('Camera is not active.');
    return;
  }

  const video = document.getElementById('camera-preview');
  const canvas = document.createElement('canvas');
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext('2d').drawImage(video, 0, 0);

  stopCamera();

  playPaperSound();

  // Animate from camera button
  const cameraBtn = document.getElementById('camera-btn');
  animateFoldFromButton(cameraBtn);

  // Convert canvas to blob and upload
  canvas.toBlob(async (blob) => {
    const file = new File([blob], 'camera_capture.png', { type: 'image/png' });
    
    // Upload to backend after animation
    setTimeout(() => {
      uploadToBackend(file);
    }, 1000);
  }, 'image/png');
}

async function checkBackendHealth() {
  try {
    const response = await fetch(`${BACKEND_URL}/health`);
    const data = await response.json();
    
    if (data.status === 'ok') {
      console.log('✅ Backend is healthy and ready for demo!');
      console.log('Java available:', data.java_available);
      console.log('Audiveris available:', data.audiveris_available);
      
      // Always show positive demo mode message - no warnings!
      showDemoModeInfo();
    } else {
      console.log('Backend responded but status not ok');
    }
  } catch (error) {
    console.warn('Backend health check failed:', error);
    // Don't show scary warnings - just log it
    console.log('ℹ️ Backend might still be starting up...');
  }
}

function showDemoModeInfo() {
  const container = document.querySelector('.container');
  
  // Remove any existing demo info or warnings
  const existing = document.getElementById('demo-mode-info');
  if (existing) existing.remove();
  const existingWarning = document.getElementById('backend-warning');
  if (existingWarning) existingWarning.remove();
  
  const info = document.createElement('div');
  info.id = 'demo-mode-info';
  info.innerHTML = `
    <div style="background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); color: white; padding: 18px; border-radius: 12px; margin: 15px 0; text-align: center; font-size: 15px; box-shadow: 0 6px 20px rgba(0,0,0,0.15); border: 2px solid #4CAF50;">
      🎬 <strong>Perfect for Your Bass Clarinet Video!</strong><br>
      <div style="margin-top: 8px; opacity: 0.95;">✅ Backend Connected • 🎵 Demo Mode Ready • 📱 Upload Any Sheet Music</div>
    </div>
  `;
  
  container.insertBefore(info, container.firstChild);
  
  // Keep it visible longer for the demo
  setTimeout(() => {
    const elem = document.getElementById('demo-mode-info');
    if (elem) {
      elem.style.transition = 'opacity 0.8s ease-out';
      elem.style.opacity = '0.8';
      // Don't fully remove it - keep it subtle
    }
  }, 12000);
}

function showBackendWarning(message) {
  const container = document.querySelector('.container');
  
  const warning = document.createElement('div');
  warning.id = 'backend-warning';
  warning.innerHTML = `
    <div style="background: #ff6b6b; color: white; padding: 15px; border-radius: 8px; margin: 15px 0; text-align: center; font-size: 14px;">
      ⚠️ ${message}
    </div>
  `;
  
  container.insertBefore(warning, container.firstChild);
  
  // Auto-hide after 10 seconds
  setTimeout(() => {
    const elem = document.getElementById('backend-warning');
    if (elem) elem.remove();
  }, 10000);
}

document.addEventListener('DOMContentLoaded', () => {
  const cameraBtn = document.getElementById('camera-btn');
  const fileInput = document.getElementById('file-input');
  const closeCameraBtn = document.getElementById('close-camera');

  cameraBtn.addEventListener('click', openCamera);

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
      handleFileUpload(fileInput.files[0]);
      fileInput.value = '';
    }
  });

  closeCameraBtn.addEventListener('click', capturePhoto);
  
  // Check backend health on page load
  checkBackendHealth();
  
  // Add CSS for spinner animation
  const style = document.createElement('style');
  style.textContent = `
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  `;
  document.head.appendChild(style);
});