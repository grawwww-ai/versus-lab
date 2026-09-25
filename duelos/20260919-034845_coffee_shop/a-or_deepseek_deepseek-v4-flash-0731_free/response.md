I've created a one-page coffee shop demo with a simple cart, product grid, and an interactive shopping flow.
```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tostadores del Sur — Tienda de café</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: #f7f3ee;
            color: #2d1b13;
            line-height: 1.6;
        }
        a {
            text-decoration: none;
        }

        /* HEADER */
        .header {
            background: #2d1b13;
            color: #f7f3ee;
            padding: 0.9rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 200;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.25);
        }
        .logo {
            display: flex;
            align-items: center;
            gap: 0.6rem;
            font-family: Georgia, serif;
            font-size: 1.4rem;
            font-weight: bold;
            letter-spacing: 0.5px;
        }
        .logo svg {
            width: 38px;
            height: 38px;
        }
        .cart-button {
            display: flex;
            align-items: center;
            gap: 10px;
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 30px;
            padding: 0.4rem 1.2rem;
            color: #f7f3ee;
            font-size: 0.95rem;
            font-weight: 600;
            cursor: default;
            transition: background 0.2s;
        }
        .cart-button:hover {
            background: rgba(255, 255, 255, 0.15);
        }
        .cart-count {
            background: #c68b59;
            border-radius: 50%;
            padding: 1px 9px;
            font-size: 0.85rem;
            font-weight: bold;
            transition: transform 0.2s;
        }
        .cart-button.bounce .cart-count {
            animation: cart-bump 0.4s ease;
        }
        @keyframes cart-bump {
            0%,
            100% {
                transform: scale(1);
            }
            50% {
                transform: scale(1.35);
            }
        }

        /* HERO */
        .hero {
            text-align: center;
            padding: 4rem 2rem;
            background: linear-gradient(135deg, #4e342e, #2d1b13);
            color: #f7f3ee;
        }
        .hero h1 {
            font-family: Georgia, serif;
            font-size: 2.4rem;
            margin-bottom: 0.3rem;
            letter-spacing: 0.5px;
        }
        .hero p {
            font-size: 1.1rem;
            opacity: 0.8;
            margin-bottom: 1.6rem;
        }
        .hero-btn {
            display: inline-block;
            background: #c68b59;
            color: #2d1b13;
            padding: 0.75rem 2.2rem;
            border-radius: 40px;
            font-weight: bold;
            transition: transform 0.2s, background 0.2s;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }
        .hero-btn:hover {
            transform: scale(1.04);
            background: #d7a86e;
        }

        /* CONTAINER */
        .container {
            max-width: 1420px;
            margin: 0 auto;
            padding: 2rem;
            display: grid;
            grid-template-columns: 1fr 370px;
            gap: 2rem;
            align-items: start;
        }
        @media (max-width: 1024px) {
            .container {
                grid-template-columns: 1fr;
            }
        }

        /* PRODUCTS */
        .products h2 {
            font-family: Georgia, serif;
            color: #4e342e;
            font-size: 1.8rem;
            margin-bottom: 1.5rem;
            position: relative;
        }
        .products h2::after {
            content: '';
            display: block;
            width: 52px;
            height: 3px;
            background: #c68b59;
            margin-top: 6px;
            border-radius: 2px;
        }
        .product-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.4rem;
        }
        @media (max-width: 768px) {
            .product-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        @media (max-width: 480px) {
            .product-grid {
                grid-template-columns: 1fr;
            }
        }
        .product-card {
            background: #fff;
            border-radius: 14px;
            padding: 1.4rem 1.4rem 1.6rem;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
            transition: transform 0.25s, box-shadow 0.25s;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .product-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 24px rgba(0, 0, 0, 0.1);
        }
        .product-image {
            width: 110px;
            height: 110px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 0.8rem;
        }
        .product-image svg {
            width: 100%;
            height: 100%;
        }
        .product-card h3 {
            font-size: 1rem;
            margin-bottom: 0.1rem;
            color: #2d1b13;
            flex: 1;
            display: flex;
            align-items: center;
        }
        .product-price {
            font-weight: bold;
            color: #5d4037;
            font-size: 1.05rem;
            margin: 0.5rem 0;
        }
        .add-btn {
            background: #4e342e;
            color: #fff;
            border: none;
            padding: 0.5rem 2rem;
            border-radius: 30px;
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 600;
            transition: background 0.2s, transform 0.15s;
            width: 100%;
            max-width: 140px;
            margin-top: auto;
        }
        .add-btn:hover {
            background: #5d4037;
            transform: scale(1.03);
        }
        .add-btn.pulse {
            animation: btn-pulse 0.4s ease;
        }
        @keyframes btn-pulse {
            0% {
                transform: scale(1);
            }
            50% {
                transform: scale(1.08);
            }
            100% {
                transform: scale(1);
            }
        }

        /* CART PANEL */
        .cart-panel {
            background: #fff;
            border-radius: 14px;
            padding: 1.4rem 1.4rem 1rem;
            box-shadow: 0 4px 18px rgba(0, 0, 0, 0.08);
            position: sticky;
            top: 90px;
            max-height: calc(100vh - 120px);
            display: flex;
            flex-direction: column;
        }
        .cart-panel h2 {
            font-family: Georgia, serif;
            color: #4e342e;
            margin-bottom: 0.8rem;
            padding-bottom: 0.6rem;
            border-bottom: 2px solid #f0ebe5;
            font-size: 1.3rem;
        }
        .cart-items {
            flex: 1;
            overflow-y: auto;
            max-height: 320px;
            min-height: 40px;
        }
        .cart-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.55rem 0;
            border-bottom: 1px solid #f8f4ef;
            gap: 6px;
        }
        .cart-item:last-child {
            border-bottom: none;
        }
        .cart-item-info {
            flex: 1;
            min-width: 0;
        }
        .cart-item-name {
            font-size: 0.82rem;
            font-weight: 600;
            color: #2d1b13;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .cart-item-price {
            font-size: 0.75rem;
            color: #a0806a;
        }
        .cart-item-controls {
            display: flex;
            align-items: center;
            gap: 3px;
        }
        .qty-btn {
            width: 22px;
            height: 22px;
            border: 1px solid #d4c8bc;
            background: #fff;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.75rem;
            line-height: 1;
            color: #4e342e;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.15s;
        }
        .qty-btn:hover {
            background: #f0ebe5;
        }
        .qty {
            font-size: 0.85rem;
            font-weight: bold;
            width: 18px;
            text-align: center;
        }
        .cart-item-total {
            font-size: 0.82rem;
            font-weight: 600;
            min-width: 50px;
            text-align: right;
            color: #2d1b13;
        }
        .empty-cart {
            color: #a0806a;
            text-align: center;
            padding: 1.8rem 0;
            font-style: italic;
            font-size: 0.9rem;
            border-bottom: 1px dashed #e5ddd5;
        }
        .cart-summary {
            border-top: 2px solid #f0ebe5;
            padding-top: 0.8rem;
            margin-top: 0.4rem;
        }
        .summary-row {
            display: flex;
            justify-content: space-between;
            font-size: 0.9rem;
            color: #4e342e;
            margin-bottom: 0.3rem;
        }
        .summary-row.total-row {
            font-weight: bold;
            font-size: 1.15rem;
            border-top: 1px solid #f0ebe5;
            padding-top: 0.5rem;
            margin-top: 0.3rem;
            color: #2d1b13;
        }
        .summary-row.discount-row span:last-child {
            color: #c62828;
            font-weight: 600;
        }
        .summary-row.shipping-row span:last-child {
            color: #2e7d32;
            font-weight: 600;
        }

        /* TOAST */
        .toast {
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: #4e342e;
            color: #fff;
            padding: 0.75rem 1.6rem;
            border-radius: 40px;
            font-size: 0.9rem;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
            opacity: 0;
            transform: translateY(80px) scale(0.9);
            transition: all 0.35s cubic-bezier(0.2, 0.9, 0.3, 1.3);
            z-index: 999;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .toast.show {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
        .toast .check {
            font-size: 1.1rem;
            color: #c68b59;
        }

        /* RESPONSIVE - cart panel */
        @media (max-width: 1024px) {
            .cart-panel {
                position: static;
                max-height: none;
            }
        }
    </style>
</head>
<body>

    <!-- HEADER -->
    <header class="header">
        <div class="logo">
            <!-- Coffee bean logo -->
            <svg viewBox="0 0 40 40">
                <ellipse cx="20" cy="20" rx="14" ry="18" fill="#C68B59"/>
                <path d="M20 2 Q26 10 26 20 Q26 30 20 38 Q14 30 14 20 Q14 10 20 2 Z" fill="#3E2723"/>
                <path d="M17 8 Q20 16 17 24" stroke="#C68B59" stroke-width="2" fill="none" stroke-linecap="round"/>
            </svg>
            <span>Tostadores del Sur</span>
        </div>
        <div class="cart-button" id="cartButton">
            <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="9" cy="21" r="1.5"/>
                <circle cx="18" cy="21" r="1.5"/>
                <path d="M2 3h2l2.5 12h11l2-8H4"/>
            </svg>
            <span>Carrito</span>
            <span class="cart-count" id="cartCount">0</span>
        </div>
    </header>

    <!-- HERO -->
    <section class="hero">
        <h1>Bienvenidos a Tostadores del Sur</h1>
        <p>Granos recién tostados y equipos para café de especialidad</p>
        <a href="#productos" class="hero-btn">Ver productos →</a>
    </section>

    <!-- MAIN -->
    <main class="container">
        <!-- PRODUCTS -->
        <section class="products" id="productos">
            <h2>Nuestros productos</h2>
            <div class="product-grid" id="productGrid"></div>
        </section>

        <!-- CART -->
        <aside class="cart-panel">
            <h2>🛒 Tu carrito</h2>
            <div class="cart-items" id="cartItems"></div>
            <div class="cart-summary">
                <div class="summary-row">
                    <span>Subtotal</span>
                    <span id="cartSubtotal">0,00 €</span>
                </div>
                <div class="summary-row discount-row">
                    <span>Descuento</span>
                    <span id="cartDiscount">0,00 €</span>
                </div>
                <div class="summary-row shipping-row">
                    <span>Envío</span>
                    <span id="cartShipping">—</span>
                </div>
                <div class="summary-row total-row">
                    <span>Total</span>
                    <span id="cartTotal">0,00 €</span>
                </div>
            </div>
        </aside>
    </main>

    <!-- TOAST -->
    <div class="toast" id="toast">
        <span class="check">✓</span>
        <span id="toastMsg"></span>
    </div>

    <script>
        // ========== DATA ==========
        const PRODUCTS = [{
            id: 1,
            name: 'Molinillo manual',
            price: 49.90,
            svg: `<svg viewBox="0 0 100 100"><rect x="28" y="25" width="44" height="55" rx="6" fill="#8D6E63"/><rect x="33" y="30" width="34" height="45" rx="3" fill="#D7A86E"/><rect x="25" y="22" width="50" height="7" rx="3.5" fill="#5D4037"/><rect x="25" y="29" width="50" height="3" fill="#3E2723"/><circle cx="45" cy="15" r="4" fill="#3E2723"/><rect x="44" y="11" width="2" height="6" fill="#3E2723"/><circle cx="64" cy="9" r="3" fill="#3E2723"/><rect x="46" y="9" width="18" height="2" fill="#3E2723"/><rect x="33" y="62" width="34" height="12" rx="3" fill="#4E342E"/><rect x="35" y="64" width="30" height="8" rx="2" fill="#5D4037"/><circle cx="50" cy="68" r="2" fill="#3E2723"/><ellipse cx="50" cy="85" rx="25" ry="3" fill="black" opacity="0.12"/></svg>`
        }, {
            id: 2,
            name: 'Cafetera espresso',
            price: 89.00,
            svg: `<svg viewBox="0 0 100 100"><polygon points="30,50 70,50 66,75 34,75" fill="#90A4AE"/><polygon points="34,50 66,50 62,28 38,28" fill="#B0BEC5"/><path d="M37 28 Q50 22 63 28" fill="none" stroke="#78909C" stroke-width="3"/><rect x="33" y="28" width="34" height="3" fill="#546E7A"/><path d="M40 26 Q50 20 60 26 Q50 22 40 26 Z" fill="#78909C"/><circle cx="50" cy="21" r="2.5" fill="#455A64"/><path d="M38 30 L20 38 Q15 42 18 50 L22 62 Q25 68 32 64 L44 54" fill="none" stroke="#3E2723" stroke-width="5" stroke-linecap="round"/><path d="M33 52 L26 60" fill="none" stroke="#90A4AE" stroke-width="4" stroke-linecap="round"/><ellipse cx="50" cy="78" rx="25" ry="3" fill="black" opacity="0.1"/></svg>`
        }, {
            id: 3,
            name: 'Café de Etiopía 250 g',
            price: 12.50,
            svg: `<svg viewBox="0 0 100 100"><path d="M28 22 Q28 15 37 13 L63 13 Q72 15 72 22 L74 80 Q74 87 65 87 L35 87 Q26 87 26 80 Z" fill="#4E342E"/><path d="M26 27 L74 27 L71 37 L29 37 Z" fill="#3E2723"/><rect x="34" y="42" width="32" height="26" rx="4" fill="#FFF3E0"/><path d="M38 54 Q42 50 46 54 Q50 58 54 54 Q58 50 62 54" fill="none" stroke="#5D4037" stroke-width="2" stroke-linecap="round"/><ellipse cx="40" cy="34" rx="4" ry="2.5" fill="#8B6F5A"/><ellipse cx="60" cy="34" rx="4" ry="2.5" fill="#6D4C41"/><ellipse cx="50" cy="90" rx="20" ry="3" fill="black" opacity="0.12"/></svg>`
        }, {
            id: 4,
            name: 'Taza de cerámica',
            price: 8.90,
            svg: `<svg viewBox="0 0 100 100"><ellipse cx="45" cy="72" rx="35" ry="7" fill="#BCAAA4"/><path d="M18 36 L23 68 Q24 74 30 74 L60 74 Q66 74 67 68 L72 36 Z" fill="#D7A86E"/><path d="M18 36 Q45 42 72 36" fill="none" stroke="#BF8F5A" stroke-width="2"/><ellipse cx="45" cy="36" rx="27" ry="6" fill="#3E2723"/><path d="M72 38 Q85 38 88 50 Q91 60 70 62" fill="none" stroke="#D7A86E" stroke-width="6" stroke-linecap="round"/><ellipse cx="45" cy="36" rx="27" ry="6" fill="none" stroke="#BF8F5A" stroke-width="1.5"/><ellipse cx="45" cy="35" rx="20" ry="4" fill="white" opacity="0.15"/><ellipse cx="45" cy="72" rx="25" ry="5" fill="black" opacity="0.05"/></svg>`
        }, {
            id: 5,
            name: 'Hervidor cuello de cisne',
            price: 39.00,
            svg: `<svg viewBox="0 0 100 100"><ellipse cx="40" cy="58" rx="28" ry="20" fill="#B0BEC5"/><path d="M15 50 L15 66 Q15 80 40 80 Q65 80 65 66 L65 50 Z" fill="#CFD8DC"/><ellipse cx="40" cy="78" rx="22" ry="4" fill="#90A4AE"/><ellipse cx="40" cy="45" rx="14" ry="5" fill="#78909C"/><circle cx="40" cy="42" r="2.5" fill="#455A64"/><path d="M65 55 Q82 48 85 28 Q86 20 92 16" fill="none" stroke="#B0BEC5" stroke-width="5" stroke-linecap="round"/><path d="M35 38 Q35 22 48 20 Q61 18 58 32" fill="none" stroke="#455A64" stroke-width="4" stroke-linecap="round"/><ellipse cx="40" cy="83" rx="25" ry="3" fill="black" opacity="0.1"/></svg>`
        }, {
            id: 6,
            name: 'Filtros de papel x100',
            price: 5.50,
            svg: `<svg viewBox="0 0 100 100"><path d="M30 33 L35 68 Q40 80 50 80 Q60 80 65 68 L70 33 Z" fill="#FFF8E1"/><ellipse cx="50" cy="35" rx="22" ry="8" fill="#FFF8E1" stroke="#FFCCBC" stroke-width="1.5"/><ellipse cx="50" cy="35" rx="18" ry="6" fill="#FFF3E0" stroke="#FFE0B2" stroke-width="1"/><path d="M50 35 L50 75" stroke="#FFD54F" stroke-width="0.8" stroke-dasharray="3,3"/><path d="M38 33 L36 70" stroke="#FFE0B2" stroke-width="0.8"/><path d="M62 33 L64 70" stroke="#FFE0B2" stroke-width="0.8"/><ellipse cx="50" cy="82" rx="22" ry="3" fill="black" opacity="0.08"/></svg>`
        }];

        // ========== STATE ==========
        let cart = {}; // { productId: quantity }

        const FREE_SHIPPING_THRESHOLD = 60; // €
        const SHIPPING_COST = 4.95; // €

        // ========== DOM REFS ==========
        const cartItemsEl = document.getElementById('cartItems');
        const cartCountEl = document.getElementById('cartCount');
        const cartSubtotalEl = document.getElementById('cartSubtotal');
        const cartDiscountEl = document.getElementById('cartDiscount');
        const cartShippingEl = document.getElementById('cartShipping');
        const cartTotalEl = document.getElementById('cartTotal');
        const productGrid = document.getElementById('productGrid');
        const cartButton = document.getElementById('cartButton');
        const toastEl = document.getElementById('toast');
        const toastMsg = document.getElementById('toastMsg');

        // ========== HELPERS ==========
        function formatPrice(value) {
            return value.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' €';
        }

        function cents(value) {
            return Math.round(value * 100);
        }

        function computeTotals() {
            let subtotal = 0;
            for (const id in cart) {
                const product = PRODUCTS.find(p => p.id === Number(id));
                if (product) {
                    subtotal += product.price * cart[id];
                }
            }
            subtotal = Math.round(subtotal * 100) / 100;

            const discount = subtotal >= 100 ?
                Math.round(subtotal * 0.10 * 100) / 100 :
                0;

            const afterDiscount = Math.round((subtotal - discount) * 100) / 100;

            const shipping = (afterDiscount > 0 && afterDiscount < FREE_SHIPPING_THRESHOLD) ?
                SHIPPING_COST :
                0;

            const total = Math.round((afterDiscount + shipping) * 100) / 100;

            return { subtotal, discount, afterDiscount, shipping, total };
        }

        // ========== RENDER ==========
        function renderCart() {
            const { subtotal, discount, afterDiscount, shipping, total } = computeTotals();

            // Count badge
            const totalQty = Object.values(cart).reduce((a, b) => a + b, 0);
            cartCountEl.textContent = totalQty;

            // Cart items
            if (totalQty === 0) {
                cartItemsEl.innerHTML = `<div class="empty-cart">Tu carrito está vacío<br>🍵</div>`;
            } else {
                let html = '';
                for (const id in cart) {
                    const product = PRODUCTS.find(p => p.id === Number(id));
                    if (!product) continue;
                    const qty = cart[id];
                    const lineTotal = Math.round(product.price * qty * 100) / 100;
                    html += `
                        <div class="cart-item">
                            <div class="cart-item-info">
                                <div class="cart-item-name">${product.name}</div>
                                <div class="cart-item-price">${formatPrice(product.price)}</div>
                            </div>
                            <div class="cart-item-controls">
                                <button class="qty-btn" data-id="${product.id}" data-delta="-1">−</button>
                                <span class="qty">${qty}</span>
                                <button class="qty-btn" data-id="${product.id}" data-delta="1">+</button>
                            </div>
                            <div class="cart-item-total">${formatPrice(lineTotal)}</div>
                        </div>`;
                }
                cartItemsEl.innerHTML = html;
            }

            // Summary
            cartSubtotalEl.textContent = formatPrice(subtotal);

            if (discount > 0) {
                cartDiscountEl.textContent = '−' + formatPrice(discount);
                cartDiscountEl.style.color = '#c62828';
            } else {
                cartDiscountEl.textContent = formatPrice(0);
                cartDiscountEl.style.color = '';
            }

            if (totalQty === 0) {
                cartShippingEl.textContent = '—';
                cartShippingEl.style.color = '';
            } else if (shipping === 0) {
                cartShippingEl.textContent = 'Gratis';
                cartShippingEl.style.color = '#2e7d32';
            } else {
                cartShippingEl.textContent = formatPrice(shipping);
                cartShippingEl.style.color = '#e65100';
            }

            cartTotalEl.textContent = formatPrice(total);
        }

        function renderProducts() {
            let html = '';
            for (const product of PRODUCTS) {
                html += `
                    <div class="product-card">
                        <div class="product-image">${product.svg}</div>
                        <h3>${product.name}</h3>
                        <div class="product-price">${formatPrice(product.price)}</div>
                        <button class="add-btn" data-id="${product.id}">Añadir</button>
                    </div>`;
            }
            productGrid.innerHTML = html;
        }

        // ========== ACTIONS ==========
        function addToCart(id, delta = 1) {
            const current = cart[id] || 0;
            cart[id] = Math.max(0, current + delta);
            if (cart[id] === 0) {
                delete cart[id];
            }
            renderCart();
        }

        function changeQty(id, delta) {
            addToCart(id, delta);
        }

        // ========== TOAST ==========
        let toastTimer;
        function showToast(message) {
            toastMsg.textContent = message;
            toastEl.classList.add('show');
            clearTimeout(toastTimer);
            toastTimer = setTimeout(() => {
                toastEl.classList.remove('show');
            }, 1600);
        }

        // ========== EVENT LISTENERS ==========
        // Product grid
        productGrid.addEventListener('click', (e) => {
            const btn = e.target.closest('.add-btn');
            if (!btn) return;
            const id = Number(btn.dataset.id);
            addToCart(id, 1);
            const product = PRODUCTS.find(p => p.id === id);
            showToast(`Añadido: ${product.name}`);
            // Pulse animation
            btn.classList.remove('pulse');
            void btn.offsetWidth;
            btn.classList.add('pulse');
            // Bump the cart
            cartButton.classList.remove('bounce');
            void cartButton.offsetWidth;
            cartButton.classList.add('bounce');
        });

        // Cart items (buttons)
        cartItemsEl.addEventListener('click', (e) => {
            const btn = e.target.closest('.qty-btn');
            if (!btn) return;
            const id = Number(btn.dataset.id);
            const delta = Number(btn.dataset.delta);
            changeQty(id, delta);
        });

        // ========== FINALIZE ==========
        // Render products
        renderProducts();

        // Empty cart
        renderCart();

        // ========== PUBLIC API ==========
        window.Tostadores = {
            getCart: () => ({ ...cart }),
            add: (id, qty = 1) => {
                addToCart(id, qty);
                const product = PRODUCTS.find(p => p.id === id);
                showToast(`Añadido: ${product ? product.name : id}`);
            },
            remove: (id) => {
                delete cart[id];
                renderCart();
                showToast('Producto eliminado');
            },
            reset: () => {
                cart = {};
                renderCart();
                showToast('Carrito vaciado');
            },
            getTotal: () => computeTotals().total,
        };

        // ========== DEMO — Procesar una secuencia de eventos ==========
        // Para que la página muestre una experiencia viva, reproducimos una corta animación.
        // Los carritos se añaden en secuencia con retardo.
        let demoStep = 0;
        const demoSteps = [
            () => window.Tostadores.add(1, 1),
            () => window.Tostadores.add(2, 1),
            () => window.Tostadores.add(3, 2),
            () => window.Tostadores.add(3, 1), // Cambia la cantidad de 2 a 3
        ];

        function runDemo() {
            if (demoStep >= demoSteps.length) {
                demoStep = 0;
                cart = {};
                renderCart();
                return;
            }
            demoSteps[demoStep]();
            demoStep++;
            setTimeout(runDemo, 800);
        }

        // Arrancar demo tras 1.2s, solo si el usuario no ha interactuado aún
        let userInteracted = false;
        const blockInteractions = ['click', 'keydown', 'touchstart'];
        const markInteract = () => {
            userInteracted = true;
            clearTimeout(demoTimer);
            blockInteractions.forEach(evt => document.removeEventListener(evt, markInteract, true));
        };
        blockInteractions.forEach(evt => document.addEventListener(evt, markInteract, true));

        const demoTimer = setTimeout(runDemo, 1200);
    </script>
</body>
</html>
```
### What You Can Do

The page combines a product catalog with a live cart so you can explore and buy items in a relaxed, intuitive way.

- **Product Grid with Add-to-Cart:** Each of the six coffee items is displayed with a custom icon, name, and price. Clicking the **"Añadir"** button adds one unit to your cart with a brief pulse feedback, and a small toast message confirms the action.
- **Live Shopping Cart Panel:** The cart on the right shows all added items with individual quantities. You can use the **+/− buttons** to adjust quantities directly in the cart, and the line total updates instantly. If the quantity reaches zero, the item is removed automatically.
- **Dynamic Pricing & Free Shipping Rules:** The subtotal is always recalculated. A **10% discount** is applied to orders over 100 €. If the discounted order value is below 60 €, a **4.95 € shipping fee** is added; otherwise, shipping is free. The final total updates live in the summary panel.
- **Automatic Demo Sequence:** A short script automatically runs a product demo a few seconds after load, adding and adjusting items so you can see the cart logic in action. You can still interact freely at any time.