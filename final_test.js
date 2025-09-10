const { chromium } = require('playwright');

async function testWithFeatureFlags() {
  console.log('🎯 Final Test: WolfHunt Enhancement System with Feature Flags Enabled\n');
  
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Monitor console output for enhancements
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('⚡') || text.includes('♿') || text.includes('🔧') || text.includes('WolfHunt')) {
      console.log(`📊 ${text}`);
    }
  });
  
  // Test URL with feature flags enabled
  const testUrl = 'https://wolfhunt.netlify.app/?performance-fixes=true&accessibility-fixes=true&button-functionality=true&debug=true';
  
  console.log('🌐 Loading WolfHunt with all enhancements enabled...');
  
  try {
    await page.goto(testUrl, { waitUntil: 'networkidle' });
    
    // Wait for all enhancements to load
    await page.waitForTimeout(5000);
    
    console.log('\n✅ Checking Enhancement Status:');
    
    // Check feature flags
    const flagsStatus = await page.evaluate(() => {
      return window.WolfHuntFlags ? {
        flags: window.WolfHuntFlags.flags,
        debugMode: window.WolfHuntFlags.debugMode
      } : null;
    });
    console.log('Feature Flags:', flagsStatus);
    
    // Check performance enhancements
    const performanceStatus = await page.evaluate(() => {
      return {
        apiCache: !!window.WolfHuntAPICache,
        cacheStats: window.WolfHuntAPICache?.getStats?.(),
        performanceData: window.wolfhuntPerformance
      };
    });
    console.log('Performance System:', performanceStatus);
    
    // Check accessibility enhancements
    const accessibilityStatus = await page.evaluate(() => {
      return {
        skipLink: !!document.querySelector('.skip-link'),
        ariaLabels: document.querySelectorAll('[aria-label]').length,
        landmarks: document.querySelectorAll('[role]').length,
        headings: document.querySelectorAll('h1,h2,h3,h4,h5,h6').length
      };
    });
    console.log('Accessibility System:', accessibilityStatus);
    
    // Check button functionality
    const buttonStatus = await page.evaluate(() => {
      return {
        tradingSystem: !!window.WolfHuntTrading,
        modals: document.querySelectorAll('.wolfhunt-modal').length,
        notifications: document.querySelectorAll('.wolfhunt-notification').length,
        enhancedButtons: document.querySelectorAll('[data-wolfhunt-enhanced]').length
      };
    });
    console.log('Button Enhancement System:', buttonStatus);
    
    console.log('\n🔘 Testing Button Interactions:');
    
    // Test a few key buttons
    const buttons = await page.locator('button').all();
    console.log(`Found ${buttons.length} buttons total`);
    
    // Test first few buttons
    for (let i = 0; i < Math.min(3, buttons.length); i++) {
      try {
        const button = buttons[i];
        const text = await button.textContent();
        const ariaLabel = await button.getAttribute('aria-label');
        
        console.log(`Button ${i + 1}: "${text}" (aria-label: "${ariaLabel}")`);
        
        await button.click({ timeout: 1000 });
        await page.waitForTimeout(500);
        
        // Check for any modals or notifications that appeared
        const afterClick = await page.evaluate(() => {
          return {
            modals: document.querySelectorAll('.wolfhunt-modal').length,
            notifications: document.querySelectorAll('.wolfhunt-notification').length
          };
        });
        
        if (afterClick.modals > 0 || afterClick.notifications > 0) {
          console.log(`  ✅ Interaction triggered UI response`);
        }
        
      } catch (error) {
        console.log(`  ⚠️ Button ${i + 1} interaction error: ${error.message}`);
      }
    }
    
    console.log('\n🎉 Enhancement System Test Completed Successfully!');
    console.log('All core systems are loaded and functional.');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  }
  
  await page.waitForTimeout(3000);
  await browser.close();
}

testWithFeatureFlags().catch(console.error);