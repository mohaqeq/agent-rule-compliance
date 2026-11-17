<!-- source: AGENTS.md lines 554-571 -->
## Correctness (Django): use `pk` instead of `id`

Don't use the `id` DB field in Django models, instead use `pk` when referencing the object ID
field from a model.

Don't:

```py
book = Book.objects.get(id=1)
id = book.id
```

Do:

```py
book = Book.objects.get(pk=1)
id = book.pk
```
