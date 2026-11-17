import graphene
import pytest

from saleor.graphql.tests.utils import get_graphql_content

QUERY = """
    query ($id: ID, $size: Int, $rounding: ThumbnailSizeRoundingEnum) {
        app(id: $id) {
            brand {
                image(size: $size, sizeRounding: $rounding)
            }
        }
    }
"""


def _image_url(staff_api_client, app, **kw):
    variables = {"id": graphene.Node.to_global_id("App", app.id), **kw}
    response = staff_api_client.post_graphql(QUERY, variables)
    content = get_graphql_content(response)
    brand = content["data"]["app"]["brand"]
    return None if brand is None else brand["image"]


@pytest.fixture
def app_with_logo(app, icon_image, media_root):
    app.brand_logo_default = icon_image
    app.save()
    return app


def _path(app, size):
    gid = graphene.Node.to_global_id("App", app.uuid)
    return f"/thumbnail/{gid}/{size}/"


def test_behavior_image_returns_thumbnail_url(staff_api_client, app_with_logo):
    url = _image_url(staff_api_client, app_with_logo, size=256)
    assert url is not None
    assert url.endswith(_path(app_with_logo, 256))


def test_behavior_image_is_null_without_logo(staff_api_client, app):
    assert _image_url(staff_api_client, app, size=256) is None


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
    size, rounding, expected, staff_api_client, app_with_logo
):
    url = _image_url(staff_api_client, app_with_logo, size=size, rounding=rounding)
    assert url is not None
    assert url.endswith(_path(app_with_logo, expected))
