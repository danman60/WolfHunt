const { chromium } = require('playwright');

async function debugJavaScriptErrors() {
  console.log('🐛 Debug: Checking for JavaScript errors in enhancement system\n');
  
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Monitor ALL console output (including errors)
  page.on('console', msg => {
    const type = msg.type();
    const text = msg.text();
    const icon = type === 'error' ? '❌' : type === 'warning' ? '⚠️' : '📟';
    console.log(`${icon} [${type.toUpperCase()}] ${text}`);
  });
  
  // Monitor JavaScript errors
  page.on('pageerror', error => {
    console.log(`🚨 JavaScript Error: ${error.message}`);
    console.log(`Stack: ${error.stack}`);
  });
  
  // Monitor failed requests
  page.on('response', response => {
    if (response.status() >= 400 && response.url().includes('js/')) {
      console.log(`❌ Script failed to load: ${response.url()} (${response.status()})`);
    }
  });
  
  try {
    console.log('🌐 Loading WolfHunt to check for JavaScript errors...');
    await page.goto('https://wolfhunt.netlify.app/', { 
      waitUntil: 'networkidle' 
    });
    
    // Wait for scripts to load
    await page.waitForTimeout(5000);
    
    console.log('\n🔍 Manually checking window.WolfHuntFlags...');
    
    const manualCheck = await page.evaluate(() => {
      try {
        console.log('Manual check: typeof WolfHuntFlags =', typeof window.WolfHuntFlags);
        console.log('Manual check: WolfHuntFlags =', window.WolfHuntFlags);
        
        if (window.WolfHuntFlags) {
          console.log('Manual check: flags =', window.WolfHuntFlags.flags);
          return {
            exists: true,
            type: typeof window.WolfHuntFlags,
            flags: window.WolfHuntFlags.flags,
            hasEnableMethod: typeof window.WolfHuntFlags.enable === 'function'
          };
        } else {
          return { exists: false };
        }
      } catch (error) {
        console.log('Manual check error:', error.message);
        return { error: error.message };
      }
    });
    
    console.log('\n🔍 Manual Check Results:');
    console.log(JSON.stringify(manualCheck, null, 2));
    
    // Try to manually create WolfHuntFlags if it doesn't exist
    if (!manualCheck.exists) {
      console.log('\n🔧 Trying to manually load feature flags...');
      
      await page.evaluate(() => {
        try {
          // Try to fetch and execute the script manually
          fetch('/js/core/feature-flags.js')
            .then(response => response.text())
            .then(code => {
              console.log('Feature flags script loaded, length:', code.length);
              console.log('Script preview:', code.substring(0, 200) + '...');
              // Execute the script
              eval(code);
              console.log('Script executed, WolfHuntFlags now:', typeof window.WolfHuntFlags);
            })
            .catch(error => {
              console.log('Failed to load script:', error);
            });
        } catch (error) {
          console.log('Manual load error:', error);
        }
      });
      
      await page.waitForTimeout(3000);
      
      const afterManualLoad = await page.evaluate(() => {
        return {
          exists: !!window.WolfHuntFlags,
          type: typeof window.WolfHuntFlags
        };
      });
      
      console.log('After manual load:', afterManualLoad);
    }
    
  } catch (error) {
    console.error('❌ Debug failed:', error.message);
  }
  
  await page.waitForTimeout(5000);
  await browser.close();
}

debugJavaScriptErrors().catch(console.error);