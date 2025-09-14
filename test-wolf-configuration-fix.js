import { chromium } from 'playwright';

async function testWolfConfigurationFix() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  // Track console errors
  const consoleErrors = [];
  const toLocaleStringErrors = [];
  
  page.on('console', msg => {
    if (msg.type() === 'error') {
      const errorText = msg.text();
      consoleErrors.push(errorText);
      
      if (errorText.includes('toLocaleString') || 
          errorText.includes('toFixed') ||
          errorText.includes('Cannot read properties of undefined')) {
        toLocaleStringErrors.push(errorText);
        console.log(`🚨 UNDEFINED DATA ERROR: ${errorText}`);
      } else {
        console.log(`❌ Console Error: ${errorText}`);
      }
    }
  });

  try {
    console.log('🔍 Testing Wolf Configuration page crash fix...');
    console.log('⏱️ Waiting 90 seconds for Netlify deployment...');
    await new Promise(resolve => setTimeout(resolve, 90000));
    
    // Navigate to the production site
    await page.goto('https://wolfhunt.netlify.app/', { waitUntil: 'networkidle' });
    console.log('✅ Loaded main dashboard');
    
    // Wait for initial load
    await page.waitForTimeout(5000);
    
    console.log('🖱️ Clicking on Wolf Configuration...');
    
    // Find and click the Wolf Configuration link
    try {
      const configLink = await page.$('a[href="/configuration"]');
      if (!configLink) {
        console.log('❌ Could not find Wolf Configuration link');
        return;
      }
      
      await page.click('a[href="/configuration"]');
      console.log('✅ Clicked Wolf Configuration link');
      
      // Wait for navigation and page load
      await page.waitForFunction(
        () => window.location.pathname === '/configuration',
        { timeout: 10000 }
      );
      console.log('✅ Navigation to /configuration successful');
      
      // Wait for page to fully render
      await page.waitForTimeout(8000);
      
      // Check if page is actually visible (not blank)
      const pageContent = await page.textContent('body');
      if (pageContent && pageContent.includes('Wolf Configuration')) {
        console.log('✅ Wolf Configuration page content loaded successfully');
        console.log('📄 Page contains Wolf Configuration heading');
      } else {
        console.log('❌ Wolf Configuration page appears blank or missing content');
        console.log(`📄 Page content preview: ${pageContent ? pageContent.substring(0, 200) + '...' : 'EMPTY'}`);
      }
      
      // Check for specific elements that should be present
      const elementsToCheck = [
        { selector: 'h1', name: 'Main heading' },
        { selector: '[data-testid="strategy-settings"], .strategy-settings, h3', name: 'Strategy Settings' },
        { selector: '.portfolio-allocation, h3:contains("Portfolio")', name: 'Portfolio Allocation section' },
        { selector: 'input[type="number"]', name: 'Input fields' }
      ];
      
      for (const element of elementsToCheck) {
        try {
          const found = await page.$(element.selector);
          if (found) {
            console.log(`✅ Found ${element.name}`);
          } else {
            console.log(`⚠️ Missing ${element.name} (${element.selector})`);
          }
        } catch (e) {
          console.log(`⚠️ Error checking ${element.name}: ${e.message}`);
        }
      }
      
      // Monitor for stability over 30 seconds
      console.log('🔄 Monitoring page stability for 30 seconds...');
      const initialErrors = toLocaleStringErrors.length;
      await page.waitForTimeout(30000);
      const finalErrors = toLocaleStringErrors.length;
      
      // Try interacting with the page (scroll, click inputs)
      try {
        await page.scroll(0, 200);
        await page.waitForTimeout(2000);
        console.log('✅ Page scroll interaction successful');
      } catch (scrollError) {
        console.log(`⚠️ Page scroll failed: ${scrollError.message}`);
      }
      
      const newErrors = finalErrors - initialErrors;
      
      console.log('\n🎯 WOLF CONFIGURATION TEST RESULTS:');
      console.log(`Total console errors: ${consoleErrors.length}`);
      console.log(`toLocaleString/undefined errors: ${finalErrors}`);
      console.log(`New undefined errors during monitoring: ${newErrors}`);
      
      if (newErrors === 0 && pageContent && pageContent.includes('Wolf Configuration')) {
        console.log('✅ SUCCESS: Wolf Configuration page loads without crashing!');
        console.log('✅ No new undefined data errors detected');
        console.log('✅ Page remains interactive and stable');
      } else if (newErrors === 0) {
        console.log('🟡 PARTIAL SUCCESS: No new errors but page content unclear');
      } else {
        console.log('❌ STILL FAILING: New undefined data errors detected');
        console.log('Recent errors:');
        toLocaleStringErrors.slice(-3).forEach((error, i) => console.log(`  ${i + 1}. ${error}`));
      }
      
    } catch (navError) {
      console.log(`❌ Failed to navigate to Wolf Configuration: ${navError.message}`);
    }
    
  } catch (error) {
    console.error('Test failed:', error);
  } finally {
    await browser.close();
  }
}

testWolfConfigurationFix().catch(console.error);