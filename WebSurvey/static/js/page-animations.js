// Page Animations and Interactions
document.addEventListener('DOMContentLoaded', function() {

    // ===== HEADER SCROLL ANIMATION =====
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        let lastScroll = 0;

        window.addEventListener('scroll', function() {
            const currentScroll = window.pageYOffset;

            // Add shadow on scroll
            if (currentScroll > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }

            lastScroll = currentScroll;
        });
    }

    // ===== SMOOTH SCROLL FOR ANCHOR LINKS =====
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#' && href !== '') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });

    // ===== PARALLAX EFFECT FOR HERO SECTIONS =====
    const heroSections = document.querySelectorAll('section[style*="background"]');
    window.addEventListener('scroll', function() {
        heroSections.forEach(section => {
            const scrolled = window.pageYOffset;
            const rate = scrolled * 0.3;
            section.style.transform = `translateY(${rate}px)`;
        });
    });

    // ===== ANIMATED COUNTER FOR NUMBERS =====
    function animateCounter(element, start, end, duration) {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            element.textContent = Math.floor(progress * (end - start) + start);
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }

    // Trigger counter animation when in viewport
    const observerOptions = {
        threshold: 0.5,
        rootMargin: '0px'
    };

    const counterObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const counter = entry.target;
                const endValue = parseInt(counter.getAttribute('data-count')) || 0;
                animateCounter(counter, 0, endValue, 2000);
                counterObserver.unobserve(counter);
            }
        });
    }, observerOptions);

    document.querySelectorAll('[data-count]').forEach(counter => {
        counterObserver.observe(counter);
    });

    // ===== CARD TILT EFFECT ON MOUSE MOVE =====
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mousemove', function(e) {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            const centerX = rect.width / 2;
            const centerY = rect.height / 2;

            const rotateX = (y - centerY) / 10;
            const rotateY = (centerX - x) / 10;

            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(10px)`;
        });

        card.addEventListener('mouseleave', function() {
            card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateZ(0)';
        });
    });

    // ===== FADE IN ELEMENTS ON SCROLL =====
    const fadeElements = document.querySelectorAll('.fade-in-scroll');
    const fadeObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1 });

    fadeElements.forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(30px)';
        element.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        fadeObserver.observe(element);
    });

    // ===== BUTTON RIPPLE EFFECT =====
    document.querySelectorAll('.btn').forEach(button => {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;

            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple-effect');

            this.appendChild(ripple);

            setTimeout(() => ripple.remove(), 600);
        });
    });

    // ===== TYPING ANIMATION FOR HERO TEXT =====
    const typeElements = document.querySelectorAll('[data-type]');
    typeElements.forEach(element => {
        const text = element.textContent;
        const speed = parseInt(element.getAttribute('data-type-speed')) || 50;
        element.textContent = '';
        element.style.opacity = '1';

        let i = 0;
        const typeWriter = () => {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
                setTimeout(typeWriter, speed);
            }
        };

        // Start typing when element is in view
        const typeObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    typeWriter();
                    typeObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });

        typeObserver.observe(element);
    });

    // ===== IMAGE LAZY LOAD WITH ANIMATION =====
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.add('loaded');
                imageObserver.unobserve(img);
            }
        });
    });

    images.forEach(img => imageObserver.observe(img));

    // ===== PROGRESS BAR ANIMATION =====
    const progressBars = document.querySelectorAll('[data-progress]');
    const progressObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const bar = entry.target;
                const progress = bar.getAttribute('data-progress');
                bar.style.width = progress + '%';
                progressObserver.unobserve(bar);
            }
        });
    }, { threshold: 0.5 });

    progressBars.forEach(bar => {
        bar.style.width = '0%';
        bar.style.transition = 'width 1.5s ease';
        progressObserver.observe(bar);
    });

    // ===== STAGGER ANIMATION FOR LISTS =====
    const staggerContainers = document.querySelectorAll('[data-stagger]');
    staggerContainers.forEach(container => {
        const children = container.children;
        const staggerObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    Array.from(children).forEach((child, index) => {
                        setTimeout(() => {
                            child.classList.add('stagger-item');
                        }, index * 100);
                    });
                    staggerObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.2 });

        staggerObserver.observe(container);
    });

    // ===== CURSOR TRAIL EFFECT (SUBTLE) =====
    let cursorTrail = [];
    const trailLength = 5;

    document.addEventListener('mousemove', function(e) {
        cursorTrail.push({ x: e.clientX, y: e.clientY, time: Date.now() });

        if (cursorTrail.length > trailLength) {
            cursorTrail.shift();
        }
    });

    // ===== FORM VALIDATION ANIMATIONS =====
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');

        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                if (this.value) {
                    this.classList.add('has-value');
                } else {
                    this.classList.remove('has-value');
                }
            });

            // Shake on error
            input.addEventListener('invalid', function() {
                this.classList.add('shake');
                setTimeout(() => this.classList.remove('shake'), 500);
            });
        });
    });

    // ===== HOVER SOUND EFFECT (OPTIONAL - SUBTLE FEEDBACK) =====
    // Uncomment if you want to add sound feedback
    /*
    const hoverSound = new Audio('/static/sounds/hover.mp3');
    document.querySelectorAll('.btn, .nav-link').forEach(element => {
        element.addEventListener('mouseenter', () => {
            hoverSound.currentTime = 0;
            hoverSound.volume = 0.1;
            hoverSound.play().catch(e => console.log('Sound play prevented'));
        });
    });
    */

    console.log('✨ Page animations loaded successfully!');
});

// ===== UTILITY: Add shake animation class =====
const style = document.createElement('style');
style.textContent = `
    .shake {
        animation: shake 0.5s;
    }
    
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
        20%, 40%, 60%, 80% { transform: translateX(5px); }
    }
    
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

