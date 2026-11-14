import pytest
from saleor.permission.models import Permission
from django.contrib.sites.models import Site

from saleor.graphql.tests.utils import get_graphql_content
from saleor.permission.enums import SitePermissions
from saleor.site.models import SiteSettings

SETTINGS_UPDATE = """
    mutation($input: ShopSettingsInput!){
        shopSettingsUpdate(input: $input){
            shop { checkoutNoteMaxLength }
            errors { field code message }
        }
    }
"""
SHOP_QUERY = "query { shop { checkoutNoteMaxLength } }"


def _grant(staff_api_client):
    staff_api_client.user.user_permissions.add(
        *Permission.objects.filter(
            codename__in=[SitePermissions.MANAGE_SETTINGS.codename]
        )
    )


def _set(client, value, **extra):
    content = get_graphql_content(
        client.post_graphql(
            SETTINGS_UPDATE, {"input": {"checkoutNoteMaxLength": value}}, **extra
        )
    )
    assert not content["data"]["shopSettingsUpdate"]["errors"]
    return content["data"]["shopSettingsUpdate"]["shop"]["checkoutNoteMaxLength"]


def _read(client, **extra):
    content = get_graphql_content(client.post_graphql(SHOP_QUERY, **extra))
    return content["data"]["shop"]["checkoutNoteMaxLength"]


def test_behavior_default_is_empty(api_client):
    assert _read(api_client) is None


def test_behavior_admin_sets_and_storefront_reads(staff_api_client, api_client):
    _grant(staff_api_client)
    assert _set(staff_api_client, 200) == 200
    assert _read(api_client) == 200


def test_behavior_value_can_be_cleared(staff_api_client, api_client):
    _grant(staff_api_client)
    _set(staff_api_client, 200)
    _set(staff_api_client, None)
    assert _read(api_client) is None


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


def test_rule_each_site_reads_its_own_value(staff_api_client, api_client, two_sites):
    first, other = two_sites
    _grant(staff_api_client)
    assert _set(staff_api_client, 100, HTTP_HOST=first.domain) == 100
    assert _set(staff_api_client, 500, HTTP_HOST=other.domain) == 500

    assert _read(api_client, HTTP_HOST=first.domain) == 100
    assert _read(api_client, HTTP_HOST=other.domain) == 500


def test_rule_update_on_one_site_leaves_the_other(
    staff_api_client, api_client, two_sites
):
    first, other = two_sites
    _grant(staff_api_client)
    _set(staff_api_client, 300, HTTP_HOST=other.domain)

    assert _read(api_client, HTTP_HOST=other.domain) == 300
    assert _read(api_client, HTTP_HOST=first.domain) is None
