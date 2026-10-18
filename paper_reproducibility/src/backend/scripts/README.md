# Backend utility scripts

This directory contains operational utilities that are not imported by the
FastAPI application at runtime.

- `diagnostics/`: read-only inspection and validation helpers
- `maintenance/`: data repair, initialization, cleanup, and deletion tools
- `migrations/`: one-off database migration and migration verification tools
- `experiments/`: manual debugging and investigation helpers

Run these tools from the `backend` directory as modules so existing imports
such as `core.database` continue to resolve correctly:

```powershell
cd backend
python -m scripts.diagnostics.check_routes
```

Maintenance tools can modify or delete data. Review their arguments and source
before running them against a non-development database.
