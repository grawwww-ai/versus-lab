```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="800" height="600">
  <defs>
    <radialGradient id="wheelGrad" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0%" stop-color="#e8eef2"/>
      <stop offset="70%" stop-color="#b9c4cc"/>
      <stop offset="100%" stop-color="#8b98a3"/>
    </radialGradient>
    <linearGradient id="bikeGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#e03028"/>
      <stop offset="100%" stop-color="#9c1510"/>
    </linearGradient>
    <radialGradient id="pelicanGrad" cx="0.4" cy="0.35" r="0.8">
      <stop offset="0%" stop-color="#5aa9e6"/>
      <stop offset="60%" stop-color="#2f7cc4"/>
      <stop offset="100%" stop-color="#1b4f86"/>
    </radialGradient>
    <linearGradient id="wingGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#4b97da"/>
      <stop offset="100%" stop-color="#1c4e80"/>
    </linearGradient>
    <linearGradient id="beakGrad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#f5b74a"/>
      <stop offset="100%" stop-color="#c97b2b"/>
    </linearGradient>
  </defs>

  <!-- background sky -->
  <rect x="0" y="0" width="800" height="600" fill="#dff0f7"/>
  <rect x="0" y="520" width="800" height="80" fill="#9fb8a5"/>
  <rect x="0" y="518" width="800" height="4" fill="#7f9a87" opacity="0.6"/>

  <!-- ============ BICYCLE ============ -->
  <!-- rear wheel -->
  <circle cx="220" cy="470" r="80" fill="none" stroke="#2b2f33" stroke-width="10"/>
  <circle cx="220" cy="470" r="70" fill="url(#wheelGrad)"/>
  <circle cx="220" cy="470" r="70" fill="none" stroke="#6f7b84" stroke-width="3"/>
  <g stroke="#9aa6af" stroke-width="3">
    <line x1="220" y1="400" x2="220" y2="540"/>
    <line x1="150" y1="470" x2="290" y2="470"/>
    <line x1="170" y1="420" x2="270" y2="520"/>
    <line x1="270" y1="420" x2="170" y2="520"/>
  </g>
  <circle cx="220" cy="470" r="10" fill="#3a4147"/>
  <circle cx="220" cy="470" r="5" fill="#1f2428"/>

  <!-- front wheel -->
  <circle cx="580" cy="470" r="80" fill="none" stroke="#2b2f33" stroke-width="10"/>
  <circle cx="580" cy="470" r="70" fill="url(#wheelGrad)"/>
  <circle cx="580" cy="470" r="70" fill="none" stroke="#6f7b84" stroke-width="3"/>
  <g stroke="#9aa6af" stroke-width="3">
    <line x1="580" y1="400" x2="580" y2="540"/>
    <line x1="510" y1="470" x2="650" y2="470"/>
    <line x1="530" y1="420" x2="630" y2="520"/>
    <line x1="630" y1="420" x2="530" y2="520"/>
  </g>
  <circle cx="580" cy="470" r="10" fill="#3a4147"/>
  <circle cx="580" cy="470" r="5" fill="#1f2428"/>

  <!-- frame (red) -->
  <g stroke="url(#bikeGrad)" stroke-width="11" stroke-linecap="round" fill="none">
    <line x1="220" y1="470" x2="400" y2="470"/>   <!-- chainstay -->
    <line x1="220" y1="470" x2="360" y2="345"/>   <!-- seatstay -->
    <line x1="400" y1="470" x2="360" y2="345"/>   <!-- seat tube -->
    <line x1="400" y1="470" x2="545" y2="360"/>   <!-- down tube -->
    <line x1="360" y1="345" x2="545" y2="355"/>   <!-- top tube -->
    <line x1="545" y1="355" x2="580" y2="470"/>   <!-- fork -->
    <line x1="545" y1="355" x2="538" y2="315"/>   <!-- head stem -->
  </g>
  <!-- headlight detail -->
  <circle cx="545" cy="355" r="7" fill="#ffd97a" opacity="0.9"/>
  <!-- seat -->
  <path d="M330,338 Q360,325 392,338 L382,348 L340,348 Z" fill="#3a2a1e"/>
  <!-- saddle post -->
  <line x1="360" y1="345" x2="360" y2="335" stroke="#4c5358" stroke-width="6"/>
  <!-- handlebars -->
  <path d="M538,315 Q520,298 495,302" stroke="#2b2f33" stroke-width="8" fill="none" stroke-linecap="round"/>
  <circle cx="493" cy="302" r="6" fill="#14181b"/>
  <!-- crankset + pedals -->
  <circle cx="400" cy="470" r="18" fill="none" stroke="#4c5358" stroke-width="6"/>
  <line x1="400" y1="470" x2="428" y2="494" stroke="#3a4147" stroke-width="8"/>
  <line x1="400" y1="470" x2="372" y2="446" stroke="#3a4147" stroke-width="8"/>
  <rect x="414" y="488" width="34" height="10" rx="3" fill="#1c1f22"/>
  <rect x="358" y="440" width="34" height="10" rx="3" fill="#1c1f22"/>

  <!-- ============ PELICAN ============ -->
  <!-- legs (behind body) to pedals -->
  <g stroke="#d98a2b" stroke-width="9" stroke-linecap="round" fill="none">
    <path d="M352,318 C348,360 352,410 374,442"/>
    <path d="M368,322 C380,370 402,440 428,490"/>
  </g>
  <!-- feet on pedals -->
  <path d="M360,440 L392,440 M364,446 L388,446" stroke="#c97b2b" stroke-width="6" stroke-linecap="round"/>
  <path d="M414,490 L448,490 M418,496 L444,496" stroke="#c97b2b" stroke-width="6" stroke-linecap="round"/>

  <!-- tail feathers -->
  <g fill="url(#wingGrad)">
    <path d="M248,286 L128,244 L168,278 L120,272 L178,296 L138,306 L196,316 L158,330 L240,318 Z"/>
    <path d="M252,290 L148,318 L210,320 L186,338 L248,322 Z" opacity="0.85"/>
  </g>
  <path d="M160,262 L246,292 M152,290 L242,302 M176,322 L240,314" stroke="#153f6b" stroke-width="2.5" opacity="0.55"/>

  <!-- body -->
  <path d="M238,296 C240,238 300,214 356,224 C410,234 432,270 424,306 C416,340 372,352 322,346 C272,340 238,330 238,296 Z" fill="url(#pelicanGrad)"/>
  <!-- body highlight -->
  <path d="M268,252 C300,228 348,228 384,244" stroke="#8ec4ee" stroke-width="7" fill="none" stroke-linecap="round" opacity="0.5"/>
  <!-- belly shading -->
  <path d="M262,320 C300,344 360,346 402,326 C388,346 330,352 288,340 Z" fill="#0e3a66" opacity="0.45"/>

  <!-- neck -->
  <path d="M398,250 C420,214 436,196 462,180 C482,168 496,166 504,170 L510,196 C494,190 478,196 462,208 C440,226 424,252 414,276 C402,272 394,262 398,250 Z" fill="url(#pelicanGrad)"/>
  <path d="M410,250 C428,218 448,198 470,186" stroke="#8ec4ee" stroke-width="5" fill="none" stroke-linecap="round" opacity="0.5"/>

  <!-- head -->
  <circle cx="508" cy="172" r="28" fill="url(#pelicanGrad)"/>
  <!-- crest -->
  <path d="M488,150 C480,138 486,128 496,132 C494,120 508,116 512,128 C520,118 532,124 526,136 C536,134 540,144 530,150 Z" fill="#2f7cc4"/>
  <!-- eye -->
  <circle cx="514" cy="164" r="7" fill="#f4f8fb"/>
  <circle cx="516" cy="165" r="3.6" fill="#14181b"/>
  <circle cx="514.6" cy="163.4" r="1.3" fill="#ffffff"/>

  <!-- beak: upper mandible + pouch -->
  <path d="M520,158 C560,152 610,164 652,186 L646,196 C606,180 560,172 524,174 Z" fill="url(#beakGrad)"/>
  <path d="M524,174 C548,214 596,224 646,196 L640,192 C596,212 556,202 532,178 C528,176 525,174 524,174 Z" fill="#e08b2e"/>
  <path d="M532,182 C556,208 592,214 632,196" stroke="#a35c18" stroke-width="2.5" fill="none" opacity="0.6"/>
  <circle cx="648" cy="190" r="3" fill="#8a4a12"/>

  <!-- wing (over body) -->
  <path d="M286,258 C318,238 366,240 396,262 C416,278 414,300 396,308 C368,320 320,316 294,300 C276,288 272,270 286,258 Z" fill="url(#wingGrad)"/>
  <g stroke="#123b63" stroke-width="2.5" fill="none" opacity="0.6">
    <path d="M300,268 C330,258 368,260 392,274"/>
    <path d="M296,282 C328,272 366,274 392,288"/>
    <path d="M300,296 C328,288 360,290 384,300"/>
  </g>
  <path d="M300,252 C330,240 366,242 388,256" stroke="#8ec4ee" stroke-width="5" fill="none" stroke-linecap="round" opacity="0.45"/>
</svg>
```