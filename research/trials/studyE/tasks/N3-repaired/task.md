# Warehouses per channel

Merchandising wants to see, for a group of channels at once, which warehouses are attached to each of them.

Please add a helper `get_warehouse_ids_by_channel(channels)` in `saleor/graphql/channel/utils.py`.
It takes a list of channels and returns a dict keyed by channel id. Each value is the list of ids of the warehouses
attached to that channel. Channels without any warehouse must still appear in the result, with an empty list.

The order of the ids in each list does not matter.
