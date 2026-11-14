# Default note on new gift cards

Support staff issue gift cards by hand and often forget to say why. The shop owner wants a standard note recorded
on every new gift card unless the person issuing it writes their own.

- Add a shop setting `defaultGiftCardNote` (text, empty means "no default note"). An admin with settings
  permission can change it with `shopSettingsUpdate` and read it back on `Shop`.
- When `giftCardCreate` is called without a `note`, the new gift card gets the default note, shown in its events
  like any other note. A note given in the request wins.
- With no default set, nothing changes.
