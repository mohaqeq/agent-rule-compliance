from decimal import Decimal

import graphene
from django.db import connection

from .....giftcard.models import GiftCard
from ....tests.utils import get_graphql_content

MUTATION_GIFT_CARD_BULK_TOP_UP = """
    mutation GiftCardBulkTopUp($ids: [ID!]!, $amount: Decimal!) {
        giftCardBulkTopUp(ids: $ids, amount: $amount) {
            count
            errors {
                code
                field
            }
        }
    }
"""

CONCURRENT_INCREASE = Decimal("5.00")


class ConcurrentBalanceWriter:
    """Simulate a concurrent writer.

    After every read of the gift card table, another operation adds a fixed
    amount to the balance of all gift cards. An implementation that writes back
    a balance computed from an earlier read loses the last of these additions.
    """

    def __init__(self):
        self.active = True
        self.runs = 0

    def __call__(self, execute, sql, params, many, context):
        result = execute(sql, params, many, context)
        if (
            self.active
            and sql.lstrip().upper().startswith("SELECT")
            and "giftcard_giftcard" in sql
            and "giftcard_giftcardevent" not in sql
        ):
            self.active = False
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE giftcard_giftcard "
                        "SET current_balance_amount = current_balance_amount + %s",
                        [CONCURRENT_INCREASE],
                    )
                self.runs += 1
            finally:
                self.active = True
        return result


def test_rule_bulk_top_up_does_not_lose_concurrent_balance_change(
    staff_api_client, gift_card_list, permission_manage_gift_card
):
    # given
    amount = Decimal("20.00")
    start_balances = {card.pk: card.current_balance_amount for card in gift_card_list}
    variables = {
        "ids": [graphene.Node.to_global_id("GiftCard", c.pk) for c in gift_card_list],
        "amount": str(amount),
    }
    writer = ConcurrentBalanceWriter()

    # when
    with connection.execute_wrapper(writer):
        response = staff_api_client.post_graphql(
            MUTATION_GIFT_CARD_BULK_TOP_UP,
            variables,
            permissions=[permission_manage_gift_card],
        )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardBulkTopUp"]
    assert data["errors"] == []
    assert data["count"] == len(gift_card_list)
    assert writer.runs >= 1
    for card in GiftCard.objects.filter(pk__in=start_balances):
        expected = start_balances[card.pk] + amount + writer.runs * CONCURRENT_INCREASE
        assert card.current_balance_amount == expected
