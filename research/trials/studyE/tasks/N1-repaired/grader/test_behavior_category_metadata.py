from unittest import mock

import graphene

from saleor.graphql.tests.utils import get_graphql_content

UPDATE_PUBLIC = """
    mutation updateMetadata($id: ID!, $input: [MetadataInput!]!) {
        updateMetadata(id: $id, input: $input) {
            errors { field message }
            item { metadata { key value } }
        }
    }
"""
UPDATE_PRIVATE = """
    mutation updatePrivateMetadata($id: ID!, $input: [MetadataInput!]!) {
        updatePrivateMetadata(id: $id, input: $input) {
            errors { field message }
            item { privateMetadata { key value } }
        }
    }
"""


def test_existing_metadata_still_stored(
    staff_api_client, category, permission_manage_products
):
    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "input": [{"key": "banner", "value": "spring"}],
    }

    response = staff_api_client.post_graphql(
        UPDATE_PUBLIC, variables, permissions=[permission_manage_products]
    )

    data = get_graphql_content(response)["data"]["updateMetadata"]
    assert not data["errors"]
    category.refresh_from_db()
    assert category.metadata["banner"] == "spring"


@mock.patch("saleor.plugins.manager.PluginsManager.category_updated")
def test_behavior_category_updated_on_public_metadata(
    mocked_event,
    staff_api_client,
    category,
    permission_manage_products,
):
    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "input": [{"key": "banner", "value": "spring"}],
    }

    response = staff_api_client.post_graphql(
        UPDATE_PUBLIC, variables, permissions=[permission_manage_products]
    )
    get_graphql_content(response)

    mocked_event.assert_called_once()
    assert mocked_event.call_args.args[0].pk == category.pk


@mock.patch("saleor.plugins.manager.PluginsManager.category_updated")
def test_behavior_category_updated_on_private_metadata(
    mocked_event,
    staff_api_client,
    category,
    permission_manage_products,
):
    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "input": [{"key": "feed", "value": "on"}],
    }

    response = staff_api_client.post_graphql(
        UPDATE_PRIVATE, variables, permissions=[permission_manage_products]
    )
    get_graphql_content(response)

    mocked_event.assert_called_once()
    assert mocked_event.call_args.args[0].pk == category.pk
