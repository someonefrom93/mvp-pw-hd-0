# Tasks: Change 003 — Public UI (UI Shell)

> First sub-change of the umbrella `change-002-features`. Lands FIRST in the stacked-to-main chain. **Scope: UI shell only — no checkout, no order POST, no WhatsApp redirect.** Those land in `change-004-cart-whatsapp`.

## Task Dependency Graph

```
T1 (components.css) → T2 (partials) → T4 (home.html) → T9 (smoke)
T3 (cart.js)         → T2
T5 (SVG assets)      → T4
T6 (base.html link)  → T4
T7 (pyproject.toml)  → T8 (routes/public.py GET /) → T9
T8 (routes/public.py GET /) → T9
```

T1 (CSS) and T3 (JS) are independent. T2 depends on T1 and T3 (partials use CSS classes + WeroCart object). T4 depends on T1, T2, T5, T6 (home page composes everything). T8 is the route handler. T9 verifies everything end-to-end.

## T1: Component CSS
**Files**: `app/static/css/components.css` (new)
**Depends on**: none
**Lines estimate**: ~250
**Status**: ✅ COMPLETE
**Acceptance**:
- [x] File contains all component classes per `component-css` spec: `.btn`, `.btn-magenta`, `.btn-amarillo`, `.btn-outline`, `.btn-block`, `.btn:hover`, `.btn:active`, `.btn:disabled`, `.card`, `.card-producto`, `.card-producto:hover`, `.card--soldout`, `.hero-banner`, `.hero-banner__starburst`, `.location-block`, `.menu-grid`, `.site-footer`, `.form-input`, `.form-label`, `.form-error`, `.modal`, `.modal__backdrop`, `.modal__content`, `.modal--cart`, `.cart-fab`, `.cart-fab__count`, `.container`, `.visually-hidden`
- [x] Uses CSS custom properties from `tokens.css` (no hardcoded colors)
- [x] Responsive breakpoints at 640px and 960px
- [x] BEM-lite naming convention
- [x] `curl http://127.0.0.1:8000/static/css/components.css` returns 200

## T2: Template Partials
**Files**: `app/templates/public/partials/product_card.html` (new), `app/templates/public/partials/cart_summary.html` (new — items list only, NO customer form)
**Depends on**: T1 (CSS classes used)
**Lines estimate**: ~45
**Status**: ✅ COMPLETE
**Acceptance**:
- [x] `product_card.html` accepts a `Producto` dataclass and renders: image (placeholder SVG), name (uppercase, display font), description, price (yellow starburst badge), "Añadir al carrito" button with `data-sku`, quantity input
- [x] For `disponible=0`: shows "Agotado" badge, no button, `card--soldout` class
- [x] `cart_summary.html` renders the cart modal items list with quantity controls and subtotals (NO customer form fields — those are added in `change-004-cart-whatsapp`)
- [x] Both render without Jinja2 errors

## T3: WeroCart JS Object
**Files**: `app/static/js/cart.js` (new)
**Depends on**: none (vanilla JS, no deps)
**Lines estimate**: ~80
**Status**: ✅ COMPLETE
**Acceptance**:
- [x] `WeroCart` is a global object with methods: `items()`, `add(sku, qty)`, `remove(sku)`, `update(sku, qty)`, `clear()`, `count()`, `totalQty()`, `isEmpty()`
- [x] Backed by `localStorage` key `wero_cart_v1`
- [x] Emits `cart:change` CustomEvent on the document on every mutation
- [x] On `DOMContentLoaded`: hooks all `[data-sku]` buttons to call `WeroCart.add` and updates the cart-fab count badge
- [x] Syntax check passes

## T4: Home Page Template
**Files**: `app/templates/public/home.html` (new)
**Depends on**: T1, T2, T5, T6
**Lines estimate**: ~80
**Status**: ✅ COMPLETE
**Acceptance**:
- [x] Extends `base.html`
- [x] Contains 5 sections in order: hero banner, location/hours, menu grid, cart trigger, footer
- [x] Hero banner shows `config.banner_promocion` text
- [x] Menu grid iterates over `productos` and renders `product_card.html` for each
- [x] Cart-fab (`.cart-fab`) with `data-cart-fab` attribute and a count badge
- [x] Includes `cart.js` at the end of body
- [x] Footer with Facebook + DiDi Food social links from `config.facebook_url` and `config.didi_food_url`
- [x] Renders without Jinja2 errors

## T5: SVG Assets
**Files**: `app/static/img/wero-mascot.svg` (new), `app/static/img/placeholder-JO-001.svg` through `placeholder-HB-003.svg` (6 new files)
**Depends on**: none
**Lines estimate**: ~150 (mostly hand-crafted SVG)
**Status**: ✅ COMPLETE
**Acceptance**:
- [x] `wero-mascot.svg`: yellow body, magenta mohawk, black sunglasses, spiked collar, simple cartoon dog face
- [x] Each `placeholder-{sku}.svg`: 400x400 viewBox, magenta-to-yellow gradient background, centered product name, "PLACEHOLDER" label, small dog emoji in corner
- [x] All 7 files are served as `image/svg+xml` with HTTP 200
- [x] `curl http://127.0.0.1:8000/static/img/wero-mascot.svg` returns 200

## T6: Base Template Link Update
**Files**: `app/templates/base.html` (modified — 1 line added)
**Depends on**: T1
**Lines estimate**: 1
**Status**: ✅ COMPLETE
**Acceptance**:
- [x] `<link rel="stylesheet" href="/static/css/components.css">` is added AFTER the `main.css` link in `<head>`
- [x] Load order is: tokens.css → main.css → components.css
- [x] The change is a single-line addition

## T7: pyproject.toml Dependency
**Files**: `pyproject.toml` (modified)
**Depends on**: none
**Lines estimate**: 1
**Status**: ✅ COMPLETE
**Acceptance**:
- [x] `itsdangerous>=2.1` is added to runtime dependencies (for forward compat with `change-004-cart-whatsapp` and `change-005-admin-ui` cookie sessions)
- [x] `pip install -e ".[dev]"` succeeds

## T8: Home Route Handler
**Files**: `app/routes/public.py` (modified — add `home` function)
**Depends on**: T5 (for SVG paths), T2 (for partials)
**Lines estimate**: ~25
**Status**: ✅ COMPLETE
**Acceptance**:
- [x] `GET /` returns HTTP 200 with `text/html; charset=utf-8`
- [x] Loads `productos` from DB (all, not filtered by `disponible` — the template handles sold-out display)
- [x] Loads `configuracion` rows as a dict `{llave: valor}`
- [x] Returns `templates.TemplateResponse(request, "public/home.html", {"productos": productos, "config": config})`
- [x] `curl -i http://127.0.0.1:8000/` returns 200 and the HTML contains "Jochos El Perro Wero"

## T9: Smoke Test
**Files**: (no new files; manual verification)
**Depends on**: T1, T2, T3, T4, T5, T6, T7, T8
**Lines estimate**: 0
**Status**: ✅ COMPLETE
**Acceptance**:
- [x] `uvicorn app.main:app --reload` starts clean
- [x] `curl -i http://127.0.0.1:8000/` returns 200 with the home page
- [x] `curl -i http://127.0.0.1:8000/static/css/components.css` returns 200
- [x] `curl -i http://127.0.0.1:8000/static/js/cart.js` returns 200
- [x] `curl -i http://127.0.0.1:8000/static/img/wero-mascot.svg` returns 200 with `Content-Type: image/svg+xml`
- [x] All 6 placeholder SVGs return 200
- [x] The HTML contains the banner text from `configuracion.banner_promocion`
- [x] The HTML contains 6 product cards (one per SKU)
- [x] A sold-out product (set `disponible=0` manually) renders with "Agotado" badge
- [x] The page is responsive at 320px, 414px, 1024px viewports
- [x] `mypy app/` is clean
- [x] `ruff check app/` is clean
- [x] `POST /ordenes` returns 404 or 405 (not yet implemented — that's change-004)

> T1–T9 completed: 2026-06-07 by sdd-apply

## Total Estimate

| Task | LOC |
|------|-----|
| T1 (components.css) | 250 |
| T2 (partials) | 45 |
| T3 (cart.js) | 80 |
| T4 (home.html) | 80 |
| T5 (SVG assets) | 150 |
| T6 (base.html link) | 1 |
| T7 (pyproject.toml) | 1 |
| T8 (GET /) | 25 |
| T9 (smoke) | 0 |
| **TOTAL** | **~632** |

> Note: total includes ~150 LOC of SVG markup (counted as code for budget purposes). The functional code is closer to 480 LOC. If forecast trends > 600, consider simplifying placeholder SVGs (e.g., make them smaller, single-color, no emoji).

## Review Workload Forecast

| Metric | Value |
|--------|-------|
| Estimated changed lines | **~632** (incl. SVGs) or **~480** (functional only) |
| Budget | 400 |
| Over budget? | **Yes — by ~58%** |
| Risk | Low — no business logic, no auth, no DB schema change |
| Recommendation | **Single PR with `size:exception`** OR **split T1 (components.css) + T5 (SVGs) into a separate change** |

**size:exception justification**:
> Public UI shell change touches: components.css (250 LOC, the entire CSS layer for the Mexican urban identity), 1 home template (80 LOC), 2 partials (45 LOC), 1 JS module (80 LOC), 1 home route (25 LOC), 7 SVG assets (~150 LOC of static markup). The bulk is the CSS layer (50% of total) and SVGs (25%). All structural, no business logic, no DB changes, no auth. The CSS layer is a single coherent design system — splitting it would fragment the visual identity across PRs.

**Alternative split** (if user rejects exception):
- `change-003a-style-foundation` — components.css + SVGs + base.html link + pyproject.toml (~400 LOC, no JS, no templates)
- `change-003b-public-ui-page` — home.html + partials + cart.js + GET / route (~230 LOC)

## Commit Strategy (work-unit commits for this change)

- Commit 1: T6 (base.html link) + T7 (pyproject.toml) — small prep commit
- Commit 2: T1 (components.css) — the CSS layer
- Commit 3: T5 (SVG assets) — mascot + 6 placeholders
- Commit 4: T3 (cart.js) — WeroCart object
- Commit 5: T2 (partials) — product_card + cart_summary (no form)
- Commit 6: T4 (home.html) — the page that composes everything
- Commit 7: T8 (GET /) — the route handler
- Commit 8: T9 (smoke test verification only) — updates tasks.md to mark all done

Each commit is independently revertable. The app boots after commits 1+2 (CSS only). The home page renders after commits 1-7.

## PR Position in the Stacked-to-Main Chain

```
PR #1: change-001-foundation        (merged)
PR #2: change-002-db-seed           (in archive)
PR #3: change-003-public-ui         (THIS CHANGE — lands first of the UI)
PR #4: change-004-cart-whatsapp     (lands after this)
PR #5: change-005-admin-ui          (planned, lands last)
```

## Cross-references

- **Spec**: `specs/{public-ui,component-css,cart-flow,whatsapp-integration}/spec.md` (end state of public UI; this change implements the UI shell subset)
- **Design**: `design.md` (full end-state design; this change implements the UI shell subset)
- **Proposal**: `proposal.md`
- **Next change**: `../change-004-cart-whatsapp/` (lands after this; adds the transactional layer)
