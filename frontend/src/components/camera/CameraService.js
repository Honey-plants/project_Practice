export class CameraService {
  constructor(videoElement, options = {}) {
    if (!videoElement) {
      throw new Error('VIDEO_ELEMENT_REQUIRED');
    }

    this.video = videoElement;
    this.stream = null;
    this.isActive = false;

    /* ===== Config ===== */

    this.facingMode = options.facingMode || 'environment';

    const isLocalhost =
      window.location.hostname === 'localhost' ||
      window.location.hostname === '127.0.0.1';

    this.__DEV__ = options.dev ?? isLocalhost;

    /* ===== Environment Detection ===== */

    this.isIOS =
      /iPad|iPhone|iPod/.test(navigator.userAgent) &&
      !window.MSStream;

    this.isDesktop =
      !/Mobi|Android|iPhone|iPad/.test(navigator.userAgent);

    /* ===== Analysis ===== */

    this.analysisCanvas = document.createElement('canvas');
    this.analysisCtx = this.analysisCanvas.getContext('2d');
    this.lastSharpness = null;

    /* ===== State ===== */

    this.disableCamera = false;
  }

  /* =========================
     Environment Info
     ========================= */

  getEnvInfo() {
    return {
      isIOS: this.isIOS,
      isDesktop: this.isDesktop,
      resolution: {
        width: this.video.videoWidth,
        height: this.video.videoHeight
      }
    };
  }

  /* =========================
     Camera Lifecycle
     ========================= */

  async start() {
    if (!navigator.mediaDevices?.getUserMedia) {
      throw { code: 'UNSUPPORTED_BROWSER' };
    }

    try {
      const constraints = {
        video: {
          facingMode: { ideal: this.facingMode },
          width: { ideal: 1280 },
          height: { ideal: 720 }
        },
        audio: false
      };

      this.stream = await navigator.mediaDevices.getUserMedia(constraints);
      this.video.srcObject = this.stream;

      await this.video.play();

      const MIN_DESKTOP_WIDTH = this.__DEV__ ? 320 : 1024;
      if (this.isDesktop && this.video.videoWidth < MIN_DESKTOP_WIDTH) {
        this.disableCamera = true;
      } else {
        this.disableCamera = false;
      }


      this.isActive = true;

      if (this.__DEV__) {
        console.log('[Camera] started');
        console.log(
          '[Camera] actual resolution:',
          this.video.videoWidth,
          this.video.videoHeight
        );
      }
    } catch (e) {
      if (this.__DEV__) {
        console.error('[Camera] start failed', e);
        console.log('[Env]', logEnvInfo());
      }

      throw this.#mapStartError(e);
    }
  }

  stop() {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }

    if (this.video) {
      this.video.srcObject = null;
    }

    this.isActive = false;

    if (this.__DEV__) {
      console.log('[Camera] stopped');
    }
  }

  async switchCamera() {
    this.facingMode =
      this.facingMode === 'environment' ? 'user' : 'environment';

    this.stop();
    await this.start();
  }

  /* =========================
     Frame Analysis
     ========================= */

  analyzeFrame() {
    const w = 160;
    const h = 120;

    this.analysisCanvas.width = w;
    this.analysisCanvas.height = h;

    this.analysisCtx.drawImage(this.video, 0, 0, w, h);
    const frame = this.analysisCtx.getImageData(0, 0, w, h);

    const brightness = this.#calcBrightness(frame);
    const sharpness = this.#calcSharpness(frame);
    const shaken = this.#detectShake(sharpness);

    return { brightness, sharpness, shaken };
  }

  canCapture() {
    if (!this.isActive) {
      return { ok: false, reason: 'NOT_READY' };
    }

    if (this.disableCamera) {
      return { ok: false, reason: 'LOW_RESOLUTION' };
    }

    const { brightness, sharpness, shaken } = this.analyzeFrame();

    if (brightness < 60) { 
      return { ok: false, reason: 'TOO_DARK' };
    }

    if (sharpness < 15) {
      return { ok: false, reason: 'BLURRY' };
    }

    if (shaken) {
      return { ok: false, reason: 'SHAKING' };
    }

    const MIN_CAPTURE_WIDTH = this.__DEV__ ? 320 : 1280;
    const MIN_CAPTURE_HEIGHT = this.__DEV__ ? 240 : 720;

    if (
      this.video.videoWidth < MIN_CAPTURE_WIDTH ||
      this.video.videoHeight < MIN_CAPTURE_HEIGHT
    ) {
      return { ok: false, reason: 'LOW_RESOLUTION' };
    }

    return { ok: true };
  }

  /* =========================
     Capture
     ========================= */

  capture() {
    return new Promise(resolve => {
      const canvas = document.createElement('canvas');
      canvas.width = this.video.videoWidth;
      canvas.height = this.video.videoHeight;

      const ctx = canvas.getContext('2d');
      ctx.drawImage(this.video, 0, 0);

      canvas.toBlob(
        blob => {
          // Blob을 File처럼 쓰고 싶으면 이름만 붙여도 됨
          const file = new File(
            [blob],
            `capture_${Date.now()}.jpg`,
            { type: 'image/jpeg' }
          );
          resolve(file);
        },
        'image/jpeg',
        0.95
      );
    });
  }


  /* =========================
     Internal Utils
     ========================= */

  #mapStartError(e) {
    if (e.name === 'NotAllowedError') {
      return { code: 'PERMISSION_DENIED' };
    }
    if (e.name === 'NotFoundError') {
      return { code: 'NO_CAMERA_DEVICE' };
    }
    if (e.name === 'NotReadableError') {
      return { code: 'CAMERA_IN_USE' };
    }
    return { code: 'UNKNOWN_CAMERA_ERROR' };
  }

  #calcBrightness(frame) {
    let sum = 0;
    const data = frame.data;

    for (let i = 0; i < data.length; i += 4) {
      sum +=
        0.2126 * data[i] +
        0.7152 * data[i + 1] +
        0.0722 * data[i + 2];
    }

    return sum / (data.length / 4);
  }

  #calcSharpness(frame) {
    let diffSum = 0;
    const data = frame.data;

    for (let i = 4; i < data.length; i += 4) {
      diffSum += Math.abs(data[i] - data[i - 4]);
    }

    return diffSum / (data.length / 4);
  }

  #detectShake(currentSharpness) {
    let shaken = false;

    if (this.lastSharpness !== null) {
      const diff = Math.abs(currentSharpness - this.lastSharpness);
      if (diff > 20) shaken = true;
    }

    this.lastSharpness = currentSharpness;
    return shaken;
  }
}

/* =========================
   DEV Utils
   ========================= */

function logEnvInfo() {
  return {
    userAgent: navigator.userAgent,
    platform: navigator.platform,
    vendor: navigator.vendor,
    screen: {
      width: window.screen.width,
      height: window.screen.height,
      ratio: window.devicePixelRatio
    }
  };
}
