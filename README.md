# Pages App

`pages` provides shared templates, partials, and standalone views (help, resources, landing page)
that wrap the rest of the portals.

## Responsibilities

- Base layouts in `pages/templates/base/` (dashboard shell, auth pages, resources, etc.).
- Navbar partial (`pages/templates/partials/nav.html`) that renders the dynamic menu and quick
  favorites driven by `core.context_processors`.
- Simple CBVs (help/resources/pages/views.py) and endpoint utilities like `save_layout`.
- Static assets (SCSS/JS/images) consumed by every portal.

## Highlights

- The dashboard template hosts the widget grid and drag/drop controls for hiding/restoring cards.
- Navbar supports in-page pinning/unpinning of quick-access links thanks to the context processor
  data and AJAX endpoint.
- `pages/views.save_layout` persists dashboard layout/visibility state for any portal key.

## Tests

This app is primarily templates, but you can smoke test the views with:

```bash
python manage.py test pages
```

Add tests whenever you introduce new view logic or context data.
