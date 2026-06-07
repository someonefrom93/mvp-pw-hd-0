# Capability: base-templates

## Purpose
Jinja2 base templates for the public client UI and the admin UI. These establish the HTML5 shell, mobile viewport, and the inheritance chain that all page templates (added in change-002) will extend.

## ADDED Requirements

### Requirement: base.html public
The system MUST provide `app/templates/base.html` containing:
- HTML5 doctype and `lang="es-MX"` on the `<html>` element
- `<head>` with:
  - `<meta charset="UTF-8">`
  - `<meta name="viewport" content="width=device-width, initial-scale=1.0">`
  - `<title>{% block title %}Jochos El Perro Wero{% endblock %}</title>`
  - Google Fonts preconnect + stylesheet `<link>` (see design-tokens spec)
  - `<link rel="stylesheet" href="/static/css/tokens.css">`
  - `<link rel="stylesheet" href="/static/css/main.css">`
  - `{% block extra_head %}{% endblock %}` for page-specific head content
- `<body>` with:
  - `{% block content %}{% endblock %}`
  - A minimal `<footer>` placeholder with `{% block footer %}{% endblock %}`
  - `{% block extra_scripts %}{% endblock %}` before `</body>`

### Requirement: base_admin.html
The system MUST provide `app/templates/base_admin.html` that:
- Extends `base.html` via `{% extends "base.html" %}`
- Sets a default title block of "Admin · Jochos El Perro Wero"
- Includes a placeholder top bar element (e.g. `<header class="admin-topbar">`) inside the content block
- Provides `{% block admin_content %}{% endblock %}` for admin page templates
- Provides `{% block admin_scripts %}{% endblock %}` for admin-specific JS

### Requirement: viewport meta in both templates
Both `base.html` AND `base_admin.html` MUST result in a rendered page that includes the `<meta name="viewport" content="width=device-width, initial-scale=1.0">` tag (inherited through `extends` for the admin template).

### Requirement: jinja2 validity
Both templates MUST be valid Jinja2 syntax (no parse errors) and MUST render successfully when invoked with an empty context `{}`.

### Requirement: title block override
The admin template MUST override the title block to a non-default value. Page templates in change-002 will be able to override it again with their own titles.

#### Scenario: base.html renders standalone
- **GIVEN** a temporary FastAPI route returns `templates.TemplateResponse(request, "base.html", {})`
- **WHEN** that route is called
- **THEN** the response is HTTP 200, the HTML contains `<!DOCTYPE html>`, the `<head>` includes the viewport meta and the Google Fonts link, and the body contains the default content block

#### Scenario: base_admin.html extends base
- **GIVEN** `base_admin.html` is rendered with empty context
- **WHEN** the HTML output is inspected
- **THEN** it contains the base.html head content (viewport meta, Google Fonts, both CSS links) AND a `{% block admin_content %}` placeholder section AND a topbar element

#### Scenario: viewport meta present
- **GIVEN** either `base.html` or `base_admin.html` is rendered
- **WHEN** the HTML output is searched for `viewport`
- **THEN** a `<meta name="viewport" ...>` tag is present in the output

#### Scenario: title default differs
- **GIVEN** both templates are rendered with empty context
- **WHEN** the `<title>` element is read from each
- **THEN** `base.html` shows "Jochos El Perro Wero" and `base_admin.html` shows "Admin · Jochos El Perro Wero"

#### Scenario: extra_head and extra_scripts blocks present
- **GIVEN** `base.html` is rendered
- **WHEN** the HTML output is searched for `{% block`
- **THEN** at least these blocks are present: `title`, `extra_head`, `content`, `footer`, `extra_scripts`

## MODIFIED Requirements
None — greenfield change.

## REMOVED Requirements
None.
