# TODO — DRF conversion & production hardening

## Plan (approved)

### Information gathered
- DRF already exists in `library_app/views.py` via ViewSet-style endpoints, wired in `library_app/urls.py` under `/api/`.
- HTML endpoints still exist in `library_app/views_web.py` and are wired at root paths in `library_app/urls.py`.
- `Library/settings.py` is development-leaning: `DEBUG=True`, hardcoded `SECRET_KEY`, minimal REST_FRAMEWORK config.
- Seed command `library_app/management/commands/seed_books.py` exists and is idempotent.
- `library_app/views.py` has several production-quality issues: inline serializer code for books, weak error handling, membership selection inefficiencies, and inconsistent response shapes.
- `library_app/views_web.py` contains correctness bugs (notably `_has_active_membership` is unused and has an invalid filter; Django views duplicate membership checks and can be cleaned).
- No tests exist (`library_app/tests.py` is empty).

### Plan (code changes)
1) DRF hardening and correctness
   - Replace inline book serialization in `BookViewSet.list` with `BookSerializer` including `available_copies` via a serializer field.
   - Implement consistent serializer usage for all endpoints (remove ad-hoc dict building).
   - Ensure membership checks are done via a reusable helper/permission class (optimize query; use `.select_related()` where helpful).
   - Replace manual error responses with DRF exceptions (`ValidationError`, `PermissionDenied`, etc.).
   - Fix status codes and response bodies for consistency.

2) URL / API structure improvements
   - Ensure DRF endpoints use consistent trailing slashes (Django defaults) and are standard REST-ish.
   - Consider router usage (optional) but keep working endpoints stable.

3) Settings for production readiness
   - Add secure defaults: `DEBUG=False` (optionally via env), proper `SECRET_KEY` via env.
   - Configure `ALLOWED_HOSTS` via env.
   - Add `REST_FRAMEWORK` improvements: pagination, exception handler defaults, throttling (lightweight), JWT auth kept.
   - Add security-related headers middleware if missing (via Django built-in where possible).

4) Web views refactor (keep functional)
   - Remove dead/incorrect helper `_has_active_membership` or fix it.
   - Factor membership validity check into a shared helper.
   - Use Django ORM efficiently (`select_related`, avoid per-request loops).

5) Tests
   - Add meaningful DRF test coverage:
     - membership create & validity
     - borrow create when no copies (400)
     - borrow create when no active membership (403)
     - return borrow flow + fine calculation

6) Quality / style
   - Type hints, remove unused imports, improve naming.
   - Ensure migrations are untouched (models already include `BookSection`, but check relationships).

### Dependent files to edit
- `library_app/views.py`
- `library_app/serializers.py`
- `library_app/urls.py`
- `library_app/views_web.py`
- `Library/settings.py`
- `library_app/tests.py`
- (possibly) `library_app/models.py` if fine typing or relations need correction

### Followup steps
- Run migrations and seed command.
- Execute Django system checks and run test suite.


