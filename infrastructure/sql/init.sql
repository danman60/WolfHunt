-- Database initialization script for dYdX Trading Bot
-- This script creates the initial database schema and seeds test data

-- Create database (PostgreSQL)
CREATE DATABASE IF NOT EXISTS wolfhunt;

-- Connect to the database
\c wolfhunt;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set timezone
SET TIME ZONE 'UTC';

-- Create initial admin user
-- Password: 'admin123' (hashed with bcrypt)
INSERT INTO users (
    email, 
    username, 
    hashed_password, 
    is_active, 
    is_superuser, 
    is_2fa_enabled, 
    trading_enabled, 
    paper_trading_mode,
    created_at
) VALUES (
    'admin@wolfhunt.trading',
    'admin',
    '$2b$12$LQv3c1yqBw91GLzgLt5uX.1BjqoEAiSJU3vTkLvPKdW8JQ1FOWqLG',
    true,
    true,
    false,
    true,
    true,
    NOW()
) ON CONFLICT (email) DO NOTHING;

-- Create test user
-- Password: 'testuser123'
INSERT INTO users (
    email,
    username,
    hashed_password,
    is_active,
    is_superuser,
    is_2fa_enabled,
    trading_enabled,
    paper_trading_mode,
    created_at
) VALUES (
    'test@wolfhunt.trading',
    'testuser',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
    true,
    false,
    false,
    true,
    true,
    NOW()
) ON CONFLICT (email) DO NOTHING;

-- Insert default configurations
INSERT INTO configurations (
    user_id,
    category,
    key,
    value,
    value_type,
    description,
    is_active,
    created_at
) VALUES 
    -- Global strategy settings
    (NULL, 'strategy', 'ema_fast_period', '12', 'int', 'Fast EMA period for crossover strategy', true, NOW()),
    (NULL, 'strategy', 'ema_slow_period', '26', 'int', 'Slow EMA period for crossover strategy', true, NOW()),
    (NULL, 'strategy', 'rsi_period', '14', 'int', 'RSI calculation period', true, NOW()),
    (NULL, 'strategy', 'rsi_oversold', '30', 'float', 'RSI oversold threshold', true, NOW()),
    (NULL, 'strategy', 'rsi_overbought', '70', 'float', 'RSI overbought threshold', true, NOW()),
    
    -- Global risk settings
    (NULL, 'risk', 'max_position_size_pct', '0.005', 'float', 'Maximum position size as percentage of equity', true, NOW()),
    (NULL, 'risk', 'max_leverage', '3.0', 'float', 'Maximum leverage allowed', true, NOW()),
    (NULL, 'risk', 'stop_loss_pct', '0.02', 'float', 'Stop loss percentage', true, NOW()),
    (NULL, 'risk', 'take_profit_ratio', '1.5', 'float', 'Risk to reward ratio for take profit', true, NOW()),
    (NULL, 'risk', 'daily_loss_limit', '0.02', 'float', 'Daily loss limit as percentage of equity', true, NOW()),
    (NULL, 'risk', 'max_correlation', '0.8', 'float', 'Maximum correlation between positions', true, NOW()),
    
    -- System settings
    (NULL, 'system', 'trading_symbols', '["BTC-USD", "ETH-USD", "LINK-USD"]', 'list', 'List of trading symbols', true, NOW()),
    (NULL, 'system', 'candle_timeframes', '["1m", "5m", "15m", "1h", "4h", "1d"]', 'list', 'Supported candle timeframes', true, NOW()),
    (NULL, 'system', 'max_open_positions', '3', 'int', 'Maximum number of open positions', true, NOW()),
    (NULL, 'system', 'order_timeout_seconds', '300', 'int', 'Order timeout in seconds', true, NOW())

ON CONFLICT (user_id, category, key) DO NOTHING;

-- Insert sample trade data for testing
INSERT INTO trades (
    user_id,
    order_id,
    symbol,
    side,
    order_type,
    size,
    price,
    filled_size,
    notional_value,
    commission,
    realized_pnl,
    status,
    strategy_name,
    timestamp,
    created_at
) VALUES 
    (2, 'test_order_1', 'BTC-USD', 'BUY', 'MARKET', 0.001, 45000.00, 0.001, 45.00, 0.045, 0, 'FILLED', 'MovingAverageCrossover', NOW() - INTERVAL '1 hour', NOW() - INTERVAL '1 hour'),
    (2, 'test_order_2', 'BTC-USD', 'SELL', 'MARKET', 0.001, 45500.00, 0.001, 45.50, 0.045, 4.55, 'FILLED', 'MovingAverageCrossover', NOW() - INTERVAL '30 minutes', NOW() - INTERVAL '30 minutes'),
    (2, 'test_order_3', 'ETH-USD', 'BUY', 'LIMIT', 0.01, 3000.00, 0.01, 30.00, 0.03, 0, 'FILLED', 'MovingAverageCrossover', NOW() - INTERVAL '2 hours', NOW() - INTERVAL '2 hours'),
    (2, 'test_order_4', 'ETH-USD', 'SELL', 'LIMIT', 0.01, 3050.00, 0.01, 30.50, 0.03, 0.47, 'FILLED', 'MovingAverageCrossover', NOW() - INTERVAL '1.5 hours', NOW() - INTERVAL '1.5 hours')
ON CONFLICT (order_id) DO NOTHING;

-- Insert sample position (currently open)
INSERT INTO positions (
    user_id,
    symbol,
    side,
    size,
    entry_price,
    mark_price,
    unrealized_pnl,
    unrealized_pnl_percent,
    notional_value,
    margin_used,
    leverage,
    stop_loss_price,
    take_profit_price,
    is_open,
    strategy_name,
    entry_reason,
    opened_at,
    created_at
) VALUES 
    (2, 'LINK-USD', 'LONG', 10.0, 15.50, 15.75, 2.50, 1.61, 155.00, 51.67, 3.0, 15.19, 15.94, true, 'MovingAverageCrossover', 'EMA12 crossed above EMA26 with RSI below 70', NOW() - INTERVAL '45 minutes', NOW() - INTERVAL '45 minutes')
ON CONFLICT (user_id, symbol, is_open) DO NOTHING;

-- Insert sample strategy signals
INSERT INTO strategy_signals (
    user_id,
    strategy_name,
    symbol,
    signal_type,
    strength,
    confidence,
    price,
    indicators,
    reasoning,
    executed,
    timestamp,
    created_at
) VALUES 
    (2, 'MovingAverageCrossover', 'BTC-USD', 'BUY', 0.8, 0.75, 45000.00, '{"ema12": 44980, "ema26": 44920, "rsi": 65}', 'Fast EMA crossed above slow EMA with moderate RSI', true, NOW() - INTERVAL '1 hour', NOW() - INTERVAL '1 hour'),
    (2, 'MovingAverageCrossover', 'ETH-USD', 'SELL', 0.9, 0.85, 3050.00, '{"ema12": 3048, "ema26": 3055, "rsi": 75}', 'Fast EMA crossed below slow EMA with overbought RSI', true, NOW() - INTERVAL '90 minutes', NOW() - INTERVAL '90 minutes'),
    (2, 'MovingAverageCrossover', 'LINK-USD', 'BUY', 0.7, 0.65, 15.50, '{"ema12": 15.48, "ema26": 15.45, "rsi": 55}', 'Fast EMA crossed above slow EMA with neutral RSI', true, NOW() - INTERVAL '45 minutes', NOW() - INTERVAL '45 minutes'),
    (2, 'MovingAverageCrossover', 'BTC-USD', 'HOLD', 0.3, 0.4, 45200.00, '{"ema12": 45195, "ema26": 45190, "rsi": 58}', 'EMAs are converging, no clear signal', false, NOW() - INTERVAL '15 minutes', NOW() - INTERVAL '15 minutes')
ON CONFLICT DO NOTHING;

-- Insert sample alerts
INSERT INTO alerts (
    user_id,
    alert_type,
    severity,
    title,
    message,
    symbol,
    strategy_name,
    metadata,
    is_read,
    is_resolved,
    timestamp,
    created_at
) VALUES 
    (2, 'trading', 'INFO', 'Trade Executed', 'Successfully bought 0.001 BTC at $45,000', 'BTC-USD', 'MovingAverageCrossover', '{"trade_id": "test_order_1", "pnl": 0}', true, true, NOW() - INTERVAL '1 hour', NOW() - INTERVAL '1 hour'),
    (2, 'risk', 'WARNING', 'Position Size Alert', 'Position in LINK-USD is 1.6% of portfolio', 'LINK-USD', 'MovingAverageCrossover', '{"position_size_pct": 1.6}', true, false, NOW() - INTERVAL '30 minutes', NOW() - INTERVAL '30 minutes'),
    (NULL, 'system', 'INFO', 'System Started', 'Trading bot system started successfully', NULL, NULL, '{"version": "1.0.0"}', false, true, NOW() - INTERVAL '2 hours', NOW() - INTERVAL '2 hours')
ON CONFLICT DO NOTHING;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_trades_user_timestamp ON trades(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_trades_symbol_timestamp ON trades(symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_trades_strategy_timestamp ON trades(strategy_name, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_positions_user_open ON positions(user_id, is_open);
CREATE INDEX IF NOT EXISTS idx_positions_symbol_open ON positions(symbol, is_open);
CREATE INDEX IF NOT EXISTS idx_positions_strategy_open ON positions(strategy_name, is_open);

CREATE INDEX IF NOT EXISTS idx_signals_strategy_timestamp ON strategy_signals(strategy_name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_signals_symbol_timestamp ON strategy_signals(symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_signals_user_executed ON strategy_signals(user_id, executed);

CREATE INDEX IF NOT EXISTS idx_alerts_user_read ON alerts(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_alerts_severity_timestamp ON alerts(severity, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_type_timestamp ON alerts(alert_type, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_config_category_key ON configurations(category, key);

-- Create functions for common queries
CREATE OR REPLACE FUNCTION calculate_daily_pnl(p_user_id INTEGER, p_date DATE)
RETURNS TABLE(realized_pnl DECIMAL, unrealized_pnl DECIMAL, total_pnl DECIMAL) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COALESCE(SUM(t.realized_pnl), 0)::DECIMAL as realized_pnl,
        COALESCE(SUM(p.unrealized_pnl), 0)::DECIMAL as unrealized_pnl,
        (COALESCE(SUM(t.realized_pnl), 0) + COALESCE(SUM(p.unrealized_pnl), 0))::DECIMAL as total_pnl
    FROM 
        trades t
        LEFT JOIN positions p ON p.user_id = p_user_id AND p.is_open = true
    WHERE 
        t.user_id = p_user_id 
        AND DATE(t.timestamp) = p_date 
        AND t.status = 'FILLED';
END;
$$ LANGUAGE plpgsql;

-- Print completion message
SELECT 'Database initialization completed successfully!' as message;