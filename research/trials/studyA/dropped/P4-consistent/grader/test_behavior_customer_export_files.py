import graphene
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from saleor.account.models import User
from saleor.csv.models import ExportFile
from saleor.graphql.tests.utils import get_graphql_content

CUSTOMER_DELETE = """
    mutation CustomerDelete($id: ID) {
        customerDelete(id: $id) {
            errors { field message }
            user { id }
        }
    }
"""

CUSTOMER_BULK_DELETE = """
    mutation CustomerBulkDelete($ids: [ID!]!) {
        customerBulkDelete(ids: $ids) {
            count
            errors { field message }
        }
    }
"""


def _export(user, name):
    export_file = ExportFile.objects.create(
        user=user, content_file=ContentFile(b"a,b\n1,2\n", name=name)
    )
    return export_file.content_file.name


def _gid(user):
    return graphene.Node.to_global_id("User", user.pk)


def test_behavior_customer_delete_removes_export_files(
    staff_api_client, staff_user, customer_user, permission_manage_users, media_root
):
    # given
    own_1 = _export(customer_user, "customer_1.csv")
    own_2 = _export(customer_user, "customer_2.csv")
    staff_path = _export(staff_user, "staff.csv")
    assert default_storage.exists(own_1)
    assert default_storage.exists(own_2)

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_DELETE,
        {"id": _gid(customer_user)},
        permissions=[permission_manage_users],
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["customerDelete"]["errors"] == []
    assert not User.objects.filter(pk=customer_user.pk).exists()
    assert not ExportFile.objects.filter(content_file__in=[own_1, own_2]).exists()
    assert not default_storage.exists(own_1)
    assert not default_storage.exists(own_2)
    # files of other users are untouched
    assert default_storage.exists(staff_path)
    assert ExportFile.objects.filter(content_file=staff_path).exists()


def test_behavior_customer_bulk_delete_removes_export_files(
    staff_api_client, staff_user, customer_user, permission_manage_users, media_root
):
    # given
    other = User.objects.create(email="other-customer@example.com")
    kept = User.objects.create(email="kept-customer@example.com")
    path_1 = _export(customer_user, "bulk_1.csv")
    path_2 = _export(other, "bulk_2.csv")
    kept_path = _export(kept, "kept.csv")

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_BULK_DELETE,
        {"ids": [_gid(customer_user), _gid(other)]},
        permissions=[permission_manage_users],
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["customerBulkDelete"]["count"] == 2
    assert not default_storage.exists(path_1)
    assert not default_storage.exists(path_2)
    assert default_storage.exists(kept_path)
    assert User.objects.filter(pk=kept.pk).exists()
