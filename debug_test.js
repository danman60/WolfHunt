const { chromium } = require('playwright');

async function debugEnhancementSystem() {
  console.log('🔧 Debug: Testing WolfHunt Enhancement System Load Process...\n');
  
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Monitor all console output
  page.on('console', msg => {
    console.log(`🖥️  Console: ${msg.text()}`);
  });
  
  // Monitor all network requests
  page.on('response', response => {
    const url = response.url();
    const status = response.status();
    if (url.includes('wolfhunt') || url.includes('js/')) {
      console.log(`🌐 ${status === 200 ? '✅' : '❌'} ${status} ${url}`);
    }
  });
  
  try {
    console.log('🌐 Loading WolfHunt homepage...');
    await page.goto('https://wolfhunt.netlify.app/', { 
      waitUntil: 'domcontentloaded' 
    });
    
    console.log('\n🔍 Checking script tags in HTML...');
    const scriptTags = await page.evaluate(() => {
      const scripts = Array.from(document.querySelectorAll('script'));
      return scripts.map(script => ({
        src: script.src || 'inline',
        content: script.src ? null : script.textContent.substring(0, 100) + '...'
      }));
    });
    
    scriptTags.forEach((script, i) => {
      console.log(`Script ${i + 1}: ${script.src || 'inline'}`);
      if (script.content) {
        console.log(`   Content preview: ${script.content}`);
      }
    });
    
    // Wait for all scripts to potentially load
    await page.waitForTimeout(5000);
    
    console.log('\n🏗️ Checking if WolfHunt objects exist...');
    const objectsStatus = await page.evaluate(() => {
      return {
        WolfHuntFlags: typeof window.WolfHuntFlags,
        WolfHuntEnhancementLoader: typeof window.WolfHuntEnhancementLoader,
        WolfHuntAPICache: typeof window.WolfHuntAPICache,
        WolfHuntTrading: typeof window.WolfHuntTrading
      };
    });
    
    console.log('Global Objects Status:', objectsStatus);
    
    console.log('\n🎛️ Manually enabling feature flags...');
    await page.evaluate(() => {
      // Force enable flags if the system exists
      if (window.WolfHuntFlags) {
        window.WolfHuntFlags.enable('performance-fixes');
        window.WolfHuntFlags.enable('accessibility-fixes');
        window.WolfHuntFlags.enable('button-functionality');
      }
      
      // Try loading enhancement loader manually
      if (window.WolfHuntEnhancementLoader) {
        console.log('Enhancement loader found, initializing...');
        window.WolfHuntEnhancementLoader.initialize();
      }
    });
    
    await page.waitForTimeout(3000);
    
    console.log('\n🔄 Re-checking objects after manual initialization...');
    const finalStatus = await page.evaluate(() => {
      return {
        flags: window.WolfHuntFlags?.flags || 'Not found',
        performance: typeof window.wolfhuntPerformance,
        accessibility: document.querySelector('.skip-link') ? 'Skip link present' : 'No skip link',
        trading: typeof window.WolfHuntTrading
      };
    });
    
    console.log('Final Status:', finalStatus);
    
  } catch (error) {
    console.error('❌ Debug test failed:', error.message);
  }
  
  await page.waitForTimeout(5000);
  await browser.close();
}

debugEnhancementSystem().catch(console.error);