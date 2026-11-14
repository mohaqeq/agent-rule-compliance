# Generated invoices per order

Finance needs to know which invoices already exist for a set of orders before they run the month-end export.

Please add a helper `get_generated_invoice_ids_by_order(orders)` in a new module `saleor/invoice/utils.py`.
It takes a list of orders and returns a dict keyed by order id. Each value is the list of ids of that order's invoices
that are already generated (their generation finished successfully). Orders without any generated invoice must still
appear in the result, with an empty list.

The order of the ids in each list does not matter.
