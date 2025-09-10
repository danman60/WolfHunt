/**
 * WolfHunt Accessibility Compliance System
 * WCAG 2.1 AA compliance fixes for trading interface
 */
(function() {
  'use strict';
  
  if (!window.WolfHuntFlags?.isEnabled('accessibility-fixes')) {
    console.log('⏭️ Accessibility fixes disabled');
    return;
  }
  
  console.log('♿ Applying WolfHunt accessibility fixes...');
  
  class AccessibilityEnhancer {
    constructor() {
      this.applied = new Set();
      this.violations = [];
      this.fixes = [];
    }
    
    async initialize() {
      try {
        await this.addSkipNavigation();
        await this.fixHeadingHierarchy();
        await this.enhanceKeyboardNavigation();
        await this.addARIALabels();
        await this.improveFocusManagement();
        await this.addLandmarks();
        await this.enhanceColorContrast();
        await this.setupScreenReaderSupport();
        await this.addLiveRegions();
        
        this.reportAccessibilityImprovements();
        
      } catch (error) {
        console.error('❌ Accessibility enhancement error:', error);
      }
    }
    
    async addSkipNavigation() {
      if (this.applied.has('skip-nav')) return;
      
      console.log('🔗 Adding skip navigation...');
      
      // Check if skip link already exists
      if (document.querySelector('.skip-link, [href="#main-content"]')) {
        this.applied.add('skip-nav');
        return;
      }
      
      // Create skip navigation link
      const skipLink = document.createElement('a');
      skipLink.href = '#main-content';
      skipLink.className = 'skip-link sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:rounded focus:outline-none focus:ring-2 focus:ring-white';
      skipLink.textContent = 'Skip to main content';
      
      // Insert at the beginning of body
      document.body.insertBefore(skipLink, document.body.firstChild);
      
      // Ensure main content has proper ID
      this.ensureMainContentId();
      
      this.fixes.push('Added skip navigation link');
      this.applied.add('skip-nav');
    }
    
    ensureMainContentId() {
      let main = document.querySelector('main');
      if (!main) {
        // Look for React app container
        main = document.querySelector('#root > div > div:last-child') ||
               document.querySelector('[class*="main"]') ||
               document.querySelector('#root');
      }
      
      if (main && !main.id) {
        main.id = 'main-content';
        main.setAttribute('role', 'main');
      }
    }
    
    async fixHeadingHierarchy() {
      if (this.applied.has('headings')) return;
      
      console.log('📄 Fixing heading hierarchy...');
      
      const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
      const h1Elements = document.querySelectorAll('h1');
      
      // Ensure we have exactly one H1
      if (h1Elements.length === 0) {
        this.addMissingH1();
      } else if (h1Elements.length > 1) {
        this.fixMultipleH1s();
      }
      
      // Check heading sequence
      this.validateHeadingSequence();
      
      this.fixes.push(`Fixed heading hierarchy (${headings.length} headings processed)`);
      this.applied.add('headings');
    }
    
    addMissingH1() {
      // Create page-appropriate H1
      const pageTitle = this.getPageTitle();
      const h1 = document.createElement('h1');
      h1.className = 'sr-only'; // Screen reader only
      h1.textContent = pageTitle;
      
      const main = document.querySelector('main, #main-content, #root');
      if (main) {
        main.insertBefore(h1, main.firstChild);
      }
    }
    
    getPageTitle() {
      const path = window.location.pathname;
      const titleMap = {
        '/': 'WolfHunt Trading Dashboard',
        '/dashboard': 'Trading Dashboard',
        '/intelligence': 'Market Intelligence',
        '/trading': 'Live Trading',
        '/history': 'Trading History',
        '/strategy': 'Trading Strategies',
        '/risk': 'Risk Management',
        '/alerts': 'Trading Alerts'
      };
      
      return titleMap[path] || document.title.split(' - ')[0] || 'WolfHunt Trading Platform';
    }
    
    fixMultipleH1s() {
      const h1Elements = document.querySelectorAll('h1');
      // Keep the first H1, convert others to H2
      for (let i = 1; i < h1Elements.length; i++) {
        const h1 = h1Elements[i];
        const h2 = document.createElement('h2');
        h2.className = h1.className;
        h2.textContent = h1.textContent;
        h1.parentNode.replaceChild(h2, h1);
      }
    }
    
    validateHeadingSequence() {
      const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
      let previousLevel = 0;
      
      headings.forEach(heading => {
        const level = parseInt(heading.tagName.charAt(1));
        
        if (level - previousLevel > 1) {
          this.violations.push({
            type: 'heading-sequence',
            element: heading,
            message: `Heading level ${level} follows level ${previousLevel} (should not skip levels)`
          });
        }
        
        previousLevel = level;
      });
    }
    
    async enhanceKeyboardNavigation() {
      if (this.applied.has('keyboard-nav')) return;
      
      console.log('⌨️ Enhancing keyboard navigation...');
      
      // Make all interactive elements keyboard accessible
      this.makeElementsKeyboardAccessible();
      
      // Add keyboard shortcuts
      this.addKeyboardShortcuts();
      
      // Improve tab order
      this.improveTabbingOrder();
      
      // Handle escape key for modals
      this.handleEscapeKey();
      
      this.fixes.push('Enhanced keyboard navigation and shortcuts');
      this.applied.add('keyboard-nav');
    }
    
    makeElementsKeyboardAccessible() {
      // Find clickable elements without proper keyboard support
      const clickableElements = document.querySelectorAll('[onclick]:not(button):not(a):not([tabindex])');
      
      clickableElements.forEach(element => {
        // Make focusable
        element.tabIndex = 0;
        
        // Add keyboard event handler
        element.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            element.click();
          }
        });
        
        // Add role if missing
        if (!element.getAttribute('role')) {
          element.setAttribute('role', 'button');
        }
      });
    }
    
    addKeyboardShortcuts() {
      const shortcuts = {
        'Alt+D': () => this.navigateTo('/dashboard'),
        'Alt+I': () => this.navigateTo('/intelligence'), 
        'Alt+T': () => this.navigateTo('/trading'),
        'Alt+H': () => this.navigateTo('/history'),
        'Alt+S': () => this.navigateTo('/strategy'),
        'Alt+R': () => this.navigateTo('/risk'),
        'Alt+A': () => this.navigateTo('/alerts'),
        'Alt+/': () => this.showKeyboardShortcuts()
      };
      
      document.addEventListener('keydown', (e) => {
        const combo = `${e.altKey ? 'Alt+' : ''}${e.ctrlKey ? 'Ctrl+' : ''}${e.shiftKey ? 'Shift+' : ''}${e.key}`;
        
        if (shortcuts[combo]) {
          e.preventDefault();
          shortcuts[combo]();
        }
      });
      
      // Add shortcut help
      this.createShortcutHelp();
    }
    
    navigateTo(path) {
      if (window.location.pathname !== path) {
        window.history.pushState({}, '', path);
        window.dispatchEvent(new PopStateEvent('popstate'));
      }
    }
    
    createShortcutHelp() {
      const helpButton = document.createElement('button');
      helpButton.className = 'fixed bottom-4 right-4 bg-blue-600 text-white p-2 rounded-full shadow-lg z-40 focus:outline-none focus:ring-2 focus:ring-white';
      helpButton.setAttribute('aria-label', 'Show keyboard shortcuts');
      helpButton.innerHTML = `
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"></path>
        </svg>
      `;
      
      helpButton.onclick = () => this.showKeyboardShortcuts();
      document.body.appendChild(helpButton);
    }
    
    showKeyboardShortcuts() {
      const modal = document.createElement('div');
      modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
      modal.setAttribute('role', 'dialog');
      modal.setAttribute('aria-labelledby', 'shortcuts-title');
      modal.setAttribute('aria-modal', 'true');
      
      modal.innerHTML = `
        <div class="bg-white rounded-lg p-6 max-w-md mx-4">
          <div class="flex justify-between items-center mb-4">
            <h2 id="shortcuts-title" class="text-lg font-semibold">Keyboard Shortcuts</h2>
            <button class="text-gray-400 hover:text-gray-600" onclick="this.closest('[role=dialog]').remove()">
              <span class="sr-only">Close</span>
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
          
          <div class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span>Dashboard</span>
              <kbd class="bg-gray-100 px-2 py-1 rounded">Alt+D</kbd>
            </div>
            <div class="flex justify-between">
              <span>Intelligence</span>
              <kbd class="bg-gray-100 px-2 py-1 rounded">Alt+I</kbd>
            </div>
            <div class="flex justify-between">
              <span>Trading</span>
              <kbd class="bg-gray-100 px-2 py-1 rounded">Alt+T</kbd>
            </div>
            <div class="flex justify-between">
              <span>History</span>
              <kbd class="bg-gray-100 px-2 py-1 rounded">Alt+H</kbd>
            </div>
            <div class="flex justify-between">
              <span>Strategy</span>
              <kbd class="bg-gray-100 px-2 py-1 rounded">Alt+S</kbd>
            </div>
            <div class="flex justify-between">
              <span>Risk Management</span>
              <kbd class="bg-gray-100 px-2 py-1 rounded">Alt+R</kbd>
            </div>
            <div class="flex justify-between">
              <span>Alerts</span>
              <kbd class="bg-gray-100 px-2 py-1 rounded">Alt+A</kbd>
            </div>
            <div class="flex justify-between border-t pt-2 mt-2">
              <span>Show this help</span>
              <kbd class="bg-gray-100 px-2 py-1 rounded">Alt+/</kbd>
            </div>
          </div>
        </div>
      `;
      
      document.body.appendChild(modal);
      
      // Focus trap
      const focusableElements = modal.querySelectorAll('button');
      if (focusableElements.length > 0) {
        focusableElements[0].focus();
      }
    }
    
    improveTabbingOrder() {
      // Ensure logical tab order for main navigation
      const navItems = document.querySelectorAll('nav a, nav button');
      navItems.forEach((item, index) => {
        item.tabIndex = index + 1;
      });
    }
    
    handleEscapeKey() {
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
          // Close modals, dropdowns, etc.
          const modals = document.querySelectorAll('[role="dialog"], .modal, .dropdown-menu');
          modals.forEach(modal => {
            if (modal.style.display !== 'none' && !modal.hidden) {
              modal.remove();
            }
          });
        }
      });
    }
    
    async addARIALabels() {
      if (this.applied.has('aria-labels')) return;
      
      console.log('🏷️ Adding ARIA labels...');
      
      // Label buttons without text
      this.labelIconButtons();
      
      // Add descriptions for complex elements
      this.addARIADescriptions();
      
      // Label form controls
      this.labelFormControls();
      
      this.fixes.push('Added comprehensive ARIA labels and descriptions');
      this.applied.add('aria-labels');
    }
    
    labelIconButtons() {
      const buttons = document.querySelectorAll('button:not([aria-label])');
      
      buttons.forEach(button => {
        const text = button.textContent?.trim();
        const hasIcon = button.querySelector('svg, [class*="icon"]');
        
        if ((!text || text.length < 2) && hasIcon) {
          const label = this.inferButtonLabel(button);
          button.setAttribute('aria-label', label);
        }
      });
    }
    
    inferButtonLabel(button) {
      const classes = button.className.toLowerCase();
      const parent = button.closest('[class*="notification"], [class*="user"], [class*="menu"], [class*="settings"], nav');
      const iconEl = button.querySelector('svg, [class*="icon"]');
      
      // Common patterns
      if (classes.includes('close') || button.textContent.includes('×')) return 'Close';
      if (classes.includes('menu') || button.textContent.includes('☰')) return 'Open menu';
      if (classes.includes('settings') || iconEl?.classList.contains('cog')) return 'Open settings';
      if (classes.includes('notification') || iconEl?.classList.contains('bell')) return 'View notifications';
      if (classes.includes('user') || parent?.className.includes('user')) return 'Open user menu';
      if (classes.includes('search')) return 'Search';
      if (classes.includes('filter')) return 'Filter options';
      if (classes.includes('sort')) return 'Sort options';
      if (classes.includes('refresh')) return 'Refresh data';
      
      // Trading specific
      if (button.textContent.toLowerCase().includes('buy')) return 'Execute buy order';
      if (button.textContent.toLowerCase().includes('sell')) return 'Execute sell order';
      if (classes.includes('trade')) return 'Open trading interface';
      
      return 'Button'; // Fallback
    }
    
    addARIADescriptions() {
      // Add descriptions for complex UI elements
      const complexElements = [
        { selector: '[class*="chart"]', description: 'Interactive trading chart showing price movements and market data' },
        { selector: '[class*="graph"]', description: 'Data visualization graph' },
        { selector: '[class*="trading"]', description: 'Trading interface for managing positions and orders' },
        { selector: '[class*="portfolio"]', description: 'Portfolio overview showing current positions and performance' },
        { selector: 'table', description: 'Data table with trading information' }
      ];
      
      complexElements.forEach(({ selector, description }) => {
        const elements = document.querySelectorAll(selector);
        elements.forEach((element, index) => {
          if (!element.getAttribute('aria-describedby')) {
            const descId = `desc-${selector.replace(/[^\w]/g, '')}-${index}`;
            const descElement = document.createElement('div');
            descElement.id = descId;
            descElement.className = 'sr-only';
            descElement.textContent = description;
            
            element.parentNode.insertBefore(descElement, element.nextSibling);
            element.setAttribute('aria-describedby', descId);
          }
        });
      });
    }
    
    labelFormControls() {
      // Ensure all form inputs have labels
      const inputs = document.querySelectorAll('input:not([aria-label]):not([id])');
      inputs.forEach((input, index) => {
        const label = input.closest('label') || 
                     document.querySelector(`label[for="${input.name}"]`) ||
                     input.previousElementSibling?.tagName === 'LABEL' ? input.previousElementSibling : null;
        
        if (!label) {
          // Create implicit label
          const labelText = input.placeholder || input.name || `Input field ${index + 1}`;
          input.setAttribute('aria-label', labelText);
        }
      });
    }
    
    async improveFocusManagement() {
      if (this.applied.has('focus')) return;
      
      console.log('🎯 Improving focus management...');
      
      // Add visible focus indicators
      this.addFocusStyles();
      
      // Manage focus for dynamic content
      this.setupFocusManagement();
      
      // Handle focus traps
      this.setupFocusTraps();
      
      this.fixes.push('Improved focus management and visibility');
      this.applied.add('focus');
    }
    
    addFocusStyles() {
      const style = document.createElement('style');
      style.textContent = `
        /* Enhanced focus indicators */
        *:focus {
          outline: 2px solid #3B82F6 !important;
          outline-offset: 2px !important;
        }
        
        button:focus,
        a:focus,
        input:focus,
        select:focus,
        textarea:focus {
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3) !important;
        }
        
        /* High contrast mode support */
        @media (prefers-contrast: high) {
          *:focus {
            outline: 3px solid currentColor !important;
            outline-offset: 3px !important;
          }
        }
        
        /* Screen reader only content */
        .sr-only {
          position: absolute !important;
          width: 1px !important;
          height: 1px !important;
          padding: 0 !important;
          margin: -1px !important;
          overflow: hidden !important;
          clip: rect(0, 0, 0, 0) !important;
          white-space: nowrap !important;
          border: 0 !important;
        }
        
        .sr-only.focus\\:not-sr-only:focus {
          position: static !important;
          width: auto !important;
          height: auto !important;
          padding: 0.5rem 1rem !important;
          margin: 0 !important;
          overflow: visible !important;
          clip: auto !important;
          white-space: normal !important;
        }
      `;
      document.head.appendChild(style);
    }
    
    setupFocusManagement() {
      // Focus management for route changes (React Router)
      const originalPushState = history.pushState;
      history.pushState = function(...args) {
        originalPushState.apply(history, args);
        
        setTimeout(() => {
          // Focus the main heading or main element
          const h1 = document.querySelector('h1');
          const main = document.querySelector('main, #main-content');
          
          if (h1 && h1.offsetParent) {
            h1.focus();
          } else if (main) {
            main.focus();
          }
        }, 100);
      };
    }
    
    setupFocusTraps() {
      // Monitor for modal-like elements
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          mutation.addedNodes.forEach((node) => {
            if (node.nodeType === 1 && node.getAttribute('role') === 'dialog') {
              this.trapFocusInModal(node);
            }
          });
        });
      });
      
      observer.observe(document.body, { childList: true, subtree: true });
    }
    
    trapFocusInModal(modal) {
      const focusableElements = modal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      
      if (focusableElements.length === 0) return;
      
      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];
      
      // Focus first element
      firstElement.focus();
      
      // Trap focus within modal
      modal.addEventListener('keydown', (e) => {
        if (e.key === 'Tab') {
          if (e.shiftKey) {
            if (document.activeElement === firstElement) {
              lastElement.focus();
              e.preventDefault();
            }
          } else {
            if (document.activeElement === lastElement) {
              firstElement.focus();
              e.preventDefault();
            }
          }
        }
      });
    }
    
    async addLandmarks() {
      if (this.applied.has('landmarks')) return;
      
      console.log('🏛️ Adding ARIA landmarks...');
      
      // Ensure main landmark
      this.ensureMainLandmark();
      
      // Add navigation landmarks
      this.addNavigationLandmarks();
      
      // Add complementary landmarks
      this.addComplementaryLandmarks();
      
      this.fixes.push('Added proper ARIA landmarks for page structure');
      this.applied.add('landmarks');
    }
    
    ensureMainLandmark() {
      if (!document.querySelector('main, [role="main"]')) {
        const mainContent = document.querySelector('#root > div') ||
                           document.querySelector('[class*="main"]') ||
                           document.querySelector('#root');
        
        if (mainContent) {
          mainContent.setAttribute('role', 'main');
        }
      }
    }
    
    addNavigationLandmarks() {
      const navElements = document.querySelectorAll('nav:not([aria-label])');
      navElements.forEach((nav, index) => {
        const label = index === 0 ? 'Main navigation' : `Navigation ${index + 1}`;
        nav.setAttribute('aria-label', label);
      });
      
      // Add breadcrumb navigation if exists
      const breadcrumbs = document.querySelectorAll('[class*="breadcrumb"]');
      breadcrumbs.forEach(breadcrumb => {
        breadcrumb.setAttribute('aria-label', 'Breadcrumb navigation');
        breadcrumb.setAttribute('role', 'navigation');
      });
    }
    
    addComplementaryLandmarks() {
      // Identify sidebar-like elements
      const sidebars = document.querySelectorAll('[class*="sidebar"], aside');
      sidebars.forEach(sidebar => {
        if (!sidebar.getAttribute('role')) {
          sidebar.setAttribute('role', 'complementary');
          sidebar.setAttribute('aria-label', 'Trading tools and information');
        }
      });
    }
    
    async enhanceColorContrast() {
      if (this.applied.has('color-contrast')) return;
      
      console.log('🎨 Enhancing color contrast...');
      
      // Add high contrast styles for accessibility
      const style = document.createElement('style');
      style.textContent = `
        /* High contrast mode adjustments */
        @media (prefers-contrast: high) {
          .text-gray-400 { color: #000 !important; }
          .text-gray-500 { color: #000 !important; }
          .text-gray-600 { color: #000 !important; }
          
          .bg-gray-100 { background-color: #fff !important; }
          .bg-gray-200 { background-color: #fff !important; }
          
          button, .btn {
            border: 2px solid currentColor !important;
          }
        }
        
        /* Dark mode improvements */
        @media (prefers-color-scheme: dark) {
          :root {
            --text-contrast: #fff;
            --bg-contrast: #000;
          }
        }
      `;
      document.head.appendChild(style);
      
      this.fixes.push('Enhanced color contrast for better visibility');
      this.applied.add('color-contrast');
    }
    
    async setupScreenReaderSupport() {
      if (this.applied.has('screen-reader')) return;
      
      console.log('📢 Setting up screen reader support...');
      
      // Add role descriptions where helpful
      this.addRoleDescriptions();
      
      // Enhance table accessibility
      this.enhanceTableAccessibility();
      
      // Add context for dynamic content
      this.addDynamicContentContext();
      
      this.fixes.push('Enhanced screen reader support and context');
      this.applied.add('screen-reader');
    }
    
    addRoleDescriptions() {
      const elements = [
        { selector: '[class*="chart"]', role: 'img', description: 'Trading chart' },
        { selector: 'canvas', role: 'img', description: 'Data visualization' },
        { selector: '[class*="trading-panel"]', role: 'region', description: 'Trading controls' }
      ];
      
      elements.forEach(({ selector, role, description }) => {
        document.querySelectorAll(selector).forEach(el => {
          if (!el.getAttribute('role')) {
            el.setAttribute('role', role);
          }
          if (!el.getAttribute('aria-roledescription')) {
            el.setAttribute('aria-roledescription', description);
          }
        });
      });
    }
    
    enhanceTableAccessibility() {
      const tables = document.querySelectorAll('table');
      tables.forEach(table => {
        // Add caption if missing
        if (!table.querySelector('caption')) {
          const caption = document.createElement('caption');
          caption.className = 'sr-only';
          caption.textContent = 'Trading data table';
          table.insertBefore(caption, table.firstChild);
        }
        
        // Ensure headers are properly associated
        const headers = table.querySelectorAll('th');
        headers.forEach((th, index) => {
          if (!th.id) {
            th.id = `header-${index}-${Date.now()}`;
          }
        });
        
        // Associate cells with headers
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
          const cells = row.querySelectorAll('td');
          cells.forEach((cell, cellIndex) => {
            if (!cell.getAttribute('headers')) {
              const header = headers[cellIndex];
              if (header) {
                cell.setAttribute('headers', header.id);
              }
            }
          });
        });
      });
    }
    
    addDynamicContentContext() {
      // Add context for price changes, alerts, etc.
      const priceElements = document.querySelectorAll('[class*="price"], [class*="amount"]');
      priceElements.forEach(el => {
        if (!el.getAttribute('aria-live')) {
          el.setAttribute('aria-live', 'polite');
        }
      });
      
      // Add context for status indicators
      const statusElements = document.querySelectorAll('[class*="status"], [class*="badge"]');
      statusElements.forEach(el => {
        if (!el.getAttribute('role')) {
          el.setAttribute('role', 'status');
        }
      });
    }
    
    async addLiveRegions() {
      if (this.applied.has('live-regions')) return;
      
      console.log('📡 Adding live regions for dynamic updates...');
      
      // Create announcement region for important updates
      const announcer = document.createElement('div');
      announcer.id = 'wolfhunt-announcer';
      announcer.className = 'sr-only';
      announcer.setAttribute('aria-live', 'assertive');
      announcer.setAttribute('aria-atomic', 'true');
      document.body.appendChild(announcer);
      
      // Create polite region for status updates
      const status = document.createElement('div');
      status.id = 'wolfhunt-status';
      status.className = 'sr-only';
      status.setAttribute('aria-live', 'polite');
      status.setAttribute('aria-atomic', 'false');
      document.body.appendChild(status);
      
      // Expose global functions for announcements
      window.WolfHuntA11y = {
        announce: (message) => {
          announcer.textContent = message;
        },
        status: (message) => {
          status.textContent = message;
        }
      };
      
      this.fixes.push('Added live regions for dynamic content announcements');
      this.applied.add('live-regions');
    }
    
    reportAccessibilityImprovements() {
      const report = {
        fixesApplied: this.fixes,
        violationsFound: this.violations.length,
        enhancementsCount: this.applied.size,
        wcagLevel: 'AA',
        timestamp: new Date().toISOString()
      };
      
      console.log('♿ Accessibility improvements applied:', report);
      
      // Store for debugging
      window.wolfhuntAccessibility = report;
      
      // Send to analytics
      if (typeof gtag === 'function') {
        gtag('event', 'accessibility_enhanced', {
          fixes_applied: this.fixes.length,
          violations_found: this.violations.length
        });
      }
      
      // Dispatch event for other systems
      document.dispatchEvent(new CustomEvent('wolfhunt-a11y-ready', {
        detail: report
      }));
    }
  }
  
  // Initialize accessibility enhancements
  const initializeA11y = () => {
    const enhancer = new AccessibilityEnhancer();
    enhancer.initialize().catch(console.error);
  };
  
  // Initialize when React content is loaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      setTimeout(initializeA11y, 1000); // Wait for React to mount
    });
  } else {
    setTimeout(initializeA11y, 1000);
  }
  
})();