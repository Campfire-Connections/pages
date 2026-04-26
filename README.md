# Pages App

`pages` provides shared templates, partials, static assets, and standalone views
(help, resources, landing page) that wrap the rest of the portals.

## Responsibilities

- Base layouts in `pages/templates/base/`:
  - `layout.html` provides the app shell, rail navigation, page title, and `page_actions`.
  - `list.html` provides consistent table/list pages with a top-right create action.
  - `form.html` provides theme-aware form cards, validation output, and cancel/save actions.
  - `show.html` provides the shared object detail shell.
- Navbar partial (`pages/templates/partials/nav.html`) that renders the dynamic menu and quick
  favorites driven by `core.context_processors`.
- Simple CBVs (help/resources/pages/views.py) and endpoint utilities like `save_layout`.
- Static assets in `pages/static/css/` consumed by every portal.

## Highlights

- The dashboard template hosts the widget grid and drag/drop controls for hiding/restoring cards.
- Navbar supports in-page pinning/unpinning of quick-access links thanks to the context processor
  data and AJAX endpoint.
- `pages/views.save_layout` persists dashboard layout/visibility state for any portal key.
- Theme tokens live in `pages/static/css/layout.css`; downstream CSS should use variables such as
  `--card`, `--panel`, `--text`, `--muted`, `--border`, and `--accent` rather than hardcoded
  light-mode colors.

## Template Conventions

- Use `base/list.html` for table/list pages and set `title_text`, `new_url`, `new_label`, and
  `table_caption` blocks where needed.
- Use `base/form.html` for CRUD forms and override `form_title`, `form_heading`, `submit_label`,
  and cancel URL blocks for app-specific labels.
- Use the `page_actions` block for primary page actions so actions remain consistent in desktop,
  mobile, light, and dark themes.

## Tests

This app is primarily templates, but you can smoke test the views with:

```bash
python manage.py test pages
```

Add tests whenever you introduce new view logic or context data.
