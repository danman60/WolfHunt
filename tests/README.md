# dYdX Trading Bot - Test Suite

This directory contains comprehensive tests for the dYdX momentum trading bot "WolfHunt".

## Test Structure

```
tests/
├── conftest.py                    # Test configuration and fixtures
├── __init__.py
├── test_api/                      # API endpoint tests
│   ├── test_auth.py              # Authentication tests
│   ├── test_health.py            # Health check tests
│   ├── test_trading.py           # Trading API tests
│   └── test_websocket.py         # WebSocket tests
├── test_database/                 # Database tests
│   ├── test_models.py            # Model tests
│   └── __init__.py
├── test_trading/                  # Trading logic tests
│   ├── test_strategies.py        # Strategy tests
│   ├── test_risk_manager.py      # Risk management tests
│   ├── test_market_data.py       # Market data tests
│   └── __init__.py
├── test_utils/                    # Utility tests
│   ├── test_helpers.py           # Helper function tests
│   ├── test_data_factory.py      # Test data factory
│   └── __init__.py
├── test_integration/              # Integration tests
│   ├── test_trading_flow.py      # Complete trading flow tests
│   └── __init__.py
└── test_performance/              # Performance tests
    ├── test_strategy_performance.py
    └── __init__.py
```

## Running Tests

### Quick Start

```bash
# Run all tests
python run_tests.py

# Run with coverage
python run_tests.py --coverage

# Run specific test suites
python run_tests.py --suite unit
python run_tests.py --suite integration
python run_tests.py --suite api
python run_tests.py --suite performance
```

### Using pytest directly

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend/src --cov-report=html

# Run specific test files
pytest tests/test_trading/test_strategies.py -v

# Run tests with markers
pytest -m "not slow"
pytest -m performance

# Run tests in parallel
pytest -n 4
```

## Test Categories

### Unit Tests
- **Strategy Tests**: Test trading strategy logic, indicators, and signals
- **Risk Manager Tests**: Test risk management rules and calculations
- **Market Data Tests**: Test price feed and orderbook management
- **Database Model Tests**: Test ORM models and relationships
- **Utility Tests**: Test helper functions and utilities

### Integration Tests
- **Trading Flow Tests**: Test complete trade execution flows
- **API Integration Tests**: Test API endpoints with real components
- **WebSocket Integration Tests**: Test real-time updates

### Performance Tests
- **Strategy Performance**: Test strategy execution speed and memory usage
- **Concurrent Processing**: Test multi-threading and async performance
- **Large Dataset Tests**: Test with realistic data volumes

## Test Configuration

### Environment Variables
```bash
# Test database (uses SQLite in-memory by default)
TEST_DATABASE_URL="sqlite:///:memory:"

# API testing
TEST_API_BASE_URL="http://localhost:8000"

# Mock API keys for testing
TEST_DYDX_API_KEY="test_api_key"
TEST_DYDX_API_SECRET="test_api_secret"
TEST_DYDX_API_PASSPHRASE="test_passphrase"
```

### Fixtures Available

- `db_session`: Database session for testing
- `test_user`: Test user with default configuration
- `test_client`: FastAPI test client
- `authenticated_client`: Authenticated test client
- `test_user_token`: JWT token for test user
- Mock trading clients and market data

## Test Markers

- `@pytest.mark.slow`: Tests that take longer to run
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.performance`: Performance tests  
- `@pytest.mark.api`: API tests
- `@pytest.mark.websocket`: WebSocket tests
- `@pytest.mark.database`: Database tests
- `@pytest.mark.trading`: Trading logic tests
- `@pytest.mark.security`: Security-related tests

## Writing New Tests

### Test Naming Convention
- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`

### Example Test

```python
import pytest
from decimal import Decimal
from backend.src.trading.strategies.ma_crossover import MovingAverageCrossoverStrategy

class TestMyFeature:
    def test_basic_functionality(self):
        """Test basic functionality."""
        strategy = MovingAverageCrossoverStrategy()
        result = strategy.some_method()
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_async_functionality(self, test_user):
        """Test async functionality."""
        # Async test code here
        pass
    
    def test_with_mock_data(self, db_session):
        """Test with database session."""
        # Database test code here
        pass
```

### Using Test Data Factory

```python
from tests.test_utils.test_data_factory import TestDataFactory

def test_with_generated_data(self, db_session):
    # Create test user
    user = TestDataFactory.create_test_user()
    db_session.add(user)
    db_session.commit()
    
    # Create test trades
    trades = TestDataFactory.create_trade_sequence(user.id, count=10)
    db_session.add_all(trades)
    db_session.commit()
    
    # Test functionality
    assert len(trades) == 10
```

## Coverage Requirements

- Minimum coverage: 80%
- Critical components (risk management, strategies): 95%
- API endpoints: 90%
- Database models: 85%

## Continuous Integration

Tests are run automatically on:
- Every commit to main branch
- Every pull request
- Nightly builds with full test suite including performance tests

### CI Pipeline
1. Unit tests (fast feedback)
2. Integration tests
3. API tests
4. Performance tests (nightly only)
5. Coverage reporting
6. Security scans

## Troubleshooting

### Common Issues

1. **Database connection errors**:
   ```bash
   # Ensure test database is properly configured
   export TEST_DATABASE_URL="sqlite:///:memory:"
   ```

2. **Import errors**:
   ```bash
   # Ensure project root is in Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

3. **Async test issues**:
   ```bash
   # Install pytest-asyncio
   pip install pytest-asyncio
   ```

4. **Missing dependencies**:
   ```bash
   # Install test dependencies
   pip install -r requirements-test.txt
   ```

### Performance Test Issues

Performance tests may be sensitive to system load. Run them in isolation:

```bash
pytest tests/test_performance/ -m performance --tb=short
```

## Mocking External Services

All external services are mocked in tests:

- **dYdX API**: Mocked responses for trading operations
- **WebSocket connections**: Mock WebSocket clients
- **Market data feeds**: Generated test data
- **Database**: In-memory SQLite for fast tests

## Test Data Management

- Test data is generated programmatically
- No external test data files required
- Deterministic data generation for reproducible tests
- Factory pattern for creating test objects

## Reporting

Test results are available in multiple formats:
- Console output (default)
- HTML coverage reports (`htmlcov/index.html`)
- XML coverage reports (`coverage.xml`)
- JUnit XML for CI integration

---

For questions about testing, see the main project documentation or create an issue in the repository.