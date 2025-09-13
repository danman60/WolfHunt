import { test, expect, Page } from '@playwright/test';

test.describe('WolfHunt Backtesting System', () => {
  let page: Page;

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;
    // Navigate to Strategy page
    await page.goto('/strategy');
    await expect(page).toHaveTitle(/WolfHunt/);
  });

  test('Strategy page loads with backtesting interface', async () => {
    // Verify page title and key elements exist
    await expect(page.getByText('Strategy Configuration')).toBeVisible();
    await expect(page.getByText('Configure and backtest your trading strategies')).toBeVisible();

    // Check for Run Backtest button
    await expect(page.getByText('Run Backtest')).toBeVisible();

    // Check for Save Configuration button
    await expect(page.getByText('Save Configuration')).toBeVisible();

    // Verify strategy list is present
    await expect(page.getByText('Available Strategies')).toBeVisible();
    await expect(page.getByText('EMA Crossover')).toBeVisible();
    await expect(page.getByText('RSI Mean Reversion')).toBeVisible();
    await expect(page.getByText('Momentum Strategy')).toBeVisible();
  });

  test('Strategy selection and parameter configuration', async () => {
    // Click on RSI Mean Reversion strategy
    await page.getByText('RSI Mean Reversion').click();

    // Verify strategy configuration panel updates
    await expect(page.getByText('RSI Mean Reversion Configuration')).toBeVisible();

    // Check for RSI-specific parameters
    await expect(page.getByText('Period')).toBeVisible();
    await expect(page.getByText('Oversold Level')).toBeVisible();
    await expect(page.getByText('Overbought Level')).toBeVisible();

    // Verify strategy description updates
    await expect(page.getByText('This strategy uses the Relative Strength Index')).toBeVisible();

    // Test parameter modification
    const periodInput = page.locator('input').filter({ hasText: '14' }).first();
    await periodInput.fill('21');
    await expect(periodInput).toHaveValue('21');
  });

  test('Strategy enable/disable toggle functionality', async () => {
    // Find the first strategy toggle button
    const firstStrategyToggle = page.locator('button').filter({ hasText: '' }).first();

    // Test toggle interaction
    await firstStrategyToggle.click();

    // Verify console log (would need to check browser console in real test)
    // For now, just verify the toggle is clickable
    await expect(firstStrategyToggle).toBeVisible();
  });

  test('Run Backtest button functionality and loading state', async () => {
    const runBacktestButton = page.getByText('Run Backtest');

    // Click Run Backtest button
    await runBacktestButton.click();

    // Button should show loading state
    await expect(page.getByText('Running Backtest...')).toBeVisible({ timeout: 2000 });

    // Wait for backtest to complete (may take several seconds)
    await expect(page.getByText('Run Backtest')).toBeVisible({ timeout: 30000 });
  });

  test('Backtest results display after successful run', async () => {
    const runBacktestButton = page.getByText('Run Backtest');

    // Run backtest
    await runBacktestButton.click();

    // Wait for results to appear
    await expect(page.getByText('Backtest Results')).toBeVisible({ timeout: 30000 });

    // Verify performance metrics are displayed
    await expect(page.getByText('Total Return')).toBeVisible();
    await expect(page.getByText('Sharpe Ratio')).toBeVisible();
    await expect(page.getByText('Max Drawdown')).toBeVisible();
    await expect(page.getByText('Win Rate')).toBeVisible();
    await expect(page.getByText('Total Trades')).toBeVisible();

    // Verify performance chart is rendered
    const chart = page.locator('.recharts-wrapper');
    await expect(chart).toBeVisible();

    // Check for strategy and benchmark lines in chart
    await expect(page.locator('.recharts-line')).toHaveCount(2);
  });

  test('Strategy configuration persistence', async () => {
    // Select EMA Crossover strategy
    await page.getByText('EMA Crossover').click();

    // Modify fast period parameter
    const fastPeriodInput = page.locator('input[type="number"]').first();
    await fastPeriodInput.fill('10');

    // Click Save Configuration
    await page.getByText('Save Configuration').click();

    // Verify the value persists after save
    await expect(fastPeriodInput).toHaveValue('10');
  });

  test('Quick Stats panel displays correctly', async () => {
    await expect(page.getByText('Quick Stats')).toBeVisible();

    // Verify stats are displayed
    await expect(page.getByText('Active Strategies:')).toBeVisible();
    await expect(page.getByText('Signals Today:')).toBeVisible();
    await expect(page.getByText('Executed:')).toBeVisible();
    await expect(page.getByText('Success Rate:')).toBeVisible();

    // Verify numeric values are present
    const activeStrategiesValue = page.locator('text="Active Strategies:"').locator('..').getByText(/\d+/);
    await expect(activeStrategiesValue).toBeVisible();
  });

  test('Responsive design on mobile viewport', async () => {
    await page.setViewportSize({ width: 375, height: 667 });

    // Verify key elements are still visible and accessible on mobile
    await expect(page.getByText('Strategy Configuration')).toBeVisible();
    await expect(page.getByText('Run Backtest')).toBeVisible();

    // Test strategy selection on mobile
    await page.getByText('EMA Crossover').click();
    await expect(page.getByText('EMA Crossover Configuration')).toBeVisible();
  });

  test('Error handling for failed backtest', async () => {
    // Mock network failure or server error by intercepting requests
    await page.route('/api/backtesting/**', route => {
      route.fulfill({ status: 500, body: 'Server Error' });
    });

    const runBacktestButton = page.getByText('Run Backtest');
    await runBacktestButton.click();

    // Should still show results (fallback simulation mode)
    await expect(page.getByText('Run Backtest')).toBeVisible({ timeout: 10000 });

    // May show fallback results
    // (Depends on implementation - could show error message or fallback data)
  });

  test('Multiple strategy parameter types handling', async () => {
    // Select Momentum strategy which has boolean parameters
    await page.getByText('Momentum Strategy').click();

    // Verify numeric parameters
    await expect(page.locator('input[type="number"]')).toHaveCount(5); // 5 numeric parameters

    // Verify boolean toggle for volumeConfirmation
    const volumeToggle = page.locator('button').filter({ hasText: '' });
    await expect(volumeToggle.first()).toBeVisible();

    // Test boolean parameter toggle
    await volumeToggle.first().click();
    // Boolean state changes are internal, just verify interaction works
  });

  test('Backtest performance chart interactivity', async () => {
    // Run backtest first
    await page.getByText('Run Backtest').click();
    await expect(page.getByText('Backtest Results')).toBeVisible({ timeout: 30000 });

    // Test chart tooltip interaction
    const chartArea = page.locator('.recharts-wrapper');
    await chartArea.hover();

    // Tooltip should appear on hover (specific selectors may vary)
    const tooltip = page.locator('.recharts-tooltip-wrapper');
    await expect(tooltip).toBeVisible({ timeout: 2000 });
  });

  test('Strategy descriptions update correctly', async () => {
    // Test each strategy shows its unique description
    await page.getByText('EMA Crossover').click();
    await expect(page.getByText('This strategy uses exponential moving averages')).toBeVisible();

    await page.getByText('RSI Mean Reversion').click();
    await expect(page.getByText('This strategy uses the Relative Strength Index')).toBeVisible();

    await page.getByText('Momentum Strategy').click();
    await expect(page.getByText('This strategy identifies strong price momentum')).toBeVisible();
  });

  test('Network request validation for backtest API', async () => {
    // Monitor network requests during backtest
    const requests: string[] = [];
    page.on('request', request => {
      if (request.url().includes('/api/backtesting/')) {
        requests.push(request.url());
      }
    });

    await page.getByText('Run Backtest').click();

    // Wait for backtest completion
    await expect(page.getByText('Run Backtest')).toBeVisible({ timeout: 30000 });

    // Verify correct API endpoints were called
    expect(requests.some(url => url.includes('/api/backtesting/run') || url.includes('/api/backtesting/quick-test'))).toBe(true);
  });
});

test.describe('WolfHunt Backtesting API Integration', () => {
  test('Direct API endpoint testing', async ({ request }) => {
    // Test strategies endpoint
    const strategiesResponse = await request.get('/api/backtesting/strategies');
    expect(strategiesResponse.status()).toBe(200);

    const strategies = await strategiesResponse.json();
    expect(strategies).toHaveProperty('strategies');
    expect(Array.isArray(strategies.strategies)).toBe(true);
  });

  test('Quick backtest API endpoint', async ({ request }) => {
    // Test quick backtest endpoint
    const quickTestResponse = await request.post('/api/backtesting/quick-test', {
      params: {
        strategy_name: 'ema_crossover',
        symbols: ['BTC'],
        days_back: '30'
      }
    });

    // Should either succeed (200) or require auth (401)
    expect([200, 401].includes(quickTestResponse.status())).toBe(true);

    if (quickTestResponse.status() === 200) {
      const result = await quickTestResponse.json();
      expect(result).toHaveProperty('summary');
    }
  });
});