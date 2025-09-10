const { chromium } = require('playwright');

async function testCorrectFlags() {
  console.log('🎯 Testing with correct flag URL parameters\n');
  
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Monitor all console output
  page.on('console', msg => {
    console.log(`📟 ${msg.text()}`);
  });
  
  // Use correct URL parameter format OR test-all shortcut
  const testUrl = 'https://wolfhunt.netlify.app/?wolfhunt-test=all';
  
  console.log('🌐 Loading with wolfhunt-test=all parameter...');
  
  try {
    await page.goto(testUrl, { waitUntil: 'networkidle' });
    
    // Wait for enhancements to load
    await page.waitForTimeout(8000);
    
    console.log('\n🔍 Final Status Check:');
    
    const finalStatus = await page.evaluate(() => {
      return {
        flags: window.WolfHuntFlags?.flags,
        apiCache: !!window.WolfHuntAPICache,
        performance: !!window.wolfhuntPerformance,
        trading: !!window.WolfHuntTrading,
        skipLink: !!document.querySelector('.skip-link'),
        enhancedButtons: document.querySelectorAll('[data-wolfhunt-enhanced]').length,
        modals: document.querySelectorAll('.wolfhunt-modal').length
      };
    });
    
    console.log('\n✅ FINAL ENHANCEMENT STATUS:');
    console.log(JSON.stringify(finalStatus, null, 2));
    
    if (finalStatus.flags && Object.values(finalStatus.flags).some(f => f)) {
      console.log('\n🎉 SUCCESS: Feature flags are working!');
    } else {
      console.log('\n❌ Issue: Feature flags still not enabling');
    }
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  }
  
  await page.waitForTimeout(5000);
  await browser.close();
}

testCorrectFlags().catch(console.error);