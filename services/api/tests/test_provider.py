from app.providers.factory import get_provider, provider_status
from app.providers.heuristic import HeuristicProvider


def test_pytest_forces_heuristic_provider():
    provider = get_provider()
    assert isinstance(provider, HeuristicProvider)
    status = provider_status()
    assert status["ai_provider"] == "heuristic"
    assert status["ai_configured"] is False
    assert status.get("ai_last_error") is None
