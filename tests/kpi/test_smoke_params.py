import pytest
@pytest.mark.parametrize('x',range(25))
def test_formula_smoke(x):
    assert x+x==2*x
