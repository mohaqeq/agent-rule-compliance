A scan of the project found old code near this change that breaks a project rule. That code stays only until it is repaired. Do not copy it.

Rule: A thumbnail field must let the `sizeRounding` argument choose how a requested size is matched; the default is `UP`, and `NEAREST` is opt-in.

Places:
- saleor/graphql/app/types.py:353 (in `resolve_default`)
- saleor/graphql/app/types.py:378 (in `get_logo_cache_size`)
