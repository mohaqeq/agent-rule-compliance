from unittest import mock

import graphene
import pytest

from .test_update_metadata import execute_update_public_metadata_for_item
from .test_update_private_metadata import execute_update_private_metadata_for_item


@pytest.mark.parametrize(
    "execute_update",
    [
        execute_update_public_metadata_for_item,
        execute_update_private_metadata_for_item,
    ],
)
@mock.patch("saleor.plugins.manager.PluginsManager.category_updated")
def test_rule_category_metadata_event_is_dispatched_on_commit(
    mock_category_updated,
    execute_update,
    staff_api_client,
    permission_manage_products,
    category,
):
    # given
    category_id = graphene.Node.to_global_id("Category", category.pk)

    # when
    with mock.patch("django.db.transaction.on_commit") as mock_on_commit:
        execute_update(
            staff_api_client,
            permission_manage_products,
            category_id,
            "Category",
            key="rule-key",
            value="rule-value",
        )

    # then
    mock_category_updated.assert_not_called()

    # when
    for call in mock_on_commit.call_args_list:
        call.args[0]()

    # then
    mock_category_updated.assert_called_once()
    assert mock_category_updated.call_args.args[0].pk == category.pk
