# dYdX Trading Bot (WolfHunt)

A production-ready automated trading bot for BTC, ETH, and LINK perpetual futures on dYdX v4. This system implements momentum-based trading strategies with enterprise-grade risk controls, secure web interface, and comprehensive monitoring.

## 🚀 Features

### Core Trading Engine
- **dYdX v4 Integration**: Full WebSocket and REST API integration with automatic reconnection
- **Momentum Strategies**: Moving Average Crossover with configurable parameters
- **Risk Management**: Position sizing, stop-loss, daily loss limits, correlation monitoring
- **Paper Trading**: Full simulation mode with realistic execution
- **Backtesting**: Comprehensive historical strategy validation

### Web Interface
- **Real-time Dashboard**: Live portfolio tracking with P&L updates
- **Strategy Configuration**: Dynamic parameter adjustment
- **Trade History**: Complete audit trail with filtering
- **Mobile Responsive**: Full mobile trading interface

### Security & Monitoring
- **Enterprise Security**: AES-256 encryption, JWT authentication, 2FA support
- **Comprehensive Monitoring**: Prometheus metrics, Grafana dashboards
- **Multi-channel Alerts**: Email, SMS, Slack integration
- **Circuit Breakers**: Automatic trading suspension on anomalies

## 📦 Project Structure

```
dydx-trading-bot/
├── backend/                 # Python FastAPI backend
│   ├── src/
│   │   ├── trading/         # Core trading engine
│   │   │   ├── strategies/  # Trading strategies
│   │   │   ├── risk_management/ # Risk controls
│   │   │   ├── execution/   # Order execution
│   │   │   └── market_data/ # Data processing
│   │   ├── api/             # REST API routes
│   │   ├── database/        # Data models and DAOs
│   │   ├── security/        # Authentication & encryption
│   │   └── monitoring/      # Health checks & metrics
│   ├── tests/               # Test suite
│   └── config/              # Configuration management
├── frontend/                # React TypeScript frontend
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/           # Application pages
│   │   ├── hooks/           # Custom React hooks
│   │   ├── services/        # API integration
│   │   └── utils/           # Utility functions
│   └── public/              # Static assets
├── infrastructure/          # Docker & monitoring configs
│   ├── docker/              # Container configurations
│   └── monitoring/          # Prometheus & Grafana
└── docs/                    # Documentation
```

## 🛠 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### Environment Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/danman60/WolfHunt.git
   cd WolfHunt
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your dYdX API credentials
   ```

3. **Start infrastructure**
   ```bash
   docker-compose up -d db redis prometheus grafana
   ```

4. **Install dependencies**
   ```bash
   # Backend
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   
   # Frontend
   cd ../frontend
   npm install
   ```

### Development Mode

1. **Start backend server**
   ```bash
   cd backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start frontend development server**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Access the application**
   - Trading Dashboard: http://localhost:5173
   - API Documentation: http://localhost:8000/docs
   - Grafana Monitoring: http://localhost:3000

### Production Deployment

```bash
# Build and deploy all services
docker-compose up -d

# View logs
docker-compose logs -f trading-bot
```

## 📊 Trading Configuration

### Strategy Parameters
```python
# Moving Average Crossover
EMA_FAST_PERIOD = 12        # Fast EMA period
EMA_SLOW_PERIOD = 26        # Slow EMA period
RSI_PERIOD = 14             # RSI calculation period
RSI_OVERSOLD = 30           # RSI oversold threshold
RSI_OVERBOUGHT = 70         # RSI overbought threshold
```

### Risk Management
```python
MAX_POSITION_SIZE_PCT = 0.005  # 0.5% of equity per trade
MAX_LEVERAGE = 3.0             # Maximum leverage allowed
DAILY_LOSS_LIMIT = 0.02        # 2% daily loss limit
STOP_LOSS_PCT = 0.02           # 2% stop loss
TAKE_PROFIT_RATIO = 1.5        # 1.5:1 risk/reward ratio
```

## 🔒 Security Features

- **API Key Encryption**: AES-256 encryption for stored credentials
- **JWT Authentication**: Secure session management with 2FA support
- **Rate Limiting**: API and WebSocket connection limits
- **Audit Logging**: Complete action trail for compliance
- **Environment Isolation**: Separate testnet/mainnet configurations

## 📈 Monitoring & Alerts

### Metrics Tracked
- Trade execution performance
- Strategy win rates and P&L
- System health and latency
- Risk utilization and drawdowns

### Alert Conditions
- Daily loss limit breaches (2%)
- High API latency (>1000ms)
- WebSocket disconnections
- System errors and failures

## 🧪 Testing

```bash
# Run all tests
pytest backend/tests/ -v --cov=backend/src

# Run specific test suites
pytest backend/tests/test_trading_integration.py -v
pytest backend/tests/test_risk_management.py -v
pytest backend/tests/test_security.py -v

# Frontend tests
cd frontend && npm test
```

## 📝 Development Phases

### Phase 1: Core Trading Engine ✅
- [x] dYdX v4 API integration
- [x] Market data processing
- [x] Moving Average strategy
- [x] Basic risk management
- [x] Backtesting framework
- [x] Paper trading mode

### Phase 2: Risk Management & Persistence
- [ ] Enhanced risk controls
- [ ] Database schema & ORM
- [ ] Configuration persistence
- [ ] Performance optimization

### Phase 3: Web Interface
- [ ] FastAPI backend routes
- [ ] React dashboard
- [ ] Real-time updates
- [ ] Authentication system

### Phase 4: Production Features
- [ ] Security hardening
- [ ] Monitoring system
- [ ] Alerting framework
- [ ] Deployment automation

## 🔧 Configuration

Key configuration files:
- `.env` - Environment variables and secrets
- `backend/src/config/settings.py` - Trading parameters
- `docker-compose.yml` - Service orchestration
- `infrastructure/monitoring/` - Monitoring configs

## 📖 API Documentation

Once running, visit http://localhost:8000/docs for interactive API documentation.

Key endpoints:
- `GET /api/trading/dashboard` - Dashboard data
- `GET /api/trading/positions` - Current positions
- `GET /api/trading/trades` - Trade history
- `POST /api/trading/strategy/config` - Update strategy
- `POST /api/emergency-stop` - Emergency trading halt

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## ⚠️ Disclaimer

This trading bot is for educational and research purposes. Trading cryptocurrencies involves significant risk of loss. Use at your own risk and never trade with more than you can afford to lose.

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.