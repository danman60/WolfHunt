import { chromium } from 'playwright';

async function testWolfHuntFixes() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  // Listen for console errors
  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
      console.log(`❌ Console Error: ${msg.text()}`);
    } else if (msg.type() === 'warn') {
      console.log(`⚠️ Console Warning: ${msg.text()}`);
    }
  });

  try {
    console.log('🔍 Testing WolfHunt production site fixes...');
    
    // Navigate to the production site
    await page.goto('https://wolfhunt.netlify.app/', { waitUntil: 'networkidle' });
    
    console.log('📊 Monitoring for 60 seconds to check for body stream errors...');
    
    // Wait for 60 seconds to monitor price feeds and dashboard updates
    await page.waitForTimeout(60000);
    
    // Check if side menu navigation still works after the wait
    console.log('🧪 Testing side menu navigation after 60 seconds...');
    
    // Try clicking on different menu items
    const menuItems = [
      { selector: 'a[href="/"]', name: 'Dashboard' },
      { selector: 'a[href="/positions"]', name: 'Positions' },
      { selector: 'a[href="/trades"]', name: 'Trades' },
      { selector: 'a[href="/wolf-configuration"]', name: 'Wolf Configuration' },
      { selector: 'a[href="/performance"]', name: 'Performance' }
    ];
    
    for (const item of menuItems) {
      try {
        console.log(`🖱️ Clicking on ${item.name}...`);
        await page.click(item.selector);
        await page.waitForTimeout(3000); // Wait 3 seconds
        
        // Check if page loaded without JavaScript errors
        const currentUrl = page.url();
        console.log(`✅ ${item.name} loaded: ${currentUrl}`);
        
      } catch (error) {
        console.log(`❌ Failed to navigate to ${item.name}: ${error.message}`);
      }
    }
    
    // Return to dashboard for final check
    await page.click('a[href="/"]');
    await page.waitForTimeout(5000);
    
    console.log('📈 Final check - monitoring price updates for 30 more seconds...');
    await page.waitForTimeout(30000);
    
    // Summary
    const bodyStreamErrors = consoleErrors.filter(error => 
      error.includes('body stream already read') || 
      error.includes('Failed to execute \'text\' on \'Response\'') ||
      error.includes('Failed to execute \'json\' on \'Response\'')
    );
    
    console.log('\n🎯 TEST RESULTS:');
    console.log(`Total console errors: ${consoleErrors.length}`);
    console.log(`Body stream errors: ${bodyStreamErrors.length}`);
    
    if (bodyStreamErrors.length === 0) {
      console.log('✅ SUCCESS: No body stream errors detected!');
    } else {
      console.log('❌ FAILED: Body stream errors still present:');
      bodyStreamErrors.forEach(error => console.log(`  - ${error}`));
    }
    
  } catch (error) {
    console.error('Test failed:', error);
  } finally {
    await browser.close();
  }
}

testWolfHuntFixes().catch(console.error);