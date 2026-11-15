import graphene
from django.contrib.sites.models import Site

from .....site.models import SiteSettings
from .....warehouse.models import Stock, Warehouse
from ....tests.utils import get_graphql_content

STOCKS_CREATE_MUTATION = """
    mutation ProductVariantStocksCreate($variantId: ID!, $stocks: [StockInput!]!){
        productVariantStocksCreate(variantId: $variantId, stocks: $stocks){
            lowStockWarnings {
                quantity
                warehouse {
                    slug
                }
            }
            errors {
                code
                field
            }
        }
    }
"""

STOCKS_UPDATE_MUTATION = """
    mutation ProductVariantStocksUpdate($variantId: ID!, $stocks: [StockInput!]!){
        productVariantStocksUpdate(variantId: $variantId, stocks: $stocks){
            lowStockWarnings {
                quantity
                warehouse {
                    slug
                }
            }
            errors {
                code
                field
            }
        }
    }
"""


def _use_site_resolved_by_host(settings, monkeypatch, threshold):
    # SITE_ID is not configured: the site is resolved from the request host.
    monkeypatch.setattr(
        "saleor.graphql.views.is_storefront_traffic_blocked", lambda context: False
    )
    host_site = Site.objects.create(name="testserver", domain="testserver")
    SiteSettings.objects.create(
        site=host_site,
        low_stock_warning_threshold=threshold,
        use_legacy_shipping_zone_stock_availability=True,
    )
    settings.SITE_ID = None
    Site.objects.clear_cache()
    return host_site


def test_rule_stocks_create_resolves_site_without_site_id(
    staff_api_client,
    variant,
    warehouse,
    permission_manage_products,
    settings,
    monkeypatch,
):
    # given
    _use_site_resolved_by_host(settings, monkeypatch, threshold=10)
    new_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    new_warehouse.slug = "second-warehouse"
    new_warehouse.pk = None
    new_warehouse.save()
    variables = {
        "variantId": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "stocks": [
            {
                "warehouse": graphene.Node.to_global_id("Warehouse", new_warehouse.pk),
                "quantity": 3,
            }
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        STOCKS_CREATE_MUTATION, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksCreate"]
    assert not data["errors"]
    assert data["lowStockWarnings"] == [
        {"quantity": 3, "warehouse": {"slug": new_warehouse.slug}}
    ]
    assert Stock.objects.filter(
        product_variant=variant, warehouse=new_warehouse, quantity=3
    ).exists()


def test_rule_stocks_update_resolves_site_without_site_id(
    staff_api_client,
    variant,
    warehouse,
    permission_manage_products,
    settings,
    monkeypatch,
):
    # given
    _use_site_resolved_by_host(settings, monkeypatch, threshold=10)
    variables = {
        "variantId": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "stocks": [
            {
                "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
                "quantity": 3,
            }
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        STOCKS_UPDATE_MUTATION, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksUpdate"]
    assert not data["errors"]
    assert data["lowStockWarnings"] == [
        {"quantity": 3, "warehouse": {"slug": warehouse.slug}}
    ]
    stock = Stock.objects.get(product_variant=variant, warehouse=warehouse)
    assert stock.quantity == 3
