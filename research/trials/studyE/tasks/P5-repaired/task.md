# Top up several gift cards at once

Marketing is running a "stored-value bonus" promotion, and support is currently adding the bonus to customers' gift
cards one card at a time. That is slow and error-prone, so we want staff to be able to do it in one go.

Please add a staff mutation `giftCardBulkTopUp(ids: [ID!]!, amount: Decimal!)` that adds `amount` to the current
balance of every listed gift card. Like the other gift card bulk mutations it returns `count` (how many cards were
topped up) and `errors`, and it needs the manage-gift-cards permission.

- The amount must be greater than zero. Otherwise nothing changes and the response has an `INVALID` error on the
  `amount` field.
- A card's initial balance stays as it is; only the current balance goes up.
