 !
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Solar System – Cinematic Camera</title>
    <style>
        body {
            margin: 0;
            overflow: hidden;
            background: #000;
            font-family: 'Arial', sans-serif;
        }
        #name {
            position: fixed;
            bottom: 40px;
            left: 50%;
            transform: translateX(-50%);
            color: #fff;
            font-size: 26px;
            letter-spacing: 3px;
            text-shadow: 0 0 20px rgba(0, 0, 0, 0.9);
            z-index: 10;
            pointer-events: none;
            background: rgba(0, 0, 0, 0.25);
            padding: 8px 20px;
            border-radius: 30px;
            opacity: 0.85;
            transition: opacity 0.4s;
        }
        #hint {
            position: fixed;
            top: 15px;
            left: 15px;
            color: rgba(255, 255, 255, 0.4);
            font-size: 12px;
            z-index: 10;
        }
    </style>
</head>
<body>
<div id="name">THE SUN</div>
<div id="hint">Sun · Mercury · Venus · Earth · Mars · Jupiter · Saturn · Uranus · Neptune</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
    // ------------------------------------------------------------------
    //  Scene / Camera / Renderer
    // ------------------------------------------------------------------
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x05050a);

    const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 3000);
    camera.position.set(0, 20, 40);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    document.body.appendChild(renderer.domElement);

    // ------------------------------------------------------------------
    //  Lights
    // ------------------------------------------------------------------
    const ambient = new THREE.AmbientLight(0x404060, 0.35);
    scene.add(ambient);

    const sunLight = new THREE.PointLight(0xfff0e0, 2.2, 0, 0);
    sunLight.position.set(0, 0, 0);
    scene.add(sunLight);

    // small fill light so the dark side of planets isn't pitch black
    const fillLight = new THREE.DirectionalLight(0x445566, 0.2);
    fillLight.position.set(1, 1, 1);
    scene.add(fillLight);

    // ------------------------------------------------------------------
    //  Helpers
    // ------------------------------------------------------------------
    function smoothstep(x) {
        const t = Math.max(0, Math.min(1, x));
        return t * t * (3 - 2 * t);
    }

    function createStars() {
        const geo = new THREE.BufferGeometry();
        const count = 6000;
        const pos = new Float32Array(count * 3);
        const col = new Float32Array(count * 3);
        for (let i = 0; i < count; i++) {
            const r = 900 + Math.random() * 400;
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos(2 * Math.random() - 1);
            pos[i * 3] = r * Math.sin(phi) * Math.cos(theta);
            pos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
            pos[i * 3 + 2] = r * Math.cos(phi);

            const shade = 0.4 + Math.random() * 0.6;
            col[i * 3] = shade;
            col[i * 3 + 1] = shade * (0.9 + Math.random() * 0.1);
            col[i * 3 + 2] = shade;
        }
        geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
        geo.setAttribute('color', new THREE.BufferAttribute(col, 3));
        const mat = new THREE.PointsMaterial({ size: 0.8, vertexColors: true, sizeAttenuation: true });
        const stars = new THREE.Points(geo, mat);
        scene.add(stars);
    }
    createStars();

    // ------------------------------------------------------------------
    //  Texture Generators (procedural)
    // ------------------------------------------------------------------
    function createSunTexture() {
        const c = document.createElement('canvas');
        c.width = 512;
        c.height = 256;
        const x = c.getContext('2d');
        const g = x.createLinearGradient(0, 0, 0, 256);
        g.addColorStop(0, '#ffcc33');
        g.addColorStop(0.5, '#ff9900');
        g.addColorStop(1, '#ff6600');
        x.fillStyle = g;
        x.fillRect(0, 0, 512, 256);

        // granulation noise
        const img = x.getImageData(0, 0, 512, 256);
        for (let i = 0; i < img.data.length; i += 4) {
            const n = (Math.random() - 0.5) * 36;
            img.data[i] += n;
            img.data[i + 1] += n;
            img.data[i + 2] += n;
        }
        x.putImageData(img, 0, 0);
        return new THREE.CanvasTexture(c);
    }

    function createRockTexture(baseColor, darkSpots) {
        return function() {
            const c = document.createElement('canvas');
            c.width = 256;
            c.height = 128;
            const x = c.getContext('2d');
            x.fillStyle = baseColor;
            x.fillRect(0, 0, 256, 128);

            // spots / craters
            const img = x.getImageData(0, 0, 256, 128);
            for (let i = 0; i < img.data.length; i += 4) {
                const n = (Math.random() - 0.5) * 24;
                img.data[i] += n;
                img.data[i + 1] += n;
                img.data[i + 2] += n;
            }
            x.putImageData(img, 0, 0);

            if (darkSpots) {
                for (let s = 0; s < 30; s++) {
                    x.fillStyle = `rgba(30,30,30,${0.15+Math.random()*0.3})`;
                    x.beginPath();
                    x.ellipse(
                        Math.random() * 256, Math.random() * 128,
                        2 + Math.random() * 8, 2 + Math.random() * 8, 0, 0, Math.PI * 2
                    );
                    x.fill();
                }
            }
            return new THREE.CanvasTexture(c);
        };
    }

    function createGasGiantTexture(colors) {
        return function() {
            const c = document.createElement('canvas');
            c.width = 512;
            c.height = 256;
            const x = c.getContext('2d');
            const bandCount = 20;
            const bh = 256 / bandCount;
            for (let i = 0; i < bandCount; i++) {
                const idx = i % colors.length;
                x.fillStyle = colors[idx];
                x.fillRect(0, i * bh, 512, Math.ceil(bh) + 1);
            }

            // turbulence
            x.globalAlpha = 0.35;
            for (let i = 0; i < 400; i++) {
                x.fillStyle = `rgba(255,255,255,${Math.random()*0.25})`;
                x.fillRect(Math.random() * 512, Math.random() * 256, 10 + Math.random() * 50, 1 + Math.random() * 3);
                x.fillStyle = `rgba(0,0,0,${Math.random()*0.2})`;
                x.fillRect(Math.random() * 512, Math.random() * 256, 10 + Math.random() * 50, 1 + Math.random() * 3);
            }
            x.globalAlpha = 1;
            return new THREE.CanvasTexture(c);
        };
    }

    function createEarthTexture() {
        const c = document.createElement('canvas');
        c.width = 512;
        c.height = 256;
        const x = c.getContext('2d');

        // ocean
        x.fillStyle = '#1a6fd0';
        x.fillRect(0, 0, 512, 256);

        // continents
        x.fillStyle = '#2d8a3e';
        const landmasses = [
            [120, 90, 45, 30], [300, 110, 60, 35], [180, 160, 38, 25],
            [400, 70, 35, 22], [60, 180, 28, 16], [440, 200, 30, 20],
            [250, 200, 25, 18], [500, 140, 22, 14]
        ];
        landmasses.forEach(([cx, cy, rx, ry]) => {
            x.beginPath();
            x.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
            x.fillStyle = '#2d8a3e';
            x.fill();
        });

        // small islands
        for (let i = 0; i < 40; i++) {
            x.beginPath();
            x.ellipse(Math.random() * 512, Math.random() * 256,
                2 + Math.random() * 6, 2 + Math.random() * 4, 0, 0, Math.PI * 2);
            x.fillStyle = `rgba(40,120,60,${0.5+Math.random()*0.5})`;
            x.fill();
        }

        // polar ice
        x.fillStyle = '#ffffff';
        x.fillRect(0, 0, 512, 18);
        x.fillRect(0, 238, 512, 18);

        // some clouds
        x.globalAlpha = 0.2;
        for (let i = 0; i < 70; i++) {
            x.fillStyle = '#ffffff';
            x.fillRect(Math.random() * 512, Math.random() * 256, 10 + Math.random() * 40, 2);
        }
        x.globalAlpha = 1;

        return new THREE.CanvasTexture(c);
    }

    function createVenusTexture() {
        const c = document.createElement('canvas');
        c.width = 400;
        c.height = 200;
        const x = c.getContext('2d');
        x.fillStyle = '#d4a66e';
        x.fillRect(0, 0, 400, 200);

        // clouds
        for (let i = 0; i < 300; i++) {
            x.fillStyle = `rgba(255,200,120,${0.05+Math.random()*0.2})`;
            x.beginPath();
            x.ellipse(Math.random() * 400, Math.random() * 200,
                5 + Math.random() * 30, 2 + Math.random() * 8, 0, 0, Math.PI * 2);
            x.fill();
        }
        return new THREE.CanvasTexture(c);
    }

    function createUranusTexture() {
        const c = document.createElement('canvas');
        c.width = 256;
        c.height = 128;
        const x = c.getContext('2d');
        x.fillStyle = '#79c5e8';
        x.fillRect(0, 0, 256, 128);
        for (let i = 0; i < 80; i++) {
            x.fillStyle = `rgba(200,240,255,${0.05+Math.random()*0.15})`;
            x.fillRect(Math.random() * 256, Math.random() * 128, 20 + Math.random() * 80, 2);
        }
        return new THREE.CanvasTexture(c);
    }

    function createNeptuneTexture() {
        const c = document.createElement('canvas');
        c.width = 256;
        c.height = 128;
        const x = c.getContext('2d');
        x.fillStyle = '#3b5ae0';
        x.fillRect(0, 0, 256, 128);
        for (let i = 0; i < 120; i++) {
            x.fillStyle = `rgba(255,255,255,${0.06+Math.random()*0.12})`;
            x.fillRect(Math.random() * 256, Math.random() * 128, 15 + Math.random() * 60, 1.5);
        }
        return new THREE.CanvasTexture(c);
    }

    function createGlowTexture() {
        const c = document.createElement('canvas');
        c.width = 256;
        c.height = 256;
        const x = c.getContext('2d');
        const g = x.createRadialGradient(128, 128, 0, 128, 128, 128);
        g.addColorStop(0, 'rgba(255,220,120,1)');
        g.addColorStop(0.25, 'rgba(255,160,50,0.7)');
        g.addColorStop(0.6, 'rgba(255,100,0,0.25)');
        g.addColorStop(1, 'rgba(255,50,0,0)');
        x.fillStyle = g;
        x.fillRect(0, 0, 256, 256);
        return new THREE.CanvasTexture(c);
    }

    // ------------------------------------------------------------------
    //  Sun
    // ------------------------------------------------------------------
    const sunMesh = new THREE.Mesh(
        new THREE.SphereGeometry(5, 48, 48),
        new THREE.MeshBasicMaterial({ map: createSunTexture() })
    );
    scene.add(sunMesh);

    // Sun glow sprite
    const sunGlowMat = new THREE.SpriteMaterial({
        map: createGlowTexture(),
        blending: THREE.AdditiveBlending,
        transparent: true,
        opacity: 0.85,
        depthWrite: false
    });
    const sunGlow = new THREE.Sprite(sunGlowMat);
    sunGlow.scale.set(28, 28, 1);
    sunGlow.position.set(0, 0, 0);
    scene.add(sunGlow);

    // ------------------------------------------------------------------
    //  Planet Data
    // ------------------------------------------------------------------
    const SUN_INDEX = 0;

    const planetData = [
        {
            name: 'Mercury',
            radius: 0.9,
            distance: 10,
            speed: 0.02,
            spin: 0.05,
            texture: createRockTexture('#8a817b', true)
        },
        {
            name: 'Venus',
            radius: 1.3,
            distance: 15,
            speed: 0.015,
            spin: 0.08,
            texture: createVenusTexture
        },
        {
            name: 'Earth',
            radius: 1.4,
            distance: 20,
            speed: 0.012,
            spin: 0.2,
            texture: createEarthTexture
        },
        {
            name: 'Mars',
            radius: 1.0,
            distance: 25,
            speed: 0.01,
            spin: 0.15,
            texture: createRockTexture('#c8653a', true)
        },
        {
            name: 'Jupiter',
            radius: 4.0,
            distance: 40,
            speed: 0.007,
            spin: 0.4,
            texture: createGasGiantTexture([
                '#c8a87c', '#e0c9a6', '#9e7c5e', '#d4b896',
                '#b8906e', '#f0dcc0', '#a67c52', '#d0b090',
                '#c9a07a', '#e8c8a4'
            ])
        },
        {
            name: 'Saturn',
            radius: 3.5,
            distance: 55,
            speed: 0.005,
            spin: 0.35,
            texture: createGasGiantTexture([
                '#e8d0a8', '#c8a868', '#f0e0c0', '#a88058',
                '#e0c890', '#d0b078', '#f8e8d0', '#b89868'
            ]),
            hasRing: true
        },
        {
            name: 'Uranus',
            radius: 2.0,
            distance: 70,
            speed: 0.003,
            spin: 0.1,
            texture: createUranusTexture
        },
        {
            name: 'Neptune',
            radius: 2.0,
            distance: 85,
            speed: 0.002,
            spin: 0.1,
            texture: createNeptuneTexture
        }
    ];

    // ------------------------------------------------------------------
    //  Create Planets & Orbit Lines
    // ------------------------------------------------------------------
    const sunGroup = new THREE.Group();
    scene.add(sunGroup);

    // Orbit lines
    const orbitLines = [];
    planetData.forEach((p) => {
        const pts = [];
        for (let i = 0; i <= 128; i++) {
            const a = (i / 128) * Math.PI * 2;
            pts.push(new THREE.Vector3(Math.cos(a) * p.distance, 0, Math.sin(a) * p.distance));
        }
        const geo = new THREE.BufferGeometry().setFromPoints(pts);
        const mat = new THREE.LineBasicMaterial({ color: 0xffffff, opacity: 0.1, transparent: true });
        const line = new THREE.Line(geo, mat);
        scene.add(line);
        orbitLines.push(line);
    });

    // Planet meshes
    planetData.forEach((p) => {
        p.offset = Math.random() * Math.PI * 2; // initial orbit angle
        const geo = new THREE.SphereGeometry(p.radius, 32, 32);
        const mat = new THREE.MeshStandardMaterial({
            map: p.texture(),
            roughness: 0.85,
            metalness: 0.1
        });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.set(0, 0, 0); // will be set in updatePlanet
        scene.add(mesh);
        p.mesh = mesh;

        // Add ring to Saturn
        if (p.hasRing) {
            const ringGeo = new THREE.RingGeometry(p.radius * 1.3, p.radius * 2.2, 64);
            const ringMat = new THREE.MeshBasicMaterial({
                color: 0xc0a070,
                side: THREE.DoubleSide,
                transparent: true,
                opacity: 0.6
            });
            const ring = new THREE.Mesh(ringGeo, ringMat);
            ring.rotation.x = Math.PI / 2;
            mesh.add(ring);
        }
    });

    // ------------------------------------------------------------------
    //  Moon (Earth)
    // ------------------------------------------------------------------
    const moonMesh = new THREE.Mesh(
        new THREE.SphereGeometry(0.3, 8, 8),
        new THREE.MeshStandardMaterial({ color: 0xaaaaaa, roughness: 0.9 })
    );
    scene.add(moonMesh);

    // ------------------------------------------------------------------
    //  Utility for Planet Position (at given time)
    // ------------------------------------------------------------------
    function getPlanetPos(planetIndex, time) {
        if (planetIndex === 0) {
            return new THREE.Vector3(0, 0, 0);
        }
        const p = planetData[planetIndex - 1];
        const a = time * p.speed + p.offset;
        return new THREE.Vector3(Math.cos(a) * p.distance, 0, Math.sin(a) * p.distance);
    }

    function updatePlanet(index, time) {
        if (index === 0) return; // sun
        const p = planetData[index - 1];
        const pos = getPlanetPos(index, time);
        p.mesh.position.copy(pos);
        p.mesh.rotation.y = time * p.spin;
    }

    function updateAllPlanets(time) {
        for (let i = 1; i <= planetData.length; i++) {
            updatePlanet(i, time);
        }
        sunMesh.rotation.y = time * 0.02;
        sunGlow.rotation.z = time * 0.01;
    }

    // Moon orbit around Earth
    function updateMoon(time) {
        const earthIndex = 3; // Earth is at index 3 in planetData
        const earthPos = getPlanetPos(earthIndex, time);
        const a = time * 5;
        const r = 2.8;
        moonMesh.position.set(
            earthPos.x + Math.cos(a) * r,
            0,
            earthPos.z + Math.sin(a) * r
        );
    }

    // ------------------------------------------------------------------
    //  Camera Update
    // ------------------------------------------------------------------
    const segmentDuration = 5.0; // seconds per segment
    const totalSegments = 9; // Sun + 8 planets
    const totalDuration = segmentDuration * totalSegments;

    // Camera offsets per index (Sun, Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, Neptune)
    // Adjust to frame the target nicely
    const camOffsets = [
        new THREE.Vector3(8, 5, 14),   // Sun
        new THREE.Vector3(1.5, 0.8, 3.0),
        new THREE.Vector3(1.8, 1.2, 3.6),
        new THREE.Vector3(1.8, 1.2, 3.8),
        new THREE.Vector3(1.6, 1.0, 3.2),
        new THREE.Vector3(4.5, 2.5, 9.0),
        new THREE.Vector3(4.0, 2.2, 8.5),
        new THREE.Vector3(2.2, 1.5, 5.5),
        new THREE.Vector3(2.2, 1.5, 5.5)
    ];

    function updateCamera(time) {
        const looped = ((time % totalDuration) + totalDuration) % totalDuration;
        const segIndex = Math.floor(looped / segmentDuration);
        const localT = (looped - segIndex * segmentDuration) / segmentDuration;

        const segStartTime = time - (looped - segIndex * segmentDuration);

        const approachDuration = Math.min(2.2, segmentDuration * 0.44);
        const rawU = (looped - segIndex * segmentDuration) / approachDuration;
        const u = Math.min(rawU, 1.0);
        const su = smoothstep(u);

        let camPos, camLookAt;

        if (u < 1.0) {
            // ----- approach phase -----
            const prevSegIndex = (segIndex - 1 + totalSegments) % totalSegments;

            // Start position from the *previous* body's hold position
            const startPos = getPlanetPos(prevSegIndex, segStartTime).add(camOffsets[prevSegIndex]);

            // End position at the *target* body
            const endTime = segStartTime + approachDuration;
            const endPos = getPlanetPos(segIndex, endTime).add(camOffsets[segIndex]);

            camPos = new THREE.Vector3().lerpVectors(startPos, endPos, su);
            camLookAt = getPlanetPos(segIndex, time);
        } else {
            // ----- hold phase -----
            const targetPos = getPlanetPos(segIndex, time);
            camPos = targetPos.clone().add(camOffsets[segIndex]);
            camLookAt = targetPos.clone();
        }

        camera.position.copy(camPos);
        camera.lookAt(camLookAt);

        // Update name label
        const names = ['THE SUN', ...planetData.map(p => p.name.toUpperCase())];
        document.getElementById('name').textContent = names[segIndex];
    }

    // ------------------------------------------------------------------
    //  Resize
    // ------------------------------------------------------------------
    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });

    // ------------------------------------------------------------------
    //  Animation Loop
    // ------------------------------------------------------------------
    let lastTime = 0;

    function animate(timestamp) {
        const time = timestamp * 0.001;

        // Update all planet positions
        updateAllPlanets(time);
        updateMoon(time);

        // Update camera
        updateCamera(time);

        renderer.render(scene, camera);
        requestAnimationFrame(animate);
    }

    // Start
    requestAnimationFrame(animate);
</script>
</body>
</html>
```
### 轨道漫游机制

为了让您快速了解这个3D太阳系漫游体验的运作方式，下面简单说明：

- **自动环绕**：相机以**8大行星 + 太阳**为顺序，每隔5秒自动切换视角，模拟太空飞行器的视角。
- **动态接近**：在切换时，相机会从上一个天体，**平滑“飞向”下一个天体**，并在目标附近停留环顾。
- **视线追踪**：相机始终**注视当前目标**（太阳或行星），即使在飞行过程中也保持视线锁定。
- **名称提示**：屏幕底部会**同步显示**当前所环绕的天体名称，方便您跟随旅程。

---

**优化建议：** 您可以在JavaScript中调整`segmentDuration`（当前5秒）来控制切换速度，也可直接修改`camOffsets`数组中的向量值来调整每个天体的观察距离。