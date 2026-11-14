"""Runs inside the ucn-studya-stats container: violation ~ site + (1 | rule), logistic, random intercept per rule.
Reads a rows JSON (rule_id, site, violations), prints one JSON object. Never raises: failures become converged=false.
Fit: statsmodels BinomialBayesMixedGLM (variational Bayes); odds ratios are exp(posterior mean +/- 1.96 sd)."""
import json
import math
import sys


def main(path):
    try:
        import pandas as pd
        from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
        rows = json.load(open(path))
        df = pd.DataFrame(rows)
        df["site"] = pd.Categorical(df["site"], categories=["consistent"] + sorted(set(df["site"]) - {"consistent"}))
        if df["site"].nunique() < 2 or df["rule_id"].nunique() < 2 or df["violations"].nunique() < 2:
            return {"run": True, "converged": False, "reason": "not enough variation (sites, rules or outcomes)"}
        m = BinomialBayesMixedGLM.from_formula("violations ~ C(site)", {"rule": "0 + C(rule_id)"}, df)
        r = m.fit_vb()
        names = list(m.exog_names)
        terms = []
        for n, mu, sd in zip(names, r.fe_mean, r.fe_sd):
            if n == "Intercept":
                continue
            if not (math.isfinite(mu) and math.isfinite(sd) and sd > 0):
                return {"run": True, "converged": False, "reason": f"non-finite estimate for {n}"}
            terms.append({"term": n.replace("C(site)[T.", "").rstrip("]"), "or": math.exp(mu),
                          "lo": math.exp(mu - 1.96 * sd), "hi": math.exp(mu + 1.96 * sd)})
        return {"run": True, "converged": True, "method": "BinomialBayesMixedGLM.fit_vb", "terms": terms,
                "rule_sd_log_odds": float(math.exp(r.vcp_mean[0]))}
    except Exception as e:
        return {"run": True, "converged": False, "reason": f"{type(e).__name__}: {str(e)[:200]}"}


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1])))
