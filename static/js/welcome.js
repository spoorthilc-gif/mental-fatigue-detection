// Welcome Page Interactive Logic - FatigueAI

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initTypingEffect();
  initScrollReveal();
  initCarousel();
  initCounters();
});

// Loader Dismissal
window.addEventListener('load', () => {
  const loader = document.getElementById('page-loader');
  if (loader) {
    loader.style.opacity = '0';
    setTimeout(() => {
      loader.style.display = 'none';
    }, 500);
  }
});

/* ──────────────── Theme Management ──────────────── */
function initTheme() {
  const currentTheme = localStorage.getItem('theme') || 'dark';
  document.documentElement.setAttribute('data-theme', currentTheme);
  updateThemeIcon(currentTheme);
}

function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', currentTheme);
  localStorage.setItem('theme', currentTheme);
  updateThemeIcon(currentTheme);
}

function updateThemeIcon(theme) {
  const icon = document.getElementById('themeToggleIcon');
  if (icon) {
    icon.textContent = theme === 'dark' ? '🌙' : '☀️';
  }
}

/* ──────────────── Text Typing Effect ──────────────── */
const phrases = [
  "Ensemble Machine Learning Predictions...",
  "MediaPipe Facial Mesh Telemetry...",
  "Real-time Behavioral Keyboard Analytics...",
  "Explainable AI Focus Diagnostics..."
];

function initTypingEffect() {
  const textContainer = document.getElementById('typingText');
  if (!textContainer) return;

  let phraseIdx = 0;
  let charIdx = 0;
  let isDeleting = false;
  let typingSpeed = 100;

  function type() {
    const currentPhrase = phrases[phraseIdx];

    if (isDeleting) {
      textContainer.textContent = currentPhrase.substring(0, charIdx - 1);
      charIdx--;
      typingSpeed = 50;
    } else {
      textContainer.textContent = currentPhrase.substring(0, charIdx + 1);
      charIdx++;
      typingSpeed = 120;
    }

    if (!isDeleting && charIdx === currentPhrase.length) {
      isDeleting = true;
      typingSpeed = 2000; // Pause at end of phrase
    } else if (isDeleting && charIdx === 0) {
      isDeleting = false;
      phraseIdx = (phraseIdx + 1) % phrases.length;
      typingSpeed = 500; // Pause before typing new phrase
    }

    setTimeout(type, typingSpeed);
  }

  type();
}

/* ──────────────── Intersection Observer Scroll Reveal ──────────────── */
function initScrollReveal() {
  const reveals = document.querySelectorAll('.reveal');
  const observer = new IntersectionObserver((entries, obs) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('active');
        obs.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.12
  });

  reveals.forEach(el => observer.observe(el));
}

/* ──────────────── Screenshot Showcase Carousel ──────────────── */
function initCarousel() {
  const slides = document.querySelectorAll('.carousel-slide');
  if (slides.length === 0) return;

  let currentIdx = 0;
  let slideInterval = setInterval(nextSlide, 6000);

  function showSlide(index) {
    slides.forEach((slide, i) => {
      slide.classList.toggle('active', i === index);
    });
    currentIdx = index;
  }

  function nextSlide() {
    let nextIdx = (currentIdx + 1) % slides.length;
    showSlide(nextIdx);
  }

  function prevSlide() {
    let prevIdx = (currentIdx - 1 + slides.length) % slides.length;
    showSlide(prevIdx);
  }

  // Handle Controls
  const nextBtn = document.getElementById('carouselNext');
  const prevBtn = document.getElementById('carouselPrev');

  if (nextBtn) {
    nextBtn.addEventListener('click', () => {
      clearInterval(slideInterval);
      nextSlide();
      slideInterval = setInterval(nextSlide, 6000);
    });
  }

  if (prevBtn) {
    prevBtn.addEventListener('click', () => {
      clearInterval(slideInterval);
      prevSlide();
      slideInterval = setInterval(nextSlide, 6000);
    });
  }
}

/* ──────────────── Statistics Counters Animation ──────────────── */
function initCounters() {
  const counterElements = document.querySelectorAll('.counter');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const targetVal = parseFloat(el.getAttribute('data-target'));
        const isFloat = el.getAttribute('data-float') === 'true';
        let count = 0;
        const speed = targetVal / 100;

        const updateCount = () => {
          count += speed;
          if (count < targetVal) {
            el.textContent = isFloat ? count.toFixed(2) : Math.floor(count);
            setTimeout(updateCount, 15);
          } else {
            el.textContent = isFloat ? targetVal.toFixed(2) : targetVal;
          }
        };

        updateCount();
        observer.unobserve(el);
      }
    });
  });

  counterElements.forEach(el => observer.observe(el));
}
