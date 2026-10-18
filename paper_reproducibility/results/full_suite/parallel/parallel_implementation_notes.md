# Controlled Local Parallel implementation

The historical application `parallel` route is provider-specific and invokes Gemini Batch API. The new adapter does not reuse that transport and is not claimed to be identical to `GeminiBatchAPI_Adaptive`.

For each fixed 64-case suite, the adapter deterministically generates all 2,016 unordered pairs in suite order. Every pair is assigned a stable pair ID. The same semantic criteria used by the application's pairwise prompt are applied to each pair. To use local llama.cpp efficiently, at most eight explicit pair requests are wrapped in one JSON call subject to a 12,000-character budget; up to four local calls run concurrently. A strict dynamic JSON Schema restricts each response to the requested pair IDs and Boolean decisions, with a 256-token output budget. No input text is truncated, and no pair is sampled or omitted.

Responses are validated against the requested pair IDs. Missing or malformed decisions are retried and preserved in the raw response log. A run succeeds only when all 2,016 pair decisions exist.

Similar edges are aggregated with deterministic union-find connected components. The lowest original suite index becomes the retained representative. Because semantic similarity is not necessarily transitive, false direct edges found inside a final component are counted as transitivity conflicts and reported. Each unordered pair is evaluated only once, so directional conflicts cannot occur.
