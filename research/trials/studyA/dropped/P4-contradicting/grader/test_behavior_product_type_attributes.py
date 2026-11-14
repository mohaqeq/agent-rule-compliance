import graphene

from saleor.attribute import AttributeType
from saleor.attribute.models import Attribute
from saleor.graphql.tests.utils import get_graphql_content
from saleor.page.models import PageType
from saleor.product.models import ProductType

PRODUCT_TYPE_DELETE = """
    mutation deleteProductType($id: ID!) {
        productTypeDelete(id: $id) {
            errors { field message }
            productType { id }
        }
    }
"""

PRODUCT_TYPE_BULK_DELETE = """
    mutation deleteProductTypes($ids: [ID!]!) {
        productTypeBulkDelete(ids: $ids) {
            count
            errors { field message }
        }
    }
"""


def _gid(product_type):
    return graphene.Node.to_global_id("ProductType", product_type.pk)


def _type(name):
    return ProductType.objects.create(name=name, slug=name, kind="normal")


def _attr(slug):
    return Attribute.objects.create(
        name=slug, slug=slug, type=AttributeType.PRODUCT_TYPE
    )


def _slugs():
    return set(
        Attribute.objects.filter(slug__startswith="t-").values_list("slug", flat=True)
    )


def test_behavior_product_type_delete_removes_attributes_assigned_nowhere_else(
    staff_api_client, permission_manage_product_types_and_attributes
):
    # given
    doomed = _type("doomed")
    other = _type("other")
    page_type = PageType.objects.create(name="pt", slug="pt")
    only_product = _attr("t-only-product")
    only_variant = _attr("t-only-variant")
    shared = _attr("t-shared-with-product-type")
    on_page_type = _attr("t-also-on-page-type")
    _attr("t-never-assigned")
    doomed.product_attributes.add(only_product, shared, on_page_type)
    doomed.variant_attributes.add(only_variant)
    other.product_attributes.add(shared)
    page_type.page_attributes.add(on_page_type)

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_TYPE_DELETE,
        {"id": _gid(doomed)},
        permissions=[permission_manage_product_types_and_attributes],
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["productTypeDelete"]["errors"] == []
    assert not ProductType.objects.filter(pk=doomed.pk).exists()
    assert _slugs() == {
        "t-shared-with-product-type",
        "t-also-on-page-type",
        "t-never-assigned",
    }


def test_behavior_product_type_bulk_delete_removes_attributes_assigned_nowhere_else(
    staff_api_client, permission_manage_product_types_and_attributes
):
    # given
    doomed_1 = _type("doomed-1")
    doomed_2 = _type("doomed-2")
    kept = _type("kept")
    a = _attr("t-only-1")
    b = _attr("t-only-2")
    between = _attr("t-between-deleted")
    with_kept = _attr("t-with-kept")
    _attr("t-never-assigned")
    doomed_1.product_attributes.add(a, between, with_kept)
    doomed_2.variant_attributes.add(b, between)
    kept.product_attributes.add(with_kept)

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_TYPE_BULK_DELETE,
        {"ids": [_gid(doomed_1), _gid(doomed_2)]},
        permissions=[permission_manage_product_types_and_attributes],
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["productTypeBulkDelete"]["count"] == 2
    assert _slugs() == {"t-with-kept", "t-never-assigned"}
