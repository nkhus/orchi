---
kind: reference
area: feature
relations:
  addresses: [req-user]
  realizes: [intent/architecture/README.md]
---
# Selected values epic design

Update src/left.py and src/right.py independently to expose VALUE as integers one and two. Preserve plain module interfaces and avoid import effects. No shared mutable state or writes cross task boundaries. Registered left/right checks inspect the resulting constants. The two edits can execute in parallel.
