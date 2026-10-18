# Scenario collision report

Mapped cases: 128.
Distinct raw ScenarioID values: 8.
Distinct artifact-scoped identities: 16.
Raw IDs that map to more than one artifact-scoped identity: 8.

Combined paired runs evaluated: 30.
Combined paired runs where raw-ID SCP differs from artifact-scoped SCP: 9.
Observed combined SCP difference range (scoped minus raw): -0.125000 to 0.000000.

## Collisions

- `TS_001` -> `requirements::Functional_and_NonFunctional_Requirements.txt::TS_001`, `source_code::ProductDetection.cpp::TS_001`
- `TS_002` -> `requirements::Functional_and_NonFunctional_Requirements.txt::TS_002`, `source_code::ProductDetection.cpp::TS_002`
- `TS_003` -> `requirements::Functional_and_NonFunctional_Requirements.txt::TS_003`, `source_code::ProductDetection.cpp::TS_003`
- `TS_004` -> `requirements::Functional_and_NonFunctional_Requirements.txt::TS_004`, `source_code::ProductDetection.cpp::TS_004`
- `TS_005` -> `requirements::Functional_and_NonFunctional_Requirements.txt::TS_005`, `source_code::ProductDetection.cpp::TS_005`
- `TS_006` -> `requirements::Functional_and_NonFunctional_Requirements.txt::TS_006`, `source_code::ProductDetection.cpp::TS_006`
- `TS_007` -> `requirements::Functional_and_NonFunctional_Requirements.txt::TS_007`, `source_code::ProductDetection.cpp::TS_007`
- `TS_008` -> `requirements::Functional_and_NonFunctional_Requirements.txt::TS_008`, `source_code::ProductDetection.cpp::TS_008`

The primary new-study metric is artifact-scoped SCP. Raw-ID SCP is retained only as a legacy comparison.
