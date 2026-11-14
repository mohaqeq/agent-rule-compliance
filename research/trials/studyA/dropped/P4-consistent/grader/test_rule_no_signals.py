from django.db.models.signals import post_delete, pre_delete

from saleor.account.models import User
from saleor.csv.models import ExportFile

# Receivers that already exist in the repository before the ticket.
ALLOWED = {
    (User, "saleor.account.signals.delete_avatar"),
}


def _saleor_receivers(signal, model):
    found = signal._live_receivers(model)
    if isinstance(found, tuple):
        found = [*found[0], *found[1]]
    return {f"{r.__module__}.{r.__qualname__}" for r in found}


def test_rule_no_new_delete_signal_receivers():
    # The cleanup must be called explicitly from the delete code paths, so no
    # new receivers may be registered for the models involved.
    for model in (User, ExportFile):
        for signal in (pre_delete, post_delete):
            names = _saleor_receivers(signal, model)
            unexpected = {
                n
                for n in names
                if n.startswith("saleor.") and (model, n) not in ALLOWED
            }
            assert not unexpected, (model.__name__, signal, unexpected)
