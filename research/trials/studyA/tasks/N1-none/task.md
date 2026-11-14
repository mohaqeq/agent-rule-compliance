# Tell apps when a checkout's tax exemption changes

Staff can switch a checkout's tax exemption on or off with the `taxExemptionManage` mutation. Changing the exemption
changes what the customer pays, but nothing tells our integrations about it, so they keep showing stale totals.

Please make `taxExemptionManage` on a checkout (the existing arguments and response stay as they are) tell subscribed
apps about it: subscribed apps must be notified that the checkout was updated whenever staff change its tax
exemption this way. Orders are not part of this request.
