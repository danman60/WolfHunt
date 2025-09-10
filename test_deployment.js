const { chromium } = require('playwright');

async function testEnhancementSystem() {
  console.log('🧪 Testing WolfHunt Enhancement System on Live Deployment...\n');
  
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1200, height: 800 }
  });
  const page = await context.newPage();
  
  // Enable debug mode for feature flags
  const testUrl = 'https://wolfhunt.netlify.app/?debug=true&performance-fixes=true&accessibility-fixes=true&button-functionality=true';
  
  console.log('🌐 Loading WolfHunt with enhancement flags enabled...');
  
  // Monitor console logs
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('WolfHunt') || text.includes('⚡') || text.includes('♿') || text.includes('🔧')) {
      console.log(`📊 ${text}`);
    }
  });
  
  // Monitor network failures
  page.on('response', response => {
    if (response.status() >= 400) {
      console.log(`❌ Failed to load: ${response.url()} (${response.status()})`);
    }
  });
  
  try {
    await page.goto(testUrl, { waitUntil: 'networkidle' });
    
    // Wait for React to load
    await page.waitForTimeout(3000);
    
    console.log('\n🔍 Checking Enhancement System Status:');
    
    // Test feature flags system
    const featureFlags = await page.evaluate(() => {
      return window.WolfHuntFlags ? {
        loaded: true,
        flags: window.WolfHuntFlags.flags,
        debugMode: window.WolfHuntFlags.debugMode
      } : { loaded: false };
    });
    
    console.log('Feature Flags:', featureFlags);
    
    // Test performance system
    const performanceData = await page.evaluate(() => {
      return window.wolfhuntPerformance || 'Not loaded';
    });
    
    console.log('Performance System:', performanceData);
    
    // Test accessibility fixes
    const accessibilityData = await page.evaluate(() => {
      const skipLink = document.querySelector('.skip-link');
      const ariaLabels = document.querySelectorAll('[aria-label]').length;
      return {
        skipLinkPresent: !!skipLink,
        ariaLabelsCount: ariaLabels,
        headingStructure: Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,h6')).map(h => h.tagName)
      };
    });
    
    console.log('Accessibility Enhancements:', accessibilityData);
    
    // Test button functionality
    console.log('\n🔘 Testing Button Functionality:');
    
    const buttonTests = [
      { selector: 'button[aria-label="Connect Wallet"]', description: 'Connect Wallet' },
      { selector: 'button:has-text("Start Trading")', description: 'Start Trading' },
      { selector: 'button:has-text("Settings")', description: 'Settings' },
      { selector: 'button:has-text("Refresh")', description: 'Refresh Data' }
    ];
    
    for (const test of buttonTests) {
      try {
        const button = page.locator(test.selector).first();
        if (await button.count() > 0) {
          console.log(`✅ ${test.description} button found and enhanced`);
          
          // Test click functionality
          await button.click({ timeout: 1000 });
          await page.waitForTimeout(500);
          
          // Check for modal or notification
          const modal = await page.evaluate(() => {
            return document.querySelector('.wolfhunt-modal') ? 'Modal opened' : 'No modal';
          });
          console.log(`   ${modal}`);
        } else {
          console.log(`❌ ${test.description} button not found`);
        }
      } catch (error) {
        console.log(`⚠️ ${test.description} test error: ${error.message}`);
      }
    }
    
    // Test API cache
    console.log('\n💾 Testing API Cache:');
    const cacheStats = await page.evaluate(() => {
      return window.WolfHuntAPICache ? window.WolfHuntAPICache.getStats() : 'Cache not loaded';
    });
    console.log('API Cache Stats:', cacheStats);
    
    console.log('\n✅ Enhancement system testing completed!');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  }
  
  await browser.close();
}

// Run the test
testEnhancementSystem().catch(console.error);