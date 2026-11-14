# Let staff set a gift card's expiry date on its own

Today the only way to change when a gift card expires is the full gift card update, which asks for a lot of other
fields. Support teams just want to extend or clear an expiry date quickly.

Please add a mutation `giftCardExpiryDateUpdate(id: ID!, expiryDate: Date)` that sets the gift card's expiry date
(passing no date removes it). It needs the same permission as other gift card changes and returns the gift card
(`giftCard { id expiryDate }`) plus the usual gift card errors.

Our integrations keep their own copy of gift cards, so subscribed apps must be notified that the gift card was
updated whenever staff change an expiry date this way.
