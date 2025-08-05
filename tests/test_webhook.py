from bot import _is_valid_webhook


def test_valid_urls():
    assert _is_valid_webhook("https://example.com")
    assert _is_valid_webhook("http://example.com:8080")


def test_invalid_urls():
    assert not _is_valid_webhook("ftp://example.com")
    assert not _is_valid_webhook("https://")
    assert not _is_valid_webhook("https://example.com:abc")
    assert not _is_valid_webhook("not a url")
