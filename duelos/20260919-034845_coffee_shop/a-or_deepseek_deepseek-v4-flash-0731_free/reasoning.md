The user wants a complete, self-contained HTML file with inline CSS and JS for a coffee shop "Tostadores del Sur". Let me break down the requirements carefully:

**Products:**
1. Molinillo manual - 49.90 €
2. Cafetera espresso - 89.00 €
3. Café de Etiopía 250 g - 12.50 €
4. Taza de cerámica - 8.90 €
5. Hervidor cuello de cisne - 39.00 €
6. Filtros de papel x100 - 5.50 €

**Business rules:**
- 10% discount on subtotal when subtotal >= 100.00 €
- Shipping: 4.95 € when order (after discount) < 60.00 €, otherwise free
- Prices include VAT
- Round final total to cents

**Requirements:**
- Header and hero (attractive)
- Product grid with drawn illustration of each product (inline SVG or CSS, no images)
- "Añadir" buttons
- Cart panel with + / - quantity controls
- Show subtotal, discount, shipping, total (total inside element id="cart-total")
- Micro-animations when adding to cart
- Auto demo on page load: adds a few products and changes quantity
- Expose window.shopTest = { reset(), add(id, qty), total() }
- total() returns final total in euros as number
- All texts in Spanish
- No external resources

**SVG Illustrations needed:**
1. Coffee grinder (manual)
2. Espresso maker (moka pot)
3. Coffee beans bag
4. Ceramic mug
5. Gooseneck kettle
6. Paper filters

Let me design simple SVG illustrations for each.

**Cart Logic:**
- Subtotal = sum(price * qty)
- Discount = 10% of subtotal if subtotal >= 100
- After discount = subtotal - discount
- Shipping = 4.95 if after discount < 60, else 0
- Total = subtotal - discount + shipping (rounded to cents)

**Demo on load:**
- Add a few products, change a quantity

**Test API:**
```js
window.shopTest = {
  reset() { ... },
  add(id, qty) { ... },
  total() { ... }
}
```

Let me think about the total() function:
- It should compute the total applying the same rules and update the visible cart.

Let me code this.

**HTML Structure:**
```html
<header>
  <div class="logo">Tostadores del Sur</div>
  <div class="cart-icon">🛒 <span id="cart-count">0</span></div>
</header>

<section class="hero">
  <h1>Bienvenido a Tostadores del Sur</h1>
  <p>Especialidad en café de origen</p>
</section>

<main>
  <section class="product-grid">
    <!-- 6 product cards -->
  </section>
  
  <aside class="cart-panel">
    <h2>Carrito</h2>
    <div id="cart-items"></div>
    <div class="cart-summary">
      <div>Subtotal: <span id="cart-subtotal"></span></div>
      <div>Descuento: <span id="cart-discount"></span></div>
      <div>Envío: <span id="cart-shipping"></span></div>
      <div>Total: <span id="cart-total"></span></div>
    </div>
  </aside>
</main>
```

**JavaScript:**
- Store products in an array
- Store cart as object { id: quantity }
- Render function updates the cart panel
- Add to cart function
- Change quantity function
- Auto demo

Let me think about the subtotal calculation:
```js
function calculateSubtotal(cart) {
  return Object.entries(cart).reduce((sum, [id, qty]) => {
    const product = products.find(p => p.id === Number(id));
    return sum + (product.price * qty);
  }, 0);
}
```

subtotal is the sum of price * qty for each item.

Discount: if subtotal >= 100, discount = subtotal * 0.10, else 0.

After discount: subtotal - discount.

Shipping: if after discount < 60, shipping = 4.95, else 0. Actually what if after discount is 0? An empty cart. Then shipping should probably be 0. Let me handle: if cart is empty, subtotal=0, discount=0, total=0. Let me check: when cart is empty, subtotal = 0, discount = 0, after discount = 0, which is < 60 so shipping = 4.95. That's wrong for an empty cart. I need to add a check: if total items quantity is 0, shipping = 0. Or if subtotal == 0, shipping = 0. Let me handle that: `shipping = (subtotal - discount) > 0 && (subtotal - discount) < 60 ? 4.95 : 0;`

Actually the rule says "shipping costs 4.95 € when the order (after the discount) is below 60.00 €, otherwise shipping is free". For an empty cart, the order is 0, which is below 60, so it would charge 4.95. But that doesn't make sense. I'll add a condition: if subtotal is 0, shipping is 0. Or if the cart has no items, shipping = 0. Let me do: `shipping = (subtotal > 0 && (subtotal - discount) < 60) ? 4.95 : 0;`

Let me re-read: "shipping costs 4.95 € when the order (after the discount) is below 60.00 €, otherwise shipping is free". I think the logical interpretation is that you only pay shipping if there are items. I'll add the check.

Total = subtotal - discount + shipping. Round to 2 decimals.

**Demo on load:**
After page loads:
```js
window.addEventListener('DOMContentLoaded', () => {
  // Auto demo
  shopTest.add(3, 2); // add 2 bags of coffee
  setTimeout(() => {
    shopTest.add(4, 1); // add a mug
    shopTest.add(1, 1); // add a grinder
  }, 500);
});
```

Wait, but the demo should be visible. Let me think about this. The demo runs "a short automatic demo that adds a few products and changes a quantity so a viewer sees the cart working". So I'll add some products with small timeouts to show the animations.

Let me plan the demo:
1. After 500ms: add 3 (Café de Etiopía) x2
2. After 1000ms: add 4 (Taza) x1
3. After 1500ms: change quantity of 3 to 3 (i.e., add 1 more)
4. After 2000ms: add 1 (Molinillo) x1

Actually, let me keep it simpler:
- Add 3 x2
- Then add 4
- Then change quantity of 3 from 2 to 4
- Then add 1

**Micro-animations:**
When adding to cart, animate the button or the cart icon. Let me do a "bounce" animation on the cart icon and a "pulse" on the button.

**SVG Illustrations:**

Let me create simple inline SVGs for each product:

1. **Molinillo manual**: A manual coffee grinder - rectangular box with a handle on top, crank, and a small drawer at the bottom.

2. **Cafetera espresso**: Moka pot - hexagonal base, handle, small spout at top.

3. **Café de Etiopía 250 g**: A bag of coffee beans - rounded bag shape with a label, maybe some beans around.

4. **Taza de cerámica**: A simple mug - U shape with a handle.

5. **Hervidor cuello de cisne**: Gooseneck kettle - a kettle with a curved spout, handle on top.

6. **Filtros de papel x100**: A stack of paper filters - flat bottomed cone shape or a packet.

Let me design each SVG carefully. I'll use simple shapes with a consistent color palette. Let me use brown/coffee colors, cream, etc.

Color palette:
- Primary: #5D4037 (dark brown)
- Secondary: #8D6E63 (medium brown)
- Accent: #D7A86E (golden)
- Background: #F5F0E8 (cream)
- Text: #2D1B13

Let me draw each SVG:

**1. Molinillo manual:**
```svg
<svg viewBox="0 0 100 100">
  <!-- Box -->
  <rect x="25" y="20" width="50" height="60" rx="5" fill="#8D6E63"/>
  <rect x="30" y="25" width="40" height="50" rx="3" fill="#D7CCC8"/>
  <!-- Handle -->
  <circle cx="50" cy="12" r="6" fill="#5D4037"/>
  <rect x="49" y="10" width="3" height="15" fill="#5D4037"/>
  <circle cx="72" cy="8" r="4" fill="#5D4037"/>
  <rect x="70" y="8" width="8" height="3" fill="#5D4037"/>
  <!-- Drawer -->
  <rect x="30" y="65" width="40" height="10" rx="2" fill="#8D6E63"/>
  <circle cx="50" cy="70" r="2" fill="#5D4037"/>
</svg>
```

**2. Cafetera espresso:**
```svg
<svg viewBox="0 0 100 100">
  <!-- Top -->
  <path d="M30 30 L70 30 L70 25 A10 10 0 0 0 60 15 L40 15 A10 10 0 0 0 30 25 Z" fill="#B0BEC5"/>
  <!-- Base -->
  <path d="M25 40 L75 40 L70 80 L30 80 Z" fill="#5D4037"/>
  <!-- Handle -->
  <path d="M25 40 L10 45 L15 60 L30 55 Z" fill="#4E342E"/>
  <!-- Spout -->
  <path d="M75 40 L90 30 L85 25 Z" fill="#B0BEC5"/>
  <!-- Details -->
  <rect x="35" y="30" width="30" height="5" fill="#37474F"/>
</svg>
```

**3. Café de Etiopía bag:**
```svg
<svg viewBox="0 0 100 100">
  <!-- Bag body -->
  <path d="M30 30 Q30 25 40 25 L60 25 Q70 25 70 30 L70 75 Q70 80 60 80 L40 80 Q30 80 30 75 Z" fill="#4E342E"/>
  <!-- Bag top fold -->
  <path d="M28 25 L72 25 L68 35 L32 35 Z" fill="#3E2723"/>
  <!-- Label -->
  <rect x="38" y="40" width="24" height="20" rx="2" fill="#E0C097"/>
  <text x="50" y="53" text-anchor="middle" font-size="6" fill="#3E2723">Etiopía</text>
  <!-- Beans -->
  <ellipse cx="35" cy="85" rx="8" ry="5" fill="#5D4037"/>
  <ellipse cx="65" cy="88" rx="8" ry="5" fill="#6D4C41"/>
</svg>
```

**4. Taza de cerámica:**
```svg
<svg viewBox="0 0 100 100">
  <!-- Mug body -->
  <path d="M25 35 L30 80 L70 80 L75 35 Z" fill="#E0C097"/>
  <!-- Handle -->
  <path d="M75 40 L90 40 Q95 40 95 50 Q95 60 85 60 L75 60 Z" fill="none" stroke="#E0C097" stroke-width="6"/>
  <!-- Coffee inside -->
  <ellipse cx="50" cy="35" rx="25" ry="8" fill="#4E342E"/>
  <ellipse cx="50" cy="32" rx="20" ry="5" fill="#5D4037"/>
  <!-- Rim -->
  <path d="M25 35 Q50 25 75 35" fill="none" stroke="#D7A86E" stroke-width="2"/>
</svg>
```

**5. Hervidor cuello de cisne:**
```svg
<svg viewBox="0 0 100 100">
  <!-- Body -->
  <ellipse cx="40" cy="60" rx="25" ry="20" fill="#78909C"/>
  <path d="M20 50 L20 70 Q20 80 40 80 Q60 80 60 70 L60 50 Z" fill="#78909C"/>
  <!-- Spout -->
  <path d="M60 55 Q80 45 85 30 Q86 27 88 28" fill="none" stroke="#78909C" stroke-width="4" stroke-linecap="round"/>
  <!-- Handle -->
  <path d="M35 40 Q35 25 50 25 Q65 25 60 40" fill="none" stroke="#546E7A" stroke-width="4"/>
</svg>
```

**6. Filtros de papel:**
```svg
<svg viewBox="0 0 100 100">
  <!-- Filter paper packet -->
  <ellipse cx="50" cy="35" rx="20" ry="8" fill="#FFF8E1"/>
  <path d="M30 35 L30 70 Q30 78 50 78 Q70 78 70 70 L70 35 Z" fill="#FFF3E0"/>
  <!-- Lines for filters -->
  <path d="M35 40 L35 65" stroke="#E0C097" stroke-width="1"/>
  <path d="M42 38 L42 70" stroke="#E0C097" stroke-width="1"/>
  <path d="M58 38 L58 70" stroke="#E0C097" stroke-width="1"/>
  <!-- Rim -->
  <ellipse cx="50" cy="35" rx="20" ry="8" fill="none" stroke="#D7CCC8" stroke-width="2"/>
</svg>
```

Let me refine these SVGs to look nice. Actually, they don't need to be perfect works of art, just decent simple illustrations. Let me use a consistent stroke and fill style.

Let me think about the layout. A common layout for online shops:
- Header with logo and cart icon
- Hero section (banner)
- Product grid
- Cart panel

Since this is an online shop, I'll use a layout where:
- Main content is centered, max-width maybe 1200px
- Product grid with cards in a 3-column grid
- Cart panel could be a slide-in from the right or a fixed panel

Actually, let me make the cart a fixed panel on the right side that's always visible. The product grid will be on the left/center, and the cart panel on the right.

Let me use CSS Grid for layout.

**Layout:**
```css
body {
  font-family: 'Georgia', serif;
  background: #F5F0E8;
  color: #2D1B13;
}

header {
  background: #2D1B13;
  color: #F5F0E8;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 100;
}

.hero {
  text-align: center;
  padding: 4rem 2rem;
  background: linear-gradient(135deg, #4E342E, #6D4C41);
  color: #F5F0E8;
}

main {
  display: grid;
  grid-template-columns: 1fr 350px;
  gap: 2rem;
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
}

.cart-panel {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  position: sticky;
  top: 80px;
  height: fit-content;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
```

For mobile responsiveness, I could add media queries, but it's not strictly required. Let me add basic responsiveness.

**Cart rendering:**

The cart-items list will show each product with name, price, quantity controls (+/-), line total. The cart-summary section shows subtotal, discount, shipping, total.

**Micro-animations:**

1. Button "Añadir" - on click, do a "pulse" animation
2. Cart icon - bounce when item added
3. Cart total - flash when updated

Let me implement a "fly" animation maybe? That could be complex. A simpler approach: when adding, the button briefly fills with a different color, and the cart icon bounces.

Let me think about the auto-demo. It should be visible but not too obnoxious. I'll use `setTimeout` to sequence:

```js
function runDemo() {
  setTimeout(() => shopTest.add(3, 2), 500);
  setTimeout(() => shopTest.add(4, 1), 1200);
  setTimeout(() => shopTest.add(3, 1), 1800);
  setTimeout(() => shopTest.add(1, 1), 2500);
}
```

Adds:
- 2x Café de Etiopía (12.50 each) = 25.00
- 1x Taza (8.90) = 8.90
- 1x more Café de Etiopía = 12.50
- 1x Molinillo manual (49.90) = 49.90
Total items: 2+1+1+1 = 5
Subtotal: 25 + 8.90 + 12.50 + 49.90 = 96.30
Since subtotal < 100, no discount.
After discount: 96.30
Shipping: 96.30 >= 60, so free.
Total: 96.30

That's a nice demo. Maybe I should also demonstrate discount. Let me add more to trigger discount:
- 2x Café de Etiopía = 25.00
- 2x Taza = 17.80
- 1x Filtros = 5.50
- 1x Molinillo = 49.90
Subtotal: 98.20... still below 100.

Let me just add the molinillo and the espresso maker:
- 1x Molinillo manual = 49.90
- 1x Cafetera espresso = 89.00
- 2x Café de Etiopía = 25.00
Subtotal: 163.90
Discount: 16.39
After discount: 147.51
Shipping: free
Total: 147.51

That demonstrates both discount and free shipping. Let me do:

```js
function runDemo() {
  setTimeout(() => shopTest.add(1, 1), 300); // Molinillo
  setTimeout(() => shopTest.add(2, 1), 900); // Cafetera
  setTimeout(() => shopTest.add(3, 2), 1500); // Café x2
  setTimeout(() => shopTest.changeQty(3, 3), 2000); // change to 3
}
```

Wait, changeQty should set the quantity. Let me expose add(id, qty) which adds qty to existing, and changeQty maybe? Or I could use add(3, 1) to add one more. The requirement says "add(id, qty)" in the test API. So add(id, qty) adds qty. To change quantity, the user uses the +/- buttons in the UI. In the auto-demo, I can use add(3, 1) to go from 2 to 3.

Actually the requirement says: "When the page loads, run a short automatic demo that adds a few products and changes a quantity". So I should have a way to change a quantity. I'll add a setQty or changeQty function internally, and use it in the demo. Or I can call add(3, 1) to increase it. That's a quantity change too.

Let me also make the demo demonstrate the +/- buttons working. Instead of test API, I can directly call internal functions.

**Test API:**
```js
window.shopTest = {
  reset() {
    cart = {};
    renderCart();
  },
  add(id, qty) {
    if (products.some(p => p.id === id)) {
      cart[id] = (cart[id] || 0) + qty;
      renderCart();
    }
  },
  total() {
    const totals = computeTotals();
    return totals.total;
  }
};
```

The requirement: "reset(), add(id, qty), total() where total() returns the final total in euros as a number, applying the same rules and updating the visible cart."

So total() should also update the visible cart. That means total() shouldn't just compute, it should also trigger a render. Interesting. Well, reset and add already render. total() can also render (idempotent) and return the total.

Let me also make sure the cart state is properly maintained.

**Rounding:**
Since prices have 2 decimal places, and we multiply by quantities (integers), subtotal will have at most 2 decimal places. But if I add floating point numbers like 12.50 * 2 = 25.00, that's fine. Discount: subtotal * 0.10 could have more decimals. E.g., 163.90 * 0.10 = 16.390000000000002. I should use Math.round(x * 100) / 100 to round to cents.

For total: Math.round((subtotal - discount + shipping) * 100) / 100.

**Changing quantity:**
In the cart panel, each item has - and + buttons. The - button decreases quantity by 1, and if it reaches 0, the item is removed. The + button increases by 1.

**Out of stock:** Let it go to 0 and remove. If all items are removed, show "El carrito está vacío".

Let me think about the design more:

**Header:**
- Logo on left (maybe a coffee bean icon)
- Title "Tostadores del Sur"
- Cart icon with item count on right

**Hero:**
- Large headline: "El café de especialidad llega a tu casa"
- Subtext: "Grano de origen, métodos de preparación y accesorios"
- Maybe a call-to-action button "Ver productos"

**Product Grid:**
Each card:
- SVG illustration at top (consistent size, e.g., 150x150)
- Product name
- Price in euros
- "Añadir" button

Let me refine the SVG illustrations one more time. I want them to look somewhat polished. Let me use a consistent viewBox and make each product distinct.

For the cart, each item:
- Name
- Price each
- Quantity controls (-, quantity, +)
- Line total

Let me also consider the cart panel position. Should it be always visible (sticky) or slide-in? Since this is a "panel", I'll make it a sticky aside on the right. On smaller screens, it could go below the products.

Let me write the complete HTML now.

Actually, let me reconsider the SVGs. I need to draw them carefully:

**Molinillo manual (manual coffee grinder):**
A box with a crank handle on top and a knob on the side. Let me design:
```
<svg viewBox="0 0 100 100">
  <!-- box body -->
  <rect x="25" y="25" width="50" height="60" rx="5" fill="#8D6E63"/>
  <rect x="30" y="30" width="40" height="50" rx="3" fill="#A1887F"/>
  <!-- wood top -->
  <rect x="22" y="22" width="56" height="8" rx="3" fill="#5D4037"/>
  <!-- handle -->
  <circle cx="50" cy="15" r="5" fill="#3E2723"/>
  <rect x="49" y="10" width="2" height="15" fill="#3E2723"/>
  <circle cx="68" cy="10" r="3" fill="#3E2723"/>
  <rect x="53" y="10" width="15" height="2" fill="#3E2723"/>
  <!-- drawer -->
  <rect x="30" y="65" width="40" height="10" rx="2" fill="#6D4C41"/>
  <circle cx="50" cy="70" r="2" fill="#3E2723"/>
</svg>
```

**Cafetera espresso (moka pot):**
```
<svg viewBox="0 0 100 100">
  <!-- base (lower chamber) -->
  <path d="M25 50 L30 75 Q30 80 35 80 L65 80 Q70 80 70 75 L75 50 Z" fill="#757575"/>
  <!-- top (upper chamber) -->
  <path d="M30 30 L25 50 L75 50 L70 30 Z" fill="#9E9E9E"/>
  <!-- lid knob -->
  <path d="M55 15 L55 30 L45 30 L45 15 Z" fill="#616161"/>
  <!-- handle -->
  <path d="M25 30 L10 35 Q5 37 8 45 L12 58 Q14 63 20 60 L30 55" fill="none" stroke="#424242" stroke-width="4"/>
  <!-- spout -->
  <path d="M30 50 L25 55 Q20 60 25 65 L30 65" fill="none" stroke="#9E9E9E" stroke-width="3"/>
  <!-- details -->
  <path d="M35 35 L40 25 L50 20 L60 25 L65 35 Z" fill="#E0E0E0" opacity="0.5"/>
</svg>
```

Hmm, let me simplify. Let me make it more recognizable:

**Moka pot:**
```
<svg viewBox="0 0 100 100">
  <!-- Lower chamber (hexagonal) -->
  <polygon points="30,50 70,50 65,75 35,75" fill="#616161"/>
  <!-- Upper chamber -->
  <polygon points="35,50 65,50 60,25 40,25" fill="#9E9E9E"/>
  <!-- Lid -->
  <rect x="40" y="18" width="20" height="7" rx="2" fill="#757575"/>
  <circle cx="50" cy="15" r="3" fill="#424242"/>
  <!-- Handle -->
  <path d="M35 25 L15 30 Q10 31 12 38 L16 50 Q18 55 24 52 L35 45" fill="none" stroke="#424242" stroke-width="4"/>
  <!-- Spout -->
  <path d="M35 50 L28 58" fill="none" stroke="#9E9E9E" stroke-width="4"/>
</svg>
```

**Café de Etiopía bag:**
```
<svg viewBox="0 0 100 100">
  <path d="M30 25 Q30 20 35 18 L65 18 Q70 20 70 25 L72 75 Q72 82 65 82 L35 82 Q28 82 28 75 Z" fill="#4E342E"/>
  <path d="M28 28 L72 28 L70 35 L30 35 Z" fill="#3E2723"/>
  <rect x="35" y="40" width="30" height="22" rx="4" fill="#FFF8E1"/>
  <text x="50" y="53" text-anchor="middle" font-size="5" fill="#4E342E">CAFÉ</text>
  <text x="50" y="60" text-anchor="middle" font-size="3" fill="#4E342E">Etiopía</text>
  <!-- bean icons -->
  <ellipse cx="30" cy="90" rx="6" ry="4" fill="#6D4C41"/>
  <ellipse cx="70" cy="88" rx="5" ry="3.5" fill="#5D4037"/>
  <ellipse cx="50" cy="90" rx="5" ry="3" fill="#8D6E63"/>
</svg>
```

Actually, let me not include text in SVG since they might not render consistently. I'll use shapes only, or I can use a label with rects.

Hmm, actually text in SVG works fine if the user has fonts, but it might not be reliable. Let me use just shapes.

Let me plan each SVG as a simple, beautiful illustration:

1. **Coffee Grinder**: A minimal wooden grinder
2. **Moka Pot**: Silver with black handle
3. **Coffee Bag**: Brown bag with beige label
4. **Ceramic Mug**: A cup with coffee inside
5. **Gooseneck Kettle**: Steel colored with curved spout
6. **Paper Filters**: White cone filters

I'll make them all with a viewBox="0 0 100 100" and use nice colors.

Let me draw them one by one:

**1. Molinillo manual (Coffee Grinder):**
```svg
<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <!-- Main body -->
  <rect x="25" y="25" width="50" height="60" rx="6" fill="#6D4C41"/>
  <rect x="30" y="30" width="40" height="50" rx="3" fill="#8D6E63"/>
  <!-- Wooden top -->
  <rect x="22" y="20" width="56" height="8" rx="4" fill="#3E2723"/>
  <rect x="22" y="28" width="56" height="4" fill="#5D4037"/>
  <!-- Handle -->
  <circle cx="50" cy="12" r="4" fill="#2D1B13"/>
  <rect x="49" y="8" width="2" height="6" fill="#2D1B13"/>
  <circle cx="66" cy="6" rx="3" ry="3" fill="#2D1B13"/>
  <rect x="52" y="6" width="14" height="2" fill="#2D1B13"/>
  <!-- Drawer -->
  <rect x="30" y="65" width="40" height="12" rx="3" fill="#4E342E"/>
  <rect x="32" y="67" width="36" height="8" rx="2" fill="#5D4037"/>
  <circle cx="50" cy="71" r="2" fill="#3E2723"/>
  <!-- Shadow -->
  <ellipse cx="50" cy="87" rx="25" ry="3" fill="rgba(0,0,0,0.1)"/>
</svg>
```

**2. Cafetera espresso (Moka Pot):**
```svg
<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <!-- Lower chamber -->
  <polygon points="28,50 72,50 68,75 32,75" fill="#78909C"/>
  <!-- Upper chamber -->
  <polygon points="32,50 68,50 63,25 37,25" fill="#90A4AE"/>
  <!-- Middle section -->
  <rect x="35" y="25" width="30" height="5" fill="#546E7A"/>
  <!-- Lid -->
  <path d="M40 25 Q50 18 60 25 Z" fill="#78909C"/>
  <circle cx="50" cy="18" r="3" fill="#546E7A"/>
  <!-- Handle -->
  <path d="M37 28 L18 35 Q12 38 15 45 L20 55 Q23 62 30 58 L40 50" fill="none" stroke="#3E2723" stroke-width="5" stroke-linecap="round"/>
  <!-- Spout -->
  <path d="M32 52 L25 60" fill="none" stroke="#90A4AE" stroke-width="4" stroke-linecap="round"/>
  <!-- Hexagonal detail -->
  <polygon points="42,28 58,28 58,45 42,45" fill="none" stroke="#CFD8DC" stroke-width="1" opacity="0.6"/>
</svg>
```

**3. Café de Etiopía Bag:**
```svg
<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <path d="M28 25 Q28 18 37 16 L63 16 Q72 18 72 25 L74 78 Q74 85 65 85 L35 85 Q26 85 26 78 Z" fill="#4E342E"/>
  <path d="M26 30 L74 30 L72 40 L28 40 Z" fill="#3E2723"/>
  <rect x="33" y="45" width="34" height="25" rx="5" fill="#FFF8E1"/>
  <ellipse cx="42" cy="55" rx="5" ry="4" fill="#5D4037"/>
  <ellipse cx="58" cy="55" rx="5" ry="4" fill="#6D4C41"/>
  <path d="M46 55 Q50 58 54 55 Q50 52 46 55" fill="#8D6E63"/>
  <rect x="40" y="62" width="20" height="3" rx="1.5" fill="#3E2723"/>
  <rect x="44" y="67" width="12" height="2" rx="1" fill="#3E2723"/>
  <ellipse cx="50" cy="90" rx="20" ry="3" fill="rgba(0,0,0,0.1)"/>
</svg>
```

**4. Taza de cerámica (Ceramic Mug):**
```svg
<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <!-- Saucer -->
  <ellipse cx="45" cy="75" rx="35" ry="8" fill="#BCAAA4"/>
  <!-- Cup body -->
  <path d="M20 35 L25 70 L65 70 L70 35 Z" fill="#D7A86E"/>
  <!-- Coffee -->
  <path d="M20 35 L70 35 L68 45 L22 45 Z" fill="#4E342E"/>
  <ellipse cx="45" cy="35" rx="25" ry="6" fill="#3E2723"/>
  <!-- Cup rim -->
  <ellipse cx="45" cy="35" rx="25" ry="6" fill="none" stroke="#BF8F5A" stroke-width="2"/>
  <!-- Handle -->
  <path d="M70 45 Q85 45 85 58 Q85 70 67 68" fill="none" stroke="#D7A86E" stroke-width="6"/>
  <!-- Decorative line -->
  <path d="M25 50 Q45 55 65 50" fill="none" stroke="#BF8F5A" stroke-width="1.5"/>
  <circle cx="45" cy="55" r="2" fill="#BF8F5A"/>
</svg>
```

**5. Hervidor cuello de cisne (Gooseneck Kettle):**
```svg
<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <!-- Kettle body -->
  <ellipse cx="40" cy="60" rx="25" ry="20" fill="#B0BEC5"/>
  <path d="M18 50 L18 68 Q18 80 40 80 Q62 80 62 68 L62 50 Z" fill="#CFD8DC"/>
  <!-- Bottom rim -->
  <ellipse cx="40" cy="78" rx="20" ry="4" fill="#90A4AE"/>
  <!-- Top lid -->
  <ellipse cx="40" cy="45" rx="15" ry="5" fill="#78909C"/>
  <circle cx="40" cy="42" r="3" fill="#546E7A"/>
  <!-- Spout (gooseneck) -->
  <path d="M62 58 Q80 50 85 30 Q86 23 90 20" fill="none" stroke="#B0BEC5" stroke-width="5" stroke-linecap="round"/>
  <path d="M62 58 Q80 50 85 30 Q86 23 90 20" fill="none" stroke="#CFD8DC" stroke-width="2" stroke-linecap="round"/>
  <!-- Handle -->
  <path d="M32 40 Q32 25 45 25 Q58 25 58 38" fill="none" stroke="#455A64" stroke-width="4" stroke-linecap="round"/>
</svg>
```

**6. Filtros de papel (Paper Filters):**
```svg
<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <!-- Filters stack -->
  <path d="M30 35 L35 70 Q40 80 50 80 Q60 80 65 70 L70 35 Z" fill="#FFF8E1"/>
  <path d="M33 32 L38 67 Q43 77 50 77 Q57 77 62 67 L67 32 Z" fill="#FFEBEE"/>
  <!-- Top rim -->
  <ellipse cx="50" cy="35" rx="22" ry="8" fill="#FFF8E1" stroke="#FFCCBC" stroke-width="1"/>
  <!-- Inner rims -->
  <ellipse cx="48" cy="33" rx="18" ry="6" fill="#FFEBEE" stroke="#FFE0B2" stroke-width="1"/>
  <!-- Pleats -->
  <path d="M38 35 L36 70" stroke="#FFCC80" stroke-width="0.8"/>
  <path d="M50 35 L50 72" stroke="#FFCC80" stroke-width="0.8"/>
  <path d="M62 35 L64 68" stroke="#FFCC80" stroke-width="0.8"/>
  <!-- Shadow -->
  <ellipse cx="50" cy="82" rx="25" ry="3" fill="rgba(0,0,0,0.1)"/>
</svg>
```

These SVGs are decent. Let me use them as-is and integrate into product cards.

Now let me write the complete HTML file. This is going to be quite long.

**Data Structure:**
```js
const products = [
  { id: 1, name: 'Molinillo manual', price: 49.90, svg: '...' },
  { id: 2, name: 'Cafetera espresso', price: 89.00, svg: '...' },
  { id: 3, name: 'Café de Etiopía 250 g', price: 12.50, svg: '...' },
  { id: 4, name: 'Taza de cerámica', price: 8.90, svg: '...' },
  { id: 5, name: 'Hervidor cuello de cisne', price: 39.00, svg: '...' },
  { id: 6, name: 'Filtros de papel x100', price: 5.50, svg: '...' }
];
```

**Cart Logic:**
```js
let cart = {};

function computeTotals() {
  let subtotal = 0;
  for (const id in cart) {
    const p = products.find(p => p.id === Number(id));
    subtotal += p.price * cart[id];
  }
  const discount = subtotal >= 100 ? subtotal * 0.1 : 0;
  const afterDiscount = subtotal - discount;
  const shipping = (afterDiscount > 0 && afterDiscount < 60) ? 4.95 : 0;
  const total = Math.round((afterDiscount + shipping) * 100) / 100;
  return { subtotal, discount, afterDiscount, shipping, total };
}
```

Wait, afterDiscount for shipping calculation: afterDiscount = subtotal - discount. In my code, afterDiscount should be subtotal - discount. Let me keep that.

Actually, I'm confused about variable names. Let me use:
- `subtotal` = sum of prices * quantities
- `discount` = 10% of subtotal if subtotal >= 100, else 0
- `discountedSubtotal` = subtotal - discount
- `shipping` = 4.95 if discountedSubtotal < 60 (and > 0), else 0
- `total` = discountedSubtotal + shipping

That's clearer.

**Precision:**
Use `Math.round(x * 100) / 100` for rounding to cents.

When computing subtotal, I should also round: `Math.round(subtotal * 100) / 100`.

Since each product price has at most 2 decimals, and qty is integer, subtotal should have at most 2 decimals. But floating point might introduce issues (e.g., 12.50 * 3 = 37.5, which is fine). Let me still round at the end.

For discount: `Math.round(subtotal * 10) / 100` for 10%? Actually subtotal * 0.10. Then round to cents: `Math.round(subtotal * 0.10 * 100) / 100`.

**Rendering:**

The cart panel will be rendered by a `renderCart()` function.

```js
function renderCart() {
  const cartItems = document.getElementById('cart-items');
  cartItems.innerHTML = '';
  
  let itemCount = 0;
  for (const id in cart) {
    const qty = cart[id];
    const p = products.find(p => p.id === Number(id));
    itemCount += qty;
    
    const item = document.createElement('div');
    item.className = 'cart-item';
    item.innerHTML = `
      <div class="cart-item-info">
        <div class="cart-item-name">${p.name}</div>
        <div class="cart-item-price">${formatPrice(p.price)}</div>
      </div>
      <div class="cart-item-controls">
        <button class="qty-btn minus" data-id="${p.id}">−</button>
        <span class="qty">${qty}</span>
        <button class="qty-btn plus" data-id="${p.id}">+</button>
      </div>
      <div class="cart-item-total">${formatPrice(p.price * qty)}</div>
    `;
    cartItems.appendChild(item);
  }
  
  if (Object.keys(cart).length === 0) {
    cartItems.innerHTML = '<p class="empty-cart">El carrito está vacío</p>';
  }
  
  const totals = computeTotals();
  document.getElementById('cart-subtotal').textContent = formatPrice(totals.subtotal);
  document.getElementById('cart-discount').textContent = totals.discount > 0 ? '−' + formatPrice(totals.discount) : '0,00 €';
  document.getElementById('cart-shipping').textContent = totals.shipping === 0 ? 'Gratis' : formatPrice(totals.shipping);
  document.getElementById('cart-total').textContent = formatPrice(totals.total);
  document.getElementById('cart-count').textContent = itemCount;
}
```

**Event Handling:**
I'll use event delegation for the cart controls.

```js
document.getElementById('cart-items').addEventListener('click', function(e) {
  if (e.target.classList.contains('plus')) {
    const id = Number(e.target.dataset.id);
    addToCart(id, 1);
  } else if (e.target.classList.contains('minus')) {
    const id = Number(e.target.dataset.id);
    changeQty(id, -1);
  }
});
```

For the product buttons, I'll add click handlers.

**Add to cart function:**
```js
function addToCart(id, qty) {
  cart[id] = (cart[id] || 0) + qty;
  renderCart();
  // Micro-animation
  animateAdd(id);
}
```

**Micro-animation:**
When adding, highlight the cart icon and maybe show a brief message.

```js
function animateAdd(id) {
  const btn = document.querySelector(`.product-card[data-id="${id}"] .add-btn`);
  if (btn) {
    btn.classList.remove('pulse');
    void btn.offsetWidth;
    btn.classList.add('pulse');
  }
  const cartIcon = document.querySelector('.cart-icon');
  cartIcon.classList.remove('bounce');
  void cartIcon.offsetWidth;
  cartIcon.classList.add('bounce');
}
```

**Demo:**
```js
function runDemo() {
  setTimeout(() => shopTest.add(1, 1), 500); // Molinillo
  setTimeout(() => shopTest.add(2, 1), 1200); // Cafetera
  setTimeout(() => shopTest.add(3, 2), 1800); // Café x2
  setTimeout(() => shopTest.add(3, 1), 2400); // modify qty of café from 2 to 3
}
```

**Test API:**
```js
window.shopTest = {
  reset() {
    cart = {};
    renderCart();
  },
  add(id, qty) {
    const product = products.find(p => p.id === id);
    if (product) {
      cart[id] = (cart[id] || 0) + qty;
      renderCart();
      animateAdd(id);
    }
  },
  total() {
    renderCart();
    return computeTotals().total;
  }
};
```

Wait, `add(id, qty)` - if qty is not an integer or negative? I'll assume positive integers. The API contract is add(id, qty) so I'll add qty (could be any number). Let me use Math.max(0, Math.floor(qty)) to be safe.

Actually, let me handle it simply:
```js
add(id, qty) {
  const product = products.find(p => p.id === id);
  if (product && typeof qty === 'number' && qty > 0) {
    cart[id] = (cart[id] || 0) + qty;
    renderCart();
    animateAdd(id);
  }
}
```

For the +/- buttons, I'll create a `changeQuantity(id, delta)` function.

**Formatting:**
```js
function formatPrice(amount) {
  return amount.toFixed(2).replace('.', ',') + ' €';
}
```

This will round to 2 decimals and use Spanish format.

**CSS Design:**

Let me design a beautiful page. Colors:
- Primary dark: #2D1B13 (almost black brown)
- Primary: #4E342E (dark brown)
- Accent: #C68B59 (caramel)
- Background: #F7F3EE (light cream)
- Card background: #FFFFFF
- Text: #2D1B13
- Subtle text: #8D6E63

Typography: Georgia or a serif font for headings, sans-serif for body? Actually, let me use system fonts. `font-family: 'Georgia', 'Times New Roman', serif;` for headings and `font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif;` for body.

Let me use a single font family for simplicity: `font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;` and use Georgia for the logo/headings.

I'll add the cart icon as a custom SVG (inline) to avoid emoji rendering issues.

Let me now write the complete HTML file.

**Header:**
```html
<header class="header">
  <div class="logo">
    <svg ...>coffee bean icon</svg>
    <span>Tostadores del Sur</span>
  </div>
  <div class="cart-button" id="cart-button">
    <svg ...>cart icon</svg>
    <span class="cart-count" id="cart-count">0</span>
  </div>
</header>
```

Wait, I should make the cart icon visible. Maybe a fixed panel that's always open? The requirement says "a cart panel". It doesn't specify slide-in or dropdown. I'll make it a fixed aside on the right that's always visible on desktop. On mobile, it could be a slide-in.

For simplicity, I'll do a two-column layout: products on the left, sticky cart on the right.

**Hero:**
```html
<section class="hero">
  <h1>El café de especialidad, en tu mesa</h1>
  <p>Granos de origen, molido perfecto y accesorios de barista</p>
  <a href="#productos" class="hero-btn">Ver productos</a>
</section>
```

**Product Grid:**
```html
<main class="container">
  <section class="products" id="productos">
    <h2>Nuestros productos</h2>
    <div class="product-grid" id="product-grid">
      <!-- cards will be generated by JS -->
    </div>
  </section>
  
  <aside class="cart-panel" id="cart-panel">
    <h2>Tu carrito</h2>
    <div id="cart-items" class="cart-items"></div>
    <div class="cart-summary">
      <div class="summary-row"><span>Subtotal</span><span id="cart-subtotal">0,00 €</span></div>
      <div class="summary-row"><span>Descuento</span><span id="cart-discount">−0,00 €</span></div>
      <div class="summary-row"><span>Envío</span><span id="cart-shipping">Gratis</span></div>
      <div class="summary-row total-row"><span>Total</span><span id="cart-total">0,00 €</span></div>
    </div>
  </aside>
</main>
```

I'll generate the product cards with JS to avoid repetition.

Let me write the complete file now. I need to be careful with the SVG content in JS strings.

Actually, I can put the SVGs as templates in the HTML.

Let me think about how to structure the product cards. Use a data attribute for the product id, and the SVG inside.

**HTML for product card:**
```html
<div class="product-card" data-id="1">
  <div class="product-image">SVG</div>
  <h3>Molinillo manual</h3>
  <div class="product-price">49,90 €</div>
  <button class="add-btn">Añadir</button>
</div>
```

I'll generate all product cards with JS from the products array, including the SVG.

This keeps the HTML clean and makes it easy to attach event handlers.

Let me plan the SVG strings. I'll define them in the products array.

**SVG for each product:** (I'll use a template string)

Let me revise the SVGs to be a bit cleaner. I'll make them with viewBox="0 0 120 120" for more room.

Actually, let me settle on 100x100 viewBox, and CSS will size them to 150x150 or so.

Let me create the SVG strings:

**1. Molinillo manual:**
```
<svg viewBox="0 0 100 100"><rect x="28" y="28" width="44" height="55" rx="6" fill="#8B6F5A"/><rect x="33" y="33" width="34" height="45" rx="3" fill="#D4B896"/><rect x="25" y="23" width="50" height="7" rx="3.5" fill="#5D4037"/><rect x="25" y="30" width="50" height="3" fill="#4E342E"/><circle cx="45" cy="15" r="4" fill="#3E2723"/><rect x="44" y="11" width="2" height="8" fill="#3E2723"/><circle cx="65" cy="10" r="3" fill="#3E2723"/><rect x="47" y="10" width="18" height="2" fill="#3E2723"/><rect x="33" y="65" width="34" height="10" rx="3" fill="#5D4037"/><circle cx="50" cy="70" r="2" fill="#3E2723"/><ellipse cx="50" cy="87" rx="25" ry="3" fill="rgba(0,0,0,0.15)"/></svg>
```

**2. Cafetera espresso:**
```
<svg viewBox="0 0 100 100"><polygon points="30,50 70,50 66,75 34,75" fill="#90A4AE"/><polygon points="34,50 66,50 62,28 38,28" fill="#B0BEC5"/><path d="M37 27 Q50 20 63 27" fill="none" stroke="#78909C" stroke-width="3"/><rect x="33" y="28" width="34" height="3" fill="#546E7A"/><path d="M42 28 Q50 22 58 28 Z" fill="#78909C"/><circle cx="50" cy="21" r="2.5" fill="#455A64"/><path d="M38 30 L20 38 Q15 42 18 50 L22 62 Q25 68 32 64 L44 54" fill="none" stroke="#3E2723" stroke-width="5" stroke-linecap="round"/><path d="M33 52 L26 60" fill="none" stroke="#90A4AE" stroke-width="4" stroke-linecap="round"/><ellipse cx="50" cy="78" rx="25" ry="3" fill="rgba(0,0,0,0.1)"/></svg>
```

**3. Café de Etiopía:**
```
<svg viewBox="0 0 100 100"><path d="M28 22 Q28 15 37 13 L63 13 Q72 15 72 22 L74 80 Q74 87 65 87 L35 87 Q26 87 26 80 Z" fill="#4E342E"/><path d="M26 27 L74 27 L71 37 L29 37 Z" fill="#3E2723"/><rect x="34" y="42" width="32" height="26" rx="4" fill="#FFF3E0"/><path d="M38 54 Q42 50 46 54 Q50 58 54 54 Q58 50 62 54" fill="none" stroke="#5D4037" stroke-width="2"/><ellipse cx="40" cy="34" rx="4" ry="2.5" fill="#8B6F5A"/><ellipse cx="60" cy="34" rx="4" ry="2.5" fill="#6D4C41"/><ellipse cx="50" cy="90" rx="20" ry="3" fill="rgba(0,0,0,0.1)"/></svg>
```

**4. Taza:**
```
<svg viewBox="0 0 100 100"><ellipse cx="45" cy="72" rx="35" ry="7" fill="#BCAAA4"/><path d="M18 38 L23 68 Q24 74 30 74 L60 74 Q66 74 67 68 L72 38 Z" fill="#D7A86E"/><path d="M18 38 L72 38 Q75 38 72 42 L18 42 Z" fill="#BF8F5A"/><ellipse cx="45" cy="38" rx="27" ry="6" fill="#3E2723"/><path d="M72 40 Q85 40 88 50 Q91 60 70 62" fill="none" stroke="#D7A86E" stroke-width="6" stroke-linecap="round"/><path d="M18 50 Q20 58 25 60" fill="none" stroke="#BF8F5A" stroke-width="2"/><ellipse cx="45" cy="38" rx="27" ry="6" fill="none" stroke="#BF8F5A" stroke-width="1.5"/><ellipse cx="45" cy="38" rx="20" ry="4" fill="rgba(255,255,255,0.2)"/></svg>
```

**5. Hervidor:**
```
<svg viewBox="0 0 100 100"><ellipse cx="40" cy="58" rx="28" ry="20" fill="#B0BEC5"/><path d="M15 50 L15 66 Q15 80 40 80 Q65 80 65 66 L65 50 Z" fill="#CFD8DC"/><ellipse cx="40" cy="78" rx="22" ry="4" fill="#90A4AE"/><ellipse cx="40" cy="45" rx="14" ry="5" fill="#78909C"/><circle cx="40" cy="42" r="2.5" fill="#455A64"/><path d="M65 55 Q82 48 85 28 Q86 20 92 16" fill="none" stroke="#B0BEC5" stroke-width="5" stroke-linecap="round"/><path d="M35 38 Q35 22 48 20 Q61 18 58 32" fill="none" stroke="#455A64" stroke-width="4" stroke-linecap="round"/><ellipse cx="40" cy="83" rx="25" ry="3" fill="rgba(0,0,0,0.1)"/></svg>
```

**6. Filtros:**
```
<svg viewBox="0 0 100 100"><path d="M30 33 L35 68 Q40 80 50 80 Q60 80 65 68 L70 33 Z" fill="#FFF8E1"/><ellipse cx="50" cy="35" rx="22" ry="8" fill="#FFF8E1" stroke="#FFCCBC" stroke-width="1.5"/><ellipse cx="50" cy="35" rx="18" ry="6" fill="#FFF3E0" stroke="#FFE0B2" stroke-width="1"/><path d="M50 35 L50 75" stroke="#FFD54F" stroke-width="0.8" stroke-dasharray="3,3"/><path d="M38 33 L36 70" stroke="#FFE0B2" stroke-width="0.8"/><path d="M62 33 L64 70" stroke="#FFE0B2" stroke-width="0.8"/><ellipse cx="50" cy="82" rx="22" ry="3" fill="rgba(0,0,0,0.08)"/></svg>
```

These SVGs look decent. Let me integrate them.

Now, let me design the CSS in detail:

```css
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  background: #F7F3EE;
  color: #2D1B13;
  line-height: 1.6;
}

/* Header */
.header {
  background: #2D1B13;
  color: #F7F3EE;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-family: Georgia, serif;
  font-size: 1.5rem;
  font-weight: bold;
}

.logo svg { width: 40px; height: 40px; }

.cart-button {
  position: relative;
  background: none;
  border: none;
  cursor: pointer;
  color: #F7F3EE;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1.2rem;
}

.cart-count {
  background: #C68B59;
  border-radius: 50%;
  padding: 2px 8px;
  font-size: 0.9rem;
  font-weight: bold;
}

/* Hero */
.hero {
  text-align: center;
  padding: 4rem 2rem;
  background: linear-gradient(135deg, #4E342E, #2D1B13);
  color: #F7F3EE;
}

.hero h1 {
  font-family: Georgia, serif;
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
}

.hero p {
  font-size: 1.1rem;
  opacity: 0.8;
  margin-bottom: 1.5rem;
}

.hero-btn {
  display: inline-block;
  background: #C68B59;
  color: #2D1B13;
  padding: 0.75rem 2rem;
  border-radius: 30px;
  text-decoration: none;
  font-weight: bold;
  transition: transform 0.2s, background 0.2s;
}

.hero-btn:hover {
  transform: scale(1.05);
  background: #D7A86E;
}

/* Container */
.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
  display: grid;
  grid-template-columns: 1fr 350px;
  gap: 2rem;
  align-items: start;
}

/* Products section */
.products h2 {
  font-family: Georgia, serif;
  margin-bottom: 1.5rem;
  color: #4E342E;
  font-size: 1.8rem;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
}

.product-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  transition: transform 0.2s, box-shadow 0.2s;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.product-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(0,0,0,0.1);
}

.product-image {
  width: 150px;
  height: 150px;
  margin: 0 auto 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.product-image svg {
  width: 100%;
  height: 100%;
}

.product-card h3 {
  font-size: 1.05rem;
  margin-bottom: 0.25rem;
  color: #2D1B13;
}

.product-price {
  font-weight: bold;
  color: #5D4037;
  font-size: 1.15rem;
  margin-bottom: 1rem;
}

.add-btn {
  background: #4E342E;
  color: white;
  border: none;
  padding: 0.5rem 2rem;
  border-radius: 25px;
  cursor: pointer;
  font-size: 0.95rem;
  transition: background 0.2s, transform 0.2s;
  width: 100%;
  max-width: 160px;
}

.add-btn:hover {
  background: #5D4037;
  transform: scale(1.03);
}

.add-btn.pulse {
  animation: pulse 0.4s ease;
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}

/* Cart panel */
.cart-panel {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
  position: sticky;
  top: 90px;
  max-height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
}

.cart-panel h2 {
  font-family: Georgia, serif;
  color: #4E342E;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid #F0EBE5;
}

.cart-items {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 1rem;
  min-height: 50px;
}

.cart-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.6rem 0;
  border-bottom: 1px solid #F5F0EA;
  gap: 8px;
}

.cart-item-info {
  flex: 1;
  min-width: 0;
}

.cart-item-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: #2D1B13;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.cart-item-price {
  font-size: 0.8rem;
  color: #8D6E63;
}

.cart-item-controls {
  display: flex;
  align-items: center;
  gap: 4px;
}

.qty-btn {
  width: 24px;
  height: 24px;
  border: 1px solid #D4C8BC;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
  line-height: 1;
  color: #4E342E;
}

.qty-btn:hover {
  background: #F0EBE5;
}

.qty {
  font-size: 0.9rem;
  font-weight: bold;
  width: 20px;
  text-align: center;
}

.cart-item-total {
  font-size: 0.85rem;
  font-weight: 600;
  min-width: 55px;
  text-align: right;
}

.empty-cart {
  color: #8D6E63;
  text-align: center;
  padding: 1.5rem 0;
  font-style: italic;
}

.cart-summary {
  border-top: 2px solid #F0EBE5;
  padding-top: 0.75rem;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.4rem;
  font-size: 0.9rem;
  color: #4E342E;
}

.summary-row.total-row {
  font-weight: bold;
  font-size: 1.2rem;
  border-top: 1px solid #F0EBE5;
  padding-top: 0.5rem;
  margin-top: 0.5rem;
  color: #2D1B13;
}

/* Animations */
.cart-button.bounce .cart-container {
  animation: bounce 0.4s ease;
}

@keyframes bounce {
  0%, 100% { transform: scale(1); }
  30% { transform: scale(1.2); }
  60% { transform: scale(1.5); }
}

/* Toast */
.toast {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background: #4E342E;
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  opacity: 0;
  transform: translateY(100px);
  transition: all 0.3s ease;
  z-index: 1000;
}

.toast.show {
  opacity: 1;
  transform: translateY(0);
}

/* Responsive */
@media (max-width: 1024px) {
  .container { grid-template-columns: 1fr; }
  .cart-panel { position: static; max-height: none; }
}

@media (max-width: 768px) {
  .product-grid { grid-template-columns: 1fr 1fr; }
  .hero h1 { font-size: 1.8rem; }
}

@media (max-width: 480px) {
  .product-grid { grid-template-columns: 1fr; }
}
```

Wait, the `cart-button.bounce .cart-container` animation. Maybe I should simplify. Let me add a bounce directly to the `.cart-button` class.

Actually, let me define the cart icon with a span wrapper so the animation is cleaner.

Let me think about the header cart icon. I'll use an SVG shopping cart icon.

**Cart SVG icon:**
```svg
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M3 3h2l.4 2M7 13h10l4-8H5.4"/>
  <circle cx="9" cy="21" r="1"/>
  <circle cx="17" cy="21" r="1"/>
  <path d="M17 13H5l-1 5h13"/>
</svg>
```

Actually let me make a simpler cart icon:
```svg
<svg width="25" height="25" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
  <path d="M6 6h15l-2 7H8L6 6z"/>
  <circle cx="9" cy="20" r="1.5"/>
  <circle cx="18" cy="20" r="1.5"/>
</svg>
```

**Logo icon:**
A coffee bean:
```svg
<svg viewBox="0 0 40 40">
  <ellipse cx="20" cy="20" rx="12" ry="16" fill="#6D4C41"/>
  <path d="M20 4 Q28 10 28 20 Q28 30 20 36 Q12 30 12 20 Q12 10 20 4" fill="#4E342E"/>
  <path d="M16 12 Q20 18 16 24" fill="none" stroke="#C68B59" stroke-width="2" stroke-linecap="round"/>
</svg>
```

Hmm, a coffee bean as a logo. Let me simplify:
```svg
<svg viewBox="0 0 40 40">
  <ellipse cx="20" cy="20" rx="14" ry="18" fill="#6D4C41"/>
  <path d="M20 2 Q26 10 26 20 Q26 30 20 38 Q14 30 14 20 Q14 10 20 2 Z" fill="#4E342E"/>
  <path d="M16 14 Q20 20 16 26" fill="none" stroke="#C68B59" stroke-width="2.5" stroke-linecap="round"/>
</svg>
```

Alright, I have enough details. Let me write the complete HTML file now.

Actually, let me reconsider the layout. In the header, I want to show:
- Logo (coffee bean icon + text)
- Cart summary (maybe "🛒 X items")

The cart panel is on the right side as an aside.

Let me also add a subtle toast notification when items are added.

For the product grid, I need to generate the cards. Let me define the products data as a JS array with an `svg` field.

**Complete JS:**

```js
const products = [
  { id: 1, name: 'Molinillo manual', price: 49.90, svg: `...` },
  { id: 2, name: 'Cafetera espresso', price: 89.00, svg: `...` },
  { id: 3, name: 'Café de Etiopía 250 g', price: 12.50, svg: `...` },
  { id: 4, name: 'Taza de cerámica', price: 8.90, svg: `...` },
  { id: 5, name: 'Hervidor cuello de cisne', price: 39.00, svg: `...` },
  { id: 6, name: 'Filtros de papel x100', price: 5.50, svg: `...` }
];
```

Let me carefully encode the SVG strings. I'll use template literals.

Actually, these SVG strings are long. Let me put them in the HTML as `<template>` elements or just inline in the JS.

I'll inline them in the JS using template strings. The SVGs use double quotes for attributes; that's fine inside a template string.

Let me write the cart icon in the header:
```html
<button class="cart-button" id="cart-button">
  <svg viewBox="0 0 24 24" width="25" height="25" fill="none" stroke="currentColor" stroke-width="2">
    <path d="M6 6h15l-2 7H8L6 6z"/>
    <path d="M6 6L4 3"/>
    <circle cx="9" cy="20" r="1.5"/>
    <circle cx="18" cy="20" r="1.5"/>
    <path d="M8 20H19" stroke-linecap="round"/>
  </svg>
  <span class="cart-count" id="cart-count">0</span>
</button>
```

Wait, the cart icon should be functional? The requirement doesn't say to make the cart icon toggle the panel, since the panel is always visible. So I'll just show it as a display.

Now let me carefully put everything together. I need to make sure:
1. Products are rendered
2. Add to cart works via buttons
3. + / - buttons in cart work
4. Auto demo runs
5. Test API works

Also, I want the "Discout" row to show "−0,00 €" when no discount? Better to show "−0,00 €" always, or "No aplicado". I'll just show the amount, which is 0 when no discount.

Actually, subtracting 0 looks odd. Let me show a styled discount only when > 0, otherwise show "—". Let me simplify: always show the discount amount, even if 0.

But in many e-commerce sites, the discount line is hidden when there's no discount. I'll show it but with a 0 value. Let me show it as "Descuento" and the value "0,00 €". That's fine.

When there's no discount, `Math.round(0 * 100) / 100 = 0`, so it shows "0,00 €".

For shipping: show "Gratis" if 0, else the price.

Let me now produce the final HTML.

**Important: Anchoring to "Ver productos" button uses `href="#productos"` which will scroll to the products section. I need to give the products section an id.**

Let me also add a small toast notification when an item is added:
```js
function showToast(message) {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.classList.add('show');
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => toast.classList.remove('show'), 1500);
}
```

OK let me combine all this into a single HTML response.

Wait, I also want to handle the case when quantity is decreased to zero and removed. The filter will remove it from the cart object.

`changeQty(id, delta)`:
```js
function changeQty(id, delta) {
  if (!cart[id]) return;
  cart[id] += delta;
  if (cart[id] <= 0) {
    delete cart[id];
  }
  renderCart();
}
```

For the demo, I need to change a quantity. I can use `changeQty` directly in the demo.

Demo:
```js
function runDemo() {
  // Add items with delays to show the animation
  setTimeout(() => shopTest.add(1, 1), 400);
  setTimeout(() => shopTest.add(2, 1), 1000);
  setTimeout(() => shopTest.add(3, 2), 1600);
  setTimeout(() => changeQty(3, 1), 2200); // Increase Café from 2 to 3
}
```

Wait, `changeQty(3, 1)` will increase the qty from 2 to 3 (delta = +1). That's a "change quantity" action.

Let me also update the test API to have a `changeQty` function? The requirement only mentions `reset`, `add`, `total`. I'll keep those three.

`shopTest.add(id, qty)` - adds qty to the existing. So `shopTest.add(3, 1)` will add 1 more Café.

For the demo "changes a quantity", I can use `shopTest.add(3, 1)` which changes the quantity from 2 to 3. That qualifies.

Let me now write the complete file. I'll be thorough with the CSS and JS.

One more thing: the toast notification. Let me include it.

**Final plan:**

```html
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Tostadores del Sur</title>
<style>
  /* CSS */
</style>
</head>
<body>
<header class="header">
  <div class="logo">
    <svg>...</svg>
    <span>Tostadores del Sur</span>
  </div>
  <div class="cart-button">
    <svg>...</svg>
    <span class="cart-count" id="cart-count">0</span>
  </div>
</header>

<section class="hero">
  <h1>...</h1>
  <p>...</p>
  <a href="#productos" class="hero-btn">Ver productos</a>
</section>

<main class="container">
  <section class="products" id="productos">
    <h2>...</h2>
    <div class="product-grid" id="product-grid"></div>
  </section>
  <aside class="cart-panel">
    <h2>Tu carrito</h2>
    <div class="cart-items" id="cart-items"></div>
    <div class="cart-summary">
      <div class="summary-row">
        <span>Subtotal</span>
        <span id="cart-subtotal">0,00 €</span>
      </div>
      <div class="summary-row">
        <span>Descuento</span>
        <span id="cart-discount">0,00 €</span>
      </div>
      <div class="summary-row">
        <span>Envío</span>
        <span id="cart-shipping">Gratis</span>
      </div>
      <div class="summary-row total-row">
        <span>Total</span>
        <span id="cart-total">0,00 €</span>
      </div>
    </div>
  </aside>
</main>

<div class="toast" id="toast"></div>

<script>
  // JS
</script>
</body>
</html>
```

Now let me flesh out all the JS. I'll render the products dynamically.

Let me write the code step by step in my response.

Actually, let me think about the SVG for each product card. I want the SVGs to be visually appealing. Let me refine the SVGs into a slightly more polished state.

Actually, I realize I should also make sure the discount line is clear. Let me display:
- Subtotal: "33,40 €"
- Descuento: "0,00 €" (or "−3,34 €" when applicable)
- Envío: "Gratis" or "4,95 €"
- Total: the final

For the discount display, if discount is > 0, show "−" + price. If not, just show "0,00 €" or "—"? I'll show "−0,00 €" when 0, which is not great. Let me just show the formatted number without minus sign for the discount row, but with the convention that it's a deduction. Actually, in e-commerce, the discount row shows a positive number and the label "Descuento" makes it clear it's deducted. So I'll show the numeric value without a minus sign.

But visually, I want to make the discount stand out when it's applied. Maybe show it in green? Let me keep it simple and just show the value.

Actually, I'll format it as: if discount > 0, show `− X,XX €` (with minus), else show `0,00 €`. When there's a discount, it's a deduction.

OK, I'm overthinking. Let me just use `formatPrice(discount)` and if it's 0, show `0,00 €`. The label says "Descuento", so the meaning is clear.

Now, let me make sure the shipping logic is correct: free shipping if `afterDiscount >= 60` OR `afterDiscount === 0` (empty cart). If afterDiscount > 0 and < 60, charge 4.95.

Let me verify with the demo:
1. Molinillo: 49.90
   - afterDiscount: 49.90, discount: 0, shipping: 4.95 (49.90 < 60)
   - total: 49.90 + 4.95 = 54.85
2. + Cafetera: 49.90 + 89.00 = 138.90
   - discount: subtotal >= 100, so discount = 13.89
   - afterDiscount: 138.90 - 13.89 = 125.01
   - shipping: free (125.01 >= 60)
   - total: 125.01
3. + Café x2: subtotal = 138.90 + 25 = 163.90
   - discount: 16.39
   - afterDiscount: 147.51
   - shipping: free
   - total: 147.51
4. + Café x1 more (qty 2->3): subtotal = 163.90 + 12.50 = 176.40
   - discount: 17.64
   - afterDiscount: 158.76
   - shipping: free
   - total: 158.76

That's a nice progression. Let me use this demo sequence.

Wait, for the demo, I'll have:
1. `shopTest.add(1, 1)` - Molinillo, subtotal 49.90, shipping 4.95, total 54.85
2. `shopTest.add(2, 1)` - + Cafetera, subtotal 138.90, discount 13.89, free shipping, total 125.01
3. `shopTest.add(3, 2)` - + Café x2, subtotal 163.90, discount 16.39, total 147.51
4. `shopTest.add(3, 1)` - + Café x1 (qty changes 2->3), subtotal 176.40, discount 17.64, total 158.76

That's a nice demo covering discount, shipping thresholds, and quantity changes.

Alright, let me now produce the final HTML.

One more detail: the product card button should say "Añadir" for all products. When clicked, it adds 1.

For event delegation on the product grid:
```js
document.getElementById('product-grid').addEventListener('click', function(e) {
  const btn = e.target.closest('.add-btn');
  if (btn) {
    const id = Number(btn.dataset.id);
    addToCart(id, 1);
  }
});
```

OK. Now let me write it all.

Actually, I need to include the SVG strings in the products array. These are multi-line template strings. Let me make sure the indentation is correct and there are no backticks inside.

Since I'm writing the SVGs with double quotes for attributes and the template strings use backticks, it should be fine.

Let me also add a `.product-tag` or badge? Not necessary.

Let me finalize the CSS and make it look polished.

The toast: I realize I should include it in the HTML:
```html
<div class="toast" id="toast"></div>
```

And show a message like "Añadido al carrito ✓".

OK, let me write the complete file now. This will be a comprehensive implementation.

Actually, there's a problem: the SVG strings in JS template literals. If the SVG contains `${...}`, it would be interpreted. Since my SVGs use `${...}`? No, they don't use `${` at all, so it's safe.

Let me also consider: the product cards should have consistent heights. The `.product-card` has `display: flex; flex-direction: column;` and the `.add-btn` at the bottom with `margin-top: auto;`.

OK, here's the final code:

Wait, let me also add a small feature: when the cart is empty, the summary shows 0. When items are in the cart, it shows the correct values.

Also, the cart panel should have a max height and scroll for the items list, so the summary stays visible.

```css
.cart-items {
  flex: 1;
  overflow-y: auto;
  min-height: 80px;
  max-height: 300px;
}
```

Alright. Let me write it.

Hmm, I also notice I need to update the `renderCart` function to show the discount row nicely. Let me do:

```js
const discountEl = document.getElementById('cart-discount');
if (totals.discount > 0) {
  discountEl.textContent = '−' + formatPrice(totals.discount);
  discountEl.style.color = '#C62828';
} else {
  discountEl.textContent = '0,00 €';
  discountEl.style.color = '';
}
```

That's a nice touch.

For shipping:
```js
const shipEl = document.getElementById('cart-shipping');
if (totals.shipping === 0) {
  if (Object.keys(cart).length === 0) {
    shipEl.textContent = '—';
  } else {
    shipEl.textContent = 'Gratis';
  }
} else {
  shipEl.textContent = formatPrice(totals.shipping);
}
```

Alright. Let me write the response now. I'll organize it as a single HTML file.

Let me double check the `computeTotals` function:

```js
function computeTotals() {
  let subtotal = 0;
  for (const id in cart) {
    const product = products.find(p => p.id === Number(id));
    if (product) {
      subtotal += product.price * cart[id];
    }
  }
  subtotal = Math.round(subtotal * 100) / 100;
  const discount = subtotal >= 100 ? Math.round(subtotal * 0.10 * 100) / 100 : 0;
  const afterDiscount = Math.round((subtotal - discount) * 100) / 100;
  const shipping = (afterDiscount > 0 && afterDiscount < 60) ? 4.95 : 0;
  const total = Math.round((afterDiscount + shipping) * 100) / 100;
  return { subtotal, discount, afterDiscount, shipping, total };
}
```

This should be precise. `discount = Math.round(subtotal * 0.10 * 100) / 100` gives the discount rounded to cents. `afterDiscount = Math.round((subtotal - discount) * 100) / 100`.

Wait, but if subtotal is 163.90, discount = 16.39, afterDiscount = 147.51. That's correct.

But what if subtotal = 100.00? discount = Math.round(10.00) = 10.00, afterDiscount = 90.00, shipping = 4.95 (90 < 60? No, 90 >= 60, so free). That's wrong in this case. Actually, afterDiscount = 90, which is >= 60, so free shipping. That's fine.

Wait, if afterDiscount >= 60, shipping is free. So even if subtotal = 100, discount = 10, afterDiscount = 90, shipping is free because 90 >= 60.

What if subtotal is 55 and discount is 0, afterDiscount = 55, shipping = 4.95 because 55 < 60. Yes.

What if subtotal = 120, discount = 12, afterDiscount = 108, shipping free. Good.

Now, let me also consider a case where subtotal is 45, after shipping 49.95 — no discount, so shipping applies. That's intended per my logic.

Hmm, but maybe the free shipping threshold should be on the *original* subtotal or the *discounted* subtotal? Typically, free shipping is based on the subtotal before discounts. But the requirement doesn't specify. I'll use afterDiscount to be consistent: shipping is calculated on the amount to be paid before shipping.

Actually, let me re-read the requirement: "applying the same rules". There are no specific rules given about free shipping threshold. I'll define it myself: free shipping if order total (after discounts) >= 50€, otherwise 4.95€. Hmm, but I already defined it at >= 60. Let me set a nice round number: 50€ free shipping threshold feels common. But in the demo, after the molinillo alone (49.90), it's just under 50, so shipping would be 4.95. After adding the cafetera (138.90 before discount, 125.01 after discount), free shipping. That works well.

Let me change the threshold to 50€ for realism:
- If afterDiscount > 0 and afterDiscount < 50: shipping = 4.95
- If afterDiscount >= 50: shipping = 0

With the demo:
1. Molinillo: afterDiscount = 49.90 < 50, so shipping = 4.95, total = 54.85
2. + Cafetera: afterDiscount = 125.01 >= 50, free shipping, total = 125.01

Yes, let me use 50€ as the free shipping threshold.

But wait, the "Molinillo" at 49.90 + shipping = 54.85. After that, adding anything will cross 50 and get free shipping. That's fine.

Actually, let me make the threshold at 60€ just to be on the side where most orders with a discount get free shipping anyway. Actually 50 is fine and more aligned with typical e-commerce.

Let me go with 60€ to be more interesting: if the user orders a single item at, say, 55€, they pay shipping. If they reach 60€, free. With the molinillo at 49.90, after discount it's < 60, so shipping applies. But as soon as they add more items and the total is > 60, free shipping.

OK let me use 60. Whatever I choose, it's consistent.

Actually, I realize the demo would show: after adding the molinillo (49.90), shipping = 4.95 (since 49.90 < 60), total 54.85. Then after adding cafetera (total afterDiscount = 125.01), free shipping. That's fine.

OK, 60 it is.

Let me finalize:

```js
const FREE_SHIPPING_THRESHOLD = 60; // €
const SHIPPING_COST = 4.95; // €
```

So:
```js
const shipping = (afterDiscount > 0 && afterDiscount < FREE_SHIPPING_THRESHOLD) ? SHIPPING_COST : 0;
```

Perfect.

Now let me write the final HTML. I need to be very careful with the SVG content inside JS.

Let me also ensure the product images are responsive.

One last thing: I should add `margin-top: auto` to the `.add-btn` in the product card so that cards with different description lengths have aligned buttons.

```css
.product-card .add-btn {
  margin-top: auto;
}
```

Actually, the product cards already have `display: flex; flex-direction: column; align-items: center;`. The `h3`, `.product-price`, `.add-btn` are block elements. With `margin-top: auto` on the button, the price will push to the bottom... but I want the price and button to be at the bottom. Let me use:

```css
.product-card {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.product-card h3 {
  margin-top: 0.75rem;
}

.product-card .add-btn {
  margin-top: auto;
}
```

And add `.product-card h3 + .product-price { margin-top: 0.25rem; }`.

This will align cards nicely.

OK, let me also create the SVG for the cart icon in the header.

**Cart Icon SVG:**
```html
<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="9" cy="21" r="1.5"></circle>
  <circle cx="18" cy="21" r="1.5"></circle>
  <path d="M2 3h2l.4 2M17 11H5l-1.2-5H2"></path>
  <path d="M6 21h10"></path>
</svg>
```

That's the Feather icon style.

**Logo Icon:** I'll use a coffee bean SVG:
```html
<svg viewBox="0 0 40 40" width="40" height="40">
  <ellipse cx="20" cy="20" rx="14" ry="18" fill="#C68B59"/>
  <path d="M20 2 Q26 10 26 20 Q26 30 20 38 Q14 30 14 20 Q14 10 20 2 Z" fill="#8B5A2B"/>
  <path d="M20 6 Q23 12 23 20 Q23 28 20 34" stroke="#C68B59" stroke-width="1.5" fill="none" stroke-linecap="round"/>
</svg>
```

Hmm, a coffee bean logo might be complex. Let me just use a simple coffee cup icon:

```html
<svg viewBox="0 0 40 40" width="40" height="40">
  <rect x="8" y="14" width="20" height="16" rx="2" fill="#C68B59"/>
  <path d="M28 16h2.5a3 3 0 0 1 0 6H28" fill="none" stroke="#C68B59" stroke-width="2"/>
  <path d="M12 20 Q16 24 20 20 Q24 16 28 20" stroke="#FFF3E0" stroke-width="1.5" fill="none"/>
</svg>
```

Actually, let me keep it simple: the logo can be just the text "Tostadores del Sur" with maybe a small icon. I'll use a simple coffee bean emoji-like SVG:

```svg
<svg viewBox="0 0 40 40" width="40" height="40">
  <ellipse cx="20" cy="20" rx="14" ry="18" fill="#6D4C41"/>
  <path d="M20 2 Q26 12 26 20 Q26 28 20 38 Q14 28 14 20 Q14 12 20 2 Z" fill="#2D1B13"/>
  <path d="M17 8 Q20 15 17 22" stroke="#C68B59" stroke-width="2" fill="none" stroke-linecap="round"/>
</svg>
```

This looks like a coffee bean. OK.

Actually, for clarity and robustness, let me use a simpler logo. Maybe a text-based logo with a Unicode coffee symbol? No, let me use an SVG.

I'll design the logo as a filled coffee cup:

```svg
<svg viewBox="0 0 40 40" width="40" height="40">
  <!-- Cup -->
  <path d="M10 18 Q10 30 20 30 Q30 30 30 18 Z" fill="#C68B59"/>
  <!-- Coffee line -->
  <path d="M10 18 Q20 22 30 18" fill="#2D1B13" opacity="0.6"/>
  <!-- Steam -->
  <path d="M15 12 Q13 8 16 5" fill="none" stroke="#C68B59" stroke-width="2" stroke-linecap="round"/>
  <path d="M22 12 Q20 8 23 5" fill="none" stroke="#C68B59" stroke-width="2" stroke-linecap="round"/>
</svg>
```

That might be more recognizable as a logo. Let me use this.

OK, I'm going to stop overthinking the logo and just use it.

Now, let me write the complete file. I'll produce it as a single HTML file with embedded CSS and JS.

One more consideration: the products will be displayed with names in Spanish:
1. Molinillo manual (Hand grinder) - 49.90€
2. Cafetera espresso (Espresso maker) - 89.00€
3. Café de Etiopía 250 g - 12.50€
4. Taza de cerámica (Ceramic mug) - 8.90€
5. Hervidor cuello de cisne (Gooseneck kettle) - 39.00€
6. Filtros de papel x100 - 5.50€

These are reasonable prices for coffee products.

OK, I'll now write the final code. Because this is a comprehensive implementation, the code will be quite long. I'll structure it well with comments.

Actually, let me re-evaluate my SVG strings. I want them to be polished and centered in their containers. Let me give each a common format:

```svg
<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">...</svg>
```

This will ensure they all display at the same size when given CSS `width: 150px; height: 150px`.

Let me finalize each SVG one more time to make sure the quality is good. I've already designed them above. Let me use those.

There was a slight issue: in some SVGs, I used `rgba(0,0,0,0.1)` inside `<ellipse>` which is a CSS function, but it's not allowed in SVG attributes. The correct way is `fill="rgba(0,0,0,0.1)"` — actually, SVG supports `rgba()` in presentation attributes? No, it doesn't. It supports `fill="black"` with `fill-opacity="0.1"`. 

So for shadows, I should use:
```svg
<ellipse cx="50" cy="87" rx="25" ry="3" fill="black" opacity="0.1"/>
```

That's more correct. Let me update the SVGs to use this patterns.

I'll update each shadow:
- `<ellipse cx="50" cy="87" rx="25" ry="3" fill="black" opacity="0.12"/>`

And for gradients/highlights, use `opacity` as well.

Also, for the coffee mug's highlight on the saucer, I used `fill="rgba(255,255,255,0.2)"`. I'll replace with `fill="white" opacity="0.2"`.

OK let me define the corrected SVG strings:

**1. Molinillo manual:**
```
<svg viewBox="0 0 100 100"><rect x="28" y="25" width="44" height="55" rx="6" fill="#8D6E63"/><rect x="33" y="30" width="34" height="45" rx="3" fill="#D7A86E"/><rect x="25" y="22" width="50" height="7" rx="3.5" fill="#5D4037"/><rect x="25" y="29" width="50" height="3" fill="#3E2723"/><circle cx="45" cy="15" r="4" fill="#3E2723"/><rect x="44" y="11" width="2" height="6" fill="#3E2723"/><circle cx="64" cy="9" r="3" fill="#3E2723"/><rect x="46" y="9" width="18" height="2" fill="#3E2723"/><rect x="33" y="62" width="34" height="12" rx="3" fill="#4E342E"/><rect x="35" y="64" width="30" height="8" rx="2" fill="#5D4037"/><circle cx="50" cy="68" r="2" fill="#3E2723"/><ellipse cx="50" cy="85" rx="25" ry="3" fill="black" opacity="0.12"/></svg>
```

**2. Cafetera espresso:**
```
<svg viewBox="0 0 100 100"><polygon points="30,50 70,50 66,75 34,75" fill="#90A4AE"/><polygon points="34,50 66,50 62,28 38,28" fill="#B0BEC5"/><path d="M37 28 Q50 22 63 28" fill="none" stroke="#78909C" stroke-width="3"/><rect x="33" y="28" width="34" height="3" fill="#546E7A"/><path d="M40 26 Q50 20 60 26 Q50 22 40 26 Z" fill="#78909C"/><circle cx="50" cy="21" r="2.5" fill="#455A64"/><path d="M38 30 L20 38 Q15 42 18 50 L22 62 Q25 68 32 64 L44 54" fill="none" stroke="#3E2723" stroke-width="5" stroke-linecap="round"/><path d="M33 52 L26 60" fill="none" stroke="#90A4AE" stroke-width="4" stroke-linecap="round"/><ellipse cx="50" cy="78" rx="25" ry="3" fill="black" opacity="0.1"/></svg>
```

**3. Café de Etiopía:**
```
<svg viewBox="0 0 100 100"><path d="M28 22 Q28 15 37 13 L63 13 Q72 15 72 22 L74 80 Q74 87 65 87 L35 87 Q26 87 26 80 Z" fill="#4E342E"/><path d="M26 27 L74 27 L71 37 L29 37 Z" fill="#3E2723"/><rect x="34" y="42" width="32" height="26" rx="4" fill="#FFF3E0"/><path d="M38 54 Q42 50 46 54 Q50 58 54 54 Q58 50 62 54" fill="none" stroke="#5D4037" stroke-width="2" stroke-linecap="round"/><ellipse cx="40" cy="34" rx="4" ry="2.5" fill="#8B6F5A"/><ellipse cx="60" cy="34" rx="4" ry="2.5" fill="#6D4C41"/><ellipse cx="50" cy="90" rx="20" ry="3" fill="black" opacity="0.12"/></svg>
```

**4. Taza de cerámica:**
```
<svg viewBox="0 0 100 100"><ellipse cx="45" cy="72" rx="35" ry="7" fill="#BCAAA4"/><path d="M18 36 L23 68 Q24 74 30 74 L60 74 Q66 74 67 68 L72 36 Z" fill="#D7A86E"/><path d="M18 36 Q45 42 72 36" fill="none" stroke="#BF8F5A" stroke-width="2"/><ellipse cx="45" cy="36" rx="27" ry="6" fill="#3E2723"/><path d="M72 38 Q85 38 88 50 Q91 60 70 62" fill="none" stroke="#D7A86E" stroke-width="6" stroke-linecap="round"/><ellipse cx="45" cy="36" rx="27" ry="6" fill="none" stroke="#BF8F5A" stroke-width="1.5"/><ellipse cx="45" cy="35" rx="20" ry="4" fill="white" opacity="0.15"/><ellipse cx="45" cy="72" rx="25" ry="5" fill="black" opacity="0.05"/></svg>
```

**5. Hervidor cuello de cisne:**
```
<svg viewBox="0 0 100 100"><ellipse cx="40" cy="58" rx="28" ry="20" fill="#B0BEC5"/><path d="M15 50 L15 66 Q15 80 40 80 Q65 80 65 66 L65 50 Z" fill="#CFD8DC"/><ellipse cx="40" cy="78" rx="22" ry="4" fill="#90A4AE"/><ellipse cx="40" cy="45" rx="14" ry="5" fill="#78909C"/><circle cx="40" cy="42" r="2.5" fill="#455A64"/><path d="M65 55 Q82 48 85 28 Q86 20 92 16" fill="none" stroke="#B0BEC5" stroke-width="5" stroke-linecap="round"/><path d="M35 38 Q35 22 48 20 Q61 18 58 32" fill="none" stroke="#455A64" stroke-width="4" stroke-linecap="round"/><ellipse cx="40" cy="83" rx="25" ry="3" fill="black" opacity="0.1"/></svg>
```

**6. Filtros de papel:**
```
<svg viewBox="0 0 100 100"><path d="M30 33 L35 68 Q40 80 50 80 Q60 80 65 68 L70 33 Z" fill="#FFF8E1"/><ellipse cx="50" cy="35" rx="22" ry="8" fill="#FFF8E1" stroke="#FFCCBC" stroke-width="1.5"/><ellipse cx="50" cy="35" rx="18" ry="6" fill="#FFF3E0" stroke="#FFE0B2" stroke-width="1"/><path d="M50 35 L50 75" stroke="#FFD54F" stroke-width="0.8" stroke-dasharray="3,3"/><path d="M38 33 L36 70" stroke="#FFE0B2" stroke-width="0.8"/><path d="M62 33 L64 70" stroke="#FFE0B2" stroke-width="0.8"/><ellipse cx="50" cy="82" rx="22" ry="3" fill="black" opacity="0.08"/></svg>
```

These corrected SVGs use `fill="black" opacity="0.1"` instead of `rgba()`, which ensures compatibility.

Now, let me also create a coffee bean SVG for the logo. Here is a simple one:

```html
<svg viewBox="0 0 40 40">
  <ellipse cx="20" cy="20" rx="14" ry="18" fill="#C68B59"/>
  <path d="M20 2 Q26 10 26 20 Q26 30 20 38 Q14 30 14 20 Q14 10 20 2 Z" fill="#4E342E"/>
  <path d="M17 8 Q20 16 17 24" stroke="#C68B59" stroke-width="2" fill="none" stroke-linecap="round"/>
</svg>
```

And the cart icon:
```html
<svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="9" cy="21" r="1.5"></circle>
  <circle cx="18" cy="21" r="1.5"></circle>
  <path d="M2 3h2l2.5 12h11l2-8H4"></path>
</svg>
```

OK. I'm ready to write the complete file. Let me put it all together.

Note: I'll need to escape the backslashes in the SVG paths? No, they are not regex, they're just strings. In JS template literals, `\` might need escaping. But my SVG strings use `\` ? No, they don't. They use quotes and slashes, no backslashes. Good.

Wait, in the SVG path data, `M` and `L` are SVG commands and `\` is not used. So the strings are fine.

Also, I need to be careful about the `/>` in SVG self-closing tags inside the HTML template strings. That should be fine.

Let me also add proper meta description and language attributes.

Here's my final plan:

```
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tostadores del Sur — Tienda de café</title>
  <style>
    /* all CSS */
  </style>
</head>
<body>
  <!-- Header -->
  <!-- Hero -->
  <!-- Main: products + cart -->
  <!-- Toast -->
  
  <script>
    // All JS
  </script>
</body>
</html>
```

Let me now produce this final response. I'll make it comprehensive and complete.