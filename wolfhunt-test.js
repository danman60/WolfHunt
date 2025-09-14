const { chromium } = require('playwright');

async function testWolfHuntSite() {
    console.log('Starting WolfHunt production site test...\n');
    
    const browser = await chromium.launch({ 
        headless: false,
        args: ['--disable-web-security', '--disable-features=VizDisplayCompositor'] 
    });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Capture console messages and errors
    const consoleMessages = [];
    const errors = [];
    
    page.on('console', msg => {
        consoleMessages.push({
            type: msg.type(),
            text: msg.text(),
            timestamp: new Date().toISOString()
        });
        console.log(`CONSOLE [${msg.type()}]: ${msg.text()}`);
    });
    
    page.on('pageerror', error => {
        errors.push({
            message: error.message,
            stack: error.stack,
            timestamp: new Date().toISOString()
        });
        console.log(`PAGE ERROR: ${error.message}`);
    });
    
    // Track network requests (especially API calls)
    const apiCalls = [];
    page.on('request', request => {
        const url = request.url();
        if (url.includes('coingecko') || url.includes('api') || url.includes('price')) {
            apiCalls.push({
                url: url,
                method: request.method(),
                timestamp: new Date().toISOString()
            });
            console.log(`API CALL: ${request.method()} ${url}`);
        }
    });
    
    try {
        console.log('1. Loading homepage...');
        await page.goto('https://wolfhunt.netlify.app/', { 
            waitUntil: 'networkidle',
            timeout: 30000 
        });
        
        // Wait a moment for initial load
        await page.waitForTimeout(3000);
        
        console.log('\n2. Checking for initial console errors...');
        const initialErrors = errors.filter(err => 
            err.message.toLowerCase().includes('body stream already read') ||
            err.message.toLowerCase().includes('stream') ||
            err.message.toLowerCase().includes('already read')
        );
        
        if (initialErrors.length > 0) {
            console.log(`Found ${initialErrors.length} "body stream already read" errors!`);
        } else {
            console.log('No "body stream already read" errors found.');
        }
        
        console.log('\n3. Checking for price feed API calls...');
        await page.waitForTimeout(5000); // Wait for price feeds to start
        
        const coinGeckoAPIs = apiCalls.filter(call => 
            call.url.toLowerCase().includes('coingecko')
        );
        
        if (coinGeckoAPIs.length > 0) {
            console.log(`Found ${coinGeckoAPIs.length} CoinGecko API calls:`);
            coinGeckoAPIs.forEach(call => {
                console.log(`  - ${call.method} ${call.url} at ${call.timestamp}`);
            });
        } else {
            console.log('No CoinGecko API calls detected yet.');
        }
        
        console.log('\n4. Looking for Wolf Configuration link...');
        const configLinks = await page.$$eval('a', links => 
            links.filter(link => 
                link.textContent.toLowerCase().includes('wolf configuration') ||
                link.textContent.toLowerCase().includes('configuration') ||
                link.href.includes('wolf-configuration') ||
                link.href.includes('config')
            ).map(link => ({
                text: link.textContent,
                href: link.href
            }))
        );
        
        if (configLinks.length > 0) {
            console.log('Found configuration links:');
            configLinks.forEach(link => {
                console.log(`  - "${link.text}" -> ${link.href}`);
            });
            
            console.log('\n5. Navigating to Wolf Configuration page...');
            try {
                await page.click('a[href*="wolf-configuration"], a[href*="config"]');
                await page.waitForURL('**/wolf-configuration*', { timeout: 10000 });
                console.log('Successfully navigated to Wolf Configuration page.');
                
                // Take screenshot of config page
                await page.screenshot({ 
                    path: 'D:\\ClaudeCode\\wolf-configuration-screenshot.png',
                    fullPage: true 
                });
                console.log('Screenshot saved: wolf-configuration-screenshot.png');
                
            } catch (navError) {
                console.log(`Navigation to config page failed: ${navError.message}`);
                
                // Try direct navigation as fallback
                try {
                    await page.goto('https://wolfhunt.netlify.app/wolf-configuration');
                    console.log('Direct navigation to config page successful.');
                    
                    await page.screenshot({ 
                        path: 'D:\\ClaudeCode\\wolf-configuration-direct-screenshot.png',
                        fullPage: true 
                    });
                    console.log('Screenshot saved: wolf-configuration-direct-screenshot.png');
                } catch (directError) {
                    console.log(`Direct navigation also failed: ${directError.message}`);
                }
            }
        } else {
            console.log('No Wolf Configuration links found. Trying direct navigation...');
            try {
                await page.goto('https://wolfhunt.netlify.app/wolf-configuration');
                console.log('Direct navigation to config page successful.');
                
                await page.screenshot({ 
                    path: 'D:\\ClaudeCode\\wolf-configuration-direct-screenshot.png',
                    fullPage: true 
                });
                console.log('Screenshot saved: wolf-configuration-direct-screenshot.png');
            } catch (directError) {
                console.log(`Direct navigation failed: ${directError.message}`);
            }
        }
        
        console.log('\n6. Testing price feeds for 30 seconds...');
        const startTime = Date.now();
        const startingAPICalls = apiCalls.length;
        
        while (Date.now() - startTime < 30000) {
            await page.waitForTimeout(2000);
            
            // Check if any new errors occurred
            const newErrors = errors.filter(err => 
                new Date(err.timestamp).getTime() > startTime
            );
            
            if (newErrors.length > 0) {
                console.log(`New errors detected during price feed test: ${newErrors.length}`);
                newErrors.forEach(err => {
                    console.log(`  ERROR: ${err.message}`);
                });
            }
        }
        
        const endingAPICalls = apiCalls.length;
        const newAPICalls = endingAPICalls - startingAPICalls;
        
        console.log(`Price feed test complete. ${newAPICalls} new API calls made during 30-second test.`);
        
        console.log('\n7. Checking navigation active states...');
        const navigationElements = await page.$$eval('nav a, .nav a, [role="navigation"] a', links => 
            links.map(link => ({
                text: link.textContent.trim(),
                href: link.href,
                classes: link.className,
                isActive: link.classList.contains('active') || link.classList.contains('current') || link.getAttribute('aria-current') === 'page'
            }))
        );
        
        console.log('Navigation elements found:');
        navigationElements.forEach(nav => {
            console.log(`  - "${nav.text}" (${nav.isActive ? 'ACTIVE' : 'inactive'}) -> ${nav.href}`);
        });
        
        console.log('\n8. Taking final homepage screenshot...');
        await page.goto('https://wolfhunt.netlify.app/');
        await page.waitForTimeout(3000);
        await page.screenshot({ 
            path: 'D:\\ClaudeCode\\wolfhunt-homepage-screenshot.png',
            fullPage: true 
        });
        console.log('Homepage screenshot saved: wolfhunt-homepage-screenshot.png');
        
    } catch (error) {
        console.error(`Test failed with error: ${error.message}`);
        console.error(error.stack);
    } finally {
        await browser.close();
    }
    
    // Generate final report
    console.log('\n' + '='.repeat(60));
    console.log('WOLFHUNT PRODUCTION TEST REPORT');
    console.log('='.repeat(60));
    
    console.log(`\nConsole Messages: ${consoleMessages.length} total`);
    console.log(`Console Errors: ${consoleMessages.filter(msg => msg.type === 'error').length}`);
    console.log(`Console Warnings: ${consoleMessages.filter(msg => msg.type === 'warning').length}`);
    
    console.log(`\nPage Errors: ${errors.length} total`);
    const bodyStreamErrors = errors.filter(err => 
        err.message.toLowerCase().includes('body stream already read') ||
        err.message.toLowerCase().includes('stream') ||
        err.message.toLowerCase().includes('already read')
    );
    console.log(`"Body stream already read" errors: ${bodyStreamErrors.length}`);
    
    console.log(`\nAPI Calls: ${apiCalls.length} total`);
    const coinGeckoCount = apiCalls.filter(call => 
        call.url.toLowerCase().includes('coingecko')
    ).length;
    console.log(`CoinGecko API calls: ${coinGeckoCount}`);
    
    if (errors.length > 0) {
        console.log('\nDetailed Error List:');
        errors.forEach((err, index) => {
            console.log(`${index + 1}. [${err.timestamp}] ${err.message}`);
        });
    }
    
    if (coinGeckoCount === 0) {
        console.log('\n❌ WARNING: No CoinGecko API calls detected - price feeds may not be working!');
    } else {
        console.log('\n✅ Price feeds appear to be working - CoinGecko API calls detected.');
    }
    
    console.log('\nTest completed at:', new Date().toISOString());
}

// Run the test
testWolfHuntSite().catch(console.error);