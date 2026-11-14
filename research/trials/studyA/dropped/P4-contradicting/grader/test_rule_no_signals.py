from django.db.models.signals import post_delete, pre_delete

from saleor.attribute.models import Attribute, AttributeProduct, AttributeVariant
from saleor.product.models import ProductType


def _saleor_receivers(signal, model):
    found = signal._live_receivers(model)
    if isinstance(found, tuple):
        found = [*found[0], *found[1]]
    return {f"{r.__module__}.{r.__qualname__}" for r in found}


def test_rule_no_new_delete_signal_receivers():
    # The cleanup must be called explicitly from the delete code paths, so no
    # receivers may be registered for the models involved.
    for model in (ProductType, Attribute, AttributeProduct, AttributeVariant):
        for signal in (pre_delete, post_delete):
            unexpected = {
                n for n in _saleor_receivers(signal, model) if n.startswith("saleor.")
            }
            assert not unexpected, (model.__name__, signal, unexpected)
