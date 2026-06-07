document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("order-form");
  if (!form) return;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const items = WeroCart.items();
    if (items.length === 0) {
      alert("Tu carrito está vacío");
      return;
    }
    const fd = new FormData(form);
    const customer = {
      nombre: fd.get("nombre"),
      telefono: fd.get("telefono"),
      edad: parseInt(fd.get("edad"), 10),
      genero: fd.get("genero"),
    };
    try {
      const resp = await fetch("/ordenes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ items, customer }),
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: "Error desconocido" }));
        alert("Error: " + (err.detail || resp.statusText));
        return;
      }
      const data = await resp.json();
      WeroCart.clear();
      window.location.href = data.whatsapp_url;
    } catch (err) {
      alert("Error de red: " + err.message);
    }
  });
});