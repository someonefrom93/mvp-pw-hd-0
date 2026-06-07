/* Checkout — simplified to just open WhatsApp with the order details.
   No DB persistence (the business receives the order via WhatsApp).
   Pure ES2020 — no build step, no dependencies.
*/

const PHONE_FALLBACK = '525555555555';

function buildOrderMessage(customer, items) {
  const lines = [
    '🐶 *Jochos El Perro Wero* — Nuevo pedido',
    '',
    `*Cliente:* ${customer.nombre}`,
    `*Teléfono:* ${customer.telefono}`,
    `*Edad:* ${customer.edad}`,
    `*Género:* ${customer.genero}`,
    '',
    '*Tu pedido:*',
  ];
  let total = 0;
  for (const item of items) {
    const subtotal = item.precio * item.cantidad;
    lines.push(`• ${item.cantidad}x ${item.nombre} — $${subtotal.toFixed(0)}`);
    total += subtotal;
  }
  lines.push(
    '',
    `*Total:* $${total.toFixed(0)}`,
    '',
    '¡Confirma por aquí y te lo llevamos en un periquito 🌭'
  );
  return lines.join('\n');
}

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('order-form');
  if (!form) return;

  form.addEventListener('submit', (e) => {
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
      edad: String(fd.get('edad') || '').trim(),
      genero: String(fd.get('genero') || '').trim(),
    };

    if (!customer.nombre || !customer.telefono) {
      alert('Por favor completa tu nombre y teléfono');
      return;
    }

    const phone = window.WERO_WHATSAPP_PHONE || PHONE_FALLBACK;
    const message = buildOrderMessage(customer, items);
    const url = `https://wa.me/${phone}?text=${encodeURIComponent(message)}`;

    // Close the modal, clear the cart, then redirect
    document.querySelector('.modal--cart')?.classList.remove('modal--open');
    document.body.style.overflow = '';
    WeroCart.clear();
    window.location.href = url;
  });
});
