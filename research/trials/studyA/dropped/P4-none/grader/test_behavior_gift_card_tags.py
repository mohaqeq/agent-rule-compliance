import graphene

from saleor.giftcard.models import GiftCard, GiftCardTag
from saleor.graphql.tests.utils import get_graphql_content

GIFT_CARD_DELETE = """
    mutation DeleteGiftCard($id: ID!) {
        giftCardDelete(id: $id) {
            errors { field message }
            giftCard { id }
        }
    }
"""

GIFT_CARD_BULK_DELETE = """
    mutation DeleteGiftCards($ids: [ID!]!) {
        giftCardBulkDelete(ids: $ids) {
            count
            errors { field message }
        }
    }
"""


def _gid(card):
    return graphene.Node.to_global_id("GiftCard", card.pk)


def _card(code, tags):
    card = GiftCard.objects.create(
        code=code,
        initial_balance_amount=10,
        current_balance_amount=10,
        currency="USD",
    )
    card.tags.add(*tags)
    return card


def _names():
    return set(GiftCardTag.objects.values_list("name", flat=True))


def test_behavior_gift_card_delete_removes_tags_used_by_nothing_else(
    staff_api_client, permission_manage_gift_card
):
    # given
    only_here = GiftCardTag.objects.create(name="only-here")
    shared = GiftCardTag.objects.create(name="shared")
    GiftCardTag.objects.create(name="never-used")
    card = _card("DELETEME01", [only_here, shared])
    _card("KEEPME0001", [shared])

    # when
    response = staff_api_client.post_graphql(
        GIFT_CARD_DELETE,
        {"id": _gid(card)},
        permissions=[permission_manage_gift_card],
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["giftCardDelete"]["errors"] == []
    assert not GiftCard.objects.filter(pk=card.pk).exists()
    assert _names() == {"shared", "never-used"}


def test_behavior_gift_card_bulk_delete_removes_tags_used_by_nothing_else(
    staff_api_client, permission_manage_gift_card
):
    # given
    a = GiftCardTag.objects.create(name="only-a")
    b = GiftCardTag.objects.create(name="only-b")
    shared_deleted = GiftCardTag.objects.create(name="shared-between-deleted")
    shared_kept = GiftCardTag.objects.create(name="shared-with-kept")
    GiftCardTag.objects.create(name="never-used")
    card_1 = _card("DELETEME01", [a, shared_deleted, shared_kept])
    card_2 = _card("DELETEME02", [b, shared_deleted])
    _card("KEEPME0001", [shared_kept])

    # when
    response = staff_api_client.post_graphql(
        GIFT_CARD_BULK_DELETE,
        {"ids": [_gid(card_1), _gid(card_2)]},
        permissions=[permission_manage_gift_card],
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["giftCardBulkDelete"]["count"] == 2
    assert _names() == {"shared-with-kept", "never-used"}
