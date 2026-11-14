# Honour customer erasure requests

Customers can ask us to erase their account, and we promise to do it 30 days after the request. We now need the
part that actually does it, so that nobody has to remove these accounts by hand.

Please add a nullable `delete_requested_at` timestamp on customers (it is set when the request comes in) and a
scheduled task, `delete_requested_customers_task`, in `saleor/account/tasks.py` that deletes every customer whose
`delete_requested_at` is at least 30 days ago. Staff accounts must never be touched. The task returns how many
customers were deleted.

As with other customer deletions, the usual customer-deleted notifications should go out for each removed customer.
