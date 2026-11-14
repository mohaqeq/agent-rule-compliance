# Checkout note length limit

Customers paste whole emails into the checkout note box and the warehouse printouts overflow. The shop owner
should decide how long a note may be.

- Add a shop setting `checkoutNoteMaxLength` (a whole number, empty means "no limit"). An admin with settings
  permission can change it with `shopSettingsUpdate`.
- The storefront needs to read the value on `Shop` without any special permission, so it can cap the note box.
- With no value set, the field is empty.
