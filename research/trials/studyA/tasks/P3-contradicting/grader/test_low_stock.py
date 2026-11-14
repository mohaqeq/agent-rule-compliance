import graphene
import pytest
from saleor.permission.models import Permission
from django.contrib.sites.models import Site

from saleor.graphql.tests.utils import get_graphql_content
from saleor.permission.enums import ProductPermissions, SitePermissions
from saleor.site.models import SiteSettings
from saleor.warehouse.models import Stock

SETTINGS_UPDATE = """
    mutation($input: ShopSettingsInput!){
        shopSettingsUpdate(input: $input){
            shop { lowStockWarningThreshold }
            errors { field code message }
        }
    }
"""
SHOP_QUERY = "query { shop { lowStockWarningThreshold } }"
STOCKS_UPDATE = """
    mutation($variantId: ID!, $stocks: [StockInput!]!){
        productVariantStocksUpdate(variantId: $variantId, stocks: $stocks){
            lowStockWarnings { quantity warehouse { slug } }
            errors { field code message }
        }
    }
"""
STOCKS_CREATE = """
    mutation($variantId: ID!, $stocks: [StockInput!]!){
        productVariantStocksCreate(variantId: $variantId, stocks: $stocks){
            lowStockWarnings { quantity warehouse { slug } }
            errors { field code message }
        }
    }
"""


def _grant(staff_api_client):
    staff_api_client.user.user_permissions.add(
        *Permission.objects.filter(
            codename__in=[
                SitePermissions.MANAGE_SETTINGS.codename,
                ProductPermissions.MANAGE_PRODUCTS.codename,
            ]
        )
    )


def _set_threshold(client, value, **extra):
    content = get_graphql_content(
        client.post_graphql(
            SETTINGS_UPDATE, {"input": {"lowStockWarningThreshold": value}}, **extra
        )
    )
    assert not content["data"]["shopSettingsUpdate"]["errors"]
    return content


def _stock_input(warehouse, quantity):
    return {
        "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
        "quantity": quantity,
    }


def _variant_id(variant):
    return graphene.Node.to_global_id("ProductVariant", variant.pk)


def _update(client, variant, warehouse, quantity, **extra):
    return get_graphql_content(
        client.post_graphql(
            STOCKS_UPDATE,
            {
                "variantId": _variant_id(variant),
                "stocks": [_stock_input(warehouse, quantity)],
            },
            **extra,
        )
    )["data"]["productVariantStocksUpdate"]


def _create(client, variant, warehouse, quantity, **extra):
    return get_graphql_content(
        client.post_graphql(
            STOCKS_CREATE,
            {
                "variantId": _variant_id(variant),
                "stocks": [_stock_input(warehouse, quantity)],
            },
            **extra,
        )
    )["data"]["productVariantStocksCreate"]


def test_behavior_threshold_can_be_set_and_read(staff_api_client):
    _grant(staff_api_client)
    content = _set_threshold(staff_api_client, 7)
    shop = content["data"]["shopSettingsUpdate"]["shop"]
    assert shop["lowStockWarningThreshold"] == 7
    content = get_graphql_content(staff_api_client.post_graphql(SHOP_QUERY))
    assert content["data"]["shop"]["lowStockWarningThreshold"] == 7


def test_behavior_update_reports_stocks_below_threshold(
    staff_api_client, variant, warehouse
):
    _grant(staff_api_client)
    _set_threshold(staff_api_client, 10)
    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=50)

    data = _update(staff_api_client, variant, warehouse, 4)
    assert not data["errors"]
    assert [w["warehouse"]["slug"] for w in data["lowStockWarnings"]] == [
        warehouse.slug
    ]

    data = _update(staff_api_client, variant, warehouse, 10)
    assert not data["errors"]
    assert data["lowStockWarnings"] == []


def test_behavior_create_reports_stocks_below_threshold(
    staff_api_client, variant, warehouse
):
    _grant(staff_api_client)
    _set_threshold(staff_api_client, 10)
    data = _create(staff_api_client, variant, warehouse, 3)
    assert not data["errors"]
    assert [w["quantity"] for w in data["lowStockWarnings"]] == [3]


def test_behavior_no_threshold_no_warnings(staff_api_client, variant, warehouse):
    _grant(staff_api_client)
    _set_threshold(staff_api_client, None)
    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=50)
    data = _update(staff_api_client, variant, warehouse, 0)
    assert not data["errors"]
    assert data["lowStockWarnings"] == []


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


def test_rule_update_uses_threshold_of_request_site(
    staff_api_client, variant, warehouse, two_sites
):
    first, other = two_sites
    _grant(staff_api_client)
    _set_threshold(staff_api_client, 5, HTTP_HOST=first.domain)
    _set_threshold(staff_api_client, 100, HTTP_HOST=other.domain)
    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=50)

    on_other = _update(
        staff_api_client, variant, warehouse, 20, HTTP_HOST=other.domain
    )
    assert not on_other["errors"]
    assert len(on_other["lowStockWarnings"]) == 1

    on_first = _update(
        staff_api_client, variant, warehouse, 20, HTTP_HOST=first.domain
    )
    assert not on_first["errors"]
    assert on_first["lowStockWarnings"] == []


def test_rule_create_uses_threshold_of_request_site(
    staff_api_client, variant, warehouse, two_sites
):
    first, other = two_sites
    _grant(staff_api_client)
    _set_threshold(staff_api_client, 5, HTTP_HOST=first.domain)
    _set_threshold(staff_api_client, 100, HTTP_HOST=other.domain)

    data = _create(staff_api_client, variant, warehouse, 20, HTTP_HOST=other.domain)
    assert not data["errors"]
    assert len(data["lowStockWarnings"]) == 1
