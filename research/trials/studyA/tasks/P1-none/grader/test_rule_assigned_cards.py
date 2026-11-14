from datetime import timedelta

from django.utils import timezone

from saleor.account.models import User
from saleor.giftcard.models import GiftCard


def _run_task():
    from saleor.account.tasks import delete_requested_customers_task

    return delete_requested_customers_task()


def _dormant(email):
    user = User.objects.create(email=email, is_active=True)
    user.delete_requested_at = timezone.now() - timedelta(days=60)
    user.save(update_fields=["delete_requested_at"])
    return user


def _assign(gift_card, user):
    gift_card.assigned_to = user
    gift_card.assigned_to_email = user.email
    gift_card.is_active = True
    gift_card.save(update_fields=["assigned_to", "assigned_to_email", "is_active"])


def test_rule_card_of_deleted_customer_is_not_spendable(gift_card):
    # given an active card restricted to a dormant customer
    user = _dormant("dormant@example.com")
    _assign(gift_card, user)
    email = user.email

    # when
    count = _run_task()

    # then the customer is gone, but the card is kept, locked, and remembers
    # who it was assigned to
    assert count == 1
    assert not User.objects.filter(pk=user.pk).exists()
    gift_card.refresh_from_db()
    assert gift_card.is_active is False
    assert gift_card.assigned_to_email == email


def test_rule_all_cards_of_deleted_customers_are_locked(gift_card_list):
    # given several dormant customers, each with a restricted active card
    cards = gift_card_list[:2]
    emails = []
    for i, card in enumerate(cards):
        user = _dormant(f"dormant{i}@example.com")
        _assign(card, user)
        emails.append(user.email)

    # when
    count = _run_task()

    # then
    assert count == 2
    for card, email in zip(cards, emails, strict=True):
        assert GiftCard.objects.filter(pk=card.pk).exists()
        card.refresh_from_db()
        assert card.is_active is False
        assert card.assigned_to_email == email


def test_rule_cards_of_remaining_customers_untouched(gift_card, customer_user):
    # given a card restricted to a customer who is not deleted
    _assign(gift_card, customer_user)
    _dormant("dormant@example.com")

    # when
    count = _run_task()

    # then
    assert count == 1
    gift_card.refresh_from_db()
    assert gift_card.is_active is True
    assert gift_card.assigned_to_id == customer_user.pk
