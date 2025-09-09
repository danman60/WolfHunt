# 🐺 Wolf Pack Intelligence Test Suite

Comprehensive testing infrastructure for the Wolf Pack AI trading intelligence system.

## 📋 Test Coverage

### 🧠 Intelligence Engine Tests (`test_intelligence_engine.py`)
- Data processing and validation
- Google Sheets API integration
- Strategy suggestion generation
- Risk assessment algorithms
- Mock data generation
- Database operations
- Cache management

### 🤖 Automation Engine Tests (`test_automation_engine.py`)
- Strategy automation logic
- Risk management systems
- Execution plan creation
- GMX trading integration
- Portfolio state management
- Leverage calculations
- Pre-execution safety checks

### 🌐 API Endpoints Tests (`test_api_endpoints.py`)
- All Wolf Pack API endpoints
- Request/response validation
- Error handling
- Authentication and authorization
- CORS configuration
- Integration workflows

## 🚀 Running Tests

### Prerequisites
```bash
pip install pytest pytest-asyncio pytest-cov httpx fastapi[all]
```

### Quick Start
```bash
# Run all tests
python run_tests.py

# Run specific test suites
python run_tests.py intelligence
python run_tests.py automation
python run_tests.py api

# Run with verbose output
python run_tests.py all -v

# Run with coverage report
python run_tests.py all -c

# Check dependencies
python run_tests.py --check-deps
```

### Alternative Methods
```bash
# Using pytest directly
pytest tests/test_wolfpack/ -v

# Run specific test file
pytest tests/test_wolfpack/test_intelligence_engine.py -v

# Run with coverage
pytest tests/test_wolfpack/ --cov=src.integrations --cov-report=html
```

## 🧪 Test Categories

### Unit Tests
- Individual function testing
- Mock data validation
- Utility function verification
- Model validation

### Integration Tests
- End-to-end workflows
- Database integration
- API integration
- GMX client integration

### API Tests
- Endpoint functionality
- Request/response validation
- Error handling
- Authentication flows

## 📊 Test Configuration

### Environment Variables
The tests use the following environment variables (automatically mocked):
- `WOLF_PACK_TRADING_ENABLED=false` - Disables real trading
- `GMX_ACCOUNT_ADDRESS` - Test account address
- `GOOGLE_SHEETS_API_KEY=None` - Forces mock data mode
- `DATABASE_URL=sqlite:///:memory:` - In-memory test database

### Mock Objects
- GMX SDK modules (handles missing dependencies)
- Google Sheets API responses
- Database connections
- Redis cache operations
- Trading execution results

## 🎯 Test Scenarios

### Intelligence Engine Scenarios
- ✅ Bullish convergence detection
- ✅ Volume momentum identification
- ✅ Signal divergence warnings
- ✅ Portfolio-level analysis
- ✅ Risk assessment validation
- ✅ Data quality checks

### Automation Engine Scenarios
- ✅ High-confidence strategy approval
- ✅ Risk-based rejection logic
- ✅ Position size limitations
- ✅ Cooldown period enforcement
- ✅ Daily trade limits
- ✅ Leverage optimization
- ✅ Pre-execution safety checks

### API Endpoint Scenarios
- ✅ Unified intelligence delivery
- ✅ Live signal streaming
- ✅ Strategy execution flows
- ✅ Performance metrics reporting
- ✅ System health monitoring
- ✅ Error handling and recovery

## 📈 Coverage Goals

Target test coverage:
- **Intelligence Engine**: >90%
- **Automation Engine**: >85%
- **API Endpoints**: >80%
- **Overall System**: >85%

## 🛡️ Safety Features

### Test Isolation
- All tests run in isolation
- No external API calls in tests
- In-memory databases only
- Mock trading executions

### Risk Management Testing
- Position size validation
- Leverage limit enforcement
- Cooldown period verification
- Daily trade limit checks
- Portfolio concentration limits

### Error Handling Testing
- API failure scenarios
- Database connection errors
- Invalid data handling
- Network timeout simulation
- Authentication failures

## 🔧 Test Maintenance

### Adding New Tests
1. Create test functions following the naming convention `test_*`
2. Use appropriate fixtures from `conftest.py`
3. Mock external dependencies
4. Include both positive and negative test cases
5. Document complex test scenarios

### Test Data Management
- Use fixtures for consistent test data
- Mock external API responses
- Maintain realistic data ranges
- Update test data when models change

### Continuous Integration
The test suite is designed to run in CI/CD environments:
- No external dependencies required
- Configurable via environment variables
- Comprehensive error reporting
- Performance benchmarking

## 📋 Test Checklist

Before deploying Wolf Pack updates:
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] API tests pass
- [ ] Coverage meets targets
- [ ] No new security vulnerabilities
- [ ] Performance benchmarks met
- [ ] Error handling verified

## 🔍 Debugging Tests

### Common Issues
1. **Import Errors**: Ensure backend path is in PYTHONPATH
2. **Async Test Failures**: Use `pytest-asyncio` and proper event loop
3. **Mock Failures**: Verify mock objects match actual interfaces
4. **Database Errors**: Check SQLite permissions and memory constraints

### Debug Commands
```bash
# Run single test with debugging
pytest tests/test_wolfpack/test_intelligence_engine.py::TestWolfPackIntelligenceEngine::test_engine_initialization -vvv -s

# Run with pdb debugging
pytest tests/test_wolfpack/ --pdb

# Run with detailed output
pytest tests/test_wolfpack/ -vvv --tb=long
```

## 📊 Test Metrics

The test suite tracks:
- Execution time per test
- Memory usage during tests
- Mock call verification
- Coverage statistics
- Performance regressions

## 🎉 Contributing

When contributing to the Wolf Pack test suite:
1. Follow existing test patterns
2. Add tests for new features
3. Maintain or improve coverage
4. Update documentation
5. Verify all tests pass

---

**🐺 The Wolf Pack hunts with precision - our tests ensure every move is calculated and safe.**