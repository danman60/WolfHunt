import { chromium } from 'playwright';

async function testFinalWolfConfigFix() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  // Track all types of errors
  const consoleErrors = [];
  const toLocaleStringErrors = [];
  const criticalErrors = [];
  
  page.on('console', msg => {
    if (msg.type() === 'error') {
      const errorText = msg.text();
      consoleErrors.push(errorText);
      
      if (errorText.includes('toLocaleString') || 
          errorText.includes('toFixed') ||
          errorText.includes('Cannot read properties of undefined')) {
        toLocaleStringErrors.push(errorText);
        console.log(`🚨 UNDEFINED DATA ERROR: ${errorText.substring(0, 100)}...`);
      } else if (errorText.includes('TypeError') || errorText.includes('ReferenceError')) {
        criticalErrors.push(errorText);
        console.log(`💥 CRITICAL ERROR: ${errorText.substring(0, 100)}...`);
      } else {
        console.log(`❌ Other Error: ${errorText.substring(0, 80)}...`);
      }
    }
  });

  try {
    console.log('🔍 Final test of Wolf Configuration fixes...');
    console.log('⏱️ Waiting 90 seconds for latest deployment...');
    await new Promise(resolve => setTimeout(resolve, 90000));
    
    // Navigate to the production site
    console.log('🌐 Loading production site...');
    await page.goto('https://wolfhunt.netlify.app/', { waitUntil: 'networkidle' });
    console.log('✅ Main dashboard loaded');
    
    // Wait for initial data load
    await page.waitForTimeout(5000);
    
    console.log('🖱️ Navigating to Wolf Configuration...');
    
    // Navigate to Wolf Configuration
    await page.click('a[href="/configuration"]');
    
    // Wait for navigation
    await page.waitForFunction(
      () => window.location.pathname === '/configuration',
      { timeout: 15000 }
    );
    console.log('✅ Navigation successful');
    
    // Wait extra time for components to render
    await page.waitForTimeout(10000);
    
    // Check if the page content is actually present and not blank
    const bodyText = await page.textContent('body');
    const hasWolfConfig = bodyText && bodyText.includes('Wolf Configuration');
    const hasStrategySettings = bodyText && bodyText.includes('Strategy');
    const hasPortfolioAllocation = bodyText && bodyText.includes('Portfolio');
    
    console.log('📊 Page content analysis:');
    console.log(`- Has "Wolf Configuration" text: ${hasWolfConfig ? '✅' : '❌'}`);
    console.log(`- Has strategy-related content: ${hasStrategySettings ? '✅' : '❌'}`);
    console.log(`- Has portfolio content: ${hasPortfolioAllocation ? '✅' : '❌'}`);
    
    // Check for specific interactive elements
    const strategyForm = await page.$('select, input[type="number"]');
    const hasInteractiveElements = !!strategyForm;
    console.log(`- Has interactive form elements: ${hasInteractiveElements ? '✅' : '❌'}`);
    
    // Try to interact with the page
    if (hasInteractiveElements) {
      try {
        await page.evaluate(() => window.scrollBy(0, 200));
        await page.waitForTimeout(2000);
        console.log('✅ Page interaction (scroll) successful');
      } catch (interactionError) {
        console.log(`⚠️ Page interaction failed: ${interactionError.message}`);
      }
    }
    
    // Monitor stability for 60 seconds
    console.log('🔄 Monitoring stability for 60 seconds...');
    const initialToLocaleErrors = toLocaleStringErrors.length;
    const initialCriticalErrors = criticalErrors.length;
    
    await page.waitForTimeout(60000);
    
    const finalToLocaleErrors = toLocaleStringErrors.length;
    const finalCriticalErrors = criticalErrors.length;
    
    const newToLocaleErrors = finalToLocaleErrors - initialToLocaleErrors;
    const newCriticalErrors = finalCriticalErrors - initialCriticalErrors;
    
    console.log('\n🎯 FINAL WOLF CONFIGURATION TEST RESULTS:');
    console.log(`==============================================`);
    console.log(`Total console errors: ${consoleErrors.length}`);
    console.log(`toLocaleString/undefined errors: ${finalToLocaleErrors}`);
    console.log(`Critical errors: ${finalCriticalErrors}`);
    console.log(`New undefined errors during 60s: ${newToLocaleErrors}`);
    console.log(`New critical errors during 60s: ${newCriticalErrors}`);
    console.log(`Page loads Wolf Configuration content: ${hasWolfConfig ? '✅ YES' : '❌ NO'}`);
    console.log(`Page has interactive elements: ${hasInteractiveElements ? '✅ YES' : '❌ NO'}`);
    
    // Final verdict
    if (hasWolfConfig && hasInteractiveElements && newToLocaleErrors === 0 && newCriticalErrors === 0) {
      console.log('\n🏆 ✅ SUCCESS: Wolf Configuration page is working correctly!');
      console.log('   - Page loads without blank screen');
      console.log('   - No new undefined data errors');
      console.log('   - Interactive elements are present');
      console.log('   - Page remains stable over time');
    } else if (hasWolfConfig && newToLocaleErrors === 0) {
      console.log('\n🟡 PARTIAL SUCCESS: Page loads but may have remaining issues');
      if (!hasInteractiveElements) console.log('   - Interactive elements missing');
      if (newCriticalErrors > 0) console.log('   - New critical errors detected');
    } else {
      console.log('\n❌ STILL FAILING: Major issues remain');
      if (!hasWolfConfig) console.log('   - Page content still not loading properly');
      if (newToLocaleErrors > 0) console.log('   - New undefined data errors still occurring');
      if (newCriticalErrors > 0) console.log('   - Critical errors present');
      
      console.log('\nRecent errors:');
      [...toLocaleStringErrors, ...criticalErrors].slice(-3).forEach((error, i) => {
        console.log(`  ${i + 1}. ${error.substring(0, 120)}...`);
      });
    }
    
  } catch (error) {
    console.error('❌ Test execution failed:', error.message);
  } finally {
    await browser.close();
  }
}

testFinalWolfConfigFix().catch(console.error);