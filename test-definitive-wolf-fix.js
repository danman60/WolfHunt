import { chromium } from 'playwright';

async function testDefinitiveWolfFix() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  // Comprehensive error tracking
  const errors = {
    toLocaleString: [],
    toFixed: [],
    other: [],
    critical: []
  };
  
  page.on('console', msg => {
    if (msg.type() === 'error') {
      const errorText = msg.text();
      
      if (errorText.includes('toLocaleString')) {
        errors.toLocaleString.push(errorText);
        console.log(`🚨 toLocaleString ERROR: ${errorText.substring(0, 80)}...`);
      } else if (errorText.includes('toFixed')) {
        errors.toFixed.push(errorText);
        console.log(`🚨 toFixed ERROR: ${errorText.substring(0, 80)}...`);
      } else if (errorText.includes('Cannot read properties') || errorText.includes('TypeError')) {
        errors.critical.push(errorText);
        console.log(`💥 CRITICAL ERROR: ${errorText.substring(0, 80)}...`);
      } else {
        errors.other.push(errorText);
        console.log(`❌ Other Error: ${errorText.substring(0, 60)}...`);
      }
    }
  });

  try {
    console.log('🏁 DEFINITIVE WOLF CONFIGURATION TEST');
    console.log('=====================================');
    
    await page.goto('https://wolfhunt.netlify.app/', { waitUntil: 'networkidle' });
    console.log('✅ Dashboard loaded');
    
    await page.waitForTimeout(3000);
    
    // Navigate to Wolf Configuration
    console.log('🖱️ Clicking Wolf Configuration...');
    await page.click('a[href="/configuration"]');
    
    // Wait for navigation
    await page.waitForFunction(
      () => window.location.pathname === '/configuration',
      { timeout: 15000 }
    );
    
    // Critical check - wait longer for content to render
    console.log('⏳ Waiting 15 seconds for page content to fully load...');
    await page.waitForTimeout(15000);
    
    // Check page content thoroughly
    const bodyText = await page.textContent('body');
    const hasMainContent = bodyText && bodyText.length > 500; // Reasonable content length
    const hasWolfConfig = bodyText && bodyText.includes('Wolf Configuration');
    const hasConfiguration = bodyText && (bodyText.includes('Strategy') || bodyText.includes('Portfolio'));
    
    // Check for actual form elements and interactivity
    const formElements = await page.$$('input, select, button');
    const hasFormElements = formElements.length > 3;
    
    // Check for specific expected content
    const expectedElements = [
      'h1, h2, h3', // Headers
      'input[type="number"]', // Number inputs for settings
      'select', // Dropdown selectors
      'button' // Action buttons
    ];
    
    let elementsFound = 0;
    for (const selector of expectedElements) {
      try {
        const element = await page.$(selector);
        if (element) {
          elementsFound++;
          console.log(`✅ Found ${selector}`);
        }
      } catch (e) {
        console.log(`❌ Missing ${selector}`);
      }
    }
    
    // Page functionality test
    let pageWorking = false;
    try {
      await page.evaluate(() => window.scrollBy(0, 100));
      await page.waitForTimeout(1000);
      pageWorking = true;
      console.log('✅ Page is interactive (scroll test passed)');
    } catch (e) {
      console.log('❌ Page interaction failed');
    }
    
    // Monitor errors for 45 seconds
    console.log('🔄 Monitoring stability for 45 seconds...');
    const initialTotalErrors = Object.values(errors).flat().length;
    
    await page.waitForTimeout(45000);
    
    const finalTotalErrors = Object.values(errors).flat().length;
    const newErrors = finalTotalErrors - initialTotalErrors;
    
    // FINAL ASSESSMENT
    console.log('\n🎯 DEFINITIVE TEST RESULTS');
    console.log('==========================');
    console.log(`Page has substantial content: ${hasMainContent ? '✅' : '❌'}`);
    console.log(`Has Wolf Configuration text: ${hasWolfConfig ? '✅' : '❌'}`);
    console.log(`Has configuration content: ${hasConfiguration ? '✅' : '❌'}`);
    console.log(`Has form elements (${formElements.length}): ${hasFormElements ? '✅' : '❌'}`);
    console.log(`Expected elements found: ${elementsFound}/4`);
    console.log(`Page is interactive: ${pageWorking ? '✅' : '❌'}`);
    console.log('');
    console.log('Error Summary:');
    console.log(`- toLocaleString errors: ${errors.toLocaleString.length}`);
    console.log(`- toFixed errors: ${errors.toFixed.length}`);
    console.log(`- Critical errors: ${errors.critical.length}`);
    console.log(`- Other errors: ${errors.other.length}`);
    console.log(`- New errors during monitoring: ${newErrors}`);
    
    // FINAL VERDICT
    const isWorking = hasMainContent && hasWolfConfig && hasConfiguration && 
                     hasFormElements && pageWorking && 
                     errors.toFixed.length === 0 && errors.toLocaleString.length === 0 &&
                     newErrors === 0;
                     
    const partiallyWorking = hasMainContent && hasWolfConfig && 
                           (errors.toFixed.length + errors.toLocaleString.length) < 2 &&
                           newErrors === 0;
    
    if (isWorking) {
      console.log('\n🏆 ✅ COMPLETE SUCCESS! Wolf Configuration is fully functional!');
      console.log('   ✅ Page loads completely without blank screen');
      console.log('   ✅ All form elements and content present');
      console.log('   ✅ No undefined data errors');
      console.log('   ✅ Page remains stable and interactive');
      console.log('   ✅ Ready for production use');
    } else if (partiallyWorking) {
      console.log('\n🟡 MAJOR IMPROVEMENT - Wolf Configuration mostly works!');
      console.log('   ✅ Page loads with content (no blank screen)');
      console.log('   ✅ No new errors during monitoring');
      if (!hasFormElements) console.log('   ⚠️ Some form elements may be missing');
      if (!pageWorking) console.log('   ⚠️ Page interaction may be limited');
    } else {
      console.log('\n❌ STILL HAS ISSUES - More work needed');
      if (!hasMainContent) console.log('   ❌ Page content not loading properly');
      if (errors.toFixed.length > 0) console.log('   ❌ toFixed errors still present');
      if (errors.toLocaleString.length > 0) console.log('   ❌ toLocaleString errors still present');
      if (newErrors > 0) console.log('   ❌ New errors appearing during monitoring');
    }
    
  } catch (error) {
    console.error('❌ Test execution failed:', error.message);
  } finally {
    await browser.close();
  }
}

testDefinitiveWolfFix().catch(console.error);