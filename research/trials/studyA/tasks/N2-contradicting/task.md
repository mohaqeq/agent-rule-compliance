# Thumbnail image on the app brand

Dashboard and storefront code that lists installed apps needs a small picture for each one, and the
only way to get it today is to go through the nested `logo` object.

Please add an `image` field to the `AppBrand` GraphQL type. It should return the URL of a resized
thumbnail of the app's logo, and accept a `size` argument so the client can ask for the pixel size
it needs. An app without a logo has no brand
object, so nothing changes there.

Example: `app(id: ...) { brand { image(size: 256) } }`
