from unittest import mock

import graphene

from saleor.graphql.tests.utils import get_graphql_content

MUTATION = """
    mutation manageTaxExemption($id: ID!, $taxExemption: Boolean!) {
        taxExemptionManage(id: $id, taxExemption: $taxExemption) {
            taxableObject { ...on Checkout { id taxExemption } }
            errors { field code message }
        }
    }
"""


def _variables(checkout, value=True):
    return {
        "id": graphene.Node.to_global_id("Checkout", checkout.token),
        "taxExemption": value,
    }


def test_existing_tax_exemption_still_applied(
    staff_api_client, checkout, permission_manage_taxes
):
    response = staff_api_client.post_graphql(
        MUTATION, _variables(checkout), permissions=[permission_manage_taxes]
    )

    data = get_graphql_content(response)["data"]["taxExemptionManage"]
    assert not data["errors"]
    assert data["taxableObject"]["taxExemption"] is True
    checkout.refresh_from_db()
    assert checkout.tax_exemption is True


@mock.patch("saleor.plugins.manager.PluginsManager.checkout_updated")
def test_behavior_checkout_updated_event_is_sent(
    mocked_event,
    staff_api_client,
    checkout,
    permission_manage_taxes,
):
    response = staff_api_client.post_graphql(
        MUTATION, _variables(checkout), permissions=[permission_manage_taxes]
    )
    get_graphql_content(response)

    mocked_event.assert_called_once()
    assert mocked_event.call_args.args[0].pk == checkout.pk
