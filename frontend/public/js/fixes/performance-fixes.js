/**
 * WolfHunt Performance Optimization Fixes
 * Improves loading speed and runtime performance
 */
(function() {
  'use strict';
  
  if (!window.WolfHuntFlags?.isEnabled('performance-fixes')) {
    console.log('⏭️ Performance fixes disabled');
    return;
  }
  
  console.log('⚡ Applying WolfHunt performance fixes...');
  
  class PerformanceEnhancer {
    constructor() {
      this.applied = new Set();
      this.performanceMetrics = {};
      this.startTime = performance.now();
    }
    
    async initialize() {
      try {
        // Apply fixes in order of impact
        await this.optimizeImages();
        await this.addResourceHints(); 
        await this.setupAPICache();
        await this.optimizeAnimations();
        await this.setupLazyLoading();
        await this.optimizeScrolling();
        await this.setupPerformanceMonitoring();
        
        this.reportPerformanceGains();
        
      } catch (error) {
        console.error('❌ Performance enhancement error:', error);
      }
    }
    
    async optimizeImages() {
      if (this.applied.has('images')) return;
      
      console.log('🖼️ Optimizing images...');
      
      // Add lazy loading to all images
      const images = document.querySelectorAll('img:not([loading])');
      images.forEach(img => {
        img.loading = 'lazy';
        img.decoding = 'async';
        
        // Add WebP support detection
        if (this.supportsWebP() && !img.src.includes('.webp')) {
          this.convertToWebP(img);
        }
      });
      
      // Optimize background images
      this.optimizeBackgroundImages();
      
      this.applied.add('images');
    }
    
    supportsWebP() {
      if (this._webpSupport !== undefined) return this._webpSupport;
      
      const canvas = document.createElement('canvas');
      canvas.width = 1;
      canvas.height = 1;
      this._webpSupport = canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
      return this._webpSupport;
    }
    
    convertToWebP(img) {
      // Only convert if we have the WebP version available
      const webpSrc = img.src.replace(/\.(jpg|jpeg|png)$/i, '.webp');
      
      // Create a new image to test if WebP version exists
      const testImg = new Image();
      testImg.onload = () => {
        // WebP version exists, create picture element
        if (!img.closest('picture')) {
          const picture = document.createElement('picture');
          const source = document.createElement('source');
          source.srcset = webpSrc;
          source.type = 'image/webp';
          
          img.parentNode.insertBefore(picture, img);
          picture.appendChild(source);
          picture.appendChild(img);
        }
      };
      testImg.onerror = () => {
        // WebP version doesn't exist, keep original
      };
      testImg.src = webpSrc;
    }
    
    optimizeBackgroundImages() {
      const elements = document.querySelectorAll('[style*="background-image"]');
      elements.forEach(el => {
        const style = el.style.backgroundImage;
        if (style && style.includes('url(')) {
          // Add background size optimization
          if (!el.style.backgroundSize) {
            el.style.backgroundSize = 'cover';
          }
        }
      });
    }
    
    async addResourceHints() {
      if (this.applied.has('resource-hints')) return;
      
      console.log('🔗 Adding resource hints...');
      
      const head = document.head;
      
      // Critical resource preloads
      const preloads = [
        { href: '/src/main.tsx', as: 'script' },
        { href: 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap', as: 'style' }
      ];
      
      preloads.forEach(({ href, as, type, crossorigin }) => {
        if (!document.querySelector(`link[href="${href}"]`)) {
          const link = document.createElement('link');
          link.rel = 'preload';
          link.href = href;
          link.as = as;
          if (type) link.type = type;
          if (crossorigin !== undefined) link.crossOrigin = crossorigin;
          head.appendChild(link);
        }
      });
      
      // DNS prefetch for external resources
      const dnsPrefetch = [
        'api.gmx.io',
        'fonts.googleapis.com',
        'fonts.gstatic.com'
      ];
      
      dnsPrefetch.forEach(domain => {
        if (!document.querySelector(`link[href="//${domain}"]`)) {
          const link = document.createElement('link');
          link.rel = 'dns-prefetch';
          link.href = `//${domain}`;
          head.appendChild(link);
        }
      });
      
      this.applied.add('resource-hints');
    }
    
    async setupAPICache() {
      if (this.applied.has('api-cache')) return;
      
      console.log('💾 Setting up API cache...');
      
      // Enhanced API Cache with TTL and size limits
      class APICache {
        constructor(options = {}) {
          this.cache = new Map();
          this.ttl = options.ttl || 30000; // 30 seconds default
          this.maxSize = options.maxSize || 100; // Max 100 entries
          this.stats = { hits: 0, misses: 0, evictions: 0 };
        }
        
        async get(key, fetcher) {
          const cached = this.cache.get(key);
          const now = Date.now();
          
          if (cached && now - cached.timestamp < this.ttl) {
            this.stats.hits++;
            return cached.data;
          }
          
          this.stats.misses++;
          
          try {
            const data = await fetcher();
            this.set(key, data);
            return data;
          } catch (error) {
            // Return stale data if available and fetcher fails
            if (cached && cached.data) {
              console.warn('API fetch failed, returning stale data');
              return cached.data;
            }
            throw error;
          }
        }
        
        set(key, data) {
          // Evict oldest entries if at max size
          if (this.cache.size >= this.maxSize) {
            const oldestKey = this.cache.keys().next().value;
            this.cache.delete(oldestKey);
            this.stats.evictions++;
          }
          
          this.cache.set(key, {
            data,
            timestamp: Date.now()
          });
        }
        
        clear() {
          this.cache.clear();
        }
        
        getStats() {
          return {
            ...this.stats,
            size: this.cache.size,
            hitRate: this.stats.hits / (this.stats.hits + this.stats.misses) || 0
          };
        }
      }
      
      // Create global API cache
      window.WolfHuntAPICache = new APICache({ ttl: 30000, maxSize: 50 });
      
      // Enhance fetch to use cache
      const originalFetch = window.fetch;
      window.fetch = function(input, init = {}) {
        // Only cache GET requests
        if (init.method && init.method !== 'GET') {
          return originalFetch(input, init);
        }
        
        const url = typeof input === 'string' ? input : input.url;
        const cacheKey = `fetch:${url}`;
        
        return window.WolfHuntAPICache.get(cacheKey, () => originalFetch(input, init));
      };
      
      this.applied.add('api-cache');
    }
    
    async optimizeAnimations() {
      if (this.applied.has('animations')) return;
      
      console.log('🎬 Optimizing animations...');
      
      // Prefer reduced motion for accessibility
      if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        document.documentElement.style.setProperty('--animation-duration', '0.01ms');
        return;
      }
      
      // Use CSS containment for better performance
      const style = document.createElement('style');
      style.textContent = `
        .animate-spin,
        .animate-pulse,
        .animate-bounce {
          contain: layout style paint;
        }
        
        /* Optimize hover effects */
        button, a, [role="button"] {
          contain: layout style;
          will-change: transform;
        }
        
        /* Optimize chart animations */
        canvas, svg {
          contain: layout style paint;
        }
        
        /* GPU acceleration for transforms */
        .transform,
        [class*="translate"],
        [class*="scale"],
        [class*="rotate"] {
          transform-style: preserve-3d;
          backface-visibility: hidden;
        }
      `;
      document.head.appendChild(style);
      
      this.applied.add('animations');
    }
    
    async setupLazyLoading() {
      if (this.applied.has('lazy-loading')) return;
      
      console.log('🔄 Setting up lazy loading...');
      
      // Intersection Observer for lazy loading components
      const observerOptions = {
        root: null,
        rootMargin: '100px', // Load 100px before entering viewport
        threshold: 0.1
      };
      
      const lazyObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const element = entry.target;
            
            // Lazy load images
            if (element.tagName === 'IMG' && element.dataset.src) {
              element.src = element.dataset.src;
              element.removeAttribute('data-src');
              lazyObserver.unobserve(element);
            }
            
            // Lazy load React components (if marked with data-lazy)
            if (element.dataset.lazy) {
              element.classList.add('loaded');
              lazyObserver.unobserve(element);
            }
          }
        });
      }, observerOptions);
      
      // Observe elements for lazy loading
      document.querySelectorAll('img[data-src], [data-lazy]').forEach(el => {
        lazyObserver.observe(el);
      });
      
      // Store observer for future use
      window.wolfhuntLazyObserver = lazyObserver;
      
      this.applied.add('lazy-loading');
    }
    
    async optimizeScrolling() {
      if (this.applied.has('scrolling')) return;
      
      console.log('📜 Optimizing scrolling...');
      
      // Passive event listeners for better scroll performance
      let ticking = false;
      
      function updateScrollPosition() {
        // Batch scroll updates
        if (ticking) return;
        
        requestAnimationFrame(() => {
          // Your scroll handling code here
          ticking = false;
        });
        
        ticking = true;
      }
      
      // Add passive listeners
      document.addEventListener('scroll', updateScrollPosition, { passive: true });
      document.addEventListener('wheel', function() {}, { passive: true });
      document.addEventListener('touchstart', function() {}, { passive: true });
      document.addEventListener('touchmove', function() {}, { passive: true });
      
      this.applied.add('scrolling');
    }
    
    async setupPerformanceMonitoring() {
      if (this.applied.has('monitoring')) return;
      
      console.log('📊 Setting up performance monitoring...');
      
      // Monitor Core Web Vitals
      if ('PerformanceObserver' in window) {
        try {
          // Largest Contentful Paint
          const lcpObserver = new PerformanceObserver((list) => {
            const entries = list.getEntries();
            const lastEntry = entries[entries.length - 1];
            this.performanceMetrics.lcp = lastEntry.startTime;
            console.log('📈 LCP:', Math.round(lastEntry.startTime), 'ms');
          });
          lcpObserver.observe({ type: 'largest-contentful-paint', buffered: true });
          
          // First Input Delay
          const fidObserver = new PerformanceObserver((list) => {
            const entries = list.getEntries();
            entries.forEach(entry => {
              this.performanceMetrics.fid = entry.processingStart - entry.startTime;
              console.log('📈 FID:', Math.round(entry.processingStart - entry.startTime), 'ms');
            });
          });
          fidObserver.observe({ type: 'first-input', buffered: true });
          
          // Cumulative Layout Shift
          let clsValue = 0;
          const clsObserver = new PerformanceObserver((list) => {
            const entries = list.getEntries();
            entries.forEach(entry => {
              if (!entry.hadRecentInput) {
                clsValue += entry.value;
              }
            });
            this.performanceMetrics.cls = clsValue;
            console.log('📈 CLS:', clsValue.toFixed(3));
          });
          clsObserver.observe({ type: 'layout-shift', buffered: true });
          
        } catch (error) {
          console.warn('Performance monitoring setup failed:', error);
        }
      }
      
      this.applied.add('monitoring');
    }
    
    reportPerformanceGains() {
      const totalTime = Math.round(performance.now() - this.startTime);
      const report = {
        optimizationsApplied: Array.from(this.applied),
        loadTime: totalTime,
        coreWebVitals: this.performanceMetrics,
        cacheStats: window.WolfHuntAPICache?.getStats(),
        timestamp: new Date().toISOString()
      };
      
      console.log('⚡ Performance optimizations applied:', report);
      
      // Store for debugging
      window.wolfhuntPerformance = report;
      
      // Send to analytics
      if (typeof gtag === 'function') {
        gtag('event', 'performance_optimized', {
          optimizations: report.optimizationsApplied.length,
          load_time: totalTime
        });
      }
    }
  }
  
  // Initialize performance enhancements
  document.addEventListener('DOMContentLoaded', () => {
    const enhancer = new PerformanceEnhancer();
    enhancer.initialize().catch(console.error);
  });
  
  // Also initialize if DOM is already loaded
  if (document.readyState !== 'loading') {
    const enhancer = new PerformanceEnhancer();
    enhancer.initialize().catch(console.error);
  }
  
})();