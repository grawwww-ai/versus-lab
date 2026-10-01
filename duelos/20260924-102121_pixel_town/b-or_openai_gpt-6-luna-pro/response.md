```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Little Town, Big Day</title>
<style>
  * { box-sizing: border-box; }
  html, body {
    margin: 0; width: 100%; height: 100%; overflow: hidden;
    background: #17243a;
  }
  body { display: grid; place-items: center; }
  canvas {
    width: min(100vw, 177.7778vh);
    height: min(100vh, 56.25vw);
    display: block;
    image-rendering: pixelated;
    image-rendering: crisp-edges;
  }
</style>
</head>
<body>
<canvas id="town" width="320" height="180" aria-label="An animated pixel-art town"></canvas>
<script>
(() => {
  const canvas = document.getElementById("town");
  const ctx = canvas.getContext("2d");
  ctx.imageSmoothingEnabled = false;

  const W = 320, H = 180;
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const smooth = (a, b, x) => {
    const t = clamp((x - a) / (b - a));
    return t * t * (3 - 2 * t);
  };
  const hex = h => [
    parseInt(h.slice(1, 3), 16),
    parseInt(h.slice(3, 5), 16),
    parseInt(h.slice(5, 7), 16)
  ];
  const mix = (a, b, t) => {
    const A = hex(a), B = hex(b), u = clamp(t);
    return "#" + A.map((v, i) => Math.round(v + (B[i] - v) * u)
      .toString(16).padStart(2, "0")).join("");
  };
  const rgba = (color, alpha) => {
    const [r, g, b] = hex(color);
    return `rgba(${r},${g},${b},${alpha})`;
  };
  const rect = (x, y, w, h, color) => {
    ctx.fillStyle = color;
    ctx.fillRect(Math.round(x), Math.round(y), Math.round(w), Math.round(h));
  };
  const poly = (points, color) => {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.moveTo(points[0][0], points[0][1]);
    for (let i = 1; i < points.length; i++) ctx.lineTo(points[i][0], points[i][1]);
    ctx.closePath();
    ctx.fill();
  };
  const line = (x1, y1, x2, y2, color, width = 1) => {
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.beginPath();
    ctx.moveTo(Math.round(x1) + .5, Math.round(y1) + .5);
    ctx.lineTo(Math.round(x2) + .5, Math.round(y2) + .5);
    ctx.stroke();
  };

  // A full cycle is twenty seconds. Palette keyframes give the sky a gradual,
  // continuous dawn → day → sunset → night transition.
  const skyKeys = [
    [0.00, "#273957", "#f5a576"],
    [0.20, "#4599c5", "#a9d6d1"],
    [0.46, "#378fc0", "#c6e3d1"],
    [0.68, "#593d70", "#f09a70"],
    [0.84, "#101d3d", "#314a72"],
    [0.95, "#172342", "#685071"],
    [1.00, "#273957", "#f5a576"]
  ];
  function skyColors(t) {
    for (let i = 0; i < skyKeys.length - 1; i++) {
      const a = skyKeys[i], b = skyKeys[i + 1];
      if (t >= a[0] && t <= b[0]) {
        const u = smooth(a[0], b[0], t);
        return [mix(a[1], b[1], u), mix(a[2], b[2], u)];
      }
    }
    return ["#273957", "#f5a576"];
  }
  function nightAmount(t) {
    if (t < .72) return 0;
    if (t < .82) return smooth(.72, .82, t);
    if (t < .94) return 1;
    return 1 - smooth(.94, 1, t);
  }
  function rainAmount(t) {
    if (t < .52 || t > .73) return 0;
    return Math.min(smooth(.52, .56, t), 1 - smooth(.69, .73, t));
  }
  function tone(color, night, sunset = 0) {
    let c = mix(color, "#26334d", night * .63);
    return mix(c, "#e98767", sunset * .18);
  }

  function drawSky(t, n, seconds) {
    const [top, bottom] = skyColors(t);
    const grad = ctx.createLinearGradient(0, 0, 0, 105);
    grad.addColorStop(0, top);
    grad.addColorStop(1, bottom);
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, W, 110);

    // Stars are fixed in place and softly twinkle after dusk.
    const starFade = clamp((n - .12) / .5);
    if (starFade > 0) {
      for (let i = 0; i < 42; i++) {
        const x = (i * 73 + 19) % 316 + 2;
        const y = (i * 41 + 7) % 67 + 4;
        const twinkle = .55 + .45 * Math.sin(seconds * 2.6 + i * 2.1);
        rect(x, y, i % 7 === 0 ? 2 : 1, i % 7 === 0 ? 2 : 1,
          rgba("#fff0bd", starFade * twinkle));
      }
    }

    // Sun follows a slow arc; the moon takes over during the dark hours.
    const sunProgress = clamp((t - .10) / .58);
    if (t > .07 && t < .70) {
      const x = 28 + sunProgress * 265;
      const y = 39 - Math.sin(sunProgress * Math.PI) * 20;
      const sunColor = mix("#ffe09a", "#fff3c2", n);
      rect(x - 5, y - 5, 11, 11, sunColor);
      rect(x - 3, y - 7, 7, 15, sunColor);
      rect(x - 7, y - 3, 15, 7, sunColor);
    }
    if (n > .25) {
      const moonAlpha = clamp((n - .25) * 2.4);
      const x = 249, y = 28;
      rect(x - 4, y - 5, 9, 12, rgba("#fff0c0", moonAlpha));
      rect(x - 2, y - 7, 6, 16, rgba("#fff0c0", moonAlpha));
      rect(x + 1, y - 6, 5, 12, rgba(top, moonAlpha));
    }

    // Slow, blocky clouds.
    const cloudX = (seconds * 4) % 390 - 55;
    for (let k = 0; k < 3; k++) {
      const x = ((cloudX + k * 137) % 390 + 390) % 390 - 55;
      const y = 19 + (k % 2) * 17;
      const cloud = mix("#c8d8d2", "#65718c", n * .75);
      rect(x, y + 4, 22, 5, rgba(cloud, .74));
      rect(x + 5, y, 12, 10, rgba(cloud, .74));
      rect(x + 17, y + 3, 12, 6, rgba(cloud, .74));
    }

    // Far hills and a tiny distant skyline.
    const hill = tone("#719b83", n, t > .5 && t < .75 ? .65 : 0);
    poly([[0, 89], [0, 78], [24, 69], [41, 80], [68, 68],
      [94, 81], [121, 72], [151, 83], [177, 67], [204, 82],
      [234, 70], [260, 82], [290, 68], [320, 80], [320, 106], [0, 106]], hill);
    const far = tone("#657d75", n);
    rect(42, 76, 7, 16, far); rect(51, 81, 10, 11, far);
    rect(183, 75, 8, 17, far); rect(193, 79, 13, 13, far);
    rect(278, 78, 9, 14, far);
  }

  function drawRoof(x, y, w, peakX, peakY, night, sunset, tile = true) {
    const outline = tone("#593a48", night);
    const roof = tone("#a84848", night, sunset);
    const roofLight = tone("#d06a56", night, sunset);
    poly([[x - 5, y + 2], [peakX, peakY], [x + w + 5, y + 2],
      [x + w + 3, y + 9], [peakX, peakY + 8], [x - 3, y + 9]], outline);
    poly([[x, y + 2], [peakX, peakY + 2], [x + w, y + 2],
      [x + w - 2, y + 7], [peakX, peakY + 7], [x + 2, y + 7]], roof);
    if (tile) {
      for (let row = 0; row < 3; row++) {
        const yy = y + 3 + row * 2;
        const start = x + row * 7;
        for (let tx = start; tx < x + w - row * 5; tx += 11) {
          rect(tx, yy, 5, 1, roofLight);
          rect(tx + 5, yy + 1, 2, 1, outline);
        }
      }
    }
  }

  function drawWindow(x, y, lit, night, sunset) {
    const frame = tone("#68464a", night);
    const glass = tone("#668b91", night, sunset);
    rect(x - 1, y - 1, 11, 12, frame);
    rect(x, y, 9, 10, lit ? "#ffd777" : glass);
    if (lit) {
      rect(x + 1, y + 1, 7, 8, "#f6bd60");
      rect(x + 4, y, 1, 10, "#a7654e");
      rect(x, y + 4, 9, 1, "#a7654e");
      rect(x + 1, y + 1, 2, 2, "#fff0ae");
    } else {
      rect(x + 4, y, 1, 10, tone("#48616d", night));
      rect(x, y + 4, 9, 1, tone("#48616d", night));
      rect(x + 1, y + 1, 2, 2, "#a6c2b0");
    }
  }

  function drawHouse(x, y, w, h, peakY, night, sunset, windows, door = true) {
    const wall = tone("#d9ad79", night, sunset);
    const shadow = tone("#a87560", night, sunset);
    const trim = tone("#754d4c", night);
    drawRoof(x, y, w, x + w / 2, peakY, night, sunset);
    rect(x, y + 5, w, h - 5, trim);
    rect(x + 2, y + 6, w - 4, h - 7, wall);
    rect(x + 2, y + h - 8, w - 4, 3, shadow);
    // Decorative timber framing.
    rect(x + 5, y + 9, 2, h - 20, tone("#bd855f", night));
    rect(x + w - 8, y + 9, 2, h - 20, tone("#bd855f", night));
    for (const win of windows) drawWindow(x + win[0], y + win[1], win[2], night, sunset);
    if (door) {
      rect(x + Math.floor(w / 2) - 5, y + h - 22, 11, 21, trim);
      rect(x + Math.floor(w / 2) - 3, y + h - 20, 7, 19,
        tone("#8b5948", night, sunset));
      rect(x + Math.floor(w / 2) + 2, y + h - 10, 1, 1, "#f6ce75");
    }
  }

  function drawTree(x, baseY, night) {
    rect(x - 2, baseY - 20, 5, 22, tone("#795344", night));
    rect(x - 1, baseY - 7, 3, 7, tone("#936047", night));
    const leaves = tone("#47785d", night);
    const lightLeaves = tone("#659266", night);
    rect(x - 12, baseY - 34, 24, 15, leaves);
    rect(x - 8, baseY - 40, 16, 12, lightLeaves);
    rect(x - 16, baseY - 28, 10, 11, lightLeaves);
    rect(x + 7, baseY - 29, 10, 12, leaves);
    rect(x - 9, baseY - 20, 18, 3, leaves);
    rect(x - 7, baseY - 36, 4, 3, tone("#83a66d", night));
  }

  function drawLamp(x, night, stage, seconds) {
    const lit = night > stage;
    if (lit) {
      const pulse = .75 + .25 * Math.sin(seconds * 4 + x);
      rect(x - 6, 91, 13, 13, rgba("#ffd878", night * .13 * pulse));
      rect(x - 4, 93, 9, 9, rgba("#ffd878", night * .2 * pulse));
    }
    rect(x, 101, 2, 32, tone("#584c50", night));
    rect(x - 3, 101, 8, 2, tone("#584c50", night));
    rect(x - 3, 96, 8, 6, tone("#4e4650", night));
    rect(x - 2, 97, 6, 4, lit ? "#ffe19a" : "#9c8466");
    rect(x - 4, 95, 10, 1, tone("#584c50", night));
    rect(x - 1, 104, 4, 1, tone("#8b7060", night));
  }

  function drawMillBlades(seconds, night) {
    const cx = 267, cy = 58;
    const angle = seconds * .72;
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(angle);
    const blade = tone("#f0d39a", night);
    const edge = tone("#85574c", night);
    for (let i = 0; i < 4; i++) {
      ctx.save();
      ctx.rotate(i * Math.PI / 2);
      rect(-2, -30, 4, 28, edge);
      rect(-1, -28, 2, 23, blade);
      rect(-6, -27, 12, 2, edge);
      rect(-5, -26, 10, 1, tone("#fff0be", night));
      rect(-8, -22, 16, 2, edge);
      rect(-7, -21, 14, 1, blade);
      ctx.restore();
    }
    ctx.restore();
    rect(cx - 4, cy - 4, 9, 9, tone("#70484a", night));
    rect(cx - 2, cy - 2, 5, 5, tone("#f3cf8a", night));
  }

  function drawSmoke(seconds, night) {
    for (let chimney = 0; chimney < 2; chimney++) {
      for (let i = 0; i < 5; i++) {
        const age = (seconds * .32 + i * .21 + chimney * .35) % 1;
        const x = (chimney ? 129 : 31) + Math.sin(seconds * 1.7 + i * 2 + chimney) * age * 5;
        const y = (chimney ? 57 : 49) - age * 23;
        const color = mix("#d5c4b1", "#8290a1", night);
        rect(x, y, age > .65 ? 3 : 2, age > .65 ? 2 : 1,
          rgba(color, (1 - age) * .62));
      }
    }
  }

  function drawFountain(seconds, night) {
    const stone = tone("#827c75", night);
    const stoneLight = tone("#c0ad8e", night);
    const water = tone("#68b8c1", night);
    // Central post and animated little jets.
    rect(157, 100, 6, 18, stone);
    rect(155, 99, 10, 3, stoneLight);
    rect(158, 95, 4, 6, water);
    for (let i = 0; i < 5; i++) {
      const offset = (seconds * 9 + i * 5) % 14;
      const x = 152 + i * 4;
      const y = 105 - Math.abs(2 - i) * 2 - offset * .32;
      rect(x, y, 1, 2, rgba("#a2e8df", .8));
    }
    // Basin, ripples, and a tiny alternating splash.
    rect(146, 116, 28, 3, stone);
    rect(142, 119, 36, 5, stoneLight);
    rect(145, 120, 30, 3, water);
    rect(139, 124, 42, 3, stone);
    rect(144, 127, 32, 2, stone);
    const ripple = Math.floor(seconds * 5) % 2;
    rect(148 + ripple * 3, 121, 5, 1, "#c0eee0");
    rect(160 - ripple * 3, 122, 4, 1, "#a1ddd5");
    rect(143, 124, 3, 1, tone("#e0c99f", night));
  }

  function drawStreet(night, rain, seconds) {
    rect(0, 132, W, 48, tone("#827469", night));
    rect(0, 132, W, 3, tone("#c2a17d", night));
    // Staggered cobbles.
    for (let row = 0; row < 6; row++) {
      const y = 138 + row * 8;
      const offset = row % 2 ? -7 : 0;
      for (let x = offset; x < W; x += 18) {
        const shade = ((row * 7 + Math.floor((x + 7) / 18) * 3) % 4);
        const colors = ["#aa927a", "#927e70", "#b49b7d", "#88766c"];
        rect(x + 1, y, 15, 5, tone(colors[shade], night));
        rect(x + 3, y + 1, 4, 1, rgba("#e0c29a", .22));
      }
    }
    // Puddles appear as the shower passes, then gradually dry.
    if (rain > 0) {
      const a = rain * .66;
      for (const p of [[34, 157, 24], [83, 169, 29], [208, 151, 31], [270, 166, 27], [118, 145, 14]]) {
        rect(p[0], p[1], p[2], 3, rgba("#425e72", a));
        rect(p[0] + 4, p[1], Math.floor(p[2] * .55), 1, rgba("#b6d5cf", a * .75));
      }
    }
  }

  function drawBirds(seconds) {
    const birds = [
      { offset: 0, y: 47 }, { offset: 5.3, y: 35 }, { offset: 9.1, y: 61 }
    ];
    birds.forEach((bird, i) => {
      const p = ((seconds + bird.offset) % 13) / 13;
      const x = -12 + p * 344;
      const y = bird.y + Math.sin(p * Math.PI * 7 + i) * 4;
      const c = "#354456";
      line(x - 4, y, x, y + 2, c, 1);
      line(x, y + 2, x + 4, y, c, 1);
      line(x + 5, y + 1, x + 8, y + 3, c, 1);
      line(x + 8, y + 3, x + 11, y + 1, c, 1);
    });
  }

  function drawRain(seconds, amount) {
    if (amount <= 0) return;
    ctx.save();
    ctx.strokeStyle = rgba("#b8d9e5", amount * .68);
    ctx.lineWidth = 1;
    for (let i = 0; i < 72; i++) {
      const x = (i * 47 + 13) % W;
      const y = (i * 31 + seconds * 112) % 190 - 5;
      ctx.beginPath();
      ctx.moveTo(Math.round(x) + .5, Math.round(y) + .5);
      ctx.lineTo(Math.round(x - 2) + .5, Math.round(y + 5) + .5);
      ctx.stroke();
    }
    ctx.restore();
  }

  function drawScene(seconds) {
    const t = (seconds % 20) / 20;
    const night = nightAmount(t);
    const rain = rainAmount(t);
    const sunset = t > .48 && t < .75 ? Math.sin(((t - .48) / .27) * Math.PI) : 0;

    drawSky(t, night, seconds);
    drawBirds(seconds);

    // Chimneys sit behind the roofs.
    rect(29, 50, 8, 17, tone("#86534b", night));
    rect(27, 49, 12, 3, tone("#69464a", night));
    rect(126, 59, 7, 18, tone("#86534b", night));
    rect(124, 58, 11, 3, tone("#69464a", night));

    // Three little homes, with a taller windmill house on the right.
    drawHouse(19, 70, 72, 64, 45, night, sunset, [
      [10, 20, night > .20], [53, 20, night > .43]
    ]);
    drawHouse(108, 81, 76, 53, 59, night, sunset, [
      [9, 16, night > .31], [56, 16, night > .55]
    ]);
    drawHouse(222, 75, 80, 59, 49, night, sunset, [
      [10, 17, night > .23], [59, 17, night > .67]
    ]);

    // Mill's upper gable and turning sails.
    poly([[240, 76], [267, 51], [294, 76]], tone("#9e4d49", night, sunset));
    poly([[246, 75], [267, 56], [288, 75]], tone("#ce6952", night, sunset));
    drawMillBlades(seconds, night);
    rect(263, 77, 8, 12, tone("#74494a", night));
    rect(265, 79, 4, 7, tone("#d39a68", night));

    drawSmoke(seconds, night);

    // Trees, lamps, and fountain sit in front of the houses.
    drawTree(12, 134, night);
    drawTree(98, 134, night);
    drawTree(308, 134, night);
    drawLamp(104, night, .30, seconds);
    drawLamp(207, night, .57, seconds);
    drawStreet(night, rain, seconds);
    drawFountain(seconds, night);

    // A few doorstep flowers.
    for (const [x, y, c] of [[29, 132, "#e27671"], [38, 133, "#f0c76e"],
      [282, 132, "#e79a69"], [294, 133, "#dd7180"]]) {
      rect(x, y, 2, 2, c);
      rect(x, y + 2, 1, 2, tone("#547b55", night));
    }

    // Rain is drawn over the town, so the shower feels like it occupies the scene.
    drawRain(seconds, rain);

    // Tiny warm light reflected on the wet cobbles.
    if (night > .2 && rain > .05) {
      rect(99, 143, 11, 1, rgba("#f7cf83", night * rain * .48));
      rect(202, 149, 13, 1, rgba("#f7cf83", night * rain * .45));
    }
  }

  const start = performance.now();
  function frame(now) {
    const seconds = (now - start) / 1000;
    ctx.clearRect(0, 0, W, H);
    drawScene(seconds);
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();
</script>
</body>
</html>
```