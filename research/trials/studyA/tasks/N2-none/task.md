# Thumbnail logo on the shop

Storefronts and the dashboard header both need the store logo, but they show it at different
sizes and today there is no way to get a small version of it over the API.

Please let merchants have a logo on the shop settings, and add a `logo` field to the `Shop`
GraphQL type. It should return the URL of a resized thumbnail of the store logo, and accept a
`size` argument so the client can ask for the pixel size it needs. A shop without a logo should return null.

Example: `shop { logo(size: 256) }`
