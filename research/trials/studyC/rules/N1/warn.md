A scan of the project found old code near this change that breaks a project rule. That code stays only until it is repaired. Do not copy it.

Rule: When triggering plugin manager methods to dispatch webhook events, always use `call_event` from `saleor.core.utils.events` instead of calling the manager method directly.

Places:
- saleor/graphql/meta/extra_methods.py:27 (in `extra_channel_actions`)
- saleor/graphql/meta/extra_methods.py:32 (in `extra_collection_actions`)
- saleor/graphql/meta/extra_methods.py:37 (in `extra_fulfillment_actions`)
- saleor/graphql/meta/extra_methods.py:42 (in `extra_gift_card_actions`)
- saleor/graphql/meta/extra_methods.py:59 (in `extra_product_actions`)
- saleor/graphql/meta/extra_methods.py:68 (in `extra_variant_actions`)
- saleor/graphql/meta/extra_methods.py:74 (in `extra_shipping_zone_actions`)
- saleor/graphql/meta/extra_methods.py:79 (in `extra_transaction_item_actions`)
- saleor/graphql/meta/extra_methods.py:87 (in `extra_user_actions`)
- saleor/graphql/meta/extra_methods.py:93 (in `extra_warehouse_actions`)
- saleor/graphql/meta/extra_methods.py:98 (in `extra_voucher_actions`)
- saleor/graphql/meta/extra_methods.py:103 (in `extra_shop_actions`)
