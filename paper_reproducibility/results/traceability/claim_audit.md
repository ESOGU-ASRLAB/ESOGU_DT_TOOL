# Manuscript claim audit

The final source was searched case-insensitively for `prove`, `optimal`, `superior`, `guarantee`, `effective`, `efficiency`, `coverage`, `correctness`, `reliable`, `robust`, and `production-ready`. The audit used word/stem-aware searches and reviewed every matching source line in context. No unsupported positive claim remains.

## Classification of every occurrence

| Term | Source line(s) | Classification | Disposition |
|---|---:|---|---|
| prove/provenance stem | 327, 490, 992, 1321, 1326 | Limitation or lexical false positive | Lines 327 and 490 explicitly say evidence does **not prove** backend or historical artifact identity. Lines 992, 1321, and 1326 contain `provenance`, not the verb “prove.” Retained. |
| optimal | none | No occurrence | No action required. |
| superior/superiority | 190, 820, 1313 | Explicitly negated | The manuscript rejects state-of-the-art, causal, broad, or universal superiority. Retained. |
| guarantee | 1313 | Explicitly negated | Fixed seeds are stated not to guarantee deterministic sampling. Retained. |
| effective/effectiveness | 190, 674, 681, 943, 948, 1135, 1319, 1324 | Explicit scope limitation | Every occurrence denies general, behavioral, optimizer, fault-detection, or industrial-effectiveness inference. Retained. |
| efficiency | 188, 394, 1050 | External citation, metric label, or explicit qualification | Line 188 attributes efficiency to cited external work and disclaims direct evidence. Line 394 names representation-efficiency metrics. Line 1050 states SRG does not establish behavioral efficiency. Retained. |
| coverage | 109, 184, 496, 943, 947, 948, 960, 967, 1319, 1321, 1324, 1332 | Metric name, related-work description, limitation, or future work | “Scenario Coverage Preservation” is defined strictly as identifier representation. Executed code/branch coverage is repeatedly disclaimed. Line 496 now distinguishes canonical new-study input from unverifiable historical identity. Retained. |
| correctness | 184, 231, 240, 474, 554, 711, 924, 936, 1324 | Module description, arithmetic invariant, or explicit qualification | Lines 231/240 describe unevaluated module intentions and limitations; line 554 concerns arithmetic identity only; all other occurrences deny semantic-correctness inference. Retained. |
| reliable | none | No occurrence | No action required. |
| robust/robustness | 955, 1180, 1183, 1184 | Negated inference or named sensitivity table/label | Line 955 rejects repeat-run robustness inference; lines 1180/1183/1184 identify the consensus-stratified robustness table, which is explicitly not a single-model accuracy estimate. Retained. |
| production-ready | none | No occurrence | No action required. |

## Strong-claim controls

- No claim states that semantic filtering proves executability, correctness, behavioral/code/branch coverage, mutation adequacy, or fault detection.
- No mode or model is called optimal, universally superior, or production-ready.
- Runtime values are workstation traces, not labor savings or universal efficiency rankings.
- Repeatability is explicitly separated from correctness.
- Human majority consensus is called a reference, never objective ground truth.

**Result: PASS — all trigger-word occurrences are either appropriately bounded, explicitly negated, descriptive metric names, or related-work statements.**
