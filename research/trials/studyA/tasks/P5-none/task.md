# Give gift card money back when staff cancel an order

When we cancel an order that a customer paid for with a gift card, the customer has to write to support to get that
money back onto the card, and someone then adds it by hand. We want cancelling to be able to do it.

Please add an optional `refundGiftCards: Boolean` argument (default `false`) to the `orderCancel` mutation. When it is
`true`, the amount that was charged to each gift card on the order is added back to the current balance of that same
card as part of the cancellation. When it is `false` or omitted, cancelling behaves exactly as it does today.

- An order paid with two gift cards gives each card back its own share.
- Orders paid by other means, or with no gift card at all, are unaffected by the flag.
