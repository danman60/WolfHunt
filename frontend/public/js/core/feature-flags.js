/**
 * WolfHunt Feature Flag Management System
 * Controls gradual rollout of production fixes
 */
class FeatureFlags {
  constructor() {
    this.flags = {
      'performance-fixes': false,
      'accessibility-fixes': false, 
      'button-functionality': false,
      'enhanced-forms': false,
      'debug-mode': false
    };
    
    this.defaultEnabledFlags = [
      'performance-fixes',  // Safe performance improvements
      'accessibility-fixes' // Critical compliance fixes
    ];
    
    this.loadFlags();
    this.logStatus();
  }
  
  loadFlags() {
    // Check URL parameters first (for testing)
    const urlParams = new URLSearchParams(window.location.search);
    
    // Enable all flags for testing
    if (urlParams.get('wolfhunt-test') === 'all') {
      Object.keys(this.flags).forEach(flag => {
        this.flags[flag] = true;
      });
      console.log('🧪 WolfHunt: All features enabled for testing');
      return;
    }
    
    // Individual flag overrides
    Object.keys(this.flags).forEach(flag => {
      if (urlParams.get(`enable-${flag}`) === 'true') {
        this.flags[flag] = true;
      } else if (urlParams.get(`disable-${flag}`) === 'true') {
        this.flags[flag] = false;
      }
    });
    
    // Load from localStorage
    const stored = localStorage.getItem('wolfhunt-feature-flags');
    if (stored) {
      try {
        const storedFlags = JSON.parse(stored);
        Object.assign(this.flags, storedFlags);
      } catch (e) {
        console.warn('WolfHunt: Invalid stored feature flags, using defaults');
      }
    } else {
      // Set defaults for new users
      this.defaultEnabledFlags.forEach(flag => {
        this.flags[flag] = true;
      });
    }
    
    // Check for emergency disable
    if (localStorage.getItem('wolfhunt-emergency-disable') === 'true') {
      console.warn('🚨 WolfHunt: Emergency disable active - all features disabled');
      Object.keys(this.flags).forEach(flag => {
        this.flags[flag] = false;
      });
    }
  }
  
  isEnabled(flag) {
    return this.flags[flag] === true;
  }
  
  enable(flag) {
    this.flags[flag] = true;
    this.persist();
    console.log(`✅ WolfHunt: Enabled ${flag}`);
  }
  
  disable(flag) {
    this.flags[flag] = false;
    this.persist();
    console.log(`❌ WolfHunt: Disabled ${flag}`);
  }
  
  toggle(flag) {
    this.flags[flag] = !this.flags[flag];
    this.persist();
    console.log(`🔄 WolfHunt: Toggled ${flag} -> ${this.flags[flag]}`);
  }
  
  persist() {
    localStorage.setItem('wolfhunt-feature-flags', JSON.stringify(this.flags));
  }
  
  emergencyDisable() {
    console.error('🚨 WolfHunt: Emergency disable activated');
    localStorage.setItem('wolfhunt-emergency-disable', 'true');
    Object.keys(this.flags).forEach(flag => {
      this.flags[flag] = false;
    });
    this.persist();
  }
  
  reset() {
    localStorage.removeItem('wolfhunt-feature-flags');
    localStorage.removeItem('wolfhunt-emergency-disable');
    this.loadFlags();
    console.log('🔄 WolfHunt: Feature flags reset to defaults');
  }
  
  getStatus() {
    return {
      flags: { ...this.flags },
      enabledCount: Object.values(this.flags).filter(Boolean).length,
      totalCount: Object.keys(this.flags).length,
      emergencyDisabled: localStorage.getItem('wolfhunt-emergency-disable') === 'true'
    };
  }
  
  logStatus() {
    const status = this.getStatus();
    console.log(`🏃 WolfHunt Feature Flags: ${status.enabledCount}/${status.totalCount} enabled`, status.flags);
  }
  
  // Development helpers
  enableAll() {
    Object.keys(this.flags).forEach(flag => this.flags[flag] = true);
    this.persist();
    console.log('🚀 WolfHunt: All features enabled');
  }
  
  disableAll() {
    Object.keys(this.flags).forEach(flag => this.flags[flag] = false);
    this.persist();
    console.log('🛑 WolfHunt: All features disabled');
  }
}

// Initialize global feature flags
window.WolfHuntFlags = new FeatureFlags();

// Expose development helpers globally
if (window.WolfHuntFlags.isEnabled('debug-mode')) {
  window.wolfhunt = {
    flags: window.WolfHuntFlags,
    enableAll: () => window.WolfHuntFlags.enableAll(),
    disableAll: () => window.WolfHuntFlags.disableAll(),
    reset: () => window.WolfHuntFlags.reset(),
    emergency: () => window.WolfHuntFlags.emergencyDisable(),
    status: () => window.WolfHuntFlags.getStatus()
  };
  
  console.log('🔧 WolfHunt Dev Tools: Available via window.wolfhunt');
}

// Export removed for browser script tag compatibility