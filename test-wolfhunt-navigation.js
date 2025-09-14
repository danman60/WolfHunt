import { chromium } from 'playwright';

async function testNavigationAfterFixes() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  // Listen for console errors
  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
      console.log(`❌ Console Error: ${msg.text()}`);
    } else if (msg.type() === 'warn' && msg.text().includes('body stream')) {
      console.log(`⚠️ Body stream warning: ${msg.text()}`);
    }
  });

  try {
    console.log('🔍 Testing WolfHunt navigation after body stream fixes...');
    
    // Navigate to the production site
    await page.goto('https://wolfhunt.netlify.app/', { waitUntil: 'networkidle' });
    console.log('✅ Loaded main dashboard');
    
    // Wait for initial data load
    await page.waitForTimeout(5000);
    
    console.log('🧪 Testing left navigation to all sub-pages...');
    
    const navigationTests = [
      { 
        selector: 'a[href="/positions"]', 
        name: 'Positions', 
        expectedUrl: '/positions',
        waitForSelector: '.positions-grid, .no-positions, h1, h2' // Any of these indicate page loaded
      },
      { 
        selector: 'a[href="/trades"]', 
        name: 'Trades', 
        expectedUrl: '/trades',
        waitForSelector: '.trades-table, .no-trades, h1, h2'
      },
      { 
        selector: 'a[href="/wolf-configuration"]', 
        name: 'Wolf Configuration', 
        expectedUrl: '/wolf-configuration',
        waitForSelector: '.config-form, .strategy-config, h1, h2'
      },
      { 
        selector: 'a[href="/performance"]', 
        name: 'Performance', 
        expectedUrl: '/performance',
        waitForSelector: '.performance-chart, .metrics-grid, h1, h2'
      },
      { 
        selector: 'a[href="/"]', 
        name: 'Dashboard (return)', 
        expectedUrl: '/',
        waitForSelector: '.dashboard-grid, .bot-status'
      }
    ];
    
    for (const test of navigationTests) {
      try {
        console.log(`🖱️ Testing navigation to ${test.name}...`);
        
        // Click the navigation link
        await page.click(test.selector);
        
        // Wait for URL to change
        await page.waitForFunction(
          (expectedUrl) => window.location.pathname === expectedUrl,
          test.expectedUrl,
          { timeout: 10000 }
        );
        
        // Wait for page content to load
        try {
          await page.waitForSelector(test.waitForSelector, { timeout: 8000 });
          console.log(`✅ ${test.name} page loaded successfully`);
        } catch (selectorError) {
          console.log(`⚠️ ${test.name} page loaded but expected content not found (selector: ${test.waitForSelector})`);
        }
        
        // Wait a moment for any API calls to settle
        await page.waitForTimeout(3000);
        
        const currentUrl = page.url();
        console.log(`📍 Current URL: ${currentUrl}`);
        
      } catch (error) {
        console.log(`❌ Failed to navigate to ${test.name}: ${error.message}`);
      }
    }
    
    console.log('\n🔄 Testing stability - monitoring for 30 seconds...');
    const errorsBefore = consoleErrors.length;
    await page.waitForTimeout(30000);
    const errorsAfter = consoleErrors.length;
    
    // Check for specific body stream errors
    const bodyStreamErrors = consoleErrors.filter(error => 
      error.includes('body stream already read') || 
      error.includes('Failed to execute \'text\' on \'Response\'') ||
      error.includes('Failed to execute \'json\' on \'Response\'')
    );
    
    console.log('\n🎯 NAVIGATION TEST RESULTS:');
    console.log(`Total console errors: ${consoleErrors.length}`);
    console.log(`Body stream errors: ${bodyStreamErrors.length}`);
    console.log(`New errors during 30s monitoring: ${errorsAfter - errorsBefore}`);
    
    if (bodyStreamErrors.length === 0) {
      console.log('✅ SUCCESS: No body stream errors detected!');
      console.log('✅ Navigation appears to be working correctly');
    } else {
      console.log('❌ STILL FAILING: Body stream errors detected:');
      bodyStreamErrors.forEach((error, i) => console.log(`  ${i + 1}. ${error}`));
    }
    
  } catch (error) {
    console.error('Navigation test failed:', error);
  } finally {
    await browser.close();
  }
}

testNavigationAfterFixes().catch(console.error);