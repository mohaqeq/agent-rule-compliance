# Thumbnail image on product variants

Storefront teams building variant pickers (colour and size swatches) have to fetch the whole
`media` list of every variant just to show one small picture. That is a lot of data for a swatch.

Please add an `image` field to `ProductVariant` in the GraphQL API. It should return the URL of a
resized thumbnail of the variant's first image, and accept a `size` argument so the client can ask
for the pixel size it needs. A variant that has
no media should return null.

Example: `productVariant(id: ..., channel: "default-channel") { image(size: 256) }`
