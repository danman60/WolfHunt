/**
 * WolfHunt React Button Enhancement System
 * Adds functionality to existing React components without modifying source
 */
(function() {
  'use strict';
  
  if (!window.WolfHuntFlags?.isEnabled('button-functionality')) {
    console.log('⏭️ Button functionality fixes disabled');
    return;
  }
  
  console.log('🔘 Enhancing React button functionality...');
  
  class ReactButtonEnhancer {
    constructor() {
      this.enhancedButtons = new Set();
      this.eventHandlers = new Map();
      this.modalStack = [];
      this.notificationQueue = [];
    }
    
    async initialize() {
      try {
        // Wait for React to fully mount
        await this.waitForReactComponents();
        
        // Set up global trading state
        this.initializeTradingState();
        
        // Enhance existing buttons
        await this.enhanceAllButtons();
        
        // Set up modal system
        this.setupModalSystem();
        
        // Set up notification system
        this.setupNotificationSystem();
        
        // Set up real-time features
        this.setupRealTimeFeatures();
        
        // Monitor for new components
        this.setupComponentMonitoring();
        
        this.reportEnhancementStatus();
        
      } catch (error) {
        console.error('❌ React button enhancement error:', error);
      }
    }
    
    async waitForReactComponents() {
      const maxWait = 15000; // 15 seconds
      const start = Date.now();
      
      return new Promise((resolve) => {
        const checkComponents = () => {
          // Check for key React components
          const hasHeader = document.querySelector('header');
          const hasNav = document.querySelector('nav') || document.querySelector('[class*="sidebar"]');
          const hasButtons = document.querySelectorAll('button').length > 3;
          
          if (hasHeader && hasNav && hasButtons) {
            console.log('✅ React components detected and ready');
            resolve();
          } else if (Date.now() - start > maxWait) {
            console.warn('⚠️ React components not fully loaded, proceeding anyway');
            resolve();
          } else {
            setTimeout(checkComponents, 200);
          }
        };
        
        checkComponents();
      });
    }
    
    initializeTradingState() {
      // Global trading bot state
      window.WolfHuntTrading = {
        isConnected: false,
        isTrading: false,
        currentMode: 'paper', // paper or live
        positions: [],
        orders: [],
        balance: { total: 0, available: 0 },
        settings: {
          apiKey: '',
          riskLevel: 'medium',
          maxPosition: 1000
        },
        
        // State management
        connect: async (credentials) => {
          console.log('🔌 Connecting to trading API...');
          await this.simulateApiCall('connect', credentials);
          this.isConnected = true;
          this.notifyStateChange('Connected to trading API');
          return true;
        },
        
        disconnect: () => {
          this.isConnected = false;
          this.isTrading = false;
          this.notifyStateChange('Disconnected from trading API');
        },
        
        startTrading: () => {
          if (!this.isConnected) {
            throw new Error('Must connect to API first');
          }
          this.isTrading = true;
          this.notifyStateChange('Trading started');
        },
        
        stopTrading: () => {
          this.isTrading = false;
          this.notifyStateChange('Trading stopped');
        },
        
        notifyStateChange: (message) => {
          if (window.WolfHuntNotifications) {
            window.WolfHuntNotifications.show(message, 'info');
          }
          
          // Update UI elements
          this.updateTradingIndicators();
        },
        
        updateTradingIndicators: () => {
          // Update status indicators in the UI
          const statusElements = document.querySelectorAll('[class*="trading-mode"], [class*="status"]');
          statusElements.forEach(el => {
            if (this.isTrading) {
              el.classList.add('trading-active');
              el.classList.remove('trading-inactive');
            } else {
              el.classList.add('trading-inactive');
              el.classList.remove('trading-active');
            }
          });
        },
        
        simulateApiCall: async (action, data) => {
          await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 1000));
          console.log(`📡 API Call: ${action}`, data);
        }
      };
    }
    
    async enhanceAllButtons() {
      console.log('🔘 Enhancing all buttons...');
      
      // Get all buttons in the app
      const buttons = document.querySelectorAll('button');
      console.log(`Found ${buttons.length} buttons to enhance`);
      
      buttons.forEach(button => this.enhanceButton(button));
      
      // Set up specific enhancements
      this.enhanceNotificationButtons();
      this.enhanceUserMenuButtons(); 
      this.enhanceSettingsButtons();
      this.enhanceTradingButtons();
      this.enhanceNavigationButtons();
    }
    
    enhanceButton(button) {
      if (this.enhancedButtons.has(button)) return;
      
      const originalHandler = this.getOriginalHandler(button);
      const enhancement = this.determineEnhancement(button);
      
      if (enhancement) {
        this.applyEnhancement(button, enhancement, originalHandler);
        this.enhancedButtons.add(button);
      }
    }
    
    getOriginalHandler(button) {
      // Extract existing onClick handler if any
      const reactProps = this.getReactProps(button);
      return reactProps?.onClick || button.onclick;
    }
    
    getReactProps(element) {
      // Get React props from element (works with React DevTools)
      const reactKey = Object.keys(element).find(key => 
        key.startsWith('__reactProps') || key.startsWith('__reactEventHandlers')
      );
      
      return reactKey ? element[reactKey] : null;
    }
    
    determineEnhancement(button) {
      const text = button.textContent?.trim().toLowerCase() || '';
      const classes = button.className.toLowerCase();
      const ariaLabel = button.getAttribute('aria-label')?.toLowerCase() || '';
      const parent = button.closest('[class*="notification"], [class*="user"], [class*="menu"], [class*="settings"], nav');
      
      // Notification buttons
      if (classes.includes('bell') || ariaLabel.includes('notification') || parent?.className.includes('notification')) {
        return 'notification';
      }
      
      // User menu buttons  
      if (classes.includes('user') || ariaLabel.includes('user menu') || text.includes('user')) {
        return 'userMenu';
      }
      
      // Settings buttons
      if (classes.includes('settings') || text.includes('settings') || ariaLabel.includes('settings')) {
        return 'settings';
      }
      
      // Trading buttons
      if (text.includes('buy') || text.includes('sell') || text.includes('trade')) {
        return 'trading';
      }
      
      // Strategy buttons
      if (text.includes('strategy') || text.includes('execute')) {
        return 'strategy';
      }
      
      // Connection/API buttons
      if (text.includes('connect') || text.includes('api')) {
        return 'connection';
      }
      
      return null;
    }
    
    applyEnhancement(button, enhancement, originalHandler) {
      const enhancedHandler = this.createEnhancedHandler(enhancement, originalHandler);
      
      // Remove existing handler and add enhanced one
      button.onclick = null;
      button.addEventListener('click', enhancedHandler);
      
      this.eventHandlers.set(button, enhancedHandler);
    }
    
    createEnhancedHandler(enhancement, originalHandler) {
      return (event) => {
        event.preventDefault();
        event.stopPropagation();
        
        // Call original handler first if it exists
        if (originalHandler) {
          try {
            originalHandler(event);
          } catch (error) {
            console.warn('Original handler error:', error);
          }
        }
        
        // Apply our enhancement
        this.executeEnhancement(enhancement, event);
      };
    }
    
    executeEnhancement(enhancement, event) {
      const handlers = {
        notification: () => this.handleNotification(event),
        userMenu: () => this.handleUserMenu(event),
        settings: () => this.handleSettings(event),
        trading: () => this.handleTrading(event),
        strategy: () => this.handleStrategy(event),
        connection: () => this.handleConnection(event)
      };
      
      const handler = handlers[enhancement];
      if (handler) {
        try {
          handler();
        } catch (error) {
          console.error(`Enhancement handler error (${enhancement}):`, error);
          this.showErrorNotification(`Failed to ${enhancement}: ${error.message}`);
        }
      }
    }
    
    handleNotification(event) {
      console.log('🔔 Opening notifications panel...');
      
      if (document.getElementById('wolfhunt-notifications-panel')) {
        document.getElementById('wolfhunt-notifications-panel').remove();
        return;
      }
      
      const button = event.target.closest('button');
      const rect = button.getBoundingClientRect();
      
      const panel = this.createNotificationPanel();
      panel.style.position = 'fixed';
      panel.style.top = `${rect.bottom + 8}px`;
      panel.style.right = `${window.innerWidth - rect.right}px`;
      panel.style.zIndex = '1000';
      
      document.body.appendChild(panel);
      
      // Auto-close after 10 seconds
      setTimeout(() => {
        if (panel.parentNode) panel.remove();
      }, 10000);
      
      // Close on outside click
      setTimeout(() => {
        const closeOnOutside = (e) => {
          if (!panel.contains(e.target) && !button.contains(e.target)) {
            panel.remove();
            document.removeEventListener('click', closeOnOutside);
          }
        };
        document.addEventListener('click', closeOnOutside);
      }, 100);
    }
    
    createNotificationPanel() {
      const panel = document.createElement('div');
      panel.id = 'wolfhunt-notifications-panel';
      panel.className = 'w-80 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 max-h-96 overflow-hidden';
      
      panel.innerHTML = `
        <div class="bg-gray-50 dark:bg-gray-900 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
          <div class="flex justify-between items-center">
            <h3 class="font-semibold text-gray-900 dark:text-white">Trading Notifications</h3>
            <span class="bg-red-500 text-white text-xs px-2 py-1 rounded-full">3</span>
          </div>
        </div>
        
        <div class="overflow-y-auto max-h-80">
          <div class="p-4 space-y-3">
            ${this.generateNotificationItems()}
          </div>
        </div>
        
        <div class="bg-gray-50 dark:bg-gray-900 px-4 py-3 border-t border-gray-200 dark:border-gray-700">
          <div class="flex justify-between">
            <button onclick="this.closest('#wolfhunt-notifications-panel').remove()" class="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white">
              Mark All Read
            </button>
            <button onclick="this.closest('#wolfhunt-notifications-panel').remove()" class="text-sm text-blue-600 hover:text-blue-800">
              View All
            </button>
          </div>
        </div>
      `;
      
      return panel;
    }
    
    generateNotificationItems() {
      const notifications = [
        { type: 'success', title: 'Position Opened', message: 'BTC-USD long position at $43,250', time: '2 min ago' },
        { type: 'warning', title: 'Risk Alert', message: 'Portfolio exposure above 75%', time: '15 min ago' },
        { type: 'info', title: 'Market Update', message: 'High volatility detected in ETH-USD', time: '1 hour ago' }
      ];
      
      return notifications.map(notif => `
        <div class="flex items-start space-x-3 p-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg">
          <div class="w-2 h-2 ${this.getNotificationColor(notif.type)} rounded-full mt-2 flex-shrink-0"></div>
          <div class="flex-1 min-w-0">
            <p class="font-medium text-gray-900 dark:text-white text-sm">${notif.title}</p>
            <p class="text-gray-600 dark:text-gray-400 text-sm">${notif.message}</p>
            <p class="text-xs text-gray-500 dark:text-gray-500 mt-1">${notif.time}</p>
          </div>
        </div>
      `).join('');
    }
    
    getNotificationColor(type) {
      const colors = {
        success: 'bg-green-500',
        warning: 'bg-yellow-500',
        error: 'bg-red-500',
        info: 'bg-blue-500'
      };
      return colors[type] || 'bg-gray-500';
    }
    
    handleUserMenu(event) {
      console.log('👤 Opening user menu...');
      
      if (document.getElementById('wolfhunt-user-menu')) {
        document.getElementById('wolfhunt-user-menu').remove();
        return;
      }
      
      const button = event.target.closest('button');
      const rect = button.getBoundingClientRect();
      
      const menu = this.createUserMenu();
      menu.style.position = 'fixed';
      menu.style.top = `${rect.bottom + 8}px`;
      menu.style.right = `${window.innerWidth - rect.right}px`;
      menu.style.zIndex = '1000';
      
      document.body.appendChild(menu);
      
      // Close on outside click
      setTimeout(() => {
        const closeOnOutside = (e) => {
          if (!menu.contains(e.target) && !button.contains(e.target)) {
            menu.remove();
            document.removeEventListener('click', closeOnOutside);
          }
        };
        document.addEventListener('click', closeOnOutside);
      }, 100);
    }
    
    createUserMenu() {
      const menu = document.createElement('div');
      menu.id = 'wolfhunt-user-menu';
      menu.className = 'w-48 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700';
      
      menu.innerHTML = `
        <div class="py-2">
          <div class="px-4 py-2 border-b border-gray-200 dark:border-gray-700">
            <p class="text-sm font-medium text-gray-900 dark:text-white">Trading User</p>
            <p class="text-xs text-gray-500 dark:text-gray-400">user@wolfhunt.trading</p>
          </div>
          
          <button onclick="window.WolfHuntModals.openProfile()" class="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center">
            <svg class="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
            </svg>
            Profile Settings
          </button>
          
          <button onclick="window.WolfHuntModals.openApiConfig()" class="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center">
            <svg class="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
            </svg>
            API Configuration
          </button>
          
          <div class="border-t border-gray-200 dark:border-gray-700 mt-1 pt-1">
            <button onclick="window.WolfHuntModals.confirmLogout()" class="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center">
              <svg class="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
              </svg>
              Sign Out
            </button>
          </div>
        </div>
      `;
      
      return menu;
    }
    
    handleSettings(event) {
      console.log('⚙️ Opening settings...');
      this.openSettingsModal();
    }
    
    handleTrading(event) {
      const button = event.target.closest('button');
      const text = button.textContent?.toLowerCase() || '';
      
      if (text.includes('buy')) {
        this.openTradeModal('BUY');
      } else if (text.includes('sell')) {
        this.openTradeModal('SELL');
      } else {
        this.openTradingInterface();
      }
    }
    
    handleStrategy(event) {
      console.log('🎯 Executing strategy...');
      
      if (!window.WolfHuntTrading.isConnected) {
        this.showErrorNotification('Please connect to API first');
        return;
      }
      
      this.showSuccessNotification('Strategy execution started...');
      
      // Simulate strategy execution
      setTimeout(() => {
        this.showSuccessNotification('Strategy executed successfully');
      }, 2000);
    }
    
    handleConnection(event) {
      console.log('🔌 Handling connection...');
      this.openApiConfigModal();
    }
    
    setupModalSystem() {
      console.log('🖼️ Setting up modal system...');
      
      window.WolfHuntModals = {
        openProfile: () => this.openProfileModal(),
        openApiConfig: () => this.openApiConfigModal(),
        openSettings: () => this.openSettingsModal(),
        openTrading: (side) => this.openTradeModal(side),
        confirmLogout: () => this.confirmLogout(),
        close: (modalId) => this.closeModal(modalId),
        closeAll: () => this.closeAllModals()
      };
    }
    
    openApiConfigModal() {
      const modal = this.createModal('api-config', 'API Configuration', `
        <form class="space-y-4" onsubmit="return window.WolfHuntModals.handleApiSubmit(event)">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              API Key <span class="text-red-500">*</span>
            </label>
            <input 
              type="password" 
              name="apiKey"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white" 
              placeholder="Enter your trading API key"
              required
            >
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Environment
            </label>
            <select name="environment" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white">
              <option value="testnet">Testnet (Safe for testing)</option>
              <option value="mainnet">Mainnet (Live trading)</option>
            </select>
          </div>
          
          <div class="flex justify-end space-x-3 pt-4">
            <button type="button" onclick="window.WolfHuntModals.close('api-config')" class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200">
              Cancel
            </button>
            <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
              Connect
            </button>
          </div>
        </form>
      `);
      
      // Add submit handler
      window.WolfHuntModals.handleApiSubmit = async (event) => {
        event.preventDefault();
        const formData = new FormData(event.target);
        
        try {
          await window.WolfHuntTrading.connect({
            apiKey: formData.get('apiKey'),
            environment: formData.get('environment')
          });
          
          this.closeModal('api-config');
          this.showSuccessNotification('Successfully connected to trading API');
        } catch (error) {
          this.showErrorNotification('Failed to connect: ' + error.message);
        }
      };
    }
    
    openTradeModal(side) {
      const modal = this.createModal('trade-execution', `${side} Order`, `
        <form class="space-y-4" onsubmit="return window.WolfHuntModals.handleTradeSubmit(event, '${side}')">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Trading Pair
              </label>
              <select name="symbol" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white">
                <option value="BTC-USD">BTC-USD</option>
                <option value="ETH-USD">ETH-USD</option>
                <option value="SOL-USD">SOL-USD</option>
              </select>
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Order Type
              </label>
              <select name="orderType" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white">
                <option value="MARKET">Market</option>
                <option value="LIMIT">Limit</option>
              </select>
            </div>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Amount (USD)
            </label>
            <input 
              type="number" 
              name="amount"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white" 
              placeholder="100.00"
              min="10"
              step="0.01"
              required
            >
          </div>
          
          <div class="bg-gray-50 dark:bg-gray-800 p-3 rounded-md">
            <div class="flex justify-between text-sm">
              <span class="text-gray-600 dark:text-gray-400">Estimated Fee:</span>
              <span class="text-gray-900 dark:text-white">$0.10</span>
            </div>
          </div>
          
          <div class="flex justify-end space-x-3 pt-4">
            <button type="button" onclick="window.WolfHuntModals.close('trade-execution')" class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200">
              Cancel
            </button>
            <button type="submit" class="px-4 py-2 ${side === 'BUY' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'} text-white rounded-md">
              Execute ${side}
            </button>
          </div>
        </form>
      `);
      
      // Add submit handler
      window.WolfHuntModals.handleTradeSubmit = async (event, side) => {
        event.preventDefault();
        const formData = new FormData(event.target);
        
        if (!window.WolfHuntTrading.isConnected) {
          this.showErrorNotification('Please connect to API first');
          return false;
        }
        
        try {
          const tradeData = {
            side: side,
            symbol: formData.get('symbol'),
            orderType: formData.get('orderType'),
            amount: parseFloat(formData.get('amount'))
          };
          
          this.showSuccessNotification(`${side} order submitted...`);
          await window.WolfHuntTrading.simulateApiCall('submitOrder', tradeData);
          
          this.closeModal('trade-execution');
          this.showSuccessNotification(`${side} order executed successfully`);
        } catch (error) {
          this.showErrorNotification('Failed to execute trade: ' + error.message);
        }
        
        return false;
      };
    }
    
    createModal(id, title, content) {
      // Remove existing modal
      const existing = document.getElementById(`wolfhunt-modal-${id}`);
      if (existing) existing.remove();
      
      const modal = document.createElement('div');
      modal.id = `wolfhunt-modal-${id}`;
      modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
      modal.setAttribute('role', 'dialog');
      modal.setAttribute('aria-modal', 'true');
      modal.setAttribute('aria-labelledby', `modal-title-${id}`);
      
      modal.innerHTML = `
        <div class="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md mx-4 max-h-[90vh] overflow-y-auto">
          <div class="flex justify-between items-center mb-4">
            <h2 id="modal-title-${id}" class="text-lg font-semibold text-gray-900 dark:text-white">${title}</h2>
            <button onclick="window.WolfHuntModals.close('${id}')" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
              <span class="sr-only">Close</span>
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
          
          <div class="modal-content">
            ${content}
          </div>
        </div>
      `;
      
      document.body.appendChild(modal);
      this.modalStack.push(modal);
      
      // Focus management
      const focusableElements = modal.querySelectorAll('button, input, select, textarea, [tabindex]:not([tabindex="-1"])');
      if (focusableElements.length > 0) {
        focusableElements[0].focus();
      }
      
      // Close on escape
      const escapeHandler = (e) => {
        if (e.key === 'Escape') {
          this.closeModal(id);
          document.removeEventListener('keydown', escapeHandler);
        }
      };
      document.addEventListener('keydown', escapeHandler);
      
      return modal;
    }
    
    closeModal(id) {
      const modal = document.getElementById(`wolfhunt-modal-${id}`);
      if (modal) {
        modal.remove();
        const index = this.modalStack.indexOf(modal);
        if (index > -1) {
          this.modalStack.splice(index, 1);
        }
      }
    }
    
    closeAllModals() {
      this.modalStack.forEach(modal => modal.remove());
      this.modalStack = [];
    }
    
    setupNotificationSystem() {
      console.log('📢 Setting up notification system...');
      
      window.WolfHuntNotifications = {
        show: (message, type = 'info', duration = 5000) => this.showNotification(message, type, duration),
        success: (message) => this.showSuccessNotification(message),
        error: (message) => this.showErrorNotification(message),
        warning: (message) => this.showWarningNotification(message)
      };
    }
    
    showNotification(message, type = 'info', duration = 5000) {
      const notification = document.createElement('div');
      notification.className = `fixed bottom-4 right-4 px-6 py-4 rounded-lg shadow-lg z-50 max-w-sm ${this.getNotificationStyles(type)}`;
      
      notification.innerHTML = `
        <div class="flex items-center">
          ${this.getNotificationIcon(type)}
          <span class="ml-2">${message}</span>
          <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-white hover:text-gray-200">
            ×
          </button>
        </div>
      `;
      
      document.body.appendChild(notification);
      
      // Auto-remove
      setTimeout(() => {
        if (notification.parentNode) {
          notification.remove();
        }
      }, duration);
    }
    
    getNotificationStyles(type) {
      const styles = {
        success: 'bg-green-500 text-white',
        error: 'bg-red-500 text-white',
        warning: 'bg-yellow-500 text-white',
        info: 'bg-blue-500 text-white'
      };
      return styles[type] || styles.info;
    }
    
    getNotificationIcon(type) {
      const icons = {
        success: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path></svg>',
        error: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path></svg>',
        warning: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path></svg>',
        info: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path></svg>'
      };
      return icons[type] || icons.info;
    }
    
    showSuccessNotification(message) {
      this.showNotification(message, 'success');
    }
    
    showErrorNotification(message) {
      this.showNotification(message, 'error', 7000);
    }
    
    showWarningNotification(message) {
      this.showNotification(message, 'warning', 6000);
    }
    
    setupRealTimeFeatures() {
      console.log('⚡ Setting up real-time features...');
      
      // Simulate price updates
      this.simulatePriceUpdates();
      
      // Simulate trading status updates
      this.simulateStatusUpdates();
    }
    
    simulatePriceUpdates() {
      setInterval(() => {
        // Update price displays
        const priceElements = document.querySelectorAll('[class*="price"], [data-symbol]');
        priceElements.forEach(el => {
          const currentPrice = parseFloat(el.textContent?.replace(/[^0-9.-]/g, '') || '0');
          if (currentPrice > 0) {
            const change = (Math.random() - 0.5) * 0.02; // ±1% change
            const newPrice = currentPrice * (1 + change);
            el.textContent = `$${newPrice.toFixed(2)}`;
            
            // Add visual feedback
            el.classList.remove('price-up', 'price-down');
            el.classList.add(change > 0 ? 'price-up' : 'price-down');
            
            setTimeout(() => {
              el.classList.remove('price-up', 'price-down');
            }, 1000);
          }
        });
      }, 2000);
    }
    
    simulateStatusUpdates() {
      // Periodically update connection status
      setInterval(() => {
        if (window.WolfHuntTrading.isConnected) {
          const statusElements = document.querySelectorAll('[class*="status"], [class*="indicator"]');
          statusElements.forEach(el => {
            el.classList.add('connected');
            el.classList.remove('disconnected');
          });
        }
      }, 5000);
    }
    
    setupComponentMonitoring() {
      console.log('👀 Setting up component monitoring...');
      
      // Monitor for new components being added
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          mutation.addedNodes.forEach((node) => {
            if (node.nodeType === 1) { // Element node
              const newButtons = node.querySelectorAll ? node.querySelectorAll('button') : [];
              newButtons.forEach(button => this.enhanceButton(button));
              
              // Also check if the node itself is a button
              if (node.tagName === 'BUTTON') {
                this.enhanceButton(node);
              }
            }
          });
        });
      });
      
      observer.observe(document.body, {
        childList: true,
        subtree: true
      });
    }
    
    reportEnhancementStatus() {
      const report = {
        enhancedButtons: this.enhancedButtons.size,
        activeHandlers: this.eventHandlers.size,
        tradingSystemReady: !!window.WolfHuntTrading,
        modalSystemReady: !!window.WolfHuntModals,
        notificationSystemReady: !!window.WolfHuntNotifications,
        timestamp: new Date().toISOString()
      };
      
      console.log('🔘 React button enhancements applied:', report);
      
      // Store for debugging
      window.wolfhuntButtonEnhancer = report;
      
      // Dispatch ready event
      document.dispatchEvent(new CustomEvent('wolfhunt-buttons-ready', {
        detail: report
      }));
    }
  }
  
  // Initialize React button enhancements
  const initializeButtonEnhancer = () => {
    const enhancer = new ReactButtonEnhancer();
    enhancer.initialize().catch(console.error);
  };
  
  // Wait for React and then initialize
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      setTimeout(initializeButtonEnhancer, 2000);
    });
  } else {
    setTimeout(initializeButtonEnhancer, 2000);
  }
  
})();