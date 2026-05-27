from tools.validate_recovered_framework_contracts import main


def test_recovered_framework_contracts():
    assert main() == 0
