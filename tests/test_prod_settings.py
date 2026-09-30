"""Production settings must refuse insecure or missing required configuration."""

import importlib

import pytest
from django.core.exceptions import ImproperlyConfigured

GOOD_ENV = {
    "SECRET_KEY": "u" * 64,
    "DJANGO_DEBUG": "false",
    "ALLOWED_HOSTS": "hanz.jsmx.org",
    "CSRF_TRUSTED_ORIGINS": "https://hanz.jsmx.org",
    "WAGTAILADMIN_BASE_URL": "https://hanz.jsmx.org",
}


def load_prod(monkeypatch, **overrides):
    env = {**GOOD_ENV, **overrides}
    for key, value in env.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)

    import config.settings.prod as prod

    return importlib.reload(prod)


@pytest.mark.parametrize("secret", [None, "", "some-insecure-key", "short"])
def test_prod_rejects_weak_secret_key(monkeypatch, secret):
    with pytest.raises(ImproperlyConfigured):
        load_prod(monkeypatch, SECRET_KEY=secret)


@pytest.mark.parametrize("hosts", [None, "", "*", "hanz.jsmx.org,*"])
def test_prod_rejects_wildcard_hosts(monkeypatch, hosts):
    with pytest.raises(ImproperlyConfigured):
        load_prod(monkeypatch, ALLOWED_HOSTS=hosts)


@pytest.mark.parametrize("origins", [None, "", "http://*", "http://hanz.jsmx.org"])
def test_prod_rejects_insecure_csrf_origins(monkeypatch, origins):
    with pytest.raises(ImproperlyConfigured):
        load_prod(monkeypatch, CSRF_TRUSTED_ORIGINS=origins)


def test_prod_rejects_debug(monkeypatch):
    with pytest.raises(ImproperlyConfigured):
        load_prod(monkeypatch, DJANGO_DEBUG="true")


@pytest.mark.parametrize("base_url", [None, "", "http://hanz.jsmx.org"])
def test_prod_rejects_non_https_admin_url(monkeypatch, base_url):
    with pytest.raises(ImproperlyConfigured):
        load_prod(monkeypatch, WAGTAILADMIN_BASE_URL=base_url)


def test_prod_hardens_cookies_and_transport(monkeypatch):
    prod = load_prod(monkeypatch)

    assert prod.DEBUG is False
    assert prod.SESSION_COOKIE_SECURE is True
    assert prod.CSRF_COOKIE_SECURE is True
    assert prod.SECURE_SSL_REDIRECT is True
    assert prod.SECURE_HSTS_SECONDS > 0
    assert prod.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https")
