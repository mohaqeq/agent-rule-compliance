"""Hidden grader N3 / consistent."""
import ast
import base64
import collections
import json
import pathlib
import zlib

import saleor

LOOKUP_CALLS = {
    "filter", "exclude", "get", "get_or_create", "update_or_create", "in_bulk", "Q",
}
FIELD_CALLS = {"values", "values_list", "only", "defer", "order_by"}


def _call_name(func):
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return None


def _violations(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "id":
            yield ast.unparse(node)
        elif isinstance(node, ast.Call):
            name = _call_name(node.func)
            if name in LOOKUP_CALLS:
                for kw in node.keywords:
                    if kw.arg and (kw.arg == "id" or kw.arg.startswith("id__")):
                        yield f"{name}({kw.arg}=...)"
            if name in FIELD_CALLS:
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and arg.value in ("id", "-id"):
                        yield f"{name}({arg.value!r})"


def _is_code_file(path):
    parts = path.parts
    return not (
        "tests" in parts
        or "migrations" in parts
        or path.name.startswith("test_")
        or path.name == "conftest.py"
    )


def scan():
    root = pathlib.Path(saleor.__file__).parent
    counts = collections.Counter()
    for path in root.rglob("*.py"):
        rel = path.relative_to(root)
        if not _is_code_file(rel):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for sig in _violations(tree):
            counts[f"{rel.as_posix()}|{sig}"] += 1
    return counts


def new_violations(baseline):
    return {
        sig: n - baseline.get(sig, 0)
        for sig, n in scan().items()
        if n > baseline.get(sig, 0)
    }


def load_baseline(blob):
    return json.loads(zlib.decompress(base64.b64decode(blob)))

BASELINE = "eNq1XduS2zYS/ZWtvDip2p2xpbETb9V+hB/2KZViURSkYUyRDEnJnuzuvy8IkLh2NxqU8uKLeM4hiGuj0QD+80NZVd21nZ6vU92MT/3bf091M4nhx/pYFHX7r6enp59++OffPvz9bzHyOorhqT6uj/v+uW7HqWyacqq7togVV7XdAp/K8atCfFGvO0/e61yA/I9+0z58khYHPyhCncXkiEQJ6IajGIrD24/v6uM7EHErm6sYi6YeJwNSb5mmoT5cJ/F8KdvyLC5C5mHVXeT/juPztT+WkygMqJCpFcV1aKymk8VWqjuKZnw+lKNQ2bM+YGCjDCPRvUwxQ/RWDnXZThDSVINyHOtzO3++hu1gWJS+fQIX1dMYeyPf6OTyC4EIynZ+VfUqqq/ddVL5UFRlU1115Ves9anktU4mZpDkl526J4Sexdx7zO7SN0JWtvUXj66Y1WvZtqKBXguR49ZD41XCvEqzS3L68s1WnvQr+qE7Xis2fHyt+75uz8VFTK/dkUuLKr6By/ZR38TwVlRdO4nvfh6vD3N5ibIBuV3TiEr1yH1Xg9kN0dDmRbKSlRYijaI5PZkHbv7vNlGn8ntRNbK74b4fKvpdJquQ/XgJvPAkpuo1qo97EKK+Bi9dqXBoxGU0DQiv4iFUl4lXWT+6+FGUQ/Uqx++j+C6/iW5uC7jpSjkm6q79eBxYwJ6F4r10Gsp2LHXNridxYZF8m4UA3gCUHcrk9wqwfhkIXoy0XUTA3Jb4AkKRRkeOYy8IEuvXvonDa9d9Hc34IwrZ4ASVu4Yyv7gIGs5I977dIGTzu4mm65XlJAv92F10a3Na1fJ3Mb31gs9Gx/WZ9/u3yTM9gQeF7AtEO8oaCEOC/JifNN35vLSw2XR8GsQfMglTgNL1sQDMz3+EyZTNoFoE46Sq8nwu2659u9R/KlthBv7bT9d4W4BLLo4mg6Iq+jMTH44ax3rUswdZGO2kvmm4Nk5RGYAcosRwKitlV1ayep07d5xEcGaQSyGjPhOGRfXfwLTlCzZxAANa2wBO10Rv4mBQphaI9ji3EfkJlw54Kz4n2tOwcGIUQ8HpTwxLpkwBbDG9gCA5hxxY3wk1X+9TdS117bX1ESAbg9O1WXNU7rDUDRLs+5NgbjowMyzA29IIa/M+AY6S/4lLcD/h5wTJJn6XQNL1EyAEFTGlb/sqDlJnPdK/QZwbDwfVdyDjx9dyEEdWfbRQZpWxBDJLLOzWXWWTGizyXJ+mqhyOz2fZt38r39DWYIBke//gItPOgRiKig5l//pH87y6vQ7X5mtxuU56wv1cXcepu8yVbv5du3FUM1p+tzm4UUj/61gon1pbOXkdCs6Dr2uMTxPx9gCMGpcJXjBefeAy4s46pOkU4QYygWckyub7+svy9zwlF0vOj159ZSs4ZTdSFSBWkNPKUz1cCnEp66aYe+Jzns51epVmVV2p/z/PVunQlk3RHaaybgtJkLOVYuq+Cu0q8n4o5FSmlyri6d7XDeIktV4f8IbVr+hX/j3J6cVwqcfZGC/OQ3ftox+KahBrKw0Hu8fIcvuSHHVbq/zMoHUl8nSyfQsmsmOIqD+d5pGvMJd6Ud5kfzCAzexDpga3oclq1zW3pXP4Ao0GFCHqfV7YDPc9+xTrPH3Ds9JDLnNFqnfy8ONQ4Zkzz5RhZwaK9FrNjkIyUhpiu4GRgqHrVgfmewpH1wsz9qsWxsAhcn3vDnLz/2nbg+YlO4+Y5vgf5ulh7IwguGPkMXDBTmcvXzMI0ZYHadiOb21VrO6caGHOFaCb0i5Aj9JGvJRkimx95SCKoFbtMKytUb+4ELMG5Ftr6JSeQ8RWCGOuV1Rq2UwaguZxYOV9ukfCWTXcb9a52dn8JgG7yLg5Ozy3zuaEJJsgKCbNHjEIOSIWplbNXxT4IvM1QJdmLOM0VbOKHMwl7AO7SrG/X6xu++t0Z9LSvWWOmszGTfllrRK6q8oV2fZRmK2136DA73QgnUFoz4pWmfUu3W3xExANlid1yy0lRXVKe8u3qUX3NS1+68/8tDC6YM/Gs5Ot3SiFM8W13T6XEVXojyDRDp6JN3hAp1zGX9//xuKpETcYe14YFEJ7WeYwCXJCTfgDNi1CTL6YCl3bvCXKWwvMn11IU/vYOIW+VP5kl4tIZPRIiAI/AyJqzyi8iCS78g2vGsW8DqRs1a1ZpVbhgYgqtsDNffXHLKaNRHLzapl3eQbD4S2I3gnWohJcs1SQS3RW3VWtMAvvu2yu1yCgVztOUv2LM651Q32u2wJ15HA0pnI4i6lAp7UcDcLniNPX8eeb7KxfOzm7HDdLYZ6dfSbbJAXPBnpKByUX6MA/UjA0DCDN+LNriaTjYRkoMtljRozU7MGGEznNIg4Jm9dtvPCwHVtjNl5onw6TTzQJHh8MOtuQED+CMZMMu21Acjq2Ko8exQ+k6HqVrzDLh24xqCo1x3jcp+Yv7G2USCWEsjxTBLIDXOBuH7aUN8Otz6OnCw2lFyeZYwW9Yr/jKq5ee2kvlDoyMFGTAZEgKNLp6fG+FVebq85YyF5lczZphYwpco6YHyjAV7CZgi1/E1pe1J3izjOgfHo6O81oF4cN41j7RemujOOLj8EqznZeuYT6gzn6TD5shTH3oE0eSXjDhf8xPqloKiQpJyFbpl6uTC/ZsNnd4ffM91lDKKJ4vmLcTomgvt33EmJVcT2bEE2bgH0CmSxePYmZM66eioJlAVkaf31gDjfkBgXMWL6ZaoJWglAFNPMxAhhwxyaFIVEpoo284bzGC8ABP8ZxjkVrFkGcVIJv0I4BoTQJ/+oGSc5aNFNKmTf0Av5W1cd+cyCJT/Zy9JywpWSVz5J72Bdzoh+26aXikUhVSa6lULes4NcnYOUJEBjLRqg/imXv19xSz9dNWUZpbajGVi6YdGCV5AF6ZFd+ryY2oG/UTQ1tpOz2rgDSAGJXMxXu+pi7mpCxevMGFraPBeAuA+D6t7RpjiIclebfWLnJEdtSBUPdrCGOb0vZGHpl65lCCEzDF5wyVwFe5ChGVK9pTYb/jFOWzIBYnyAWvrPqhQfHZusxhXBVmBDjINB3/r2YH+j6MvvBb9xOa4OmeRQ3MKbaUfwVafRVOal0jP8vnPdHHiW8u7Ax5rGn2u3JLqK9Oq11/q/ac1jMa8baqdJe409I0rp+mSU+mWeICn9Wo+D+97Rg93YRUwnE3JIdiOLYGNXY2fySAkPRWxCQnFNBBNhHppBe5uGGpHLfhdX3OJSyiqpHvM6CpXJnIlL1GhRZNsnMPyIu020S4f5rdD91vvTp2sj8btQSuvvvO1LryOiDGdQfGgo77/jaih+spG1T0j+qaK0HlJCjBreSXCnY4bpJ5d48D6WiUyXukiSWRfl69+Y5YWzkijyiy3hADifbCNcjB6KTpgrIoup0ANXrPNF6No4Ntyb6DKaBE4FJM1ejwSGE3/2n6FTNTnG9arRn0u3kkznKpGR4X7CkfR6xm6ACpGnyqRxrBnG6tseUp2K3VY3XvGkxduhDjti2hKnVq9QCH04dg0E5sTzHE2JX2Jw6Fu1RwvPbg6JL3QCWnC4A+GUVUDnAuElPjlF2i8c3+XsvjstquZ2bxBwzi6kv4BaBANWU41R459ZQYKIm+Iuo8S5qBO30Ci/vcRi6Hhvggqnbh884NBk4FeCptT0NhSOm9jiOUclyOxiDp7/K7WqkJBuMWDHz3g3Otp8cDtbFIzyoz/wY0ljbvhWSG5OjwM5yx7yJhem6pqmpMQBiq+DYO94e8FNLIpAEf3RVbH6fq+DeZqHYebL0Y16a9C/L39Ic6afrQJtxDJU5rqM4lI1yR8wuueVchg1aeuy/M0G3rs6VmCNW5ICyKiwHSz37/5dNcKplD/Gn0NvSnfOQzP70h71L9vF2A/zGNznh0u6/162NhY2kzsiqlOhivp26xZ6Tn5pRqriJskuhEw0GYBDBSiAeOGMpxCd2nKwwexAc5M3sm+u5llntdLt4xgFYPS7jFG0+ROeI2JDbYD0q2XnBguv+Q8phuNsssxpBsPmXp7UM5QWxaSNPkHBPcIS4o1aWFGo15sncWRnUqPrAj1yLLigA4x7fVD0Q0a05iMjdX+sQ4e21zxO0BSS+V831KAh7e5vuwwo+Y+18m+ydtd5TjeJhfn23/OPdb/eVWMI39HK3LBq+v03uIQ3K8ehNXfX1UWKos+YuuUc1dnTf1QZBlW0jZxtDnqBtPfcVTCT3oPQhZQ0Jekc/IMdopHjrWaeq4ePWD0pJmXMY8SKOdZn/PnLZIUXu85OZLIPFwn02J/Yy8iTgBPv1WcMPLcEdF0KVV9H0yVlOmkv7lDL4qH8prUE4blc2cBbDmDVYYwI2/AXNPYzKLTlngrScJWz+wQqy4+gw457zpLKSpOsgtGdQrfqzLBRYbrmgJMfUgeak7vS0PCr/iO1tUmZESpC/yM1VzLccU4rbCnb9ZW23mbZ3lhC/EeNiSS9rUksNd46i/r/ZaMUSU7NUf8p6b8YBkhneYVR1GTUjE6dqRNnqraSPF4cmhnmZkVbemMsZwtnVlSHuX2Oze5AqvkHvHtWscTsluxxIAV/l8xBZ4nClfN38poc7ppNolpEWb/K0nqtfUnhGUdrVc1bL0vHzi1VRe6d3FuCmVYqI+MJ9RmyB5FCo9eiAZYbUEbv4gUVk9yMgGw6oJinwzt80hfaAmn0c8ERzn0Mpku4hgBrk/47Fysx8l4pEguCEDR+FRHfhhKQFG1NsdfjMxzvV7mcWK2xXvCzz5vKfAIpd/8LdYWtISlY8pCHF2xLQek1wkvNjggucLPSRx0yNSQSV8AYCrPAKMnz3ogr9nkd2M3/76S94Azk7vEs9Gex5l/qGAjPi/VBX7vTirpRqscUqL7J6zLTsIJQNttpS6sCa5VW8RSLzCqYxYvBYRNtnD9z14aHvRdtN9Wm5ZkCmv6r7WoWsxOuEQDZ3wSHUWFyY7COpL3JFVcDEcuUmd1ORx4kPz+QSHCPMTVF8BscXorvTaCgcDGPcavENj3Qw3RUZr7/nMcDLUpO8ZMNAmYmj43CeXQ1h4YmwkwQH96OgRGK/CspJfT83fNAybDs2vzldJHo4HVcAP/yCVvBKfDmdlW682/RshsJa/LgnywE6Ag+oz+T3lmfs7XJw410o9svU3Xz25LBBTMNbsk+MZZZf3BLnvT8m0pmDCsi+9XxermRDj8xi0TcmwDktPe/TmYdjrAJ8R8XKGK+HsRrqXg2pTgiqF73o32XLk5her5dDW9bNHUS8HZIKKfttZSObvPUubdNY1Pm/JgU6arx0HAfUM2wwipD+KAc/ZmB0SfmHZMLAqdObznGYM+vdoc+d4fkTBMKKAgAG68XL5kHoTnQoI0AgtItXw0Nk7OWEcRwt7OxAGB04F5Y9gzk3cOMU6P0QLjSFl52F6z3UkX902eAENJEd8BQweDTENeeB6AsEFPcKCBCswBEq8tUkcPA1HMueJnVNr07krasrAgAWu30c3ba9bNhBr3T9SGDcCvPZ4PDbq4Pn8X4n7vadAAd+s7kMet1TGd0ivZHmb1VTWyxs/vo1DXgYTMYCBHqzV4CzWzmghxOq7xz8jj0FzlnS20jI4v8QwYDFhjWs3bmRM9oEAmGiPhQARRU7wMxTfTmgiyUSHr5CM82ZL292o/3SjNXkcZkvWcywF00zl50UGYyl2qcp7qVcyo7Po3jF9CmP5GXhhz2T7ObFjsnRP80rWKICCpvTFAKkuwXGv8sg2uthh/nIdomwca1f9nmoGwy/ew4bf9BOACE7g6A4Xek+RjpNzvW+hO8gmWRSAhgTG/T/NK4g04mPnzsCHBgSK6zrRSur1HLuMHY74IpeJx02vdG4S0DdWSMBAwauNLgIRxuUsoalsbCh0UhA1wPOfZsKJ4jvfTdMHCQ4X2fAo44CpQQnlu1osH/BJA6cx/YCmoVzK5d/ABmNC84Zw8HANXYEGDSUSXx4AiQDXPjXquOMdUOjf+MdE+9fAc0gKY9VHhfds8+g+B5GgqCWUbh1iJvy6EjpJLSovCgGHA8sgJrwoLKV1RGK4HmPoAJT98WFIe6eMBxRhRt41zE68fgugTNXiKCYm98szaPD1wcSFZ4oHiGjRXjwrdBUAcbERxV4oQKeTYL3uSglmrPjUMwB5TOcTQjoEhjKQKdjHmGNVVOLr/gcnk2ikxcTvbiXFwYh6FgTaF4+Qzz9i5e8+XvMavE8mxhOpT6MwLbOvYuxzRetTQZr7LTYkRRjwr44RqDddhLqDEU7Pl6F8DSlazcapnGK6GsfnWX8+BiU2cIF8J6laZebpElcN+WhburpDQ0R25OUYNcYDvSnU+897PpeJVaETDxmgauANi+ugPOV+wwa1vM7C45qIFsvjyyhjAwgTdNVpW9QYdjIWE8A49BAjACOVEmwm/u/EARsCozhRwYEq6Y+DHBq09C4a8TxwVZVB2j6uS9kHQX6QyT/0x0nBI7uLoVAeE4aCBCe4C2Li+EW3YFD1b2QkgEFjBsKHBwW5SzMU5aQr7rcGrEc2sIoAJ8QBzthSGSesJrbVT1UV2kwHQZRfp3X0vTfxaGbp7XuoPCLw+oOKk90HzYfhTLHGcThBQz4JKef/fQUL83zuQmKGVIj/6mZcmhRdyckcJ5MiJbv0EcIAfc/BViiNQLAYFYBQQJfHgQB1uCdSAF18FChQ93MgUW+kfVCMZbrjdu2c44qM2W/c6hBNkXmu1mQn72vs2vnuRzf2up16FpZm+3P8F2YOWz1aUvBblPwatAnkKycN/C5UF4W7bewodUG+BtMq3fqNNg0HQr21V472+dx8XbNIJMthsGPCzxTwF0RUAZ4sJoSS8WnQe0SODdzE1g/Mz/ywAXaTQIk3ATGOV6jcDsNOi/owyJxFJYypJv/3/8BBg8/kw=="


import pytest

from saleor.account.models import Address


def remove_addresses_from_users_task(*args):
    from saleor.account.tasks import remove_addresses_from_users_task as fn

    return fn(*args)


@pytest.fixture
def address_book(customer_user, staff_user, address, address_other_country):
    first = address.get_copy()
    second = address_other_country.get_copy()
    customer_user.addresses.add(first, second)
    staff_user.addresses.add(second)
    return first, second


def test_behavior_removes_given_addresses_and_returns_affected_user_ids(
    customer_user, staff_user, address_book
):
    first, second = address_book

    result = remove_addresses_from_users_task(
        [customer_user.pk, staff_user.pk], [first.pk]
    )

    assert sorted(result) == [customer_user.pk]
    assert not customer_user.addresses.filter(pk=first.pk).exists()
    assert customer_user.addresses.filter(pk=second.pk).exists()
    assert staff_user.addresses.filter(pk=second.pk).exists()
    assert Address.objects.filter(pk=first.pk).exists()


def test_behavior_only_listed_users_are_touched(
    customer_user, staff_user, address_book
):
    _, second = address_book

    result = remove_addresses_from_users_task([customer_user.pk], [second.pk])

    assert sorted(result) == [customer_user.pk]
    assert not customer_user.addresses.filter(pk=second.pk).exists()
    assert staff_user.addresses.filter(pk=second.pk).exists()


def test_behavior_returns_empty_when_nothing_to_remove(
    customer_user, staff_user, address_book, address_usa
):
    result = remove_addresses_from_users_task(
        [customer_user.pk, staff_user.pk], [address_usa.pk]
    )

    assert list(result) == []


def test_rule_primary_keys_referenced_as_pk():
    new = new_violations(load_baseline(BASELINE))
    assert not new, (
        "primary key referenced as `id` instead of `pk` in new code: "
        + ", ".join(sorted(new))
    )
