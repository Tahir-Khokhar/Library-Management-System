# TODO - Library Membership & Borrowing API + Frontend + Seed Books

## Backend (DRF) hardening
- [ ] Confirm project runs: apply migrations (if not already)
- [ ] Add/extend models to support library sections/categories (recommended: `BookSection` + relation to `Book`)
- [ ] Update serializers minimally (API should remain stable)
- [ ] Register new models in admin

## Data seeding (Books since 1857)
- [ ] Add management command to seed sample library data grouped by sections
- [ ] Seed kid section: story books, comic, manga
- [ ] Seed adults section: newspaper collections (whole-year)
- [ ] Seed additional Pakistan-style library categories available in the library
- [ ] Ensure seeding is idempotent (safe to run multiple times)

## Frontend (Django templates)
- [x] Add templates directory setup in `settings.py`
- [x] Add HTML pages:
  - [x] Home / landing
  - [x] Sections list
  - [x] Books by section
  - [x] Membership status / purchase
  - [x] My transactions
- [x] Add HTML routes in `library_app/urls.py`
- [x] Implement HTML views using Django ORM (avoid JWT in browser for stability)


## Testing / Validation
- [ ] `python manage.py makemigrations`
- [ ] `python manage.py migrate`
- [ ] run seeding command
- [ ] runserver and manually test HTML pages
- [ ] verify DRF endpoints still work

