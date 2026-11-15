from datetime import timedelta

from django.utils import timezone

from .....account.models import User
from ....tests.utils import get_graphql_content

DELETE_INACTIVE_CUSTOMERS_MUTATION = """
    mutation deleteInactiveCustomers($inactiveMonths: Int!) {
        deleteInactiveCustomers(inactiveMonths: $inactiveMonths) {
            count
            errors {
                field
                code
            }
        }
    }
"""


def test_rule_assigned_gift_card_is_not_spendable_after_customer_deletion(
    staff_api_client,
    customer_user,
    gift_card,
    permission_manage_users,
):
    # given a restricted, active gift card and a customer who is inactive
    customer_user.last_login = timezone.now() - timedelta(days=800)
    customer_user.save(update_fields=["last_login"])
    gift_card.assigned_to = customer_user
    gift_card.assigned_to_email = customer_user.email
    gift_card.is_active = True
    gift_card.save(update_fields=["assigned_to", "assigned_to_email", "is_active"])
    email = customer_user.email

    # when
    response = staff_api_client.post_graphql(
        DELETE_INACTIVE_CUSTOMERS_MUTATION,
        {"inactiveMonths": 12},
        permissions=[permission_manage_users],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["deleteInactiveCustomers"]
    assert data["errors"] == []
    assert not User.objects.filter(email=email).exists()
    gift_card.refresh_from_db()
    assert gift_card.assigned_to_email == email
    still_restricted_to_user = gift_card.assigned_to_id is not None
    assert still_restricted_to_user or gift_card.is_active is False
