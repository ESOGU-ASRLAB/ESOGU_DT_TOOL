# Local Bulk partitioning and reconciliation

Each 64-case suite is ordered exactly as stored in the fixed suite artifact and partitioned into thirty-two contiguous two-case batches. Each batch is sent as a complete JSON classification request. Cases, descriptions, and objectives are not truncated. Initial eight-case and four-case validation attempts were rejected because the model repeatedly omitted input indices; those failed attempts are preserved, and no result from them was persisted as a completed run. The two-case partition was selected before the successful study runs because it was the smallest group-level unit that passed complete-index validation without imputing a missing classification.

The resulting duplicate groups are validated and converted into pair-level evidence for every unordered pair inside each batch. The first case in original suite order is retained as the representative of a duplicate component.

There is no cross-batch reconciliation in this mode. Consequently, a case cannot be removed on the basis of a case in another batch, and global duplicates that cross a partition boundary may remain. The mode is therefore described as deterministic partitioned local Bulk, not as a single call over the whole suite and not as globally exhaustive deduplication. This limitation is retained in the Results, Discussion, and threats to validity.
