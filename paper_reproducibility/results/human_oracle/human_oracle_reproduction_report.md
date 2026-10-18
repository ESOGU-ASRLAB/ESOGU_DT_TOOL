# Human Oracle reproduction report

## Result

- Public evaluator files parsed: 21 (7 source suites x 3 evaluators).
- Aligned items: 1074.
- Unmatched or unresolved items: 0.
- Majority consensus: 740 Unique and 334 Similar.
- Unanimous three-rater agreement proportion: 0.440410 (473/1074).
- Fleiss' kappa: 0.186386.
- Historical kappa 0.1864 classification: **REPRODUCED WITH ROUNDING DIFFERENCE**.
- Pairwise Cohen kappas: H1/H2 0.163797; H1/H3 0.144623; H2/H3 0.267066.
- Gwet AC1: 0.515971. AC1 is supplementary and does not replace or soften the low Fleiss result.
- Unanimous items: 473 (44.040968%).
- Two-of-three majority items: 601 (55.959032%).

Alignment uses `(normalized source model, row_ref)` and independently requires identical TestCaseID, title, description, and objective signatures across all three exports. Row order is not used as the identity. The public JSON exports do not contain ScenarioID, confidence, or save timestamps, so those fields are reported as unavailable rather than inferred.

The majority label is a human consensus reference, not objective ground truth. The complete optimizer comparison is stratified into all, unanimous, and majority-only subsets. A false removal is a consensus-Unique item predicted Similar.

## Validation issues

- None.
