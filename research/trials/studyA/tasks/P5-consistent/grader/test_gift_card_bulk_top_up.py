import threading
from decimal import Decimal

import graphene
import pytest
from django.db import OperationalError, connection, connections
from django.db.models import F
from prices import Money

from saleor.giftcard.models import GiftCard
from saleor.graphql.tests.utils import assert_no_permission, get_graphql_content

MUTATION = """
    mutation GiftCardBulkTopUp($ids: [ID!]!, $amount: Decimal!) {
        giftCardBulkTopUp(ids: $ids, amount: $amount) {
            count
            errors { field code message }
        }
    }
"""


def _make_cards(user, balances):
    cards = []
    for i, balance in enumerate(balances):
        cards.append(
            GiftCard.objects.create(
                code=f"topup-card-{i}",
                created_by=user,
                created_by_email=user.email,
                initial_balance=Money(Decimal("100.00"), "USD"),
                current_balance=Money(Decimal(balance), "USD"),
            )
        )
    return cards


def _ids(cards):
    return [graphene.Node.to_global_id("GiftCard", c.pk) for c in cards]


def _top_up(api_client, cards, amount, permissions):
    return api_client.post_graphql(
        MUTATION,
        {"ids": _ids(cards), "amount": str(amount)},
        permissions=permissions,
    )


def test_behavior_adds_amount_to_every_card(
    staff_api_client, customer_user, permission_manage_gift_card
):
    # given
    cards = _make_cards(customer_user, ["10.00", "0.00", "37.50"])

    # when
    response = _top_up(
        staff_api_client, cards, "5.25", [permission_manage_gift_card]
    )

    # then
    data = get_graphql_content(response)["data"]["giftCardBulkTopUp"]
    assert data["errors"] == []
    assert data["count"] == 3
    balances = {c.pk: c for c in GiftCard.objects.filter(pk__in=[c.pk for c in cards])}
    assert [balances[c.pk].current_balance_amount for c in cards] == [
        Decimal("15.25"),
        Decimal("5.25"),
        Decimal("42.75"),
    ]


def test_behavior_initial_balance_is_unchanged(
    staff_api_client, customer_user, permission_manage_gift_card
):
    # given
    cards = _make_cards(customer_user, ["10.00", "99.00"])

    # when
    response = _top_up(
        staff_api_client, cards, "20.00", [permission_manage_gift_card]
    )

    # then
    assert get_graphql_content(response)["data"]["giftCardBulkTopUp"]["count"] == 2
    for card in cards:
        card.refresh_from_db()
        assert card.initial_balance_amount == Decimal("100.00")


@pytest.mark.parametrize("amount", ["0", "-3.00"])
def test_behavior_rejects_non_positive_amount(
    amount, staff_api_client, customer_user, permission_manage_gift_card
):
    # given
    cards = _make_cards(customer_user, ["10.00", "20.00"])

    # when
    response = _top_up(
        staff_api_client, cards, amount, [permission_manage_gift_card]
    )

    # then
    data = get_graphql_content(response)["data"]["giftCardBulkTopUp"]
    assert data["count"] == 0
    assert [(e["field"], e["code"]) for e in data["errors"]] == [("amount", "INVALID")]
    for card, expected in zip(cards, ["10.00", "20.00"], strict=True):
        card.refresh_from_db()
        assert card.current_balance_amount == Decimal(expected)


def test_behavior_requires_permission(staff_api_client, customer_user):
    # given
    cards = _make_cards(customer_user, ["10.00"])

    # when
    response = _top_up(staff_api_client, cards, "5.00", [])

    # then
    assert_no_permission(response)
    cards[0].refresh_from_db()
    assert cards[0].current_balance_amount == Decimal("10.00")


class _ChangeBehindTheBack:
    """Change the stored balances through a second connection, once, right before the
    mutation's first write to a gift card balance reaches the database.

    This is what a concurrent checkout charge or another staff action looks like to the
    mutation. If the mutation holds a row lock until it writes, the second connection
    cannot get in (it gives up after a short lock timeout) and nothing is changed
    behind its back. Otherwise the change lands and the mutation must not lose it.
    """

    def __init__(self, pks, extra):
        self.pks = list(pks)
        self.extra = extra
        self.fired = False
        self.landed = False

    def _apply(self):
        try:
            with connections["default"].cursor() as cursor:
                cursor.execute("SET lock_timeout = '500ms'")
            GiftCard.objects.filter(pk__in=self.pks).update(
                current_balance_amount=F("current_balance_amount") + self.extra
            )
            self.landed = True
        except OperationalError:
            self.landed = False
        finally:
            connections.close_all()

    def __call__(self, execute, sql, params, many, context):
        text = sql.upper()
        if (
            not self.fired
            and text.lstrip().startswith('UPDATE "GIFTCARD_GIFTCARD"')
            and "CURRENT_BALANCE_AMOUNT" in text
        ):
            self.fired = True
            thread = threading.Thread(target=self._apply)
            thread.start()
            thread.join()
        return execute(sql, params, many, context)


@pytest.mark.django_db(transaction=True)
def test_rule_balance_change_made_in_the_meantime_is_not_lost(
    staff_api_client, customer_user, permission_manage_gift_card
):
    # given
    start = ["10.00", "0.00", "37.50"]
    cards = _make_cards(customer_user, start)
    other_change = Decimal("7.00")
    amount = Decimal("5.25")
    interference = _ChangeBehindTheBack([c.pk for c in cards], other_change)

    # when
    with connection.execute_wrapper(interference):
        response = _top_up(
            staff_api_client, cards, amount, [permission_manage_gift_card]
        )

    # then
    data = get_graphql_content(response)["data"]["giftCardBulkTopUp"]
    assert data["errors"] == []
    assert data["count"] == 3
    extra = other_change if interference.landed else Decimal(0)
    for card, begin in zip(cards, start, strict=True):
        card.refresh_from_db()
        assert card.current_balance_amount == Decimal(begin) + amount + extra
