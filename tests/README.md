# ContextKeeper v3 Test Suite

## 📋 Overview

This comprehensive test suite validates all functionality of ContextKeeper v3, including the Sacred Layer implementation, Flask API endpoints, CLI integration, path filtering, and end-to-end workflows. The test suite is designed to prevent regression and ensure quality as the codebase evolves.

## 🏗️ Test Architecture

### Directory Structure
```
tests/
├── conftest.py              # Shared test configuration and fixtures
├── pytest.ini              # Pytest configuration
├── requirements.txt         # Testing dependencies
├── README.md               # This documentation
├── api/                    # API endpoint tests
│   └── test_flask_endpoints.py
├── cli/                    # CLI integration tests
│   └── test_cli_integration.py
├── integration/            # End-to-end workflow tests
│   └── test_end_to_end_workflows.py
├── performance/            # Performance and load tests
├── sacred/                 # Sacred Layer specific tests
│   ├── test_sacred_layer.py
│   └── test_plan_approval.py
└── unit/                   # Unit tests for individual components
    └── test_path_filtering.py
```

### Test Categories

Tests are organized by pytest markers for easy execution:

- **`@pytest.mark.unit`**: Unit tests for individual components
- **`@pytest.mark.integration`**: End-to-end workflow tests
- **`@pytest.mark.api`**: Flask API endpoint tests
- **`@pytest.mark.cli`**: Command-line interface tests
- **`@pytest.mark.sacred`**: Sacred Layer specific tests
- **`@pytest.mark.performance`**: Performance and load tests
- **`@pytest.mark.slow`**: Tests that take more than 1 second

## 🚀 Quick Start

### Installation

1. **Install testing dependencies:**
   ```bash
   cd /path/to/contextkeeper
   pip install -r tests/requirements.txt
   ```

2. **Verify environment setup:**
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   export CONTEXTKEEPER_TEST_MODE="true"
   ```

### Running Tests

#### Run All Tests
```bash
pytest tests/ -v
```

#### Run Specific Test Categories
```bash
# Sacred Layer tests only
pytest tests/ -m sacred -v

# API endpoint tests only
pytest tests/ -m api -v

# Unit tests only
pytest tests/ -m unit -v

# Integration tests only
pytest tests/ -m integration -v

# CLI tests only
pytest tests/ -m cli -v
```

#### Run Tests with Coverage
```bash
pytest tests/ --cov=rag_agent --cov=sacred_layer_implementation --cov=project_manager --cov-report=html
```

#### Run Performance Tests
```bash
pytest tests/ -m performance -v --durations=10
```

#### Run Quick Smoke Tests
```bash
pytest tests/ -m "not slow" -v
```

## 📊 Test Coverage Areas

### 1. Sacred Layer Functionality ✅
**Location**: `tests/sacred/test_sacred_layer.py`

**Coverage**:
- ✅ Plan creation workflow
- ✅ Two-layer verification system
- ✅ Plan approval process
- ✅ Sacred query functionality
- ✅ Plan status management
- ✅ Embeddings integration
- ✅ Immutability guarantees
- ✅ Large plan chunking
- ✅ Security features
- ✅ Performance characteristics

**Key Tests**:
- `test_create_plan_basic()` - Plan creation
- `test_plan_approval_flow_success()` - Approval workflow
- `test_approved_plan_cannot_be_modified()` - Immutability
- `test_large_plan_chunking()` - Content chunking
- `test_verification_code_security()` - Security validation

### 2. Flask API Endpoints ✅
**Location**: `tests/api/test_flask_endpoints.py`

**Coverage**:
- ✅ Health check endpoints
- ✅ Core RAG endpoints (`/query`, `/ingest`, `/query_llm`)
- ✅ Sacred endpoints (`/sacred/plans`, `/sacred/query`, `/sacred/approve`)
- ✅ Error handling (400, 401, 404, 500)
- ✅ Request validation
- ✅ Response formatting

**Key Tests**:
- `test_query_endpoint()` - RAG querying
- `test_create_sacred_plan_endpoint()` - Sacred plan creation
- `test_approve_sacred_plan_endpoint()` - Plan approval
- `test_missing_json_validation()` - Input validation

### 3. CLI Integration ✅
**Location**: `tests/cli/test_cli_integration.py`

**Coverage**:
- ✅ Sacred CLI commands (`create`, `list`, `approve`, `query`)
- ✅ Port connectivity (5556 vs 5555 fix)
- ✅ Command validation
- ✅ Error handling and recovery
- ✅ Authentication workflows

**Key Tests**:
- `test_sacred_plan_create_command()` - Plan creation via CLI
- `test_port_5556_availability()` - Port connectivity fix
- `test_valid_create_command()` - Command validation
- `test_connection_error_handling()` - Error scenarios

### 4. Path Filtering ✅
**Location**: `tests/unit/test_path_filtering.py`

**Coverage**:
- ✅ Virtual environment exclusion (`venv`, `.venv`)
- ✅ Build artifact exclusion (`__pycache__`, `node_modules`)
- ✅ Project file inclusion
- ✅ Directory traversal logic
- ✅ Performance optimization
- ✅ Cross-platform compatibility

**Key Tests**:
- `test_venv_exclusion()` - Virtual environment filtering
- `test_project_file_inclusion()` - Project file detection
- `test_nested_exclusion_logic()` - Deep directory filtering
- `test_large_directory_filtering_performance()` - Performance

### 5. End-to-End Workflows ✅
**Location**: `tests/integration/test_end_to_end_workflows.py`

**Coverage**:
- ✅ Complete RAG workflow (ingest → embed → query)
- ✅ Sacred Layer integration
- ✅ Multi-project isolation
- ✅ System resilience
- ✅ Performance scaling
- ✅ Concurrent operation handling

**Key Tests**:
- `test_file_ingestion_to_query_workflow()` - Complete RAG flow
- `test_plan_creation_from_rag_results()` - Sacred integration
- `test_multi_project_isolation_workflow()` - Project isolation
- `test_concurrent_query_handling()` - Concurrency

## 🔧 Test Configuration

### Environment Variables
```bash
# Required for testing
export GEMINI_API_KEY="test_api_key"
export CONTEXTKEEPER_TEST_MODE="true"
export CONTEXTKEEPER_LOG_LEVEL="DEBUG"

# Optional port configuration
export CONTEXTKEEPER_PORT="5556"
export CONTEXTKEEPER_HOST="127.0.0.1"

# Sacred Layer testing
export SACRED_APPROVAL_KEY="test_sacred_key_12345"
```

### Pytest Configuration
The test suite uses `pytest.ini` for configuration:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
markers =
    unit: Unit tests for individual components
    integration: Integration tests for complete workflows
    api: API endpoint tests
    cli: Command-line interface tests
    sacred: Sacred Layer specific tests
    performance: Performance and load tests
    slow: Tests that take more than 1 second
addopts = -v --tb=short --strict-markers
```

### Test Fixtures

**Global Fixtures** (from `conftest.py`):
- `temp_dir`: Temporary directory for test files
- `mock_embedder`: Mock embedding service
- `sacred_manager`: Sacred Layer manager instance
- `mock_rag_agent`: Mock RAG agent for testing
- `sample_files_for_ingestion`: Sample files for ingestion tests

**Specialized Fixtures**:
- `sample_plan_content`: Standard plan content for testing
- `sample_large_plan_content`: Large content for chunking tests
- `performance_test_data`: Data sets for performance testing

## 🎯 Test Validation Areas

### Recently Fixed Issues Validated

1. **Sacred Layer Two-Layer Verification** ✅
   - Tests verify proper verification code generation
   - Tests validate secondary key requirement
   - Tests ensure plan immutability after approval

2. **Flask Endpoint Functionality** ✅
   - All Sacred endpoints tested for correct responses
   - Core RAG endpoints validated for proper operation
   - Error handling verified for all failure scenarios

3. **Path Filtering Fixes** ✅
   - Virtual environment exclusion working correctly
   - Project file inclusion validated
   - Performance optimizations verified

4. **CLI Port Connectivity (5556 vs 5555 fix)** ✅
   - Port distinction tests ensure no confusion
   - Connectivity tests validate proper port usage
   - Command routing tests verify correct endpoints

5. **API Model Integration** ✅
   - Google GenAI embedding functionality tested
   - LLM response integration validated
   - Backward compatibility verified

## 📈 Performance Benchmarks

### Expected Performance Metrics

- **Plan Creation**: < 1 second for standard content
- **File Ingestion**: < 5 seconds for 10 files
- **Query Response**: < 2 seconds per query
- **Path Filtering**: < 2 seconds for 100 files
- **API Endpoints**: < 1 second response time

### Performance Test Commands
```bash
# Run performance tests with timing
pytest tests/ -m performance -v --durations=10

# Run with memory profiling (if memory-profiler installed)
pytest tests/ -m performance --profile

# Run load tests
pytest tests/integration/ -v -x
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Ensure you're in the correct directory
cd /path/to/contextkeeper

# Check Python path
python -c "import sys; print(sys.path)"
```

#### 2. Missing Dependencies
```bash
# Install test requirements
pip install -r tests/requirements.txt

# Install main requirements
pip install -r requirements.txt
```

#### 3. Port Conflicts
```bash
# Check if ports are in use
netstat -an | grep 555

# Kill processes using the ports
lsof -ti:5556 | xargs kill -9
```

#### 4. API Key Issues
```bash
# Verify API key is set
echo $GEMINI_API_KEY

# Set test API key
export GEMINI_API_KEY="test_key_for_testing"
```

### Debug Mode

Run tests in debug mode for detailed output:
```bash
pytest tests/ -v -s --tb=long --log-cli-level=DEBUG
```

### Test Data Cleanup

Clean up test artifacts:
```bash
# Remove temporary test files
find . -name "test_*.db" -delete
find . -name "*test*.log" -delete
rm -rf /tmp/contextkeeper_test*
```

## 🔄 Continuous Integration

### Pre-commit Checks
```bash
# Run all tests before committing
pytest tests/ -v --tb=short

# Run quick smoke tests
pytest tests/ -m "not slow" -v

# Check test coverage
pytest tests/ --cov=rag_agent --cov-report=term-missing
```

### Automated Test Execution

The test suite is designed for CI/CD integration:

1. **Fast Tests** (`< 30 seconds`): Unit tests, API tests
2. **Medium Tests** (`< 2 minutes`): Integration tests, CLI tests  
3. **Slow Tests** (`< 5 minutes`): Performance tests, load tests

### Test Results Reporting

Generate test reports:
```bash
# HTML report
pytest tests/ --html=test_report.html --self-contained-html

# JSON report (for CI parsing)
pytest tests/ --json-report --json-report-file=test_report.json

# JUnit XML (for CI integration)
pytest tests/ --junitxml=test_results.xml
```

## 📝 Contributing to Tests

### Adding New Tests

1. **Determine test category**:
   - Unit test → `tests/unit/`
   - Integration test → `tests/integration/`
   - API test → `tests/api/`
   - CLI test → `tests/cli/`
   - Sacred test → `tests/sacred/`

2. **Follow naming conventions**:
   - File: `test_feature_name.py`
   - Class: `TestFeatureName`
   - Method: `test_specific_behavior()`

3. **Use appropriate fixtures**:
   ```python
   def test_my_feature(self, sacred_manager, temp_dir):
       # Test implementation
       pass
   ```

4. **Add proper markers**:
   ```python
   @pytest.mark.unit
   @pytest.mark.sacred
   def test_plan_creation(self):
       pass
   ```

### Test Quality Guidelines

1. **Descriptive names**: Test names should clearly describe what they validate
2. **Arrange-Act-Assert**: Structure tests with clear setup, execution, and validation
3. **Independent tests**: Each test should run independently without dependencies
4. **Mock external services**: Use mocks for API calls, file system operations
5. **Performance aware**: Mark slow tests appropriately
6. **Documentation**: Add docstrings explaining complex test scenarios

## 📞 Support

### Getting Help

- **Test failures**: Check the troubleshooting section above
- **New test development**: Follow the contributing guidelines
- **Performance issues**: Run performance tests to identify bottlenecks
- **Integration problems**: Verify environment variables and dependencies

### Test Suite Maintenance

This test suite should be maintained alongside code changes:

- **New features**: Add corresponding tests
- **Bug fixes**: Add regression tests
- **API changes**: Update API tests
- **Performance improvements**: Update performance benchmarks

---

**Last Updated**: 2025-07-29 04:17:00 (Australia/Sydney)  
**Test Suite Version**: 1.0.0  
**Compatible with**: ContextKeeper v3.0+