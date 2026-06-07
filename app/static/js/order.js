/* Checkout — POSTs the order to /ordenes (DB persistence for the
   admin orders viewer), then redirects to the WhatsApp URL returned
   by the server. Pure ES2020 — no build step, no dependencies.
*/

const PHONE_FALLBACK = '4421231234'; // TODO: replace with the real business number

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('order-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const items = WeroCart.items();
    if (items.length === 0) {
      alert('Tu carrito está vacío');
      return;
    }

    const fd = new FormData(form);
    const customer = {
      nombre: String(fd.get('nombre') || '').trim(),
      telefono: String(fd.get('telefono') || '').trim(),
      edad: parseInt(fd.get('edad'), 10),
      genero: String(fd.get('genero') || '').trim(),
    };

    if (!customer.nombre || !customer.telefono) {
      alert('Por favor completa tu nombre y teléfono');
      return;
    }

    // Close the modal immediately for UX (we'll redirect next)
    document.querySelector('.modal--cart')?.classList.remove('modal--open');
    document.body.style.overflow = '';

    // Clear the form so reopening the cart shows fresh fields
    form.reset();

    try {
      const resp = await fetch('/ordenes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items, customer }),
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: 'Error desconocido' }));
        alert('Error al crear el pedido: ' + (err.detail || resp.statusText));
        return;
      }

      const data = await resp.json();

      // Order is saved in the DB (visible in /admin/ordenes).
      // Clear the cart and redirect to WhatsApp with the formatted order.
      WeroCart.clear();

      // Prefer the server-returned whatsapp_url (it has the right phone
      // and message). Fallback to the window-injected phone if missing.
      const url = data.whatsapp_url
        || `https://wa.me/${window.WERO_WHATSAPP_PHONE || PHONE_FALLBACK}?text=${encodeURIComponent('Pedido desde Jochos El Perro Wero')}`;

      window.location.href = url;
    } catch (err) {
      alert('Error de red: ' + err.message);
    }
  });
});
