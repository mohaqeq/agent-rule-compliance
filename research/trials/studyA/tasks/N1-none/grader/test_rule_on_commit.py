import traceback
from unittest import mock

import graphene

from saleor.graphql.tests.utils import get_graphql_content

MUTATION = """
    mutation manageTaxExemption($id: ID!, $taxExemption: Boolean!) {
        taxExemptionManage(id: $id, taxExemption: $taxExemption) {
            taxableObject { ...on Checkout { id } }
            errors { field code message }
        }
    }
"""


def _inside_graphql_execution():
    return any(
        "graphql/execution" in frame.filename.replace("\\", "/")
        for frame in traceback.extract_stack()
    )


@mock.patch("saleor.plugins.manager.PluginsManager.checkout_updated")
def test_rule_event_fires_only_after_commit(
    mocked_event,
    staff_api_client,
    checkout,
    permission_manage_taxes,
):
    variables = {
        "id": graphene.Node.to_global_id("Checkout", checkout.token),
        "taxExemption": True,
    }

    fired_during_execution = []
    mocked_event.side_effect = lambda *a, **k: fired_during_execution.append(
        _inside_graphql_execution()
    )

    response = staff_api_client.post_graphql(
        MUTATION, variables, permissions=[permission_manage_taxes]
    )
    get_graphql_content(response)

    # the event must be deferred until the transaction commits, i.e. it must not
    # run while the mutation is still being resolved
    mocked_event.assert_called_once()
    assert fired_during_execution == [False]
