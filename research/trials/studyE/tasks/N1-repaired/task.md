# Tell apps when a category's metadata changes

Staff and apps store custom values (public and private metadata) on categories through the `updateMetadata` and
`updatePrivateMetadata` mutations. Those values drive storefront banners and feeds, but nothing tells our integrations
when they change, so their copies of the category go stale.

Please make changing a category's metadata through those mutations tell subscribed apps: subscribed apps must be
notified that the category was updated whenever its metadata (public or private) actually changes. The mutations'
arguments and responses stay as they are.
