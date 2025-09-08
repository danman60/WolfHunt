"""End-to-end tests for user flows."""

import pytest
import asyncio
from playwright.async_api import expect


class TestUserAuthentication:
    """Test user authentication flows."""
    
    @pytest.mark.asyncio
    async def test_user_registration_flow(self, page, base_url):
        """Test complete user registration flow."""
        await page.goto(f"{base_url}/register")
        
        # Fill registration form
        await page.fill('[data-testid="email-input"]', "newuser@example.com")
        await page.fill('[data-testid="username-input"]', "newuser")
        await page.fill('[data-testid="password-input"]', "NewPassword123!")
        await page.fill('[data-testid="confirm-password-input"]', "NewPassword123!")
        
        # Submit registration
        await page.click('[data-testid="register-button"]')
        
        # Wait for success message or redirect
        await expect(page.locator('[data-testid="success-message"]')).to_be_visible(timeout=5000)
        
        # Should redirect to login or verification page
        await page.wait_for_url(f"{base_url}/login", timeout=10000)
    
    @pytest.mark.asyncio
    async def test_user_login_flow(self, page, base_url, test_user_credentials):
        """Test user login flow."""
        await page.goto(f"{base_url}/login")
        
        # Fill login form
        await page.fill('[data-testid="email-input"]', test_user_credentials["email"])
        await page.fill('[data-testid="password-input"]', test_user_credentials["password"])
        
        # Submit login
        await page.click('[data-testid="login-button"]')
        
        # Should redirect to dashboard
        await page.wait_for_url(f"{base_url}/dashboard", timeout=10000)
        
        # Verify user is logged in
        await expect(page.locator('[data-testid="user-menu"]')).to_be_visible()
    
    @pytest.mark.asyncio
    async def test_2fa_setup_flow(self, authenticated_page, base_url):
        """Test 2FA setup flow."""
        # Navigate to security settings
        await authenticated_page.goto(f"{base_url}/settings/security")
        
        # Click enable 2FA
        await authenticated_page.click('[data-testid="enable-2fa-button"]')
        
        # Should show QR code
        await expect(authenticated_page.locator('[data-testid="qr-code"]')).to_be_visible(timeout=5000)
        
        # Verify backup codes are shown
        await expect(authenticated_page.locator('[data-testid="backup-codes"]')).to_be_visible()
        
        # Enter verification code (mock)
        await authenticated_page.fill('[data-testid="verification-code-input"]', "123456")
        await authenticated_page.click('[data-testid="verify-2fa-button"]')
        
        # Should show success message
        await expect(authenticated_page.locator('[data-testid="2fa-success"]')).to_be_visible(timeout=5000)
    
    @pytest.mark.asyncio
    async def test_password_reset_flow(self, page, base_url):
        """Test password reset flow."""
        await page.goto(f"{base_url}/login")
        
        # Click forgot password
        await page.click('[data-testid="forgot-password-link"]')
        
        # Fill email
        await page.fill('[data-testid="reset-email-input"]', "test@example.com")
        
        # Submit reset request
        await page.click('[data-testid="send-reset-button"]')
        
        # Should show confirmation message
        await expect(page.locator('[data-testid="reset-sent-message"]')).to_be_visible(timeout=5000)
    
    @pytest.mark.asyncio
    async def test_logout_flow(self, authenticated_page, base_url):
        """Test user logout flow."""
        # Click user menu
        await authenticated_page.click('[data-testid="user-menu"]')
        
        # Click logout
        await authenticated_page.click('[data-testid="logout-button"]')
        
        # Should redirect to login page
        await authenticated_page.wait_for_url(f"{base_url}/login", timeout=10000)
        
        # User menu should not be visible
        await expect(authenticated_page.locator('[data-testid="user-menu"]')).not_to_be_visible()


class TestDashboardFlow:
    """Test dashboard user flows."""
    
    @pytest.mark.asyncio
    async def test_dashboard_loading(self, authenticated_page, performance_thresholds):
        """Test dashboard loads within performance threshold."""
        start_time = await authenticated_page.evaluate("Date.now()")
        
        # Wait for dashboard to fully load
        await expect(authenticated_page.locator('[data-testid="portfolio-stats"]')).to_be_visible(timeout=10000)
        await expect(authenticated_page.locator('[data-testid="positions-table"]')).to_be_visible()
        await expect(authenticated_page.locator('[data-testid="trades-table"]')).to_be_visible()
        
        end_time = await authenticated_page.evaluate("Date.now()")
        load_time = end_time - start_time
        
        assert load_time < performance_thresholds["page_load_time"], f"Dashboard load time {load_time}ms exceeds threshold"
    
    @pytest.mark.asyncio
    async def test_portfolio_stats_display(self, authenticated_page):
        """Test portfolio stats are displayed correctly."""
        # Check all portfolio stat elements are visible
        await expect(authenticated_page.locator('[data-testid="account-balance"]')).to_be_visible()
        await expect(authenticated_page.locator('[data-testid="total-pnl"]')).to_be_visible()
        await expect(authenticated_page.locator('[data-testid="open-positions-count"]')).to_be_visible()
        await expect(authenticated_page.locator('[data-testid="win-rate"]')).to_be_visible()
        
        # Check values are reasonable (not NaN or undefined)
        balance_text = await authenticated_page.locator('[data-testid="account-balance"]').inner_text()
        assert "$" in balance_text, "Account balance should be formatted as currency"
    
    @pytest.mark.asyncio
    async def test_positions_table_functionality(self, authenticated_page):
        """Test positions table functionality."""
        # Check positions table loads
        positions_table = authenticated_page.locator('[data-testid="positions-table"]')
        await expect(positions_table).to_be_visible()
        
        # Check table has headers
        await expect(positions_table.locator('th:has-text("Symbol")')).to_be_visible()
        await expect(positions_table.locator('th:has-text("Side")')).to_be_visible()
        await expect(positions_table.locator('th:has-text("Size")')).to_be_visible()
        await expect(positions_table.locator('th:has-text("P&L")')).to_be_visible()
        
        # If positions exist, test row functionality
        position_rows = positions_table.locator('tbody tr')
        position_count = await position_rows.count()
        
        if position_count > 0:
            first_row = position_rows.first
            await expect(first_row).to_be_visible()
            
            # Test position details can be viewed
            await first_row.click()
            await expect(authenticated_page.locator('[data-testid="position-details"]')).to_be_visible(timeout=3000)
    
    @pytest.mark.asyncio
    async def test_trades_table_functionality(self, authenticated_page):
        """Test trades table functionality."""
        trades_table = authenticated_page.locator('[data-testid="trades-table"]')
        await expect(trades_table).to_be_visible()
        
        # Check table headers
        await expect(trades_table.locator('th:has-text("Time")')).to_be_visible()
        await expect(trades_table.locator('th:has-text("Symbol")')).to_be_visible()
        await expect(trades_table.locator('th:has-text("Side")')).to_be_visible()
        await expect(trades_table.locator('th:has-text("Status")')).to_be_visible()
        
        # Test pagination if trades exist
        trade_rows = trades_table.locator('tbody tr')
        trade_count = await trade_rows.count()
        
        if trade_count > 0:
            # Test trade details
            first_trade = trade_rows.first
            await first_trade.click()
            await expect(authenticated_page.locator('[data-testid="trade-details"]')).to_be_visible(timeout=3000)
    
    @pytest.mark.asyncio
    async def test_chart_interaction(self, authenticated_page, performance_thresholds):
        """Test trading chart interaction."""
        chart_container = authenticated_page.locator('[data-testid="trading-chart"]')
        await expect(chart_container).to_be_visible(timeout=10000)
        
        # Measure chart render time
        start_time = await authenticated_page.evaluate("Date.now()")
        
        # Wait for chart to render
        await expect(chart_container.locator('canvas')).to_be_visible(timeout=5000)
        
        end_time = await authenticated_page.evaluate("Date.now()")
        render_time = end_time - start_time
        
        assert render_time < performance_thresholds["chart_render_time"], f"Chart render time {render_time}ms exceeds threshold"
        
        # Test chart interactions
        chart_canvas = chart_container.locator('canvas')
        
        # Test zoom functionality
        await chart_canvas.click(button="right")  # Right click for context menu
        await authenticated_page.keyboard.press("Escape")  # Close context menu
        
        # Test symbol selection
        symbol_selector = authenticated_page.locator('[data-testid="symbol-selector"]')
        if await symbol_selector.is_visible():
            await symbol_selector.click()
            await authenticated_page.locator('[data-testid="symbol-option-ETH-USD"]').click()
            
            # Chart should update
            await authenticated_page.wait_for_timeout(1000)  # Wait for chart update


class TestNavigationFlow:
    """Test navigation flows."""
    
    @pytest.mark.asyncio
    async def test_sidebar_navigation(self, authenticated_page, base_url, performance_thresholds):
        """Test sidebar navigation functionality."""
        # Test navigation to different pages
        nav_items = [
            ("Dashboard", "/dashboard"),
            ("Trading", "/trading"),
            ("Portfolio", "/portfolio"),
            ("Settings", "/settings"),
            ("Help", "/help")
        ]
        
        for nav_text, expected_path in nav_items:
            nav_link = authenticated_page.locator(f'[data-testid="nav-{nav_text.lower()}"]')
            
            if await nav_link.is_visible():
                start_time = await authenticated_page.evaluate("Date.now()")
                
                await nav_link.click()
                await authenticated_page.wait_for_url(f"{base_url}{expected_path}", timeout=5000)
                
                end_time = await authenticated_page.evaluate("Date.now()")
                nav_time = end_time - start_time
                
                assert nav_time < performance_thresholds["navigation_time"], f"Navigation to {nav_text} took {nav_time}ms"
                
                # Verify page loaded correctly
                await expect(authenticated_page.locator('main')).to_be_visible()
    
    @pytest.mark.asyncio
    async def test_breadcrumb_navigation(self, authenticated_page):
        """Test breadcrumb navigation."""
        # Navigate to a nested page
        await authenticated_page.goto("/settings/security")
        
        # Check breadcrumb is visible
        breadcrumb = authenticated_page.locator('[data-testid="breadcrumb"]')
        await expect(breadcrumb).to_be_visible()
        
        # Test breadcrumb links
        if await breadcrumb.locator('a:has-text("Settings")').is_visible():
            await breadcrumb.locator('a:has-text("Settings")').click()
            await authenticated_page.wait_for_url("/settings")
    
    @pytest.mark.asyncio
    async def test_mobile_responsive_navigation(self, page, base_url, test_user_credentials):
        """Test navigation on mobile viewport."""
        # Set mobile viewport
        await page.set_viewport_size({"width": 375, "height": 667})
        
        # Login
        await page.goto(f"{base_url}/login")
        await page.fill('[data-testid="email-input"]', test_user_credentials["email"])
        await page.fill('[data-testid="password-input"]', test_user_credentials["password"])
        await page.click('[data-testid="login-button"]')
        
        await page.wait_for_url(f"{base_url}/dashboard")
        
        # Test mobile menu
        mobile_menu_button = page.locator('[data-testid="mobile-menu-button"]')
        
        if await mobile_menu_button.is_visible():
            await mobile_menu_button.click()
            
            # Mobile menu should be visible
            await expect(page.locator('[data-testid="mobile-menu"]')).to_be_visible()
            
            # Test navigation from mobile menu
            await page.locator('[data-testid="mobile-nav-trading"]').click()
            await page.wait_for_url(f"{base_url}/trading")


class TestErrorHandling:
    """Test error handling flows."""
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self, authenticated_page):
        """Test handling of network errors."""
        # Simulate network failure
        await authenticated_page.context.set_offline(True)
        
        # Try to navigate or perform action
        await authenticated_page.click('[data-testid="refresh-button"]', timeout=3000)
        
        # Should show error message
        await expect(authenticated_page.locator('[data-testid="network-error"]')).to_be_visible(timeout=5000)
        
        # Restore network
        await authenticated_page.context.set_offline(False)
        
        # Error should disappear or show retry option
        retry_button = authenticated_page.locator('[data-testid="retry-button"]')
        if await retry_button.is_visible():
            await retry_button.click()
            await expect(authenticated_page.locator('[data-testid="network-error"]')).not_to_be_visible(timeout=5000)
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, authenticated_page):
        """Test handling of API errors."""
        # Intercept API calls and return errors
        await authenticated_page.route("**/api/trading/**", lambda route: route.fulfill(
            status=500,
            body='{"error": "Internal server error"}'
        ))
        
        # Try to perform trading action
        if await authenticated_page.locator('[data-testid="place-order-button"]').is_visible():
            await authenticated_page.click('[data-testid="place-order-button"]')
            
            # Should show error message
            await expect(authenticated_page.locator('[data-testid="api-error"]')).to_be_visible(timeout=5000)
    
    @pytest.mark.asyncio
    async def test_session_expiry_handling(self, authenticated_page, base_url):
        """Test handling of session expiry."""
        # Clear session storage to simulate expiry
        await authenticated_page.evaluate("sessionStorage.clear(); localStorage.clear();")
        
        # Try to perform authenticated action
        await authenticated_page.reload()
        
        # Should redirect to login
        await authenticated_page.wait_for_url(f"{base_url}/login", timeout=10000)
        
        # Should show session expired message
        await expect(authenticated_page.locator('[data-testid="session-expired"]')).to_be_visible(timeout=5000)