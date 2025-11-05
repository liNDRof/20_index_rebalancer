/**
 * CRYPTO EFFECTS - Advanced Animations & Visual Effects
 * Modern cryptocurrency trading platform animations
 * Features: Particle effects, animated backgrounds, interactive elements
 */

(function() {
  'use strict';

  // ========================================
  // FLOATING PARTICLES ANIMATION
  // ========================================
  class CryptoParticles {
    constructor(canvasId, options = {}) {
      this.canvas = document.getElementById(canvasId);
      if (!this.canvas) return;

      this.ctx = this.canvas.getContext('2d');
      this.particles = [];
      this.options = {
        particleCount: options.particleCount || 50,
        particleSpeed: options.particleSpeed || 0.5,
        particleSize: options.particleSize || 2,
        particleColor: options.particleColor || 'rgba(59, 130, 246, 0.6)',
        connectionDistance: options.connectionDistance || 150,
        lineColor: options.lineColor || 'rgba(59, 130, 246, 0.2)',
        ...options
      };

      this.init();
      this.animate();
      window.addEventListener('resize', () => this.resize());
    }

    init() {
      this.resize();
      this.createParticles();
    }

    resize() {
      this.canvas.width = window.innerWidth;
      this.canvas.height = window.innerHeight;
    }

    createParticles() {
      this.particles = [];
      for (let i = 0; i < this.options.particleCount; i++) {
        this.particles.push({
          x: Math.random() * this.canvas.width,
          y: Math.random() * this.canvas.height,
          vx: (Math.random() - 0.5) * this.options.particleSpeed,
          vy: (Math.random() - 0.5) * this.options.particleSpeed,
          size: Math.random() * this.options.particleSize + 1
        });
      }
    }

    drawParticles() {
      this.particles.forEach(particle => {
        this.ctx.beginPath();
        this.ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
        this.ctx.fillStyle = this.options.particleColor;
        this.ctx.fill();
      });
    }

    updateParticles() {
      this.particles.forEach(particle => {
        particle.x += particle.vx;
        particle.y += particle.vy;

        if (particle.x < 0 || particle.x > this.canvas.width) particle.vx *= -1;
        if (particle.y < 0 || particle.y > this.canvas.height) particle.vy *= -1;
      });
    }

    drawConnections() {
      for (let i = 0; i < this.particles.length; i++) {
        for (let j = i + 1; j < this.particles.length; j++) {
          const dx = this.particles[i].x - this.particles[j].x;
          const dy = this.particles[i].y - this.particles[j].y;
          const distance = Math.sqrt(dx * dx + dy * dy);

          if (distance < this.options.connectionDistance) {
            this.ctx.beginPath();
            this.ctx.strokeStyle = this.options.lineColor;
            this.ctx.lineWidth = 1 - distance / this.options.connectionDistance;
            this.ctx.moveTo(this.particles[i].x, this.particles[i].y);
            this.ctx.lineTo(this.particles[j].x, this.particles[j].y);
            this.ctx.stroke();
          }
        }
      }
    }

    animate() {
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
      this.drawParticles();
      this.drawConnections();
      this.updateParticles();
      requestAnimationFrame(() => this.animate());
    }
  }

  // ========================================
  // CRYPTO TICKER ANIMATION
  // ========================================
  class CryptoTicker {
    constructor(elementId, symbols = []) {
      this.element = document.getElementById(elementId);
      if (!this.element) return;

      this.symbols = symbols.length > 0 ? symbols : ['BTC', 'ETH', 'BNB', 'USDC', 'SOL', 'ADA'];
      this.currentIndex = 0;
      this.init();
    }

    init() {
      this.updateTicker();
      setInterval(() => this.updateTicker(), 3000);
    }

    updateTicker() {
      const symbol = this.symbols[this.currentIndex];
      const price = this.generateRandomPrice(symbol);
      const change = (Math.random() * 10 - 5).toFixed(2);
      const isPositive = change >= 0;

      this.element.innerHTML = `
        <span class="ticker-symbol">${symbol}</span>
        <span class="ticker-price">$${price}</span>
        <span class="ticker-change ${isPositive ? 'positive' : 'negative'}">
          ${isPositive ? '▲' : '▼'} ${Math.abs(change)}%
        </span>
      `;

      this.element.style.animation = 'none';
      setTimeout(() => {
        this.element.style.animation = 'tickerSlide 0.5s ease';
      }, 10);

      this.currentIndex = (this.currentIndex + 1) % this.symbols.length;
    }

    generateRandomPrice(symbol) {
      const prices = {
        'BTC': (40000 + Math.random() * 20000).toFixed(2),
        'ETH': (2000 + Math.random() * 1000).toFixed(2),
        'BNB': (300 + Math.random() * 100).toFixed(2),
        'USDC': '1.00',
        'SOL': (50 + Math.random() * 50).toFixed(2),
        'ADA': (0.5 + Math.random() * 0.5).toFixed(3)
      };
      return prices[symbol] || '0.00';
    }
  }

  // ========================================
  // NUMBER COUNTER ANIMATION
  // ========================================
  function animateCounter(element, targetValue, duration = 1000, decimals = 2) {
    if (!element) return;

    const startValue = parseFloat(element.textContent) || 0;
    const target = parseFloat(targetValue);
    const startTime = performance.now();

    function update(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);

      const easeOutQuad = progress * (2 - progress);
      const currentValue = startValue + (target - startValue) * easeOutQuad;

      element.textContent = currentValue.toFixed(decimals);

      if (progress < 1) {
        requestAnimationFrame(update);
      } else {
        element.textContent = target.toFixed(decimals);
      }
    }

    requestAnimationFrame(update);
  }

  // ========================================
  // GLOWING EFFECT ON ELEMENTS
  // ========================================
  function addGlowEffect(selector, color = 'rgba(59, 130, 246, 0.5)') {
    const elements = document.querySelectorAll(selector);
    elements.forEach(el => {
      el.addEventListener('mouseenter', function() {
        this.style.boxShadow = `0 0 20px ${color}, 0 0 40px ${color}`;
      });
      el.addEventListener('mouseleave', function() {
        this.style.boxShadow = '';
      });
    });
  }

  // ========================================
  // CARD TILT EFFECT (3D)
  // ========================================
  function addTiltEffect(selector, maxTilt = 10) {
    const elements = document.querySelectorAll(selector);

    elements.forEach(el => {
      el.addEventListener('mousemove', function(e) {
        const rect = this.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const centerX = rect.width / 2;
        const centerY = rect.height / 2;

        const rotateX = ((y - centerY) / centerY) * maxTilt;
        const rotateY = ((centerX - x) / centerX) * maxTilt;

        this.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`;
      });

      el.addEventListener('mouseleave', function() {
        this.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale3d(1, 1, 1)';
      });

      // Add transition for smooth effect
      el.style.transition = 'transform 0.1s ease-out';
    });
  }

  // ========================================
  // RIPPLE EFFECT ON CLICK
  // ========================================
  function addRippleEffect(selector) {
    const elements = document.querySelectorAll(selector);

    elements.forEach(el => {
      el.addEventListener('click', function(e) {
        const ripple = document.createElement('span');
        ripple.classList.add('ripple-effect');

        const rect = this.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;

        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';

        this.appendChild(ripple);

        setTimeout(() => ripple.remove(), 600);
      });

      // Add required CSS if not present
      if (!el.style.position || el.style.position === 'static') {
        el.style.position = 'relative';
      }
      if (!el.style.overflow) {
        el.style.overflow = 'hidden';
      }
    });

    // Add CSS for ripple effect if not exists
    if (!document.getElementById('ripple-style')) {
      const style = document.createElement('style');
      style.id = 'ripple-style';
      style.textContent = `
        .ripple-effect {
          position: absolute;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.6);
          transform: scale(0);
          animation: ripple-animation 0.6s ease-out;
          pointer-events: none;
        }
        @keyframes ripple-animation {
          to {
            transform: scale(2);
            opacity: 0;
          }
        }
      `;
      document.head.appendChild(style);
    }
  }

  // ========================================
  // SMOOTH SCROLL REVEAL ANIMATION
  // ========================================
  class ScrollReveal {
    constructor(selector, options = {}) {
      this.elements = document.querySelectorAll(selector);
      this.options = {
        threshold: options.threshold || 0.1,
        delay: options.delay || 100,
        ...options
      };
      this.init();
    }

    init() {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry, index) => {
          if (entry.isIntersecting) {
            setTimeout(() => {
              entry.target.classList.add('revealed');
            }, index * this.options.delay);
            observer.unobserve(entry.target);
          }
        });
      }, { threshold: this.options.threshold });

      this.elements.forEach(el => {
        el.classList.add('reveal-element');
        observer.observe(el);
      });

      // Add CSS for reveal animation
      this.addRevealStyles();
    }

    addRevealStyles() {
      if (!document.getElementById('reveal-style')) {
        const style = document.createElement('style');
        style.id = 'reveal-style';
        style.textContent = `
          .reveal-element {
            opacity: 0;
            transform: translateY(30px);
            transition: opacity 0.6s ease, transform 0.6s ease;
          }
          .reveal-element.revealed {
            opacity: 1;
            transform: translateY(0);
          }
        `;
        document.head.appendChild(style);
      }
    }
  }

  // ========================================
  // PRICE FLASH ANIMATION
  // ========================================
  function flashPrice(element, isIncrease) {
    if (!element) return;

    const flashClass = isIncrease ? 'flash-green' : 'flash-red';
    element.classList.add(flashClass);

    setTimeout(() => {
      element.classList.remove(flashClass);
    }, 500);

    // Add CSS for flash effect if not exists
    if (!document.getElementById('flash-style')) {
      const style = document.createElement('style');
      style.id = 'flash-style';
      style.textContent = `
        @keyframes flash-green-anim {
          0%, 100% { background-color: transparent; }
          50% { background-color: rgba(34, 197, 94, 0.3); }
        }
        @keyframes flash-red-anim {
          0%, 100% { background-color: transparent; }
          50% { background-color: rgba(239, 68, 68, 0.3); }
        }
        .flash-green {
          animation: flash-green-anim 0.5s ease;
        }
        .flash-red {
          animation: flash-red-anim 0.5s ease;
        }
      `;
      document.head.appendChild(style);
    }
  }

  // ========================================
  // TYPING EFFECT
  // ========================================
  function typeWriter(element, text, speed = 50) {
    if (!element) return;

    let i = 0;
    element.textContent = '';

    function type() {
      if (i < text.length) {
        element.textContent += text.charAt(i);
        i++;
        setTimeout(type, speed);
      }
    }

    type();
  }

  // ========================================
  // CONFETTI EFFECT (for successful trades)
  // ========================================
  function launchConfetti(options = {}) {
    const count = options.count || 100;
    const colors = options.colors || ['#3b82f6', '#8b5cf6', '#f59e0b', '#22c55e'];
    const duration = options.duration || 3000;

    for (let i = 0; i < count; i++) {
      setTimeout(() => {
        createConfettiPiece(colors[Math.floor(Math.random() * colors.length)]);
      }, i * 30);
    }

    function createConfettiPiece(color) {
      const confetti = document.createElement('div');
      confetti.style.position = 'fixed';
      confetti.style.width = '10px';
      confetti.style.height = '10px';
      confetti.style.backgroundColor = color;
      confetti.style.left = Math.random() * window.innerWidth + 'px';
      confetti.style.top = '-20px';
      confetti.style.opacity = '1';
      confetti.style.transform = `rotate(${Math.random() * 360}deg)`;
      confetti.style.zIndex = '9999';
      confetti.style.pointerEvents = 'none';
      confetti.style.borderRadius = Math.random() > 0.5 ? '50%' : '0';

      document.body.appendChild(confetti);

      const fallDuration = duration + Math.random() * 1000;
      const horizontalMovement = (Math.random() - 0.5) * 200;

      confetti.animate([
        {
          transform: `translateY(0) translateX(0) rotate(0deg)`,
          opacity: 1
        },
        {
          transform: `translateY(${window.innerHeight + 20}px) translateX(${horizontalMovement}px) rotate(${360 * 3}deg)`,
          opacity: 0
        }
      ], {
        duration: fallDuration,
        easing: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)'
      });

      setTimeout(() => confetti.remove(), fallDuration);
    }
  }

  // ========================================
  // EXPORT TO GLOBAL SCOPE
  // ========================================
  window.CryptoEffects = {
    CryptoParticles,
    CryptoTicker,
    animateCounter,
    addGlowEffect,
    addTiltEffect,
    addRippleEffect,
    ScrollReveal,
    flashPrice,
    typeWriter,
    launchConfetti
  };

  // ========================================
  // AUTO-INITIALIZE ON DOM READY
  // ========================================
  document.addEventListener('DOMContentLoaded', function() {
    // Add ripple effect to all buttons
    addRippleEffect('button, .btn');

    // Add glow effect to cards
    addGlowEffect('.card, .block');

    // Initialize scroll reveal for blocks
    if (document.querySelectorAll('.block').length > 0) {
      new ScrollReveal('.block', { delay: 100 });
    }

    console.log('🚀 Crypto Effects initialized');
  });

})();
