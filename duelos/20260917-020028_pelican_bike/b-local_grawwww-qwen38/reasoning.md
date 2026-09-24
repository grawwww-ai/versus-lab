Let me think through this carefully. I need to draw a pelican riding a bicycle in SVG. Let me plan the components:

**Bicycle (red):**
- Two wheels (circles) - let's say at x=200, y=450 and x=550, y=450, radius ~80
- Frame (lines/paths connecting wheels, seat post, handlebar post)
- Pedals (small rects/circles on a crank)
- Handlebars
- Chain, gears

**Pelican (blue):**
- Large beak (long, prominent)
- Head (circle/ellipse)
- Eye
- Body (large oval/path)
- Wings (curved paths)
- Tail feathers (pointed shapes at rear)
- Feet on pedals
- Neck

Let me plan coordinates:
- Canvas: 800x600
- Ground level: ~520
- Wheels: center at (200, 440) and (550, 440), radius 80
- Frame: connects from rear wheel to front wheel area, with seat post going up, handlebar post going up
- Seat: around (280, 320)
- Handlebars: around (520, 280)
- Crank center (where pedals are): around (380, 440)
- Pedals: small rects near crank

Pelican:
- Body: large oval, center around (300, 250), extending back
- Neck: curved from body up to head
- Head: around (450, 150)
- Beak: very long, extending forward from head, maybe to (650, 170)
- Eye: on head
- Wings: on the body, one visible
- Tail feathers: at rear of body, pointing back/down
- Feet: from lower body down to pedals

Let me refine the layout:
- Bike frame:
  - Rear wheel center: (180, 440), r=80
  - Front wheel center: (580, 440), r=80
  - Bottom bracket (crank center): (380, 440)
  - Seat tube: from (380, 440) up to (300, 300)
  - Down tube: from (380, 440) to (520, 340)
  - Top tube: from (300, 300) to (520, 340)
  - Chain stay: from (180, 440) to (380, 440)
  - Seat stay: from (180, 440) to (300, 300)
  - Fork: from (520, 340) to (580, 440)
  - Handlebar: at top of fork, around (520, 300)
  - Seat: at top of seat tube, around (290, 280)
  - Crank arm and pedals: at (380, 440), pedals at maybe (360, 470) and (400, 410)

Pelican:
- Sitting on seat at (290, 280)
- Body: large, from about (200, 250) to (400, 320), oval shape
- Neck: from upper body (~350, 240) curving up to head at (~480, 140)
- Head: circle at (~480, 140), r=25
- Beak: very long, from (490, 145) extending to (~680, 165), with lower mandible
- Eye: small circle at (~485, 130)
- Wing: on the body, visible, curved
- Tail feathers: at rear (~200, 280), pointing back and down, 3-4 pointed shapes
- Feet: from body bottom (~350, 310) down to pedals

Let me now write the SVG. I'll use:
- Gradients for subtle shading
- Paths for organic shapes (pelican body, neck, beak, wings, tail)
- Circles for wheels, eye
- Rects for pedals
- Lines/paths for bike frame

Let me code this up:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600">
  <defs>
    <!-- Gradients for shading -->
    <linearGradient id="pelicanBody" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#4A90D9"/>
      <stop offset="100%" stop-color="#2C5F8A"/>
    </linearGradient>
    <linearGradient id="pelicanBeak" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#E8A838"/>
      <stop offset="100%" stop-color="#C47A1F"/>
    </linearGradient>
    <radialGradient id="wheelGrad" cx="50%" cy="50%" r="50%">
      <stop offset="80%" stop-color="#333"/>
      <stop offset="100%" stop-color="#111"/>
    </radialGradient>
    <linearGradient id="wingGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#5BA3E0"/>
      <stop offset="100%" stop-color="#2C5F8A"/>
    </linearGradient>
    <linearGradient id="tailGrad" x1="100%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#4A90D9"/>
      <stop offset="100%" stop-color="#1E3F5C"/>
    </linearGradient>
  </defs>
  
  <!-- Background -->
  <rect width="800" height="600" fill="#F0F4F8"/>
  
  <!-- Ground -->
  <rect x="0" y="520" width="800" height="80" fill="#8B7355" opacity="0.3"/>
  
  <!-- === BICYCLE (red) === -->
  
  <!-- Rear wheel -->
  <circle cx="180" cy="440" r="78" fill="none" stroke="#CC2222" stroke-width="6"/>
  <circle cx="180" cy="440" r="74" fill="none" stroke="#992222" stroke-width="2"/>
  <circle cx="180" cy="440" r="8" fill="#CC2222"/>
  <!-- Spokes rear -->
  <line x1="180" y1="362" x2="180" y2="518" stroke="#CC2222" stroke-width="1.5" opacity="0.6"/>
  <line x1="102" y1="440" x2="258" y2="440" stroke="#CC2222" stroke-width="1.5" opacity="0.6"/>
  <line x1="125" y1="385" x2="235" y2="495" stroke="#CC2222" stroke-width="1.5" opacity="0.6"/>
  <line x1="125" y1="495" x2="235" y2="385" stroke="#CC2222" stroke-width="1.5" opacity="0.6"/>
  
  <!-- Front wheel -->
  <circle cx="580" cy="440" r="78" fill="none" stroke="#CC2222" stroke-width="6"/>
  <circle cx="580" cy="440" r="74" fill="none" stroke="#992222" stroke-width="2"/>
  <circle cx="580" cy="440" r="8" fill="#CC2222"/>
  <!-- Spokes front -->
  <line x1="580" y1="362" x2="580" y2="518" stroke="#CC2222" stroke-width="1.5" opacity="0.6"/>
  <line x1="502" y1="440" x2="658" y2="440" stroke="#CC2222" stroke-width="1.5" opacity="0.6"/>
  <line x1="525" y1="385" x2="635" y2="495" stroke="#CC2222" stroke-width="1.5" opacity="0.6"/>
  <line x1="525" y1="495" x2="635" y2="385" stroke="#CC2222" stroke-width="1.5" opacity="0.6"/>
  
  <!-- Frame -->
  <!-- Chain stay: rear hub to crank -->
  <line x1="180" y1="440" x2="380" y2="440" stroke="#DD2222" stroke-width="8"/>
  <!-- Seat tube: crank to seat -->
  <line x1="380" y1="440" x2="310" y2="290" stroke="#DD2222" stroke-width="8"/>
  <!-- Down tube: crank to head tube -->
  <line x1="380" y1="440" x2="530" y2="330" stroke="#DD2222" stroke-width="8"/>
  <!-- Top tube: seat to head tube -->
  <line x1="310" y1="290" x2="530" y2="330" stroke="#DD2222" stroke-width="7"/>
  <!-- Seat stay: rear hub to seat -->
  <line x1="180" y1="440" x2="310" y2="290" stroke="#DD2222" stroke-width="6"/>
  <!-- Fork/head tube -->
  <line x1="530" y1="330" x2="580" y2="440" stroke="#DD2222" stroke-width="7"/>
  <!-- Handlebar stem -->
  <line x1="530" y1="330" x2="520" y2="280" stroke="#CC1111" stroke-width="6"/>
  
  <!-- Handlebars -->
  <path d="M 520 280 C 520 260, 540 250, 560 255 L 570 260" fill="none" stroke="#881111" stroke-width="5" stroke-linecap="round"/>
  
  <!-- Seat -->
  <ellipse cx="300" cy="280" rx="25" ry="8" fill="#331111"/>
  
  <!-- Crank and pedals -->
  <circle cx="380" cy="440" r="12" fill="#AA1111"/>
  <!-- Crank arms -->
  <line x1="380" y1="440" x2="355" y2="475" stroke="#881111" stroke-width="5"/>
  <line x1="380" y1="440" x2="405" y2="405" stroke="#881111" stroke-width="5"/>
  <!-- Pedals -->
  <rect x="340" y="472" width="30" height="8" rx="2" fill="#551111"/>
  <rect x="390" y="400" width="30" height="8" rx="2" fill="#551111"/>
  
  <!-- Chain ring -->
  <circle cx="380" cy="440" r="20" fill="none" stroke="#881111" stroke-width="2" opacity="0.7"/>
  
  <!-- === PELICAN (blue) === -->
  
  <!-- Tail feathers -->
  <path d="M 220 280 L 160 320 L 170 310 L 140 350 L 165 325 L 150 360 L 180 320 Z" fill="url(#tailGrad)" opacity="0.9"/>
  <path d="M 215 275 L 155 300 L 160 295 L 130 330 L 158 305 L 145 340 L 175 300 Z" fill="#1E3F5C" opacity="0.7"/>
  
  <!-- Body -->
  <path d="M 230 270 C 220 240, 260 210, 320 215 C 380 220, 410 250, 400 290 C 390 320, 340 330, 290 320 C 250 312, 235 295, 230 270 Z" fill="url(#pelicanBody)"/>
  
  <!-- Wing -->
  <path d="M 260 240 C 280 225, 330 220, 360 235 C 380 245, 370 270, 340 280 C 310 290, 270 280, 260 260 Z" fill="url(#wingGrad)" opacity="0.85"/>
  <!-- Wing feather details -->
  <path d="M 280 245 C 300 235, 330 232, 350 240" fill="none" stroke="#1E3F5C" stroke-width="1.5" opacity="0.5"/>
  <path d="M 275 255 C 295 248, 325 245, 345 252" fill="none" stroke="#1E3F5C" stroke-width="1.5" opacity="0.5"/>
  
  <!-- Neck -->
  <path d="M 370 230 C 390 200, 420 170, 460 145 C 470 138, 480 135, 485 138" fill="none" stroke="#4A90D9" stroke-width="18" stroke-linecap="round"/>
  <path d="M 370 230 C 390 200, 420 170, 460 145 C 470 138, 480 135, 485 138" fill="none" stroke="#3A7BC0" stroke-width="12" stroke-linecap="round"/>
  
  <!-- Head -->
  <circle cx="490" cy="140" r="22" fill="#4A90D9"/>
  <circle cx="490" cy="140" r="22" fill="url(#pelicanBody)" opacity="0.5"/>
  
  <!-- Eye -->
  <circle cx="497" cy="133" r="5" fill="#111"/>
  <circle cx="498" cy="132" r="2" fill="#FFF" opacity="0.8"/>
  
  <!-- Beak - upper -->
  <path d="M 505 135 C 540 130, 620 135, 680 155 L 680 160 C 620 148, 540 145, 505 148 Z" fill="#D4943A"/>
  <!-- Beak - lower (pouch) -->
  <path d="M 505 148 C 540 155, 600 170, 670 162 L 680 158 C 620 155, 540 150, 505 148 Z" fill="#B87A28"/>
  <path d="M 510 150 C 550 158, 620 168, 670 160 C 650 172, 580 170, 520 155 Z" fill="#A06A20" opacity="0.6"/>
  
  <!-- Beak tip -->
  <path d="M 675 153 L 690 157 L 680 162 Z" fill="#C47A1F"/>
  
  <!-- Feet -->
  <!-- Left foot (on rear pedal) -->
  <path d="M 340 320 C 335 360, 340 400, 350 440 L 355 470 L 340 472 L 350 475" fill="none" stroke="#D4943A" stroke-width="6" stroke-linecap="round"/>
  <path d="M 340 472 L 335 478 L 350 475 L 345 480 Z" fill="#D4943A"/>
  
  <!-- Right foot (on front pedal) -->
  <path d="M 360 310 C 365 350, 380 380, 395 400 L 400 405 L 390 400 L 400 403" fill="none" stroke="#D4943A" stroke-width="6" stroke-linecap="round"/>
  <path d="M 395 400 L 390 406 L 405 403 L 400 408 Z" fill="#D4943A"/>
  
</svg>
```

Hmm, let me reconsider the layout. The pelican should be clearly sitting on the bike. Let me adjust:

- The pelican's body should be above the seat
- The neck goes up and forward
- The beak is very large (pelicans have huge beaks)
- The feet should clearly be on the pedals

Let me also make sure the beak is more prominent - pelicans have very large, long beaks with a distinctive pouch.

Let me also reconsider the bike proportions. The seat is at about (300, 280), and the pelican body should be around there. The pedals are at the crank (380, 440), so the feet need to extend from the body down to those positions.

Let me redo this more carefully with better proportions and make sure everything looks right.

Actually, let me reconsider the overall layout:
- The bike should be centered in the image
- Wheels at roughly y=440 (bottom of wheels at ~520)
- The bike frame goes up to about y=280 (handlebars/seat area)
- The pelican body sits on the seat, body center around (300, 250)
- Neck goes up and to the right
- Head at about (480, 140)
- Beak extends from head to about x=680
- Tail feathers at rear of body, around (180-220, 280-340)
- Feet: from body bottom to pedals at (355, 472) and (400, 403)

This seems reasonable. Let me also add:
- A subtle shadow under the bike
- Better wing detail
- More prominent beak pouch (pelican characteristic)

Let me finalize the SVG.
