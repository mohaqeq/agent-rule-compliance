import datetime
import traceback
from unittest import mock

import graphene

from saleor.graphql.tests.utils import get_graphql_content

MUTATION = """
    mutation giftCardExpiryDateUpdate($id: ID!, $expiryDate: Date) {
        giftCardExpiryDateUpdate(id: $id, expiryDate: $expiryDate) {
            giftCard { id }
            errors { field message }
        }
    }
"""


def _inside_graphql_execution():
    return any(
        "graphql/execution" in frame.filename.replace("\\", "/")
        for frame in traceback.extract_stack()
    )


@mock.patch("saleor.plugins.manager.PluginsManager.gift_card_updated")
def test_rule_event_fires_only_after_commit(
    mocked_event,
    staff_api_client,
    gift_card,
    permission_manage_gift_card,
):
    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
        "expiryDate": (datetime.date.today() + datetime.timedelta(days=30)).isoformat(),
    }

    fired_during_execution = []
    mocked_event.side_effect = lambda *a, **k: fired_during_execution.append(
        _inside_graphql_execution()
    )

    response = staff_api_client.post_graphql(
        MUTATION, variables, permissions=[permission_manage_gift_card]
    )
    get_graphql_content(response)

    # the event must be deferred until the transaction commits, i.e. it must not
    # run while the mutation is still being resolved
    mocked_event.assert_called_once()
    assert fired_during_execution == [False]
