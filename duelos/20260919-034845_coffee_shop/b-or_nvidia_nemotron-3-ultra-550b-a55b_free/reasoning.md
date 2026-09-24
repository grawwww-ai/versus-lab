The user wants a complete, self-contained HTML file for an online shop page for "Tostadores del Sur" with specific requirements. Let me break this down:

1. **Products** with specific IDs, names, prices in euros
2. **Business rules**: 10% discount on subtotal >= 100€, shipping 4.95€ if order (after discount) < 60€ else free, prices include VAT, round to cents
3. **UI Requirements**:
   - Attractive header and hero
   - Product grid with drawn illustrations (inline SVG/CSS, no images)
   - "Añadir" buttons
   - Cart panel with +/− quantity controls
   - Shows subtotal, discount, shipping, total (total in element with id="cart-total")
   - Micro-animations when adding to cart
4. **Auto-demo** on page load that adds products and changes quantities
5. **Test API**: window.shopTest = { reset(), add(id, qty), total() }
6. **All texts in Spanish**
7. **No external resources** - everything inline
8. **Single HTML file**

Let me design this carefully.

**Product IDs**: I'll assign them as: grinder=1, espresso=2, beans=3, mug=4, kettle=5, filters=6

**Illustrations**: I'll create simple but elegant SVG illustrations for each product using basic shapes.

**Cart functionality**: Need to manage state, update UI, calculate totals with business rules.

**Animations**: When adding to cart, a small animation (maybe a flying effect or pulse).

**Auto-demo**: On load, add a few items with delays to show functionality.

**Test API**: Expose methods that manipulate the cart and return calculated total.

Let me write the complete HTML file.