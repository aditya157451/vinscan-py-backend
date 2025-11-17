/* ============================================
   VinScan - Authentication Module
   ============================================ */

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
    return !!api.getToken();
}

/**
 * Get current user info from localStorage
 */
function getCurrentUser() {
    const clientInfo = localStorage.getItem('clientInfo');
    if (clientInfo) {
        try {
            return JSON.parse(clientInfo);
        } catch (e) {
            return null;
        }
    }
    return null;
}

/**
 * Get client ID from localStorage
 */
function getClientId() {
    return localStorage.getItem('clientId');
}

/**
 * Require authentication - redirect to login if not authenticated
 */
function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = '/';
        return false;
    }
    return true;
}

/**
 * Handle login form submission
 */
async function handleLogin(event) {
    event.preventDefault();
    
    const form = event.target;
    const email = form.querySelector('#login-email').value.trim();
    const password = form.querySelector('#login-password').value;
    const submitBtn = form.querySelector('button[type="submit"]');
    
    // Validation
    if (!email || !password) {
        showToast('Please fill in all fields', 'error');
        return;
    }
    
    if (!validateEmail(email)) {
        showToast('Please enter a valid email address', 'error');
        return;
    }
    
    setLoading(submitBtn, true);
    
    try {
        const response = await api.login(email, password);
        showToast('Login successful!', 'success');
        
        // Redirect to dashboard
        setTimeout(() => {
            window.location.href = '/dashboard';
        }, 500);
    } catch (error) {
        console.error('Login error:', error);
        showToast(error.message || 'Login failed. Please check your credentials.', 'error');
    } finally {
        setLoading(submitBtn, false);
    }
}

/**
 * Handle signup form submission
 */
async function handleSignup(event) {
    event.preventDefault();
    
    const form = event.target;
    const name = form.querySelector('#signup-name').value.trim();
    const email = form.querySelector('#signup-email').value.trim();
    const password = form.querySelector('#signup-password').value;
    const position = form.querySelector('#signup-position')?.value.trim() || '';
    const websiteUrl = form.querySelector('#signup-website')?.value.trim() || '';
    const company = form.querySelector('#signup-company')?.value.trim() || '';
    const submitBtn = form.querySelector('button[type="submit"]');
    
    // Validation
    if (!name || !email || !password) {
        showToast('Please fill in all required fields', 'error');
        return;
    }
    
    if (!validateEmail(email)) {
        showToast('Please enter a valid email address', 'error');
        return;
    }
    
    const passwordValidation = validatePassword(password);
    if (!passwordValidation.valid) {
        showToast(passwordValidation.errors[0], 'error');
        return;
    }
    
    if (websiteUrl) {
        const urlValidation = validateUrl(websiteUrl);
        if (!urlValidation.valid) {
            showToast(urlValidation.error, 'error');
            return;
        }
    }
    
    setLoading(submitBtn, true);
    
    try {
        const userData = {
            name,
            email,
            password,
            position: position && position.trim() ? position.trim() : null,
            websiteUrl: websiteUrl && websiteUrl.trim() ? websiteUrl.trim() : null,
            company: company && company.trim() ? company.trim() : null
        };
        
        const response = await api.signup(userData);
        showToast('Account created successfully!', 'success');
        
        // Store available stakeholders if provided
        if (response.availableStakeholders) {
            localStorage.setItem('availableStakeholders', JSON.stringify(response.availableStakeholders));
        }
        
        // Redirect to dashboard
        setTimeout(() => {
            window.location.href = '/dashboard';
        }, 500);
    } catch (error) {
        console.error('Signup error:', error);
        showToast(error.message || 'Signup failed. Please try again.', 'error');
    } finally {
        setLoading(submitBtn, false);
    }
}

/**
 * Handle logout
 */
function handleLogout() {
    api.clearAuth();
    showToast('Logged out successfully', 'info');
    window.location.href = '/';
}

/**
 * Initialize auth forms when DOM is ready
 */
function initAuth() {
    // Login form
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    // Signup form
    const signupForm = document.getElementById('signup-form');
    if (signupForm) {
        signupForm.addEventListener('submit', handleSignup);
    }
    
    // Logout button
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
    
    // Toggle between login and signup
    const toggleLinks = document.querySelectorAll('.auth-toggle');
    toggleLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const container = document.querySelector('.auth-container');
            if (container) {
                container.classList.toggle('show-signup');
            }
        });
    });
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAuth);
} else {
    initAuth();
}

