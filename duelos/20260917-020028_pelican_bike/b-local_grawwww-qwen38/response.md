```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600">
  <defs>
    <linearGradient id="bodyGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#5BA3E0"/>
      <stop offset="100%" stop-color="#2C5F8A"/>
    </linearGradient>
    <linearGradient id="wingGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#6DB3F0"/>
      <stop offset="100%" stop-color="#2C5F8A"/>
    </linearGradient>
    <linearGradient id="tailGrad" x1="100%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#4A90D9"/>
      <stop offset="100%" stop-color="#1A3550"/>
    </linearGradient>
    <linearGradient id="beakGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#E8A838"/>
      <stop offset="100%" stop-color="#B87A28"/>
    </linearGradient>
    <linearGradient id="pouchGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#D4943A"/>
      <stop offset="100%" stop-color="#9A6220"/>
    </linearGradient>
    <radialGradient id="wheelShade" cx="50%" cy="50%" r="50%">
      <stop offset="70%" stop-color="#FF0000" stop-opacity="0"/>
      <stop offset="100%" stop-color="#FF0000" stop-opacity="0.15"/>
    </radialGradient>
    <linearGradient id="neckGrad" x1="0%" y1="100%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#3A7BC0"/>
      <stop offset="100%" stop-color="#5BA3E0"/>
    </linearGradient>
  </defs>

  <!-- Background -->
  <rect width="800" height="600" fill="#EDF2F7"/>
  <rect x="0" y="518" width="800" height="82" fill="#7A8B6A" opacity="0.25"/>
  <ellipse cx="380" cy="522" rx="280" ry="12" fill="#000" opacity="0.08"/>

  <!-- === BICYCLE (red) === -->
  <!-- Rear wheel -->
  <circle cx="180" cy="440" r="78" fill="none" stroke="#CC2222" stroke-width="6"/>
  <circle cx="180" cy="440" r="78" fill="url(#wheelShade)"/>
  <circle cx="180" cy="440" r="73" fill="none" stroke="#AA1818" stroke-width="1.5"/>
  <circle cx="180" cy="440" r="9" fill="#BB2020"/>
  <line x1="180" y1="365" x2="180" y2="515" stroke="#CC2222" stroke-width="1.2" opacity="0.5"/>
  <line x1="105" y1="440" x2="255" y2="440" stroke="#CC2222" stroke-width="1.2" opacity="0.5"/>
  <line x1="127" y1="387" x2="233" y2="493" stroke="#CC2222" stroke-width="1.2" opacity="0.5"/>
  <line x1="127" y1="493" x2="233" y2="387" stroke="#CC2222" stroke-width="1.2" opacity="0.5"/>
  <line x1="180" y1="365" x2="127" y2="493" stroke="#CC2222" stroke-width="0.8" opacity="0.3"/>
  <line x1="180" y1="515" x2="127" y2="387" stroke="#CC2222" stroke-width="0.8" opacity="0.3"/>
  <line x1="180" y1="365" x2="233" y2="493" stroke="#CC2222" stroke-width="0.8" opacity="0.3"/>
  <line x1="180" y1="515" x2="233" y2="387" stroke="#CC2222" stroke-width="0.8" opacity="0.3"/>

  <!-- Front wheel -->
  <circle cx="590" cy="440" r="78" fill="none" stroke="#CC2222" stroke-width="6"/>
  <circle cx="590" cy="440" r="78" fill="url(#wheelShade)"/>
  <circle cx="590" cy="440" r="73" fill="none" stroke="#AA1818" stroke-width="1.5"/>
  <circle cx="590" cy="440" r="9" fill="#BB2020"/>
  <line x1="590" y1="365" x2="590" y2="515" stroke="#CC2222" stroke-width="1.2" opacity="0.5"/>
  <line x1="515" y1="440" x2="665" y2="440" stroke="#CC2222" stroke-width="1.2" opacity="0.5"/>
  <line x1="537" y1="387" x2="643" y2="493" stroke="#CC2222" stroke-width="1.2" opacity="0.5"/>
  <line x1="537" y1="493" x2="643" y2="387" stroke="#CC2222" stroke-width="1.2" opacity="0.5"/>
  <line x1="590" y1="365" x2="537" y2="493" stroke="#CC2222" stroke-width="0.8" opacity="0.3"/>
  <line x1="590" y1="515" x2="537" y2="387" stroke="#CC2222" stroke-width="0.8" opacity="0.3"/>
  <line x1="590" y1="365" x2="643" y2="493" stroke="#CC2222" stroke-width="0.8" opacity="0.3"/>
  <line x1="590" y1="515" x2="643" y2="387" stroke="#CC2222" stroke-width="0.8" opacity="0.3"/>

  <!-- Bike frame -->
  <!-- Chain stay -->
  <line x1="180" y1="440" x2="380" y2="440" stroke="#DD2222" stroke-width="9" stroke-linecap="round"/>
  <!-- Seat tube -->
  <line x1="380" y1="440" x2="305" y2="285" stroke="#DD2222" stroke-width="9" stroke-linecap="round"/>
  <!-- Down tube -->
  <line x1="380" y1="440" x2="540" y2="325" stroke="#DD2222" stroke-width="9" stroke-linecap="round"/>
  <!-- Top tube -->
  <line x1="305" y1="285" x2="540" y2="325" stroke="#DD2222" stroke-width="7" stroke-linecap="round"/>
  <!-- Seat stay -->
  <line x1="180" y1="440" x2="305" y2="285" stroke="#CC1818" stroke-width="6" stroke-linecap="round"/>
  <!-- Head tube / fork -->
  <line x1="540" y1="325" x2="590" y2="440" stroke="#DD2222" stroke-width="7" stroke-linecap="round"/>
  <!-- Steer tube -->
  <line x1="540" y1="325" x2="530" y2="270" stroke="#CC1818" stroke-width="7" stroke-linecap="round"/>

  <!-- Handlebars -->
  <path d="M 530 270 C 530 255, 548 248, 568 252 C 578 255, 582 262, 578 268" fill="none" stroke="#771111" stroke-width="6" stroke-linecap="round"/>
  <circle cx="578" cy="268" r="5" fill="#551010"/>

  <!-- Seat post and saddle -->
  <line x1="305" y1="285" x2="295" y2="265" stroke="#AA1515" stroke-width="5"/>
  <ellipse cx="288" cy="260" rx="28" ry="9" fill="#2A0808"/>
  <ellipse cx="288" cy="258" rx="24" ry="6" fill="#3A1010"/>

  <!-- Crankset -->
  <circle cx="380" cy="440" r="22" fill="none" stroke="#991515" stroke-width="2.5"/>
  <circle cx="380" cy="440" r="13" fill="#AA1818"/>
  <circle cx="380" cy="440" r="5" fill="#771010"/>
  <!-- Crank arms -->
  <line x1="380" y1="440" x2="352" y2="478" stroke="#881212" stroke-width="6" stroke-linecap="round"/>
  <line x1="380" y1="440" x2="408" y2="402" stroke="#881212" stroke-width="6" stroke-linecap="round"/>
  <!-- Pedals -->
  <rect x="335" y="474" width="34" height="9" rx="3" fill="#4A0A0A"/>
  <rect x="391" y="396" width="34" height="9" rx="3" fill="#4A0A0A"/>
  <!-- Chain hint -->
  <path d="M 180 432 L 380 425" stroke="#771111" stroke-width="1.5" opacity="0.4" stroke-dasharray="3,3"/>
  <path d="M 180 448 L 380 455" stroke="#771111" stroke-width="1.5" opacity="0.4" stroke-dasharray="3,3"/>

  <!-- === PELICAN (blue) === -->

  <!-- Tail feathers (rear) -->
  <path d="M 230 275 L 165 310 L 175 305 L 140 345 L 168 318 L 148 358 L 180 322 Z" fill="url(#tailGrad)"/>
  <path d="M 225 268 L 158 298 L 162 294 L 132 328 L 158 306 L 142 338 L 172 308 Z" fill="#1A3550" opacity="0.8"/>
  <path d="M 228 280 L 172 325 L 155 360 L 165 330 Z" fill="#1A3550" opacity="0.5"/>

  <!-- Body -->
  <path d="M 225 268 C 218 235, 255 205, 315 208 C 375 212, 408 245, 400 285 C 392 320, 340 332, 285 322 C 248 315, 230 295, 225 268 Z" fill="url(#bodyGrad)"/>
  <!-- Body highlight -->
  <path d="M 250 235 C 265 218, 310 212, 350 218 C 370 222, 380 232, 375 242 C 350 235, 290 232, 260 245 Z" fill="#7BC0F5" opacity="0.3"/>

  <!-- Wing (folded, on top of body) -->
  <path d="M 255 238 C 275 218, 330 210, 365 225 C 385 235, 378 262, 348 275 C 318 288, 272 282, 258 262 Z" fill="url(#wingGrad)" opacity="0.9"/>
  <!-- Wing feather lines -->
  <path d="M 275 238 C 300 226, 335 222, 358 230" fill="none" stroke="#1E3F5C" stroke-width="1.5" opacity="0.5"/>
  <path d="M 268 250 C 292 240, 328 236, 352 244" fill="none" stroke="#1E3F5C" stroke-width="1.2" opacity="0.4"/>
  <path d="M 265 260 C 288 252, 320 248, 345 255" fill="none" stroke="#1E3F5C" stroke-width="1" opacity="0.3"/>
  <!-- Wing tip feathers -->
  <path d="M 365 225 C 375 230, 380 245, 370 258 C 365 250, 360 238, 365 225 Z" fill="#1E3F5C" opacity="0.4"/>

  <!-- Neck (curved) -->
  <path d="M 370 228 C 395 195, 425 165, 465 142 C 475 136, 483 133, 488 135" fill="none" stroke="url(#neckGrad)" stroke-width="20" stroke-linecap="round"/>
  <path d="M 370 228 C 395 195, 425 165, 465 142 C 475 136, 483 133, 488 135" fill="none" stroke="#5BA3E0" stroke-width="14" stroke-linecap="round" opacity="0.4"/>

  <!-- Head -->
  <ellipse cx="492" cy="138" rx="24" ry="22" fill="#4A90D9"/>
  <ellipse cx="492" cy="134" rx="20" ry="16" fill="#6DB3F0" opacity="0.3"/>
  <!-- Crown detail -->
  <path d="M 478 120 C 485 115, 498 114, 505 118 C 500 116, 488 116, 478 120 Z" fill="#2C5F8A" opacity="0.4"/>

  <!-- Eye -->
  <circle cx="500" cy="130" r="6" fill="#FFF"/>
  <circle cx="501" cy="130" r="4" fill="#111"/>
  <circle cx="502.5" cy="128.5" r="1.5" fill="#FFF" opacity="0.9"/>

  <!-- BEAK - upper mandible (very long, pelican-style) -->
  <path d="M 510 128 C 550 122, 620 126, 685 148 L 688 153 C 620 140, 550 138, 510 142 Z" fill="url(#beakGrad)"/>
  <!-- Beak ridge -->
  <path d="M 512 130 C 550 125, 615 128, 680 147" fill="none" stroke="#C47A1F" stroke-width="1.5" opacity="0.6"/>

  <!-- BEAK - lower pouch (pelican's distinctive gular pouch) -->
  <path d="M 510 142 C 540 148, 590 165, 670 158 L 685 153 C 620 155, 555 148, 510 142 Z" fill="url(#pouchGrad)"/>
  <!-- Pouch depth/shadow -->
  <path d="M 515 144 C 545 152, 600 164, 665 156 C 640 168, 570 165, 520 148 Z" fill="#7A5018" opacity="0.5"/>
  <!-- Pouch membrane lines -->
  <path d="M 530 148 C 560 156, 610 162, 660 155" fill="none" stroke="#8A5A20" stroke-width="1" opacity="0.4"/>
  <path d="M 525 145 C 555 152, 600 158, 650 153" fill="none" stroke="#8A5A20" stroke-width="0.8" opacity="0.3"/>

  <!-- Beak tip -->
  <path d="M 683 148 L 695 153 L 685 157 Z" fill="#A06820"/>

  <!-- NOSTRIL -->
  <ellipse cx="530" cy="128" rx="4" ry="2" fill="#8A5A20" opacity="0.6"/>

  <!-- === FEET ON PEDALS === -->
  <!-- Left leg (far side, slightly behind) -->
  <path d="M 340 318 C 338 355, 342 395, 352 435 C 354 448, 355 460, 352 474" fill="none" stroke="#D4943A" stroke-width="7" stroke-linecap="round"/>
  <path d="M 340 318 C 338 355, 342 395, 352 435 C 354 448, 355 460, 352 474" fill="none" stroke="#B87A28" stroke-width="4" stroke-linecap="round" opacity="0.5"/>
  <!-- Left foot / webbed toes -->
  <path d="M 345 474 L 335 480 L 348 477 L 340 484 L 355 478 L 350 484 L 360 476 Z" fill="#D4943A"/>
  <path d="M 335 480 L 340 484 M 348 477 L 350 484 M 355 478 L 360 476" stroke="#B87A28" stroke-width="1" opacity="0.6"/>

  <!-- Right leg (near side) -->
  <path d="M 365 312 C 370 348, 382 378, 395 400 C 398 406, 400 410, 398 400" fill="none" stroke="#D4943A" stroke-width="7" stroke-linecap="round"/>
  <path d="M 365 312 C 370 348, 382 378, 395 400" fill="none" stroke="#B87A28" stroke-width="4" stroke-linecap="round" opacity="0.5"/>
  <!-- Right foot / webbed toes -->
  <path d="M 392 398 L 382 405 L 394 401 L 388 408 L 400 401 L 396 408 L 406 400 Z" fill="#D4943A"/>
  <path d="M 382 405 L 388 408 M 394 401 L 396 408 M 400 401 L 406 400" stroke="#B87A28" stroke-width="1" opacity="0.6"/>
</svg>
```