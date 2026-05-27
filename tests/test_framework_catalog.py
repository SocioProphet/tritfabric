from tools.validate_framework_catalog import main


def test_framework_catalog_contracts():
    assert main() == 0
