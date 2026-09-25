```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="100%" height="100%">
  <defs>
    <!-- Sky Gradient -->
    <linearGradient id="skyGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#02000a" />
      <stop offset="40%" stop-color="#0a0020" />
      <stop offset="70%" stop-color="#140040" />
      <stop offset="100%" stop-color="#003366" />
    </linearGradient>

    <!-- Building Gradients -->
    <linearGradient id="bldg1" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#1a0033" />
      <stop offset="100%" stop-color="#05001a" />
    </linearGradient>
    <linearGradient id="bldg2" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#001a33" />
      <stop offset="100%" stop-color="#000a1a" />
    </linearGradient>
    <linearGradient id="bldg3" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#2a0033" />
      <stop offset="100%" stop-color="#0a001a" />
    </linearGradient>
    <linearGradient id="bldg4" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#001a2a" />
      <stop offset="100%" stop-color="#000a15" />
    </linearGradient>

    <!-- Reflection Gradient -->
    <linearGradient id="reflection" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="rgba(0, 255, 255, 0.15)" />
      <stop offset="100%" stop-color="rgba(0, 255, 255, 0)" />
    </linearGradient>

    <!-- Planet Gradient -->
    <radialGradient id="planetGrad" cx="30%" cy="30%" r="70%">
      <stop offset="0%" stop-color="#ff66cc" />
      <stop offset="50%" stop-color="#9900cc" />
      <stop offset="100%" stop-color="#1a0033" />
    </radialGradient>

    <!-- Moon Glow Gradient -->
    <radialGradient id="moonGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="rgba(255, 102, 204, 0.4)" />
      <stop offset="100%" stop-color="rgba(255, 102, 204, 0)" />
    </radialGradient>

    <!-- Fog Gradient -->
    <radialGradient id="fogGrad" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="rgba(0, 255, 255, 0.1)" />
      <stop offset="100%" stop-color="rgba(0, 255, 255, 0)" />
    </radialGradient>
    <radialGradient id="fogGradPink" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="rgba(255, 0, 255, 0.1)" />
      <stop offset="100%" stop-color="rgba(255, 0, 255, 0)" />
    </radialGradient>

    <!-- Glow Filters -->
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="3" result="blur" />
      <feMerge>
        <feMergeNode in="blur" />
        <feMergeNode in="blur" />
        <feMergeNode in="SourceGraphic" />
      </feMerge>
    </filter>
    <filter id="glowStrong" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="6" result="blur" />
      <feMerge>
        <feMergeNode in="blur" />
        <feMergeNode in="blur" />
        <feMergeNode in="SourceGraphic" />
      </feMerge>
    </filter>

    <!-- Window Patterns -->
    <pattern id="windows1" width="20" height="30" patternUnits="userSpaceOnUse">
      <rect x="2" y="5" width="6" height="10" fill="#00ffff" opacity="0.4" />
      <rect x="12" y="5" width="4" height="8" fill="#ff00ff" opacity="0.2" />
      <rect x="2" y="20" width="8" height="6" fill="#00ccff" opacity="0.3" />
      <rect x="14" y="18" width="4" height="10" fill="#ffcc00" opacity="0.5" />
    </pattern>
    <pattern id="windows2" width="15" height="25" patternUnits="userSpaceOnUse">
      <rect x="2" y="2" width="5" height="15" fill="#ff00ff" opacity="0.5" />
      <rect x="9" y="5" width="4" height="10" fill="#00ffff" opacity="0.3" />
    </pattern>
    <pattern id="windows3" width="25" height="40" patternUnits="userSpaceOnUse">
      <rect x="3" y="5" width="10" height="15" fill="#00ffff" opacity="0.2" />
      <rect x="15" y="10" width="8" height="20" fill="#ff00ff" opacity="0.4" />
      <rect x="5" y="25" width="6" height="10" fill="#cc00ff" opacity="0.6" />
    </pattern>

    <!-- Grid Pattern -->
    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(0, 255, 255, 0.05)" stroke-width="1" />
    </pattern>

    <!-- Motion Paths -->
    <path id="path1" d="M-50,200 Q300,180 850,220" />
    <path id="path2" d="M850,300 Q500,320 150,280" />
    <path id="path3" d="M-50,400 Q400,350 850,450" />
    <path id="path4" d="M850,120 Q400,150 -50,180" />
    <path id="path5" d="M200,-50 Q250,300 300,650" />
  </defs>

  <!-- Background Sky -->
  <rect width="800" height="600" fill="url(#skyGrad)" />

  <!-- Stars -->
  <g fill="#ffffff">
    <circle cx="50" cy="50" r="1.5" opacity="0.8"><animate attributeName="opacity" values="0.8;0.2;0.8" dur="3s" repeatCount="indefinite" /></circle>
    <circle cx="150" cy="80" r="1" opacity="0.5" />
    <circle cx="250" cy="30" r="2" opacity="0.9"><animate attributeName="opacity" values="0.9;0.3;0.9" dur="4s" repeatCount="indefinite" /></circle>
    <circle cx="400" cy="60" r="1" opacity="0.4" />
    <circle cx="500" cy="40" r="1.5" opacity="0.7" />
    <circle cx="700" cy="70" r="2" opacity="0.8"><animate attributeName="opacity" values="0.8;0.1;0.8" dur="5s" repeatCount="indefinite" /></circle>
    <circle cx="750" cy="120" r="1" opacity="0.5" />
    <circle cx="80" cy="150" r="1" opacity="0.6" />
    <circle cx="320" cy="100" r="1.5" opacity="0.3" />
    <circle cx="600" cy="100" r="1" opacity="0.7" />
    <circle cx="420" cy="140" r="1" opacity="0.5" />
    <circle cx="180" cy="180" r="2" opacity="0.6" />
    <circle cx="680" cy="180" r="1.5" opacity="0.4" />
    <circle cx="100" cy="250" r="1" opacity="0.8" />
    <circle cx="350" cy="200" r="1.5" opacity="0.2" />
    <circle cx="550" cy="130" r="1" opacity="0.9" />
  </g>

  <!-- Large Planet / Moon -->
  <g>
    <circle cx="620" cy="220" r="140" fill="url(#moonGlow)">
      <animate attributeName="r" values="140;150;140" dur="6s" repeatCount="indefinite" />
    </circle>
    <circle cx="620" cy="220" r="100" fill="url(#planetGrad)" />
    <!-- Planet Craters -->
    <circle cx="580" cy="180" r="15" fill="rgba(0,0,0,0.3)" />
    <circle cx="650" cy="240" r="22" fill="rgba(0,0,0,0.2)" />
    <circle cx="600" cy="260" r="10" fill="rgba(0,0,0,0.4)" />
    <circle cx="660" cy="180" r="8" fill="rgba(0,0,0,0.3)" />
    <!-- Planet Ring -->
    <ellipse cx="620" cy="220" rx="160" ry="30" fill="none" stroke="#00ffff" stroke-width="2" opacity="0.4" transform="rotate(-15 620 220)" filter="url(#glow)" />
    <ellipse cx="620" cy="220" rx="170" ry="35" fill="none" stroke="#ff00ff" stroke-width="1" opacity="0.3" transform="rotate(-15 620 220)" />
  </g>

  <!-- Distant City Skyline -->
  <g fill="#05001a">
    <path d="M0,450 L30,380 L60,450 L100,360 L140,450 L180,390 L220,450 L260,350 L300,450 L340,400 L380,450 L420,370 L460,450 L500,390 L540,450 L580,420 L620,450 L660,380 L700,450 L740,390 L800,450 L800,600 L0,600 Z" />
    <!-- Distant City Lights -->
    <rect x="30" y="390" width="2" height="4" fill="#00ffff" opacity="0.6" />
    <rect x="35" y="420" width="2" height="4" fill="#ff00ff" opacity="0.8" />
    <rect x="100" y="370" width="3" height="5" fill="#00ffff" opacity="0.5" />
    <rect x="120" y="400" width="2" height="3" fill="#ffcc00" opacity="0.7" />
    <rect x="260" y="360" width="3" height="6" fill="#ff00ff" opacity="0.6" />
    <rect x="280" y="410" width="2" height="4" fill="#00ffff" opacity="0.8" />
    <rect x="420" y="380" width="4" height="5" fill="#00ffff" opacity="0.4" />
    <rect x="450" y="400" width="2" height="4" fill="#ff00ff" opacity="0.9" />
    <rect x="660" y="390" width="3" height="5" fill="#ff00ff" opacity="0.7" />
    <rect x="680" y="420" width="2" height="3" fill="#00ffff" opacity="0.5" />
  </g>

  <!-- Midground Skyscrapers -->
  <g>
    <!-- Building 1 (Left) -->
    <rect x="20" y="180" width="100" height="420" fill="url(#bldg1)" />
    <rect x="20" y="180" width="100" height="420" fill="url(#windows1)" />
    <rect x="25" y="200" width="4" height="400" fill="#ff00ff" opacity="0.8" filter="url(#glow)" />
    <rect x="110" y="250" width="5" height="350" fill="#00ffff" opacity="0.8" filter="url(#glow)" />
    <!-- Rooftop Structure -->
    <rect x="50" y="150" width="40" height="30" fill="#0a0a1a" />
    <line x1="70" y1="150" x2="70" y2="120" stroke="#ff00ff" stroke-width="2" filter="url(#glow)" />
    <circle cx="70" cy="120" r="3" fill="#00ffff" filter="url(#glow)"><animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite" /></circle>

    <!-- Building 2 (Center-Left) -->
    <rect x="140" y="100" width="120" height="500" fill="url(#bldg2)" />
    <rect x="140" y="100" width="120" height="500" fill="url(#windows2)" />
    <rect x="145" y="120" width="3" height="480" fill="#00ffff" opacity="0.6" filter="url(#glow)" />
    <rect x="255" y="150" width="4" height="450" fill="#ff00ff" opacity="0.9" filter="url(#glow)" />
    <!-- Antenna -->
    <line x1="200" y1="100" x2="200" y2="60" stroke="#00ffff" stroke-width="2" filter="url(#glow)" />
    <circle cx="200" cy="60" r="4" fill="#ff00ff" filter="url(#glow)" />
    <!-- Horizontal Neon -->
    <rect x="150" y="180" width="100" height="4" fill="#ff00ff" opacity="0.8" filter="url(#glow)" />
    <rect x="150" y="220" width="80" height="3" fill="#00ffff" opacity="0.8" filter="url(#glow)" />

    <!-- Building 3 (Center) -->
    <rect x="280" y="150" width="140" height="450" fill="url(#bldg3)" />
    <rect x="280" y="150" width="140" height="450" fill="url(#windows3)" />
    <rect x="285" y="170" width="4" height="430" fill="#ff00ff" opacity="0.7" filter="url(#glow)" />
    <rect x="410" y="200" width="5" height="400" fill="#00ffff" opacity="0.8" filter="url(#glow)" />
    <!-- Rooftop -->
    <rect x="320" y="120" width="60" height="30" fill="#0d0d1a" />
    <rect x="340" y="100" width="20" height="20" fill="#0d0d1a" />
    <line x1="350" y1="100" x2="350" y2="70" stroke="#ff00ff" stroke-width="2" filter="url(#glow)" />
    <!-- Horizontal Neon -->
    <rect x="300" y="250" width="100" height="5" fill="#00ffff" opacity="0.9" filter="url(#glow)" />
    <rect x="310" y="280" width="80" height="3" fill="#ff00ff" opacity="0.7" filter="url(#glow)" />

    <!-- Building 4 (Center-Right) -->
    <rect x="440" y="120" width="110" height="480" fill="url(#bldg4)" />
    <rect x="440" y="120" width="110" height="480" fill="url(#windows1)" />
    <rect x="445" y="140" width="4" height="460" fill="#00ffff" opacity="0.8" filter="url(#glow)" />
    <rect x="540" y="180" width="5" height="420" fill="#ff00ff" opacity="0.6" filter="url(#glow)" />
    <!-- Rooftop -->
    <rect x="470" y="90" width="50" height="30" fill="#0a0a15" />
    <line x1="495" y1="90" x2="495" y2="50" stroke="#00ffff" stroke-width="2" filter="url(#glow)" />
    <circle cx="495" cy="50" r="4" fill="#ff00ff" filter="url(#glow)"><animate attributeName="opacity" values="1;0.2;1" dur="2s" repeatCount="indefinite" /></circle>

    <!-- Building 5 (Right) -->
    <rect x="570" y="160" width="130" height="440" fill="url(#bldg1)" />
    <rect x="570" y="160" width="130" height="440" fill="url(#windows2)" />
    <rect x="575" y="180" width="4" height="420" fill="#ff00ff" opacity="0.7" filter="url(#glow)" />
    <rect x="690" y="220" width="5" height="380" fill="#00ffff" opacity="0.8" filter="url(#glow)" />
    <!-- Horizontal -->
    <rect x="580" y="300" width="110" height="4" fill="#00ffff" opacity="0.8" filter="url(#glow)" />
    <rect x="600" y="350" width="80" height="3" fill="#ff00ff" opacity="0.9" filter="url(#glow)" />
    <!-- Rooftop -->
    <rect x="610" y="130" width="50" height="30" fill="#0d0d1a" />
    <line x1="635" y1="130" x2="635" y2="90" stroke="#ff00ff" stroke-width="2" filter="url(#glow)" />

    <!-- Building 6 (Far Right) -->
    <rect x="720" y="220" width="100" height="380" fill="url(#bldg2)" />
    <rect x="720" y="220" width="100" height="380" fill="url(#windows3)" />
    <rect x="725" y="240" width="3" height="360" fill="#00ffff" opacity="0.6" filter="url(#glow)" />
    <rect x="810" y="270" width="4" height="330" fill="#ff00ff" opacity="0.8" filter="url(#glow)" />
    <line x1="770" y1="220" x2="770" y2="180" stroke="#ff00ff" stroke-width="2" filter="url(#glow)" />
  </g>

  <!-- Holographic Billboards -->
  <g>
    <!-- Billboard 1 (Cyan) -->
    <g>
      <rect x="160" y="220" width="80" height="50" fill="rgba(0, 255, 255, 0.1)" stroke="#00ffff" stroke-width="2" filter="url(#glow)" />
      <!-- Text lines -->
      <line x1="168" y1="230" x2="232" y2="230" stroke="#00ffff" stroke-width="2" opacity="0.8" />
      <line x1="168" y1="238" x2="210" y2="238" stroke="#00ffff" stroke-width="2" opacity="0.6" />
      <line x1="168" y1="246" x2="220" y2="246" stroke="#00ffff" stroke-width="2" opacity="0.4" />
      <line x1="168" y1="254" x2="200" y2="254" stroke="#00ffff" stroke-width="2" opacity="0.7" />
      <line x1="168" y1="262" x2="228" y2="262" stroke="#00ffff" stroke-width="2" opacity="0.5" />
      <!-- Animated Scanning Line -->
      <rect x="160" y="220" width="80" height="2" fill="#ffffff" opacity="0.8" filter="url(#glow)">
        <animate attributeName="y" values="220;270;220" dur="3s" repeatCount="indefinite" />
      </rect>
    </g>

    <!-- Billboard 2 (Pink) -->
    <g>
      <rect x="500" y="180" width="90" height="70" fill="rgba(255, 0, 255, 0.1)" stroke="#ff00ff" stroke-width="2" filter="url(#glow)" />
      <!-- Text lines -->
      <line x1="510" y1="195" x2="580" y2="195" stroke="#ff00ff" stroke-width="3" opacity="0.9" />
      <line x1="510" y1="205" x2="560" y2="205" stroke="#ff00ff" stroke-width="2" opacity="0.7" />
      <line x1="510" y1="215" x2="590" y2="215" stroke="#ff00ff" stroke-width="2" opacity="0.5" />
      <line x1="510" y1="225" x2="570" y2="225" stroke="#ff00ff" stroke-width="2" opacity="0.8" />
      <line x1="510" y1="235" x2="550" y2="235" stroke="#ff00ff" stroke-width="2" opacity="0.6" />
      <!-- Animated Progress Bar -->
      <rect x="510" y="242" width="20" height="4" fill="#ff00ff" filter="url(#glow)">
        <animate attributeName="width" values="20;70;20" dur="4s" repeatCount="indefinite" />
      </rect>
    </g>

    <!-- Billboard 3 (Vertical, Purple) -->
    <g>
      <rect x="650" y="80" width="40" height="120" fill="rgba(136, 0, 255, 0.1)" stroke="#8a00ff" stroke-width="2" filter="url(#glow)" />
      <!-- Text lines -->
      <line x1="660" y1="90" x2="660" y2="190" stroke="#8a00ff" stroke-width="3" opacity="0.8" />
      <line x1="670" y1="95" x2="670" y2="185" stroke="#8a00ff" stroke-width="2" opacity="0.6" />
      <line x1="680" y1="100" x2="680" y2="180" stroke="#8a00ff" stroke-width="2" opacity="0.4" />
      <!-- Animated Flicker -->
      <rect x="650" y="80" width="40" height="120" fill="none" stroke="#ffffff" stroke-width="1" opacity="0">
        <animate attributeName="opacity" values="0;1;0;1;0" dur="2s" repeatCount="indefinite" />
      </rect>
    </g>

    <!-- Holographic Projection (Abstract) -->
    <g opacity="0.4">
      <polygon points="400,50 370,100 430,100" fill="none" stroke="#00ffff" stroke-width="2" filter="url(#glow)">
        <animate attributeName="opacity" values="0.4;0.8;0.4" dur="3s" repeatCount="indefinite" />
      </polygon>
      <polygon points="400,50 380,100 420,100" fill="none" stroke="#ff00ff" stroke-width="1" filter="url(#glow)" />
      <!-- Orbiting Drones -->
      <circle cx="400" cy="75" r="2" fill="#00ffff" filter="url(#glow)">
        <animateTransform attributeName="transform" type="rotate" from="0 400 75" to="360 400 75" dur="4s" repeatCount="indefinite" />
      </circle>
    </g>
  </g>

  <!-- Foreground Buildings / Silhouettes -->
  <g fill="#030008">
    <!-- Left Foreground -->
    <rect x="-20" y="320" width="120" height="280" />
    <rect x="10" y="280" width="60" height="40" />
    <rect x="30" y="250" width="20" height="30" />
    <!-- Right Foreground -->
    <rect x="700" y="300" width="120" height="300" />
    <rect x="730" y="260" width="60" height="40" />
    <rect x="750" y="230" width="20" height="30" />
    <!-- Bottom Foreground -->
    <rect x="300" y="500" width="200" height="100" />
    <rect x="340" y="480" width="120" height="20" />
  </g>

  <!-- Foreground Details & Neon -->
  <g>
    <!-- Left Foreground Neon -->
    <rect x="80" y="350" width="4" height="250" fill="#ff00ff" opacity="0.9" filter="url(#glow)" />
    <rect x="90" y="400" width="10" height="3" fill="#00ffff" opacity="0.8" filter="url(#glow)" />
    <rect x="90" y="420" width="15" height="3" fill="#00ffff" opacity="0.6" filter="url(#glow)" />
    <rect x="90" y="440" width="8" height="3" fill="#00ffff" opacity="0.7" filter="url(#glow)" />
    <!-- Right Foreground Neon -->
    <rect x="720" y="330" width="5" height="270" fill="#00ffff" opacity="0.8" filter="url(#glow)" />
    <rect x="690" y="380" width="20" height="4" fill="#ff00ff" opacity="0.9" filter="url(#glow)" />
    <rect x="680" y="400" width="30" height="4" fill="#ff00ff" opacity="0.5" filter="url(#glow)" />
    <!-- Bottom Foreground Neon -->
    <rect x="320" y="510" width="160" height="4" fill="#00ffff" opacity="0.7" filter="url(#glow)" />
    <rect x="350" y="530" width="100" height="4" fill="#ff00ff" opacity="0.8" filter="url(#glow)" />
    <rect x="400" y="490" width="6" height="10" fill="#00ffff" filter="url(#glow)"><animate attributeName="opacity" values="1;0.2;1" dur="1.5s" repeatCount="indefinite" /></rect>
  </g>

  <!-- Flying Vehicles -->
  <g>
    <!-- Vehicle 1 (Left to Right, High) -->
    <g>
      <polygon points="0,0 20,5 0,10" fill="#ff00ff" filter="url(#glow)" />
      <path d="M-15,5 L0,5" stroke="#ff00ff" stroke-width="2" filter="url(#glow)" />
      <animateMotion dur="8s" repeatCount="indefinite" rotate="auto">
        <mpath href="#path1" />
      </animateMotion>
    </g>

    <!-- Vehicle 2 (Right to Left, Mid) -->
    <g>
      <polygon points="0,0 15,4 0,8" fill="#00ffff" filter="url(#glow)" />
      <path d="M-10,4 L0,4" stroke="#00ffff" stroke-width="2" filter="url(#glow)" />
      <animateMotion dur="12s" repeatCount="indefinite" rotate="auto">
        <mpath href="#path2" />
      </animateMotion>
    </g>

    <!-- Vehicle 3 (Left to Right, Low) -->
    <g>
      <polygon points="0,0 25,6 0,12" fill="#8a00ff" filter="url(#glow)" />
      <path d="M-20,6 L0,6" stroke="#8a00ff" stroke-width="3" filter="url(#glow)" />
      <animateMotion dur="15s" repeatCount="indefinite" rotate="auto" begin="1s">
        <mpath href="#path3" />
      </animateMotion>
    </g>

    <!-- Vehicle 4 (Right to Left, High) -->
    <g>
      <polygon points="0,0 18,5 0,10" fill="#ffcc00" filter="url(#glow)" />
      <path d="M-12,5 L0,5" stroke="#ffcc00" stroke-width="2" filter="url(#glow)" />
      <animateMotion dur="10s" repeatCount="indefinite" rotate="auto" begin="3s">
        <mpath href="#path4" />
      </animateMotion>
    </g>

    <!-- Vehicle 5 (Diagonal, Bottom to Top) -->
    <g>
      <polygon points="0,0 10,3 0,6" fill="#00ffff" filter="url(#glow)" />
      <path d="M-8,3 L0,3" stroke="#00ffff" stroke-width="2" filter="url(#glow)" />
      <animateMotion dur="7s" repeatCount="indefinite" rotate="auto" begin="2s">
        <mpath href="#path5" />
      </animateMotion>
    </g>

    <!-- Drone Swarm (Small glowing dots) -->
    <g>
      <circle cx="0" cy="0" r="2" fill="#00ffff" filter="url(#glow)" />
      <circle cx="5" cy="5" r="2" fill="#00ffff" filter="url(#glow)" />
      <circle cx="10" cy="0" r="2" fill="#00ffff" filter="url(#glow)" />
      <circle cx="15" cy="5" r="2" fill="#00ffff" filter="url(#glow)" />
      <animateMotion dur="20s" repeatCount="indefinite" rotate="auto">
        <mpath href="#path2" />
      </animateMotion>
    </g>
  </g>

  <!-- Atmosphere / Fog -->
  <g>
    <ellipse cx="200" cy="550" rx="300" ry="100" fill="url(#fogGrad)">
      <animate attributeName="cx" values="200;250;200" dur="10s" repeatCount="indefinite" />
    </ellipse>
    <ellipse cx="600" cy="580" rx="400" ry="120" fill="url(#fogGradPink)">
      <animate attributeName="cx" values="600;550;600" dur="12s" repeatCount="indefinite" />
    </ellipse>
    <ellipse cx="400" cy="600" rx="600" ry="150" fill="url(#fogGrad)" opacity="0.5" />
  </g>

  <!-- Ground Reflections and Grid -->
  <g>
    <!-- Reflective Ground -->
    <rect x="0" y="520" width="800" height="80" fill="url(#reflection)" />
    
    <!-- Perspective Grid -->
    <rect x="0" y="520" width="800" height="80" fill="url(#grid)" />
    
    <!-- Grid Perspective Lines -->
    <path d="M0,600 L400,520 L800,600" fill="none" stroke="rgba(0, 255, 255, 0.1)" stroke-width="1" />
    <path d="M100,600 L400,520 L700,600" fill="none" stroke="rgba(0, 255, 255, 0.1)" stroke-width="1" />
    <path d="M200,600 L400,520 L600,600" fill="none" stroke="rgba(0, 255, 255, 0.1)" stroke-width="1" />
    <path d="M300,600 L400,520 L500,600" fill="none" stroke="rgba(0, 255, 255, 0.1)" stroke-width="1" />
    
    <!-- Neon Reflections on the ground -->
    <rect x="80" y="530" width="4" height="40" fill="#ff00ff" opacity="0.3" filter="url(#glow)" />
    <rect x="720" y="530" width="5" height="40" fill="#00ffff" opacity="0.3" filter="url(#glow)" />
    <rect x="320" y="540" width="160" height="3" fill="#00ffff" opacity="0.4" filter="url(#glow)" />
    <rect x="350" y="560" width="100" height="3" fill="#ff00ff" opacity="0.3" filter="url(#glow)" />
  </g>

  <!-- Additional Detailed Elements: Wires, Antennas, Small Signs -->
  <g>
    <!-- Wires between buildings -->
    <path d="M120,250 Q200,280 280,200" fill="none" stroke="#00ffff" stroke-width="1" opacity="0.4" />
    <path d="M280,220 Q360,260 440,180" fill="none" stroke="#ff00ff" stroke-width="1" opacity="0.4" />
    <path d="M440,200 Q520,240 570,200" fill="none" stroke="#00ffff" stroke-width="1" opacity="0.4" />
    
    <!-- Tiny Neon Signs -->
    <rect x="130" y="300" width="20" height="4" fill="#ffcc00" opacity="0.8" filter="url(#glow)" />
    <rect x="260" y="350" width="15" height="3" fill="#00ffff" opacity="0.9" filter="url(#glow)" />
    <rect x="420" y="400" width="25" height="4" fill="#ff00ff" opacity="0.7" filter="url(#glow)" />
    <rect x="580" y="280" width="30" height="4" fill="#00ffff" opacity="0.8" filter="url(#glow)" />
    
    <!-- Satellite Dishes / Tech details -->
    <circle cx="180" cy="130" r="8" fill="none" stroke="#00ffff" stroke-width="1.5" opacity="0.6" />
    <line x1="180" y1="130" x2="190" y2="140" stroke="#00ffff" stroke-width="1" opacity="0.6" />
    <circle cx="520" cy="160" r="6" fill="none" stroke="#ff00ff" stroke-width="1.5" opacity="0.6" />
    <line x1="520" y1="160" x2="530" y2="150" stroke="#ff00ff" stroke-width="1" opacity="0.6" />
    
    <!-- Floating Data Particles -->
    <circle cx="300" cy="300" r="1.5" fill="#00ffff" opacity="0.8" filter="url(#glow)">
      <animate attributeName="cy" values="300;250;300" dur="4s" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0.8;0;0.8" dur="4s" repeatCount="indefinite" />
    </circle>
    <circle cx="450" cy="350" r="1" fill="#ff00ff" opacity="0.8" filter="url(#glow)">
      <animate attributeName="cy" values="350;280;350" dur="5s" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0.8;0;0.8" dur="5s" repeatCount="indefinite" />
    </circle>
    <circle cx="600" cy="320" r="2" fill="#8a00ff" opacity="0.8" filter="url(#glow)">
      <animate attributeName="cy" values="320;260;320" dur="6s" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0.8;0;0.8" dur="6s" repeatCount="indefinite" />
    </circle>
  </g>

  <!-- Finishing Touches: Lens Flares & Glowing Orbs -->
  <g>
    <circle cx="620" cy="220" r="150" fill="none" stroke="rgba(0, 255, 255, 0.1)" stroke-width="1" />
    <circle cx="620" cy="220" r="200" fill="none" stroke="rgba(255, 0, 255, 0.05)" stroke-width="1" />
    
    <!-- Global Lens Flare -->
    <circle cx="400" cy="200" r="300" fill="none" stroke="rgba(0, 255, 255, 0.03)" stroke-width="2" />
    <circle cx="400" cy="200" r="400" fill="none" stroke="rgba(255, 0, 255, 0.02)" stroke-width="1" />
  </g>
</svg>
```