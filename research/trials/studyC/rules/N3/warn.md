A scan of the project found old code near this change that breaks a project rule. That code stays only until it is repaired. Do not copy it.

Rule: Don't use the `id` DB field in Django models, instead use `pk` when referencing the object ID field from a model.

Places:
- saleor/graphql/channel/utils.py:122 (in `delete_invalid_warehouse_to_shipping_zone_relations`)
- saleor/graphql/channel/utils.py:152 (in `_get_invalid_shipping_zone_warehouses_ids`)
