/**
 * WolfHunt Enhancement Loader
 * Safely loads and manages production fixes
 */
(function() {
  'use strict';
  
  class WolfHuntEnhancementLoader {
    constructor() {
      this.loadOrder = [
        'performance-fixes',    // Load first for speed improvements
        'accessibility-fixes',  // Critical for compliance
        'button-functionality', // Core UI functionality  
        'enhanced-forms'        // Advanced form features
      ];
      
      this.loadedModules = new Set();
      this.errorCount = 0;
      this.maxErrors = 3;
      this.startTime = performance.now();
    }
    
    async initialize() {
      try {
        console.log('🚀 WolfHunt Enhancement System Starting...');
        
        // Wait for DOM to be ready
        await this.waitForDOM();
        
        // Wait for React to mount (check for #root content)
        await this.waitForReact();
        
        // Load feature flag system first
        await this.loadFeatureFlags();
        
        // Load enhancements in priority order
        await this.loadEnhancements();
        
        // Report final status
        this.reportStatus();
        
      } catch (error) {
        console.error('💥 WolfHunt Enhancement System Failed:', error);
        this.handleCriticalError(error);
      }
    }
    
    async waitForDOM() {
      return new Promise(resolve => {
        if (document.readyState === 'loading') {
          document.addEventListener('DOMContentLoaded', resolve);
        } else {
          resolve();
        }
      });
    }
    
    async waitForReact() {
      const maxWait = 10000; // 10 seconds max
      const start = Date.now();
      
      return new Promise(resolve => {
        const checkReact = () => {
          // Check if React has mounted content
          const root = document.getElementById('root');
          const hasReactContent = root && root.children.length > 0 && 
                                 !root.querySelector('.loading-container');
          
          if (hasReactContent) {
            console.log('✅ React application detected and loaded');
            resolve();
          } else if (Date.now() - start > maxWait) {
            console.warn('⚠️ React app not detected, proceeding anyway');
            resolve();
          } else {
            setTimeout(checkReact, 100);
          }
        };
        
        checkReact();
      });
    }
    
    async loadFeatureFlags() {
      try {
        // Feature flags are already loaded via script tag, just verify
        if (typeof window.WolfHuntFlags === 'undefined') {
          console.error('❌ Feature flags not loaded');
          // Create minimal fallback
          window.WolfHuntFlags = {
            isEnabled: () => false,
            getStatus: () => ({ flags: {}, enabledCount: 0 })
          };
        }
      } catch (error) {
        console.error('❌ Feature flag initialization failed:', error);
      }
    }
    
    async loadEnhancements() {
      for (const module of this.loadOrder) {
        if (window.WolfHuntFlags.isEnabled(module)) {
          try {
            await this.loadModule(module);
          } catch (error) {
            console.error(`❌ Failed to load ${module}:`, error);
            this.errorCount++;
            
            if (this.errorCount >= this.maxErrors) {
              console.error('🚨 Too many errors, stopping enhancement loading');
              this.emergencyDisable();
              break;
            }
          }
        } else {
          console.log(`⏭️ Skipping ${module} (disabled)`);
        }
      }
    }
    
    async loadModule(moduleName) {
      console.log(`🔧 Loading ${moduleName}...`);
      const startTime = performance.now();
      
      const moduleMap = {
        'performance-fixes': '/js/fixes/performance-fixes.js',
        'accessibility-fixes': '/js/fixes/accessibility-fixes.js',
        'button-functionality': [
          '/js/fixes/button-functionality.js',
          '/js/fixes/react-button-enhancer.js'
        ],
        'enhanced-forms': '/js/fixes/form-enhancements.js'
      };
      
      const scripts = Array.isArray(moduleMap[moduleName]) 
        ? moduleMap[moduleName] 
        : [moduleMap[moduleName]];
        
      for (const script of scripts) {
        await this.loadScript(script);
      }
      
      const loadTime = Math.round(performance.now() - startTime);
      this.loadedModules.add(moduleName);
      console.log(`✅ ${moduleName} loaded successfully (${loadTime}ms)`);
      
      // Dispatch custom event for module loading
      this.dispatchModuleEvent(moduleName);
    }
    
    loadScript(src) {
      return new Promise((resolve, reject) => {
        // Check if script already loaded
        if (document.querySelector(`script[src="${src}"]`)) {
          resolve();
          return;
        }
        
        const script = document.createElement('script');
        script.src = src;
        script.async = true;
        
        const timeout = setTimeout(() => {
          reject(new Error(`Script load timeout: ${src}`));
        }, 10000); // 10 second timeout
        
        script.onload = () => {
          clearTimeout(timeout);
          resolve();
        };
        
        script.onerror = () => {
          clearTimeout(timeout);
          reject(new Error(`Failed to load: ${src}`));
        };
        
        document.head.appendChild(script);
      });
    }
    
    dispatchModuleEvent(moduleName) {
      const event = new CustomEvent('wolfhunt-module-loaded', {
        detail: { 
          module: moduleName,
          timestamp: Date.now(),
          totalLoaded: this.loadedModules.size
        }
      });
      
      document.dispatchEvent(event);
    }
    
    reportStatus() {
      const totalTime = Math.round(performance.now() - this.startTime);
      const status = {
        loadedModules: Array.from(this.loadedModules),
        totalModules: this.loadOrder.length,
        enabledModules: this.loadOrder.filter(m => window.WolfHuntFlags.isEnabled(m)),
        errors: this.errorCount,
        loadTime: totalTime,
        timestamp: new Date().toISOString(),
        featureFlags: window.WolfHuntFlags.getStatus()
      };
      
      console.log('📊 WolfHunt Enhancement Status:', status);
      
      // Store status for debugging
      window.wolfhuntStatus = status;
      
      // Send to analytics if available
      if (typeof gtag === 'function') {
        gtag('event', 'enhancement_loaded', {
          modules_loaded: status.loadedModules.length,
          load_time: totalTime,
          errors: this.errorCount
        });
      }
      
      // Dispatch completion event
      document.dispatchEvent(new CustomEvent('wolfhunt-enhancements-ready', {
        detail: status
      }));
    }
    
    emergencyDisable() {
      console.error('🚨 WolfHunt: Emergency disable activated');
      
      if (window.WolfHuntFlags && typeof window.WolfHuntFlags.emergencyDisable === 'function') {
        window.WolfHuntFlags.emergencyDisable();
      }
      
      // Remove loaded enhancements
      this.loadedModules.clear();
      
      // Show user notification
      this.showEmergencyNotification();
    }
    
    showEmergencyNotification() {
      const notification = document.createElement('div');
      notification.className = 'fixed top-4 right-4 bg-red-600 text-white px-6 py-4 rounded-lg shadow-lg z-50 max-w-sm';
      notification.innerHTML = `
        <div class="flex items-center">
          <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
          </svg>
          <div>
            <div class="font-medium">System Error</div>
            <div class="text-sm opacity-90">Some features temporarily disabled</div>
          </div>
          <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-white hover:text-red-200">
            ×
          </button>
        </div>
      `;
      
      document.body.appendChild(notification);
      
      // Auto-remove after 10 seconds
      setTimeout(() => {
        if (notification.parentNode) {
          notification.remove();
        }
      }, 10000);
    }
    
    handleCriticalError(error) {
      // Log to monitoring service if available
      if (window.Sentry) {
        window.Sentry.captureException(error);
      }
      
      // Show user-friendly error
      console.error('WolfHunt Enhancement System encountered a critical error. Basic functionality will continue to work.');
    }
  }
  
  // Auto-initialize when DOM is ready, unless emergency disabled
  if (localStorage.getItem('wolfhunt-emergency-disable') !== 'true') {
    const loader = new WolfHuntEnhancementLoader();
    loader.initialize().catch(error => {
      console.error('WolfHunt Enhancement Loader failed:', error);
    });
  } else {
    console.warn('🚨 WolfHunt Enhancement System disabled due to emergency mode');
  }
  
  // Expose loader for debugging
  window.WolfHuntLoader = WolfHuntEnhancementLoader;
  
})();