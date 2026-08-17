---
type: "query"
date: "2026-08-14T16:13:10.161381+00:00"
question: "Why does _post connect test_auth.py to auth_remote_ds.dart and predicciones.py?"
contributor: "graphify"
outcome: "corrected"
correction: "Treat these former decorator edges as a cross-language name collision, not a runtime dependency."
source_nodes: ["_postTokens", "guardar_mercados", "apuesta_combinada"]
---

# Q: Why does _post connect test_auth.py to auth_remote_ds.dart and predicciones.py?

## Answer

Corrected: Python router.post decorators were falsely resolved to the Dart helper _post by global symbol-name matching. Renamed the private Dart helper to _postTokens; there is no backend-to-Flutter call or dependency.

## Outcome

- Signal: corrected
- Correction: Treat these former decorator edges as a cross-language name collision, not a runtime dependency.

## Source Nodes

- _postTokens
- guardar_mercados
- apuesta_combinada