from minos import rulesync_convert


def test_get_adapter_returns_eurlex_for_gdpr():
    adapter = rulesync_convert._get_adapter("gdpr")
    assert isinstance(adapter, rulesync_convert.EurlexAdapter)
