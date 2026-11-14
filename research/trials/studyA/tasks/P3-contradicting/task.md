# Low stock warnings in the stock mutations

Warehouse staff keep overselling by accident because nobody notices when a variant is nearly out of stock in a
warehouse. Operations wants the shop owner to decide what "low" means.

- Add a shop setting `lowStockWarningThreshold` (a whole number, empty means "no warnings"). An admin with
  settings permission can change it with `shopSettingsUpdate` and read it back on `Shop`.
- `productVariantStocksCreate` and `productVariantStocksUpdate` should report, in a new response field
  `lowStockWarnings`, the stocks they just wrote whose quantity is below the threshold, so the dashboard can show
  a banner after saving.
- With no threshold set the list is empty.
