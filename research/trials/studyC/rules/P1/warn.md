A scan of the project found old code near this change that breaks a project rule. That code stays only until it is repaired. Do not copy it.

Rule: When the customer a gift card is assigned to is deleted, the card must not silently become free for anyone to use again; it stays restricted until staff reassign it.

Places:
- saleor/graphql/account/bulk_mutations/customer_bulk_delete.py:63 (in `bulk_action`)
- saleor/graphql/account/bulk_mutations/staff_bulk_delete.py:76 (in `bulk_action`)
- saleor/graphql/account/mutations/staff/customer_delete.py:42 (in `perform_mutation`)
