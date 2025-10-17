from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
import logging
import os
from dotenv import load_dotenv

from .routers import users
from .routers import products
from .routers import examples
from .routers import auth
from .routers import secure_auth
from .database import engine, Base

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def get_login_html():
    """Return the HTML for the login page."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Python Backend API</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .container {
            background: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
            width: 400px;
            max-width: 90vw;
            display: none; /* Initially hidden while checking session */
        }
        
        .logo {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .logo h1 {
            color: #333;
            font-size: 1.8rem;
            margin-bottom: 0.5rem;
        }
        
        .logo p {
            color: #666;
            font-size: 0.9rem;
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        label {
            display: block;
            margin-bottom: 0.5rem;
            color: #333;
            font-weight: 500;
        }
        
        input[type="email"], input[type="password"] {
            width: 100%;
            padding: 0.75rem;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 1rem;
            transition: border-color 0.3s;
        }
        
        input[type="email"]:focus, input[type="password"]:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn {
            width: 100%;
            padding: 0.75rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 1rem;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .message {
            margin-top: 1rem;
            padding: 0.75rem;
            border-radius: 5px;
            display: none;
        }
        
        .message.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .message.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .links {
            text-align: center;
            margin-top: 1.5rem;
        }
        
        .links a {
            color: #667eea;
            text-decoration: none;
            margin: 0 1rem;
            font-size: 0.9rem;
        }
        
        .links a:hover {
            text-decoration: underline;
        }
        
        .token-display {
            margin-top: 1rem;
            padding: 1rem;
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            display: none;
        }
        
        .token-display h3 {
            color: #28a745;
            margin-bottom: 0.5rem;
        }
        
        .token-value {
            background: #e9ecef;
            padding: 0.5rem;
            border-radius: 3px;
            font-family: monospace;
            font-size: 0.8rem;
            word-break: break-all;
            margin-bottom: 0.5rem;
        }
        
        .copy-btn {
            background: #28a745;
            color: white;
            border: none;
            padding: 0.25rem 0.5rem;
            border-radius: 3px;
            cursor: pointer;
            font-size: 0.8rem;
        }
        
        .loading {
            text-align: center;
            color: white;
            font-size: 1.2em;
            margin-top: 20px;
        }
        
        .loading::after {
            content: '';
            display: inline-block;
            animation: spin 1s linear infinite;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: white;
            margin-left: 10px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div id="loadingIndicator" class="loading">Checking session...</div>
    <div class="container">
        <div class="logo">
            <h1>🔐 Login</h1>
            <p>Python Backend API</p>
        </div>
        
        <form id="loginForm">
            <div class="form-group">
                <label for="email">Email:</label>
                <input type="email" id="email" name="email" required>
            </div>
            
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <button type="submit" class="btn" id="loginBtn">Login</button>
        </form>
        
        <div id="message" class="message"></div>
        
        <div class="links">
            <a href="/docs">API Docs</a>
            <a href="/register">Register</a>
            <a href="/">Home</a>
        </div>
    </div>

    <script>
        let currentToken = '';
        
        // Check for existing session on page load
        window.addEventListener('load', function() {
            checkSession();
        });
        
        async function checkSession() {
            try {
                const response = await fetch('/api/v1/secure-auth/me', {
                    credentials: 'include'  // Include session cookie
                });
                
                if (response.ok) {
                    const userData = await response.json();
                    showUserInfo(userData);
                } else {
                    // No valid session
                    showLoginForm();
                }
            } catch (error) {
                console.log('No active session');
                showLoginForm();
            }
        }
        
        function showUserInfo(userData) {
            const container = document.querySelector('.container');
            container.innerHTML = `
                <div class="logo">
                    <h1>👋 Welcome Back!</h1>
                    <p>Secure Session Active</p>
                </div>
                
                <div class="user-info" style="background: #f8f9fa; padding: 1rem; border-radius: 5px; margin-bottom: 1rem;">
                    <h3>User Information:</h3>
                    <p><strong>Name:</strong> ${userData.name}</p>
                    <p><strong>Email:</strong> ${userData.email}</p>
                    <p><strong>ID:</strong> ${userData.id}</p>
                </div>
                
                <button onclick="logout()" class="btn" style="background: #dc3545;">Logout</button>
                <button onclick="extendSession()" class="btn" style="background: #28a745; margin-top: 0.5rem;">Extend Session</button>
                
                <div class="links">
                    <a href="/docs">API Docs</a>
                    <a href="/">Home</a>
                </div>
            `;
        }
        
        function showLoginForm() {
            // The form is already shown, just ensure it's visible
            const container = document.querySelector('.container');
            if (container) {
                container.style.display = 'block';
            }
        }
        
        // Wait for DOM to be fully loaded before adding event listeners
        document.addEventListener('DOMContentLoaded', function() {
            const loginForm = document.getElementById('loginForm');
            if (loginForm) {
                loginForm.addEventListener('submit', handleLogin);
            }
            
            // Check for existing session on page load
            checkExistingSession();
            
            // Quick fallback: show login form if session check doesn't complete quickly
            setTimeout(() => {
                const loadingIndicator = document.getElementById('loadingIndicator');
                
                if (loadingIndicator && window.getComputedStyle(loadingIndicator).display !== 'none') {
                    console.log('Quick fallback: Showing login form after 800ms');
                    showLoginForm();
                }
            }, 800); // 800ms quick fallback
            
            // Absolute fallback: if loading takes too long, show login form anyway
            setTimeout(() => {
                const loadingIndicator = document.getElementById('loadingIndicator');
                
                if (loadingIndicator && window.getComputedStyle(loadingIndicator).display !== 'none') {
                    console.log('Fallback: Session check took too long, showing login form');
                    showLoginForm();
                }
            }, 2000); // 2 second absolute fallback
        });
        
        async function checkExistingSession() {
            const loadingIndicator = document.getElementById('loadingIndicator');
            const loginForm = document.getElementById('loginForm');
            
            try {
                console.log('Checking for existing session at: /api/v1/secure-auth/me'); // Debug log
                
                // Create AbortController for timeout
                const controller = new AbortController();
                const timeoutId = setTimeout(() => {
                    controller.abort();
                    console.log('Session check aborted due to timeout');
                }, 1500); // 1.5 second timeout
                
                const response = await fetch('/api/v1/secure-auth/me', {
                    method: 'GET',
                    credentials: 'include',  // Include cookies
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId); // Clear timeout if successful
                console.log('Session check response status:', response.status); // Debug log
                
                if (response.ok) {
                    const userData = await response.json();
                    console.log('Found existing session for:', userData.email); // Debug log
                    
                    // Hide loading indicator
                    if (loadingIndicator) {
                        loadingIndicator.style.display = 'none';
                    }
                    
                    // Keep login form hidden
                    if (loginForm) {
                        loginForm.style.display = 'none';
                    }
                    
                    showMessage('Welcome back! Restoring your session...', 'success');
                    
                    // Show session dashboard
                    setTimeout(() => {
                        showSessionDashboard(userData);
                    }, 500);
                } else {
                    console.log('No existing session found, status:', response.status); // Debug log
                    
                    // Hide loading indicator and show login form
                    showLoginForm();
                }
            } catch (error) {
                console.error('Error checking existing session:', error.message);
                
                // Always show login form on any error (timeout, network, etc.)
                showLoginForm();
            }
        }
        
        function showLoginForm() {
            const loadingIndicator = document.getElementById('loadingIndicator');
            const loginForm = document.getElementById('loginForm');
            const sessionDashboard = document.getElementById('sessionDashboard');
            
            // Hide loading indicator
            if (loadingIndicator) {
                loadingIndicator.style.display = 'none';
            }
            
            // Hide session dashboard if it exists
            if (sessionDashboard) {
                sessionDashboard.style.display = 'none';
            }
            
            // Show login form
            if (loginForm) {
                loginForm.style.display = 'block';
            }
            
            // Ensure container is visible
            const container = document.querySelector('.container');
            if (container) {
                container.style.display = 'block';
            }
        }
        
        async function handleLogin(e) {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const loginBtn = document.getElementById('loginBtn');
            
            // Reset displays
            hideMessage();
            
            // Disable button
            loginBtn.disabled = true;
            loginBtn.textContent = 'Logging in...';
            
            try {
                console.log('Attempting login for:', email); // Debug log
                
                const response = await fetch('/api/v1/secure-auth/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        email: email,
                        password: password
                    }),
                    credentials: 'include'  // Important: include cookies
                });
                
                console.log('Login response status:', response.status); // Debug log
                const data = await response.json();
                console.log('Login response data:', data); // Debug log
                
                if (response.ok) {
                    // Success - session-based login
                    showMessage('Login successful! Session created securely on server.', 'success');
                    
                    // Clear form
                    document.getElementById('loginForm').reset();
                    
                    // Show success message and redirect info
                    setTimeout(() => {
                        checkSession();
                    }, 1000);
                } else {
                    // Error
                    showMessage(data.detail || 'Login failed', 'error');
                }
            } catch (error) {
                console.error('Login error:', error); // Debug log
                showMessage('Network error: ' + error.message, 'error');
            } finally {
                // Re-enable button
                loginBtn.disabled = false;
                loginBtn.textContent = 'Login';
            }
        }
        
        function showMessage(text, type) {
            let message = document.getElementById('message');
            if (!message) {
                // Create message div if it doesn't exist
                const container = document.querySelector('.container');
                message = document.createElement('div');
                message.id = 'message';
                message.className = 'message';
                container.appendChild(message);
            }
            message.textContent = text;
            message.className = 'message ' + type;
            message.style.display = 'block';
        }
        
        function hideMessage() {
            const message = document.getElementById('message');
            if (message) {
                message.style.display = 'none';
            }
        }
        
        
        
        async function extendSession() {
            try {
                const response = await fetch('/api/v1/secure-auth/extend-session', {
                    method: 'POST',
                    credentials: 'include'
                });
                
                if (response.ok) {
                    showMessage('Session extended successfully', 'success');
                } else {
                    showMessage('Could not extend session', 'error');
                }
            } catch (error) {
                showMessage('Network error', 'error');
            }
        }
        
        async function checkSession() {
            try {
                const response = await fetch('/api/v1/secure-auth/me', {
                    method: 'GET',
                    credentials: 'include'  // Include cookies
                });
                
                if (response.ok) {
                    const userData = await response.json();
                    showMessage(`Welcome back, ${userData.email}! Session is active.`, 'success');
                    
                    // Show logout option
                    setTimeout(() => {
                        showSessionInfo(userData);
                    }, 1000);
                } else {
                    showMessage('No active session found.', 'error');
                }
            } catch (error) {
                console.error('Session check error:', error);
                showMessage('Session check failed: ' + error.message, 'error');
            }
        }
        
        function showSessionInfo(userData) {
            // Hide login form
            const loginForm = document.getElementById('loginForm');
            if (loginForm) {
                loginForm.style.display = 'none';
            }
            
            // Show dashboard
            showSessionDashboard(userData);
        }
        
        async function showSessionDashboard(userData) {
            const container = document.querySelector('.container');
            let dashboardDiv = document.getElementById('sessionDashboard');
            
            if (!dashboardDiv) {
                dashboardDiv = document.createElement('div');
                dashboardDiv.id = 'sessionDashboard';
                dashboardDiv.className = 'session-dashboard';
                container.appendChild(dashboardDiv);
            }
            
            // Show loading state
            dashboardDiv.innerHTML = `
                <div class="dashboard-header">
                    <h2>Session Dashboard</h2>
                    <button onclick="logout()" class="btn btn-secondary">Logout</button>
                </div>
                <p>Loading session data...</p>
            `;
            dashboardDiv.style.display = 'block';
            
            try {
                // Fetch all user sessions
                const response = await fetch('/api/v1/secure-auth/sessions', {
                    method: 'GET',
                    credentials: 'include'
                });
                
                if (response.ok) {
                    const sessionData = await response.json();
                    renderDashboard(userData, sessionData);
                } else {
                    dashboardDiv.innerHTML = `
                        <div class="dashboard-header">
                            <h2>Session Dashboard</h2>
                            <button onclick="logout()" class="btn btn-secondary">Logout</button>
                        </div>
                        <p class="error">Failed to load session data</p>
                    `;
                }
            } catch (error) {
                console.error('Error loading sessions:', error);
                dashboardDiv.innerHTML = `
                    <div class="dashboard-header">
                        <h2>Session Dashboard</h2>
                        <button onclick="logout()" class="btn btn-secondary">Logout</button>
                    </div>
                    <p class="error">Error loading session data: ${error.message}</p>
                `;
            }
        }
        
        function renderDashboard(userData, sessionData) {
            const dashboardDiv = document.getElementById('sessionDashboard');
            const currentSessionId = document.cookie
                .split('; ')
                .find(row => row.startsWith('session_id='))
                ?.split('=')[1];
            
            dashboardDiv.innerHTML = `
                <div class="dashboard-header">
                    <div>
                        <h2>Welcome, ${userData.email}</h2>
                        <p style="margin: 0; color: #666;">User ID: ${userData.id}</p>
                    </div>
                    <div>
                        <button onclick="refreshDashboard()" class="btn" style="margin-right: 10px;">Refresh</button>
                        <button onclick="logoutAllDevices()" class="btn btn-warning" style="margin-right: 10px;">Logout All Devices</button>
                        <button onclick="logout()" class="btn btn-secondary">Logout</button>
                    </div>
                </div>
                
                <div class="stats">
                    <div class="stat-item">
                        <div class="stat-number">${sessionData.active_sessions}</div>
                        <div class="stat-label">Active Sessions</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${sessionData.sessions.length}</div>
                        <div class="stat-label">Total Sessions</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">1</div>
                        <div class="stat-label">Current Device</div>
                    </div>
                </div>
                
                <h3>Active Sessions</h3>
                <div class="session-list">
                    ${sessionData.sessions.map(session => {
                        const isCurrentSession = session.session_id === currentSessionId;
                        const createdAt = new Date(session.created_at).toLocaleString();
                        const lastAccessed = new Date(session.last_accessed).toLocaleString();
                        const expiresAt = new Date(session.expires_at).toLocaleString();
                        
                        return `
                            <div class="session-item ${isCurrentSession ? 'current-session' : ''}">
                                <div class="session-details">
                                    <div>
                                        <strong>${isCurrentSession ? '🔵 Current Session' : '📱 Other Device'}</strong>
                                        ${isCurrentSession ? ' (This Device)' : ''}
                                    </div>
                                    <div class="session-meta">
                                        <div><strong>Created:</strong> ${createdAt}</div>
                                        <div><strong>Last Active:</strong> ${lastAccessed}</div>
                                        <div><strong>Expires:</strong> ${expiresAt}</div>
                                        <div><strong>Session ID:</strong> ${session.session_id.substring(0, 8)}...</div>
                                    </div>
                                </div>
                                <div class="session-actions">
                                    ${!isCurrentSession ? 
                                        `<button onclick="terminateSession('${session.session_id}')" class="btn btn-danger btn-sm">Terminate</button>` : 
                                        '<span style="color: #007bff; font-weight: bold;">Current</span>'
                                    }
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
                
                <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd;">
                    <h3>Quick Actions</h3>
                    <button onclick="testProtectedEndpoint()" class="btn">Test Protected API</button>
                    <button onclick="extendCurrentSession()" class="btn" style="margin-left: 10px;">Extend Current Session</button>
                </div>
            `;
        }
        
        async function refreshDashboard() {
            try {
                const response = await fetch('/api/v1/secure-auth/me', {
                    method: 'GET',
                    credentials: 'include'
                });
                
                if (response.ok) {
                    const userData = await response.json();
                    showSessionDashboard(userData);
                } else {
                    showMessage('Failed to refresh dashboard', 'error');
                }
            } catch (error) {
                showMessage('Error refreshing dashboard: ' + error.message, 'error');
            }
        }
        
        async function terminateSession(sessionId) {
            if (!confirm('Are you sure you want to terminate this session?')) {
                return;
            }
            
            try {
                // Note: You'll need to add this endpoint to your backend
                const response = await fetch(`/api/v1/secure-auth/sessions/${sessionId}`, {
                    method: 'DELETE',
                    credentials: 'include'
                });
                
                if (response.ok) {
                    showMessage('Session terminated successfully', 'success');
                    refreshDashboard();
                } else {
                    const error = await response.json();
                    showMessage('Failed to terminate session: ' + (error.detail || 'Unknown error'), 'error');
                }
            } catch (error) {
                showMessage('Error terminating session: ' + error.message, 'error');
            }
        }
        
        async function logoutAllDevices() {
            if (!confirm('Are you sure you want to logout from all devices? This will end all your active sessions.')) {
                return;
            }
            
            try {
                // Note: You'll need to add this endpoint to your backend
                const response = await fetch('/api/v1/secure-auth/logout-all', {
                    method: 'POST',
                    credentials: 'include'
                });
                
                if (response.ok) {
                    showMessage('Logged out from all devices successfully!', 'success');
                    setTimeout(() => {
                        location.reload();
                    }, 2000);
                } else {
                    const error = await response.json();
                    showMessage('Failed to logout from all devices: ' + (error.detail || 'Unknown error'), 'error');
                }
            } catch (error) {
                showMessage('Error logging out from all devices: ' + error.message, 'error');
            }
        }
        
        async function extendCurrentSession() {
            try {
                // Note: You'll need to add this endpoint to your backend
                const response = await fetch('/api/v1/secure-auth/extend-session', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        minutes: 30
                    }),
                    credentials: 'include'
                });
                
                if (response.ok) {
                    showMessage('Session extended by 30 minutes', 'success');
                    refreshDashboard();
                } else {
                    const error = await response.json();
                    showMessage('Failed to extend session: ' + (error.detail || 'Unknown error'), 'error');
                }
            } catch (error) {
                showMessage('Error extending session: ' + error.message, 'error');
            }
        }
        
        async function logout() {
            try {
                const response = await fetch('/api/v1/secure-auth/logout', {
                    method: 'POST',
                    credentials: 'include'
                });
                
                if (response.ok) {
                    showMessage('Logged out successfully!', 'success');
                    
                    // Hide dashboard
                    const dashboardDiv = document.getElementById('sessionDashboard');
                    if (dashboardDiv) {
                        dashboardDiv.style.display = 'none';
                    }
                    
                    // Hide any loading indicator
                    const loadingIndicator = document.getElementById('loadingIndicator');
                    if (loadingIndicator) {
                        loadingIndicator.style.display = 'none';
                    }
                    
                    // Show login form again
                    const loginForm = document.getElementById('loginForm');
                    if (loginForm) {
                        loginForm.style.display = 'block';
                        loginForm.reset();
                    }
                    
                    // Clear any messages after a delay
                    setTimeout(() => {
                        hideMessage();
                    }, 3000);
                } else {
                    showMessage('Logout failed', 'error');
                }
            } catch (error) {
                showMessage('Logout error: ' + error.message, 'error');
            }
        }
        
        async function testProtectedEndpoint() {
            try {
                const response = await fetch('/api/v1/users/', {
                    method: 'GET',
                    credentials: 'include'
                });
                
                if (response.ok) {
                    const users = await response.json();
                    showMessage(`Protected API works! Found ${users.length} users.`, 'success');
                } else {
                    const error = await response.json();
                    showMessage(`Protected API failed: ${error.detail}`, 'error');
                }
            } catch (error) {
                showMessage('API test error: ' + error.message, 'error');
            }
        }
    </script>
</body>
</html>
"""

def get_register_html():
    """Return the HTML for the registration page."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Register - Python Backend API</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 2rem 0;
        }
        
        .container {
            background: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
            width: 400px;
            max-width: 90vw;
        }
        
        .logo {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .logo h1 {
            color: #333;
            font-size: 1.8rem;
            margin-bottom: 0.5rem;
        }
        
        .logo p {
            color: #666;
            font-size: 0.9rem;
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        label {
            display: block;
            margin-bottom: 0.5rem;
            color: #333;
            font-weight: 500;
        }
        
        input[type="text"], input[type="email"], input[type="password"], 
        input[type="number"], textarea {
            width: 100%;
            padding: 0.75rem;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 1rem;
            transition: border-color 0.3s;
        }
        
        textarea {
            resize: vertical;
            min-height: 80px;
        }
        
        input:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn {
            width: 100%;
            padding: 0.75rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 1rem;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .message {
            margin-top: 1rem;
            padding: 0.75rem;
            border-radius: 5px;
            display: none;
        }
        
        .message.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .message.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .links {
            text-align: center;
            margin-top: 1.5rem;
        }
        
        .links a {
            color: #667eea;
            text-decoration: none;
            margin: 0 1rem;
            font-size: 0.9rem;
        }
        
        .links a:hover {
            text-decoration: underline;
        }
        
        .optional {
            color: #888;
            font-size: 0.8rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <h1>📝 Register</h1>
            <p>Create your account</p>
        </div>
        
        <form id="registerForm">
            <div class="form-group">
                <label for="name">Full Name:</label>
                <input type="text" id="name" name="name" required>
            </div>
            
            <div class="form-group">
                <label for="email">Email:</label>
                <input type="email" id="email" name="email" required>
            </div>
            
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" required minlength="6">
                <small style="color: #666; font-size: 0.8rem;">Minimum 6 characters</small>
            </div>
            
            <div class="form-group">
                <label for="age">Age <span class="optional">(optional)</span>:</label>
                <input type="number" id="age" name="age" min="0" max="150">
            </div>
            
            <div class="form-group">
                <label for="bio">Bio <span class="optional">(optional)</span>:</label>
                <textarea id="bio" name="bio" placeholder="Tell us about yourself..."></textarea>
            </div>
            
            <button type="submit" class="btn" id="registerBtn">Register</button>
        </form>
        
        <div id="message" class="message"></div>
        
        <div class="links">
            <a href="/login">Login</a>
            <a href="/docs">API Docs</a>
            <a href="/">Home</a>
        </div>
    </div>

    <script>
        document.getElementById('registerForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = {
                name: document.getElementById('name').value,
                email: document.getElementById('email').value,
                password: document.getElementById('password').value,
                age: parseInt(document.getElementById('age').value) || null,
                bio: document.getElementById('bio').value || null
            };
            
            const registerBtn = document.getElementById('registerBtn');
            const message = document.getElementById('message');
            
            // Reset message
            message.style.display = 'none';
            
            // Disable button
            registerBtn.disabled = true;
            registerBtn.textContent = 'Registering...';
            
            try {
                const response = await fetch('/api/v1/auth/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData)
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    // Success
                    showMessage('Registration successful! You can now login.', 'success');
                    document.getElementById('registerForm').reset();
                    
                    // Redirect to login page after 2 seconds
                    setTimeout(() => {
                        window.location.href = '/login';
                    }, 2000);
                } else {
                    // Error
                    showMessage(data.detail || 'Registration failed', 'error');
                }
            } catch (error) {
                showMessage('Network error: ' + error.message, 'error');
            } finally {
                // Re-enable button
                registerBtn.disabled = false;
                registerBtn.textContent = 'Register';
            }
        });
        
        function showMessage(text, type) {
            const message = document.getElementById('message');
            message.textContent = text;
            message.className = 'message ' + type;
            message.style.display = 'block';
        }
    </script>
</body>
</html>
"""

# Create database tables
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.warning(f"Failed to create database tables: {e}")
    logger.info("Continuing without database tables - you may need to set up PostgreSQL")

# Create FastAPI application
app = FastAPI(
    title="Python Backend API",
    description="A RESTful API with PostgreSQL database supporting GET, POST, and PUT operations",
    version="1.0.0",
    docs_url=None,  # Disable default docs to use custom
    redoc_url="/redoc"
)

# Custom OpenAPI schema with session authentication
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Python Backend API",
        version="1.0.0",
        description="A RESTful API with PostgreSQL database, JWT & Session authentication",
        routes=app.routes,
    )
    
    # Add session authentication to the schema
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        },
        "SessionAuth": {
            "type": "apiKey",
            "in": "cookie",
            "name": "session_id",
            "description": "Session-based authentication using HTTP-only cookies"
        },
        "SessionHeader": {
            "type": "apiKey",
            "in": "header",
            "name": "X-Session-ID",
            "description": "Session ID for testing in Swagger UI (use session_id from login response)"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI that supports session authentication."""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
        swagger_ui_parameters={
            "persistAuthorization": True
        }
    )

# Configure CORS
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create static directory if it doesn't exist
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# Mount static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(secure_auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
# app.include_router(examples.router, prefix="/api/v1")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception handler caught: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint to verify API is running."""
    return {
        "status": "healthy",
        "message": "API is running successfully",
        "version": "1.0.0"
    }

# Web Login Page
@app.get("/login", response_class=HTMLResponse, tags=["web"])
async def login_page():
    """Serve the web login page."""
    return get_login_html()

# Web Registration Page
@app.get("/register", response_class=HTMLResponse, tags=["web"])
async def register_page():
    """Serve the web registration page."""
    return get_register_html()

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to Python Backend API",
        "docs": "/docs",
        "login": "/login",
        "redoc": "/redoc",
        "health": "/health",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )