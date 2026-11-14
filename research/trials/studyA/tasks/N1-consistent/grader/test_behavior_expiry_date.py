import datetime
from unittest import mock

import graphene

from saleor.graphql.tests.utils import get_graphql_content

MUTATION = """
    mutation giftCardExpiryDateUpdate($id: ID!, $expiryDate: Date) {
        giftCardExpiryDateUpdate(id: $id, expiryDate: $expiryDate) {
            giftCard { id expiryDate }
            errors { field message }
        }
    }
"""


def test_behavior_expiry_date_is_set(
    staff_api_client, gift_card, permission_manage_gift_card
):
    gift_card.expiry_date = None
    gift_card.save(update_fields=["expiry_date"])
    new_date = datetime.date.today() + datetime.timedelta(days=90)
    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
        "expiryDate": new_date.isoformat(),
    }

    response = staff_api_client.post_graphql(
        MUTATION, variables, permissions=[permission_manage_gift_card]
    )

    data = get_graphql_content(response)["data"]["giftCardExpiryDateUpdate"]
    assert not data["errors"]
    assert data["giftCard"]["expiryDate"] == new_date.isoformat()
    gift_card.refresh_from_db()
    assert gift_card.expiry_date == new_date


def test_behavior_expiry_date_is_removed(
    staff_api_client, gift_card, permission_manage_gift_card
):
    gift_card.expiry_date = datetime.date.today() + datetime.timedelta(days=10)
    gift_card.save(update_fields=["expiry_date"])
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.pk)}

    response = staff_api_client.post_graphql(
        MUTATION, variables, permissions=[permission_manage_gift_card]
    )

    data = get_graphql_content(response)["data"]["giftCardExpiryDateUpdate"]
    assert not data["errors"]
    gift_card.refresh_from_db()
    assert gift_card.expiry_date is None


@mock.patch("saleor.plugins.manager.PluginsManager.gift_card_updated")
def test_behavior_gift_card_updated_event_is_sent(
    mocked_event,
    staff_api_client,
    gift_card,
    permission_manage_gift_card,
):
    new_date = datetime.date.today() + datetime.timedelta(days=30)
    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
        "expiryDate": new_date.isoformat(),
    }

    response = staff_api_client.post_graphql(
        MUTATION, variables, permissions=[permission_manage_gift_card]
    )
    get_graphql_content(response)

    mocked_event.assert_called_once()
    assert mocked_event.call_args.args[0].pk == gift_card.pk
