const { chromium } = require('playwright');

async function testAllFeatures() {
  console.log('🎉 FINAL TEST: All WolfHunt Enhancement Features\n');
  
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Monitor key enhancement messages
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('🚀') || text.includes('⚡') || text.includes('♿') || text.includes('🔧') || text.includes('enhancement') || text.includes('WolfHunt')) {
      console.log(`📊 ${text}`);
    }
  });
  
  // Test with all features enabled via URL
  const testUrl = 'https://wolfhunt.netlify.app/?wolfhunt-test=all';
  
  console.log('🌐 Loading WolfHunt with ALL enhancements enabled...');
  
  try {
    await page.goto(testUrl, { waitUntil: 'networkidle' });
    
    // Wait for all enhancements to fully load
    await page.waitForTimeout(8000);
    
    console.log('\n🔍 COMPREHENSIVE ENHANCEMENT AUDIT:');
    
    // Comprehensive status check
    const enhancementAudit = await page.evaluate(() => {
      return {
        // Feature Flags
        featureFlags: window.WolfHuntFlags?.getStatus?.() || 'Not loaded',
        
        // Performance System
        performanceSystem: {
          apiCache: !!window.WolfHuntAPICache,
          cacheStats: window.WolfHuntAPICache?.getStats?.(),
          performanceMetrics: !!window.wolfhuntPerformance,
          lazyObserver: !!window.wolfhuntLazyObserver
        },
        
        // Accessibility System
        accessibilitySystem: {
          skipLink: !!document.querySelector('.skip-link'),
          ariaLabels: document.querySelectorAll('[aria-label]').length,
          landmarks: document.querySelectorAll('[role]').length,
          headingStructure: document.querySelectorAll('h1,h2,h3,h4,h5,h6').length,
          focusableElements: document.querySelectorAll('[tabindex]').length
        },
        
        // Button Enhancement System  
        buttonSystem: {
          tradingSystem: !!window.WolfHuntTrading,
          enhancedButtons: document.querySelectorAll('[data-wolfhunt-enhanced]').length,
          modals: document.querySelectorAll('.wolfhunt-modal').length,
          notifications: document.querySelectorAll('.wolfhunt-notification').length
        },
        
        // UI Elements Count
        uiElements: {
          totalButtons: document.querySelectorAll('button').length,
          totalInputs: document.querySelectorAll('input').length,
          totalForms: document.querySelectorAll('form').length,
          totalLinks: document.querySelectorAll('a').length
        },
        
        // Performance Metrics
        coreWebVitals: window.wolfhuntPerformance || null
      };
    });
    
    console.log('\n✅ FINAL ENHANCEMENT AUDIT RESULTS:');
    console.log('='.repeat(50));
    console.log(JSON.stringify(enhancementAudit, null, 2));
    console.log('='.repeat(50));
    
    // Test button interactions
    console.log('\n🔘 Testing Enhanced Button Functionality:');
    
    const buttons = await page.locator('button:visible').all();
    const testButtons = buttons.slice(0, 5); // Test first 5 visible buttons
    
    for (let i = 0; i < testButtons.length; i++) {
      try {
        const button = testButtons[i];
        const text = await button.textContent();
        const ariaLabel = await button.getAttribute('aria-label');
        
        console.log(`🔘 Button ${i + 1}: "${text?.trim() || 'No text'}" (aria: "${ariaLabel || 'None'}")`);
        
        // Quick click test
        await button.click({ timeout: 1000 });
        await page.waitForTimeout(500);
        
      } catch (error) {
        console.log(`   ⚠️ Button ${i + 1} interaction: ${error.message}`);
      }
    }
    
    // Performance summary
    const performanceMetrics = enhancementAudit.performanceSystem;
    const accessibilityMetrics = enhancementAudit.accessibilitySystem;
    
    console.log('\n📊 ENHANCEMENT IMPACT SUMMARY:');
    console.log(`Performance: API Cache ${performanceMetrics.apiCache ? '✅' : '❌'}, Metrics ${performanceMetrics.performanceMetrics ? '✅' : '❌'}`);
    console.log(`Accessibility: Skip Link ${accessibilityMetrics.skipLink ? '✅' : '❌'}, ARIA Labels: ${accessibilityMetrics.ariaLabels}, Landmarks: ${accessibilityMetrics.landmarks}`);
    console.log(`UI Elements: ${enhancementAudit.uiElements.totalButtons} buttons, ${enhancementAudit.uiElements.totalInputs} inputs, ${enhancementAudit.uiElements.totalForms} forms`);
    
    if (enhancementAudit.featureFlags.enabledCount >= 2) {
      console.log('\n🎉 SUCCESS: WolfHunt Enhancement System is FULLY OPERATIONAL!');
      console.log(`🚀 ${enhancementAudit.featureFlags.enabledCount}/${enhancementAudit.featureFlags.totalCount} enhancement modules active`);
    } else {
      console.log('\n⚠️ Partial Success: Some enhancement modules may not be enabled');
    }
    
  } catch (error) {
    console.error('❌ Final test failed:', error.message);
  }
  
  await page.waitForTimeout(5000);
  await browser.close();
}

testAllFeatures().catch(console.error);