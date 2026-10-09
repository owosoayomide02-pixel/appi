from app.integrations.supabase import normalize_supabase_url, supabase_configured


def test_strips_rest_v1_from_supabase_url():
    assert (
        normalize_supabase_url("https://abc.supabase.co/rest/v1/")
        == "https://abc.supabase.co"
    )


def test_supabase_not_configured_in_tests():
    assert supabase_configured() is False
