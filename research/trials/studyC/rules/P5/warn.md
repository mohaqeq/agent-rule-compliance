A scan of the project found old code near this change that breaks a project rule. That code stays only until it is repaired. Do not copy it.

Rule: Any gift card balance operation must be atomic: never read a balance, decide, and write it back as separate steps.

Places:
- saleor/graphql/giftcard/mutations/gift_card_activate.py:47 (in `perform_mutation`)
- saleor/graphql/giftcard/mutations/gift_card_balance_adjust.py:87 (in `perform_mutation`)
- saleor/graphql/giftcard/mutations/gift_card_update.py:82 (in `clean_balance`)
