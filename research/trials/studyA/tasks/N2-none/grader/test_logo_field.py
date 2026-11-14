import graphene
import pytest

from saleor.graphql.tests.utils import get_graphql_content

QUERY = """
    query ($size: Int, $rounding: ThumbnailSizeRoundingEnum) {
        shop {
            logo(size: $size, sizeRounding: $rounding)
        }
    }
"""


def _logo_url(api_client, **variables):
    response = api_client.post_graphql(QUERY, variables)
    content = get_graphql_content(response)
    return content["data"]["shop"]["logo"]


@pytest.fixture
def site_with_logo(site_settings, icon_image, media_root):
    site_settings.logo = icon_image
    site_settings.save()
    return site_settings


def _path(site_settings, size):
    gid = graphene.Node.to_global_id("SiteSettings", site_settings.pk)
    return f"/thumbnail/{gid}/{size}/"


def test_behavior_logo_returns_thumbnail_url(api_client, site_with_logo):
    url = _logo_url(api_client, size=256)
    assert url is not None
    assert url.endswith(_path(site_with_logo, 256))


def test_behavior_logo_is_null_without_logo(api_client, site_settings):
    assert _logo_url(api_client, size=256) is None


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
def test_rule_logo_size_rounding_follows_argument_and_defaults_up(
    size, rounding, expected, api_client, site_with_logo
):
    url = _logo_url(api_client, size=size, rounding=rounding)
    assert url is not None
    assert url.endswith(_path(site_with_logo, expected))
