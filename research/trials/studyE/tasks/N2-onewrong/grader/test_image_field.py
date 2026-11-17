import graphene
import pytest

from saleor.graphql.tests.utils import get_graphql_content

QUERY = """
    query ($id: ID!, $channel: String, $size: Int, $rounding: ThumbnailSizeRoundingEnum) {
        productVariant(id: $id, channel: $channel) {
            image(size: $size, sizeRounding: $rounding)
        }
    }
"""


def _image_url(staff_api_client, permission_manage_products, variant, channel, **kw):
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "channel": channel.slug,
        **kw,
    }
    response = staff_api_client.post_graphql(
        QUERY,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    return content["data"]["productVariant"]["image"]


def _media_path(variant, size):
    media = variant.variant_media.first().media
    gid = graphene.Node.to_global_id("ProductMedia", media.pk)
    return f"/thumbnail/{gid}/{size}/"


def test_behavior_image_returns_thumbnail_url_of_variant_media(
    staff_api_client, permission_manage_products, variant_with_image, channel_USD
):
    url = _image_url(
        staff_api_client,
        permission_manage_products,
        variant_with_image,
        channel_USD,
        size=256,
    )
    assert url is not None
    assert url.endswith(_media_path(variant_with_image, 256))


def test_behavior_image_is_null_without_media(
    staff_api_client, permission_manage_products, variant, channel_USD
):
    url = _image_url(
        staff_api_client, permission_manage_products, variant, channel_USD, size=256
    )
    assert url is None


@pytest.mark.parametrize(
    ("size", "rounding", "expected"),
    [
        (1500, None, 2048),
        (1500, "UP", 2048),
        (1500, "NEAREST", 1024),
        (700, None, 1024),
        (700, "NEAREST", 512),
    ],
)
def test_rule_image_size_rounding_follows_argument_and_defaults_up(
    size,
    rounding,
    expected,
    staff_api_client,
    permission_manage_products,
    variant_with_image,
    channel_USD,
):
    url = _image_url(
        staff_api_client,
        permission_manage_products,
        variant_with_image,
        channel_USD,
        size=size,
        rounding=rounding,
    )
    assert url is not None
    assert url.endswith(_media_path(variant_with_image, expected))
