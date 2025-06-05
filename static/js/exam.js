// Global variables
let endTime;
let timerInterval;
let warningCount = 0;
let maxWarnings = 50; // Maximum number of warnings before auto-submit
let isFullscreen = false;
let questionCount = 0;
let answeredCount = 0;
let currentQuestion = 1;
let attemptId = null;
let warningUrl = null;
let isSubmitting = false;

// Initialize the exam environment
function initExamEnvironment(attemptIdValue, warningUrlValue) {
    attemptId = attemptIdValue;
    warningUrl = warningUrlValue;
    
    // Set end time from server
    const endTimeElement = document.getElementById('endTime');
    if (endTimeElement) {
        endTime = new Date(endTimeElement.value);
        
        // Start the countdown timer
        startTimer();
    }
    
    // Set up browser focus detection
    setupBrowserFocusDetection();
    
    // Set up fullscreen mode
    setupFullscreenMode();
    
    // Initialize question navigation
    initQuestionNav();
    
    // Set up form submit handling
    setupFormSubmission();
    
    // Set header warning count
    const headerWarningCountElement = document.getElementById('headerWarningCount');
    if (headerWarningCountElement) {
        warningCount = parseInt(headerWarningCountElement.textContent) || 0;
    }
    
    // Update progress bar for initial state
    updateProgress();
}

// Start countdown timer
function startTimer() {
    updateTimer(); // Update immediately
    
    timerInterval = setInterval(() => {
        updateTimer();
    }, 1000);
}

// Update countdown timer
function updateTimer() {
    const now = new Date();
    let diff = endTime - now;
    
    // If time is up
    if (diff <= 0) {
        clearInterval(timerInterval);
        document.getElementById('countdown').innerHTML = '00:00:00';
        // Auto-submit the exam
        autoSubmitExam('Time is up!');
        return;
    }
    
    // Calculate hours, minutes, seconds
    const hours = Math.floor(diff / (1000 * 60 * 60));
    diff -= hours * (1000 * 60 * 60);
    const minutes = Math.floor(diff / (1000 * 60));
    diff -= minutes * (1000 * 60);
    const seconds = Math.floor(diff / 1000);
    
    // Format the time
    const timeString = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    const countdownElement = document.getElementById('countdown');
    
    // Add warning classes for low time
    if (hours === 0) {
        if (minutes <= 5) {
            countdownElement.className = 'countdown-danger';
        } else if (minutes <= 10) {
            countdownElement.className = 'countdown-warning';
        }
    }
    
    countdownElement.innerHTML = timeString;
}

// Set up browser focus detection
function setupBrowserFocusDetection() {
    // Tab change detection
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden') {
            reportWarning();
        }
    });
    
    // Window blur detection
    window.addEventListener('blur', () => {
        if (!isFullscreen) {
            reportWarning();
        }
    });
}

// Report a warning
function reportWarning() {
    // Ignore warnings if form is being submitted
    if (isSubmitting) return;
    
    warningCount++;
    
    // Update UI with warning
    const warningBanner = document.getElementById('warningBanner');
    const warningCountElement = document.getElementById('warningCount');
    const headerWarningCount = document.getElementById('headerWarningCount');
    
    if (warningCountElement) {
        warningCountElement.textContent = warningCount;
    }
    
    if (headerWarningCount) {
        headerWarningCount.textContent = warningCount;
    }
    
    if (warningBanner) {
        warningBanner.style.display = 'block';
        
        // Hide banner after 3 seconds
        setTimeout(() => {
            warningBanner.style.display = 'none';
        }, 3000);
    }
    
    // Send warning to server
    fetch(warningUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCsrfToken(),
        },
        body: 'warning=true',
    });
    
    // Auto-submit if too many warnings
    if (warningCount >= maxWarnings) {
        autoSubmitExam('Too many tab switches or window blurs detected.');
    }
}

// Auto-submit the exam
function autoSubmitExam(reason) {
    if (isSubmitting) return;  // Prevent multiple submits
    isSubmitting = true;
    
    alert(reason + ' Your exam will be submitted automatically.');
    document.getElementById('examForm').submit();
}

// Set up fullscreen mode
function setupFullscreenMode() {
    const fullscreenButton = document.getElementById('returnFullscreen');
    if (fullscreenButton) {
        fullscreenButton.addEventListener('click', toggleFullscreen);
    }
    
    // Enter fullscreen initially
    setTimeout(() => {
        toggleFullscreen();
    }, 1000);
    
    // Listen for fullscreen change
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
    document.addEventListener('mozfullscreenchange', handleFullscreenChange);
    document.addEventListener('MSFullscreenChange', handleFullscreenChange);
}

// Toggle fullscreen mode
function toggleFullscreen() {
    if (!document.fullscreenElement && 
        !document.mozFullScreenElement && 
        !document.webkitFullscreenElement && 
        !document.msFullscreenElement) {
        // Enter fullscreen
        const docElement = document.documentElement;
        if (docElement.requestFullscreen) {
            docElement.requestFullscreen();
        } else if (docElement.mozRequestFullScreen) {
            docElement.mozRequestFullScreen();
        } else if (docElement.webkitRequestFullscreen) {
            docElement.webkitRequestFullscreen();
        } else if (docElement.msRequestFullscreen) {
            docElement.msRequestFullscreen();
        }
    } else {
        // Exit fullscreen
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.mozCancelFullScreen) {
            document.mozCancelFullScreen();
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) {
            document.msExitFullscreen();
        }
    }
}

// Handle fullscreen change
function handleFullscreenChange() {
    isFullscreen = !!document.fullscreenElement || 
                   !!document.mozFullScreenElement || 
                   !!document.webkitFullscreenElement || 
                   !!document.msFullscreenElement;
    
    const fullscreenMessage = document.getElementById('fullscreenMessage');
    
    if (!isFullscreen && fullscreenMessage) {
        fullscreenMessage.style.display = 'block';
    } else if (fullscreenMessage) {
        fullscreenMessage.style.display = 'none';
    }
}

// Initialize question navigation
function initQuestionNav() {
    // Count total questions
    questionCount = document.querySelectorAll('.question-card').length;
    
    // Set up question navigation
    const questionNav = document.getElementById('questionNav');
    if (questionNav) {
        const questionNumbers = questionNav.querySelectorAll('.question-number');
        questionNumbers.forEach(qNum => {
            qNum.addEventListener('click', () => {
                goToQuestion(parseInt(qNum.dataset.question));
            });
        });
    }
    
    // Set up next/previous buttons
    const nextButtons = document.querySelectorAll('.next-question');
    nextButtons.forEach(button => {
        button.addEventListener('click', () => {
            goToQuestion(currentQuestion + 1);
        });
    });
    
    const prevButtons = document.querySelectorAll('.prev-question');
    prevButtons.forEach(button => {
        button.addEventListener('click', () => {
            goToQuestion(currentQuestion - 1);
        });
    });
    
    // Last next button goes to review card
    const lastNextButton = document.querySelector('.question-card:last-child .next-question');
    if (lastNextButton) {
        lastNextButton.textContent = 'Review & Submit';
        lastNextButton.addEventListener('click', showReviewCard);
    }
    
    // Back to questions button
    const backToQuestionsButton = document.querySelector('.back-to-questions');
    if (backToQuestionsButton) {
        backToQuestionsButton.addEventListener('click', () => {
            hideReviewCard();
            goToQuestion(currentQuestion);
        });
    }
    
    // Track answer changes to update progress
    const optionInputs = document.querySelectorAll('.option-checkbox, .option-radio');
    optionInputs.forEach(input => {
        input.addEventListener('change', () => {
            markQuestionAnswered(currentQuestion);
            updateProgress();
        });
    });
    
    // Set up the submit button
    const submitButton = document.getElementById('submitButton');
    if (submitButton) {
        submitButton.addEventListener('click', () => {
            showConfirmSubmitModal();
        });
    }
    
    // Initialize the current question
    markCurrentQuestion(currentQuestion);
}

// Go to a specific question
function goToQuestion(questionNumber) {
    if (questionNumber < 1 || questionNumber > questionCount) return;
    
    // Hide all question cards
    document.querySelectorAll('.question-card').forEach(card => {
        card.style.display = 'none';
    });
    
    // Hide review card
    document.getElementById('review-card').style.display = 'none';
    
    // Show selected question
    document.getElementById(`question-${questionNumber}`).style.display = 'block';
    
    // Update current question
    currentQuestion = questionNumber;
    markCurrentQuestion(questionNumber);
}

// Mark the current question in the navigation
function markCurrentQuestion(questionNumber) {
    // Remove current class from all question numbers
    document.querySelectorAll('.question-number').forEach(qNum => {
        qNum.classList.remove('current');
    });
    
    // Add current class to the current question
    const currentNavItem = document.getElementById(`nav-q-${questionNumber}`);
    if (currentNavItem) {
        currentNavItem.classList.add('current');
    }
}

// Mark a question as answered
function markQuestionAnswered(questionNumber) {
    const questionCard = document.getElementById(`question-${questionNumber}`);
    const navItem = document.getElementById(`nav-q-${questionNumber}`);
    
    if (questionCard && navItem) {
        const isAnswered = checkIfQuestionAnswered(questionCard);
        
        if (isAnswered) {
            navItem.classList.add('answered');
        } else {
            navItem.classList.remove('answered');
        }
    }
    
    // Update the answered count
    countAnsweredQuestions();
}

// Check if a question has been answered
function checkIfQuestionAnswered(questionCard) {
    const radioInputs = questionCard.querySelectorAll('.option-radio:checked');
    const checkboxInputs = questionCard.querySelectorAll('.option-checkbox:checked');
    
    return radioInputs.length > 0 || checkboxInputs.length > 0;
}

// Count answered questions
function countAnsweredQuestions() {
    answeredCount = document.querySelectorAll('.question-number.answered').length;
}

// Show the review card
function showReviewCard() {
    // Hide all question cards
    document.querySelectorAll('.question-card').forEach(card => {
        card.style.display = 'none';
    });
    
    // Show review card
    document.getElementById('review-card').style.display = 'block';
    
    // Update progress again
    updateProgress();
}

// Hide the review card
function hideReviewCard() {
    document.getElementById('review-card').style.display = 'none';
}

// Update progress bar and status
function updateProgress() {
    countAnsweredQuestions();
    
    const progressBar = document.getElementById('progressBar');
    const answeredStatus = document.getElementById('answeredStatus');
    
    if (progressBar && answeredStatus) {
        const progressPercentage = Math.round((answeredCount / questionCount) * 100);
        progressBar.style.width = `${progressPercentage}%`;
        progressBar.setAttribute('aria-valuenow', progressPercentage);
        progressBar.textContent = `${progressPercentage}%`;
        
        answeredStatus.textContent = `You've answered ${answeredCount} out of ${questionCount} questions.`;
    }
}

// Set up form submission
function setupFormSubmission() {
    const examForm = document.getElementById('examForm');
    if (!examForm) return;
    
    const submitModal = new bootstrap.Modal(document.getElementById('submitModal'));
    
    // Confirm submit button
    const confirmSubmitBtn = document.getElementById('confirmSubmit');
    if (confirmSubmitBtn) {
        confirmSubmitBtn.addEventListener('click', () => {
            isSubmitting = true; // Prevent warnings during submission
            examForm.submit();
        });
    }
}

// Show confirmation dialog before submitting
function showConfirmSubmitModal() {
    const submitModal = new bootstrap.Modal(document.getElementById('submitModal'));
    const unansweredWarning = document.getElementById('unansweredWarning');
    
    // Show warning if not all questions are answered
    if (unansweredWarning) {
        if (answeredCount < questionCount) {
            unansweredWarning.style.display = 'block';
        } else {
            unansweredWarning.style.display = 'none';
        }
    }
    
    submitModal.show();
}

// Get CSRF token for AJAX requests
function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}
