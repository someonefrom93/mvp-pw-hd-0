# Capability: design-tokens

## Purpose
CSS custom properties and font loading that establish the Royal Blue / Magenta Pink / Yellow Mexican urban identity. All visual styling in change-002 will reference these tokens.

## ADDED Requirements

### Requirement: color tokens
The system MUST define these CSS custom properties on `:root` in `app/static/css/tokens.css`:
- `--color-azul-rey: #1E3A8A`
- `--color-azul-rey-dark: #0F1E47`
- `--color-magenta: #EC4899`
- `--color-magenta-dark: #BE185D`
- `--color-amarillo: #FACC15`
- `--color-amarillo-dark: #CA8A04`
- `--color-white: #FFFFFF`
- `--color-text: #FFFFFF` (white on blue background)
- `--color-text-dark: #0F1E47` (dark text for yellow backgrounds)

### Requirement: font tokens
The system MUST define these font custom properties in `tokens.css`:
- `--font-display: 'Bebas Neue', 'Anton', Impact, sans-serif`
- `--font-body: 'Inter', system-ui, -apple-system, sans-serif`

### Requirement: spacing scale
The system MUST define a spacing scale on `:root` in `tokens.css`:
- `--space-1: 4px`
- `--space-2: 8px`
- `--space-3: 12px`
- `--space-4: 16px`
- `--space-5: 24px`
- `--space-6: 32px`
- `--space-7: 48px`
- `--space-8: 64px`

### Requirement: radius scale
The system MUST define a border-radius scale in `tokens.css`:
- `--radius-sm: 6px`
- `--radius-md: 12px`
- `--radius-lg: 24px`
- `--radius-pill: 999px`

### Requirement: shadow tokens
The system MUST define at least these shadow tokens in `tokens.css`:
- `--shadow-magenta: 0 8px 24px rgba(236, 72, 153, 0.4)`
- `--shadow-amarillo: 0 8px 24px rgba(250, 204, 21, 0.4)`
- `--shadow-azul: 0 8px 24px rgba(30, 58, 138, 0.4)`

### Requirement: typography in main.css
The system MUST set in `app/static/css/main.css`:
- `body` uses `font-family: var(--font-body); color: var(--color-text); background: var(--color-azul-rey);`
- `h1, h2, h3, h4, h5, h6` use `font-family: var(--font-display); text-transform: uppercase; letter-spacing: 0.02em;`

### Requirement: css reset
The system MUST include a minimal CSS reset at the top of `main.css`:
- `*, *::before, *::after { box-sizing: border-box; }`
- `body, h1, h2, h3, h4, h5, h6, p, ul, ol { margin: 0; padding: 0; }`
- `ul, ol { list-style: none; }`
- `img { display: block; max-width: 100%; }`
- `a { color: inherit; text-decoration: none; }`

### Requirement: google fonts in base template
The system MUST include in the `<head>` of `app/templates/base.html` a `<link rel="preconnect">` to `fonts.googleapis.com` and a `<link rel="stylesheet">` to `https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Anton&family=Inter:wght@400;600;700&display=swap`.

#### Scenario: tokens file contains required properties
- **GIVEN** `app/static/css/tokens.css` exists
- **WHEN** the file content is read
- **THEN** it contains all 7 named colors, 2 font tokens, the 8 spacing variables, the 4 radius variables, and at least 3 shadow tokens

#### Scenario: main.css applies display font to headings
- **GIVEN** `app/static/css/main.css` is loaded by a page
- **WHEN** an `h1` element is rendered on that page
- **THEN** the computed `font-family` resolves to a value matching `--font-display` (Bebas Neue or fallback)

#### Scenario: google fonts link present
- **GIVEN** `base.html` is rendered
- **WHEN** the HTML output is inspected
- **THEN** a `<link rel="stylesheet">` tag with `fonts.googleapis.com` in the href is present in the `<head>`, and the URL contains `Bebas+Neue`, `Anton`, and `Inter`

#### Scenario: reset applied to all elements
- **GIVEN** `main.css` is loaded
- **WHEN** a browser parses it
- **THEN** every element has `box-sizing: border-box` and zero default margin/padding

## MODIFIED Requirements
None — greenfield change.

## REMOVED Requirements
None.
