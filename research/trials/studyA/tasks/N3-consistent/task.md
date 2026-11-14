# Bulk removal of saved addresses

Support often has to clean up customers' address books in bulk, for example after an import produced duplicate addresses.

Please add a background task `remove_addresses_from_users_task(user_pks, address_pks)` in `saleor/account/tasks.py`.
It takes a list of users and a list of addresses. For each of those users it removes the listed addresses from their
saved addresses. Users who do not have a given address are left as they are, and the address records themselves are not
deleted.

The task returns the ids of the users who actually lost at least one address, so support can see who was touched.
The order of the returned ids does not matter.
