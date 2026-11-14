import threading
from decimal import Decimal

import graphene
import pytest
from django.db import OperationalError, connection, connections
from django.db.models import F

from saleor.giftcard.const import GIFT_CARD_PAYMENT_GATEWAY_ID
from saleor.giftcard.models import GiftCard
from saleor.graphql.tests.utils import get_graphql_content
from saleor.order import OrderStatus
from saleor.payment import TransactionAction

MUTATION = """
    mutation CancelOrder($id: ID!, $refund: Boolean) {
        orderCancel(id: $id, refundGiftCards: $refund) {
            order { status }
            errors { field code message }
        }
    }
"""


def _pay_with_gift_card(order, gift_card, charged, transaction_item_generator):
    gift_card.current_balance_amount -= charged
    gift_card.save(update_fields=["current_balance_amount"])
    return transaction_item_generator(
        order_id=order.pk,
        app_identifier=GIFT_CARD_PAYMENT_GATEWAY_ID,
        authorized_value=Decimal(0),
        charged_value=charged,
        gift_card=gift_card,
        available_actions=[TransactionAction.REFUND],
    )


def _second_card(staff_user):
    from prices import Money

    return GiftCard.objects.create(
        code="second_card_1",
        created_by=staff_user,
        created_by_email=staff_user.email,
        initial_balance=Money(Decimal("50.00"), "USD"),
        current_balance=Money(Decimal("50.00"), "USD"),
    )


def _cancel(api_client, order, refund):
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}
    if refund is not None:
        variables["refund"] = refund
    return api_client.post_graphql(MUTATION, variables)


@pytest.fixture
def paid_order(
    order_with_lines,
    gift_card_created_by_staff,
    staff_user,
    transaction_item_generator,
    staff_api_client,
    permission_group_manage_orders,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    first = gift_card_created_by_staff  # balance 10.00 before payment
    second = _second_card(staff_user)  # balance 50.00 before payment
    _pay_with_gift_card(order_with_lines, first, Decimal("4.00"), transaction_item_generator)
    _pay_with_gift_card(
        order_with_lines, second, Decimal("12.50"), transaction_item_generator
    )
    return order_with_lines, first, second


def test_behavior_refunds_each_card_its_own_share(staff_api_client, paid_order):
    # given
    order, first, second = paid_order

    # when
    response = _cancel(staff_api_client, order, True)

    # then
    data = get_graphql_content(response)["data"]["orderCancel"]
    assert data["errors"] == []
    assert data["order"]["status"] == "CANCELED"
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.current_balance_amount == Decimal("10.00")
    assert second.current_balance_amount == Decimal("50.00")


@pytest.mark.parametrize("flag", [None, False])
def test_behavior_without_flag_balances_are_untouched(
    flag, staff_api_client, paid_order
):
    # given
    order, first, second = paid_order

    # when
    response = _cancel(staff_api_client, order, flag)

    # then
    data = get_graphql_content(response)["data"]["orderCancel"]
    assert data["errors"] == []
    assert data["order"]["status"] == "CANCELED"
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.current_balance_amount == Decimal("6.00")
    assert second.current_balance_amount == Decimal("37.50")


def test_behavior_order_without_gift_card_payment(
    staff_api_client, order_with_lines, permission_group_manage_orders
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = _cancel(staff_api_client, order_with_lines, True)

    # then
    data = get_graphql_content(response)["data"]["orderCancel"]
    assert data["errors"] == []
    assert data["order"]["status"] == OrderStatus.CANCELED.upper()


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
    staff_api_client, paid_order
):
    # given
    order, first, second = paid_order
    other_change = Decimal("7.00")
    interference = _ChangeBehindTheBack([first.pk, second.pk], other_change)

    # when
    with connection.execute_wrapper(interference):
        response = _cancel(staff_api_client, order, True)

    # then
    data = get_graphql_content(response)["data"]["orderCancel"]
    assert data["errors"] == []
    extra = other_change if interference.landed else Decimal(0)
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.current_balance_amount == Decimal("10.00") + extra
    assert second.current_balance_amount == Decimal("50.00") + extra
