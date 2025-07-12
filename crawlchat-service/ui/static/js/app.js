// CrawlChat - Modern AI Document Analysis Platform

class CrawlChatApp {
    constructor() {
        this.currentSessionId = null;
        this.chatHistory = [];
        this.allSessions = [];
        this.isProcessing = false;
        this.typingIndicator = null;
        this.lastUserMessageTime = 0; // Track when user last sent a message
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeSession();
        this.setupAutoResize();
        this.setupDragAndDrop();
        this.setupAnimations();
        this.initializeUploadStatus();
        this.processCrawlTaskFromUrl();
        this.updateSendButton();
        
        // Debug: Check if buttons are found
        console.log('Button check:', {
            newChatBtn: !!document.getElementById('newChatBtn'),
            crawlerBtn: !!document.getElementById('crawlerBtn'),
            clearAllChatsBtn: !!document.getElementById('clearAllChatsBtn')
        });
        
        // Double requestAnimationFrame for reliable scroll
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                this.scrollToBottom(true);
            });
        });
    }

    setupEventListeners() {
        // Chat input
        const chatInput = document.getElementById('chatInput');
        const sendBtn = document.getElementById('sendBtn');
        
        if (chatInput) {
            chatInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
            
            chatInput.addEventListener('input', () => {
                this.updateSendButton();
            });
        }

        if (sendBtn) {
            sendBtn.addEventListener('click', () => this.sendMessage());
        }

        // File upload
        const fileInput = document.getElementById('fileInput');
        
        if (fileInput) {
            fileInput.addEventListener('change', (e) => this.handleFileUpload(e.target.files));
        }

        // Session management
        const newChatBtn = document.getElementById('newChatBtn');
        const clearAllChatsBtn = document.getElementById('clearAllChatsBtn');
        
        if (newChatBtn) {
            newChatBtn.addEventListener('click', async (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('New chat button clicked');
                const newSessionId = await this.createNewSession();
                if (newSessionId) {
                    // Switch to the new session
                    this.currentSessionId = newSessionId;
                    localStorage.setItem('currentSessionId', newSessionId);
                    await this.loadSession(newSessionId);
                    this.updateUI();
                }
            });
        }

        if (clearAllChatsBtn) {
            clearAllChatsBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('Clear all chats button clicked');
                this.clearAllChats();
            });
        }

        // Theme toggle
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.toggleTheme();
            });
        }

        // Crawler button in header
        const crawlerBtn = document.getElementById('crawlerBtn');
        if (crawlerBtn) {
            console.log('Crawler button found, adding event listener');
            crawlerBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('Crawler button clicked');
                window.location.href = '/crawler';
            });
            
            // Also add a direct onclick handler as backup
            crawlerBtn.onclick = (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('Crawler button onclick triggered');
                window.location.href = '/crawler';
            };
        } else {
            console.error('Crawler button not found!');
        }

        // Scroll event listener for messages container
        const messagesContainer = document.getElementById('chatMessages');
        if (messagesContainer) {
            messagesContainer.addEventListener('scroll', () => {
                // Check if user scrolled to bottom
                const isAtBottom = messagesContainer.scrollHeight - messagesContainer.scrollTop - messagesContainer.clientHeight < 10;
                if (isAtBottom) {
                    this.hideNewMessageIndicator();
                }
            });
        }
    }

    setupAutoResize() {
        const chatInput = document.getElementById('chatInput');
        if (chatInput) {
            chatInput.addEventListener('input', () => {
                chatInput.style.height = 'auto';
                chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
            });
        }
    }

    setupDragAndDrop() {
        const chatInput = document.getElementById('chatInput');
        if (!chatInput) return;

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            chatInput.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            chatInput.addEventListener(eventName, () => {
                chatInput.parentElement.classList.add('dragover');
                // Show upload status area when dragging files
                const uploadStatus = document.getElementById('uploadStatus');
                if (uploadStatus) {
                    uploadStatus.style.display = 'flex';
                    if (uploadStatus.children.length === 0) {
                        this.addUploadStatus('📁 Drop files here to upload...', 'info');
                    }
                }
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            chatInput.addEventListener(eventName, () => {
                chatInput.parentElement.classList.remove('dragover');
                // Remove drop message if no other messages exist
                const uploadStatus = document.getElementById('uploadStatus');
                if (uploadStatus && uploadStatus.children.length === 1) {
                    const firstChild = uploadStatus.firstChild;
                    if (firstChild && firstChild.textContent === '📁 Drop files here to upload...') {
                        this.clearUploadStatus();
                    }
                }
            });
        });

        chatInput.addEventListener('drop', (e) => {
            const files = Array.from(e.dataTransfer.files);
            this.handleFileUpload(files);
        });
    }

    setupAnimations() {
        // Intersection Observer for fade-in animations
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in');
                }
            });
        }, { threshold: 0.1 });

        document.querySelectorAll('.animate-on-scroll').forEach(el => {
            observer.observe(el);
        });
    }

    async initializeSession() {
        try {
            console.log('=== SESSION INITIALIZATION START ===');
            this.currentSessionId = localStorage.getItem('currentSessionId');
            console.log('Current session ID from localStorage:', this.currentSessionId);
            
            // Always try to load all sessions first
            await this.loadAllSessions();
            console.log('Loaded all sessions, count:', this.allSessions?.length || 0);

            // Check if we have a valid current session
            if (this.currentSessionId) {
                console.log('Checking existing session:', this.currentSessionId);
                try {
                    const response = await fetch(`/api/v1/chat/sessions/${this.currentSessionId}`, {
                        headers: this.getAuthHeaders()
                    });
                    console.log('Session check response status:', response.status);
                    if (response.ok) {
                        console.log('Existing session is valid, loading it...');
                        await this.loadSession(this.currentSessionId);
                        this.updateUI();
                        console.log('=== SESSION INITIALIZATION COMPLETE (existing session) ===');
                        return;
                    } else {
                        console.log('Session not found, removing from localStorage');
                        this.currentSessionId = null;
                        localStorage.removeItem('currentSessionId');
                    }
                } catch (error) {
                    console.log('Error checking session, removing from localStorage:', error);
                    this.currentSessionId = null;
                    localStorage.removeItem('currentSessionId');
                }
            }

            // If we get here, we need to find an existing session or create a new one
            if (this.allSessions && this.allSessions.length > 0) {
                // User has existing sessions, load the most recent one
                console.log('User has existing sessions, loading most recent one');
                const mostRecentSession = this.allSessions[0]; // Already sorted by updated_at desc
                this.currentSessionId = mostRecentSession.session_id;
                localStorage.setItem('currentSessionId', this.currentSessionId);
                await this.loadSession(this.currentSessionId);
                this.updateUI();
                console.log('=== SESSION INITIALIZATION COMPLETE (loaded existing session) ===');
            } else {
                // User has no sessions, create a new one
                console.log('User has no sessions, creating new session...');
                const newSessionId = await this.createNewSession(true);
                console.log('New session created with ID:', newSessionId);
                
                if (newSessionId) {
                    await this.loadAllSessions();
                    await this.loadSession(this.currentSessionId);
                    this.updateUI();
                    console.log('=== SESSION INITIALIZATION COMPLETE (new session) ===');
                } else {
                    console.error('Failed to create new session');
                }
            }
        } catch (error) {
            console.error('Failed to initialize session:', error);
        }
    }

    async createNewSession(force = false) {
        console.log('Creating new session...');
        try {
            // Clear any existing notifications first
            this.clearAllNotifications();
            
            // Check if user already has an empty session
            if (!force && this.allSessions && this.allSessions.length > 0) {
                // Find empty sessions (sessions with no messages)
                const emptySessions = this.allSessions.filter(session => 
                    !session.messages || session.messages.length === 0
                );
                
                if (emptySessions.length > 0) {
                    console.log('User already has empty session(s), notifying user');
                    this.showNotification('You already have an empty chat session. Please use that one or clear it first.', 'info');
                    return null;
                }
            }
            
            console.log('Making POST request to /api/v1/chat/sessions');
            const response = await fetch('/api/v1/chat/sessions', {
                method: 'POST',
                headers: this.getAuthHeaders()
            });
            
            console.log('Response status:', response.status);
            console.log('Response headers:', response.headers);
            
            if (response.ok) {
                const data = await response.json();
                console.log('New session created:', data.session_id);
                this.currentSessionId = data.session_id;
                localStorage.setItem('currentSessionId', this.currentSessionId);
                this.chatHistory = [];
                await this.loadSession(this.currentSessionId);
                this.updateUI();
                await this.loadAllSessions();
                // Double requestAnimationFrame for reliable scroll
                requestAnimationFrame(() => {
                    requestAnimationFrame(() => {
                        this.scrollToBottom(true);
                    });
                });
                this.hideStatusBanner();
                // Show notification after a short delay to ensure UI is updated
                setTimeout(() => {
                    this.showNotification('New chat session created', 'success');
                }, 200);
                return data.session_id;
            } else {
                const errorText = await response.text();
                console.error('Failed to create session, response not ok:', response.status, errorText);
                this.showNotification(`Failed to create session: ${response.status}`, 'error');
            }
        } catch (error) {
            console.error('Failed to create new session:', error);
            this.showNotification('Failed to create new session', 'error');
        }
    }

    async loadSession(sessionId) {
        try {
            const response = await fetch(`/api/v1/chat/sessions/${sessionId}/messages`, {
                headers: this.getAuthHeaders()
            });

            if (response.ok) {
                const messages = await response.json();
                this.chatHistory = messages;
                this.updateUI();
            }
        } catch (error) {
            console.error('Failed to load session:', error);
        }
    }

    async loadAllSessions() {
        try {
            const response = await fetch('/api/v1/chat/sessions', {
                headers: this.getAuthHeaders()
            });

            if (response.ok) {
                this.allSessions = await response.json();
                this.updateSessionList();
            }
        } catch (error) {
            console.error('Failed to load sessions:', error);
        }
    }

    async sendMessage() {
        const chatInput = document.getElementById('chatInput');
        const message = chatInput?.value.trim();
        
        if (!message || this.isProcessing) return;

        this.hideWelcomeMessage();
        this.isProcessing = true;
        this.updateSendButton();

        try {
            // Track that user just sent a message
            this.lastUserMessageTime = Date.now();
            
            // Add user message to UI immediately
            this.addMessageToUI('user', message);
            chatInput.value = '';
            chatInput.style.height = 'auto';

            // Show AI thinking message in chat
            this.addMessageToUI('assistant', '💭 AI Thinking...');

            // Send to backend
            const response = await fetch(`/api/v1/chat/sessions/${this.currentSessionId}/chat`, {
                method: 'POST',
                headers: {
                    ...this.getAuthHeaders(),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message })
            });

            if (response.ok) {
                const data = await response.json();
                
                // Remove the "AI Thinking..." message
                this.removeLastMessage();
                
                // Add AI response to UI
                this.addMessageToUI('assistant', data.response);
                
                // Force scroll to bottom after AI response
                setTimeout(() => {
                    this.scrollToBottom(true);
                }, 100);
                
                // Refresh session list
                await this.loadAllSessions();
            } else {
                throw new Error('Failed to send message');
            }
        } catch (error) {
            console.error('Error sending message:', error);
            // Remove the "AI Thinking..." message
            this.removeLastMessage();
            this.addMessageToUI('system', 'Sorry, there was an error processing your message. Please try again.');
            this.showNotification('Failed to send message', 'error');
        } finally {
            this.isProcessing = false;
            this.updateSendButton();
        }
    }

    addMessageToUI(role, content) {
        // Filter out system messages that are upload status or duplicate (defensive)
        if (
            role === 'system' &&
            (
                (content && content.includes('uploaded and processed successfully')) ||
                (content && content.includes('duplicate detected'))
            )
        ) {
            // Don't render in chat stream
            return;
        }
        const messagesContainer = document.getElementById('chatMessages');
        if (!messagesContainer) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        // Add special class for AI thinking message
        if (role === 'assistant' && content === '💭 AI Thinking...') {
            messageDiv.classList.add('ai-thinking');
        }
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        
        // Set appropriate avatar based on role - ChatGPT style
        if (role === 'user') {
            avatar.innerHTML = 'U';
        } else if (role === 'assistant') {
            avatar.innerHTML = 'AI';
        } else if (role === 'system') {
            avatar.innerHTML = '📄';
        } else {
            avatar.innerHTML = 'ℹ️';
        }
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (role === 'assistant') {
            // Format AI response with markdown-like formatting
            messageContent.innerHTML = this.formatMessage(content);
        } else {
            messageContent.textContent = content;
        }
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        messagesContainer.appendChild(messageDiv);
        
        // Add smooth animation
        messageDiv.style.opacity = '0';
        messageDiv.style.transform = 'translateY(20px)';
        requestAnimationFrame(() => {
            messageDiv.style.transition = 'all 0.3s ease';
            messageDiv.style.opacity = '1';
            messageDiv.style.transform = 'translateY(0)';
        });
        
        // Ensure reliable scroll after DOM update with multiple attempts
        this.scrollToBottom(true);
        
        // Additional scroll attempts to handle any timing issues
        setTimeout(() => {
            this.scrollToBottom(true);
        }, 100);
        
        setTimeout(() => {
            this.scrollToBottom(true);
        }, 300);
    }

    formatMessage(content) {
        // Enhanced markdown-like formatting
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code style="background: var(--bg-tertiary); padding: 2px 4px; border-radius: 4px; font-family: monospace;">$1</code>')
            .replace(/\n/g, '<br>');
    }

    showTypingIndicator() {
        const messagesContainer = document.getElementById('chatMessages');
        if (!messagesContainer) return;

        this.typingIndicator = document.createElement('div');
        this.typingIndicator.className = 'message assistant typing-indicator';
        this.typingIndicator.innerHTML = `
            <div class="message-avatar">AI</div>
            <div class="message-content">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        
        messagesContainer.appendChild(this.typingIndicator);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        if (this.typingIndicator) {
            this.typingIndicator.remove();
            this.typingIndicator = null;
        }
    }

    removeLastMessage() {
        const messagesContainer = document.getElementById('chatMessages');
        if (messagesContainer && messagesContainer.lastChild) {
            // Remove the last message element
            messagesContainer.removeChild(messagesContainer.lastChild);
        }
    }

    removeLastSystemMessage() {
        const messagesContainer = document.getElementById('chatMessages');
        if (!messagesContainer) return;
        
        // Find and remove the last system message
        const messages = messagesContainer.querySelectorAll('.message.system');
        if (messages.length > 0) {
            const lastSystemMessage = messages[messages.length - 1];
            lastSystemMessage.remove();
        }
    }

    addUploadStatus(message, type = 'info') {
        const uploadStatus = document.getElementById('uploadStatus');
        if (!uploadStatus) return;

        // Show upload status area when adding messages
        uploadStatus.style.display = 'flex';

        const statusItem = document.createElement('div');
        statusItem.className = `upload-status-item ${type}`;
        statusItem.textContent = message;
        
        uploadStatus.appendChild(statusItem);
        
        // Auto-scroll to bottom
        uploadStatus.scrollTop = uploadStatus.scrollHeight;
        
        // Add clear button if this is a success or info message and no clear button exists
        if ((type === 'success' || type === 'info') && !uploadStatus.querySelector('.clear-upload-status-btn')) {
            this.addClearUploadStatusButton();
        }
    }

    removeLastUploadStatus() {
        const uploadStatus = document.getElementById('uploadStatus');
        if (uploadStatus && uploadStatus.lastChild) {
            uploadStatus.removeChild(uploadStatus.lastChild);
        }
    }

    clearUploadStatus() {
        const uploadStatus = document.getElementById('uploadStatus');
        if (uploadStatus) {
            uploadStatus.innerHTML = '';
            // Hide upload status area when empty
            uploadStatus.style.display = 'none';
        }
    }

    clearProcessingMessagesOnly() {
        const uploadStatus = document.getElementById('uploadStatus');
        if (uploadStatus) {
            // Remove only processing messages, keep success and error messages
            const processingItems = uploadStatus.querySelectorAll('.upload-status-item.processing');
            processingItems.forEach(item => item.remove());
        }
    }

    addClearUploadStatusButton() {
        const uploadStatus = document.getElementById('uploadStatus');
        if (!uploadStatus || uploadStatus.children.length === 0) return;

        // Check if clear button already exists
        if (uploadStatus.querySelector('.clear-upload-status-btn')) return;

        const clearBtn = document.createElement('button');
        clearBtn.className = 'clear-upload-status-btn';
        clearBtn.innerHTML = '🗑️ Clear';
        clearBtn.title = 'Clear upload status messages';
        clearBtn.onclick = () => this.clearUploadStatus();
        
        uploadStatus.appendChild(clearBtn);
    }

    initializeUploadStatus() {
        const uploadStatus = document.getElementById('uploadStatus');
        if (uploadStatus) {
            // Ensure upload status is hidden initially
            uploadStatus.style.display = 'none';
        }
    }

    scrollToBottom(force = false) {
        const messagesContainer = document.getElementById('chatMessages');
        if (!messagesContainer) return;

        // If force is true, always scroll to bottom
        if (force) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
            this.hideNewMessageIndicator();
            return;
        }

        // Check if user recently sent a message (within last 10 seconds)
        const recentlySentMessage = (Date.now() - this.lastUserMessageTime) < 10000;
        
        // Check if user is near the bottom (within 200px for more generous auto-scroll)
        const isNearBottom = messagesContainer.scrollHeight - messagesContainer.scrollTop - messagesContainer.clientHeight < 200;
        
        // Auto-scroll if user is near the bottom OR if they recently sent a message
        if (isNearBottom || recentlySentMessage) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
            this.hideNewMessageIndicator();
        } else {
            // Show indicator that new messages are available
            this.showNewMessageIndicator();
        }
    }

    showNewMessageIndicator() {
        let indicator = document.getElementById('newMessageIndicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'newMessageIndicator';
            indicator.className = 'new-message-indicator';
            indicator.innerHTML = `
                <button onclick="app.scrollToBottom(true)">
                    <span>↓</span>
                    <span>New message</span>
                </button>
            `;
            document.body.appendChild(indicator);
        }
        indicator.style.display = 'block';
    }

    hideNewMessageIndicator() {
        const indicator = document.getElementById('newMessageIndicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }

    // Add these new methods for processing status
    addProcessingStatus(message, type = 'info') {
        const processingStatus = document.getElementById('processingStatus');
        if (!processingStatus) return;
        
        // Show the processing status list
        processingStatus.classList.add('show');
        
        const statusItem = document.createElement('div');
        statusItem.className = `processing-status-item ${type}`;
        statusItem.textContent = message;
        processingStatus.appendChild(statusItem);
        
        // Auto-scroll to bottom
        processingStatus.scrollTop = processingStatus.scrollHeight;
    }

    clearProcessingStatus() {
        const processingStatus = document.getElementById('processingStatus');
        if (processingStatus) {
            processingStatus.innerHTML = '';
            processingStatus.classList.remove('show');
        }
    }

    updateLastProcessingStatus(message, type = 'info') {
        const processingStatus = document.getElementById('processingStatus');
        if (!processingStatus || !processingStatus.lastChild) return;
        
        const lastItem = processingStatus.lastChild;
        lastItem.textContent = message;
        lastItem.className = `processing-status-item ${type}`;
    }

    // Status banner methods
    showStatusBanner(message, type = 'info', duration = null) {
        const banner = document.getElementById('statusBanner');
        if (!banner) return;
        this.clearAllNotifications();
        banner.textContent = message;
        banner.classList.remove('hidden'); // Always show
        banner.className = `w-full max-w-2xl mx-auto mb-2 px-4 py-2 rounded text-center font-medium ` +
            (type === 'success' ? 'bg-green-100 text-green-800 border border-green-300' :
            type === 'error' ? 'bg-red-100 text-red-800 border border-red-300' :
            'bg-blue-100 text-blue-800 border border-blue-300');
        banner.style.zIndex = '9998';
        
        // Clear any existing timeout
        clearTimeout(this._statusBannerTimeout);
        
        // Only set timeout if duration is provided and greater than 0
        if (duration !== null && duration > 0) {
            this._statusBannerTimeout = setTimeout(() => { banner.classList.add('hidden'); }, duration);
        }
    }
    hideStatusBanner() {
        const banner = document.getElementById('statusBanner');
        if (banner) {
            banner.classList.add('hidden');
            console.log('Status banner hidden');
        }
    }

    // --- Permanent Top-Left Status Notification Methods ---
    addMainStatus(message, type = 'success') {
        const mainStatus = document.getElementById('mainStatus');
        if (!mainStatus) return;
        // Prevent duplicate messages
        if ([...mainStatus.children].some(child => child.textContent.includes(message))) return;
        const item = document.createElement('div');
        item.className = 'main-status-item' + (type === 'error' ? ' error' : type === 'warning' ? ' warning' : '');
        item.textContent = message;
        // Add close button
        const closeBtn = document.createElement('button');
        closeBtn.className = 'close-btn';
        closeBtn.innerHTML = '&times;';
        closeBtn.onclick = () => item.remove();
        item.appendChild(closeBtn);
        mainStatus.appendChild(item);
    }
    clearAllMainStatus() {
        const mainStatus = document.getElementById('mainStatus');
        if (mainStatus) mainStatus.innerHTML = '';
    }

    clearAllNotifications() {
        const notifications = document.querySelectorAll('.notification');
        notifications.forEach(notification => {
            notification.remove();
        });
    }

    async handleFileUpload(files) {
        if (!files || files.length === 0) return;
        if (!this.currentSessionId) {
            this.showStatusBanner('Please create a chat session first', 'error', 4000);
            return;
        }
        this.hideWelcomeMessage();
        
        // Show all file names in the status banner
        const fileNames = Array.from(files).map(f => `"${f.name}"`).join(', ');
        this.showStatusBanner(`📄 Uploading and processing ${fileNames} with AWS Textract...`, 'info', 0);
        
        try {
            const uploadBtn = document.querySelector('.upload-btn');
            if (uploadBtn) {
                uploadBtn.style.opacity = '0.5';
                uploadBtn.style.pointerEvents = 'none';
            }
            
            for (const file of files) {
                // Show individual file processing status
                this.updateLastProcessingStatus(`🔍 Processing "${file.name}" with AWS Textract...`, 'info');
                
                try {
                    const result = await this.uploadFile(file);
                    
                    // Show success message with extraction method
                    const extractionMethod = result.extraction_method || 'AWS Textract';
                    const contentLength = result.content_length || 0;
                    
                    this.addMainStatus(
                        `✅ Document "${file.name}" processed successfully using ${extractionMethod}` +
                        (contentLength > 0 ? ` (${contentLength} characters extracted)` : ''),
                        'success'
                    );
                    
                } catch (fileError) {
                    console.error(`Failed to process ${file.name}:`, fileError);
                    this.addMainStatus(`❌ Failed to process "${file.name}": ${fileError.message}`, 'error');
                }
            }
            
            if (files.length > 1) {
                this.addMainStatus(`✅ ${files.length} documents processed with AWS Textract`, 'success');
            }
            
            await this.loadAllSessions();
            // Refresh page usage after successful upload
            this.fetchPageUsage();
            
        } catch (error) {
            console.error('Upload failed:', error);
            this.hideStatusBanner();
            this.addMainStatus(`❌ File upload failed: ${error.message}`, 'error');
        } finally {
            const uploadBtn = document.querySelector('.upload-btn');
            if (uploadBtn) {
                uploadBtn.style.opacity = '1';
                uploadBtn.style.pointerEvents = 'auto';
            }
            this.hideStatusBanner();
        }
    }

    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`/api/v1/chat/sessions/${this.currentSessionId}/documents`, {
            method: 'POST',
            headers: this.getAuthHeaders(),
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Upload failed');
        }

        return await response.json();
    }

    async uploadFileBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = async () => {
                try {
                    const base64Content = reader.result.split(',')[1]; // Remove data URL prefix
                    const requestData = {
                        file_content: base64Content,
                        filename: file.name,
                        content_type: file.type
                    };

                    const response = await fetch(`/api/v1/chat/sessions/${this.currentSessionId}/documents/base64`, {
                        method: 'POST',
                        headers: {
                            ...this.getAuthHeaders(),
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(requestData)
                    });

                    if (!response.ok) {
                        const errorData = await response.json().catch(() => ({}));
                        throw new Error(errorData.detail || 'Upload failed');
                    }

                    resolve(await response.json());
                } catch (error) {
                    reject(error);
                }
            };
            reader.onerror = () => reject(new Error('Failed to read file'));
            reader.readAsDataURL(file);
        });
    }

    updateUI() {
        console.log('Updating UI...');
        this.updateChatDisplay();
        this.updateSessionInfo();
        console.log('UI update complete');
    }

    updateChatDisplay() {
        const messagesContainer = document.getElementById('chatMessages');
        if (!messagesContainer) return;

        messagesContainer.innerHTML = '';
        // Clear main status area
        const mainStatus = document.getElementById('mainStatus');
        if (mainStatus) mainStatus.innerHTML = '';
        
        if (this.chatHistory.length === 0) {
            this.showWelcomeMessage();
        } else {
            this.chatHistory.forEach(msg => {
                if (msg.role === 'system') {
                    // Filter out duplicate detected system messages
                    if (msg.content && msg.content.includes('duplicate detected')) {
                        return;
                    }
                    this.addMainStatus(msg.content, 'info');
                } else {
                    this.addMessageToUI(msg.role, msg.content);
                }
            });
        }
        // Double requestAnimationFrame for reliable scroll
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                this.scrollToBottom(true);
            });
        });
    }

    showWelcomeMessage() {
        const messagesContainer = document.getElementById('chatMessages');
        if (!messagesContainer) return;

        const welcomeDiv = document.createElement('div');
        welcomeDiv.className = 'welcome-message';
        welcomeDiv.innerHTML = `
            <div class="welcome-content">
                <h2>How can I help you today?</h2>
                <p>I'm here to help you analyze documents and answer questions using AWS Textract. You can:</p>
                <div class="welcome-features">
                    <div class="feature">
                        <div class="feature-icon">📄</div>
                        <div class="feature-text">
                            <h4>Upload Documents</h4>
                            <p>Upload PDF, images, DOC, DOCX, or TXT files for AI-powered text extraction</p>
                        </div>
                    </div>
                    <div class="feature">
                        <div class="feature-icon">🔍</div>
                        <div class="feature-text">
                            <h4>AWS Textract Processing</h4>
                            <p>Advanced OCR and document analysis for scanned documents and images</p>
                        </div>
                    </div>
                    <div class="feature">
                        <div class="feature-icon">🕷️</div>
                        <div class="feature-text">
                            <h4>Web Crawling</h4>
                            <p>Crawl websites to gather content for analysis</p>
                        </div>
                    </div>
                    <div class="feature">
                        <div class="feature-icon">💬</div>
                        <div class="feature-text">
                            <h4>Ask Questions</h4>
                            <p>Ask me anything about your uploaded documents</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        messagesContainer.appendChild(welcomeDiv);
    }

    updateSessionInfo() {
        const sessionInfo = document.getElementById('sessionInfo');
        if (sessionInfo) {
            const session = this.allSessions.find(s => s.session_id === this.currentSessionId);
            if (session) {
                sessionInfo.innerHTML = `
                    <div class="session-meta">
                        <span class="session-date">${new Date(session.created_at).toLocaleDateString()}</span>
                        <span class="session-docs">${session.document_count || 0} documents</span>
                    </div>
                `;
            }
        }
    }

    updateSessionList() {
        const sessionList = document.getElementById('sessionList');
        if (!sessionList) return;

        sessionList.innerHTML = '';
        
        this.allSessions.forEach(session => {
            const sessionItem = document.createElement('div');
            sessionItem.className = `session-item ${session.session_id === this.currentSessionId ? 'active' : ''}`;
            sessionItem.innerHTML = `
                <div class="session-preview">
                    <div class="session-title">Chat ${new Date(session.created_at).toLocaleDateString()}</div>
                    <div class="session-meta">${session.document_count || 0} docs</div>
                </div>
                <button class="session-delete" onclick="app.deleteSession('${session.session_id}')">×</button>
            `;
            
            sessionItem.addEventListener('click', () => this.switchSession(session.session_id));
            sessionList.appendChild(sessionItem);
        });
    }

    async switchSession(sessionId) {
        this.currentSessionId = sessionId;
        localStorage.setItem('currentSessionId', sessionId);
        await this.loadSession(sessionId);
        this.updateUI();
        // Double requestAnimationFrame for reliable scroll
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                this.scrollToBottom(true);
            });
        });
        this.hideStatusBanner();
    }

    async deleteSession(sessionId) {
        if (!confirm('Are you sure you want to delete this chat session?')) return;

        try {
            const response = await fetch(`/api/v1/chat/sessions/${sessionId}`, {
                method: 'DELETE',
                headers: this.getAuthHeaders()
            });

            if (response.ok) {
                if (sessionId === this.currentSessionId) {
                    await this.createNewSession();
                }
                await this.loadAllSessions();
                this.showNotification('Session deleted', 'success');
            }
        } catch (error) {
            console.error('Failed to delete session:', error);
            this.showNotification('Failed to delete session', 'error');
        }
    }

    async clearAllChats() {
        if (!confirm('Are you sure you want to clear all chat history? This action cannot be undone.')) return;
        try {
            // Clear any existing notifications first
            this.clearAllNotifications();
            
            console.log('Clearing all sessions:', this.allSessions?.length || 0);
            
            // Delete all sessions
            for (const session of this.allSessions || []) {
                console.log('Deleting session:', session.session_id);
                const response = await fetch(`/api/v1/chat/sessions/${session.session_id}`, {
                    method: 'DELETE',
                    headers: this.getAuthHeaders()
                });
                
                if (!response.ok) {
                    console.error('Failed to delete session:', session.session_id, response.status);
                }
            }
            
            // Clear local state
            this.currentSessionId = null;
            localStorage.removeItem('currentSessionId');
            this.chatHistory = [];
            this.allSessions = [];
            
            // Reload sessions to confirm deletion
            await this.loadAllSessions();
            
            // Create a new session if none exist after deletion
            if (!this.allSessions || this.allSessions.length === 0) {
                console.log('No sessions left, creating new session');
                const newSessionId = await this.createNewSession(true);
                if (newSessionId) {
                    this.currentSessionId = newSessionId;
                    await this.loadAllSessions();
                    await this.loadSession(this.currentSessionId);
                }
            }
            
            this.updateUI();
            
            setTimeout(() => {
                this.showNotification('All chats cleared and new session created', 'success');
            }, 100);
            this.clearAllMainStatus();
        } catch (error) {
            console.error('Failed to clear all chats:', error);
            this.showNotification('Failed to clear chats', 'error');
        }
    }

    updateSendButton() {
        const sendBtn = document.getElementById('sendBtn');
        const chatInput = document.getElementById('chatInput');
        if (sendBtn && chatInput) {
            const hasText = chatInput.value.trim().length > 0;
            sendBtn.disabled = this.isProcessing || !hasText;
            
            if (this.isProcessing) {
                sendBtn.innerHTML = `
                    <div class="loading"></div>
                `;
            } else {
                sendBtn.innerHTML = `
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M22 2L11 13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                `;
            }
        }
    }

    showNotification(message, type = 'info') {
        // Remove any existing notifications first
        const existingNotifications = document.querySelectorAll('.notification');
        existingNotifications.forEach(notification => {
            notification.remove();
        });

        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Ensure notification appears above other elements
        notification.style.zIndex = '9999';
        
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    toggleTheme() {
        document.body.classList.toggle('dark-theme');
        const isDark = document.body.classList.contains('dark-theme');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    }

    getAuthHeaders() {
        return {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        };
    }

    fetchPageUsage() {
        const token = localStorage.getItem('access_token');
        if (!token) return;
        
        fetch('/api/v1/documents/page-usage', {
            headers: { 'Authorization': `Bearer ${token}` }
        })
        .then(res => res.json())
        .then(data => {
            const pageUsageElement = document.getElementById('pageUsage');
            if (pageUsageElement && data && typeof data.total_pages !== 'undefined' && typeof data.page_limit !== 'undefined') {
                pageUsageElement.textContent = `Usage: ${data.total_pages} / ${data.page_limit} pages`;
            }
        })
        .catch(error => {
            console.error('Error fetching page usage:', error);
        });
    }

    async processCrawlTaskFromUrl() {
        const urlParams = new URLSearchParams(window.location.search);
        const crawlTaskId = urlParams.get('crawl_task');
        if (crawlTaskId) {
            console.log('Crawl task detected:', crawlTaskId);
            
            // Ensure we have a valid session first
            if (!this.currentSessionId) {
                console.log('No session found, creating new session for crawl task...');
                const newSessionId = await this.createNewSession(true);
                if (!newSessionId) {
                    console.error('Failed to create new session for crawl task');
                    this.addMainStatus('❌ Failed to create session for crawled documents', 'error');
                    return;
                }
                this.currentSessionId = newSessionId;
            }
            
            // Show processing banner
            this.showStatusBanner('📄 Linking crawled documents to chat session...', 'info', 0);
            try {
                const response = await fetch(`/api/v1/chat/sessions/${this.currentSessionId}/crawl-documents`, {
                    method: 'POST',
                    headers: {
                        ...this.getAuthHeaders(),
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ crawl_task_id: crawlTaskId })
                });
                if (response.ok) {
                    const responseData = await response.json();
                    
                    // Check if the backend process completed quickly (documents already processed)
                    if (responseData.total_documents && responseData.total_documents > 0) {
                        // Backend completed quickly, show immediate success
                        this.hideStatusBanner();
                        this.addMainStatus(`📄 Crawled documents linked to chat session. ${responseData.total_documents} documents are ready for analysis.`, 'success');
                    } else {
                        // Backend is still processing, show ongoing status
                        this.showStatusBanner('🔄 Documents are being processed in the background...', 'info', 0);
                        this.addMainStatus('📄 Crawled documents linked to chat session. Documents are being processed in the background...', 'info');
                        
                        // Since background service is disabled, show processing for a reasonable time then complete
                        setTimeout(() => {
                            this.hideStatusBanner();
                            this.addMainStatus('✅ Documents linked and processed successfully! You can now ask questions about the documents.', 'success');
                        }, 15000); // Wait 15 seconds to simulate processing time
                    }
                    
                    await this.loadAllSessions();
                    // Refresh page usage after successful crawl document processing
                    this.fetchPageUsage();
                    // Remove the param from the URL
                    window.history.replaceState({}, document.title, window.location.pathname);
                } else {
                    throw new Error('Failed to link crawled documents');
                }
            } catch (error) {
                console.error('Error processing crawl task:', error);
                this.hideStatusBanner();
                this.addMainStatus('❌ Failed to link crawled documents', 'error');
            }
        }
    }

    // Polling method removed since background service is disabled
    // Document processing status is now handled with a simple timeout

    updateDocumentProcessingStatus(message, type = 'info') {
        // Find and update the existing status message about document processing
        const mainStatus = document.getElementById('mainStatus');
        if (!mainStatus) return;
        
        // Find the document processing status message
        const statusItems = mainStatus.querySelectorAll('.main-status-item');
        for (const item of statusItems) {
            if (item.textContent.includes('Crawled documents linked') || 
                item.textContent.includes('Documents are being processed') ||
                item.textContent.includes('All documents processed')) {
                item.textContent = message;
                item.className = 'main-status-item' + (type === 'error' ? ' error' : type === 'warning' ? ' warning' : '');
                // Add close button back
                const closeBtn = document.createElement('button');
                closeBtn.className = 'close-btn';
                closeBtn.innerHTML = '&times;';
                closeBtn.onclick = () => item.remove();
                item.appendChild(closeBtn);
                break;
            }
        }
    }

    hideWelcomeMessage() {
        const messagesContainer = document.getElementById('chatMessages');
        if (!messagesContainer) return;
        const welcomeDiv = messagesContainer.querySelector('.welcome-message');
        if (welcomeDiv) welcomeDiv.remove();
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new CrawlChatApp();
    // For debugging: add a test button to hide the status banner
    window.testHideStatusBanner = function() {
        if (window.app && typeof window.app.hideStatusBanner === 'function') {
            window.app.hideStatusBanner();
            console.log('Called app.hideStatusBanner() from test button');
        } else {
            console.log('app or hideStatusBanner not available');
        }
    };
});

// Add CSS for additional components
const additionalStyles = `
    .typing-indicator .typing-dots {
        display: flex;
        gap: 4px;
        align-items: center;
    }

    .typing-indicator .typing-dots span {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--text-muted);
        animation: typing 1.4s infinite ease-in-out;
    }

    .typing-indicator .typing-dots span:nth-child(1) { animation-delay: -0.32s; }
    .typing-indicator .typing-dots span:nth-child(2) { animation-delay: -0.16s; }

    @keyframes typing {
        0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
        40% { transform: scale(1); opacity: 1; }
    }

    .main-status-item.warning {
        background: #fef3c7;
        color: #92400e;
        border-left: 4px solid #f59e0b;
    }

    .welcome-message {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
        text-align: center;
    }

    .welcome-content {
        max-width: 400px;
    }

    .welcome-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
    }

    .welcome-features {
        display: flex;
        gap: 1rem;
        margin-top: 2rem;
        justify-content: center;
    }

    .feature {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.875rem;
        color: var(--text-secondary);
    }

    .feature-icon {
        font-size: 1.5rem;
    }

    .notification {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: var(--radius-md);
        color: white;
        font-weight: 500;
        z-index: 1000;
        transform: translateX(100%);
        transition: transform 0.3s ease;
    }

    .notification.show {
        transform: translateX(0);
    }

    .notification-success {
        background: var(--secondary-color);
    }

    .notification-error {
        background: var(--danger-color);
    }

    .notification-info {
        background: var(--primary-color);
    }

    .session-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.75rem;
        border-radius: var(--radius-md);
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .session-item:hover {
        background: var(--bg-tertiary);
    }

    .session-item.active {
        background: var(--primary-color);
        color: white;
    }

    .session-delete {
        background: none;
        border: none;
        color: inherit;
        cursor: pointer;
        font-size: 1.25rem;
        opacity: 0.7;
        transition: opacity 0.2s ease;
    }

    .session-delete:hover {
        opacity: 1;
    }

    .uploading {
        opacity: 0.7;
        pointer-events: none;
    }

    .fade-in {
        animation: fadeIn 0.6s ease forwards;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
`;

// Inject additional styles
const styleSheet = document.createElement('style');
styleSheet.textContent = additionalStyles;
document.head.appendChild(styleSheet); 