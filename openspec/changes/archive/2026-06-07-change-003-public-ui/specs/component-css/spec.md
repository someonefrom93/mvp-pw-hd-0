# Capability: component-css

## Purpose
Reusable CSS components that layer on top of `tokens.css` + `main.css` to give the app its Mexican urban visual identity: comic-book style with Royal Blue background, Magenta CTAs, Yellow starbursts for prices, and a "Wero" dog mascot. All components are pure CSS (no JS), responsive (mobile-first), and follow BEM-lite naming.

## Requirements

### Requirement: components.css file
The system MUST provide `app/static/css/components.css` loaded AFTER `main.css` in `base.html` (so tokens → main → components).

#### Scenario: load order is correct
- **GIVEN** `base.html` is rendered
- **WHEN** the HTML head is inspected
- **THEN** the `<link rel="stylesheet">` tags appear in this order: `tokens.css`, `main.css`, `components.css`

#### Scenario: components.css is served by FastAPI
- **GIVEN** the server is running
- **WHEN** `GET /static/css/components.css` is requested
- **THEN** the response is HTTP 200 with `Content-Type: text/css` and the file body

### Requirement: button components
The system MUST define the following button classes in `components.css`:
- `.btn` — base button (`.btn { display: inline-flex; align-items: center; justify-content: center; padding: var(--space-3) var(--space-5); border: 0; border-radius: var(--radius-pill); font-family: var(--font-display); font-size: 1.1rem; text-transform: uppercase; letter-spacing: 0.05em; cursor: pointer; transition: transform 0.15s ease, box-shadow 0.15s ease; }`)
- `.btn-magenta` — primary CTA (`.btn-magenta { background: var(--color-magenta); color: var(--color-white); box-shadow: var(--shadow-magenta); }`)
- `.btn-amarillo` — secondary CTA (`.btn-amarillo { background: var(--color-amarillo); color: var(--color-text-dark); box-shadow: var(--shadow-amarillo); }`)
- `.btn-outline` — outlined button (`.btn-outline { background: transparent; border: 2px solid var(--color-white); color: var(--color-white); }`)
- `.btn:hover` — scale up 1.05x with deeper shadow
- `.btn:active` — scale down 0.98x
- `.btn:disabled` — opacity 0.5, cursor not-allowed, no hover effect
- `.btn-block` — full width

#### Scenario: button hover effect
- **GIVEN** a `<button class="btn btn-magenta">Pedir</button>` is on the page
- **WHEN** the user hovers over it
- **THEN** the button scales up 1.05x and the magenta shadow deepens

#### Scenario: disabled button has no hover effect
- **GIVEN** a `<button class="btn btn-magenta" disabled>Agotado</button>` is on the page
- **WHEN** the user hovers over it
- **THEN** the button does NOT change scale or shadow, the cursor is `not-allowed`, and opacity is 0.5

### Requirement: card components
The system MUST define:
- `.card` — base card (white-ish background, rounded corners, padding, subtle shadow)
- `.card-producto` — product card (uses grid, has hover lift effect, `transition: transform 0.2s ease`)
- `.card-producto:hover` — translateY(-4px) with deeper shadow
- `.card--soldout` — modifier that desaturates the card (grayscale filter 80%) and dims it (opacity 0.7)

#### Scenario: product card hover lift
- **GIVEN** a `.card-producto` is in the menu grid
- **WHEN** the user hovers over the card
- **THEN** the card translates up 4px and the shadow deepens

#### Scenario: sold-out card is visually distinct
- **GIVEN** a product with `disponible=0` is rendered
- **WHEN** the page is displayed
- **THEN** the card has class `card--soldout`, the image is desaturated, and an "Agotado" badge is visible in the top-right corner

### Requirement: hero banner component
The system MUST define `.hero-banner` with:
- Royal Blue background (`var(--color-azul-rey)`)
- Bebas Neue display font
- A starburst element (`.hero-banner__starburst`) as a CSS-only shape using `clip-path: polygon(...)` for a 12-point star
- The starburst is Yellow (`var(--color-amarillo)`) and contains the banner text rotated -8deg
- The banner is full-width, vertically padded with `var(--space-7)` top and bottom
- A small "Wero" mascot SVG is positioned in the bottom-right corner

#### Scenario: hero banner renders
- **GIVEN** `configuracion.banner_promocion` is set
- **WHEN** the home page renders
- **THEN** the `.hero-banner` div appears at the top of the page with a yellow starburst containing the banner text rotated -8deg

#### Scenario: starburst is a 12-point star
- **GIVEN** the hero banner is rendered
- **WHEN** the `.hero-banner__starburst` element is inspected
- **THEN** it has `clip-path: polygon(...)` with 24 points (12 outer + 12 inner) creating a 12-point star shape

### Requirement: footer component
The system MUST define `.site-footer` with:
- Darker Royal Blue background (`var(--color-azul-rey-dark)`)
- 3 columns on desktop (schedule | contact | social) collapsing to 1 column on mobile
- Social icons: Facebook and DiDi Food as inline SVG links
- Each link uses `target="_blank"` and `rel="noopener noreferrer"`
- White text, Magenta hover state for links

#### Scenario: footer has 3 columns on desktop
- **GIVEN** the viewport is 1024px wide
- **WHEN** the footer is rendered
- **THEN** it shows 3 columns side by side

#### Scenario: footer collapses on mobile
- **GIVEN** the viewport is 320px wide
- **WHEN** the footer is rendered
- **THEN** the 3 columns stack vertically (1 column)

#### Scenario: social icons open in new tab
- **GIVEN** the footer has a Facebook link
- **WHEN** the link is rendered
- **THEN** the `<a>` tag has `target="_blank"` and `rel="noopener noreferrer"` for security

### Requirement: form components
The system MUST define:
- `.form-input` — full-width input with thick Magenta focus border, rounded corners
- `.form-label` — uppercase Bebas Neue label above each input
- `.form-error` — small red error message below an input
- `.form-row` — flex row that wraps on mobile

#### Scenario: input focus state
- **GIVEN** a `<input class="form-input">` is on the page
- **WHEN** the user focuses it
- **THEN** the input shows a 2px Magenta border (instead of the default) and a subtle Magenta glow

#### Scenario: error message styling
- **GIVEN** a form input has class `form-input` and there's a `<span class="form-error">` next to it
- **WHEN** the page is rendered
- **THEN** the error span is small, red, and positioned below the input

### Requirement: modal component (for cart)
The system MUST define `.modal` with:
- A backdrop (`.modal__backdrop`) covering the full viewport with semi-transparent dark overlay
- A content area (`.modal__content`) centered, with white background, rounded corners, max-width 600px, max-height 80vh with scroll
- Close button (`.modal__close`) in the top-right
- Slide-in-from-right animation on mobile, fade-in on desktop
- Cart modal specifically (`.modal--cart`) shows the items list and a "Confirmar pedido" CTA

#### Scenario: modal opens on cart click
- **GIVEN** the user clicks the cart-fab button
- **WHEN** the click event fires
- **THEN** a modal with class `modal modal--cart` appears centered on the page with a dark backdrop, and scrolling the body is disabled

#### Scenario: modal closes on backdrop click
- **GIVEN** the cart modal is open
- **WHEN** the user clicks the backdrop (outside the content area)
- **THEN** the modal closes (display: none or `hidden` attribute)

### Requirement: wero mascot SVG
The system MUST provide `app/static/img/wero-mascot.svg` — a simple SVG illustration of the "Wero" dog:
- Yellow body (`var(--color-amarillo)`)
- Magenta mohawk (`var(--color-magenta)`)
- Black sunglasses (two ellipses)
- Spiked collar (5-7 triangles)
- Holding a hot dog in one paw (suggested with a small rectangle and curve)

#### Scenario: mascot is served as static
- **GIVEN** the server is running
- **WHEN** `GET /static/img/wero-mascot.svg` is requested
- **THEN** the response is HTTP 200 with `Content-Type: image/svg+xml` and the SVG content

### Requirement: product placeholder SVGs
The system MUST provide 6 placeholder SVG files at `app/static/img/placeholder-{sku}.svg` (one per seed product: `JO-001`, `JO-002`, `JO-003`, `HB-001`, `HB-002`, `HB-003`). Each SVG:
- 400x400 viewBox
- Magenta-to-Yellow gradient background
- Centered text: product name (truncated if long) and "PLACEHOLDER" label
- Used in the product card image

#### Scenario: placeholder is rendered for each product
- **GIVEN** the menu grid renders 6 products
- **WHEN** the HTML is inspected
- **THEN** each product card has an `<img src="/static/img/placeholder-{sku}.svg" alt="...">` matching its SKU

#### Scenario: all 6 placeholders are served
- **GIVEN** the server is running
- **WHEN** each of the 6 placeholder URLs is requested
- **THEN** all return HTTP 200 with SVG content

### Requirement: cart-fab floating button
The system MUST define `.cart-fab` (fixed position cart button):
- Fixed to bottom-right with 24px margin
- Magenta circular button (64px diameter)
- Inline SVG cart icon (white)
- Small badge (`.cart-fab__count`) in top-right showing the item count, hidden when count is 0
- Yellow background for the badge, dark text
- Pulse animation when an item is added

#### Scenario: cart-fab shows count
- **GIVEN** the cart has 3 items
- **WHEN** the home page is rendered
- **THEN** the cart-fab shows a yellow badge with "3" in the top-right

#### Scenario: cart-fab pulses on add
- **GIVEN** the cart-fab is visible
- **WHEN** an item is added to the cart (via JS)
- **THEN** the cart-fab briefly scales up to 1.15x and back to 1.0x (CSS keyframe animation, 300ms duration)

## MODIFIED Requirements
None — greenfield change.

## REMOVED Requirements
None.
