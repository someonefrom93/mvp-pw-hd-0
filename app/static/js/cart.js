/* WeroCart — client-side cart backed by localStorage.
   Emits 'cart:change' CustomEvent on every mutation.
   Pure ES2020 — no build step, no dependencies.
*/

const STORAGE_KEY = 'wero_cart_v1';

const WeroCart = (() => {
  let state = load();

  function load() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    } catch {
      return {};
    }
  }

  function save() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    document.dispatchEvent(new CustomEvent('cart:change'));
  }

  return {
    items() {
      return Object.entries(state).map(([sku, cantidad]) => ({ sku, cantidad }));
    },

    add(sku, qty = 1) {
      state[sku] = (state[sku] || 0) + qty;
      save();
      return this;
    },

    remove(sku) {
      delete state[sku];
      save();
      return this;
    },

    update(sku, qty) {
      if (qty <= 0) return this.remove(sku);
      state[sku] = qty;
      save();
      return this;
    },

    clear() {
      state = {};
      save();
      return this;
    },

    count() {
      return Object.keys(state).length;
    },

    totalQty() {
      return Object.values(state).reduce((a, b) => a + b, 0);
    },

    isEmpty() {
      return this.count() === 0;
    },
  };
})();

window.WeroCart = WeroCart;

// On DOMContentLoaded: hook [data-sku] buttons and update fab badge
document.addEventListener('DOMContentLoaded', () => {
  // Update cart-fab count badge
  function updateFabCount() {
    const badge = document.querySelector('.cart-fab__count');
    if (!badge) return;
    const qty = WeroCart.totalQty();
    badge.textContent = qty;
    badge.style.display = qty > 0 ? 'flex' : 'none';
  }

  // Open cart modal
  const fab = document.querySelector('[data-cart-fab]');
  if (fab) {
    fab.addEventListener('click', () => {
      const modal = document.querySelector('.modal--cart');
      if (modal) {
        modal.classList.add('modal--open');
        document.body.style.overflow = 'hidden';
      }
    });
  }

  // Close modal
  document.querySelectorAll('.modal__close, .modal__backdrop').forEach(el => {
    el.addEventListener('click', () => {
      const modal = document.querySelector('.modal--cart');
      if (modal) {
        modal.classList.remove('modal--open');
        document.body.style.overflow = '';
      }
    });
  });

  // Hook "Añadir al carrito" buttons
  document.querySelectorAll('[data-sku]').forEach(btn => {
    btn.addEventListener('click', () => {
      const card = btn.closest('.card-producto');
      const qtyInput = card ? card.querySelector('input[type=number]') : null;
      const qty = qtyInput ? Math.max(1, parseInt(qtyInput.value, 10) || 1) : 1;
      const sku = btn.dataset.sku;
      WeroCart.add(sku, qty);

      // Pulse animation on fab
      const fabEl = document.querySelector('.cart-fab');
      if (fabEl) {
        fabEl.classList.remove('cart-fab__pulse-animation');
        void fabEl.offsetWidth; // reflow
        fabEl.classList.add('cart-fab__pulse-animation');
      }
    });
  });

  // Initial render
  updateFabCount();

  // Listen for cart changes
  document.addEventListener('cart:change', updateFabCount);
});