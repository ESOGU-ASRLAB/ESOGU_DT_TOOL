# Deterministic lexical baseline verification

The retained reference concatenates Title, Description, and Objective, applies lowercase word unigrams and bigrams with sublinear TF--IDF weighting, and uses cosine similarity in the order-dependent retained-representative pattern documented in `analyze_revision_public_archive.py`.

The reconstructed Human 1/Human 2/Human 3 alignment contains 1,074 items. The baseline prediction file contains 3,222 rows (1,074 items at each fixed threshold: 0.30, 0.50, and 0.70). Joining by source model and public `row_ref` produced zero consensus-label mismatches. Therefore, reconstructing the evaluator panels did not change the majority-vote reference labels used by the archived deterministic baseline, and regeneration is not numerically required.

At threshold 0.50, the overall Similar-class results are precision 0.570866, recall 0.434132, F1 0.493197, balanced accuracy 0.643417, and 109 false removals. The threshold is reported as a fixed analysis point, not as a prospectively selected or deployment-optimal threshold.

SHA-256 hashes of the preserved files:

- `analyze_revision_public_archive.py`: `15B7AA42CCC500FB82714B1AF0E42174DDE0B5CA32CDB416145CAA40501F35A5`
- `tfidf_baseline_metrics.csv`: `C6408D1D103AFFDF91F3ACBD2735E76BEBD25AF90A1640A9B4356D5537D1C845`
- `tfidf_baseline_predictions.csv`: `3F37F50FBA7710DBE25E440ABB7B044DC02D46BB52CFC7FBC9AA2734FB7D69D7`

This baseline is a deterministic lexical reference, not ground truth and not an automatically justified deployment rule.
