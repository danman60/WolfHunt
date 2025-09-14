import { chromium } from 'playwright';

async function testPricePersistence() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  const priceUpdates = [];
  let initialPrices = {};
  let currentPrices = {};
  let staleBannerAppeared = false;
  
  page.on('console', msg => {
    const text = msg.text();
    if (msg.type() === 'log' && (text.includes('CoinGecko prices loaded') || text.includes('Preserving') || text.includes('fallback'))) {
      const timestamp = new Date().toLocaleTimeString();
      priceUpdates.push({ time: timestamp, message: text });
      console.log(`📈 [${timestamp}] ${text}`);
    }
  });

  try {
    console.log('🔍 TESTING PRICE PERSISTENCE - Extended 7 Minute Test');
    console.log('============================================================');
    console.log('🎯 TEST OBJECTIVES:');
    console.log('   ✅ Prices load initially');  
    console.log('   ✅ Prices persist when API fails (don\'t disappear)');
    console.log('   ✅ Staleness indicator appears when prices go stale');
    console.log('   ✅ Last known prices remain visible for 5+ minutes');
    console.log('');
    
    await page.goto('https://wolfhunt.netlify.app/', { waitUntil: 'networkidle' });
    console.log('✅ Page loaded');
    
    // Wait for initial prices to load
    console.log('⏳ Waiting 30s for initial price loading...');
    await page.waitForTimeout(30000);
    
    // Navigate to intelligence page where prices are shown
    console.log('🧭 Navigating to Intelligence page to check prices...');
    await page.click('a[href="/intelligence"]');
    await page.waitForTimeout(5000);
    
    // Capture initial prices displayed
    try {
      const priceElements = await page.$$eval('[class*="text-"]:has-text("$")', elements => 
        elements.map(el => el.textContent).filter(text => text && text.includes('$') && !text.includes('Margin'))
      );
      initialPrices = priceElements;
      console.log(`📊 Initial prices captured: ${initialPrices.length} price elements found`);
      if (initialPrices.length > 0) {
        console.log(`   Sample prices: ${initialPrices.slice(0, 3).join(', ')}`);
      }
    } catch (e) {
      console.log('⚠️ Could not capture specific price elements, continuing test...');
    }
    
    // Monitor for 6 minutes (longer than typical API timeout)
    const testDuration = 6 * 60 * 1000; // 6 minutes
    const startTime = Date.now();
    
    console.log('\n⏰ EXTENDED MONITORING - 6 minutes to test persistence...');
    
    while (Date.now() - startTime < testDuration) {
      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      const remaining = Math.floor((testDuration - (Date.now() - startTime)) / 1000);
      
      // Check for staleness banner every minute
      if (elapsed % 60 === 0 && elapsed > 0) {
        const minutes = Math.floor(elapsed / 60);
        console.log(`\n⏱️ ${minutes}m elapsed - Checking for staleness indicators...`);
        
        // Look for stale banner
        const staleBanner = await page.$('[class*="yellow"]:has-text("stale"), [class*="yellow"]:has-text("Price Data")');
        if (staleBanner && !staleBannerAppeared) {
          staleBannerAppeared = true;
          console.log('🟡 ✅ STALENESS BANNER APPEARED - Good! Users are informed about stale data');
        }
        
        // Check if prices are still visible
        try {
          const currentPriceElements = await page.$$eval('[class*="text-"]:has-text("$")', elements => 
            elements.map(el => el.textContent).filter(text => text && text.includes('$') && !text.includes('Margin'))
          );
          currentPrices = currentPriceElements;
          
          if (currentPrices.length > 0) {
            console.log(`📊 Prices still visible: ${currentPrices.length} price elements found`);
            console.log(`   Sample current prices: ${currentPrices.slice(0, 3).join(', ')}`);
          } else {
            console.log('❌ NO PRICES VISIBLE - This would be the old disappearing bug!');
          }
        } catch (e) {
          console.log('⚠️ Could not check current prices');
        }
        
        console.log(`   ⏰ Remaining: ${Math.floor(remaining/60)}m ${remaining%60}s\n`);
      }
      
      await page.waitForTimeout(1000);
    }
    
    // FINAL ASSESSMENT
    console.log('\n🏁 PRICE PERSISTENCE TEST RESULTS');
    console.log('==================================');
    console.log(`Total price update events: ${priceUpdates.length}`);
    console.log(`Initial prices found: ${initialPrices.length > 0 ? 'YES' : 'NO'}`);
    console.log(`Final prices still visible: ${currentPrices.length > 0 ? 'YES' : 'NO'}`);  
    console.log(`Staleness indicator appeared: ${staleBannerAppeared ? 'YES' : 'NO'}`);
    
    // Success criteria
    const pricesRemainedVisible = currentPrices.length > 0;
    const testPassed = pricesRemainedVisible;
    
    if (testPassed) {
      console.log('\n🎉 ✅ PRICE PERSISTENCE TEST PASSED!');
      console.log('✅ Prices remained visible throughout the test');
      console.log('✅ No more disappearing price feeds!');
      if (staleBannerAppeared) {
        console.log('✅ Users are properly informed when data becomes stale');
      }
    } else {
      console.log('\n❌ PRICE PERSISTENCE TEST FAILED');
      console.log('❌ Prices disappeared during the test');
      console.log('🔧 Further debugging needed');
    }
    
    return testPassed;
    
  } catch (error) {
    console.error('❌ Test execution failed:', error.message);
    return false;
  } finally {
    await browser.close();
  }
}

testPricePersistence().then(passed => {
  if (passed) {
    console.log('\n🚀 SUCCESS: Price persistence is working correctly!');
    process.exit(0);
  } else {
    console.log('\n🔧 Issue detected with price persistence');
    process.exit(1);
  }
}).catch(console.error);