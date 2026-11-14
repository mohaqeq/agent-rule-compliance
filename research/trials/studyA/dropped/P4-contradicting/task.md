# Clean up attributes when a product type is deleted

Staff delete product types from the dashboard, one at a time or in bulk. The attributes that were set up
for a product type (including its variant attributes) stay behind afterwards, and the attribute list
fills up with entries that nothing uses any more.

When a product type is deleted, also delete the attributes it had that no other product type or page
type uses. Attributes still assigned elsewhere must stay, and so must attributes that were already
unassigned before. This should work the same whether the product type is deleted on its own or as part
of a bulk delete.
