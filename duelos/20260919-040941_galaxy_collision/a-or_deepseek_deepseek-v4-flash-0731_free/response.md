 :Here is a complete, self-contained HTML document that creates an interactive 3D scientific visualization of two colliding galaxies. You can run it directly in your browser.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Galaxy Collision Simulation</title>
    <style>
        body {
            margin: 0;
            overflow: hidden;
            background-color: black;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        #info {
            position: absolute;
            top: 20px;
            left: 20px;
            color: white;
            z-index: 100;
            background: rgba(0, 0, 0, 0.6);
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 16px;
            letter-spacing: 1px;
            pointer-events: none;
        }
        #instructions {
            position: absolute;
            bottom: 20px;
            left: 20px;
            color: rgba(255,255,255,0.5);
            font-size: 12px;
            z-index: 100;
        }
    </style>
</head>
<body>
    <div id="info">Time: 0 Myr</div>
    <div id="instructions">Orbit camera • Auto‑rotating</div>

    <script type="importmap">
        {
            "imports": {
                "three": "https://unpkg.com/three@0.124.0/build/three.module.js"
            }
        }
    </script>

    <script type="module">
        import * as THREE from 'three';

        // ---------- Constants ----------
        const SIM_SPEED = 5.0;
        const SUBSTEPS = 3;
        const NUM_SUBSTEPS = 3;          // for physics substeps
        const TOTAL_GALAXIES = 2;
        const PARTICLES_PER_GALAXY = 20000;
        const STAR_COUNT = 5000;

        const V0 = 18;        // rotation curve amplitude (code units)
        const SOFTENING = 6;  // softening length
        const SCALE_LENGTH = 25;
        const MAX_RADIUS = 100;
        const THICKNESS = 0.4;
        const ARMS_FRACTION = 0.85;
        const PITCH_TAN = 0.3;      // tan(pitch)
        const INNER_R = 5;
        const ARM_SCATTER = 0.35;   // radians

        // ---------- Renderer / Scene ----------
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(
            60,
            window.innerWidth / window.innerHeight,
            0.1,
            5000
        );

        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        document.body.appendChild(renderer.domElement);

        // ---------- Helpers ----------
        function createSpriteTexture() {
            const size = 64;
            const canvas = document.createElement('canvas');
            canvas.width = size;
            canvas.height = size;
            const ctx = canvas.getContext('2d');
            const gradient = ctx.createRadialGradient(
                size / 2, size / 2, 0,
                size / 2, size / 2, size / 2
            );
            gradient.addColorStop(0, 'rgba(255,255,255,1)');
            gradient.addColorStop(0.4, 'rgba(255,255,255,0.8)');
            gradient.addColorStop(1, 'rgba(255,255,255,0)');
            ctx.fillStyle = gradient;
            ctx.fillRect(0, 0, size, size);
            return new THREE.CanvasTexture(canvas);
        }

        const spriteTexture = createSpriteTexture();

        // ---------- Global Arrays for Particles ----------
        const totalParticles = PARTICLES_PER_GALAXY * 2;
        const positions = new Float32Array(totalParticles * 3);
        const velocities = new Float32Array(totalParticles * 3);
        const colors = new Float32Array(totalParticles * 3);

        // ---------- Galaxy Structure ----------
        const galaxies = [
            {
                pos: new THREE.Vector3(120, 0, 0),
                vel: new THREE.Vector3(0, 0, -12),
                start: 0,
                count: PARTICLES_PER_GALAXY,
            },
            {
                pos: new THREE.Vector3(-120, 0, 0),
                vel: new THREE.Vector3(0, 0, 12),
                start: PARTICLES_PER_GALAXY,
                count: PARTICLES_PER_GALAXY,
            }
        ];

        // ---------- Utility ----------
        function gaussian() {
            let u = 0, v = 0;
            while (u === 0) u = Math.random();
            while (v === 0) v = Math.random();
            return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
        }

        // ---------- Generate one galaxy ----------
        function generateGalaxy(gal) {
            const startIdx = gal.start * 3;

            for (let i = 0; i < gal.count; i++) {
                const idx3 = (gal.start + i) * 3;

                // --- Sample radius & theta ---
                let r, theta;

                if (Math.random() < ARMS_FRACTION) {
                    // Arm particle: sample from exponential to get a disk
                    r = -SCALE_LENGTH * Math.log(1 - Math.random());
                    r = Math.max(r, INNER_R);
                    const thetaArm = Math.log(r / INNER_R) / PITCH_TAN;
                    const armIdx = Math.floor(Math.random() * 2); // 2 arms
                    theta = thetaArm + armIdx * Math.PI + gaussian() * ARM_SCATTER;
                    // Add some radial scatter
                    r *= Math.max(0.3, 1 + gaussian() * 0.15);
                } else {
                    r = -SCALE_LENGTH * Math.log(1 - Math.random());
                    theta = Math.random() * Math.PI * 2;
                }

                // Limit radius
                r = Math.min(r, MAX_RADIUS);

                // position in disk (XZ plane)
                const x = r * Math.cos(theta);
                const z = r * Math.sin(theta);
                const y = gaussian() * THICKNESS * (1 + 0.1 * r / MAX_RADIUS);

                // circular velocity at this radius
                const vCirc = V0 * r / Math.sqrt(r * r + SOFTENING * SOFTENING);
                let vx = -vCirc * Math.sin(theta);
                let vz = vCirc * Math.cos(theta);
                let vy = 0;

                // add small random velocity (velocity dispersion)
                const sig = vCirc * 0.04;
                vx += gaussian() * sig;
                vy += gaussian() * sig * 0.3;
                vz += gaussian() * sig;

                // apply centre velocity
                vx += gal.vel.x;
                vy += gal.vel.y;
                vz += gal.vel.z;

                // add centre position
                const px = x + gal.pos.x;
                const py = y + gal.pos.y;
                const pz = z + gal.pos.z;

                // write to arrays
                positions[idx3] = px;
                positions[idx3 + 1] = py;
                positions[idx3 + 2] = pz;

                velocities[idx3] = vx;
                velocities[idx3 + 1] = vy;
                velocities[idx3 + 2] = vz;

                // --- Assign colour (blue core → warm arms) ---
                const t = Math.min(1, r / MAX_RADIUS);
                const color = new THREE.Color();
                if (t < 0.15) {
                    // hot core / yellow
                    color.setRGB(1.0, 0.65, 0.2);
                } else if (t < 0.35) {
                    // transition to white-yellow
                    const s = (t - 0.15) / 0.2;
                    color.lerpColors(
                        new THREE.Color(1.0, 0.65, 0.2),
                        new THREE.Color(1.0, 0.9, 0.8),
                        s
                    );
                } else {
                    // arms blue-white
                    const s = Math.min(1, (t - 0.35) / 0.65);
                    color.lerpColors(
                        new THREE.Color(1.0, 0.9, 0.8),
                        new THREE.Color(0.35, 0.5, 1.0),
                        s
                    );
                }

                colors[idx3] = color.r;
                colors[idx3 + 1] = color.g;
                colors[idx3 + 2] = color.b;
            }
        }

        // ---------- Generate galaxies ----------
        galaxies.forEach(g => generateGalaxy(g));

        // ---------- Create Particle Geometry ----------
        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

        const pointsMaterial = new THREE.PointsMaterial({
            color: 0xffffff,
            size: 2.0,
            map: spriteTexture,
            vertexColors: true,
            blending: THREE.AdditiveBlending,
            transparent: true,
            depthWrite: false,
            sizeAttenuation: true,
        });

        const points = new THREE.Points(geometry, pointsMaterial);
        scene.add(points);

        // ---------- Background Stars ----------
        function createBackground() {
            const bgGeo = new THREE.BufferGeometry();
            const pos = new Float32Array(STAR_COUNT * 3);
            for (let i = 0; i < STAR_COUNT; i++) {
                const theta = Math.random() * Math.PI * 2;
                const phi = Math.acos(2 * Math.random() - 1);
                const r = 800 + Math.random() * 1200;
                pos[i * 3] = r * Math.sin(phi) * Math.cos(theta);
                pos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
                pos[i * 3 + 2] = r * Math.cos(phi);
            }
            bgGeo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
            const bgMat = new THREE.PointsMaterial({
                color: 0xffffff,
                size: 1.0,
                sizeAttenuation: false,
                map: spriteTexture,
                blending: THREE.AdditiveBlending,
                transparent: true,
                depthWrite: false,
            });
            const bg = new THREE.Points(bgGeo, bgMat);
            scene.add(bg);
        }
        createBackground();

        // ---------- Camera Path ----------
        const clock = new THREE.Clock();
        let cameraAngle = 0;
        const cameraRadius = 280;
        const cameraHeight = 120;

        // ---------- Label ----------
        const infoLabel = document.getElementById('info');
        let simTimeMyr = 0;

        // ---------- Physics Update ----------
        function integrate(dt) {
            const step = dt * SIM_SPEED / NUM_SUBSTEPS;

            for (let s = 0; s < NUM_SUBSTEPS; s++) {
                // -- Update centre velocities from mutual gravity --
                const dx = galaxies[0].pos.x - galaxies[1].pos.x;
                const dy = galaxies[0].pos.y - galaxies[1].pos.y;
                const dz = galaxies[0].pos.z - galaxies[1].pos.z;
                const d2 = dx * dx + dy * dy + dz * dz + SOFTENING * SOFTENING;
                const accelMag = (V0 * V0) / d2;

                // velocities
                const ax0 = -accelMag * dx;
                const ay0 = -accelMag * dy;
                const az0 = -accelMag * dz;
                galaxies[0].vel.x += ax0 * step;
                galaxies[0].vel.y += ay0 * step;
                galaxies[0].vel.z += az0 * step;
                galaxies[1].vel.x -= ax0 * step;
                galaxies[1].vel.y -= ay0 * step;
                galaxies[1].vel.z -= az0 * step;

                // positions
                galaxies.forEach(g => {
                    g.pos.x += g.vel.x * step;
                    g.pos.y += g.vel.y * step;
                    g.pos.z += g.vel.z * step;
                });

                // -- Update particle velocities & positions --
                const g1 = galaxies[0];
                const g2 = galaxies[1];

                for (let i = 0; i < totalParticles; i++) {
                    const idx3 = i * 3;
                    const px = positions[idx3];
                    const py = positions[idx3 + 1];
                    const pz = positions[idx3 + 2];
                    const vx = velocities[idx3];
                    const vy = velocities[idx3 + 1];
                    const vz = velocities[idx3 + 2];

                    let axN = 0, ayN = 0, azN = 0;

                    // galaxy 1
                    {
                        const dxN = px - g1.pos.x;
                        const dyN = py - g1.pos.y;
                        const dzN = pz - g1.pos.z;
                        const d2N = dxN * dxN + dyN * dyN + dzN * dzN + SOFTENING * SOFTENING;
                        const f = V0 * V0 / d2N;
                        axN -= f * dxN;
                        ayN -= f * dyN;
                        azN -= f * dzN;
                    }
                    // galaxy 2
                    {
                        const dxN = px - g2.pos.x;
                        const dyN = py - g2.pos.y;
                        const dzN = pz - g2.pos.z;
                        const d2N = dxN * dxN + dyN * dyN + dzN * dzN + SOFTENING * SOFTENING;
                        const f = V0 * V0 / d2N;
                        axN -= f * dxN;
                        ayN -= f * dyN;
                        azN -= f * dzN;
                    }

                    velocities[idx3] += axN * step;
                    velocities[idx3 + 1] += ayN * step;
                    velocities[idx3 + 2] += azN * step;

                    positions[idx3] += velocities[idx3] * step;
                    positions[idx3 + 1] += velocities[idx3 + 1] * step;
                    positions[idx3 + 2] += velocities[idx3 + 2] * step;
                }
            }
        }

        // ---------- Animation Loop ----------
        function animate() {
            requestAnimationFrame(animate);

            const dt = Math.min(clock.getDelta(), 0.1); // cap to 100ms

            // update label time (illustrative)
            simTimeMyr += dt * 10 * (SIM_SPEED / 5);
            infoLabel.textContent = `Time: ${simTimeMyr.toFixed(0)} Myr`;

            // physics
            integrate(dt);

            // mark position attribute for update
            geometry.attributes.position.needsUpdate = true;

            // update camera orbit
            cameraAngle += dt * 0.08;
            camera.position.x = cameraRadius * Math.cos(cameraAngle);
            camera.position.z = cameraRadius * Math.sin(cameraAngle);
            camera.position.y = cameraHeight + 20 * Math.sin(cameraAngle * 0.5);
            camera.lookAt(0, 0, 0);

            // render
            renderer.render(scene, camera);
        }

        // ---------- Resize ----------
        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });

        // ---------- Start ----------
        renderer.render(scene, camera);
        animate();
    </script>
</body>
</html>
```

### Simulation Details

1. **Physics Engine**: The code uses a custom `integrate` function that updates the positions and velocities of all particles and galaxy centres each frame. It implements Newtonian gravitational interaction between all particles and the two galaxy centres, with a softening parameter to avoid numerical instabilities.

2. **Visualisation**: Particles are rendered as additive-blended points using a custom sprite texture, giving the galaxies a glowing, stellar appearance. A background field of stars is also generated for context.

3. **Camera**: The camera automatically orbits around the simulation, providing a dynamic view of the collision from all angles. No interaction is required, but you can zoom in/out manually if you add OrbitControls.

4. **Time display**: The top-left corner continuously shows the simulated time in millions of years, helping you track the progress of the collision.

Simply run this HTML file in a modern browser (with ES module support), and the simulation will start automatically. Enjoy!