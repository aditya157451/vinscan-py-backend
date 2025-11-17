/* ============================================
   VinScan - Chat Module
   ============================================ */

let conversationState = null;
let clientId = null;
let isTyping = false;

/**
 * Initialize chat interface
 */
async function initChat() {
    clientId = getClientId();
    
    if (!clientId) {
        showToast('Client ID not found. Please login again.', 'error');
        setTimeout(() => window.location.href = '/', 2000);
        return;
    }

    // Check if stakeholders need to be selected
    await loadConversationState();
    
    // Setup message form
    const messageForm = document.getElementById('chat-form');
    if (messageForm) {
        messageForm.addEventListener('submit', handleSendMessage);
    }

    // Setup stakeholder selection
    const stakeholderForm = document.getElementById('stakeholder-form');
    if (stakeholderForm) {
        stakeholderForm.addEventListener('submit', handleStakeholderSelection);
    }

    // Auto-scroll to bottom
    scrollToBottom();
}

/**
 * Load conversation state
 */
async function loadConversationState() {
    try {
        const response = await api.getConversationState(clientId);
        conversationState = response.conversationState;
        
        // Check if stakeholder selection is needed
        if (response.needStakeholderSelection || !conversationState.currentStakeholder) {
            showStakeholderSelection();
        } else {
            hideStakeholderSelection();
            // Load conversation history
            if (conversationState.conversationHistory) {
                displayConversationHistory(conversationState.conversationHistory);
            }
            updateProgress();
        }
    } catch (error) {
        console.error('Error loading conversation state:', error);
        showToast('Failed to load conversation', 'error');
    }
}

/**
 * Show stakeholder selection UI
 */
function showStakeholderSelection() {
    const selectionUI = document.getElementById('stakeholder-selection');
    const chatUI = document.getElementById('chat-interface');
    
    if (selectionUI) {
        selectionUI.style.display = 'block';
    }
    if (chatUI) {
        chatUI.style.display = 'none';
    }

    // Load available stakeholders
    const availableStakeholders = JSON.parse(
        localStorage.getItem('availableStakeholders') || 
        '["CEO", "Marketing Head", "Finance Head", "HR Head", "IT Head"]'
    );

    const container = document.getElementById('stakeholder-checkboxes');
    if (container) {
        container.innerHTML = availableStakeholders.map(stakeholder => `
            <div class="checkbox-item">
                <input type="checkbox" id="stakeholder-${stakeholder}" name="stakeholders" value="${stakeholder}">
                <label for="stakeholder-${stakeholder}">${stakeholder}</label>
            </div>
        `).join('');
    }
}

/**
 * Hide stakeholder selection UI
 */
function hideStakeholderSelection() {
    const selectionUI = document.getElementById('stakeholder-selection');
    const chatUI = document.getElementById('chat-interface');
    
    if (selectionUI) {
        selectionUI.style.display = 'none';
    }
    if (chatUI) {
        chatUI.style.display = 'block';
    }
}

/**
 * Handle stakeholder selection
 */
async function handleStakeholderSelection(event) {
    event.preventDefault();
    
    const form = event.target;
    const checkboxes = form.querySelectorAll('input[type="checkbox"]:checked');
    const otherInput = form.querySelector('#other-stakeholder');
    
    if (checkboxes.length === 0 && (!otherInput || !otherInput.value.trim())) {
        showToast('Please select at least one stakeholder', 'error');
        return;
    }

    const selectedStakeholders = Array.from(checkboxes).map(cb => cb.value);
    const otherStakeholder = otherInput?.value.trim() || null;

    const submitBtn = form.querySelector('button[type="submit"]');
    setLoading(submitBtn, true);

    try {
        await api.selectStakeholders(clientId, selectedStakeholders, otherStakeholder);
        showToast('Stakeholders selected successfully', 'success');
        
        // Reload conversation state
        await loadConversationState();
    } catch (error) {
        console.error('Error selecting stakeholders:', error);
        showToast(error.message || 'Failed to select stakeholders', 'error');
    } finally {
        setLoading(submitBtn, false);
    }
}

/**
 * Handle sending a message
 */
async function handleSendMessage(event) {
    event.preventDefault();
    
    if (isTyping) return;
    
    const form = event.target;
    const input = form.querySelector('#message-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Clear input
    input.value = '';
    
    // Add user message to UI
    addMessage('user', message);
    
    // Show typing indicator
    showTypingIndicator();
    isTyping = true;
    
    try {
        const response = await api.sendMessage(clientId, message);
        
        // Hide typing indicator
        hideTypingIndicator();
        isTyping = false;
        
        // Add assistant response
        if (response.message) {
            addMessage('assistant', response.message);
        }
        
        // Reload conversation state to update progress
        await loadConversationState();
        
        // Check if report generation was triggered
        if (response.message && response.message.includes('report')) {
            showToast('Report generation started! You can view it in the Reports section.', 'success');
        }
        
    } catch (error) {
        console.error('Error sending message:', error);
        hideTypingIndicator();
        isTyping = false;
        showToast(error.message || 'Failed to send message', 'error');
    }
}

/**
 * Add message to chat UI
 */
function addMessage(role, content) {
    const messagesContainer = document.getElementById('chat-messages');
    if (!messagesContainer) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${role}`;
    
    const timestamp = new Date().toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    
    messageDiv.innerHTML = `
        <div class="message-content">${escapeHtml(content)}</div>
        <div class="message-time">${timestamp}</div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

/**
 * Display conversation history
 */
function displayConversationHistory(history) {
    const messagesContainer = document.getElementById('chat-messages');
    if (!messagesContainer) return;
    
    messagesContainer.innerHTML = '';
    
    history.forEach(msg => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message message-${msg.role}`;
        
        const timestamp = msg.timestamp ? 
            formatDate(msg.timestamp, true) : 
            new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
        
        messageDiv.innerHTML = `
            <div class="message-content">${escapeHtml(msg.content)}</div>
            <div class="message-time">${timestamp}</div>
        `;
        
        messagesContainer.appendChild(messageDiv);
    });
    
    scrollToBottom();
}

/**
 * Show typing indicator
 */
function showTypingIndicator() {
    const messagesContainer = document.getElementById('chat-messages');
    if (!messagesContainer) return;
    
    let indicator = document.getElementById('typing-indicator');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'typing-indicator';
        indicator.className = 'message message-assistant typing-indicator';
        indicator.innerHTML = `
            <div class="message-content">
                <span class="typing-dots">
                    <span>.</span><span>.</span><span>.</span>
                </span>
            </div>
        `;
        messagesContainer.appendChild(indicator);
    }
    indicator.style.display = 'block';
    scrollToBottom();
}

/**
 * Hide typing indicator
 */
function hideTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.style.display = 'none';
    }
}

/**
 * Update progress indicators
 */
function updateProgress() {
    if (!conversationState) return;
    
    // Update current stakeholder
    const currentStakeholderEl = document.getElementById('current-stakeholder');
    if (currentStakeholderEl) {
        currentStakeholderEl.textContent = conversationState.currentStakeholder || 'Selecting...';
    }
    
    // Update phase
    const currentPhaseEl = document.getElementById('current-phase');
    if (currentPhaseEl) {
        const phase = conversationState.phase || 'context_setting';
        currentPhaseEl.textContent = phase.replace('_', ' ').toUpperCase();
    }
    
    // Update progress bar
    const progressBar = document.getElementById('progress-bar');
    if (progressBar && conversationState.pendingStakeholders) {
        const total = (conversationState.stakeholdersInterviewed?.length || 0) + 
                     (conversationState.pendingStakeholders?.length || 0);
        const completed = conversationState.stakeholdersInterviewed?.length || 0;
        const percentage = total > 0 ? (completed / total) * 100 : 0;
        progressBar.style.width = `${percentage}%`;
    }
}

/**
 * Scroll chat to bottom
 */
function scrollToBottom() {
    const messagesContainer = document.getElementById('chat-messages');
    if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

// Initialize chat when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initChat);
} else {
    initChat();
}

