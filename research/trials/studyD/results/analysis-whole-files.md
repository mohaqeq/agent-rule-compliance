Study D: 444 runs, 156 violations

## Checks as delivered

| Rule | Class | Notes of the author | Errors |
|---|---|---|---|
| N1 | pattern | Reports a direct call of a PluginsManager webhook-event method (a method whose name matches a WebhookEventAsyncType, read from the workspace) on a receiver named like a manager, for example `manager.product_updated(p)`, also inside `transaction.on_commit(lambda: ...)`; a call wrapped as `call_event(manager.x, ...)` is correct. It cannot see a call through an alias (`f = manager.x; f()`) or through a receiver whose name does not contain 'manager'. | 0 |
| N2 | pattern | Reports changed code that makes NEAREST the default or the forced thumbnail rounding: DEFAULT_THUMBNAIL_SIZE_ROUNDING set to anything but UP, NEAREST as a parameter/field default or as an `or`/`.get()` fallback, None treated as NEAREST, NEAREST hard-coded in get_thumbnail_size(), a nearest-size min(THUMBNAIL_SIZES, ...) in code without any rounding choice, a resolver that ignores its size_rounding argument, and `= NEAREST` defaults in schema.graphql. It cannot see rounding logic written in other forms, or a new thumbnail field that has no sizeRounding argument. | 0 |
| N3 | pattern | Reports `id` used as a Django field in changed code: lookups such as filter(id=...), get(id=...), Q(id__in=...), product__id=..., string references such as values_list('id'), OuterRef('id'), order_by('-id'), and `.id` read on a variable that is known to hold a model instance (a parameter annotated with a model class that the check resolves through the imports, a result of Model.objects.get/first/create, a loop over a queryset, `self` in a model, or one ForeignKey step from such a variable). It misses `.id` on objects whose type it cannot prove (for example `info.context.user.id`, attributes of other objects, unannotated parameters). | 0 |
| P1 | pattern | Reports changed code that drops the trace of a gift card assignment in a user-deletion path (clears `assigned_to_email` in a function or file about delete/remove/anonymize/deactivate), a usage check that tests only `assigned_to`/`assigned_to_id` ("assigned and not this user", or `assigned_to__isnull=True` as "free") in a function that never looks at `assigned_to_email` or `usage_restriction_reason`. It misses other forms, for example a change to the `assigned_to` foreign key, raw SQL, or a restriction check that is written in another way. | 0 |
| P3 | pattern | Reports changed code that reads `settings.SITE_ID` (also through getattr) outside the two modules that implement site resolution, and queries that assume one site: Site/SiteSettings .objects.get() with no filter, .first()/.last()/.earliest()/.latest(), indexing [0], or get(pk=<constant>). It cannot see per-site data keyed by a constant (for example a cache key or a module-level dict without the site), because that needs knowledge of what the data means. | 0 |
| P5 | pattern | Reports a changed write of a gift card balance (`current_balance_amount`/`current_balance` by assignment, `-=`/`+=`, setattr, `.update(...)` or a cleaned_input key) whose value is computed from a balance read in Python, or that sits under an `if` that tests the balance, when the row is not locked with select_for_update (in the same function, or by every caller when the card is a parameter); an F() expression is accepted. It cannot see races that span several functions in other ways, for example a check in one request and an F() write without a condition in another, and it does not check that an F() write is clamped at zero. | 0 |

## All rules

- Recall: 102 / 156 (65.4%)
- False alarms: 100 / 288 (34.7%)
- H5: INCONCLUSIVE

## For each rule

| Rule | Violations found (recall) | Runs without violation that got a finding (false alarms) |
|---|---|---|
| N1 | 23 / 23 (100.0%) | 26 / 46 (56.5%) |
| N2 | 22 / 37 (59.5%) | 27 / 42 (64.3%) |
| N3 | 23 / 23 (100.0%) | 27 / 46 (58.7%) |
| P1 | 0 / 30 (0.0%) | 0 / 49 (0.0%) |
| P3 | 23 / 23 (100.0%) | 0 / 56 (0.0%) |
| P5 | 11 / 20 (55.0%) | 20 / 49 (40.8%) |

## For each site type

| Site | Violations found (recall) | Runs without violation that got a finding (false alarms) |
|---|---|---|
| consistent | 3 / 10 (30.0%) | 6 / 50 (12.0%) |
| control | 0 / 4 (0.0%) | 0 / 26 (0.0%) |
| none | 4 / 11 (36.4%) | 2 / 49 (4.1%) |
| contradicting | 95 / 131 (72.5%) | 92 / 163 (56.4%) |

## For each study and model

| Study and model | Violations found (recall) | Runs without violation that got a finding (false alarms) |
|---|---|---|
| A haiku | 24 / 40 (60.0%) | 8 / 65 (12.3%) |
| A sonnet | 24 / 40 (60.0%) | 4 / 65 (6.2%) |
| B haiku | 42 / 57 (73.7%) | 68 / 123 (55.3%) |
| B sonnet | 12 / 19 (63.2%) | 20 / 35 (57.1%) |

## Only runs with task success

| Rule | Violations found (recall) | Runs without violation that got a finding (false alarms) |
|---|---|---|
| N1 | 23 / 23 (100.0%) | 26 / 46 (56.5%) |
| N2 | 3 / 3 (100.0%) | 27 / 40 (67.5%) |
| N3 | 22 / 22 (100.0%) | 27 / 44 (61.4%) |
| P1 | 0 / 23 (0.0%) | 0 / 46 (0.0%) |
| P3 | 22 / 22 (100.0%) | 0 / 56 (0.0%) |
| P5 | 1 / 1 (100.0%) | 20 / 48 (41.7%) |

## Cross-rule findings (the check of one rule on runs of a different rule; not confirmed by a grader)

| Check | Runs of rule | Runs with a finding |
|---|---|---|
| N3 | N2 | 71 |
| N3 | P5 | 17 |
| P3 | N2 | 1 |
