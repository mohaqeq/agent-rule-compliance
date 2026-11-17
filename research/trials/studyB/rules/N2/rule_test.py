import graphene
import pytest

from .....thumbnail import ThumbnailSizeRounding
from ....tests.utils import get_graphql_content

QUERY_APP_BRAND_IMAGE = """
    query ($id: ID!, $size: Int, $sizeRounding: ThumbnailSizeRoundingEnum) {
        app(id: $id) {
            brand {
                image(size: $size, sizeRounding: $sizeRounding)
            }
        }
    }
"""


def _get_image_url(api_client, app, size, size_rounding):
    variables = {
        "id": graphene.Node.to_global_id("App", app.id),
        "size": size,
        "sizeRounding": size_rounding,
    }
    response = api_client.post_graphql(QUERY_APP_BRAND_IMAGE, variables)
    content = get_graphql_content(response)
    return content["data"]["app"]["brand"]["image"]


@pytest.mark.parametrize(
    ("size_rounding", "expected_size"),
    [
        (None, 2048),
        (ThumbnailSizeRounding.UP.name, 2048),
        (ThumbnailSizeRounding.NEAREST.name, 1024),
    ],
)
def test_rule_app_brand_image_respects_size_rounding(
    size_rounding, expected_size, staff_api_client, app, icon_image, media_root
):
    # given
    app.brand_logo_default = icon_image
    app.save()
    media_id = graphene.Node.to_global_id("App", app.uuid)
    expected_url = f"https://example.com/thumbnail/{media_id}/{expected_size}/"

    # when
    url = _get_image_url(staff_api_client, app, 1500, size_rounding)

    # then
    assert url == expected_url


def test_rule_app_brand_image_default_rounding_never_returns_fewer_pixels(
    staff_api_client, app, icon_image, media_root
):
    # given
    app.brand_logo_default = icon_image
    app.save()
    media_id = graphene.Node.to_global_id("App", app.uuid)

    # when
    url = _get_image_url(staff_api_client, app, 1025, None)

    # then
    assert url == f"https://example.com/thumbnail/{media_id}/2048/"
