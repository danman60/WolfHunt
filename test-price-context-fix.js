import { chromium } from 'playwright';

async function testPriceContextFix() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  // Track specific errors
  const errors = {
    bodyStream: [],
    wolfPack: [],
    priceUpdates: [],
    navigation: []
  };
  
  let priceUpdateCount = 0;
  let lastPriceUpdate = Date.now();
  
  page.on('console', msg => {
    if (msg.type() === 'error') {
      const errorText = msg.text();
      const timestamp = new Date().toLocaleTimeString();
      
      if (errorText.includes('body stream already read')) {
        errors.bodyStream.push({ time: timestamp, error: errorText });
        console.log(`🚨 [${timestamp}] BODY STREAM ERROR: ${errorText.substring(0, 120)}...`);
      } else if (errorText.includes('Wolf Pack intelligence unavailable')) {
        errors.wolfPack.push({ time: timestamp, error: errorText });
        console.log(`🐺 [${timestamp}] WOLF PACK ERROR: ${errorText.substring(0, 120)}...`);
      } else {
        console.log(`❌ [${timestamp}] OTHER ERROR: ${errorText.substring(0, 80)}...`);
      }
    } else if (msg.type() === 'log' && (msg.text().includes('prices loaded') || msg.text().includes('CoinGecko'))) {
      priceUpdateCount++;
      lastPriceUpdate = Date.now();
      console.log(`📈 [${new Date().toLocaleTimeString()}] Price update #${priceUpdateCount}`);
    }
  });

  try {
    console.log('🔍 Testing centralized price context fixes...');
    console.log('Target: Stable price feeds during navigation');
    console.log('===========================================');
    
    await page.goto('https://wolfhunt.netlify.app/', { waitUntil: 'networkidle' });
    console.log('✅ Dashboard loaded');
    
    const startTime = Date.now();
    const testDuration = 8 * 60 * 1000; // 8 minutes test
    
    // Navigation sequence - test the problem areas
    const navSequence = [
      { path: '/', name: 'Dashboard' },
      { path: '/intelligence', name: 'Intelligence' },
      { path: '/configuration', name: 'Wolf Configuration' },
      { path: '/', name: 'Dashboard' },
      { path: '/intelligence', name: 'Intelligence' },
      { path: '/configuration', name: 'Wolf Configuration' }
    ];
    
    let navIndex = 0;
    let lastNavigation = Date.now();
    const navigationInterval = 60 * 1000; // Navigate every 60 seconds
    
    // Monitor loop
    while (Date.now() - startTime < testDuration) {
      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      
      // Navigate if it's time
      if (Date.now() - lastNavigation >= navigationInterval) {
        const nav = navSequence[navIndex % navSequence.length];
        
        try {
          console.log(`🧭 [${new Date().toLocaleTimeString()}] Navigating to ${nav.name}`);
          await page.click(`a[href="${nav.path}"]`);
          
          await page.waitForFunction(
            (expectedPath) => window.location.pathname === expectedPath,
            nav.path,
            { timeout: 8000 }
          );
          
          await page.waitForTimeout(5000); // Let page settle
          
          console.log(`✅ [${new Date().toLocaleTimeString()}] Navigation to ${nav.name} successful`);
          lastNavigation = Date.now();
          navIndex++;
          
        } catch (navError) {
          console.log(`❌ [${new Date().toLocaleTimeString()}] Navigation failed: ${navError.message}`);
          errors.navigation.push({ time: new Date().toLocaleTimeString(), error: navError.message });
        }
      }
      
      // Check for stale price feeds
      const timeSincePrice = Date.now() - lastPriceUpdate;
      if (timeSincePrice > 90000) { // 90 seconds stale
        console.log(`⚠️ [${new Date().toLocaleTimeString()}] Price feeds stale: ${Math.floor(timeSincePrice/1000)}s`);
      }
      
      // Progress update
      if (elapsed % 60 === 0 && elapsed > 0) {
        console.log(`⏱️ [${new Date().toLocaleTimeString()}] ${Math.floor(elapsed/60)}m elapsed - ${priceUpdateCount} price updates`);
        console.log(`   🚨 Errors: ${errors.bodyStream.length} body stream, ${errors.wolfPack.length} wolf pack`);
      }
      
      await page.waitForTimeout(1000);
    }
    
    console.log('\n🎯 PRICE CONTEXT FIX TEST RESULTS');
    console.log('=================================');
    
    const totalMinutes = Math.floor((Date.now() - startTime) / 60000);
    const priceRate = priceUpdateCount / totalMinutes;
    
    console.log(`Test Duration: ${totalMinutes} minutes`);
    console.log(`Price Updates: ${priceUpdateCount} (${priceRate.toFixed(1)}/min)`);
    console.log(`Navigation Count: ${navIndex}`);
    console.log('');
    console.log('Error Summary:');
    console.log(`- Body Stream Errors: ${errors.bodyStream.length}`);
    console.log(`- Wolf Pack Errors: ${errors.wolfPack.length}`);
    console.log(`- Navigation Errors: ${errors.navigation.length}`);
    
    // Assessment
    const priceStability = priceRate >= 1.8; // Should be ~2 per minute
    const lowErrors = errors.bodyStream.length <= 1; // Allow 1 initial error
    const navigationWorks = errors.navigation.length === 0;
    
    console.log('\n📊 FIX ASSESSMENT:');
    console.log(`Price Feed Consistency: ${priceStability ? '✅ IMPROVED' : '❌ STILL BROKEN'} (${priceRate.toFixed(1)}/min)`);
    console.log(`Error Reduction: ${lowErrors ? '✅ SUCCESS' : '❌ STILL FAILING'} (${errors.bodyStream.length} body stream errors)`);
    console.log(`Navigation Stability: ${navigationWorks ? '✅ WORKING' : '❌ BROKEN'}`);
    
    if (priceStability && lowErrors && navigationWorks) {
      console.log('\n🏆 ✅ PRICE CONTEXT FIX SUCCESSFUL!');
      console.log('Price feeds now stable during navigation');
      return true;
    } else {
      console.log('\n❌ PRICE CONTEXT FIX INCOMPLETE - Need more work');
      
      if (!priceStability) {
        console.log('  - Price feeds still not consistent enough');
      }
      if (!lowErrors) {
        console.log('  - Body stream errors still occurring');
        console.log('Recent body stream errors:');
        errors.bodyStream.slice(-2).forEach((err, i) => {
          console.log(`    ${i+1}. [${err.time}] ${err.error.substring(0, 100)}...`);
        });
      }
      if (!navigationWorks) {
        console.log('  - Navigation still has issues');
      }
      
      return false;
    }
    
  } catch (error) {
    console.error('❌ Test execution failed:', error.message);
    return false;
  } finally {
    await browser.close();
  }
}

testPriceContextFix().then(success => {
  if (success) {
    console.log('\n✅ Ready to proceed with Wolf Pack fix and golden test!');
  } else {
    console.log('\n🔧 Need to debug and fix remaining issues');
  }
}).catch(console.error);