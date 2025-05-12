// Initialize Bootstrap components
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Initialize Feather icons if available
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
    
    // Initialize animation on scroll
    animateOnScroll();
    
    // Add smooth scrolling to all links
    addSmoothScrolling();
});

// Function to animate elements when they come into view
function animateOnScroll() {
    const elements = document.querySelectorAll('.animate-on-scroll');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animated');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1
    });
    
    elements.forEach(element => {
        observer.observe(element);
    });
}

// Function to add smooth scrolling to all links
function addSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
}

// Toggle password visibility
function togglePasswordVisibility(inputId, toggleButtonId) {
    const passwordInput = document.getElementById(inputId);
    const toggleButton = document.getElementById(toggleButtonId);
    
    if (passwordInput && toggleButton) {
        toggleButton.addEventListener('click', function() {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            
            // Toggle icon if using feather icons
            if (typeof feather !== 'undefined') {
                const icon = toggleButton.querySelector('i');
                if (icon) {
                    if (type === 'password') {
                        icon.setAttribute('data-feather', 'eye');
                    } else {
                        icon.setAttribute('data-feather', 'eye-off');
                    }
                    feather.replace();
                }
            }
        });
    }
}

// Dynamic form validation
function validateForm(formId, rules) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        let isValid = true;
        
        // Clear previous error messages
        form.querySelectorAll('.invalid-feedback').forEach(el => el.remove());
        form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
        
        // Check each rule
        for (const fieldId in rules) {
            const field = document.getElementById(fieldId);
            const fieldRules = rules[fieldId];
            
            if (field && fieldRules) {
                // Required validation
                if (fieldRules.required && !field.value.trim()) {
                    showFieldError(field, fieldRules.required);
                    isValid = false;
                }
                
                // Minimum length validation
                if (fieldRules.minLength && field.value.length < fieldRules.minLength.value) {
                    showFieldError(field, fieldRules.minLength.message);
                    isValid = false;
                }
                
                // Maximum length validation
                if (fieldRules.maxLength && field.value.length > fieldRules.maxLength.value) {
                    showFieldError(field, fieldRules.maxLength.message);
                    isValid = false;
                }
                
                // Pattern validation (regex)
                if (fieldRules.pattern && !new RegExp(fieldRules.pattern.value).test(field.value)) {
                    showFieldError(field, fieldRules.pattern.message);
                    isValid = false;
                }
                
                // Email validation
                if (fieldRules.email && field.value && !validateEmail(field.value)) {
                    showFieldError(field, fieldRules.email);
                    isValid = false;
                }
                
                // Match validation (for password confirmation)
                if (fieldRules.match) {
                    const matchField = document.getElementById(fieldRules.match.field);
                    if (matchField && field.value !== matchField.value) {
                        showFieldError(field, fieldRules.match.message);
                        isValid = false;
                    }
                }
                
                // Custom validation function
                if (fieldRules.custom && typeof fieldRules.custom.validate === 'function') {
                    const customValid = fieldRules.custom.validate(field.value);
                    if (!customValid) {
                        showFieldError(field, fieldRules.custom.message);
                        isValid = false;
                    }
                }
            }
        }
        
        if (!isValid) {
            e.preventDefault();
            // Scroll to first error
            const firstError = form.querySelector('.is-invalid');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                firstError.focus();
            }
        }
    });
    
    // Function to show field error
    function showFieldError(field, message) {
        field.classList.add('is-invalid');
        
        const errorMessage = document.createElement('div');
        errorMessage.className = 'invalid-feedback';
        errorMessage.textContent = message;
        
        // Insert after the field
        field.parentNode.insertBefore(errorMessage, field.nextSibling);
    }
    
    // Email validation helper
    function validateEmail(email) {
        const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
        return re.test(String(email).toLowerCase());
    }
}

// Countdown timer utility
function initializeCountdown(endTime, displayElementId, onComplete) {
    const countdownElement = document.getElementById(displayElementId);
    if (!countdownElement) return;
    
    const countdownDate = new Date(endTime).getTime();
    
    // Update the countdown every 1 second
    const x = setInterval(function() {
        // Get current date and time
        const now = new Date().getTime();
        
        // Find the distance between now and the countdown date
        const distance = countdownDate - now;
        
        // Time calculations for days, hours, minutes and seconds
        const days = Math.floor(distance / (1000 * 60 * 60 * 24));
        const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);
        
        // Display the result
        countdownElement.innerHTML = '';
        
        if (days > 0) {
            countdownElement.innerHTML += days + "d ";
        }
        
        countdownElement.innerHTML += String(hours).padStart(2, '0') + "h "
        + String(minutes).padStart(2, '0') + "m " + String(seconds).padStart(2, '0') + "s";
        
        // If the countdown is finished, clear interval and call the completion callback
        if (distance < 0) {
            clearInterval(x);
            countdownElement.innerHTML = "EXPIRED";
            
            if (typeof onComplete === 'function') {
                onComplete();
            }
        }
    }, 1000);
}

// Utility for handling AJAX requests
function ajaxRequest(url, method, data, onSuccess, onError) {
    // Get CSRF token from meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    
    // Create request options
    const options = {
        method: method || 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin' // Include cookies
    };
    
    // Add CSRF token for non-GET requests
    if (method && method.toUpperCase() !== 'GET' && csrfToken) {
        options.headers['X-CSRFToken'] = csrfToken;
    }
    
    // Add body for non-GET requests
    if (method && method.toUpperCase() !== 'GET' && data) {
        options.body = JSON.stringify(data);
    }
    
    // Make the request
    fetch(url, options)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (typeof onSuccess === 'function') {
                onSuccess(data);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            if (typeof onError === 'function') {
                onError(error);
            }
        });
}