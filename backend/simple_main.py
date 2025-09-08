"""
Simple FastAPI server for testing the dYdX trading bot frontend integration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime
import random
import os

app = FastAPI(title="dYdX Trading Bot API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data for demonstration
@app.get("/api/trading/dashboard")
async def get_dashboard_data():
    """Get comprehensive dashboard data"""
    return {
        "total_equity": 99843 + random.randint(-1000, 1000),
        "account_balance": 98000,
        "daily_pnl": 2156 + random.randint(-500, 500),
        "daily_pnl_percent": 2.34 + random.uniform(-1, 1),
        "total_unrealized_pnl": 1245 + random.randint(-200, 200),
        "available_margin": 91323,
        "used_margin": 8520,
        "margin_utilization": 8.7 + random.uniform(-2, 2),
        "open_positions": random.randint(1, 3),
        "total_trades": random.randint(50, 100),
        "win_rate": 68.5 + random.uniform(-5, 5),
        "sharpe_ratio": 1.45,
        "max_drawdown": 1.2,
        "system_status": "healthy",
        "trading_enabled": True,
        "paper_mode": True,
    }

@app.get("/api/trading/positions")
async def get_positions():
    """Get current positions"""
    return [
        {
            "id": 1,
            "symbol": "BTC-USD",
            "side": "LONG",
            "size": 0.5,
            "entry_price": 44200,
            "mark_price": 45750 + random.randint(-100, 100),
            "unrealized_pnl": 775 + random.randint(-50, 50),
            "unrealized_pnl_percent": 1.75,
            "notional_value": 22875,
            "margin_used": 7625,
            "leverage": 3.0,
            "liquidation_price": 40500,
            "strategy_name": "MovingAverageCrossover",
            "opened_at": "2024-01-15T10:30:00Z",
            "updated_at": datetime.utcnow().isoformat(),
        },
        {
            "id": 2,
            "symbol": "ETH-USD", 
            "side": "SHORT",
            "size": -2.0,
            "entry_price": 2920,
            "mark_price": 2895 + random.randint(-10, 10),
            "unrealized_pnl": 50 + random.randint(-20, 20),
            "unrealized_pnl_percent": 0.86,
            "notional_value": 5790,
            "margin_used": 1930,
            "leverage": 3.0,
            "liquidation_price": 3200,
            "strategy_name": "MovingAverageCrossover",
            "opened_at": "2024-01-15T11:00:00Z",
            "updated_at": datetime.utcnow().isoformat(),
        },
    ]

@app.get("/api/trading/trades")
async def get_trades():
    """Get trade history"""
    return [
        {
            "id": 1,
            "order_id": "order_001",
            "symbol": "BTC-USD",
            "side": "BUY",
            "order_type": "MARKET",
            "size": 0.25,
            "price": 44800,
            "filled_size": 0.25,
            "notional_value": 11200,
            "commission": 11.2,
            "realized_pnl": 237.5,
            "status": "FILLED",
            "strategy_name": "MovingAverageCrossover",
            "timestamp": "2024-01-15T10:28:45Z",
            "created_at": "2024-01-15T10:28:45Z",
        },
        {
            "id": 2,
            "order_id": "order_002",
            "symbol": "LINK-USD",
            "side": "SELL",
            "order_type": "MARKET",
            "size": -100,
            "price": 15.62,
            "filled_size": -100,
            "notional_value": 1562,
            "commission": 1.56,
            "realized_pnl": -23.0,
            "status": "FILLED",
            "strategy_name": "MovingAverageCrossover",
            "timestamp": "2024-01-15T10:15:23Z",
            "created_at": "2024-01-15T10:15:23Z",
        },
    ]

@app.post("/api/trading/positions/{position_id}/close")
async def close_position(position_id: int):
    """Close a position"""
    return {
        "success": True,
        "message": f"Position {position_id} closed successfully",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/trading/emergency-stop")
async def emergency_stop():
    """Emergency stop trading"""
    return {
        "success": True,
        "message": "Emergency stop activated",
        "trading_enabled": False,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/trading/health")
async def get_health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "database": "healthy",
            "dydx_api": "healthy",
            "websocket": "healthy",
            "strategies": "healthy",
            "risk_management": "healthy"
        },
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    return {"message": "dYdX Trading Bot API", "status": "running"}

if __name__ == "__main__":
    print("Starting dYdX Trading Bot API Server...")
    print("Dashboard available at: http://localhost:3001")
    print("API available at: http://localhost:8000")
    print("API docs at: http://localhost:8000/docs")
    
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload in production
        log_level="info"
    )