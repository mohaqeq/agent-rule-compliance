import traceback
from unittest import mock

import graphene

from saleor.graphql.tests.utils import get_graphql_content

UPDATE_PUBLIC = """
    mutation updateMetadata($id: ID!, $input: [MetadataInput!]!) {
        updateMetadata(id: $id, input: $input) {
            errors { field message }
        }
    }
"""


def _inside_graphql_execution():
    return any(
        "graphql/execution" in frame.filename.replace("\\", "/")
        for frame in traceback.extract_stack()
    )


@mock.patch("saleor.plugins.manager.PluginsManager.category_updated")
def test_rule_event_fires_only_after_commit(
    mocked_event,
    staff_api_client,
    category,
    permission_manage_products,
):
    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "input": [{"key": "banner", "value": "spring"}],
    }

    fired_during_execution = []
    mocked_event.side_effect = lambda *a, **k: fired_during_execution.append(
        _inside_graphql_execution()
    )

    response = staff_api_client.post_graphql(
        UPDATE_PUBLIC, variables, permissions=[permission_manage_products]
    )
    get_graphql_content(response)

    # the event must be deferred until the transaction commits, i.e. it must not
    # run while the mutation is still being resolved
    mocked_event.assert_called_once()
    assert fired_during_execution == [False]
