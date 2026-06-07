/* WeroCart — client-side cart backed by localStorage.
   Pure ES2020 — no build step, no dependencies.

   State shape (stored in localStorage as JSON):
     { "JO-001": { cantidad: 2, nombre: "Jocho Clásico", precio: 65.0 } }

   Public API:
     WeroCart.add(sku, nombre, precio, qty=1)
     WeroCart.remove(sku)
     WeroCart.update(sku, qty)
     WeroCart.clear()
     WeroCart.items()   → [{sku, nombre, precio, cantidad, subtotal}]
     WeroCart.count()   → number of distinct SKUs
     WeroCart.totalQty() → sum of quantities
     WeroCart.total()   → sum of (precio * cantidad)
     WeroCart.isEmpty()

   DOM bindings (this file):
     - Renders the cart modal dynamically (items, total, form visibility)
     - Opens/closes the cart modal
     - Handles "Añadir al carrito", +/-/× buttons on cart items
     - Updates the cart-fab count badge
*/

const STORAGE_KEY = 'wero_cart_v2';

const WeroCart = (() => {
  let state = load();

  function load() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); }
    catch { return {}; }
  }

  function save() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    document.dispatchEvent(new CustomEvent('cart:change'));
  }

  return {
    add(sku, nombre, precio, qty = 1) {
      if (state[sku]) {
        state[sku].cantidad += qty;
      } else {
        state[sku] = { cantidad: qty, nombre, precio: Number(precio) };
      }
      save();
      return this;
    },
    remove(sku) { delete state[sku]; save(); return this; },
    update(sku, qty) {
      if (qty <= 0) return this.remove(sku);
      if (state[sku]) { state[sku].cantidad = qty; save(); }
      return this;
    },
    clear() { state = {}; save(); return this; },
    items() {
      return Object.entries(state).map(([sku, d]) => ({
        sku, nombre: d.nombre, precio: d.precio, cantidad: d.cantidad,
        subtotal: d.precio * d.cantidad,
      }));
    },
    count() { return Object.keys(state).length; },
    totalQty() { return Object.values(state).reduce((s, d) => s + d.cantidad, 0); },
    total() { return Object.values(state).reduce((s, d) => s + d.precio * d.cantidad, 0); },
    isEmpty() { return Object.keys(state).length === 0; },
  };
})();

window.WeroCart = WeroCart;

// ── Helpers ────────────────────────────────────────────────────────
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));
const fmt = (n) => n.toFixed(0);
const escHtml = (s) => { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; };
const escAttr = (s) => String(s).replace(/"/g, '&quot;');

// ── Render cart modal ─────────────────────────────────────────────
function renderCart() {
  const items = WeroCart.items();
  const container = $('#cart-items-container');
  const fabCount = $('.cart-fab__count');
  const totalSection = $('#cart-total');
  const totalAmount = $('#cart-total-amount');
  const orderForm = $('#order-form');
  const confirmBtn = $('#btn-confirmar');

  // FAB count
  const qty = WeroCart.totalQty();
  if (fabCount) {
    fabCount.textContent = qty;
    fabCount.style.display = qty > 0 ? '' : 'none';
  }

  if (!container) return;

  if (WeroCart.isEmpty()) {
    container.innerHTML = `<p class="cart-empty">Tu carrito está vacío</p>`;
    if (totalSection) totalSection.style.display = 'none';
    if (orderForm) orderForm.style.display = 'none';
    if (confirmBtn) confirmBtn.disabled = true;
    return;
  }

  container.innerHTML = `
    <ul class="cart-items">
      ${items.map(item => `
        <li class="cart-item">
          <div class="cart-item__info">
            <div class="cart-item__name">${escHtml(item.nombre)}</div>
            <div class="cart-item__price">$${fmt(item.precio)} × ${item.cantidad} = $${fmt(item.subtotal)}</div>
          </div>
          <div class="cart-item__controls">
            <button class="btn btn-outline btn-qty" data-cart-update="${escAttr(item.sku)}" data-qty="${item.cantidad - 1}" type="button" aria-label="Quitar uno">−</button>
            <span class="cart-item__qty">${item.cantidad}</span>
            <button class="btn btn-magenta btn-qty" data-cart-update="${escAttr(item.sku)}" data-qty="${item.cantidad + 1}" type="button" aria-label="Agregar uno">+</button>
            <button class="btn btn-outline btn-remove" data-cart-remove="${escAttr(item.sku)}" type="button" aria-label="Quitar del carrito">×</button>
          </div>
        </li>
      `).join('')}
    </ul>`;

  if (totalSection) totalSection.style.display = '';
  if (totalAmount) totalAmount.textContent = fmt(WeroCart.total());
  if (orderForm) orderForm.style.display = '';
  if (confirmBtn) confirmBtn.disabled = false;
}

// ── Modal open/close ─────────────────────────────────────────────
function openCartModal() {
  const modal = $('.modal--cart');
  if (!modal) return;
  modal.classList.add('modal--open');
  document.body.style.overflow = 'hidden';
}
function closeCartModal() {
  const modal = $('.modal--cart');
  if (!modal) return;
  modal.classList.remove('modal--open');
  document.body.style.overflow = '';
}

// ── Wire up on DOMContentLoaded ───────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  renderCart();

  // Cart FAB opens the modal
  $$('[data-cart-fab]').forEach(btn => btn.addEventListener('click', openCartModal));

  // Close on backdrop / × click
  $$('.modal--cart .modal__backdrop, .modal--cart .modal__close').forEach(el => {
    el.addEventListener('click', closeCartModal);
  });
  // Close on ESC
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeCartModal();
  });

  // "Añadir al carrito" on product cards
  $$('[data-cart-add]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const sku = btn.dataset.sku;
      const nombre = btn.dataset.nombre;
      const precio = parseFloat(btn.dataset.precio);
      const qty = parseInt(btn.closest('.card-producto')?.querySelector('input[type="number"]')?.value || '1', 10);
      WeroCart.add(sku, nombre, precio, qty);
      // Brief visual feedback
      const original = btn.textContent;
      btn.textContent = '¡Agregado!';
      btn.disabled = true;
      setTimeout(() => { btn.textContent = original; btn.disabled = false; }, 900);
    });
  });

  // Delegate clicks for item controls (+, −, ×)
  const container = $('#cart-items-container');
  if (container) {
    container.addEventListener('click', (e) => {
      const removeBtn = e.target.closest('[data-cart-remove]');
      if (removeBtn) {
        WeroCart.remove(removeBtn.dataset.cartRemove);
        return;
      }
      const updateBtn = e.target.closest('[data-cart-update]');
      if (updateBtn) {
        WeroCart.update(updateBtn.dataset.cartUpdate, parseInt(updateBtn.dataset.qty, 10));
      }
    });
  }

  // Re-render on any cart change
  document.addEventListener('cart:change', renderCart);
});
