from tools.validate_community_streams import main


def test_community_stream_contracts():
    assert main() == 0
