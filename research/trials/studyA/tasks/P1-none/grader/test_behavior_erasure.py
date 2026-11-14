from datetime import timedelta
from unittest import mock

from django.utils import timezone

from saleor.account.models import User


def _run_task():
    from saleor.account.tasks import delete_requested_customers_task

    return delete_requested_customers_task()


def _customer(email, requested_days_ago=None, is_staff=False):
    user = User.objects.create(email=email, is_active=True, is_staff=is_staff)
    if requested_days_ago is not None:
        user.delete_requested_at = timezone.now() - timedelta(days=requested_days_ago)
        user.save(update_fields=["delete_requested_at"])
    return user


def test_behavior_deletes_only_customers_past_the_grace_period(order):
    # given
    due = _customer("due@example.com", 45)
    recent = _customer("recent@example.com", 5)
    never = _customer("never@example.com")
    staff = _customer("staff@example.com", 90, is_staff=True)

    # when
    count = _run_task()

    # then
    assert count == 1
    assert not User.objects.filter(pk=due.pk).exists()
    for kept in (recent, never, staff):
        assert User.objects.filter(pk=kept.pk).exists()


def test_behavior_does_nothing_when_nobody_is_due():
    # given
    recent = _customer("recent@example.com", 5)

    # when
    count = _run_task()

    # then
    assert count == 0
    assert User.objects.filter(pk=recent.pk).exists()


def test_behavior_sends_customer_deleted_event(django_capture_on_commit_callbacks):
    # given
    due = _customer("due@example.com", 45)

    # when
    with (
        mock.patch("saleor.plugins.manager.PluginsManager.customer_deleted") as sent,
        django_capture_on_commit_callbacks(execute=True),
    ):
        _run_task()

    # then
    assert sent.call_count == 1
    assert sent.call_args[0][0].email == due.email
