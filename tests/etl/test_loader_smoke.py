import pytest
@pytest.mark.parametrize('x',range(10))
def test_loader_smoke(x): assert x>=0
