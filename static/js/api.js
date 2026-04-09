/* ============================================
   AI Business Interview & Reporting System - API Client
   Centralized API communication
   ============================================ */

class APIClient {
    constructor() {
        // API base URL - adjust if needed
        this.baseURL = window.location.origin;
        this.token = localStorage.getItem('token');
    }

    /**
     * Set authentication token
     */
    setToken(token) {
        this.token = token;
        if (token) {
            localStorage.setItem('token', token);
        } else {
            localStorage.removeItem('token');
        }
    }

    /**
     * Get authentication token
     */
    getToken() {
        return this.token || localStorage.getItem('token');
    }

    /**
     * Clear authentication
     */
    clearAuth() {
        this.token = null;
        localStorage.removeItem('token');
        localStorage.removeItem('clientId');
        localStorage.removeItem('clientInfo');
    }

    /**
     * Build request headers
     */
    getHeaders(includeAuth = true) {
        const headers = {
            'Content-Type': 'application/json',
        };

        if (includeAuth && this.getToken()) {
            headers['Authorization'] = `Bearer ${this.getToken()}`;
        }

        return headers;
    }

    /**
     * Handle API response
     */
    async handleResponse(response) {
        const contentType = response.headers.get('content-type');
        
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            if (!response.ok) {
                throw new Error(text || `HTTP error! status: ${response.status}`);
            }
            return text;
        }

        const data = await response.json();

        if (!response.ok) {
            const error = data.detail || data.message || `HTTP error! status: ${response.status}`;
            throw new Error(error);
        }

        return data;
    }

    /**
     * Make API request
     */
    async request(endpoint, options = {}) {
        const {
            method = 'GET',
            body = null,
            headers = {},
            includeAuth = true,
            ...restOptions
        } = options;

        const url = endpoint.startsWith('http') ? endpoint : `${this.baseURL}${endpoint}`;
        
        const config = {
            method,
            headers: {
                ...this.getHeaders(includeAuth),
                ...headers,
            },
            ...restOptions,
        };

        if (body && method !== 'GET') {
            config.body = typeof body === 'string' ? body : JSON.stringify(body);
        }

        try {
            const response = await fetch(url, config);
            return await this.handleResponse(response);
        } catch (error) {
            console.error('API Request Error:', error);
            
            // Handle authentication errors
            if (error.message.includes('401') || error.message.includes('Unauthorized')) {
                this.clearAuth();
                if (window.location.pathname !== '/') {
                    window.location.href = '/';
                }
            }
            
            throw error;
        }
    }

    /**
     * GET request
     */
    async get(endpoint, options = {}) {
        return this.request(endpoint, { ...options, method: 'GET' });
    }

    /**
     * POST request
     */
    async post(endpoint, data, options = {}) {
        return this.request(endpoint, { ...options, method: 'POST', body: data });
    }

    /**
     * PUT request
     */
    async put(endpoint, data, options = {}) {
        return this.request(endpoint, { ...options, method: 'PUT', body: data });
    }

    /**
     * DELETE request
     */
    async delete(endpoint, options = {}) {
        return this.request(endpoint, { ...options, method: 'DELETE' });
    }

    // ========== Auth Endpoints ==========

    /**
     * Sign up new user
     */
    async signup(userData) {
        const response = await this.post('/api/signup', userData, { includeAuth: false });
        if (response.token) {
            this.setToken(response.token);
            if (response.clientId) {
                localStorage.setItem('clientId', response.clientId);
            }
            if (response.clientInfo) {
                localStorage.setItem('clientInfo', JSON.stringify(response.clientInfo));
            }
        }
        return response;
    }

    /**
     * Login user
     */
    async login(email, password) {
        const response = await this.post('/api/login', { email, password }, { includeAuth: false });
        if (response.token) {
            this.setToken(response.token);
            if (response.clientInfo?.clientId) {
                localStorage.setItem('clientId', response.clientInfo.clientId);
            }
            if (response.clientInfo) {
                localStorage.setItem('clientInfo', JSON.stringify(response.clientInfo));
            }
        }
        return response;
    }

    // ========== User Endpoints ==========

    /**
     * Get user profile
     */
    async getProfile() {
        return this.get('/api/profile');
    }

    /**
     * Update user profile
     */
    async updateProfile(clientId, data) {
        return this.put(`/api/client/${clientId}`, data);
    }

    // ========== Chat Endpoints ==========

    /**
     * Select stakeholders
     */
    async selectStakeholders(clientId, selectedStakeholders, otherStakeholder = null) {
        return this.post('/api/select-stakeholders', {
            clientId,
            selectedStakeholders,
            otherStakeholder
        });
    }

    /**
     * Get conversation state
     */
    async getConversationState(clientId) {
        return this.get(`/api/conversation-state/${clientId}`);
    }

    /**
     * Send chat message
     */
    async sendMessage(clientId, message) {
        return this.post('/api/chat', {
            clientId,
            message
        });
    }

    // ========== Report Endpoints ==========

    /**
     * Get report
     */
    async getReport(clientId) {
        return this.get(`/api/report/${clientId}`);
    }

    /**
     * Generate report
     */
    async generateReport(clientId) {
        return this.post(`/api/report/generate/${clientId}`, {});
    }
}

// Create singleton instance
const api = new APIClient();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
}

