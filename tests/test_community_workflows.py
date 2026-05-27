from tools.validate_community_workflows import main


def test_community_workflow_contracts():
    assert main() == 0
