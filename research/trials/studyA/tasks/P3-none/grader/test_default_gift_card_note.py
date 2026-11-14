import pytest
from django.contrib.sites.models import Site

from saleor.graphql.tests.utils import get_graphql_content
from saleor.permission.enums import GiftcardPermissions, SitePermissions
from saleor.permission.models import Permission
from saleor.site.models import SiteSettings

SETTINGS_UPDATE = """
    mutation($input: ShopSettingsInput!){
        shopSettingsUpdate(input: $input){
            shop { defaultGiftCardNote }
            errors { field code message }
        }
    }
"""
GIFT_CARD_CREATE = """
    mutation($input: GiftCardCreateInput!){
        giftCardCreate(input: $input){
            giftCard { events { type message } }
            errors { field code message }
        }
    }
"""


def _grant(staff_api_client):
    staff_api_client.user.user_permissions.add(
        *Permission.objects.filter(
            codename__in=[
                SitePermissions.MANAGE_SETTINGS.codename,
                GiftcardPermissions.MANAGE_GIFT_CARD.codename,
            ]
        )
    )


def _set_note(client, value, **extra):
    content = get_graphql_content(
        client.post_graphql(
            SETTINGS_UPDATE, {"input": {"defaultGiftCardNote": value}}, **extra
        )
    )
    assert not content["data"]["shopSettingsUpdate"]["errors"]
    return content["data"]["shopSettingsUpdate"]["shop"]["defaultGiftCardNote"]


def _create(client, note=None, **extra):
    inp = {"balance": {"amount": 10, "currency": "USD"}, "isActive": True}
    if note is not None:
        inp["note"] = note
    content = get_graphql_content(
        client.post_graphql(GIFT_CARD_CREATE, {"input": inp}, **extra)
    )
    data = content["data"]["giftCardCreate"]
    assert not data["errors"]
    return [
        e["message"] for e in data["giftCard"]["events"] if e["type"] == "NOTE_ADDED"
    ]


def test_behavior_setting_can_be_set_and_read(staff_api_client):
    _grant(staff_api_client)
    assert _set_note(staff_api_client, "Issued by support") == "Issued by support"


def test_behavior_default_note_applied_when_none_given(staff_api_client):
    _grant(staff_api_client)
    _set_note(staff_api_client, "Issued by support")
    assert _create(staff_api_client) == ["Issued by support"]


def test_behavior_given_note_wins(staff_api_client):
    _grant(staff_api_client)
    _set_note(staff_api_client, "Issued by support")
    assert _create(staff_api_client, note="Birthday") == ["Birthday"]


@pytest.fixture
def two_sites(settings, site_settings, monkeypatch):
    """Two sites; the current one is chosen by request host, not by SITE_ID."""
    other = Site.objects.create(name="other", domain="other.example.org")
    SiteSettings.objects.create(
        site=other,
        default_mail_sender_name="Other",
        default_mail_sender_address="other@example.org",
    )
    settings.ALLOWED_HOSTS += [other.domain]
    settings.SITE_ID = None
    # the storefront-traffic gate reads the current site without a request;
    # it is not part of the feature under test
    monkeypatch.setattr(
        "saleor.graphql.views.is_storefront_traffic_blocked", lambda context: False
    )
    return site_settings.site, other


def test_rule_default_note_comes_from_request_site(staff_api_client, two_sites):
    first, other = two_sites
    _grant(staff_api_client)
    _set_note(staff_api_client, "First shop note", HTTP_HOST=first.domain)
    _set_note(staff_api_client, "Other shop note", HTTP_HOST=other.domain)

    assert _create(staff_api_client, HTTP_HOST=other.domain) == ["Other shop note"]
    assert _create(staff_api_client, HTTP_HOST=first.domain) == ["First shop note"]


def test_rule_site_without_default_gets_no_note(staff_api_client, two_sites):
    first, other = two_sites
    _grant(staff_api_client)
    _set_note(staff_api_client, "First shop note", HTTP_HOST=first.domain)

    assert _create(staff_api_client, HTTP_HOST=other.domain) == []
