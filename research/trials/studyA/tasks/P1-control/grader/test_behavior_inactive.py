from datetime import timedelta
from unittest import mock

from django.utils import timezone

from saleor.account.models import User
from saleor.graphql.tests.utils import assert_no_permission, get_graphql_content

MUTATION = """
    mutation DeleteInactive($months: Int!) {
        deleteInactiveCustomers(inactiveMonths: $months) {
            count
            errors { field code message }
        }
    }
"""


def _customer(email, last_login_days_ago):
    user = User.objects.create(email=email, is_active=True)
    user.last_login = timezone.now() - timedelta(days=last_login_days_ago)
    user.save(update_fields=["last_login"])
    return user


def test_behavior_deletes_only_dormant_customers_without_orders(
    staff_api_client, permission_manage_users, order
):
    # given
    dormant = _customer("dormant@example.com", 400)
    active = _customer("active@example.com", 10)
    buyer = _customer("buyer@example.com", 400)
    order.user = buyer
    order.save(update_fields=["user"])
    staff = _customer("oldstaff@example.com", 400)
    staff.is_staff = True
    staff.save(update_fields=["is_staff"])

    # when
    response = staff_api_client.post_graphql(
        MUTATION, {"months": 6}, permissions=[permission_manage_users]
    )

    # then
    data = get_graphql_content(response)["data"]["deleteInactiveCustomers"]
    assert data["errors"] == []
    assert data["count"] == 1
    assert not User.objects.filter(pk=dormant.pk).exists()
    for kept in (active, buyer, staff):
        assert User.objects.filter(pk=kept.pk).exists()


def test_behavior_threshold_is_in_months(staff_api_client, permission_manage_users):
    # given
    old = _customer("old@example.com", 800)
    recent = _customer("recent@example.com", 200)

    # when
    response = staff_api_client.post_graphql(
        MUTATION, {"months": 24}, permissions=[permission_manage_users]
    )

    # then
    data = get_graphql_content(response)["data"]["deleteInactiveCustomers"]
    assert data["count"] == 1
    assert not User.objects.filter(pk=old.pk).exists()
    assert User.objects.filter(pk=recent.pk).exists()


def test_behavior_requires_manage_users(staff_api_client):
    # given
    dormant = _customer("dormant@example.com", 400)

    # when
    response = staff_api_client.post_graphql(MUTATION, {"months": 6})

    # then
    assert_no_permission(response)
    assert User.objects.filter(pk=dormant.pk).exists()


def test_behavior_rejects_less_than_one_month(
    staff_api_client, permission_manage_users
):
    # given
    dormant = _customer("dormant@example.com", 400)

    # when
    response = staff_api_client.post_graphql(
        MUTATION, {"months": 0}, permissions=[permission_manage_users]
    )

    # then
    data = get_graphql_content(response)["data"]["deleteInactiveCustomers"]
    assert data["errors"][0]["field"] == "inactiveMonths"
    assert User.objects.filter(pk=dormant.pk).exists()


def test_behavior_sends_customer_deleted_event(
    staff_api_client, permission_manage_users
):
    # given
    dormant = _customer("dormant@example.com", 400)

    # when
    with mock.patch("saleor.plugins.manager.PluginsManager.customer_deleted") as sent:
        response = staff_api_client.post_graphql(
            MUTATION, {"months": 6}, permissions=[permission_manage_users]
        )
        get_graphql_content(response)

    # then
    assert sent.call_count == 1
    assert sent.call_args[0][0].email == dormant.email
