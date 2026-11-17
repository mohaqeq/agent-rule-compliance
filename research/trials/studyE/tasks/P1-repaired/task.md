# Clean up dormant customer accounts

Our customer list is full of accounts that signed up once and never came back, and merchants keep asking
us to prune them. Staff need a way to remove them in one go instead of selecting them in the dashboard
page by page.

Please add a staff mutation, `deleteInactiveCustomers(inactiveMonths: Int!)`, that deletes every customer who has
no orders and who has not logged in for at least that many months. Staff accounts must never be touched. It
returns how many customers were deleted (`count`) and the usual `errors`. It is available to staff who can manage
users, and an `inactiveMonths` below 1 is rejected with an error on that field.

As with other customer deletions, the usual customer-deleted notifications should go out for each removed customer.
