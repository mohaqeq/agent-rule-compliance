A scan of the project found old code near this change that breaks a project rule. That code stays only until it is repaired. Do not copy it.

Rule: Never read `settings.SITE_ID` directly to identify the current site; resolve the site with `Site.objects.get_current()` (or the `get_site_promise` dataloader in the GraphQL layer).

Places:
- saleor/graphql/product/bulk_mutations/product_variant_stocks_create.py:111 (in `perform_mutation`)
- saleor/graphql/product/bulk_mutations/product_variant_stocks_update.py:157 (in `perform_mutation`)
