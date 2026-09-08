---
kind: architecture
area: feature
artifacts: [src/left.py, src/right.py, src/api.py]
relations:
  addresses: [req-user]
---
# Target architecture

Two independent value modules expose immutable integer constants. A public API module combines them. Dependencies point from API to values; no module changes another module's state. There are no network integrations, persistence or deployment services. Verification reads the modules through the operator-registered checks.

The values epic establishes the internal data contract. The API epic realizes the public boundary after the actual values have been verified. Detailed implementation choices for the API are deferred until that epic is selected.
