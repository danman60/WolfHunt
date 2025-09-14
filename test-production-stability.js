import { chromium } from 'playwright';

async function testProductionStability() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  // Comprehensive error tracking
  const errors = {
    bodyStream: [],
    wolfPack: [],
    priceFeeds: [],
    navigation: [],
    other: []
  };
  
  let lastPriceUpdate = Date.now();
  let priceUpdateCount = 0;
  let navigationCount = 0;
  
  page.on('console', msg => {
    if (msg.type() === 'error') {
      const errorText = msg.text();
      const timestamp = new Date().toLocaleTimeString();
      
      if (errorText.includes('body stream already read')) {
        errors.bodyStream.push({ time: timestamp, error: errorText });
        console.log(`🚨 [${timestamp}] BODY STREAM ERROR: ${errorText.substring(0, 100)}...`);
      } else if (errorText.includes('Wolf Pack intelligence unavailable')) {
        errors.wolfPack.push({ time: timestamp, error: errorText });
        console.log(`🚨 [${timestamp}] WOLF PACK ERROR: ${errorText.substring(0, 100)}...`);
      } else if (errorText.includes('price') || errorText.includes('CoinGecko') || errorText.includes('GMX')) {
        errors.priceFeeds.push({ time: timestamp, error: errorText });
        console.log(`📈 [${timestamp}] PRICE FEED ERROR: ${errorText.substring(0, 100)}...`);
      } else if (errorText.includes('navigation') || errorText.includes('route')) {
        errors.navigation.push({ time: timestamp, error: errorText });
        console.log(`🧭 [${timestamp}] NAVIGATION ERROR: ${errorText.substring(0, 100)}...`);
      } else {
        errors.other.push({ time: timestamp, error: errorText });
        console.log(`❌ [${timestamp}] OTHER ERROR: ${errorText.substring(0, 80)}...`);
      }
    } else if (msg.type() === 'log' && msg.text().includes('prices loaded')) {
      lastPriceUpdate = Date.now();
      priceUpdateCount++;
      console.log(`📈 [${new Date().toLocaleTimeString()}] Price update #${priceUpdateCount}`);
    }
  });

  try {
    console.log('🔍 PRODUCTION STABILITY TEST - Starting...');
    console.log('Target: 10+ minutes price stability + navigation testing');
    console.log('=======================================================');
    
    await page.goto('https://wolfhunt.netlify.app/', { waitUntil: 'networkidle' });
    console.log('✅ Dashboard loaded');
    
    const startTime = Date.now();
    const testDuration = 12 * 60 * 1000; // 12 minutes
    const navigationInterval = 45 * 1000; // Navigate every 45 seconds
    
    // Navigation sequence
    const navSequence = [
      { path: '/', name: 'Dashboard', wait: 8000 },
      { path: '/intelligence', name: 'Intelligence Brief', wait: 8000 },
      { path: '/configuration', name: 'Wolf Configuration', wait: 10000 },
      { path: '/history', name: 'History', wait: 8000 },
      { path: '/risk', name: 'Risk Management', wait: 8000 },
      { path: '/alerts', name: 'Alerts', wait: 8000 }
    ];
    
    let navIndex = 0;
    let lastNavigation = Date.now();
    
    // Main monitoring loop
    while (Date.now() - startTime < testDuration) {
      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      const remaining = Math.floor((testDuration - (Date.now() - startTime)) / 1000);
      
      // Navigate if it's time
      if (Date.now() - lastNavigation >= navigationInterval) {
        const nav = navSequence[navIndex % navSequence.length];
        
        try {
          console.log(`🧭 [${new Date().toLocaleTimeString()}] Navigating to ${nav.name} (${nav.path})`);
          
          // Click navigation link
          await page.click(`a[href="${nav.path}"]`);
          
          // Wait for navigation
          await page.waitForFunction(
            (expectedPath) => window.location.pathname === expectedPath,
            nav.path,
            { timeout: 8000 }
          );
          
          // Wait for page to settle
          await page.waitForTimeout(nav.wait);
          
          navigationCount++;
          lastNavigation = Date.now();
          navIndex++;
          
          console.log(`✅ [${new Date().toLocaleTimeString()}] Navigation #${navigationCount} to ${nav.name} successful`);
          
        } catch (navError) {
          console.log(`❌ [${new Date().toLocaleTimeString()}] Navigation to ${nav.name} failed: ${navError.message}`);
          errors.navigation.push({ 
            time: new Date().toLocaleTimeString(), 
            error: `Navigation to ${nav.name} failed: ${navError.message}` 
          });
        }
      }
      
      // Check price feed freshness
      const timeSinceLastPrice = Date.now() - lastPriceUpdate;
      if (timeSinceLastPrice > 90000) { // 90 seconds without price update
        console.log(`⚠️ [${new Date().toLocaleTimeString()}] Price feeds may be stale (${Math.floor(timeSinceLastPrice/1000)}s since last update)`);
      }
      
      // Progress update every 30 seconds
      if (elapsed % 30 === 0) {
        console.log(`⏱️ [${new Date().toLocaleTimeString()}] Progress: ${Math.floor(elapsed/60)}m ${elapsed%60}s / ${Math.floor(testDuration/60000)}m (${remaining}s remaining)`);
        console.log(`   📊 Stats: ${priceUpdateCount} price updates, ${navigationCount} navigations`);
        console.log(`   🚨 Errors: ${errors.bodyStream.length} body stream, ${errors.wolfPack.length} wolf pack, ${errors.priceFeeds.length} price feed`);
      }
      
      await page.waitForTimeout(1000); // Check every second
    }
    
    console.log('\n🎯 PRODUCTION STABILITY TEST RESULTS');
    console.log('====================================');
    
    const totalMinutes = Math.floor((Date.now() - startTime) / 60000);
    const priceUpdatesPerMinute = priceUpdateCount / totalMinutes;
    
    console.log(`Test Duration: ${totalMinutes} minutes`);
    console.log(`Price Updates: ${priceUpdateCount} (${priceUpdatesPerMinute.toFixed(1)}/min)`);
    console.log(`Navigations: ${navigationCount}`);
    console.log('');
    console.log('ERROR SUMMARY:');
    console.log(`- Body Stream Errors: ${errors.bodyStream.length}`);
    console.log(`- Wolf Pack Intelligence Errors: ${errors.wolfPack.length}`);
    console.log(`- Price Feed Errors: ${errors.priceFeeds.length}`);
    console.log(`- Navigation Errors: ${errors.navigation.length}`);
    console.log(`- Other Errors: ${errors.other.length}`);
    
    // Print recent errors for analysis
    if (errors.bodyStream.length > 0) {
      console.log('\n🚨 BODY STREAM ERRORS:');
      errors.bodyStream.slice(-3).forEach((err, i) => {
        console.log(`  ${i+1}. [${err.time}] ${err.error.substring(0, 120)}...`);
      });
    }
    
    if (errors.wolfPack.length > 0) {
      console.log('\n🐺 WOLF PACK ERRORS:');
      errors.wolfPack.slice(-3).forEach((err, i) => {
        console.log(`  ${i+1}. [${err.time}] ${err.error.substring(0, 120)}...`);
      });
    }
    
    // PASS/FAIL ASSESSMENT
    const priceStability = priceUpdateCount > (totalMinutes * 1.5); // At least 1.5 updates per minute
    const lowErrorRate = (errors.bodyStream.length + errors.wolfPack.length) < 3;
    const navigationWorking = errors.navigation.length < 2;
    
    console.log('\n📊 STABILITY ASSESSMENT:');
    console.log(`Price Feed Stability: ${priceStability ? '✅ PASS' : '❌ FAIL'}`);
    console.log(`Error Rate: ${lowErrorRate ? '✅ PASS' : '❌ FAIL'}`);
    console.log(`Navigation Stability: ${navigationWorking ? '✅ PASS' : '❌ FAIL'}`);
    
    if (priceStability && lowErrorRate && navigationWorking) {
      console.log('\n🏆 ✅ STABILITY TEST PASSED!');
      console.log('Price feeds are stable and navigation works correctly');
      return true;
    } else {
      console.log('\n❌ STABILITY TEST FAILED - Issues need to be fixed:');
      if (!priceStability) console.log('  - Price feeds not updating consistently');
      if (!lowErrorRate) console.log('  - Too many body stream / wolf pack errors');
      if (!navigationWorking) console.log('  - Navigation errors detected');
      return false;
    }
    
  } catch (error) {
    console.error('❌ Test execution failed:', error.message);
    return false;
  } finally {
    await browser.close();
  }
}

// Run the test
testProductionStability().then(passed => {
  if (!passed) {
    console.log('\n🔧 Test failed - fixes needed before golden test');
    process.exit(1);
  } else {
    console.log('\n✅ Ready for golden test!');
  }
}).catch(console.error);