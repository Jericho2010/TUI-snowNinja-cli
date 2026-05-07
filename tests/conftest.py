import pytest

def pytest_addoption(parser):
    parser.addoption("--run-integration", action="store_true", help="run integration tests")
    parser.addoption("--run-e2e", action="store_true", help="run e2e tests")

def pytest_configure(config):
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "e2e: mark test as e2e test")

@pytest.fixture(autouse=True)
def skip_integration(request):
    if request.node.get_closest_marker("integration"):
        if not request.config.getoption("--run-integration"):
            pytest.skip("needs --run-integration option to run")

@pytest.fixture(autouse=True)
def skip_e2e(request):
    if request.node.get_closest_marker("e2e"):
        if not request.config.getoption("--run-e2e"):
            pytest.skip("needs --run-e2e option to run")
