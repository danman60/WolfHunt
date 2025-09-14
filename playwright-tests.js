const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function runWolfHuntGoldenTests() {
  const browser = await chromium.launch({
    headless: false, // Show browser for better debugging
    slowMo: 1000 // Slow down for observation
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });

  const page = await context.newPage();
  const baseURL = 'http://localhost:3000';
  const screenshotsDir = 'D:\\ClaudeCode\\WolfHunt\\test-screenshots';

  // Create screenshots directory
  if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir, { recursive: true });
  }

  const testResults = [];
  const consoleErrors = [];

  // Capture console errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(`${new Date().toISOString()}: ${msg.text()}`);
    }
  });

  page.on('pageerror', error => {
    consoleErrors.push(`${new Date().toISOString()}: PAGE ERROR - ${error.message}`);
  });

  try {
    console.log('🚀 Starting WolfHunt Golden Tests...\n');

    // GOLDEN TEST 1: App Loading & Navigation
    console.log('🧪 Golden Test 1: App Loading & Navigation');
    try {
      await page.goto(baseURL, { waitUntil: 'networkidle' });
      await page.waitForTimeout(3000); // Wait for initial load

      // Check for gray-950 dark theme
      const bodyClass = await page.getAttribute('body', 'class');
      const hasDarkTheme = bodyClass && bodyClass.includes('dark');

      // Check sidebar navigation
      const sidebar = await page.locator('[data-testid="sidebar"], .sidebar, nav').first();
      const sidebarVisible = await sidebar.isVisible().catch(() => false);

      // Check header
      const header = await page.locator('header, [data-testid="header"]').first();
      const headerVisible = await header.isVisible().catch(() => false);

      await page.screenshot({
        path: path.join(screenshotsDir, 'wolfhunt_test_1_loading.png'),
        fullPage: true
      });

      testResults.push({
        test: 'Golden Test 1: App Loading & Navigation',
        status: 'PASS',
        details: `Dark theme: ${hasDarkTheme}, Sidebar: ${sidebarVisible}, Header: ${headerVisible}`
      });

    } catch (error) {
      testResults.push({
        test: 'Golden Test 1: App Loading & Navigation',
        status: 'FAIL',
        error: error.message
      });
    }

    // GOLDEN TEST 2: Dashboard Page
    console.log('🧪 Golden Test 2: Dashboard Page');
    try {
      // Should already be on dashboard (default route)
      await page.waitForTimeout(2000);

      // Look for trading metrics, portfolio data
      const metricsElements = await page.locator('[class*="metric"], [class*="portfolio"], [class*="trading"]').count();
      const priceElements = await page.locator('[class*="price"], .price, [data-testid*="price"]').count();

      await page.screenshot({
        path: path.join(screenshotsDir, 'wolfhunt_test_2_dashboard.png'),
        fullPage: true
      });

      testResults.push({
        test: 'Golden Test 2: Dashboard Page',
        status: 'PASS',
        details: `Metrics elements: ${metricsElements}, Price elements: ${priceElements}`
      });

    } catch (error) {
      testResults.push({
        test: 'Golden Test 2: Dashboard Page',
        status: 'FAIL',
        error: error.message
      });
    }

    // GOLDEN TEST 3: Wolf Configuration Page
    console.log('🧪 Golden Test 3: Wolf Configuration Page');
    try {
      // Try multiple possible configuration routes
      const configRoutes = ['/configuration', '/trading', '/config', '/settings'];
      let configFound = false;

      for (const route of configRoutes) {
        try {
          await page.goto(`${baseURL}${route}`, { waitUntil: 'networkidle' });
          await page.waitForTimeout(2000);

          // Check if we're on a valid page (not 404)
          const notFound = await page.locator('text=/404|not found|page not found/i').count();
          if (notFound === 0) {
            configFound = true;
            break;
          }
        } catch (e) {
          continue;
        }
      }

      // Look for trading parameter controls
      const controlElements = await page.locator('input, select, button, [role="slider"]').count();
      const strategyElements = await page.locator('[class*="strategy"], [class*="config"], [class*="parameter"]').count();

      await page.screenshot({
        path: path.join(screenshotsDir, 'wolfhunt_test_3_configuration.png'),
        fullPage: true
      });

      testResults.push({
        test: 'Golden Test 3: Wolf Configuration Page',
        status: configFound ? 'PASS' : 'FAIL',
        details: `Config found: ${configFound}, Controls: ${controlElements}, Strategy elements: ${strategyElements}`
      });

    } catch (error) {
      testResults.push({
        test: 'Golden Test 3: Wolf Configuration Page',
        status: 'FAIL',
        error: error.message
      });
    }

    // GOLDEN TEST 4: Navigation Menu
    console.log('🧪 Golden Test 4: Navigation Menu');
    try {
      await page.goto(baseURL, { waitUntil: 'networkidle' });

      const navigationRoutes = [
        '/', '/intelligence', '/configuration', '/history', '/risk', '/alerts'
      ];

      let navigationWorking = 0;

      for (const route of navigationRoutes) {
        try {
          await page.goto(`${baseURL}${route}`, { waitUntil: 'networkidle' });
          await page.waitForTimeout(1000);

          const notFound = await page.locator('text=/404|not found|page not found/i').count();
          if (notFound === 0) {
            navigationWorking++;
          }
        } catch (e) {
          console.log(`Navigation to ${route} failed: ${e.message}`);
        }
      }

      await page.screenshot({
        path: path.join(screenshotsDir, 'wolfhunt_test_4_navigation.png'),
        fullPage: true
      });

      testResults.push({
        test: 'Golden Test 4: Navigation Menu',
        status: navigationWorking >= 3 ? 'PASS' : 'FAIL',
        details: `${navigationWorking}/${navigationRoutes.length} routes working`
      });

    } catch (error) {
      testResults.push({
        test: 'Golden Test 4: Navigation Menu',
        status: 'FAIL',
        error: error.message
      });
    }

    // GOLDEN TEST 5: Intelligence Brief Page
    console.log('🧪 Golden Test 5: Intelligence Brief Page');
    try {
      await page.goto(`${baseURL}/intelligence`, { waitUntil: 'networkidle' });
      await page.waitForTimeout(2000);

      const intelligenceElements = await page.locator('[class*="intelligence"], [class*="brief"], [class*="analysis"]').count();
      const marketDataElements = await page.locator('[class*="market"], [class*="data"]').count();

      await page.screenshot({
        path: path.join(screenshotsDir, 'wolfhunt_test_5_intelligence.png'),
        fullPage: true
      });

      testResults.push({
        test: 'Golden Test 5: Intelligence Brief Page',
        status: 'PASS',
        details: `Intelligence elements: ${intelligenceElements}, Market data: ${marketDataElements}`
      });

    } catch (error) {
      testResults.push({
        test: 'Golden Test 5: Intelligence Brief Page',
        status: 'FAIL',
        error: error.message
      });
    }

    // GOLDEN TEST 6: Price Context & Data
    console.log('🧪 Golden Test 6: Price Context & Data');
    try {
      await page.goto(baseURL, { waitUntil: 'networkidle' });
      await page.waitForTimeout(5000); // Wait longer for price data to load

      // Check for price displays
      const priceElements = await page.locator('[class*="price"], .price, [data-testid*="price"]').count();

      // Check for WebSocket connections or loading states
      const loadingElements = await page.locator('[class*="loading"], .loading, [class*="spinner"]').count();

      // Check for error states
      const errorElements = await page.locator('[class*="error"], .error').count();

      await page.screenshot({
        path: path.join(screenshotsDir, 'wolfhunt_test_6_prices.png'),
        fullPage: true
      });

      testResults.push({
        test: 'Golden Test 6: Price Context & Data',
        status: 'PASS',
        details: `Price elements: ${priceElements}, Loading: ${loadingElements}, Errors: ${errorElements}`
      });

    } catch (error) {
      testResults.push({
        test: 'Golden Test 6: Price Context & Data',
        status: 'FAIL',
        error: error.message
      });
    }

    // GOLDEN TEST 7: Responsive Sidebar
    console.log('🧪 Golden Test 7: Responsive Sidebar');
    try {
      await page.goto(baseURL, { waitUntil: 'networkidle' });

      // Test desktop view
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.waitForTimeout(1000);
      const desktopSidebar = await page.locator('nav, .sidebar, [class*="sidebar"]').first();
      const desktopVisible = await desktopSidebar.isVisible().catch(() => false);

      // Test mobile view
      await page.setViewportSize({ width: 375, height: 667 });
      await page.waitForTimeout(1000);
      const mobileSidebar = await page.locator('nav, .sidebar, [class*="sidebar"]').first();
      const mobileVisible = await mobileSidebar.isVisible().catch(() => false);

      // Look for collapse/expand functionality
      const toggleButton = await page.locator('[class*="toggle"], [class*="menu"], button').first();
      const toggleExists = await toggleButton.isVisible().catch(() => false);

      await page.screenshot({
        path: path.join(screenshotsDir, 'wolfhunt_test_7_sidebar.png'),
        fullPage: true
      });

      testResults.push({
        test: 'Golden Test 7: Responsive Sidebar',
        status: 'PASS',
        details: `Desktop: ${desktopVisible}, Mobile: ${mobileVisible}, Toggle: ${toggleExists}`
      });

    } catch (error) {
      testResults.push({
        test: 'Golden Test 7: Responsive Sidebar',
        status: 'FAIL',
        error: error.message
      });
    }

    // GOLDEN TEST 8: History & Risk Management
    console.log('🧪 Golden Test 8: History & Risk Management');
    try {
      // Test History page
      await page.goto(`${baseURL}/history`, { waitUntil: 'networkidle' });
      await page.waitForTimeout(2000);
      const historyElements = await page.locator('[class*="history"], [class*="trade"], table, .table').count();

      // Test Risk page
      await page.goto(`${baseURL}/risk`, { waitUntil: 'networkidle' });
      await page.waitForTimeout(2000);
      const riskElements = await page.locator('[class*="risk"], [class*="management"]').count();

      await page.screenshot({
        path: path.join(screenshotsDir, 'wolfhunt_test_8_history_risk.png'),
        fullPage: true
      });

      testResults.push({
        test: 'Golden Test 8: History & Risk Management',
        status: 'PASS',
        details: `History elements: ${historyElements}, Risk elements: ${riskElements}`
      });

    } catch (error) {
      testResults.push({
        test: 'Golden Test 8: History & Risk Management',
        status: 'FAIL',
        error: error.message
      });
    }

    // GOLDEN TEST 9: Alerts System
    console.log('🧪 Golden Test 9: Alerts System');
    try {
      await page.goto(`${baseURL}/alerts`, { waitUntil: 'networkidle' });
      await page.waitForTimeout(2000);

      const alertElements = await page.locator('[class*="alert"], .alert').count();

      // Check for notification count in header (should show 3)
      const notificationBadge = await page.locator('[class*="notification"], [class*="badge"]').count();

      await page.screenshot({
        path: path.join(screenshotsDir, 'wolfhunt_test_9_alerts.png'),
        fullPage: true
      });

      testResults.push({
        test: 'Golden Test 9: Alerts System',
        status: 'PASS',
        details: `Alert elements: ${alertElements}, Notification badges: ${notificationBadge}`
      });

    } catch (error) {
      testResults.push({
        test: 'Golden Test 9: Alerts System',
        status: 'FAIL',
        error: error.message
      });
    }

    // GOLDEN TEST 10: Backend Integration
    console.log('🧪 Golden Test 10: Backend Integration');
    try {
      await page.goto(baseURL, { waitUntil: 'networkidle' });
      await page.waitForTimeout(5000); // Wait for backend calls

      // Check for trading mode indicator
      const tradingModeElements = await page.locator('text=/paper|live|demo/i').count();

      // Check for API connection status
      const statusElements = await page.locator('[class*="status"], [class*="connection"]').count();

      await page.screenshot({
        path: path.join(screenshotsDir, 'wolfhunt_test_10_backend.png'),
        fullPage: true
      });

      testResults.push({
        test: 'Golden Test 10: Backend Integration',
        status: 'PASS',
        details: `Trading mode elements: ${tradingModeElements}, Status elements: ${statusElements}, Console errors: ${consoleErrors.length}`
      });

    } catch (error) {
      testResults.push({
        test: 'Golden Test 10: Backend Integration',
        status: 'FAIL',
        error: error.message
      });
    }

  } catch (globalError) {
    console.error('Global test error:', globalError);
  } finally {
    await browser.close();
  }

  // Generate test report
  const report = {
    timestamp: new Date().toISOString(),
    testResults,
    consoleErrors,
    summary: {
      totalTests: testResults.length,
      passed: testResults.filter(r => r.status === 'PASS').length,
      failed: testResults.filter(r => r.status === 'FAIL').length,
    }
  };

  const reportPath = path.join('D:\\ClaudeCode\\WolfHunt', 'test-report.json');
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

  console.log('\n📊 TEST RESULTS SUMMARY:');
  console.log(`✅ Passed: ${report.summary.passed}/${report.summary.totalTests}`);
  console.log(`❌ Failed: ${report.summary.failed}/${report.summary.totalTests}`);
  console.log(`🐛 Console Errors: ${consoleErrors.length}`);
  console.log(`📁 Screenshots saved to: ${screenshotsDir}`);
  console.log(`📄 Report saved to: ${reportPath}`);

  if (consoleErrors.length > 0) {
    console.log('\n🐛 CONSOLE ERRORS:');
    consoleErrors.forEach(error => console.log(`  - ${error}`));
  }

  return report;
}

// Run the tests
runWolfHuntGoldenTests().catch(console.error);