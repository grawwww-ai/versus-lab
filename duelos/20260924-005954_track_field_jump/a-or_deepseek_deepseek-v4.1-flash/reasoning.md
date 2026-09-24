Let me build this carefully. It's a big single-file HTML game. Need:

- Canvas, pixel art, nearest-neighbour scaling.
- Side-scrolling stadium: runway, takeoff board, sand pit with measuring tape, crowd in stands, flags, scoreboard, sky.
- Animated athlete sprite with run cycle, lean, jump arc, tuck, landing with sand puff particles, landing mark in sand.
- Mechanics: speed bar filled by alternating two keys (left/right arrows or Z/X), angle selector swinging while running, foul line invalidation, distance in metres with one decimal, 3 attempts, best mark, world record line.
- Slow-motion replay of the jump.
- Results screen.
- Autoplay demo toggled with P.
- Animated details: crowd waving, flags, clouds.
- HUD readable.

Let me design the architecture.

Canvas internal resolution: let's use 512x288 (16:9) scaled up with image-rendering: pixelated. Actually classic NES is 256x240. But we want widescreen stadium. Let's use 480x270 or 512x288. I'll go with 480x270 which scales nicely to 1920x1080 (4x) and 1280x720 (2.667 — not integer). Let's use 320x180 for integer scaling to 1280x720 (4x). Hmm, 320x180 is quite small for HUD detail but that's NES-ish. Actually the NES is 256x240. For side-scrolling with a stadium, let's use 384x216 (16:9, scales 5x to 1920x1080). That's a decent pixel canvas. I'll go with 384x216... maybe a bit small for text. Let's do 480x270 — text at 8px tall is fine, and CSS scale to fit window with integer scaling when possible.

I'll implement a custom pixel font? No — I'll use canvas fillText with a monospace font and imageSmoothingEnabled=false. But fillText at small sizes gets antialiased. Better: draw a tiny bitmap font procedurally. That's a lot of work but doable... Alternatively, use a large canvas with CSS pixelated scaling and draw text with a bold sans font at small sizes; it'll be antialiased but readable. Requirement says "readable HUD" and "pixel art drawn procedurally in code". Text isn't pixel art per se. But mixing antialiased text with pixelated scaling looks blurry-ish... Actually if I render at 480x270 and scale up with pixelated, the text pixels get scaled as blocks — the antialiasing becomes blocky, which is acceptable and looks retro-ish.

Hmm, but a proper pixel font would be much nicer. Let me write a compact 5x7 bitmap font for A-Z, 0-9, and some punctuation. That's a fair chunk of data but manageable. Let me define font as strings.

Actually, let me do a 3x5 font for tiny labels and 5x7 for main? Just do one 5x7 font. Let me write it.

5x7 font, each char 5 wide 7 tall, encoded as 7 strings of 5 chars using '#' and '.'.

Let me define:

A:
.###.
#...#
#...#
#####
#...#
#...#
#...#

Hmm 5x7 with rows. Let me just do it.

I'll write a compact representation: each glyph as an array of 7 numbers (5 bits each), or as strings. Strings are more readable but long. Let's use a hex-ish encoding: each row is 5 bits, so 7 rows -> 7 values 0-31. I could encode each glyph as a string of 7 chars from a base32 alphabet. That's compact but error-prone to write.

Alternative: write each glyph as 7 strings of 5 chars. 36 glyphs * 7 lines = 252 lines. Too long but fine? It bloats the file. Let me use a compact string form: for each character, a string like "01110 10001 10001 11111 10001 10001 10001" — that's 7 groups. I can write it as one string with rows separated by nothing, using binary digits: "01110100011000111111100011000110001" (35 chars). Hmm.

Simpler: use a compact encoding where each glyph is 5 columns, each column is 7 bits. Encode as 5 chars from a set. Meh.

Let me just use a well-known approach: define font as an object mapping char to array of 7 strings. I'll write it out. It's verbose but clear and I can be accurate. Actually, I can compress by putting rows on one line separated by '/': e.g. 
A: ".###./#...#/#...#/#####/#...#/#...#/#...#"
That's one line per char, 36 lines. That's fine.

Actually to reduce, I'll use 5x7 but write as: `A:"01110,10001,10001,11111,10001,10001,10001"`. Using 1/0. I'll write with 0/1.

Let me be careful and write all needed chars: A-Z, 0-9, space, ., :, -, !, ?, /, %, ', ", (, ), +, <, >, comma.

I need: A-Z (26), 0-9 (10), space, '.', ':', '-', '!', '?', '/', '%', ',', "'". ~44 glyphs.

Let me write them.

I'll use 5 wide, 7 tall.

A:
01110
10001
10001
11111
10001
10001
10001

B:
11110
10001
10001
11110
10001
10001
11110

C:
01110
10001
10000
10000
10000
10001
01110

D:
11110
10001
10001
10001
10001
10001
11110

E:
11111
10000
10000
11110
10000
10000
11111

F:
11111
10000
10000
11110
10000
10000
10000

G:
01110
10001
10000
10111
10001
10001
01111

H:
10001
10001
10001
11111
10001
10001
10001

I:
11111
00100
00100
00100
00100
00100
11111

J:
00111
00010
00010
00010
00010
10010
01100

K:
10001
10010
10100
11000
10100
10010
10001

L:
10000
10000
10000
10000
10000
10000
11111

M:
10001
11011
10101
10101
10001
10001
10001

N:
10001
11001
10101
10011
10001
10001
10001

O:
01110
10001
10001
10001
10001
10001
01110

P:
11110
10001
10001
11110
10000
10000
10000

Q:
01110
10001
10001
10001
10101
10010
01101

R:
11110
10001
10001
11110
10100
10010
10001

S:
01111
10000
10000
01110
00001
00001
11110

T:
11111
00100
00100
00100
00100
00100
00100

U:
10001
10001
10001
10001
10001
10001
01110

V:
10001
10001
10001
10001
10001
01010
00100

W:
10001
10001
10001
10101
10101
11011
10001

X:
10001
10001
01010
00100
01010
10001
10001

Y:
10001
10001
01010
00100
00100
00100
00100

Z:
11111
00001
00010
00100
01000
10000
11111

0:
01110
10001
10011
10101
11001
10001
01110

1:
00100
01100
00100
00100
00100
00100
01110

2:
01110
10001
00001
00010
00100
01000
11111

3:
11111
00010
00100
00010
00001
10001
01110

4:
00010
00110
01010
10010
11111
00010
00010

5:
11111
10000
11110
00001
00001
10001
01110

6:
00110
01000
10000
11110
10001
10001
01110

7:
11111
00001
00010
00100
01000
01000
01000

8:
01110
10001
10001
01110
10001
10001
01110

9:
01110
10001
10001
01111
00001
00010
01100

'.':
00000
00000
00000
00000
00000
01100
01100

',':
00000
00000
00000
00000
01100
01100
00100  -> hmm, comma tail. Let's do:
00000
00000
00000
00000
00110
00100
01000

':':
00000
01100
01100
00000
01100
01100
00000

'-':
00000
00000
00000
11111
00000
00000
00000

'!':
00100
00100
00100
00100
00100
00000
00100

'?':
01110
10001
00001
00110
00100
00000
00100

'/':
00001
00010
00010
00100
01000
01000
10000

'%':
11001
11010
00010
00100
01000
01011
10011

"'":
00100
00100
00000
00000
00000
00000
00000

'(':
00010
00100
01000
01000
01000
00100
00010

')':
01000
00100
00010
00010
00010
00100
01000

'+':
00000
00100
00100
11111
00100
00100
00000

'*':
00000
10101
01110
11111
01110
10101
00000

'=':
00000
00000
11111
00000
11111
00000
00000

'>' : 
01000
00100
00010
00001
00010
00100
01000  -> that's '<'. Let's do '>' as:
00010
00100
01000
10000
01000
00100
00010

'<':
01000
00100
00010
00001
00010
00100
01000

Hmm I wrote '>' first. Fine, swap.

' ' : all zeros.

Also need 'M' for metres — fine.

OK. Text renderer: drawText(ctx, str, x, y, color, scale=1, spacing=1). Each glyph 5px wide + 1 spacing = 6px per char at scale 1.

Now, game design.

### World layout

Side-scrolling camera follows the athlete. World coordinates in metres? Let's use pixels for world with a scale: 1 metre = 24 pixels? The runway is 40m long, pit 9m. In the original Track & Field, the runway is ~ 30-40m and the jump ~ 8-9m.

Let's define: world x in pixels. 1 m = 16 px? Then 40 m runway = 640 px. Screen is 480 wide. Camera follows.

Actually for good visuals, let's have the athlete about 20px tall (in a 270-tall canvas that's small but okay). Hmm. NES Track & Field athlete is about 16-20 px tall. Screen height 216-240. So athlete ~20px. Let's make the canvas 480x270 and athlete ~24px tall. Good.

Scale: 1 metre = 20 px? Then 24px athlete ≈ 1.2 m tall. Reasonable-ish. Runway 40m = 800px. Pit 9m = 180px. Camera scrolls.

Actually let's simplify: 1 m = 18 px. Runway length 35 m from start to takeoff board = 630 px. Pit 10 m = 180 px.

Camera: centered on athlete, but clamped so we see the takeoff board and pit near the end.

Hmm, but for the takeoff, the player needs to see the board. In the original, the camera scrolls and you jump when you cross the line. Let's keep the athlete at a fixed screen position (like x=140) and scroll the world.

Camera x = athlete.x - 140. Clamp to [ -? , maxX ]. Actually let's allow the camera to go up to the end of the pit.

### Physics / mechanics

Speed: player alternates two keys (e.g., Left/Right arrow, or Z/X). Each valid alternating press adds speed. Speed decays slowly. Max speed.

In Track & Field, you mash left-right alternately. Let's do: `speed` in m/s, from 0 to ~11.5 m/s. Each press adds `+0.55` to speed, capped. Friction: speed *= 0.995 per frame or a constant decel.

Angle selector: an oscillating bar from 0° to 90°? Actually in the original, the angle is chosen by pressing the jump button, and the angle oscillates between like 15° and 75°? In the original Track & Field long jump, there's a bar that shows the angle going up and down, and you press the button to set it. Let me recall: In the NES Track & Field long jump, you run, and there's a gauge showing the angle that oscillates; you press A to jump. The angle affects the jump.

Actually in the original, when you press the jump button, the angle is determined by a separate oscillating indicator. Let's implement: an angle indicator that swings 20°..60° at some rate while running. Player presses the jump key to take off at the current angle.

Then the jump: v = speed (m/s), angle θ. vx = v*cos θ, vy = v*sin θ. Gravity g = 9.8 m/s²... but that gives a hang time of 2*v*sinθ/g = 2*11*0.8/9.8 ≈ 1.8 s and distance ≈ v²sin2θ/g = 121*0.9/9.8 ≈ 11m. Realistic long jump is ~8.95m world record. With v=11 m/s at 22° you get ~7.9m. Hmm, real jumpers take off at ~22° and speed 10 m/s.

But this is a game. Let's use a reduced gravity to make arcs look nice and distances land in the 6-9 m range. Let's tune: distance = v²·sin(2θ)/g with g = 12? v=11, θ=25° → 121*0.766/12 = 7.7m. θ=45° → 121/12 = 10m. Hmm, too much at 45.

Real: the athlete's takeoff speed is ~10 m/s and the optimum angle is about 20-25° because of the height of the center of mass. Let's just use g=14, and clamp distances. v=11, θ=25 → 121*0.766/14=6.6m. θ=40 → 121*0.985/14 = 8.5m. Hmm, 40° becomes best. But visually 40° looks fine actually.

Hmm, in the original game the angle gauge mattered a lot. Let's just make it: distance ≈ (v² * sin(2θ)) / g, g=13.5, plus takeoff board offset. And a perfect angle around 40-45° gives max distance. But we want realistic: the world record is 8.95 m. With v_max = 11.5 and θ=45°, d = 132.25/13.5 = 9.8m. Slightly over WR. Let's set g = 15: 132.25/15 = 8.8m. And θ=25°: 132.25*0.766/15 = 6.75. So the angle really matters — good gameplay. Optimum at 45°.

Hmm but real long jumpers jump at 20°. Whatever, it's a game. But maybe more authentic to make the optimum around 30-35°. Let's not overthink. Actually, let's make it so that the optimum is around 42-45° which is the physics-correct answer for projectile motion with the simple model. That's fine and intuitive.

Actually, I'll add a small takeoff height bonus (the athlete leaves the ground from a slightly elevated board? no). Keep it simple.

But also: foul if you take off past the board. In the original, you must jump before/at the board; if you take off past it, it's a foul. Let's implement: the board occupies a range [boardX, boardX+boardW]. If the athlete's takeoff foot is beyond boardX+boardW (i.e., past the board into the runway... wait). Let me set up the direction: athlete runs to the right. The board is at the end of the runway, before the pit. The "foul line" is the front edge of the board (the edge nearest the pit). If the athlete's takeoff point is past the front edge of the board (i.e., in the pit area / beyond the board), it's a foul.

So board from x = boardStart to boardStart + 40px (2m?). Actually the takeoff board is 20cm wide. Let's make it visually ~ 24px. The athlete must take off with their foot on or before the front edge.

Simplify: if takeoffX > boardFrontX → FOUL. Else measure from boardFrontX to landing X.

Distance = landingX - boardFrontX, in metres. Plus, actually in real long jump the measurement is from the takeoff line to the nearest mark. Yes.

So distance = (landingX - boardFrontX) / PPM. If negative (landed before board) → small/zero.

Foul also if... only that. Also if the athlete takes off too early they lose distance naturally.

Let's also add: if the athlete never jumps and runs past the board into the pit, that's a "no jump" → foul / 0.

### Visual: the run

Athlete sprite: I'll draw procedurally with a small function that draws limbs as rectangles based on a phase. Pixel art: use a palette and draw at integer coords.

Athlete: head (skin), hair, torso (tank top), shorts, arms, legs. ~14 wide x 24 tall.

Run cycle: phase p in [0,1). Legs: front leg swings forward/back. I'll compute knee and foot positions with simple sinusoidal kinematics, then draw thigh and shin as thick lines (Bresenham-ish filled rects). Drawing thick lines on a pixel canvas: I'll write a `pxLine` function that draws a line of squares of given thickness using Bresenham.

Actually simpler: draw limbs as small filled rectangles rotated? Rotation on pixel art is ugly. Let's use line drawing with thickness 2-3 px. That's fine and looks pixel-arty.

Let me write helper: `drawLimb(x1,y1,x2,y2,thickness,color)` — draws a filled capsule-ish via Bresenham with square brush.

For the run cycle, compute in local sprite coordinates (origin at hip).

Let me define athlete drawing in "world" pixels with y up? No, canvas y down. Ground at groundY. Athlete's hip at groundY - 12 (leg length 12). Torso up from hip 10, head above.

Let me define local coordinate system with origin at the hip, x to the right, y down (canvas coords). Body height ~24: legs 12, torso 10, head 5.

Run cycle: 
- hip bob: y offset = -1.5*|sin(2π p)| ... actually bob twice per cycle.
- leg phase: left leg angle = A*sin(2πp), right leg = A*sin(2πp + π). Thigh angle from vertical. Knee bend depends on phase.

Let's do a simplified approach:
For each leg with phase φ:
- hipAngle = 35° * sin(φ)   (thigh swings)
- kneeBend = max(0, 90° * sin(φ + something))...

I'll do a common approximation:
thigh angle θ1 = 30° * sin(φ) (forward positive)
shin angle relative to thigh θ2 = -40° + 40° * sin(φ + 1.2) clamped... 

Hmm. Let me just hand-tune: 

For a run cycle, at φ=0 the leg is at max forward reach (heel strike-ish), φ=π max back (toe off).

thigh: θt = A*cos(φ) where A=35°, forward positive when cos>0.
knee: bend k = 20 + 55*(1+cos(φ+π*0.7))/2... 

Let me simplify with an explicit keyframe table and interpolate. Actually, let me use a formula-based approach that generally looks okay:

θ_thigh(φ) = 35° * sin(φ)         // positive = forward
θ_knee(φ)  = 60° - 60° * sin(φ + 0.9)  // bend amount, always >= 0

Knee bends backward: the shin rotates backward relative to thigh by θ_knee.

So: thigh from hip: direction = (sin θt, cos θt) scaled by thighLen. Knee pos = hip + thighLen * (sin θt, cos θt).
Shin direction: θs = θt - θ_knee (rotate backward). Foot = knee + shinLen*(sin θs, cos θs).

With θt = 35 sin φ, θknee = 60 - 60 sin(φ+0.9) → ranges 0..120.

At φ = π/2 (leg fully forward): θt = 35°, θknee = 60-60*sin(π/2+0.9)= 60-60*sin(2.47)=60-60*0.62=22.8°. Leg forward, slightly bent. Good.
At φ = -π/2 (leg back): θt = -35°, θknee = 60-60*sin(-0.67)=60+37=97°. Leg back with big knee bend (heel up). Good.
At φ=0: θt=0, θknee=60-60*sin(0.9)=60-47=13°. Straight leg passing under. Hmm, should be more bent at mid-swing but whatever.

Good enough. Also add foot: small 3x2 rect at the end.

Arms: similar with opposite phase, θ_arm = 40° * sin(φ + π) with elbow bend.

Torso lean: when accelerating, lean forward more. Lean angle from -10° (upright) to -25° (leaning forward). Rotate the whole upper body by lean. To keep it simple, I'll just offset the shoulder position horizontally by lean amount and draw torso as a line from hip to shoulder.

Actually, drawing the torso as a thick line from hip to neck with a lean offset works.

Let's define: leanPx = lean * something. When running fast, torso leans forward: neck = hip + (2.5, -10) rotated. I'll compute neck = hip + rotate((0,-10), leanAngle).

OK, use a rotate helper for 2D points. Then draw torso as a thick line, head as a circle-ish blob (a 5x5 rounded rect) at neck + up 3.

Good.

During jump: tuck — legs come forward and up, arms up. I'll define a "tuck" pose function.

During landing: legs extended forward, then absorb.

Let me define poses by blending:
- pose.run(phase)
- pose.jump(t) where t is normalized flight time: at t=0 takeoff (legs extended back), t=0.4 tuck (knees to chest), t=0.8 extend legs forward for landing, t=1 land.

Actually a real long jump: takeoff → the athlete "hitches" (cycles legs) → then extends legs forward before landing. Let's do: 
- t in [0,0.25]: legs trail back then swing forward
- t in [0.25,0.6]: tuck, knees high
- t in [0.6,0.9]: extend legs forward
- t in [0.9,1]: legs down/forward for landing

I'll implement with a keyframe interpolation over joint angles. Let's just use arrays of {t, thighL, kneeL, thighR, kneeR, armL, armR, lean}.

Simplify: define function legAngles(t) returning {thigh, knee} for each leg, and arm angles.

Let me define keyframes:
t=0.0: thigh=-40, knee=20 (legs trailing back), arms forward-up
t=0.2: thigh=-10, knee=90 (tucking)
t=0.45: thigh=50, knee=100 (knees up front)
t=0.7: thigh=65, knee=30 (extending forward)
t=0.9: thigh=55, knee=5 (legs extended forward for landing)
t=1.0: thigh=45, knee=15

Both legs similar with a slight offset (one leg slightly ahead).

OK, I'll do that.

### Sand landing

When landing, compute landingX. Draw a mark in the sand at landingX (a small divot/dark ellipse + a line). Raise particles: ~20 sand particles with velocity, gravity, fading.

Also add a "splash" of sand pixels.

### Camera and scrolling

The stadium: 
- Sky gradient (dark blue to lighter) with clouds moving.
- Stands: rows of crowd, animated (waving arms — random pixels flickering). Flags on top waving.
- Scoreboard showing attempt, distance, best, WR.
- Track/runway: red/orange track with lane lines, then the board (white with a red/blue edge), then the sand pit (light tan) with a measuring tape (a line with tick marks and numbers).

The pit should be sunken? Visually, just a rectangle of sand at ground level.

Ground line: groundY = 200 maybe (canvas 480x270). Let's set groundY = 196. Above the ground: the stands occupy y from ~60 to ~150, and the track surface from 196 down to 270.

Hmm, we need the crowd visible and the sky. Let's lay out:
- y 0..70: sky with clouds
- y 70..160: stands with crowd (multiple tiers), flags on top at y~65
- y 160..196: the far side of the track / barrier / advertising boards
- y 196..270: the track surface where the athlete runs, drawn in perspective-ish (a band). Actually for a side view, the track is a horizontal band from y=196 to y=270? The athlete stands on groundY=230 maybe.

Let me reconsider: in a side-scrolling view, the athlete's feet are on a line. Below that line is the track surface going toward the viewer (a bit of perspective) or just a band of color. Let's set groundY = 210 and fill from 210 to 270 with the track color, plus the runway strip. That gives 60px of foreground. Fine.

Hmm, but then the athlete is 24px tall standing at y=210, occupying 186..210. The stands behind at 70..160. There'd be a gap 160..210 (50px). That gap could be: a low wall / advertising boards and the far track edge. Good.

Actually let's compress: stands 60..170, then barrier/ad boards 170..186, then a strip of grass/track edge 186..196, then the running surface 196..270 with groundY = 215. Hmm, the athlete's feet at 215 and the surface extends below.

Let's just do:
- Sky: 0..64
- Stands (crowd): 64..168 (with a roof at 56..64)
- Wall/ads: 168..186
- Track surface: 186..270, with groundY = 214 (the line the athlete runs on). Below 214 is the "near" part of the track.

Hmm, but the runway and pit need to be drawn at groundY. The pit sand is a rectangle from y=214 to y=240 maybe, i.e., a shallow pit. Actually let's draw the pit as a rectangle from 210 to 238 (sunken), with the top edge at groundY.

Hmm. Simpler: everything at ground level; the pit is drawn as a sand-colored band from groundY-2 to groundY+26 (i.e., below the running line, going toward the viewer), with the front edge at groundY+26. The athlete lands at groundY.

Hmm, that means the sand pit visually extends below the athlete's feet. That's like a top-down-ish perspective. Fine, common in these games.

Actually in NES Track & Field, the pit is drawn in a pseudo-3D way extending downward. Let's do that: pit band from y = groundY to y = groundY + 28, drawn with a lighter tan, and the athlete lands "on" the line y=groundY.

Hmm, but then the sand mark is at y=groundY.

OK. Let's go with:
- groundY = 206.
- Track band from y=186 (far edge) to y=270 (near edge). Actually let's have the runway strip drawn from y=200 to y=270 as the red track, and above it (186..200) a green verge.

Let me just decide:
- horizon/stands bottom at y=170
- wall 170..184
- green verge 184..196
- track surface 196..270 (reddish)
- groundY (athlete's feet line) = 212.

The runway is a lane of the track; the pit is a sand rectangle from x_board to x_board+pitLen, y from 212 to 212+30 (i.e., 212..242), so it extends below the run line. And the board is at y 212..218 (a thin strip).

Hmm, when the athlete lands, their feet at y=212 — but the pit is drawn below. It'll look like they're landing at the far edge of the pit. That's actually fine visually.

Alternatively, put the pit centered: pit from y=200 to 226, and groundY = 213 in the middle. Then the athlete's feet at 213 are in the middle of the pit. That looks better! Let's do: pit rectangle y from 198 to 230, and groundY = 214. The runway is the same: track surface from 198 to 230 with groundY=214 in the middle. Below 230, more track (near side) to 270.

Hmm, that means the athlete runs on a line in the middle of the track band. Fine.

Actually simplest and cleanest: draw everything with groundY = 214, track band 198..270, and the pit as a lighter rectangle from 198 to 242 with the landing line at 214.

I'll go with that. And add a slight darker edge.

### Measuring tape

In the pit, draw a tape measure line along the pit with tick marks every 1 m and numbers every 1 m, and a highlighted line at the world record distance (8.95 m). Also a "best mark" line.

The tape runs horizontally at some y within the pit, e.g., y = 236 (below the landing line). Ticks going down. Numbers small.

Actually, the measuring tape should be at the ground line so the distance markers align with the landing mark. Let's put the tape at y=222 (just below the feet line) with ticks pointing down, and numbers below.

Hmm, the athlete's feet are at 214 and the pit sand is drawn from 198 to 242. The tape at y=222 with ticks. The landing mark at the athlete's landing x. OK.

Alternatively, put the tape in the foreground below the pit at y=250 across the whole width, showing distances from the board. That's clean: a tape measure strip that scrolls with the world, showing metre marks. And also draw faint vertical lines in the pit at each metre.

I'll do both: vertical metre lines in the sand (light), plus a tape strip at y=248 with ticks and numbers.

Hmm, but the tape should only span the pit region. Fine.

### HUD

Top-left: "ATTEMPT 1/3", "SPEED" bar, "ANGLE" indicator, "BEST", "LAST".
Top-right or a scoreboard in the stands: distances.

Let's do:
- HUD bar at the top (y 0..30) semi-transparent black? Or overlay on the sky. Let's overlay a dark strip at the top with the HUD. But we also want the sky visible. Hmm, the sky is 0..64. Let's put the HUD at the bottom instead? NES Track & Field puts it at the top.

Let's put the HUD in the top 26 pixels: a translucent dark panel. Actually let's draw the scoreboard in the stands (a big board) and the speed/angle meters at the bottom of the screen (like the original which has the speed bar at the top... actually in the original the speed bar is at the top-left as a vertical/horizontal bar).

I'll do:
- Top strip (0..24): dark blue panel with: left = "SPEED" + bar; center = "ATTEMPT 1/3"; right = "BEST 0.0M".
- Bottom strip (256..270): angle indicator + hints? Hmm.

Actually the angle selector in the original is a small arc/bar near the athlete. Let's put the angle gauge at the bottom-left as a vertical bar with a moving marker, plus a numeric angle.

Let me do:
- Top panel (0..22): SPEED bar (horizontal, fills with alternating key presses), ATTEMPT counter, BEST.
- Bottom panel (248..270): ANGLE gauge (horizontal bar with a marker swinging), plus current angle degrees, plus hint text "PRESS < > TO RUN".

Hmm, 22px tall top panel at 480 wide: fine with 5x7 font.

Let's write:
Top panel:
- x=4,y=4: "SPEED" (5x7 font)
- speed bar: x=44..200, y=4..14 (filled proportionally)
- x=210: "TRY 1/3"  → "ATT 1/3"
- x=300: "BEST" then value
- x=380: "WR 8.95"

Bottom panel:
- Angle gauge: a horizontal bar from x=4 to x=180, with tick marks, marker at current angle.
- Text "ANGLE 42" 

Plus a "distance" readout after landing.

And during the replay, show "REPLAY" and slow-mo.

### Game states

- TITLE? Maybe skip, go straight to the game. But a title screen is nice. Let's have a brief title screen with "PRESS ENTER" or auto-start. Actually requirement: "The animation should show everything important within the first 30 seconds". So maybe skip the title, or make it auto-dismiss. Let's start directly in the game with the athlete at the start of the runway, and a "GO!" prompt. Actually, let's include a short title that auto-advances after 2 seconds or on keypress. Hmm, in autoplay mode it should just play. Let's skip the title screen entirely and start with attempt 1. Add a small intro text "PRESS LEFT/RIGHT ALTERNATELY" for a moment.

Hmm, but a title screen is part of the classic. I'll add a very brief title (1.5s) that any key skips, and autoplay skips it. Actually, to guarantee good footage, let's just start immediately with the run. I'll skip the title. Actually let's include it but auto-advance after 2.5s. Hmm — "show everything important within the first 30 seconds" — a title screen wastes time. Skip it. Start directly.

States: 
- 'ready' (brief countdown 1s: "GO!")
- 'run' (athlete runs, player mashes, angle swings)
- 'flight' (in the air)
- 'land' (landing, sand puff, mark)
- 'result' (show distance, wait ~2s)
- 'replay' (slow motion replay of the run-up + jump)
- 'gameover' (results screen after 3 attempts)

Flow: run → flight → land → result → replay → next attempt → ... → after 3 attempts → results screen → then loop back to attempt 1 (to keep looping for the recording).

Actually, "it may loop or continue after that" — so after the results screen, wait a bit then restart. Good.

### Replay

Record the athlete's state (x, y, pose params, phase, etc.) each frame during run+flight+land into an array. Then play it back at 0.35x speed. Camera follows. Show "REPLAY" and a slow-motion indicator.

Recording: store {x, y, phase, state, angle, lean, tuckT, ...}. Simpler: store the full render state each frame: {x, y, phase, mode, lean, jumpT}. Then during replay, just call the same draw function with those params.

Let's make the athlete draw function take a state object: {x, y, phase, mode, lean, jumpT, ...}. Then replay = iterate through the recorded array.

Recording length: run ~4-6 s at 60fps = 360 frames, plus flight ~1.2s = 72 frames, plus land. ~500 frames * ~10 numbers = fine.

Actually the replay should start a bit before the takeoff (the last ~2 seconds of the run) — let's record everything and replay the last N frames before takeoff + flight + landing.

### Autoplay AI

Toggle with P. When on, the AI controls the player:
- Mash: alternate the two keys at a good rate (e.g., 12 presses/sec) to fill the speed bar.
- Jump at the right moment: when x is close to the board front (within a few px), press jump. Aim for takeoff right at the board edge.
- Choose the angle: since the angle swings, the AI should press jump when the angle is near optimal (45°). But it also must take off at the right x. Conflict. Solution: the angle oscillates fast enough that near the board, the AI waits for both conditions: x in the takeoff window AND angle near optimal.

Better: make the angle oscillation period ~0.9s so it passes through the optimal angle frequently. The AI checks: if x is within the takeoff window (last ~1.5m) and |angle - 45| < 6, then jump.

Hmm, but if it waits too long it'll pass the board. Let's make the AI: compute the ideal takeoff x. If x >= idealX - 3 and angle within tolerance → jump. If x >= boardFront - 2 (about to foul) → jump anyway.

Also, the speed: the AI needs max speed. Mash at ~14 Hz which should fill the bar.

Actually, let's make speed increase per press and decay so that ~10 presses/sec gets near max.

Let's define: speed in m/s, max 11.6. Each press: speed += 0.28, capped. Decay: speed -= 1.6 * dt (per second). Hmm, at 10 presses/sec that's 2.8/s gain vs 1.6/s decay → net +1.2/s. From 0 to 11.6 takes ~10 s. Too slow for a 35m runway.

Let's tune: each press += 0.42, decay 1.2/s. At 12 presses/s: gain 5.04/s, decay 1.2 → net 3.84/s → 3 s to max. Good. Runway 35m at avg 7 m/s ≈ 5s. Good.

Hmm, but a human mashing at 6/s: gain 2.52, decay 1.2, net 1.32/s → 8.8s. Too slow. Let's make the decay proportional to speed: decay = 0.06 * speed per second? Then at max speed 11.6, decay = 0.7/s. At 6 presses/s: gain 2.52/s. So it'd hit max in ~5s. OK.

Let's do: decay = speed * 0.09 per second (so equilibrium at pressRate*0.42 = speed*0.09 → speed = 4.67*pressRate). At 6/s → 28 m/s (capped at 11.6). Hmm too easy.

Let's do: decay = speed * 0.35 per second → equilibrium speed = 0.42*rate/0.35 = 1.2*rate. At 10/s → 12 m/s. At 6/s → 7.2 m/s. At 4/s → 4.8 m/s. That's a nice spread. And the time constant is 1/0.35 ≈ 2.9s. Hmm, that's a bit slow to reach max but OK.

Actually, let's just make it snappier: decay = speed*0.55/s → equilibrium = 0.76*rate. At 14/s → 10.7. At 12/s → 9.1. Hmm, need max ~11.6 for a WR.

Let's use: per press += 0.5 m/s, decay = speed * 0.5 /s. Equilibrium = rate (m/s per press per sec... ). Actually equilibrium speed = 0.5*rate/0.5 = rate. So speed_eq = presses per second. Nice and clean! At 11 presses/sec → 11 m/s. Max cap 11.8.

Time constant 2s. From 0, reaching 63% in 2s, 86% in 4s, 95% in 6s. Runway at 35m: hmm.

Let's make the runway 45 m to give more time. At an average speed of 8 m/s, 45m takes 5.6s. Reaching ~92% of max. Good.

Actually, let's shorten: make the acceleration faster with a time constant of ~1.2s: decay = speed*0.85/s, press += 0.85*... hmm, then equilibrium = rate again if press gain = 0.85*... no: eq: gain = press*G, decay = speed*D. eq speed = press*G/D. Want eq = press (i.e., speed in m/s ≈ presses/sec), so G/D = 1 → G = D. With D = 0.85 and G = 0.85: 12 presses/s → 10.2 m/s. Time constant 1/0.85 = 1.18s. 

But G=0.85 per press is a big jump per press. It's fine — the bar visibly jumps.

Hmm, but with a max cap of 11.8, mashing at 14/s gives 11.8 (capped). Good.

Let's go: G = 0.85 m/s per alternating press, D = 0.85 /s decay, cap 11.8 m/s. Runway length 45 m.

Hmm, 45 m runway is long: 45*18 = 810 px. At a screen width of 480 with the athlete at x=150, the camera scrolls 810+ px. Fine.

Actually, for the game to be fun and quick, maybe 35m. At 10 m/s that's 3.5s of running. Reaching 10 m/s takes ~2.5s... over 35m at avg 7 m/s = 5s. OK, 35m is fine. Let's do 38 m.

Let me use PPM = 18 px/m. Runway: 38 m → 684 px. Pit: 10 m → 180 px. Plus some space after.

World coordinates: 
- startX = 0 (athlete start)
- boardFront = 38*18 = 684
- boardBack = 684 - 0.25*18 ≈ 679.5 → board is 4.5px. Hmm, too thin. Real takeoff board is 20cm ≈ 3.6px. That's too thin to see.

Let's exaggerate: make the board 1 m wide visually (18 px) but the foul line is its front edge. Hmm, that's a huge board. In the original game the board looks like ~2 metres. Let's make it 1.5 m = 27 px, drawn as a white board with a red foul line at the front edge.

Actually, real long jump: there's a 20cm board and a plasticine indicator. The athlete's foot must not cross the front edge. Visually, I'll draw a 20px wide white board with the front edge marked in red. And the measurement starts from the front edge.

OK.

- boardFrontX = 684, boardW = 20 → boardBackX = 664.
- pitStart = boardFrontX (the pit starts right after the board)
- pitEnd = boardFrontX + 11*18 = 684 + 198 = 882.

Landing must be before pitEnd. If the jump is too long, we cap it (or the athlete lands beyond the pit → still counts, but the pit ends). Let's make the pit 12m long = 216 px → ends at 900.

Total world width ~ 950.

Camera: camX = athleteX - 150, clamped to [-20, worldEnd - 480 + 60]. Hmm, at the start the athlete is at x=0, camera would be -150. Let's clamp camX >= -60 so we see some of the start area. Actually let's just start the athlete at x=0 and camX = -80 (showing some lead-in). And the athlete's screen position = worldX - camX.

Actually for the takeoff, the athlete should be visible near the board and the pit visible. With the athlete at screen x=150 and the board at 684, when the athlete is at 684 the board is at screen 150. The pit extends to 900 → screen 366. Good, visible.

Let's set the athlete's screen x target to 140 during the run, and during the flight, keep the camera following so we see the arc and landing.

During flight, the camera should follow the athlete too. At landing, the athlete is at ~684 + 8*18 = 828. Camera = 828-140 = 688. Pit end at 900 → screen 212. Fine.

Camera clamp: camX in [-100, 500]? worldEnd = 900 + some. Let's clamp camX to [-120, 900-480+80] = [-120, 500]. Hmm, at camX=500 we see up to x=980. Fine.

Actually let's not overthink; clamp camX to [-120, 460].

Hmm wait, when the athlete is at 0 and camX = -120, the athlete's screen x = 120. Good.

Camera target = athleteX - 140, clamped.

Smooth the camera with lerp.

### Angle gauge

While running, the angle oscillates: angle = 45 + 30*sin(t*ω)? Let's do 20° to 70°, so angle = 45 + 25*sin(2π t / T), T = 0.8s. So it sweeps 20..70 in 0.8s. Hmm, that's fast — a human would find it hard. Let's use T = 1.0s. Range 20..70.

Optimal for distance: 45°. So the player must press when the gauge is near 45 going up or down.

Hmm, but actually if the max distance is at 45°, then the gauge at 45 is hit twice per cycle. That's ~2 opportunities per second. Fine.

But wait — realistic long jump angle is ~20°. Let's make the physics: distance = v²sin(2θ)/g with g=15. At θ=45, d = v²/15. v=11.8 → 9.28 m. That beats the WR (8.95). Good. At θ=20, d = 11.8²*0.643/15 = 5.96 m.

Hmm, the difference between 45° and 20° is huge. That's fine for gameplay.

Actually, let's reconsider: a real long jump takeoff at 45° isn't possible at high speed. But whatever, it's a game.

Hmm, but maybe more satisfying: make the optimum ~35-40° so the gauge at 45 isn't perfect. Eh, keep it simple: optimum 45.

Actually, let me add a small correction: the athlete's center of mass is elevated at takeoff and landing, which reduces the optimal angle. Let's use: launch height h0 = 1.0 m above the landing height... no wait, in a long jump the athlete lands lower than takeoff. Ugh. Skip.

Let's use the simple projectile: 
vx = v*cos θ, vy = v*sin θ (m/s)
x(t) = vx*t, y(t) = vy*t - 0.5*g*t²
Land when y(t) = 0 → t = 2*vy/g.
d = vx * 2*vy/g = 2*v²*sinθ*cosθ/g = v²*sin(2θ)/g. Yes.

With g=15, v=11.8, θ=45 → 9.28m.

Good, WR line at 8.95 m. Achievable with a near-perfect jump.

Also add: the athlete takes off from the board which is at ground level, so no height bonus.

### Foul

If takeoffX > boardFrontX → foul. Show "FOUL!" and distance = 0, attempt counted.

Also if the athlete's foot crosses... well, takeoff point = athlete's x position at jump. Actually the athlete's foot position. Let's use the athlete's hip x.

Hmm, the athlete is drawn with the hip at (x, y). Let's say the takeoff point is the athlete's x at the moment of jumping. If x > boardFrontX → foul.

Since the board's front edge is the line, and the athlete's x is roughly their center, we should use the foot position. Let's just use x - 4 (the front foot is a bit behind the center)? Overcomplicating. Use x.

Actually, to make it visually correct: the athlete's feet should be at the board when taking off. The athlete's sprite: the hip is at x, the feet are around x ± 6. Let's define the takeoff foot at the hip x. Fine.

So foul if x > boardFrontX at takeoff.

### Scoreboard in the stands

Draw a scoreboard above the stands showing: ATT, BEST, LAST. Actually the HUD covers that. Let's draw a nice scoreboard anyway in the stands at the far right or center. Maybe redundant. Let's put a big scoreboard on the left of the stands showing the current distance. Hmm.

Actually, let's put the scoreboard in the stands (a big dark panel with yellow LED-style digits) showing: "ATT 1", "BEST 8.12", "WR 8.95". And keep the HUD minimal at the top with the speed bar and angle.

Hmm, screen space. The stands are 64..168, that's 104px tall. A scoreboard 90x50 in there works.

Let's put the scoreboard at world-fixed screen position? It should be part of the stadium, so it scrolls with the camera. But then it might go off-screen. Let's make it parallax-fixed (moves slowly) so it's mostly visible. Or just put it at screen-fixed position over the stands. I'll make it screen-fixed at the right side (x=370..470, y=70..120). It looks like it's part of the stadium since the stands scroll behind it.

Hmm, that could look odd. Let's use a parallax factor of 0.15 so it drifts slowly.

Eh, simplest: screen-fixed overlay with a "stadium scoreboard" look. I'll do that.

Actually, I'll draw the scoreboard as part of the far stands (parallax 0.1) positioned at world x = 300 or so... it'd drift off. Let's just do screen-fixed. Fine.

### Crowd

Draw rows of little 3x4 pixel people in the stands, with colors varying. Animate: some of them have arms up that wave. Use a deterministic pseudo-random per person with a phase; the arm position changes with time.

Performance: the stands are 480 wide, 100 tall, with 3px people → 160 x 25 = 4000 people per screen. Too many. Let's do larger: 5px wide, 8px tall people → 96 x 12 = 1150. Still a lot per frame but we can pre-render the crowd to an offscreen canvas and only animate a few.

Better: pre-render the crowd to an offscreen canvas (a repeating tile, say 480x104) once, then blit it with parallax. For waving, overlay a few animated "wavers" (like 30 sprites) drawn each frame.

That's efficient. Let's do that.

Actually the crowd needs to scroll with parallax. Pre-render a tile of width 480 (or 960) and blit it twice with the offset.

Let's pre-render crowdTile as an offscreen canvas of 480x110 with the stands structure (tiers, aisles, people). Then draw it at (-(camX*0.25) % 480, y).

For animation, draw ~40 waving people on top at positions derived from a hash, with the wave phase from time. Their x positions should scroll with the crowd. So: for i in 0..40: worldX = hash-based position in [0, 2000); screenX = worldX - camX*0.25 mod something. Simpler: use a fixed set of columns across the visible width, e.g., for k in 0..30: x = k*16 + ((t*8) mod 16) - 16... no.

Simplest: pick N=50 waving people at fixed *screen-ish* positions computed from a modular pattern: x = ((i*37 + Math.floor(camX*0.25)) % 480). Hmm, that would make them jump.

Let's just do: for each waving person i, its world position wx_i = i*23 + 5 (in the parallax world). screenX = wx_i - camX*0.25, wrapped modulo 520 into [-20, 500]. Wrapping causes popping but they're tiny.

Eh, it's fine — small pixel people. Actually, popping is visible. Alternative: don't scroll the wavers; just have them wave in place at fixed screen positions. Since the crowd tile scrolls, the wavers would appear to slide relative to the crowd. But if the crowd tile scrolls slowly (parallax 0.15) and the wavers are at fixed screen positions, it's noticeable over a long run.

Alternative: make the crowd NOT scroll at all (parallax 0), i.e., the stadium stands are static and only the track scrolls. That's actually common in these games and looks fine. Then the wavers can be at fixed screen positions.

Hmm, but a completely static background with a scrolling track might look odd. Let's give the stands a very slow parallax (0.1) and just pre-render the whole stand strip (width 480+some) and blit with wrapping. For the wavers, compute their positions in the same parallax space with modulo wrapping, and use a fade at the edges to hide the pop. Or just accept it.

Actually — simplest robust solution: pre-render the crowd tile AND animate the waving by drawing arms on top, where the waver positions are chosen from the same pseudo-random sequence used to generate the crowd, and I recompute the visible ones each frame based on the camera. Since the crowd tile is generated deterministically, I can also generate a list of "waver" positions (e.g., every 17th person) in tile space, and then for each tile copy drawn, draw its wavers. So: tile width 480, we draw 2 copies at offsets; wavers are drawn per copy at (tileX + wx, wy) with the wave phase from (wx, wy, time). That's consistent and no popping (except at the tile seam, which is fine since it's periodic).

Number of wavers: let's say 24 per tile, 2 tiles = 48. Fine.

Good, that works.

### Flags

Draw a few flags on poles above the stands. Waving: the flag is drawn as a series of vertical strips whose vertical offset varies sinusoidally with x and time. Draw with pixel columns.

### Clouds

A few clouds in the sky, drifting slowly, with parallax.

### Sky

A gradient from deep blue at the top to lighter near the horizon. Plus maybe a sun.

Drawing a gradient on a pixel canvas: draw horizontal lines with interpolated colors. 64 lines, fine.

### Sound?

No audio required, and autoplay audio would be blocked. Skip. Maybe add a tiny WebAudio beep? Not required. Skip to keep it simple. Actually, a bit of sound would be nice but the requirement doesn't ask. Skip.

### Now let's write the code.

Structure:

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Track &amp; Field — Long Jump</title>
<style> ... </style>
</head>
<body>
<canvas id="c"></canvas>
<script>
(function(){
  ...
})();
</script>
</body>
</html>
```

CSS: body black, canvas centered, image-rendering: pixelated, scaled with CSS transform or width/height in px.

I'll compute the integer scale factor on resize: scale = max(1, floor(min(innerWidth/W, innerHeight/H))). Set canvas.style.width = W*scale + 'px'.

Canvas: width=480, height=270. Actually let's use 448x252? No, 480x270 is fine.

Hmm, one concern: with a 480x270 canvas and 5x7 font, text is readable at 1x but at 3-4x scale it's chunky and readable. Good.

Let me now write the code.

```js
const W = 480, H = 270;
const cvs = document.getElementById('c');
const ctx = cvs.getContext('2d');
cvs.width = W; cvs.height = H;
ctx.imageSmoothingEnabled = false;
```

Resize handler.

### Font

```js
const FONT = {
 'A':"01110,10001,10001,11111,10001,10001,10001",
 ...
};
```

I'll write a helper `drawText(str, x, y, color, scale)`.

For efficiency, cache glyph rendering? Not needed; 5x7 = 35 fillRect per char. With ~100 chars on screen that's 3500 fillRects per frame. That might be slow. Let's pre-render the font into an offscreen canvas atlas at 1x, then blit glyphs. 

Pre-render each glyph to a small canvas (5x7) in white, then use it as a mask... but we need color. Alternative: pre-render each glyph in a few colors. Or: draw the text into an offscreen canvas once per unique string+color... 

Simplest efficient approach: pre-render the whole font atlas in white on an offscreen canvas (glyph grid), then for each char, drawImage from the atlas with globalCompositeOperation... no, that doesn't tint.

Alternative: use fillRect but batch — actually 3500 fillRects at 60fps is probably OK in modern browsers. Canvas fillRect is fast. Let's estimate: 3500 fillRects/frame * 60 = 210k/s. That's fine.

Actually, most HUD text is static-ish. Let's just do fillRect. But we can optimize: only draw pixels that are '1'. Average glyph has ~15 set pixels. 100 chars * 15 = 1500 fillRects. Totally fine.

OK, use fillRect.

### Helper drawing functions

```js
function px(x,y,w,h,c){ ctx.fillStyle=c; ctx.fillRect(x|0,y|0,w,h); }
```

Actually use Math.round or |0. Since we're at pixel scale, floor is fine.

```js
function line(x0,y0,x1,y1,thick,color){
  // Bresenham with square brush
}
```

I'll implement:
```js
function limb(x0,y0,x1,y1,t,col){
  x0=Math.round(x0); y0=Math.round(y0); x1=Math.round(x1); y1=Math.round(y1);
  let dx=Math.abs(x1-x0), sx=x0<x1?1:-1;
  let dy=-Math.abs(y1-y0), sy=y0<y1?1:-1;
  let err=dx+dy;
  ctx.fillStyle=col;
  const h=Math.floor(t/2);
  while(true){
    ctx.fillRect(x0-h, y0-h, t, t);
    if(x0===x1&&y0===y1) break;
    const e2=2*err;
    if(e2>=dy){err+=dy;x0+=sx;}
    if(e2<=dx){err+=dx;y0+=sy;}
  }
}
```
Good.

### Colors palette

```js
const C = {
  sky1:'#1a2a5e', sky2:'#4a7ec7', sky3:'#8fc4e8',
  ...
};
```

Let me define a nice palette:
- Sky top: #101a3a → #2a4a8f → #6fa8dc near horizon.
- Clouds: #cfe6f7 with a #9dc4e0 shadow.
- Stands structure: #3a3f52 dark blue-gray; tiers #4a5068.
- Crowd colors: various bright.
- Roof: #2a2e3d with a highlight.
- Flags: red/yellow/blue.
- Wall/ads: #d8d8d8 with colored panels.
- Verge (grass): #2f7a3f, #3f9a4f.
- Track: #c05030 / #a8402a with white lane lines.
- Board: #f0f0f0 with a red front edge.
- Sand: #e8c87a, with darker #c9a45c specks, and the mark #a8834a.
- Athlete: skin #f0c090, hair #3a2a1a, top #e03030 (red), shorts #202040 (dark blue), shoes #ffffff.

Let's write it.

### World constants

```js
const PPM = 18; // pixels per metre
const RUNWAY_M = 38;
const BOARD_X = RUNWAY_M * PPM; // front edge of board = 684
const BOARD_W = 22;
const PIT_M = 12;
const PIT_START = BOARD_X;
const PIT_END = BOARD_X + PIT_M*PPM; // 684+216 = 900
const GROUND_Y = 214;
```

Athlete start x = 0. Hmm, actually the athlete should start behind, so the run-up is 38m. Let's start at x = -0? Let's start at x=0 and the board front at 684 → 38m of run-up. Good.

### State machine

```js
const G = {
  state: 'ready',   // ready | run | fly | land | result | replay | over
  t: 0,             // state timer
  attempt: 0,
  best: 0,
  results: [],
  speed: 0,
  angle: 45,
  angleT: 0,
  x: 0, y: 0,
  vx: 0, vy: 0,
  phase: 0,
  lean: 0,
  jumpAngle: 0,
  takeoffX: 0,
  foul: false,
  dist: 0,
  camX: -120,
  lastKey: null,   // 'L' or 'R'
  ...
};
```

### Input

Keys: ArrowLeft / ArrowRight (or A/D, or Z/X) alternate for running. Space / ArrowUp / Z for jump? Let's use: Left/Right arrows to run (alternate), Space or Up to jump.

Hmm, the classic uses two buttons alternately. Let's support: Left Arrow & Right Arrow, and also Z & X. And Space/Up/Enter for jump.

Actually let me define: run keys = ['ArrowLeft','ArrowRight','KeyZ','KeyX','KeyA','KeyD']? Hmm, 'A'/'D' with 'D' also... let's keep it simple: ArrowLeft/ArrowRight and Z/X. Jump: Space, ArrowUp, or Enter... but Enter is also used for menus. Let's use Space / ArrowUp / KeyC.

Wait, Z/X as run keys and Space as jump. Hmm, but many will use arrows. Let's accept:
- Run: ArrowLeft, ArrowRight, KeyA, KeyD, KeyZ, KeyX — no wait, if both A and D count as "left" and "right" respectively, and Z/X too, then alternating any of them works. Let's define leftKeys = {ArrowLeft, KeyA, KeyZ}, rightKeys = {ArrowRight, KeyD, KeyX}. Hmm, A/Z both left. That's a bit odd but fine.

Actually classic Track & Field: you alternate two buttons. Let's just say: alternate LEFT and RIGHT arrow keys, or A/D, or Z/X. And JUMP = Space or ArrowUp or W... no, W conflicts with nothing. Let's do Jump = Space, ArrowUp, or KeyK? Let's use Space and ArrowUp and Enter.

Simpler: 
- RUN: ArrowLeft/ArrowRight (also A/D, also Z/X)
- JUMP: Space (also ArrowUp, also Enter... but Enter for menus)

Hmm, ArrowUp for jump while ArrowLeft/Right for run is natural.

Let's define:
```js
const LEFT_KEYS = ['ArrowLeft','KeyA','KeyZ'];
const RIGHT_KEYS = ['ArrowRight','KeyD','KeyX'];
const JUMP_KEYS = ['Space','ArrowUp','Enter','KeyK'];
```

Wait, but ArrowUp as jump plus ArrowLeft/Right as run — a player using arrows would press Left, Right, Left, Right, then Up. That works.

OK.

Key handling: on keydown, if the key is a left/right key and it's different from the last one pressed, add speed. Prevent default for arrows/space.

Also handle 'KeyP' for autoplay toggle, and 'KeyR' maybe for restart.

### Run mechanics detail

```js
function onRunKey(side){
  if(G.state!=='run') return;
  if(side===G.lastSide) return; // must alternate
  G.lastSide = side;
  G.speed = Math.min(MAX_SPEED, G.speed + PRESS_GAIN);
  // trigger a stride (visual)
  G.stepFlash = 1;
}
```

Hmm, but should the visual run cycle be driven by the key presses? Yes! In the original, the legs move with each press. Let's make the run phase advance with each press: phase += 0.5 per press (each press = half a cycle = one step). That gives a nice "mashing = running" feel.

But then if the player stops mashing, the legs freeze. That's authentic. But for smoothness, let's blend: phase advances with speed AND with presses.

Hmm. Let's do: phase advances at a rate proportional to speed (like real running), and each press adds a small "kick". Actually in Track & Field, the sprite's legs move exactly with the button presses. Let's do that: each alternating press advances the phase by 0.5 (so two presses = full cycle = both legs). And add a bit of automatic advance based on speed so it doesn't look frozen.

Let's do: phase += 0.5 per press, and phase += speed*0.06*dt*60 as a baseline... Hmm, might look weird.

I'll do: each press advances the phase by 0.5. Plus a slow auto-advance proportional to speed (so at max speed without pressing, the legs still move slowly). Actually no — let's keep it press-driven, which is the classic feel. But add: if no press for a while, the legs settle to a standing pose.

Hmm, simplest: phase advances by 0.5 per alternating press. That's it. At 12 presses/sec → 6 cycles/sec = 12 steps/sec. That's fast, realistic for sprinting.

Wait, one full cycle = 2 steps. 6 cycles/s = 12 steps/s. Yes, correct for sprinting.

Good, press-driven. 

But: the distance the athlete moves is determined by `speed` (m/s), which is continuous. So the legs and the ground movement might not match perfectly. At 12 presses/s and 12 m/s, each press = 1m = 18px, and each step = 1 cycle/2... hmm, 12 presses/s = 6 cycles/s, so each cycle covers 2m = 36px. A stride of 2m is realistic. 

### Angle oscillation

While running: angleT += dt; angle = 45 + 25*sin(2π*angleT/1.1). Range 20..70.

Actually let's make it so the angle indicator is meaningful: display it as a bar.

### Jump

On jump key (state 'run'):
- takeoffX = G.x
- foul = takeoffX > BOARD_X
- launch: vx = speed*cos(angle), vy = speed*sin(angle) (m/s, y up positive)
- state = 'fly', t=0
- record start

Physics in the fly state:
```
G.vy -= G.g * dt;  // using y-up in metres
G.x += G.vx * dt * PPM;
G.y += G.vy * dt * PPM;  // y-up, so screen y = GROUND_Y - height
```
When y <= 0 → land.

Also apply a slight air drag? Not needed.

g = 15 m/s².

Hmm, wait: with v=11.8 and θ=45°, vy = 8.34 m/s, t_flight = 2*8.34/15 = 1.11s. Airtime ~1.1s. Good for a replay.

Max height = vy²/(2g) = 69.6/30 = 2.32 m = 41.7 px. The athlete's hip would be at GROUND_Y - 41.7 = 172. Fine, within the screen.

Good.

Distance = v²sin(2θ)/g = 139.24/15 = 9.28 m. Plus, the athlete takes off at BOARD_X so the landing is at BOARD_X + 9.28*18 = 684+167 = 851. Pit ends at 900. Good.

### Landing

When y <= 0:
- state = 'land'
- compute dist = (x - BOARD_X)/PPM
- if foul → dist = 0, show FOUL
- if x < BOARD_X → negative, clamp to 0
- Create sand particles
- Record the landing mark
- After a delay, state = 'result'

Actually, let's do the landing as a short state with the athlete absorbing the impact (sinking into the sand), then the result.

### Result

Show the distance with a big readout, wait 2s, then start the replay.

### Replay

Play back the recorded frames at 0.35 speed. Show "REPLAY" text and a slow-motion bar.

The recorded frames should cover from ~2s before takeoff to landing. Let's record continuously into a ring buffer during the run and flight. On landing, extract frames from (takeoffFrame - 120) to the end.

Each frame: {x, y, phase, mode, lean, jumpT, speed, angle}.

The athlete draw function needs: x, y (screen), phase, mode ('run'|'fly'|'land'), lean, jumpT, and the run phase.

Let's write `drawAthlete(x, y, st)` where st has {mode, phase, lean, jumpT, vy}.

For the replay, we just call drawAthlete with the recorded values.

Also during the replay, the camera should follow. Record camX too? Or recompute. Let's record camX as well... actually simpler to recompute from x: camX = clamp(x - 140, ...). But the live camera is smoothed. For the replay, let's just use a smoothed camera computed on the fly. Fine.

### Results screen

After 3 attempts, show a table of attempts and the best. Wait 4s, then reset.

### Autoplay AI

```js
if(autoplay){
  // run
  if(G.state==='run'){
    aiTimer -= dt;
    if(aiTimer<=0){ aiTimer += 1/AI_RATE; onRunKey(aiSide); aiSide = aiSide==='L'?'R':'L'; }
    // jump decision
    const distToBoard = BOARD_X - G.x;
    if(G.x > BOARD_X - 200){  // within ~11m
      const idealAngle = 45;
      if(Math.abs(G.angle - idealAngle) < 4 && distToBoard < 40 && distToBoard > 0) doJump();
      if(distToBoard < 4) doJump();
    }
  }
}
```

Hmm, need the AI to jump at the right x with a good angle. Since the angle oscillates with period 1.1s and the athlete covers ~12 m/s = 12m/s, in 1.1s they cover 13m. So the angle window near 45° (|angle-45|<4 → within ±4° of 45 out of a ±25 swing) lasts about... angle = 45+25 sin(ωt). Near the peak, it's slow. But we want 45 which is the center, where the derivative is max. |25 sin| < 4 → |sin| < 0.16 → ωt within ±0.16 rad → dt = 0.16*1.1/(2π) *2 = 0.056s. So the window is ~0.11s wide, twice per 1.1s cycle. In 0.11s the athlete moves 1.3m = 23px. 

So the AI should jump when it's within ~25px of the board AND the angle is within 4° of 45. But it might be at 20px and the angle window comes at 5px. Then it jumps at 5px. If the window doesn't come before x=BOARD_X, it fouls.

Better approach: predict. Compute when the angle will next be 45° and where the athlete will be. Let's do a simple predictive approach:

Each frame in the AI run state:
- Compute the time until the angle next equals 45° (going in the direction). Actually, we can compute the target time t45.
- Predicted x at that time = x + speed*t45.
- If predicted x is within [BOARD_X - 25, BOARD_X] then jump now? No — jump when the predicted x at t45 is near BOARD_X. Hmm, but we must jump exactly at t45.

Alternative: just check each frame: if the angle is within tolerance of 45 AND x is within the last 1.5m → jump. With a 1.5m window and the window being 1.3m wide, it should usually work. And add a fallback: if x > BOARD_X - 8, jump regardless (to avoid a foul, though the angle might be bad).

Hmm, the risk is the AI's speed varies. Let's make the AI's speed constant at max once achieved.

Let me just compute: the angle is 45 + 25 sin(2π t / T) with T=1.1. The athlete's x at time t is roughly x0 + v*t. We want the angle ≈ 45 when x ≈ BOARD_X - 3.

Let t_jump be the time when the athlete reaches BOARD_X - 3: t_jump = (BOARD_X - 3 - x)/v.
We need angle(t_jump) ≈ 45, i.e., 2π t_jump / T ≈ kπ, i.e., t_jump ≈ k*T/2.

So we can adjust: if the next 45-crossing happens at time t45 = ceil(...)... 

Let's just do: compute t45 = the smallest t >= 0 such that angle(t + t45) is within tolerance. Then jump when t45 <= dt (i.e., now) and the athlete's x is in the window [BOARD_X - 30, BOARD_X].

Simpler practical approach: 

```js
const v = Math.max(G.speed, 1);
const tToBoard = (BOARD_X - 2 - G.x) / v;  // seconds
// find the next time the angle equals 45 (in the future), relative now
// angle(t) = 45 + 25 sin(2π(t0+t)/T)
// want sin(...) = 0 → 2π(t0+t)/T = kπ
```

Let me define φ = 2π * G.angleT / T. We want φ + 2π t/T = kπ → t = (kπ - φ) * T/(2π).
Find the smallest t >= 0 with k integer: k = ceil(φ/π). Then t45 = (kπ - φ)*T/(2π).

Then if |t45 - tToBoard| < 0.05 → jump.

Hmm, but we also need t45 <= tToBoard (otherwise we'd overshoot). Actually we want to jump when the athlete is at the right x AND the angle is 45. Since we can't control both exactly, we should jump at the moment when the angle is 45 and the x is as close to the board as possible without fouling.

Let's do: at each frame, if t45 <= tToBoard (the next 45-crossing happens before we reach the board), then wait. Actually we want the crossing to happen as close to the board as possible. So we want the largest t45 that is <= tToBoard. 

So: if t45 <= tToBoard and the next crossing (t45 + T/2) > tToBoard → jump now (well, jump at t45).

Implementation: each frame compute t45. If t45 <= tToBoard and t45 <= dt (about to happen this frame) → jump. Since t45 decreases as time passes and jumps back up after crossing.

Hmm, this is getting complex. Let's simplify: 

```js
// AI jump logic
const v = Math.max(G.speed, 2);
const tToBoard = (BOARD_X - 2 - G.x) / v;
// next time angle == 45
let phi = 2*Math.PI*G.angleT/T_ANG;
let k = Math.ceil(phi/Math.PI);
let t45 = (k*Math.PI - phi)*T_ANG/(2*Math.PI);
if (t45 <= tToBoard) {
   // the next 45-crossing is before the board; check the following one
   let t45b = t45 + T_ANG/2;
   if (t45b > tToBoard) {
     // this crossing is the last before the board → jump at t45
     if (t45 < 0.02) doJump();
   }
}
```

Also a safety: if tToBoard < 0.02 → jump now (avoid foul/overshoot).

Hmm, if t45 <= tToBoard but t45b <= tToBoard, we skip and wait for the next one. Good. That naturally picks the last crossing before the board.

But there's a subtlety: t45 could be slightly negative due to floating point. Handle with mod.

Also the athlete's speed changes (it's decaying). Let's have the AI keep mashing at max rate so the speed is capped at MAX_SPEED.

Also, we should add a small margin: the AI should jump slightly before the board so it doesn't foul. Let's target BOARD_X - 4.

Also, the angle gauge might not be exactly 45 at the jump; a few degrees off is fine.

I think this works. Let me also add: if autoplay and the state is 'result'/'replay'/'over', auto-advance (skip the waits quickly).

Actually, the states auto-advance with timers, so it's fine. Just make the timers a bit shorter in autoplay.

### Now let's write the rendering.

Order:
1. Sky gradient + sun + clouds
2. Stands (roof, crowd tile with parallax, flags)
3. Wall / ad boards
4. Verge
5. Track surface + runway + board + pit + tape
6. Landing marks
7. Athlete
8. Particles
9. HUD / overlays

Let's write each.

#### Sky

```js
function drawSky(){
  const g = ctx.createLinearGradient(0,0,0,80);
  g.addColorStop(0,'#0d1b3e');
  g.addColorStop(0.5,'#2a4a8f');
  g.addColorStop(1,'#6fa8dc');
  ctx.fillStyle=g; ctx.fillRect(0,0,W,80);
}
```
Hmm, createLinearGradient each frame is a bit wasteful but fine. Actually let's precompute it once.

Actually with pixel art, a gradient might look smooth/non-pixelated. It's fine.

Hmm, "pixel art drawn procedurally" — a gradient is fine.

Let's do a banded gradient (posterized) for a retro look: 8 bands.

```js
const SKY_BANDS = ['#0a1430','#122045','#1c2f5e','#284178','#365591','#4a70ab','#6493c6','#86b6dd'];
```
Draw each band as a 8px tall rect from y=0 to 64.

Actually the stands start at y=64. Let's make the sky 0..80 with bands.

Hmm, let's plan the vertical layout more concretely:

- 0..70: sky
- 70..78: stadium roof edge
- 78..170: stands (crowd)
- 170..184: wall / advertising
- 184..196: grass verge
- 196..270: track

Hmm, that gives the track 74px. groundY=214.

Hmm, the athlete at groundY=214 with a height of ~26 → head at 188. That's above the track into the verge. Fine.

Wait, but the athlete's feet at 214 and the track top at 196 — the athlete is drawn in front of the track. Good.

Actually, let me reconsider: maybe make groundY = 210 and the track from 190 to 270.

Let me finalize:
- SKY: 0..72
- ROOF: 64..74
- STANDS: 74..168
- WALL: 168..182
- VERGE: 182..194
- TRACK: 194..270
- GROUND_Y = 212

Athlete height 26 → head at 186. That overlaps the verge and the wall a bit. Fine, it's in front.

Hmm, when the athlete jumps 42px up, the head goes to 144, which is in the stands area. Fine, drawn in front.

OK.

#### Stands / crowd tile

Pre-render a canvas of width 480, height 94 (74..168) — actually let's make the tile 480 wide and 100 tall covering y 68..168.

Content:
- Roof: a dark band at the top with a lighter edge.
- Tiers: 4 tiers of seating, each ~20px tall, separated by darker walkways.
- People: 4px wide, 7px tall, random colors, in rows.

Let me generate:
```js
const crowdTile = document.createElement('canvas');
crowdTile.width = 480; crowdTile.height = 100;
const ct = crowdTile.getContext('2d');
```

Draw:
- Fill the background with a dark color (#232838).
- For each tier (y from 0 to 100 step 22): draw a tier background (#3a4258), a darker walkway line.
- For each row within the tier (2 rows of people per tier, spaced 8px), draw people.

Person: 4 wide, 6 tall: head (3x2), body (4x3). Colors from a palette.

Also, some people have their arms up (waving). I'll handle the waving separately, but let's also bake in a static crowd.

Deterministic RNG:
```js
function hash(i){ let x = Math.sin(i*127.1)*43758.5453; return x - Math.floor(x); }
```

Let's write the crowd generation:
```js
const crowdColors = ['#e8d0b0','#c8a888','#8a6a4a','#e05050','#5080e0','#50c060','#e0c040','#d060c0','#f0f0f0','#40c0d0','#e08030'];
```
Head color: skin tones.

Let's draw:
for each person at (px, py):
  - body: fillRect(px, py+2, 4, 4) with a random color
  - head: fillRect(px+1, py, 2, 2) with a skin color

Hmm, 4 wide 6 tall people. Rows spaced 7px, columns spaced 5px → 96 columns × 14 rows = 1344 people. Each 2 fillRects = 2688 ops, once. Fine.

Add some shadow between rows.

Also add aisles (vertical dark lines every ~64px).

Also add a barrier/railing at the front of the stands.

OK.

Then draw: `ctx.drawImage(crowdTile, -offset, 68)` and again at -offset+480.

Where offset = (camX*0.12) % 480. Hmm, if camX can be negative, use a proper modulo.

Let's define `wrap(v, m) = ((v % m) + m) % m`.

offset = wrap(camX*0.12, 480). Then draw at x = -offset and x = -offset + 480. That covers the screen.

#### Wavers

Generate a list of waver positions in tile space: pick every 13th person or so. Let's generate a separate list of ~30 positions with their row y.

For each waver: draw the body (from the tile, already drawn), and draw arms up that wave. Since the tile is already drawn, we just draw the arms on top:
- left arm: from (px+0, py+2) to (px-1, py-2+wave) 
- right arm: from (px+4, py+2) to (px+5, py-2-wave)

where wave = sin(time*4 + phase)*2.

Just 1-2 px lines. Simple.

Let's draw them as small rects:
```js
const w = Math.round(Math.sin(t*5 + ph)*1.5);
ct2.fillStyle = armColor;
fillRect(px-1, py+1 - (2+w), 1, 3+w);  // hmm
```

Let's simplify: arms are 1px wide, 3px tall, at the sides, moving up and down by 1px.

Good enough at this scale.

#### Flags

Draw 3-5 flags on poles rising above the roof. Poles at fixed screen positions (or with parallax). Let's put them with parallax 0.12 too, at tile positions.

Flag drawing: a pole 1px wide, 20px tall; the flag is a 12x8 rectangle drawn as 12 vertical 1px columns, each offset vertically by sin(x*0.6 + t*6)*1.5.

Colors: alternate red/white/blue or country-ish.

#### Wall / ads

A band with colored panels and text. Let's draw panels of alternating colors with small white text like "TRACK", "FIELD", "GO!", "JUMP", "1983". Actually text would be too small. Just colored panels with a stripe.

Let's make: y 168..182. A dark base, with panels 40px wide, alternating colors (#c03030, #f0f0f0, #3060c0, #f0c030), each with a 2px dark border. Scroll with the world (parallax 1.0? or 0.6). Let's use parallax 0.8 so it feels attached to the track but slightly behind.

Hmm, actually the wall is at the far side of the track, so it should scroll at the same rate as the track (parallax 1.0). But then it moves fast. That's correct for a side view.

Hmm, but then the stands behind at 0.12 parallax would look weird (they'd be static while the wall scrolls fast). That's actually how parallax works and looks fine.

Let's use parallax 0.9 for the wall/ads.

#### Verge (grass)

A green band 182..194, parallax 1.0. With some texture (darker green dashes).

#### Track

194..270, red/orange. 
- The runway: a lane from the far side. Let's draw the whole track as the base color, then the runway lane as a slightly different shade with white lane lines at y=200 and y=228? Hmm.

Simplify: 
- Fill 194..270 with #b04a30 (track).
- Draw a horizontal white line at y=198 (the far edge of the runway).
- Draw a horizontal white line at y=232 (the near edge of the runway).
- So the runway is 198..232, and the athlete's feet at 212 are in the middle. 

Hmm, but then the athlete is running "in the middle of the lane" vertically, which looks like a top-down view. In a side view, the feet should be at the bottom edge of the lane. 

Ugh. Let's think about it differently: this is a side view where the ground plane is compressed. The athlete's feet are at y=212, and the ground extends from 194 (far) to 270 (near). The athlete's feet at 212 means they're standing at a point 18px from the far edge.

That's fine — it's the standard "2.5D" look.

Actually, let me just place GROUND_Y = 218 and the track from 194 to 270. Then the runway strip (lighter) from 206 to 232, with the athlete's feet at 218 in the middle. Fine.

Hmm, I keep going back and forth. Let's just commit:

GROUND_Y = 214.
Track: 194..270, base color #a8442c.
Runway lane: 202..238, color #c25038 (slightly lighter), with white lines at 202 and 238.
The athlete's feet at 214, in the upper-middle of the lane.

Sand pit: a rectangle from PIT_START to PIT_END, y from 202 to 240. Sand color #e8c87a with darker speckles.

The takeoff board: x from BOARD_X-BOARD_W to BOARD_X, y from 202 to 222 (a white board). With the front edge (at BOARD_X) marked in red.

Hmm, the board should be flush with the ground. Let's draw the board from y=204 to y=224 (20px tall) as a white rectangle with a red stripe on the right edge (the foul line).

Hmm, the foul line is the front edge = BOARD_X. And the athlete must take off before it.

OK, whatever — visually it'll read fine.

Measuring tape: draw along the pit at y=230..240, with tick marks and numbers. Hmm, that might collide with the sand. Let's draw the tape as a yellow strip from PIT_START to PIT_END at y=236..242, with black ticks every 18px and numbers.

Hmm, at y=236 it's below the athlete's feet (214). It's in the "foreground" part of the pit. Fine.

Actually, let me instead draw the metre markers as vertical lines in the sand across the pit height (202..240), with small numbers at the top. That reads better as a measuring tape.

Let's do: for m = 0..12: x = PIT_START + m*PPM. Draw a 1px vertical line from y=204 to y=238 in a slightly darker sand color, and a small number at y=206. Plus a thicker line at the world record distance (8.95m) in red, labeled "WR".

And also draw a tape strip at the bottom edge (238..244) with ticks. Hmm, maybe too busy. Let's just do the vertical lines + numbers, plus the WR line.

Actually the numbers might be hard to read at 5x7 in the sand. Let's use a scale-1 font with a dark color. It'll be 5x7 px. Readable enough.

OK.

#### Landing mark

When the athlete lands, draw:
- A dark oval/divot at (landingX, GROUND_Y).
- Two foot imprints.
- Sand particles.

Keep the mark for the rest of the attempt and the replay.

Let's store `G.mark = {x: landingX}` and draw it.

#### Athlete

```js
function drawAthlete(sx, sy, st)
```
where sx, sy are screen coords of the hip, st = {mode, phase, lean, jumpT, speed}.

Let me define the drawing:

```js
const SKIN='#f2c49b', HAIR='#2a1c10', TOP='#e33b3b', SHORT='#1c2a4a', SHOE='#ffffff', SHOE2='#e0e0e0';
```

Local coordinates: hip at (0,0), y down.

Torso: from hip to neck. Neck at (leanX, -11). Draw with a thick line of 5px, color TOP.
Head: a 5x5 blob at neck + (0,-4). Color SKIN, with hair on top and back.
Arms: from shoulder (neck + (0,1)) to hand.
Legs: thigh from hip to knee, shin from knee to foot.

Let me define a function `poseAngles(st)` returning:
{ thighA, kneeA, thighB, kneeB, armA, elbowA, armB, elbowB, torsoLean }

For mode 'run': use the run cycle formulas.
For mode 'fly': use the keyframe interpolation on jumpT.
For mode 'land': a landing crouch.

Let's implement.

```js
function runAngles(phase){
  const a = phase*Math.PI*2;
  const tA = 35*Math.sin(a);            // thigh A
  const kA = 60 - 60*Math.sin(a+0.9);   // knee bend A
  const tB = 35*Math.sin(a+Math.PI);
  const kB = 60 - 60*Math.sin(a+Math.PI+0.9);
  const arA = 45*Math.sin(a+Math.PI);   // arm A opposite to leg A
  const arB = 45*Math.sin(a);
  return {tA,kA,tB,kB,arA,arB};
}
```

Hmm, wait: for the legs, I need the foot to reach the ground. With thigh length 7 and shin length 7, hip at y=0, the foot should be at y=+14 when the leg is straight down. With thigh angle 35° and knee bend 13°, the foot would be at y = 7*cos(35°) + 7*cos(35-13°) = 5.73 + 6.49 = 12.2, and x = 7*sin(35) + 7*sin(22) = 4.01+2.62 = 6.6. So the foot is 12.2 below the hip, i.e., the hip is 12.2 above the ground. But the athlete's hip is drawn at GROUND_Y - HIP_H where HIP_H = 14 (leg length). Hmm, the foot would float.

Let's compute the hip height dynamically: hipY = GROUND_Y - maxFootDepth, where maxFootDepth is the lowest foot y in the pose. That way the feet touch the ground. That's a neat trick for procedural animation.

Actually, simpler: set HIP_H = 13 and accept slight float/clip. But with a run cycle, the legs are bent so the foot would be at y=12.2 max... The lowest point varies. Let's compute:

footY = 7*cos(t) + 7*cos(t - k) where t is the thigh angle and k the knee bend. We want the hip at GROUND_Y - min over legs of footY... no wait, we want the lowest foot to be at the ground: hipY = GROUND_Y - max(footY_A, footY_B). Then the other foot is above the ground. 

Hmm, but that makes the hip bob a lot. Actually, that's exactly the natural bob! Let's do it. hipY = GROUND_Y - maxFootY. And maxFootY varies between ~12 (bent) and ~14 (straight). So a 2px bob. 

But we should smooth it. Actually the natural bob happens twice per cycle, which is correct.

Hmm, but during the flight phase, the athlete's y is determined by physics. Let's only apply the ground-lock in 'run' mode.

Let's do: in run mode, compute the pose, find maxFootY, set hipY = GROUND_Y - maxFootY. In other modes, hipY = GROUND_Y - 13 + yOffset.

Hmm, for the flight, y is the physics height above ground. So hipY = GROUND_Y - 13 - jumpHeight. Let's use a constant 13.

OK, let's define thighLen=7, shinLen=7, so a straight leg is 14. Then hipY = GROUND_Y - 14 when standing. Let's set the base hip height to 14 and compute the bob.

Fine.

Now the torso: hip to neck, length 11, leaning. leanAngle in degrees (negative = forward lean, since forward is +x). neck = hip + rotate((0,-11), leanRad) where rotate by angle θ: (x cosθ - y sinθ, x sinθ + y cosθ). With lean θ = -15° (forward), point (0,-11) → (0*cos(-15) - (-11)*sin(-15), 0*sin(-15) + (-11)*cos(-15)) = (-11*0.259, -10.6) = (-2.85, -10.6). That leans backward! Because rotating (0,-11) by a negative angle moves it in -x. So for a forward lean (toward +x), I need a positive θ: (0,-11) rotated by +15° → (0*cos15 - (-11)*sin15, ...) = (11*0.259, -10.6) = (2.85, -10.6). Yes, positive θ leans forward.

So leanRad = +lean where lean in radians, positive = forward.

Head: at neck + (0, -3), drawn as a 6x6 blob.

Arms: shoulder at neck + (0, 1). Arm length 5 upper, 5 lower.
armAngle: measured from vertical down. For running, arms swing forward/back.
upperArm dir = (sin(aA), cos(aA)) — positive aA = forward (+x). elbow = shoulder + 5*(sin aA, cos aA).
forearm: angle aA - elbowBend (bend backward)... for arms, the elbow bends so the forearm goes forward/up. Hmm.

For running arms: the elbow is bent ~90°. The upper arm swings forward/back, the forearm points forward-up.

Let's define: upper arm angle from vertical-down: uA = 40*sin(φ) (forward positive). Forearm angle relative to the upper arm: bend backward by 70° (so the forearm points forward relative to the down direction). Hmm.

Let's think: upper arm pointing down-forward at 40°: dir = (sin40, cos40) = (0.64, 0.77). Elbow at shoulder + (3.2, 3.8). Forearm should point forward and up: dir ≈ (0.9, -0.4). 

If I define the forearm angle as uA + 110°: sin(150°)=0.5, cos(150°)=-0.87 → (0.5,-0.87), pointing forward and up steeply. Hmm, close.

Let's just use forearmAngle = uA + 100°. When uA = -40 (arm back), forearm angle = 60° → dir (0.87, 0.5) pointing forward-down. Hmm, that's wrong — when the arm is back, the forearm should still point forward-ish (elbow behind, hand at the hip).

Hmm. Actually in running, the elbow angle stays ~90° and the whole arm swings. When the upper arm is back (uA=-40°), the forearm points forward-down... no. Let's think: upper arm back means the elbow is behind the shoulder. The forearm then points forward and down (the hand is near the hip). So the forearm direction from the elbow ≈ forward and down. With uA=-40, forearm angle should be around +60° from vertical down → dir (sin60, cos60) = (0.87, 0.5). Forward and down. Yes! That's what uA+100 gives.

When the upper arm is forward (uA=+40), the elbow is in front of the shoulder, and the forearm points forward and up: dir (0.5, -0.87) → angle from vertical down = 150°. uA+110 = 150. Yes!

So forearm angle = uA + 105° works. 

So: elbowAngle = uA + 105°.

Good.

Legs: thigh angle tA from vertical down, positive = forward. knee at hip + thighLen*(sin tA, cos tA). Shin angle = tA - kA (knee bends backward, so the shin rotates backward relative to the thigh). Foot at knee + shinLen*(sin(tA-kA), cos(tA-kA)).

Wait: if the thigh is forward at tA=35° and the knee bends backward by kA=90°, the shin angle = 35-90 = -55°, so the shin points backward and down: dir (sin(-55), cos(-55)) = (-0.82, 0.57). So the foot is behind and below the knee. Yes, correct for a bent knee.

Good.

Foot: a small 4x2 rect at the foot position, oriented roughly horizontally, colored white (shoe).

OK.

Let's write drawAthlete:

```js
function drawAthlete(sx, sy, st){
  // sy = hip Y (screen), sx = hip X
  ...
}
```

Hmm, but I said hipY depends on the pose. Let me pass sy as the "ground reference" and compute internally.

Let me restructure: `drawAthlete(gx, gy, st)` where (gx, gy) is the ground contact point (feet on ground level) — no, during flight the athlete is in the air.

Let's pass the hip position directly and compute it outside:
- run mode: compute the pose first, find maxFootY, hipY = gy - maxFootY.
- other modes: hipY = gy - 13 - airHeight.

Let me write a function `computePose(st)` that returns all joint angles, then `drawAthlete` uses it.

Let me now write it concretely.

```js
function poseRun(phase){
  const a = phase * Math.PI * 2;
  const T = 35, K = 62;
  return {
    tA: T*Math.sin(a),
    kA: Math.max(0, K - K*Math.sin(a + 0.9)),
    tB: T*Math.sin(a + Math.PI),
    kB: Math.max(0, K - K*Math.sin(a + Math.PI + 0.9)),
    uA: 42*Math.sin(a + Math.PI),
    uB: 42*Math.sin(a),
    lean: 14 + 8*Math.sin(a*2)   // slight bob in lean
  };
}
```

Hmm, lean should be a constant-ish forward lean while running, more when accelerating. Let's use lean = 10 + speedFactor*12. And add a small oscillation.

Actually, let's compute lean from the speed: lean = 6 + 14*(speed/MAX). So at max speed, lean = 20°.

OK.

For flight:
```js
const FLY_KEYS = [
  {t:0.00, tA:-38, kA:25, tB:-25, kB:45, uA:-60, uB:-50, lean:-5},
  {t:0.20, tA:-5,  kA:95, tB:10,  kB:80, uA:-70, uB:-60, lean:0},
  {t:0.45, tA:45,  kA:105,tB:30,  kB:110,uA:-80, uB:-70, lean:5},
  {t:0.70, tA:62,  kA:35, tB:52,  kB:60, uA:-60, uB:-50, lean:10},
  {t:0.90, tA:55,  kA:8,  tB:48,  kB:15, uA:-20, uB:-10, lean:12},
  {t:1.00, tA:48,  kA:12, tB:42,  kB:20, uA:0,   uB:10,  lean:14},
];
```

Wait, uA/uB are arm angles where positive = forward. During flight, the arms go up/back at takeoff and then forward for balance. Let's just use negative (backward) for the arms during the flight. Actually at takeoff the arms swing up and forward. Hmm.

Let's do: at takeoff, the arms are up (uA = 150 means the upper arm points... wait, uA is the angle from vertical down. 180° = straight up. So an arm up = uA ≈ 160.

Hmm, my arm formula: dir = (sin(uA), cos(uA)). At uA=180: (0, -1) = straight up. At uA=0: (0,1) = straight down. At uA=90: (1,0) = straight forward.

So for the arms up, uA ≈ 150-170.

Let's redo the flight keyframes with the arms swinging up at takeoff and then down/forward:

t=0: arms up and forward: uA=140, uB=120 (both arms up)
t=0.3: arms coming down, uA=60, uB=40
t=0.6: arms forward/down uA=20, uB=0
t=1.0: arms forward for balance uA=40, uB=20

Hmm. Actually in a long jump, the arms swing up at takeoff and then the athlete "cycles" them. Let's keep it simple and readable.

And the legs: at takeoff, the takeoff leg is extended back, the free leg is forward. Then both tuck, then extend forward for landing.

Let me redo:

FLY keys:
```
t=0.00: tA=-45, kA=15, tB=20, kB=60, uA=140, uB=120, lean=5
t=0.15: tA=-20, kA=70, tB=45, kB=95, uA=120, uB=100, lean=8
t=0.40: tA=50,  kA=110,tB=35, kB=120,uA=70,  uB=50,  lean=10
t=0.65: tA=70,  kA=45, tB=58, kB=55, uA=30,  uB=10,  lean=12
t=0.85: tA=62,  kA=10, tB=55, kB=12, uA=10,  uB=-10, lean=14
t=1.00: tA=55,  kA=5,  tB=50, kB=8,  uA=20,  uB=0,   lean=16
```

Hmm, at t=1 (landing) the legs should be extended forward, feet ahead of the hips, ready to land in the sand. tA=55, kA=5 → the leg points forward-down at 55°, nearly straight. Good.

Actually, for landing, the feet should be ahead and slightly below. With tA=55°, the foot is at (7*sin55 + 7*sin50, 7*cos55 + 7*cos50) = (5.73+5.36, 4.01+4.5) = (11.1, 8.5). So the feet are 11px ahead and 8.5 below the hip. Good.

Then on landing, we transition to a crouch.

Landing pose (mode 'land', with t from 0 to 1):
- Absorb: knees bend, hips drop, arms forward.

Let's do:
```
t=0: tA=55,kA=5,tB=50,kB=8, uA=20,uB=0, lean=16
t=0.4: tA=70,kA=70,tB=65,kB=75, uA=60,uB=40, lean=25
t=1: tA=50,kA=90,tB=45,kB=95, uA=80,uB=60, lean=30  (crouch, standing up)
```

Hmm, whatever, a simple crouch.

Actually after landing the athlete should decelerate and stand up. Let's keep it short.

OK, and I need to interpolate between the keyframes.

```js
function lerpKeys(keys, t){
  let i = 0;
  while(i < keys.length-1 && t > keys[i+1].t) i++;
  const a = keys[i], b = keys[Math.min(i+1, keys.length-1)];
  const span = b.t - a.t;
  const f = span > 0 ? (t - a.t)/span : 0;
  const out = {};
  for(const k in a) if(k !== 't') out[k] = a[k] + (b[k]-a[k])*f;
  return out;
}
```

Good.

#### Drawing the athlete in detail

```js
function drawAthlete(hipX, hipY, p, colors){
  // p = pose with angles in degrees
  const rad = Math.PI/180;
  const thigh=7, shin=7, upper=5, fore=5;
  const lean = p.lean*rad;
  
  // hip
  const hx = hipX, hy = hipY;
  
  // neck
  const nx = hx + Math.sin(lean)*11;
  const ny = hy - Math.cos(lean)*11;
  
  // legs (draw back leg first)
  ...
}
```

Order: draw the far arm and far leg first (darker), then the torso, then the near leg and near arm.

Far side color = darkened versions.

Let's define:
```js
const COL = {
  skin:'#f0c090', skinD:'#c99a6a',
  top:'#e04040', topD:'#a82c2c',
  short:'#20304f', shortD:'#16223a',
  shoe:'#f8f8f8', shoeD:'#c0c0c0',
  hair:'#2a1e14'
};
```

Draw order:
1. Far leg (A): thigh, shin, shoe in dark colors
2. Far arm (B): dark
3. Torso (top color)
4. Head + hair
5. Near leg (B): normal
6. Near arm (A): normal

Hmm, "far" vs "near" — in a side view facing right, the far limbs are drawn behind. Let's say leg A is the far leg, leg B is the near leg. Same for arms.

OK.

Leg drawing:
```js
function drawLeg(hx,hy, tA, kA, cols){
  const rad = Math.PI/180;
  const kx = hx + Math.sin(tA*rad)*7;
  const ky = hy + Math.cos(tA*rad)*7;
  const fx = kx + Math.sin((tA-kA)*rad)*7;
  const fy = ky + Math.cos((tA-kA)*rad)*7;
  limb(hx,hy,kx,ky,4,cols.thigh);
  limb(kx,ky,fx,fy,3,cols.shin);
  // shoe
  ctx.fillStyle = cols.shoe;
  ctx.fillRect(Math.round(fx)-2, Math.round(fy)-1, 5, 3);
}
```

Hmm, the shoe should be oriented with the foot. For simplicity, always draw a horizontal 5x3 shoe. Good enough.

Arm:
```js
function drawArm(nx,ny, uA, cols){
  const rad=Math.PI/180;
  const ex = nx + Math.sin(uA*rad)*5;
  const ey = ny + Math.cos(uA*rad)*5;
  const fa = uA + 105;
  const hx2 = ex + Math.sin(fa*rad)*5;
  const hy2 = ey + Math.cos(fa*rad)*5;
  limb(nx,ny,ex,ey,3,cols.arm);
  limb(ex,ey,hx2,hy2,2,cols.arm);
  // hand
  ctx.fillStyle=cols.hand; ctx.fillRect(Math.round(hx2)-1, Math.round(hy2)-1,2,2);
}
```

Torso:
```js
limb(hx,hy,nx,ny,6,COL.top);
```
Thickness 6 might be too thick; let's use 5.

Head:
```js
const hdx = nx + Math.sin(lean)*3;
const hdy = ny - Math.cos(lean)*3;
ctx.fillStyle=COL.skin;
ctx.fillRect(hdx-2, hdy-3, 5, 5);  // head blob
ctx.fillStyle=COL.hair;
// hair on top and back
ctx.fillRect(hdx-3, hdy-4, 6, 3);
```

Hmm, need to handle the lean for the head. Let's just place the head above the neck with a slight offset.

Let me simplify: head center = neck + (sin(lean)*3, -cos(lean)*3). Draw a 5x5 skin rect centered there, plus a hair rect on top.

Alright.

Also add a ponytail or something? No.

#### Sand particles

```js
particles = [{x,y,vx,vy,life,color,size}]
```
Update: vy += 400*dt (gravity in px/s²), x += vx*dt, y += vy*dt. Life decreases.

Draw as 1-2px rects in sand colors.

#### Landing mark

Draw an elongated dark shape at the landing x: a 6x3 dark sand rect, plus two foot imprints.

#### Measuring tape lines

Drawn as part of the pit.

### HUD details

Top panel: 
- Background: rgba(10,14,30,0.85) from y=0 to y=22.
- "SPEED" at x=6, y=4 (scale 1)
- Speed bar: x=44, y=5, w=150, h=10. Border white, fill gradient from green to yellow to red based on the speed.
- "ATT" + attempt at x=210
- "BEST" + best at x=280
- "WR 8.95" at x=390? Hmm, 480 wide. Let's lay out:
  - x=6: "SPEED"
  - x=44..194: bar
  - x=204: "ATT 1/3"  (7 chars * 6 = 42px) → 204..246
  - x=256: "LAST 7.4"  → 256..304
  - x=316: "BEST 8.1"  → 316..364
  - x=376: "WR 8.95" → 376..418
  
  Hmm, "LAST" during the run is the previous attempt's distance. OK.

Bottom panel (y=250..270):
- Angle gauge: a horizontal bar x=6..186, y=254..264. Marker at the angle position. Ticks at 20,45,70.
- Text "ANGLE 45" at x=196.
- Hint text at x=300: "LEFT/RIGHT = RUN   SPACE = JUMP" — too long. Let's do "P = DEMO" at the right.

Hmm, the bottom panel would cover part of the track. That's fine (it's the foreground).

Actually, maybe put the angle gauge right above the athlete? No, the bottom panel is fine.

Let's make the bottom panel semi-transparent dark.

Hmm, but then the track foreground is covered. That's fine.

Actually, let me make the bottom panel shorter: y=252..270 (18px).

OK.

### Overlays

- Big center text for "FOUL!", the distance result, "REPLAY", etc.

Let me use a scale-3 font for the big text.

### Let me now think about the frame loop.

```js
let last = performance.now();
function frame(now){
  let dt = (now-last)/1000; last = now;
  dt = Math.min(dt, 0.05);
  update(dt);
  render();
  requestAnimationFrame(frame);
}
```

### update(dt)

```js
function update(dt){
  G.time += dt;
  switch(G.state){
    case 'ready': ...
    case 'run': updateRun(dt); break;
    case 'fly': updateFly(dt); break;
    case 'land': updateLand(dt); break;
    case 'result': ...
    case 'replay': updateReplay(dt); break;
    case 'over': ...
  }
  updateParticles(dt);
  updateCamera(dt);
  // record
}
```

Let me write each.

**ready**: show "GO!" for 0.8s, then state='run'. Actually, let's start with the athlete at x=0, speed=0, and show "GO!" briefly.

Hmm, but during 'ready' the player can't press. Let's make it short (0.6s).

**run**:
```js
G.speed = Math.max(0, G.speed - G.speed*0.85*dt);
G.x += G.speed * dt * PPM;
G.angleT += dt;
G.angle = 45 + 25*Math.sin(G.angleT*2*Math.PI/ANGLE_PERIOD);
// autoplay
// check if past the board → auto-foul (run into the pit without jumping)
if(G.x > BOARD_X + 20) { doJump(true); } // forced foul? 
```

Hmm, if the player never jumps, they run past the board. Let's make it so that if x > PIT_START + 5, it's an automatic foul with a 0 distance and we go to the result.

Actually simpler: if x > BOARD_X, the athlete has crossed the foul line → immediately trigger a foul jump (they stumble). Let's set state='result' with foul=true, dist=0. But we want the animation... Let's just trigger doJump() with foul=true when x > BOARD_X + 2. The jump will happen but the distance is 0.

Hmm, cleaner: when x > BOARD_X, force a jump (foul). Then the flight happens, they land in the sand, and the result shows FOUL.

OK.

**fly**:
```js
G.flyT += dt;
G.vy -= G.g*dt;
G.x += G.vx*dt*PPM;
G.h += G.vy*dt*PPM;   // h in pixels, y-up
if(G.h <= 0){ G.h = 0; land(); }
```
where vx, vy are in m/s and h is in pixels. Hmm, mixing units. Let me store the height in metres and convert when drawing.

Let's do:
```js
G.vx (m/s), G.vy (m/s), G.hm (metres)
G.x += G.vx*dt*PPM;
G.hm += G.vy*dt;
G.vy -= G.g*dt;
if(G.hm <= 0) land();
```
And the screen y = GROUND_Y - 14 - G.hm*PPM.

Hmm, 1 metre = 18 px, so a 2.3m jump = 41px. Good.

Wait, but the physics: vx and vy in m/s, g in m/s². Time to land: t = 2*vy/g. With vy=8.3, g=15 → 1.11s. Distance = vx*t = 8.3*1.11 = 9.2m. Good.

**land**: 
- Compute the distance.
- Spawn particles.
- Set the mark.
- After 0.5s → state='result'.

Actually, let's do the landing animation: the athlete sinks into the sand (the hip drops), the particles fly. Then after ~1s, show the result.

Let's have 'land' last 1.2s and then go to 'result'.

**result**: show the distance for 2.5s, then start the replay.

**replay**: play back the frames at 0.35x speed. When done, wait 0.5s, then advance to the next attempt or the results screen.

Hmm, that's a lot of waiting. Total per attempt: run ~5s + fly 1.1s + land 1.2 + result 2.5 + replay (7s of footage at 0.35x = 20s!). Way too long.

Let's limit the replay to the last 1.2s of the run + the flight + landing = ~2.5s of footage. At 0.4x speed that's 6.25s. Hmm, still long.

Let's do: replay footage = from 0.8s before takeoff to landing (about 2s), played at 0.5x → 4s. Acceptable.

Total per attempt: 5 + 1.1 + 1.2 + 2.5 + 4 + 0.5 = 14.3s. Three attempts = 43s. Hmm, that exceeds the 30s window. But "may loop or continue after that" — the requirement is that everything important is shown within 30s. So the first attempt should show everything: run, jump, land, replay. That's ~14s. Then the second and third attempts continue.

Actually, maybe speed things up: result display 1.8s, land 0.8s, replay 3.5s. First attempt: 5+1.1+0.8+1.8+3.5 = 12.2s. Good — within 30s we'd see the first attempt and most of the second. 

Hmm, but in autoplay mode the run is faster (max speed), so ~4s.

OK.

**over** (results screen): show the table for 5s, then reset to attempt 0.

### Recording for replay

```js
G.rec = [];  // array of frames
```
Push every frame during run/fly/land: {x, h, phase, mode, pose, speed, angle, lean, camX}.

Actually, store the pose object? That's a lot of allocation. Let's store the minimal data: {x, h, phase, mode, flyT, landT, lean, speed}.

Then during the replay, recompute the pose from these.

Hmm, the pose computation needs the mode and phase/flyT. Let's just store those.

Actually, let's store the computed pose values directly (tA,kA,tB,kB,uA,uB,lean) — 8 numbers. That avoids recomputation. Fine.

Let's store: {x, h, pose:{...}, mode}. Plus the camera.

Actually simpler: store {x, h, tA,kA,tB,kB,uA,uB,lean, mode}.

I'll store an object with these fields. ~600 frames * 10 fields. Fine.

Also, I want to cap the recording length: keep only the last 400 frames (about 6.7s). Use a ring buffer or just shift.

Let's keep an array and if length > 600, splice off the front. Splicing is O(n) but only occasionally... actually every frame. Let's use a simple approach: keep the array and slice when needed.

Actually, let's record into an array and cap it by removing chunks: if (rec.length > 600) rec.splice(0, 60). That's cheap.

### Replay extraction

On landing, take the frames from (takeoffIndex - 45) to the end. We need the takeoff index. Let's record `G.takeoffRecIndex = G.rec.length` at takeoff. Then the replay starts at max(0, takeoffRecIndex - 40).

Then during the replay, we play those frames at 0.5x speed: frameIndex advances by 0.5 per frame... i.e., replayT += dt*0.5*60 frames.

Hmm, let's store the replay as a sub-array: `G.replayFrames = G.rec.slice(start)`.

Then `G.replayIdx` advances by `dt * 60 * 0.5`.

When replayIdx >= replayFrames.length → done.

Good.

### Camera

```js
function updateCamera(dt){
  const targetX = clamp(G.x - 140, -120, 520);
  G.camX += (targetX - G.camX) * Math.min(1, dt*8);
}
```

Hmm, for the replay, we should use the recorded x. Let's just set G.x during the replay from the recorded frame, and the camera follows.

### Render

```js
function render(){
  drawSky();
  drawStands();
  drawFlags();
  drawWall();
  drawVerge();
  drawTrack();   // includes runway, board, pit, tape, marks
  drawAthleteWorld();
  drawParticles();
  drawHUD();
  drawOverlays();
}
```

Let's write these.

**drawSky**: bands + sun + clouds.

Clouds: an array of {x, y, w, h, speed}. They drift; the x wraps.

```js
const clouds = [];
for(let i=0;i<7;i++) clouds.push({x: Math.random()*600, y: 6+Math.random()*40, w: 20+Math.random()*30, h: 5+Math.random()*4, s: 3+Math.random()*5});
```
Cloud drawing: a few overlapping rounded rects in white/#dceaf5.

Hmm, deterministic would be better for consistency, but random is fine.

**drawStands**: 
```js
const off = wrap(G.camX*0.12, 480);
ctx.drawImage(crowdTile, -off, 68);
ctx.drawImage(crowdTile, -off+480, 68);
```
Plus the wavers.

Wait, crowdTile is 480x100 covering y=68..168.

Also draw the roof at the top: y=64..72.

Hmm, let me just include the roof in the tile. Tile height 100 → y 68..168. Roof at the top of the tile (68..76).

Actually, let me make the tile cover y=60..168 (108 tall) and include the roof.

Let's set: crowdTile height = 108, drawn at y=60.

Roof: 60..70. Stands: 70..168.

OK.

**drawFlags**: draw poles rising from the roof at y=60 up to y=30. With parallax 0.12.

Let's place flags at tile x positions [40, 160, 300, 420] and draw them per tile copy. Hmm, that would be 8 flags. Fine.

Actually let's put the flags only on the first copy... no, they'd disappear. Let's do per-copy.

Hmm, 4 flags per 480px tile. Let's use 2 per tile at x=100 and x=340.

**drawWall**: parallax 0.85. 
```js
const off = wrap(G.camX*0.85, 60);
for(let i=-1;i<10;i++){
  const x = i*60 - off;
  ...draw panel...
}
```

Panels 60 wide, alternating colors. y=168..182.

Hmm, we need the ads to look continuous. Use a base dark strip and colored panels.

**drawVerge**: green band 182..194, parallax 1.0. Fill with green, add darker tufts at world positions.

**drawTrack**: 
- Fill 194..270 with the base track color.
- Draw the runway lane 202..238 lighter.
- Lane lines at 202 and 238 (white, 1px).
- Then the board and pit.

All at parallax 1.0, so screen x = worldX - camX.

Let's write:
```js
const ox = -G.camX; // world to screen offset
```

Board: rect from BOARD_X-BOARD_W to BOARD_X, y 204..240? Let's make the board a vertical strip: x from BOARD_X-22 to BOARD_X, y from 202 to 240. White with a red edge on the right.

Hmm, the board is the takeoff board. In the real long jump, the board is flush with the runway, 20cm wide. Visually, I'll draw a white/light strip.

Let's draw: rect(BOARD_X-20, 200, 20, 42) filled with '#e8e8e8', then a 3px red strip at x=BOARD_X-3.

Hmm, actually the foul line is at BOARD_X (the front edge). Let's draw a red line at x=BOARD_X-2, width 2.

Pit: rect(PIT_START, 200, PIT_END-PIT_START, 44) filled with sand.

Hmm, the pit starts at BOARD_X (right after the board). Good.

Sand texture: pre-generate speckles deterministically.

Let me pre-render the pit into an offscreen canvas? The pit is 216px wide. Let's just draw it procedurally each frame with a cached speckle list.

Actually, let's pre-render the pit background (sand + speckles + metre lines + numbers) into an offscreen canvas of 216x44 once, and blit it. Then draw the WR line and the landing marks on top.

That's efficient. 

Let's create `pitCanvas` of width PIT_END-PIT_START = 216, height 44, representing y=200..244.

Content:
- Fill with #e8c87a.
- Add speckles: random darker/lighter 1-2px dots.
- Metre lines: for m=1..11: x = m*PPM, a 1px vertical line from y=4 to y=44 in rgba(160,130,80,0.5).
- Numbers: small dark text at y=6.

Hmm, the numbers might be cluttered. Let's only draw numbers every 2m? Or draw them small. Let's draw them at every metre, 5x7 font, in a brownish color at y=8. 11 numbers over 216px = every 18px, and each number is 5px wide. Fits.

Actually, the numbers should represent the distance from the board. At x = m*PPM, the number is m. Good.

- The tape strip at the bottom: y=36..44, a yellow band with black ticks every 18px.

OK, let's build the pit canvas.

Also, draw the front edge of the pit (a wooden border) — a 2px dark line at the left and right edges? Nah.

**Landing mark**: draw after the pit. If G.mark exists, draw at screen x = G.mark.x - camX:
- A dark sand splat: fillRect(x-4, 202, 9, 3) in #b08a4a, plus a lighter area.
- Foot imprints: two 4x2 rects.

Hmm, let's draw the mark at the landing x with a slight spread.

Also draw a vertical dashed line from the board to the landing mark showing the measured distance? That'd be a nice touch. Maybe during the result.

Let's do: during the result, draw a horizontal measuring line from BOARD_X to the landing x at y=248, with arrows and the distance label. Nice.

**Athlete**: 
```js
const sx = G.x - G.camX;
const sy = GROUND_Y;
```

For run mode: compute the pose, find the max foot y, hipY = sy - maxFootY.

Hmm, but I need the foot y from the pose. Let me write a helper that computes the foot positions from the pose.

```js
function footY(t, k){ return 7*Math.cos(t*RAD) + 7*Math.cos((t-k)*RAD); }
```

Then maxFootY = max(footY(tA,kA), footY(tB,kB)), clamped to at least 10.

hipY = sy - maxFootY.

Hmm, but during the run the hip would bob between 12 and 14 px above the ground. That's a 2px bob. Good.

Actually, I realize the athlete also should be at a consistent height. Let's just do it.

For flight/land: hipY = sy - 13 - hm*PPM (flight) or sy - 13 + sink (land).

Hmm, in the land state, the athlete's feet are on the ground and they crouch. Let's compute the foot y from the landing pose similarly: hipY = sy - maxFootY.

OK, so for run and land, use the ground-lock. For flight, use the physics height.

Good.

**Particles**: sand puffs.

### HUD

Let's write drawHUD() with the speed bar and angle gauge.

### Overlays

Big text in the center.

Let me now also handle the "results screen".

```js
function drawResults(){
  // dark overlay
  ctx.fillStyle='rgba(6,10,24,0.88)';
  ctx.fillRect(40, 50, 400, 170);
  // border
  drawText('RESULTS', ...);
  for each attempt: draw "ATTEMPT 1   7.4 M   FOUL"
  draw "BEST 8.12 M"
  draw "WORLD RECORD 8.95 M"
  if new record: "NEW WORLD RECORD!"
}
```

### Autoplay toggle

Press P → G.autoplay = !G.autoplay. Show an indicator in the HUD.

When autoplay is on, the AI controls everything. When toggled off mid-run, the player takes over.

Let's also make the game start in autoplay? No — the requirement says "toggled with the P key". So default off. But then a viewer watching the recording would need to press P... The recording is of the page as-is. Hmm, "Also include an autoplay demo mode toggled with the P key, in which the game plays itself competently (an AI controls the player) so a viewer can watch a good run."

Hmm, if the recording starts with autoplay off, the athlete won't run (no input). That'd be a boring recording. 

I think the safest interpretation: default autoplay OFF, but... the recording would show nothing. Hmm.

Maybe: start with autoplay ON by default so the demo looks good, and P toggles it off. But the requirement says "toggled with the P key, in which the game plays itself". 

I'll default autoplay to ON (demo mode) and let P toggle it off — that way the recording shows a good run immediately. Hmm, but then a human player would be confused.

Compromise: start with autoplay ON, and show a clear indicator "DEMO (P)". The moment the player presses any run key, autoplay turns off. That's the best of both. And P re-enables it.

Yes! Let's do that: autoplay starts true; any run/jump key press disables autoplay automatically. P toggles.

That guarantees the recording shows a great run.

### Let's now write all the code.

I'll be careful with details.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TRACK &amp; FIELD — LONG JUMP</title>
<style>
  html,body{margin:0;padding:0;background:#05060a;height:100%;overflow:hidden;}
  body{display:flex;align-items:center;justify-content:center;}
  canvas{image-rendering:pixelated;image-rendering:crisp-edges;display:block;}
</style>
</head>
<body>
<canvas id="c"></canvas>
<script>
...
</script>
</body>
</html>
```

Now the JS.

Let me write it step by step.

```js
const W=480, H=270;
const cv = document.getElementById('c');
cv.width=W; cv.height=H;
const ctx = cv.getContext('2d');
ctx.imageSmoothingEnabled = false;

function resize(){
  const s = Math.max(1, Math.min(Math.floor(innerWidth/W), Math.floor(innerHeight/H)));
  cv.style.width = (W*s)+'px';
  cv.style.height = (H*s)+'px';
}
addEventListener('resize', resize); resize();
```

Hmm, if the window is smaller than 480x270, s=1 and the canvas overflows. Let's allow fractional scaling down: if the window is small, use min(innerWidth/W, innerHeight/H) without flooring. Let's do:
```js
let s = Math.min(innerWidth/W, innerHeight/H);
s = s >= 1 ? Math.floor(s) : s;
```
Good.

### Font

```js
const FONT_DATA = {
'A':"01110,10001,10001,11111,10001,10001,10001",
...
};
```

I'll write it as an object with comma-separated rows.

Let me write a function to parse.

```js
const GLYPHS = {};
for(const ch in FONT_DATA){
  GLYPHS[ch] = FONT_DATA[ch].split(',').map(r=>r.split('').map(Number));
}
```

drawText:
```js
function drawText(str, x, y, color, sc){
  sc = sc||1;
  ctx.fillStyle = color;
  let cx = x;
  str = String(str).toUpperCase();
  for(let i=0;i<str.length;i++){
    const g = GLYPHS[str[i]];
    if(g){
      for(let r=0;r<7;r++){
        const row = g[r];
        let runStart=-1;
        for(let c=0;c<5;c++){
          if(row[c]){ if(runStart<0) runStart=c; }
          else { if(runStart>=0){ ctx.fillRect(cx+runStart*sc, y+r*sc, (c-runStart)*sc, sc); runStart=-1; } }
        }
        if(runStart>=0) ctx.fillRect(cx+runStart*sc, y+r*sc, (5-runStart)*sc, sc);
      }
    }
    cx += 6*sc;
  }
}
```

Using run-length encoding to reduce fillRect calls. 

Also a `textWidth(str, sc)` helper = str.length*6*sc - sc.

### Now the main code.

Let me write out the full thing.

```js
// ---------- constants ----------
const PPM = 18;
const RUNWAY_M = 38;
const BOARD_X = RUNWAY_M * PPM;      // 684 - front edge of board (foul line)
const BOARD_W = 22;
const PIT_START = BOARD_X;
const PIT_LEN = 12*PPM;              // 216
const PIT_END = PIT_START + PIT_LEN; // 900
const GROUND_Y = 214;
const MAX_SPEED = 11.8;
const PRESS_GAIN = 0.85;
const SPEED_DECAY = 0.85;
const GRAV = 15;
const ANGLE_PERIOD = 1.15;
const WR = 8.95;
```

Wait, I need to double check the distance. With MAX_SPEED=11.8 and 45°: d = 11.8²/15 = 9.28m. The landing x = 684 + 9.28*18 = 851. PIT_END = 900. Good.

But the athlete takes off from x slightly before BOARD_X (to avoid a foul), so the actual distance is less. And the athlete's x is the hip; the measured distance is from BOARD_X to the landing hip x.

Fine.

Now the game state:

```js
const G = {
  state:'ready',
  t:0,
  time:0,
  attempt:0,        // 0-based, 0..2
  results:[],       // per attempt: {dist, foul}
  best:0,
  last:0,
  speed:0,
  x:0, hm:0,
  vx:0, vy:0,
  phase:0,
  angle:45,
  angleT:0,
  lean:0,
  jumpAngle:0,
  takeoffX:0,
  foul:false,
  camX:-120,
  mark:null,
  particles:[],
  rec:[],
  replayFrames:null,
  replayIdx:0,
  autoplay:true,
  aiSide:'L',
  aiTimer:0,
  lastSide:null,
  shakeT:0,
  msg:'',
};
```

### reset attempt

```js
function startAttempt(){
  G.state='ready'; G.t=0;
  G.speed=0; G.x=0; G.hm=0; G.vx=0; G.vy=0;
  G.phase=0; G.angle=45; G.angleT=0;
  G.foul=false; G.mark=null; G.particles.length=0;
  G.rec.length=0;
  G.lastSide=null;
  G.camX = -120;
  G.aiTimer=0; G.aiSide='L';
  G.dist=0;
}
```

### The pose computation

```js
const RAD = Math.PI/180;
function poseRun(phase, speedFrac){
  const a = phase*Math.PI*2;
  const T=36, K=62;
  const tA = T*Math.sin(a);
  const kA = Math.max(0, K - K*Math.sin(a+0.9));
  const tB = T*Math.sin(a+Math.PI);
  const kB = Math.max(0, K - K*Math.sin(a+Math.PI+0.9));
  const uA = 44*Math.sin(a+Math.PI);
  const uB = 44*Math.sin(a);
  const lean = 8 + 14*speedFrac + 3*Math.sin(a*2);
  return {tA,kA,tB,kB,uA,uB,lean};
}
```

Hmm, the arms: uA is the angle from vertical down, positive = forward. When the left leg is forward (tA>0), the right arm should be forward. tA = T sin(a), so when sin(a)>0, leg A is forward. Arm B should be forward: uB = 44 sin(a) → yes, matches. And arm A: uA = 44 sin(a+π) = -44 sin(a) → backward. Correct.

But wait, I need to double check the arm formula direction. dir = (sin(u), cos(u)). At u=44°, dir = (0.69, 0.72) → forward and down. Good.

### Flight pose

```js
const FLY_KEYS = [
  {t:0.00, tA:-45, kA:18, tB:22,  kB:55, uA:145, uB:120, lean:6},
  {t:0.16, tA:-18, kA:72, tB:48,  kB:98, uA:120, uB:100, lean:9},
  {t:0.40, tA:48,  kA:112,tB:34,  kB:122,uA:72,  uB:52,  lean:11},
  {t:0.65, tA:70,  kA:48, tB:58,  kB:58, uA:34,  uB:14,  lean:13},
  {t:0.85, tA:63,  kA:12, tB:56,  kB:14, uA:12,  uB:-8,  lean:15},
  {t:1.00, tA:56,  kA:6,  tB:52,  kB:10, uA:22,  uB:2,   lean:17},
];
```

### Land pose

```js
const LAND_KEYS = [
  {t:0.00, tA:56, kA:6,  tB:52, kB:10, uA:22, uB:2,  lean:17},
  {t:0.35, tA:68, kA:62, tB:64, kB:66, uA:58, uB:38, lean:26},
  {t:1.00, tA:52, kA:88, tB:48, kB:92, uA:78, uB:58, lean:32},
];
```

### Interpolation

```js
function lerpPose(keys, t){
  t = Math.max(0, Math.min(1, t));
  let i=0;
  while(i<keys.length-1 && t>keys[i+1].t) i++;
  const a=keys[i], b=keys[Math.min(i+1,keys.length-1)];
  const span = b.t-a.t;
  const f = span>0 ? (t-a.t)/span : 0;
  const o={};
  for(const k in a) if(k!=='t') o[k] = a[k]+(b[k]-a[k])*f;
  return o;
}
```

### Drawing the athlete

```js
function drawAthlete(px, groundY, p, mode){
  // compute foot depths
  const fyA = 7*Math.cos(p.tA*RAD) + 7*Math.cos((p.tA-p.kA)*RAD);
  const fyB = 7*Math.cos(p.tB*RAD) + 7*Math.cos((p.tB-p.kB)*RAD);
  ...
}
```

Hmm, I need to pass the hip Y. Let me restructure: pass hipX and hipY, and the caller computes hipY.

For run/land: hipY = groundY - max(fyA, fyB). But fyA/fyB depend on the pose which is computed in the caller. OK, let's compute the pose in the caller, then compute the hipY, then call drawAthlete(hipX, hipY, pose).

For flight: hipY = groundY - 13 - hm*PPM.

Hmm, but the feet at landing should be at the ground. In the flight, when hm=0, hipY = groundY-13, and the pose has the feet at fy ≈ 8.5 below the hip → the feet would be 4.5px above the ground. Then they sink. Let's handle it by using the max foot depth in the flight too, so the feet touch the ground at hm=0. Actually no — during the flight, the athlete's "height" is the hip height, and the feet dangle. It's fine for the feet to be above the ground at hm=0 (that's when the feet touch). Hmm, no: at hm=0 the athlete should be landing with their feet touching the ground.

Let's just define: hipY = groundY - 13 - hm*PPM for flight, and at hm=0, the hip is 13 above the ground. With the landing pose (tA=56, kA=6), the foot y is 7cos56 + 7cos50 = 3.91+4.5 = 8.4. So the feet are 8.4 below the hip = 13-8.4 = 4.6px above the ground. Not great.

Let's instead use hipY = groundY - maxFootY - hm*PPM for all modes. Then at hm=0 the lowest foot touches the ground. 

But then during the flight, as the pose changes, the hip would move relative to the arc. That's actually fine and looks natural (the body follows the parabola of the lowest point... no, it makes the body jitter).

Hmm. Let's use a constant offset during flight: the lowest foot should be at the ground when hm=0. At t=1 the foot depth is 8.4, so hipY = groundY - 8.4 - hm*PPM. But at t=0 the foot depth is different (legs trailing back: tA=-45,kA=18 → 7cos(-45)+7cos(-63) = 4.95+3.18 = 8.13; tB=22,kB=55 → 7cos22+7cos(-33) = 6.49+5.87=12.36). Max = 12.36. So at t=0 the hip is at groundY-12.36, and at t=1 at groundY-8.4. So the hip rises 4px relative to the parabola. That's actually realistic (the legs trail down at takeoff).

Hmm, but it makes the arc look weird. Let's just use a fixed hip offset during flight and accept slight foot float at landing. Use offset = 11.

Actually, you know what — the simplest visually good approach: during flight, hipY = groundY - 12 - hm*PPM. Then at hm=0 the hip is 12 above the ground. The feet in the landing pose are at 8.4 below → 3.6px above the ground. Then we switch to the 'land' state which uses ground-lock, so the feet snap to the ground. A 3.6px snap is barely noticeable, especially with the sand puff covering it.

OK, use 12. Actually let's use 10 so the feet are at 10-8.4 = 1.6 above. Hmm, but during the middle of the flight the legs tuck up, so the feet would be way above the ground — that's correct.

Let's use hipOffset = 11 for flight. Fine.

OK.

### drawAthlete implementation

```js
function drawAthlete(hipX, hipY, p){
  const hipXr = Math.round(hipX), hipYr = Math.round(hipY);
  const lean = p.lean*RAD;
  const nx = hipXr + Math.sin(lean)*11;
  const ny = hipYr - Math.cos(lean)*11;
  
  // far leg (A)
  drawLeg(hipXr,hipYr, p.tA, p.kA, true);
  // far arm (B)
  drawArm(nx,ny, p.uB, true);
  // torso
  limb(hipXr,hipYr,nx,ny,6,'#a82c2c');  // hmm, use the top color
  ...
}
```

Hmm, the torso should be the top color. Let's define the palette.

Let me write helper functions with color params.

```js
const P = {
  skin:'#f2c69c', skinD:'#c99a6e',
  top:'#e04040', topD:'#9e2626',
  short:'#26355c', shortD:'#182238',
  shoe:'#f8f8f8', shoeD:'#b8b8b8',
  hair:'#2a1c12'
};
```

drawLeg:
```js
function drawLeg(hx,hy,tA,kA,dark){
  const kx = hx + Math.sin(tA*RAD)*7;
  const ky = hy + Math.cos(tA*RAD)*7;
  const fx = kx + Math.sin((tA-kA)*RAD)*7;
  const fy = ky + Math.cos((tA-kA)*RAD)*7;
  limb(hx,hy,kx,ky,4, dark?P.shortD:P.short);
  limb(kx,ky,fx,fy,3, dark?P.skinD:P.skin);
  ctx.fillStyle = dark?P.shoeD:P.shoe;
  ctx.fillRect(Math.round(fx)-2, Math.round(fy)-1, 5, 3);
}
```

Hmm, the shorts should cover the upper thigh. Using the short color for the whole thigh is fine (like a full-length short). Actually, let's make the thigh skin colored and add shorts as a separate blob near the hip. Simpler: thigh = skin, and draw a shorts blob over the hip.

Let's do: thigh = skin color, shin = skin color, shoe = white. And a shorts blob: a 7x5 rect at the hip covering the top of both thighs. Hmm, but with the legs at different angles, a static rect is fine.

Let's draw the shorts as a rounded blob at the hip: fillRect(hipX-4, hipY-2, 8, 6) in short color. Then the thighs come out of it. Good.

Actually, since the hip is where both legs attach, drawing the shorts after the far leg but before the near leg would put the shorts over the far leg. Let's draw: far leg → shorts → torso → near leg → near arm.

Hmm, the near leg would then cover the shorts. That's fine since the near thigh comes from the hip.

Let me just draw the shorts right after the far leg. Then the near leg is drawn on top, emerging from the hip. Looks fine.

OK.

drawArm:
```js
function drawArm(nx,ny,uA,dark){
  const ex = nx + Math.sin(uA*RAD)*5;
  const ey = ny + Math.cos(uA*RAD)*5;
  const fa = uA+105;
  const hx = ex + Math.sin(fa*RAD)*5;
  const hy = ey + Math.cos(fa*RAD)*5;
  limb(nx,ny,ex,ey,3, dark?P.topD:P.top);
  limb(ex,ey,hx,hy,2, dark?P.skinD:P.skin);
  ctx.fillStyle = dark?P.skinD:P.skin;
  ctx.fillRect(Math.round(hx)-1, Math.round(hy)-1, 3, 3);
}
```

Head:
```js
const hx2 = nx + Math.sin(lean)*2;
const hy2 = ny - Math.cos(lean)*2;
ctx.fillStyle=P.skin;
ctx.fillRect(Math.round(hx2)-2, Math.round(hy2)-4, 5, 6);
ctx.fillStyle=P.hair;
ctx.fillRect(Math.round(hx2)-3, Math.round(hy2)-5, 6, 3);
ctx.fillRect(Math.round(hx2)-3, Math.round(hy2)-3, 2, 3); // back of head hair
```

Hmm, the head is at the neck + up. The neck is already at hip + 11 up. So the head center is at ~13 above the hip. Total height: hip at groundY-13, head top at groundY-13-13-5 = groundY-31. So the athlete is ~31px tall? That's too tall for my earlier estimate of 24.

Let me recompute: hip at groundY-13 (legs 14 long, so the hip is 14 above the feet... wait, with a straight leg the foot is 14 below the hip. With the run pose, the max foot depth is ~13. So the hip is ~13 above the ground.

Torso 11 up → neck at 24 above the ground. Head 5 tall above that → head top at ~29 above the ground.

So the athlete is 29px tall. In a 270px canvas, that's 11% of the height. That's reasonable (a real person is 1.8m; at 18px/m that's 32px). Good, consistent!

Actually 29px / 18px per metre = 1.6m. Slightly short but fine.

Hmm, the athlete at 29px tall might look big relative to the stands. The stands are 100px tall = 3.4 athletes. Fine.

OK.

### Now let me write everything.

One more thing: the "puff of particles" on landing. Let's spawn ~24 particles at the landing point with random velocities, colored sand.

Also a small dust cloud.

### Measuring the distance

On landing:
```js
const landingX = G.x;
let d = (landingX - BOARD_X)/PPM;
if(G.foul) d = 0;
if(d < 0) d = 0;
G.dist = Math.round(d*10)/10;
```

### Now the AI.

Let me write the AI carefully.

```js
function updateAI(dt){
  if(G.state!=='run') return;
  // mash
  G.aiTimer -= dt;
  if(G.aiTimer <= 0){
    G.aiTimer += 1/AI_RATE;   // AI_RATE = 14
    pressRun(G.aiSide);
    G.aiSide = G.aiSide==='L'?'R':'L';
  }
  // jump decision
  const v = Math.max(G.speed, 2);
  const tToBoard = (BOARD_X - 4 - G.x)/v;
  const phi = 2*Math.PI*G.angleT/ANGLE_PERIOD;
  let k = Math.ceil(phi/Math.PI);
  let t45 = (k*Math.PI - phi)*ANGLE_PERIOD/(2*Math.PI);
  if(t45 < 0) t45 += ANGLE_PERIOD/2;
  // is this the last crossing before the board?
  const tNext = t45 + ANGLE_PERIOD/2;
  if(t45 <= tToBoard && tNext > tToBoard){
    if(t45 < dt*1.5) doJump();
  }
  // safety
  if(tToBoard < 0.03) doJump();
}
```

Hmm, `pressRun` needs to bypass the autoplay check. Let's have a separate function.

Also, the AI's speed: with 14 presses/sec, equilibrium = 14 m/s, capped at 11.8. Good, it hits max.

But wait: the AI presses at a fixed rate, but if it presses while the state is not 'run', nothing happens. Fine.

Also, `G.aiTimer += 1/AI_RATE` — if dt is large, this could loop. Fine.

Hmm, one issue: the AI alternates sides strictly. `pressRun(side)` checks that side !== lastSide. Since the AI alternates, it's fine.

Now, the timing: ANGLE_PERIOD = 1.15s, so a 45° crossing every 0.575s. At 11.8 m/s, that's 6.8m apart. The AI picks the last crossing before the board. It needs to be within 6.8m of the board when it starts looking. Since the check runs every frame, it'll find the right one.

But there's a subtlety: tToBoard is computed with the current x and speed. As the athlete approaches, tToBoard decreases. The condition `t45 <= tToBoard && tNext > tToBoard` becomes true at some point and stays true until the jump. Then `t45 < dt*1.5` triggers the jump. Good.

But if t45 is large (say 0.4s) and tToBoard is 0.45s, then the condition is true and we wait. As time passes, t45 decreases and tToBoard decreases. If the speed is constant, they decrease at the same rate, so the condition stays true. Good.

Then when t45 reaches ~0, we jump. 

But what if the athlete's x overshoots? The safety `tToBoard < 0.03` catches it.

Good.

Also, `G.angleT` is only advanced during 'run'. Good.

Hmm, one thing: the AI computes t45 from the current angleT. But angleT advances by dt each frame. So phi advances. t45 = time until the next multiple of π. Let me verify: angle = 45 + 25 sin(2π angleT/T). We want sin(...) = 0, i.e., 2π angleT/T = kπ. So angleT = kT/2. At the current angleT, the next crossing is at angleT_next = ceil(angleT/(T/2)) * T/2. So t45 = angleT_next - angleT. 

Let me use that directly:
```js
const half = ANGLE_PERIOD/2;
let t45 = Math.ceil(G.angleT/half)*half - G.angleT;
if(t45 < 0.0001) t45 += half;
```
Hmm, if angleT is exactly at a multiple, t45 = 0. Then we'd jump. That's correct (we're at 45°).

Actually, if angleT is exactly a multiple of half, we're at 45°. Good.

But floating point: ceil might give the same value. Let's handle: if t45 < 1e-6, t45 = 0 (jump now).

Let's write:
```js
const half = ANGLE_PERIOD/2;
let t45 = Math.ceil((G.angleT + 1e-9)/half)*half - G.angleT;
```

Then t45 ∈ [0, half). Good.

And the next crossing after that is t45 + half.

Condition: `t45 <= tToBoard && t45 + half > tToBoard`. Then jump when t45 < 0.02.

Hmm, but if t45 is 0.5 and tToBoard is 0.52, then t45+half = 1.075 > 0.52. Condition true. Then we wait until t45 ≈ 0, which is 0.5s later. But in 0.5s the athlete moves 5.9m and tToBoard becomes 0.02. So t45 ≈ 0 and tToBoard ≈ 0.02 simultaneously. 

But wait: as time passes, t45 decreases from 0.5 to 0, and tToBoard decreases from 0.52 to 0.02. They decrease at the same rate. So they stay in sync. At the end, t45=0 and tToBoard=0.02 → jump. 

But hold on: t45 jumps back to `half` after the crossing. So right after the crossing, t45 = 1.15/2 = 0.575. The condition `t45 <= tToBoard` would then be 0.575 <= 0.02 → false. So we wouldn't re-trigger. Good.

Great.

But there's a risk: the athlete's speed decays between presses, so v isn't constant. The estimate tToBoard uses the current v. It should be close enough. And the safety check catches fouls.

Actually, one more risk: what if the AI's x at the jump is exactly BOARD_X - 4? Then the takeoff is 4px before the foul line. The distance measured is from BOARD_X, so we lose 4px = 0.22m. That's fine.

Hmm, but I want the AI to jump as close to the board as possible. Let's target BOARD_X - 2. With a 0.02s reaction, at 11.8 m/s that's 0.24m = 4.3px. So the AI would jump at BOARD_X - 2 - 4.3 = BOARD_X - 6.3. That's 0.35m lost. Hmm.

Let's reduce the threshold: jump when t45 < 0.005. And target BOARD_X - 1. Then the jump happens at about BOARD_X - 1 - 0.06*18... 

Actually let's just make the AI check `t45 <= tToBoard` where tToBoard = (BOARD_X - 1 - x)/v, and jump when t45 < 0.008. The result: the athlete jumps about 0.1m before the board. Losing ~0.1m. Acceptable.

Also, the takeoff angle will be very close to 45°.

Let's estimate the AI's distance: speed 11.8, angle ~45 → 9.28m minus 0.1 = 9.18m. That's a world record. 

But wait — that's only if the speed is exactly 11.8. The AI mashes at 14/s → equilibrium 14, capped at 11.8. So yes, 11.8.

Hmm, that means the AI always breaks the world record. Maybe too good. Let's lower the AI rate to 11.5/s → equilibrium 11.5 m/s. Then d = 11.5²/15 = 8.82m. Just under the WR. 

Let's use AI_RATE = 11.5. Then the AI's distance ≈ 8.8m, close to but under the WR. Sometimes it might vary.

Hmm, but the speed equilibrium: gain = 0.85 per press, decay = speed*0.85 per second. Equilibrium: 0.85*11.5 = speed*0.85 → speed = 11.5. Yes.

But the cap is 11.8, so it reaches 11.5. Time constant 1/0.85 = 1.18s. Over 38m at an average speed of ~10 m/s = 3.8s. Starting from 0, reaching 11.5*0.96 = 11.04 in 3.8s. Hmm, so it's still accelerating.

Let's see: speed(t) = 11.5*(1-e^(-0.85t)). At t=3.8: 11.5*(1-0.039) = 11.05. Distance traveled = ∫ = 11.5*(t + (e^(-0.85t)-1)/0.85) = 11.5*(3.8 + (0.039-1)/0.85) = 11.5*(3.8 - 1.13) = 30.7m. So it reaches the board at 30.7m, not 38m. Hmm, so it takes longer.

Let's solve: distance = 38 = 11.5*(t - (1-e^(-0.85t))/0.85). Try t=5: 11.5*(5 - (1-0.0142)/0.85) = 11.5*(5-1.16) = 44.2. Too far. t=4.5: 11.5*(4.5 - (1-0.0219)/0.85)=11.5*(4.5-1.15)=38.5. So t≈4.47s. Speed at t=4.47: 11.5*(1-e^-3.8) = 11.5*0.9776 = 11.24. 

So the AI's speed at the board is 11.24 m/s. d = 11.24²/15 = 8.42m. Under the WR. 

And the jump takes 2*11.24*sin(45)/15 = 2*7.95/15 = 1.06s. Good.

So the AI gets ~8.4m. Nice, a strong but not record-breaking jump. Occasionally with a good angle it might hit 8.5-8.6.

Let's make the runway a bit shorter so the AI doesn't reach as high a speed... no, 8.4m is good.

Hmm, but I want the world record line at 8.95m to be visible and reachable. A human mashing faster than 11.5/s could reach 11.8 → 9.28m. But it'd be hard.

Let's set MAX_SPEED = 12.2 so a very fast masher can break the record. Then equilibrium at 14/s = 14 (capped at 12.2). d = 12.2²/15 = 9.92m. Hmm, that's a lot.

Let's set g = 16: d = 12.2²/16 = 9.30m. And the AI at 11.24: 11.24²/16 = 7.9m. Hmm, that's below WR.

Let's tune: I want the AI to get ~8.5m and a perfect human run to get ~9.2m.

With g = 15: AI at 11.24 → 8.42m. Perfect at 12.2 → 9.92m. The gap is large.

The speed range 11.24 to 12.2 is small but the distance is quadratic. Let's just accept it. Set MAX_SPEED = 12.0: perfect → 9.6m. 

Hmm, the WR is 8.95. A perfect run would be 9.6m, which beats it by a lot.

Let's set MAX_SPEED = 11.8 and the AI_RATE = 11.0. Then the AI's equilibrium is 11.0 and it reaches ~10.8 at the board → d = 10.8²/15 = 7.78m. Hmm, a bit low.

Let's use g = 14.5, MAX_SPEED = 11.8.
- AI at 11.24: 11.24²/14.5 = 8.71m. 
- Perfect at 11.8: 11.8²/14.5 = 9.60m.

Still 9.6 for perfect. Hmm.

Honestly, the WR line is just a visual reference. It's fine if a perfect jump beats it. Let's keep g=15, MAX_SPEED=11.8, AI_RATE=11.0.

AI equilibrium 11.0 → at the board ~10.85 → d = 10.85²/15 = 7.85m. That's a decent jump.

Hmm, let's use AI_RATE = 12.0 → equilibrium 12.0, capped at 11.8. At the board, speed = 11.8*(1-e^(-0.85*4.47))... wait, with the cap: speed(t) = min(11.8, 12*(1-e^(-0.85t))). It reaches 11.8 when 12*(1-e^-0.85t)=11.8 → e^-0.85t = 0.0167 → t = 4.8s. Distance at 4.8s: ∫min(...) ≈ 12*(4.8 - (1-0.0167)/0.85) = 12*(4.8-1.157) = 43.7m. So it caps out around 43.7m, which is past the board (38m). At 38m: t ≈ 4.2s, speed = 12*(1-e^-3.57) = 12*0.9718 = 11.66. d = 11.66²/15 = 9.06m. 

That's just over the WR. Nice — the AI gets a near-record jump. Let's use AI_RATE = 12.0.

Hmm, but then the AI breaks the WR every time, which is a bit much. Let's use AI_RATE = 11.4: equilibrium 11.4, at the board speed ≈ 11.4*(1-e^(-0.85*4.35)) = 11.4*0.9752 = 11.12 → d = 8.24m. Good, under the WR.

Let's go with AI_RATE = 11.6 → at the board ~11.31 → d = 8.53m. Nice.

OK, AI_RATE = 11.6. And MAX_SPEED = 11.8.

Actually, hmm, I realize the AI's actual distance also depends on the takeoff angle. If the angle is exactly 45, d = v²/15. If it's 43 or 47, d = v² sin(86°)/15 = v²*0.9976/15. Negligible.

Good.

Let me also double check the run distance: 38m at an average speed... the AI takes ~4.4s to cover 38m. Plus the flight 1.06s. So the run portion is 4.4s. The replay covers the last 0.8s of the run + 1.06s flight + 0.6s land = 2.5s at 0.5x = 5s. Hmm, a bit long. Let's use 0.55x and a 2.2s window → 4s.

OK.

### Let's write the render for the pit and the world.

I'll write a helper `wx(x)` = x - G.camX for world→screen.

### Time to write the actual code. Let me be systematic.

I'll write the whole file now.

```js
// ============ FONT ============
const FONT_DATA = {
'A':"01110,10001,10001,11111,10001,10001,10001",
'B':"11110,10001,10001,11110,10001,10001,11110",
'C':"01110,10001,10000,10000,10000,10001,01110",
'D':"11110,10001,10001,10001,10001,10001,11110",
'E':"11111,10000,10000,11110,10000,10000,11111",
'F':"11111,10000,10000,11110,10000,10000,10000",
'G':"01110,10001,10000,10111,10001,10001,01111",
'H':"10001,10001,10001,11111,10001,10001,10001",
'I':"11111,00100,00100,00100,00100,00100,11111",
'J':"00111,00010,00010,00010,00010,10010,01100",
'K':"10001,10010,10100,11000,10100,10010,10001",
'L':"10000,10000,10000,10000,10000,10000,11111",
'M':"10001,11011,10101,10101,10001,10001,10001",
'N':"10001,11001,10101,10011,10001,10001,10001",
'O':"01110,10001,10001,10001,10001,10001,01110",
'P':"11110,10001,10001,11110,10000,10000,10000",
'Q':"01110,10001,10001,10001,10101,10010,01101",
'R':"11110,10001,10001,11110,10100,10010,10001",
'S':"01111,10000,10000,01110,00001,00001,11110",
'T':"11111,00100,00100,00100,00100,00100,00100",
'U':"10001,10001,10001,10001,10001,10001,01110",
'V':"10001,10001,10001,10001,10001,01010,00100",
'W':"10001,10001,10001,10101,10101,11011,10001",
'X':"10001,10001,01010,00100,01010,10001,10001",
'Y':"10001,10001,01010,00100,00100,00100,00100",
'Z':"11111,00001,00010,00100,01000,10000,11111",
'0':"01110,10001,10011,10101,11001,10001,01110",
'1':"00100,01100,00100,00100,00100,00100,01110",
'2':"01110,10001,00001,00010,00100,01000,11111",
'3':"11111,00010,00100,00010,00001,10001,01110",
'4':"00010,00110,01010,10010,11111,00010,00010",
'5':"11111,10000,11110,00001,00001,10001,01110",
'6':"00110,01000,10000,11110,10001,10001,01110",
'7':"11111,00001,00010,00100,01000,01000,01000",
'8':"01110,10001,10001,01110,10001,10001,01110",
'9':"01110,10001,10001,01111,00001,00010,01100",
' ':"00000,00000,00000,00000,00000,00000,00000",
'.':"00000,00000,00000,00000,00000,01100,01100",
',':"00000,00000,00000,00000,00110,00100,01000",
':':"00000,01100,01100,00000,01100,01100,00000",
'-':"00000,00000,00000,11111,00000,00000,00000",
'!':"00100,00100,00100,00100,00100,00000,00100",
'?':"01110,10001,00001,00110,00100,00000,00100",
'/':"00001,00010,00010,00100,01000,01000,10000",
'%':"11001,11010,00010,00100,01000,01011,10011",
"'":"00100,00100,00000,00000,00000,00000,00000",
'(':"00010,00100,01000,01000,01000,00100,00010",
')':"01000,00100,00010,00010,00010,00100,01000",
'+':"00000,00100,00100,11111,00100,00100,00000",
'*':"00000,10101,01110,11111,01110,10101,00000",
'=':"00000,00000,11111,00000,11111,00000,00000",
'<':"01000,00100,00010,00001,00010,00100,01000",
'>':"00010,00100,01000,10000,01000,00100,00010",
};
```

Good.

Now let's write the rest.

I need to be careful about performance with drawText. Let's cache the HUD text? Nah.

Let me write the crowd tile generation.

```js
function makeCrowdTile(){
  const c = document.createElement('canvas');
  c.width = 480; c.height = 108;
  const g = c.getContext('2d');
  g.imageSmoothingEnabled = false;
  // roof
  g.fillStyle = '#1c2130'; g.fillRect(0,0,480,10);
  g.fillStyle = '#2c3348'; g.fillRect(0,10,480,3);
  // stands background
  g.fillStyle = '#151a28'; g.fillRect(0,13,480,95);
  
  const tierH = 24;
  const tiers = 4;
  const skin = ['#f0c8a0','#d8a878','#a87850','#f8e0c0'];
  const shirts = ['#e05050','#4a7fd8','#4fc060','#e8c040','#d060c0','#f0f0f0','#40c8d0','#e08030','#8050d0','#50a0e0','#c0c0c0','#70d070'];
  
  let seed = 12345;
  function rnd(){ seed = (seed*1103515245 + 12345) & 0x7fffffff; return seed/0x7fffffff; }
  
  for(let t=0;t<tiers;t++){
    const ty = 13 + t*tierH;
    // tier base
    g.fillStyle = t%2 ? '#232a3e' : '#1e2436';
    g.fillRect(0, ty, 480, tierH);
    // walkway
    g.fillStyle = '#0e1220';
    g.fillRect(0, ty+tierH-3, 480, 3);
    
    // rows of people
    for(let row=0; row<2; row++){
      const ry = ty + 2 + row*10;
      for(let x=0; x<480; x+=5){
        if(rnd() < 0.12) continue;
        const px = x + Math.floor(rnd()*2);
        const sh = shirts[Math.floor(rnd()*shirts.length)];
        const sk = skin[Math.floor(rnd()*skin.length)];
        // body
        g.fillStyle = sh;
        g.fillRect(px, ry+3, 4, 5);
        // head
        g.fillStyle = sk;
        g.fillRect(px+1, ry, 2, 3);
      }
    }
  }
  // front railing
  g.fillStyle = '#39415c'; g.fillRect(0,104,480,4);
  g.fillStyle = '#5a6488'; g.fillRect(0,104,480,1);
  return c;
}
```

Hmm, the tier rows: tierH=24, 4 tiers = 96, plus 13 top = 109. Let's make the height 112 and the tiers start at 13. 13+96 = 109. OK, height 112.

Let's set the tile height to 112 and draw at y=58. Then it covers 58..170. The stands area is 70..168, plus the roof 58..70.

Hmm, I said the roof is at 60..70 and the stands at 70..168. Let me align: tile drawn at y=58, roof at 58..71 (13 tall), stands 71..168.

Let's set: tile height 112, roof 0..13, stands 13..109, railing 109..112. Drawn at y=58 → 58..170.

Good.

Then the wall at 170..184.

OK.

Now the wavers. I'll generate a list of positions in tile space where people wave. Let's pick positions deterministically:

```js
const WAVERS = [];
for(let t=0;t<4;t++){
  for(let i=0;i<7;i++){
    const x = 20 + i*66 + ((t*17)%23);
    const y = 13 + t*24 + 2 + (i%2)*10;
    WAVERS.push({x, y, ph: (i*1.7+t*0.9)});
  }
}
```

28 wavers per tile. Drawn twice (2 tile copies) = 56. Each is a couple of fillRects. Fine.

Draw:
```js
function drawWavers(off){
  const tt = G.time;
  for(let copy=0; copy<2; copy++){
    const baseX = -off + copy*480;
    if(baseX > 480 || baseX < -480) continue;
    for(const w of WAVERS){
      const x = baseX + w.x;
      if(x < -6 || x > 486) continue;
      const y = 58 + w.y;
      const s = Math.sin(tt*6 + w.ph);
      const up = s > 0 ? 1 : 0;
      ctx.fillStyle = '#f0c8a0';
      // arms
      ctx.fillRect(Math.round(x)-1, y - (2+up*2), 1, 3);
      ctx.fillRect(Math.round(x)+4, y - (2+ (1-up)*2), 1, 3);
    }
  }
}
```

Hmm, the waver's y is the top of the head. The arms would be at y+1..y+4. Let's just draw small 1x3 arms at the sides going up.

Fine.

### Flags

```js
const FLAG_POS = [{x:110, c1:'#e03030', c2:'#f8f8f8'}, {x:350, c1:'#3070e0', c2:'#f8e040'}];
```

Draw at tile x positions with the parallax offset:
```js
function drawFlags(off){
  const t = G.time;
  for(let copy=0; copy<2; copy++){
    const baseX = -off + copy*480;
    for(const f of FLAG_POS){
      const x = Math.round(baseX + f.x);
      if(x < -20 || x > 500) continue;
      // pole
      ctx.fillStyle = '#c8c8d0';
      ctx.fillRect(x, 20, 1, 40);
      // flag
      for(let i=0;i<14;i++){
        const fy = 22 + Math.round(Math.sin(t*5 + i*0.5)*2);
        ctx.fillStyle = i < 7 ? f.c1 : f.c2;
        ctx.fillRect(x+1+i, fy, 1, 8);
      }
    }
  }
}
```

Hmm, the flag would be 14 wide and 8 tall. Good.

But wait, the flag is drawn per copy, so 4 flags total. Fine.

Actually, the poles would be at y=20..60 which overlaps the sky and the roof. Good.

### Clouds

```js
const CLOUDS = [];
for(let i=0;i<8;i++){
  CLOUDS.push({x: Math.random()*700, y: 5+Math.random()*35, w: 18+Math.random()*26, h: 4+Math.random()*3, s: 2+Math.random()*4});
}
```

Update: x -= s*dt; if x < -60, x += 760.

Draw: a cloud is a set of overlapping rects. Let's do:
```js
function drawCloud(x,y,w,h){
  ctx.fillStyle='#dceaf8';
  ctx.fillRect(x, y+h*0.4, w, h*0.6);
  ctx.fillRect(x+w*0.15, y, w*0.5, h);
  ctx.fillRect(x+w*0.5, y+h*0.2, w*0.4, h*0.8);
  // shading
  ctx.fillStyle='#b8cfe6';
  ctx.fillRect(x, y+h, w, 1);
}
```

Rough but fine. Let's use rounded pixel values.

### Now let's write the world drawing.

```js
function drawWorld(){
  const cam = G.camX;
  // wall/ads
  drawAds(cam);
  // verge
  ctx.fillStyle = '#2a6a38';
  ctx.fillRect(0, 182, W, 12);
  ctx.fillStyle = '#37864a';
  ctx.fillRect(0, 182, W, 2);
  // grass tufts
  ...
  // track base
  ctx.fillStyle = '#9c3f28';
  ctx.fillRect(0, 194, W, H-194);
  // runway lane
  ctx.fillStyle = '#b8503a';
  ctx.fillRect(0, 202, W, 36);
  // lane lines
  ctx.fillStyle = '#e8e0d8';
  ctx.fillRect(0, 202, W, 1);
  ctx.fillRect(0, 237, W, 1);
  
  // board
  const bx = BOARD_X - cam;
  ctx.fillStyle = '#e8e8e8';
  ctx.fillRect(bx-BOARD_W, 200, BOARD_W, 42);
  ctx.fillStyle = '#c0c0c0';
  ctx.fillRect(bx-BOARD_W, 240, BOARD_W, 2);
  ctx.fillStyle = '#e03030';
  ctx.fillRect(bx-2, 200, 2, 42);
  ...
}
```

Hmm, the board at y=200..242 and the pit at 200..244. OK.

Pit:
```js
  ctx.drawImage(pitCanvas, PIT_START-cam, 200);
```

Where pitCanvas is 216x44.

Then the landing mark, the WR line, the best line.

WR line: a vertical red line at x = BOARD_X + WR*PPM, from y=196 to y=246, dashed.
Best line: a green line at BOARD_X + best*PPM.

Hmm, but the best line should only show during subsequent attempts.

Also the takeoff board's front edge already has a red line.

Let's also draw a white "foul line" marker.

OK.

### Pit canvas generation

```js
function makePit(){
  const c = document.createElement('canvas');
  c.width = PIT_LEN; c.height = 44;
  const g = c.getContext('2d');
  g.fillStyle = '#e6c882'; g.fillRect(0,0,PIT_LEN,44);
  // speckles
  let seed = 999;
  function rnd(){ seed = (seed*1103515245+12345)&0x7fffffff; return seed/0x7fffffff; }
  for(let i=0;i<900;i++){
    const x = Math.floor(rnd()*PIT_LEN), y = Math.floor(rnd()*44);
    g.fillStyle = rnd()<0.5 ? '#d4b070' : '#f4dc9c';
    g.fillRect(x,y,1,1);
  }
  // darker edges
  g.fillStyle = 'rgba(140,110,60,0.5)';
  g.fillRect(0,0,PIT_LEN,1);
  g.fillRect(0,43,PIT_LEN,1);
  // metre lines
  for(let m=1;m<=11;m++){
    const x = m*PPM;
    if(x >= PIT_LEN) break;
    g.fillStyle = 'rgba(120,90,50,0.35)';
    g.fillRect(x, 4, 1, 40);
  }
  // tape strip
  g.fillStyle = '#f0d060'; g.fillRect(0, 34, PIT_LEN, 10);
  g.fillStyle = '#a08030'; g.fillRect(0, 34, PIT_LEN, 1);
  for(let m=0;m<=12;m++){
    const x = m*PPM;
    if(x >= PIT_LEN) break;
    g.fillStyle = '#403010';
    g.fillRect(x, 34, 1, 6);
    g.fillRect(x+9, 34, 1, 3);
  }
  // numbers
  ...
}
```

Hmm, drawing text into the pit canvas requires my drawText function which draws to ctx. Let me make drawText take a context parameter. Or use a global "target context" variable.

Let me refactor: `function textOn(g, str, x, y, color, sc)`.

Then `drawText(str,x,y,color,sc)` calls `textOn(ctx,...)`.

OK.

Numbers in the pit: at each metre, draw the number just below the tape. Actually let's draw the numbers above the tape, at y=24, in a dark brown, scale 1.

Hmm, the tape is at y=34..44. Numbers at y=25..32 (7 tall). Good.

Actually, let's put the numbers on the tape strip itself, alternating. Hmm, the tape is only 10px tall and the numbers are 7px. So the numbers fit on the tape at y=35..42 in black. 

Let's do: tape strip at y=33..44 (11 tall), numbers at y=35. And the ticks would collide. Let's just have the numbers, no ticks on the tape.

Hmm. Let's simplify: tape strip 33..44 in yellow, with black numbers every metre at y=35, and a tick line at every 0.5m above the tape.

Fine.

Actually the numbers 1-12 at 18px spacing, each 6px wide — fits fine.

OK.

### Landing mark

```js
function drawMark(){
  if(!G.mark) return;
  const x = G.mark.x - G.camX;
  // divot
  ctx.fillStyle = '#b89050';
  ctx.fillRect(Math.round(x)-5, 204, 10, 4);
  ctx.fillStyle = '#9c7840';
  ctx.fillRect(Math.round(x)-4, 206, 8, 3);
  ctx.fillStyle = '#d8b878';
  ctx.fillRect(Math.round(x)-6, 202, 12, 2);
  // feet
  ctx.fillStyle = '#8c6838';
  ctx.fillRect(Math.round(x)-4, 208, 3, 5);
  ctx.fillRect(Math.round(x)+1, 208, 3, 5);
}
```

Something like that.

### Particles

```js
function spawnSand(x, n){
  for(let i=0;i<n;i++){
    const a = -Math.PI*0.15 - Math.random()*Math.PI*0.7;
    const sp = 40 + Math.random()*160;
    G.particles.push({
      x: x + (Math.random()-0.5)*8,
      y: GROUND_Y + (Math.random()-0.5)*4,
      vx: Math.cos(a)*sp * (Math.random()<0.5?-1:1) ... 
    });
  }
}
```

Hmm, let me simplify: particles shoot up and outward.

```js
const ang = -Math.PI/2 + (Math.random()-0.5)*2.0;  // mostly up
const sp = 30 + Math.random()*140;
vx = Math.cos(ang)*sp;
vy = Math.sin(ang)*sp;   // negative = up in screen coords
```

Then update: vy += 500*dt; x += vx*dt; y += vy*dt. Life decreases. Draw as 1x1 or 2x2.

Also add some particles that go forward (in the direction of travel).

Good.

### Now, the main loop and states.

Let me write the update functions.

```js
function update(dt){
  G.time += dt;
  
  // clouds
  for(const c of CLOUDS){ c.x -= c.s*dt; if(c.x < -80) c.x += 760; }
  
  updateParticles(dt);
  
  switch(G.state){
    case 'ready':
      G.t += dt;
      if(G.t > 0.7){ G.state='run'; G.t=0; }
      break;
    case 'run': {
      G.t += dt;
      G.speed = Math.max(0, G.speed - G.speed*SPEED_DECAY*dt);
      G.x += G.speed*dt*PPM;
      G.angleT += dt;
      G.angle = 45 + 25*Math.sin(G.angleT*2*Math.PI/ANGLE_PERIOD);
      if(G.autoplay) aiRun(dt);
      // record
      recordFrame();
      // crossed the board without jumping → forced foul jump
      if(G.x > BOARD_X + 1 && G.state==='run'){ doJump(true); }
      break;
    }
    case 'fly': {
      G.t += dt;
      G.vy -= GRAV*dt;
      G.x += G.vx*dt*PPM;
      G.hm += G.vy*dt;
      recordFrame();
      if(G.hm <= 0){ G.hm = 0; doLand(); }
      break;
    }
    case 'land': {
      G.t += dt;
      recordFrame();
      if(G.t > 1.0){ G.state='result'; G.t=0; }
      break;
    }
    case 'result': {
      G.t += dt;
      if(G.t > 2.2){ startReplay(); }
      break;
    }
    case 'replay': {
      G.t += dt;
      G.replayIdx += dt*60*0.5;
      if(G.replayIdx >= G.replayFrames.length-1){ 
        G.state='replayEnd'; G.t=0; 
      }
      break;
    }
    case 'replayEnd': {
      G.t += dt;
      if(G.t > 0.8){ nextAttempt(); }
      break;
    }
    case 'over': {
      G.t += dt;
      if(G.t > 6){ restartGame(); }
      break;
    }
  }
  
  updateCamera(dt);
}
```

Hmm, `recordFrame` needs the current pose. Let me compute the pose in recordFrame.

Let me define `currentPose()`:
```js
function currentPose(){
  if(G.state==='fly'){
    const ft = Math.min(1, G.hm > 0 ? G.t/(G.flightTime) : 1);
    return lerpPose(FLY_KEYS, ft);
  }
  if(G.state==='land'){
    return lerpPose(LAND_KEYS, Math.min(1, G.t/0.9));
  }
  return poseRun(G.phase, G.speed/MAX_SPEED);
}
```

Hmm, for the flight, I need the normalized time. Let me compute `G.flyNorm = G.t / G.flightTime` where flightTime = 2*vy0/g.

Let's store `G.flightTime` at takeoff.

Then `ft = clamp(G.t/G.flightTime, 0, 1)`.

Good.

recordFrame:
```js
function recordFrame(){
  const p = currentPose();
  G.rec.push({x:G.x, hm:G.hm, tA:p.tA,kA:p.kA,tB:p.tB,kB:p.kB,uA:p.uA,uB:p.uB,lean:p.lean, mode:G.state});
  if(G.rec.length > 700) G.rec.splice(0, 100);
}
```

Hmm, splicing 100 at a time is fine.

Actually, the takeoff index: since we splice, the indices shift. Let's store `G.takeoffRecIndex` relative to the array. When splicing, subtract 100.

Simpler: don't splice during a run. Only clear at the start of each attempt. The run is ~5s = 300 frames, the flight 1.1s = 66 frames, the land 1s = 60. Total ~430 frames. That's fine. No splicing needed.

But if the player runs forever... no, the run ends at the board.

Actually, if the player never presses anything, the athlete stays at x=0 forever. Then the recording grows. Let's cap at 1200 frames and splice.

OK, handle the takeoff index adjustment.

Actually, simplest: only start recording when x > 100 (i.e., after 5.5m). No... 

Let's just record everything and cap at 1500 frames with a splice of 300. And track the takeoff index accordingly.

Hmm, if the athlete is standing still, that's 25 seconds of standing. The replay would start from the takeoff index anyway, so it doesn't matter.

Let's just do the simple cap.

Actually, for the replay we only need the last ~2.5s before the landing. Let's just, at landing time, slice from the takeoff index. If the takeoff index is valid, great.

I'll do: at doJump(), set `G.takeoffRecIdx = G.rec.length`. At doLand(), build the replay frames: `G.replayFrames = G.rec.slice(Math.max(0, G.takeoffRecIdx - 50))`.

But we also want the landing frames. So we should build the replay after the 'land' state finishes, so the recording includes the landing. Let's build the replay frames at the transition from 'land' to 'result'.

OK.

### doJump

```js
function doJump(forced){
  if(G.state!=='run') return;
  G.state='fly'; G.t=0;
  G.takeoffX = G.x;
  G.foul = forced || (G.x > BOARD_X);
  G.jumpAngle = G.angle;
  const th = G.jumpAngle*RAD;
  G.vx = G.speed*Math.cos(th);
  G.vy = G.speed*Math.sin(th);
  G.flightTime = 2*G.vy/GRAV;
  G.hm = 0.001;
  G.takeoffRecIdx = G.rec.length;
  G.phase = 0;
}
```

Hmm, if the speed is 0 (no presses), then vy=0 and the athlete falls immediately. Let's give a minimum speed of 2 for the jump so it doesn't look broken.

Actually, if the player never runs and presses jump at x=0, the speed is 0 → they just fall. That's fine and funny.

Let's add: if speed < 1.5, set it to 1.5 for the jump.

### doLand

```js
function doLand(){
  G.state='land'; G.t=0;
  const landingX = G.x;
  let d = (landingX - BOARD_X)/PPM;
  if(d < 0) d = 0;
  if(G.foul) d = 0;
  G.dist = Math.round(d*10)/10;
  G.mark = {x: landingX};
  spawnSand(landingX, 30);
  G.shakeT = 0.25;
}
```

### Result → next

```js
function finishAttempt(){
  G.results.push({d:G.dist, foul:G.foul});
  if(!G.foul && G.dist > G.best) G.best = G.dist;
  G.last = G.foul ? 0 : G.dist;
}
```

Call finishAttempt when transitioning to 'result'.

### startReplay

```js
function startReplay(){
  G.replayFrames = G.rec.slice(Math.max(0, G.takeoffRecIdx - 55));
  G.replayIdx = 0;
  G.state='replay'; G.t=0;
}
```

### nextAttempt

```js
function nextAttempt(){
  G.attempt++;
  if(G.attempt >= 3){ G.state='over'; G.t=0; }
  else startAttempt();
}
```

### restartGame

```js
function restartGame(){
  G.attempt=0; G.results=[]; G.best=0; G.last=0;
  startAttempt();
}
```

### updateCamera

```js
function updateCamera(dt){
  let targetX = G.x - 150;
  targetX = Math.max(-140, Math.min(560, targetX));
  G.camX += (targetX - G.camX) * Math.min(1, dt*9);
}
```

Hmm, for the replay, G.x is set from the replay frames. Good.

But wait, during the replay I set G.x from the frame. Let me make sure the camera follows.

Actually, in the 'replay' state, I should update G.x, G.hm, and the pose from the frame. Let me do that in the render or in the update.

Let me handle it in the update:
```js
case 'replay': {
  G.t += dt;
  G.replayIdx += dt*60*0.5;
  const i = Math.min(G.replayFrames.length-1, Math.floor(G.replayIdx));
  const f = G.replayFrames[i];
  if(f){ G.x = f.x; G.hm = f.hm; G.replayPose = f; }
  ...
}
```

And in the render, if the state is 'replay', use G.replayPose instead of currentPose().

Good.

### Rendering the athlete

```js
function renderAthlete(){
  let p, hipX, hipY;
  if(G.state==='replay' && G.replayPose){
    const f = G.replayPose;
    p = {tA:f.tA,kA:f.kA,tB:f.tB,kB:f.kB,uA:f.uA,uB:f.uB,lean:f.lean};
    hipX = f.x - G.camX;
    const fy = Math.max(footDepth(p.tA,p.kA), footDepth(p.tB,p.kB));
    hipY = GROUND_Y - fy - f.hm*PPM;
  } else {
    p = currentPose();
    hipX = G.x - G.camX;
    if(G.state==='fly'){
      hipY = GROUND_Y - 11 - G.hm*PPM;
    } else {
      const fy = Math.max(footDepth(p.tA,p.kA), footDepth(p.tB,p.kB));
      hipY = GROUND_Y - fy;
    }
  }
  drawAthlete(hipX, hipY, p);
}
```

Hmm, in the replay for the flight frames, using the foot-depth-based hipY would differ from the live version. Let me store the mode in the frame and use the same logic.

Let me store `mode` in each recorded frame and use it.

OK:
```js
if(f.mode === 'fly') hipY = GROUND_Y - 11 - f.hm*PPM;
else hipY = GROUND_Y - fy;
```

Good.

### The 'ready' state

Show "GO!" or "READY". The athlete stands at x=0 with a standing pose.

Standing pose: tA=0, kA=5, tB=0, kB=5, uA=5, uB=5, lean=3.

Let's use a poseRun(0, 0) — that gives tA=0, kA=62-62*sin(0.9)=62-48.6=13.4, tB=0, kB=62-62*sin(0.9+π)... = 62+48.6=110. Hmm, one leg is bent a lot. That's a running pose, not standing.

Let's define a standing pose explicitly:
```js
const STAND_POSE = {tA:8,kA:6,tB:-8,kB:6,uA:10,uB:10,lean:4};
```

Use that for 'ready'.

### HUD

Let's write it.

```js
function drawHUD(){
  // top panel
  ctx.fillStyle = 'rgba(8,12,26,0.85)';
  ctx.fillRect(0,0,W,24);
  ctx.fillStyle = '#2a3a60';
  ctx.fillRect(0,24,W,1);
  
  drawText('SPEED', 6, 5, '#8fb8ff', 1);
  // speed bar
  const bw = 130, bh = 10, bx = 48, by = 6;
  ctx.fillStyle='#101828'; ctx.fillRect(bx,by,bw,bh);
  ctx.strokeStyle='#4a6a9a'; ctx.lineWidth=1; ctx.strokeRect(bx+0.5,by+0.5,bw-1,bh-1);
  const f = Math.min(1, G.speed/MAX_SPEED);
  // color gradient
  const col = f<0.5 ? '#40d060' : f<0.8 ? '#e0d040' : '#f05030';
  ctx.fillStyle = col;
  ctx.fillRect(bx+1, by+1, Math.floor((bw-2)*f), bh-2);
  // segments
  ...
  
  drawText('ATT '+ (G.attempt+1) +'/3', 190, 5, '#ffffff');
  drawText('LAST '+ (G.last>0? G.last.toFixed(1):'--'), 260, 5, '#8fd0ff');
  drawText('BEST '+ (G.best>0? G.best.toFixed(1):'--'), 330, 5, '#ffe060');
  drawText('WR '+WR.toFixed(2), 400, 5, '#ff8080');
  
  // bottom panel
  ctx.fillStyle='rgba(8,12,26,0.8)';
  ctx.fillRect(0,248,W,22);
  ctx.fillStyle='#2a3a60';
  ctx.fillRect(0,248,W,1);
  
  drawText('ANGLE', 6, 254, '#8fb8ff');
  // gauge
  const gx=48, gy=253, gw=120, gh=12;
  ctx.fillStyle='#101828'; ctx.fillRect(gx,gy,gw,gh);
  // zones
  // marker
  const af = (G.angle-20)/50; // 20..70
  ctx.fillStyle='#ffffff';
  ctx.fillRect(gx + Math.floor(af*gw)-1, gy-1, 2, gh+2);
  // optimal marker at 45
  ctx.fillStyle='#40ff80';
  ctx.fillRect(gx + Math.floor(((45-20)/50)*gw)-1, gy-1, 2, gh+2);
  ...
}
```

Hmm, having both the optimal marker and the current marker at the same position when at 45 is confusing. Let's draw the optimal zone as a green band behind, and the current marker as a white line.

Let's draw: a green band from 42° to 48° in the background, then the white marker on top.

Good.

Then the angle value: `drawText('ANGLE ' + Math.round(G.angle), ...)`. Let's put the numeric readout after the gauge.

And a hint at the right: "P = DEMO" / "DEMO ON".

Also, during the run, show the "takeoff window" indicator? Nah.

### Overlays

- During 'ready': big "GO!" in the center.
- During 'result': big distance readout with "M".
- During 'replay': "REPLAY" and "SLOW MOTION".
- During 'over': the results screen.

Let's write.

### Big text

`drawText(str, x, y, color, 3)` with centering:
```js
function drawTextC(str, y, color, sc){
  const w = String(str).length*6*sc - sc;
  drawText(str, Math.round((W-w)/2), y, color, sc);
}
```

### Result display

```js
if(G.state==='result' || G.state==='replay' || G.state==='replayEnd'){
  // show the distance at the top-center or near the mark
}
```

Let's show a floating panel near the landing mark:
```js
ctx.fillStyle='rgba(8,12,26,0.85)';
ctx.fillRect(150, 60, 180, 44);
drawText('DISTANCE', ...);
drawText(G.dist.toFixed(1)+' M', ...);
```

Hmm, or show it big in the center. Let's do a big center readout with a border.

Actually, in the original, the distance appears near the landing mark. Let's draw a marker at the landing point with the distance above it.

Let me do both: a big center-ish panel.

Let's do a panel at the top-center: x from 140 to 340, y from 40 to 90.
- "DISTANCE" small
- "8.4 M" big (scale 3)

And if it's a foul, "FOUL!" in red.

Good.

### Results screen

```js
function drawResultsScreen(){
  ctx.fillStyle='rgba(4,8,20,0.9)';
  ctx.fillRect(50,40,380,190);
  ctx.fillStyle='#3a5a9a';
  ctx.fillRect(50,40,380,2);
  ctx.fillRect(50,228,380,2);
  ctx.fillRect(50,40,2,190);
  ctx.fillRect(428,40,2,190);
  
  drawTextC('FINAL RESULTS', 54, '#ffe060', 2);
  
  for(let i=0;i<3;i++){
    const r = G.results[i];
    const y = 88 + i*26;
    drawText('ATTEMPT '+(i+1), 80, y, '#8fb8ff', 2);
    if(r){
      drawText(r.foul?'FOUL':r.d.toFixed(1)+' M', 280, y, r.foul?'#ff6060':'#ffffff', 2);
    } else {
      drawText('--', 280, y, '#505870', 2);
    }
  }
  
  drawText('BEST', 80, 180, '#8fb8ff', 2);
  drawText(G.best.toFixed(1)+' M', 280, 180, '#60ff90', 2);
  
  if(G.best > WR) drawTextC('NEW WORLD RECORD!', 205, '#ffd040', 1);
  else drawTextC('WORLD RECORD 8.95 M', 205, '#a0a8c0', 1);
}
```

Hmm, the layout needs checking. 3 attempts at y=88, 114, 140. Then BEST at 180. Then the record line at 205. The panel ends at 230. OK.

Let's adjust: panel from y=40 to y=230 (190 tall).

- Title at 54 (scale 2, 14 tall) → 54..68
- Attempts at 84, 110, 136 (scale 2) → each 14 tall
- BEST at 168
- Record at 196

Good.

### Now, the "distance measured with one decimal" — yes, using toFixed(1).

### Let's also add a "measuring" animation during the result: a line from the board to the mark.

Let's draw it in the world during 'result' and 'replay'.

```js
if((G.state==='result'||G.state==='replay'||G.state==='replayEnd') && !G.foul && G.mark){
  const x0 = BOARD_X - G.camX;
  const x1 = G.mark.x - G.camX;
  const y = 246;
  ctx.fillStyle='#ffe060';
  ctx.fillRect(Math.round(x0), y, Math.round(x1-x0), 1);
  // end ticks
  ctx.fillRect(Math.round(x0), y-3, 1, 7);
  ctx.fillRect(Math.round(x1), y-3, 1, 7);
  // label
  drawText(G.dist.toFixed(1)+' M', Math.round((x0+x1)/2)-18, y+3, '#ffe060');
}
```

Hmm, y=246 is near the bottom panel (248). Let's use y=243.

Hmm, the track goes to 270. The bottom panel starts at 248. So y=243 is just above. OK.

Hmm, but the tape strip in the pit is at 233..244 (in pit-local coords 33..44, and the pit is drawn at y=200, so 233..244). Conflict.

Let's move the measuring line to y=246 and make the bottom panel start at 252. Hmm, tight.

Alternative: draw the measuring line right at the pit's top area, y=198, above the pit. Let's do y=197, above the pit (the pit starts at 200).

Actually, the track's far edge is at 194. So y=197 is on the track just above the pit. Let's use that. And a label above at y=188? That's the verge. Hmm.

Let's just put the measuring line at y=197 with the label at y=186 in yellow. Hmm, the verge is at 182-194.

OK, let's do: the measuring line at y=197, ticks going down 3px, and the label at the midpoint at y=186 (drawn over the verge in yellow). It'll be readable.

Hmm, the athlete's legs are around y=200-214, so the line at 197 is above them. Fine.

Let's do that.

### Shake

On landing, add a screen shake. Let's skip or make it tiny.

Actually let's add a small camera shake: offset the whole render by a few px. That requires translating. Let's use ctx.translate in the render. Hmm, it complicates the coordinate math. Let's skip the shake.

### Let me now also handle the 'P' key and auto-disable on player input.

```js
addEventListener('keydown', e=>{
  const k = e.code;
  if(k==='KeyP'){ G.autoplay = !G.autoplay; e.preventDefault(); return; }
  if(RUN_LEFT.includes(k) || RUN_RIGHT.includes(k) || JUMP_KEYS.includes(k)){
    if(G.autoplay) G.autoplay = false;
  }
  ...
});
```

Hmm, but if the player presses a run key, autoplay turns off and the press counts. Good.

Hmm, but that means during the demo, any accidental keypress kills the demo. That's the intended behavior though.

Let's also add: pressing 'P' when in autoplay shows "DEMO" in the HUD.

### Now let me handle the run keys.

```js
function pressRun(side){
  if(G.state!=='run') return;
  if(side === G.lastSide) return;
  G.lastSide = side;
  G.speed = Math.min(MAX_SPEED, G.speed + PRESS_GAIN);
  G.phase += 0.5;
  if(G.phase >= 1) G.phase -= 1;
}
```

Wait, the phase should wrap at 1. `G.phase += 0.5` then `if(G.phase>=1) G.phase -= 1`. Yes.

Hmm, but if the player presses rapidly, the legs spin fast. Good.

Also, if the player doesn't press, the legs freeze in the last position. Hmm, that looks odd — one leg forward, one back, frozen. In Track & Field that's exactly what happens. OK.

But during the 'ready' state, the athlete should stand still. And when transitioning to 'run', the phase is 0 → legs at sin(0)=0 → both legs at 0° thigh angle but different knee bends (kA=13.4, kB=110). Hmm, that's a weird pose.

Let me fix the run pose so that at phase 0, both legs are near vertical with a slight bend.

Actually, the issue is the knee formula: kB at phase 0 = 62 - 62*sin(π + 0.9) = 62 + 62*0.783 = 110.5. That's a heavily bent knee, which is correct for the back leg in mid-swing... but at phase 0 both thighs are at 0 (vertical), so one leg is straight down and the other is bent up behind. That's the "passing" pose in a run. It's actually correct!

Hmm, at phase 0: tA=0, kA=13 → leg A nearly straight down. tB=0, kB=110 → the thigh points down, the shin points backward-up. So the foot is behind and up. That's the recovery phase. Correct.

OK, it's fine.

But the hip height: footDepth(tB=0, kB=110) = 7*cos(0) + 7*cos(-110°) = 7 + 7*(-0.342) = 7 - 2.4 = 4.6. And footDepth(tA=0,kA=13) = 7 + 7*cos(-13) = 7+6.8 = 13.8. Max = 13.8. So the hip is at groundY-13.8. Good.

Alright.

### Autoplay toggle and the phase

The AI presses at 11.6/s → the phase advances 5.8/s → 5.8 cycles/s. Good.

### One more: the "lean" during the run.

lean = 8 + 14*speedFrac + 3*sin(2a). At max speed, lean = 22 + oscillation. That's a good forward lean.

Hmm, 22° is quite a lean. Let's use 6 + 12*speedFrac.

### Let me write the final code now.

I also need to handle the initial state: G.autoplay = true, and the state starts at 'ready'.

Let me write `startAttempt()` and call it at init.

Also, I should make sure that in the 'ready' state the athlete stands.

Let me write `currentPose()`:
```js
function currentPose(){
  if(G.state==='fly') return lerpPose(FLY_KEYS, Math.min(1, G.t/Math.max(0.01,G.flightTime)));
  if(G.state==='land') return lerpPose(LAND_KEYS, Math.min(1, G.t/0.9));
  if(G.state==='ready' || G.state==='result' || G.state==='replayEnd' || G.state==='over') return STAND_POSE;
  return poseRun(G.phase, Math.min(1,G.speed/MAX_SPEED));
}
```

Hmm, during 'result' the athlete should be in the landing pose (standing up from the crouch). Let's use LAND_KEYS at t=1.

Let's return `lerpPose(LAND_KEYS, 1)` for those states.

Actually for 'ready' use STAND_POSE, and for 'result'/'over' use the end of LAND_KEYS.

OK.

### Rendering order and the camera.

Everything world-related uses `G.camX`.

Let me now write the whole thing out. I'll try to be complete and correct.

One more consideration: `ctx.drawImage(pitCanvas, x, y)` with a non-integer x would blur. Let's round.

Also `ctx.imageSmoothingEnabled=false` handles it, but rounding is better.

Let me write the code.

```js
// ---- helpers ----
function px(x,y,w,h,c){ ctx.fillStyle=c; ctx.fillRect(Math.round(x),Math.round(y),Math.round(w),Math.round(h)); }
function wrap(v,m){ return ((v%m)+m)%m; }
function clamp(v,a,b){ return v<a?a:v>b?b:v; }
function lerp(a,b,t){ return a+(b-a)*t; }
```

OK writing now. Let me produce the final file.

One thing I need to double-check: the `limb` function with a thick brush. Let me implement it as described.

```js
function limb(x0,y0,x1,y1,t,col){
  x0=Math.round(x0); y0=Math.round(y0); x1=Math.round(x1); y1=Math.round(y1);
  let dx=Math.abs(x1-x0), sx=x0<x1?1:-1;
  let dy=-Math.abs(y1-y0), sy=y0<y1?1:-1;
  let err=dx+dy;
  const h=Math.floor(t/2);
  ctx.fillStyle=col;
  let guard=0;
  while(guard++ < 200){
    ctx.fillRect(x0-h, y0-h, t, t);
    if(x0===x1 && y0===y1) break;
    const e2=2*err;
    if(e2>=dy){ err+=dy; x0+=sx; }
    if(e2<=dx){ err+=dx; y0+=sy; }
  }
}
```

Good.

Now, drawing the athlete. Let me write it fully.

```js
function drawAthlete(hipX, hipY, p){
  const hx = Math.round(hipX), hy = Math.round(hipY);
  const lean = p.lean*RAD;
  const nx = hx + Math.sin(lean)*11;
  const ny = hy - Math.cos(lean)*11;
  
  // far leg
  drawLeg(hx,hy,p.tA,p.kA,true);
  // shorts
  ctx.fillStyle = P.shortD;
  ctx.fillRect(hx-4, hy-3, 8, 7);
  // far arm
  drawArm(nx,ny,p.uB,true);
  // torso
  limb(hx,hy,nx,ny,6,P.topD);
  // near arm
  drawArm(nx,ny,p.uA,false);
  // near leg
  drawLeg(hx,hy,p.tB,p.kB,false);
  // head
  const hdx = Math.round(nx + Math.sin(lean)*2);
  const hdy = Math.round(ny - Math.cos(lean)*2);
  ctx.fillStyle = P.skin;
  ctx.fillRect(hdx-2, hdy-4, 5, 6);
  ctx.fillStyle = P.hair;
  ctx.fillRect(hdx-3, hdy-6, 6, 3);
  ctx.fillRect(hdx-3, hdy-4, 2, 4);
  // eye
  ctx.fillStyle = '#2a1c12';
  ctx.fillRect(hdx+2, hdy-2, 1, 1);
}
```

Hmm, the shorts are drawn before the far arm and torso. The torso is drawn over the shorts at the hip. Since the torso is a thick line from the hip to the neck, it'll cover the top of the shorts. Let me draw the shorts after the torso.

Order: far leg → far arm → torso → shorts → near leg → near arm → head.

Hmm, the shorts should be over the torso's bottom. Yes.

Actually, the torso's bottom is at the hip, so the shorts at hy-3..hy+4 cover the hip area. Drawing the shorts after the torso covers the torso's bottom. Good.

Then the near leg is drawn on top of the shorts, which is fine (the thigh emerges from the shorts).

Let me reorder: far leg, far arm, torso, shorts, near leg, near arm, head.

Hmm, but the near arm is drawn from the shoulder (which is up at the neck). Drawing it after the torso is right.

Wait, I have the far arm drawn before the torso — good. And the near arm after. Good.

Let's finalize the order:
1. far leg (A)
2. far arm (B)
3. torso
4. shorts
5. near leg (B)
6. near arm (A)
7. head

Hmm, the head should be drawn before the near arm if the arm passes in front of the face. Doesn't matter much. Let's draw the head before the near arm.

Actually, when the arms are up (uA=145), the hand is above the head. Drawing the arm after the head means the arm is in front. Fine.

Order: far leg, far arm, torso, shorts, head, near leg, near arm.

OK.

Wait, "near arm (A)" — I said uA goes with leg A. And leg A is the far leg. Hmm, that's inconsistent. Let me just say: leg A is the far leg, arm B is the far arm. The near leg is B, the near arm is A.

For the run cycle: leg A forward ↔ arm A backward, arm B forward. Since leg A is far and arm B is far, that means when the far leg is forward, the far arm is backward. Correct (contralateral).

OK, so:
- far: leg A (tA,kA), arm B (uB)
- near: leg B (tB,kB), arm A (uA)

Good.

Now `drawArm(nx,ny,uA,dark)` uses the shoulder position. Fine.

Let me write drawLeg and drawArm with the dark flag.

```js
function drawLeg(hx,hy,tA,kA,dark){
  const kx = hx + Math.sin(tA*RAD)*7;
  const ky = hy + Math.cos(tA*RAD)*7;
  const fx = kx + Math.sin((tA-kA)*RAD)*7;
  const fy = ky + Math.cos((tA-kA)*RAD)*7;
  limb(hx,hy,kx,ky,4, dark?P.skinD:P.skin);
  limb(kx,ky,fx,fy,3, dark?P.skinD:P.skin);
  ctx.fillStyle = dark?P.shoeD:P.shoe;
  ctx.fillRect(Math.round(fx)-2, Math.round(fy)-1, 5, 3);
}
```

Hmm, the shoe at the foot position, always horizontal. For a running pose the foot should be angled. Let's keep it horizontal — it reads as a shoe.

Actually, let's angle the shoe slightly based on the shin angle:
```js
const sa = (tA-kA)*RAD;
const sx = Math.round(fx), sy = Math.round(fy);
ctx.fillRect(sx-2, sy-1, 4, 3);
ctx.fillRect(sx + (Math.cos(sa)>0?2:-3), sy-1, 2, 3);
```
Meh. Keep it simple: a 5x3 horizontal shoe.

OK.

Now let's write everything out.

Let me also double check the pit canvas number drawing. I'll use textOn.

Alright, writing the final code.

Also: the `recordFrame` during 'run' records every frame, including when the athlete is standing still at the start. That's fine.

Let me also handle the case where the replay frames array is empty (shouldn't happen).

Let me write it.

One more: I should prevent the default action for arrow keys and space to avoid page scrolling.

Let me write the final file.

Also for the 'over' state I need to reset. And after the results screen, restart the game (attempt 0).

Let me write.

Also: during the replay, I should show "REPLAY" and maybe a slow-motion vignette.

Let me add a subtle dark vignette during the replay.

OK, writing.

Actually one more detail: the `G.phase` should reset when the run starts. In startAttempt, phase = 0.

And during the flight, the phase isn't used (the FLY_KEYS use G.t).

Let's write it.

Final consideration on performance: the crowd tile is 480x112, drawn twice per frame. That's fine.

The pit canvas is 216x44. Fine.

Let me write.

def drawAds:
```js
function drawAds(cam){
  const off = wrap(cam*0.9, 64);
  for(let i=-1;i<9;i++){
    const x = Math.round(i*64 - off);
    const idx = i + Math.floor((cam*0.9)/64) + 1;
    const cols = ['#c23a3a','#3a5ac2','#e0c040','#3aa85a','#c23a9a','#e0e0e0'];
    const c = cols[((idx%6)+6)%6];
    ctx.fillStyle = '#14182a';
    ctx.fillRect(x, 168, 64, 16);
    ctx.fillStyle = c;
    ctx.fillRect(x+1, 170, 62, 12);
    // stripe
    ctx.fillStyle = 'rgba(0,0,0,0.25)';
    ctx.fillRect(x+1, 178, 62, 4);
    ctx.fillStyle = 'rgba(255,255,255,0.35)';
    ctx.fillRect(x+1, 170, 62, 1);
  }
}
```

Good.

Now writing everything for real.

For the sky bands, let's do:
```js
const SKY = ['#0a1330','#122048','#1b2e5e','#274177','#35558f','#476da6','#5c88bd','#75a3d2'];
function drawSky(){
  for(let i=0;i<8;i++){
    ctx.fillStyle = SKY[i];
    ctx.fillRect(0, i*9, W, 9);
  }
  // horizon glow
  ctx.fillStyle = '#8fc0e0';
  ctx.fillRect(0, 72, W, 2);
}
```
8 bands * 9 = 72. Good.

Then the sun: a circle at (380, 20) in pale yellow. Let's draw a pixel circle.

```js
function circle(cx,cy,r,col){
  ctx.fillStyle=col;
  for(let y=-r;y<=r;y++){
    const w = Math.floor(Math.sqrt(r*r-y*y));
    ctx.fillRect(cx-w, cy+y, w*2+1, 1);
  }
}
```

Good.

Let me write the final code.

I'll be careful with the order of definitions (function declarations are hoisted, so it's fine).

Writing now.

For the "GO!" text in the ready state, let's show "GO!" big in the center for the first 0.7s.

Hmm, actually let's show "READY" then "GO". Nah, just "GO!".

Let me write out everything.

One last thing: the initial camera. startAttempt sets G.camX = -140. Then the athlete at x=0 appears at screen x=140. Good.

Writing the final answer now.

Actually, let me reconsider the `drawText` uppercase conversion — I should support lowercase by converting. Yes, `String(str).toUpperCase()`.

OK.

Let me write out the complete file.

Regarding `G.lastSide` — I need to reset it at the start of each attempt.

Also, the AI needs to reset aiTimer/aiSide per attempt.

Let me write.

Also, one thing: when autoplay is on and the state is 'ready', the AI shouldn't press. The 'ready' state lasts 0.7s.

Let me make sure the AI doesn't jump during 'ready'.

OK. Writing.

Also I want to add a subtle "speed lines" effect when running fast. Skip.

Let me write the final code.

Final check on the measurement: `G.dist = (landingX - BOARD_X)/PPM`. If the athlete takes off at BOARD_X - 6 and lands at BOARD_X + 8.5*18 = BOARD_X+153, then d = 153/18 = 8.5m. Correct — the measurement is from the board, not from the takeoff point. 

Now writing.

Let me make sure `toFixed(1)` is used everywhere for distances.

Writing the file now. I'll aim for completeness and correctness.

Let me write out `updateParticles`:
```js
function updateParticles(dt){
  for(let i=G.particles.length-1;i>=0;i--){
    const p = G.particles[i];
    p.vy += 620*dt;
    p.x += p.vx*dt;
    p.y += p.vy*dt;
    p.life -= dt;
    if(p.life <= 0 || p.y > 280) G.particles.splice(i,1);
  }
}
```

And drawing:
```js
function drawParticles(){
  for(const p of G.particles){
    const a = Math.min(1, p.life*3);
    ctx.globalAlpha = a;
    ctx.fillStyle = p.c;
    ctx.fillRect(Math.round(p.x - G.camX), Math.round(p.y), p.s, p.s);
  }
  ctx.globalAlpha = 1;
}
```

Good.

Now, writing the whole thing.

Let me count the code size — it'll be maybe 1200 lines. That's fine.

Let me write it.

For the HUD "LAST" and "BEST" during the first attempt, show "--".

OK. Writing.

Let me write the file.

Wait — one issue with the AI: `pressRun` is called with G.aiSide, and it checks `side === G.lastSide`. The AI alternates, so fine. But if the player toggles autoplay off mid-run and presses, there could be a conflict. Not a problem.

Also, the AI must not be blocked by `G.autoplay` being false. `aiRun` is only called when autoplay is true.

OK.

Writing now for real.

Let me handle the "forced foul jump" — when the athlete crosses the board without jumping. `if(G.x > BOARD_X + 1 && G.state==='run') doJump(true)`. But doJump checks `G.state !== 'run'` → returns. Fine, it's in the run state.

Hmm, but doJump(true) sets foul=true. And the athlete is already past the board. The jump will happen from x > BOARD_X. Then the landing is way past. The distance is 0 due to the foul. Good.

Actually, we want the athlete to visibly run past the board into the pit and then it's a foul. Let's trigger at x > BOARD_X + 6 so it looks like they crossed.

Hmm, but then they'd be running on the sand. Whatever. Let's trigger at BOARD_X + 2.

OK, writing.

Let me write the final code now, carefully.

I'll write it in one go.

Note: in `drawWorld`, I need to draw the pit, then the mark, then the WR/best lines.

Let me write.

Also the takeoff board: I want it to look like a proper board. Let's draw:
- The board surface: a light gray/white rect from BOARD_X-20 to BOARD_X, y 200..242.
- A red strip at the front edge: x from BOARD_X-3 to BOARD_X, y 200..242.
- Actually the foul line should be at BOARD_X. Let's draw the red strip at BOARD_X-3..BOARD_X-1 and the white board behind.

Hmm, actually in real long jump, the board is white/light and the foul line is the front edge. Let's draw the board in white with a red front edge.

Fine.

Also add a "plasticine" strip? Nah.

OK writing.

Let me finalize the code.

I'll now produce the complete HTML.

One more: I should make sure the athlete is drawn AFTER the world but BEFORE the HUD.

And the particles after the athlete? The sand puff should be in front. Yes.

OK, writing.

Let me write the code in full.

```js
// ---------- setup ----------
...
// ---------- font ----------
...
// ---------- assets ----------
...
// ---------- game ----------
...
// ---------- render ----------
...
// ---------- loop ----------
```

Writing now.

Actually, for `textOn`, I'll pass the context.

Let me write:

```js
function textOn(g, str, x, y, color, sc){
  sc = sc || 1;
  g.fillStyle = color;
  str = String(str).toUpperCase();
  let cx = Math.round(x);
  const cy = Math.round(y);
  for(let i=0;i<str.length;i++){
    const gl = GLYPHS[str[i]];
    if(gl){
      for(let r=0;r<7;r++){
        const row = gl[r];
        let rs = -1;
        for(let c=0;c<5;c++){
          if(row[c]){ if(rs<0) rs=c; }
          else if(rs>=0){ g.fillRect(cx+rs*sc, cy+r*sc, (c-rs)*sc, sc); rs=-1; }
        }
        if(rs>=0) g.fillRect(cx+rs*sc, cy+r*sc, (5-rs)*sc, sc);
      }
    }
    cx += 6*sc;
  }
}
function drawText(str,x,y,c,sc){ textOn(ctx,str,x,y,c,sc); }
```

Good.

Now writing the whole thing.

For the pit numbers, I'll call textOn(g, String(m), x+2, 35, '#3a2a10', 1).

Hmm, the numbers should be centered on the metre line. x + 2 puts the number starting 2px right of the line. Fine.

OK. Final write.

Let me also handle: the pit canvas height is 44 and it's drawn at y=200, so it covers 200..244.

The tape strip is at local y 33..44 → 233..244.

The numbers at local y 35 → 235.

Good.

Writing.

Actually, I realize the metre lines from local y=4 to y=44 would go through the tape. Let me draw them from y=4 to y=33 only.

OK.

Let me write it all out now.

I'll also add a subtle "shadow" under the athlete on the ground. Skip.

Final: writing the code.

def spawnSand(x, n):
```js
function spawnSand(worldX, n){
  for(let i=0;i<n;i++){
    const a = -Math.PI/2 + (Math.random()-0.5)*2.4;
    const sp = 30 + Math.random()*170;
    G.particles.push({
      x: worldX + (Math.random()-0.5)*10,
      y: GROUND_Y - 2 + Math.random()*4,
      vx: Math.cos(a)*sp*0.9 + (Math.random()-0.3)*40,
      vy: Math.sin(a)*sp,
      life: 0.4 + Math.random()*0.8,
      c: Math.random()<0.5 ? '#e8c87a' : (Math.random()<0.5?'#d4b070':'#f4dc9c'),
      s: Math.random()<0.6 ? 1 : 2
    });
  }
}
```

Good.

Now, writing the final file.

I'm going to write it now, complete.

Let me double check the `lerpPose` when keys have `t`. Yes.

And FLY_KEYS/ LAND_KEYS have `t` as the first property. `for(const k in a) if(k!=='t')` — good.

Writing.

Let me write out the final code.

Also need `STAND_POSE`.

OK here goes.

For the HUD speed bar segments, let me draw vertical dividers every 10%.

Let me write the HUD.

Also, I want a "takeoff zone" indicator on the runway — maybe a marker showing the last few metres before the board. Let's draw a subtle "TAKEOFF ZONE" marker on the track from BOARD_X - 3m to BOARD_X. Hmm, might be confusing.

Let's skip.

Writing now.

Actually, let me add a small detail: the athlete's shadow on the ground. It helps ground the character. A dark ellipse under the athlete, shrinking with height.

```js
// shadow
const shX = G.x - G.camX;
const shY = GROUND_Y + 2;
const sc = 1 - Math.min(0.6, G.hm*0.2);
ctx.fillStyle='rgba(0,0,0,0.25)';
ctx.fillRect(Math.round(shX-5*sc), shY, Math.round(10*sc), 2);
```

Hmm, for the replay I need the frame's x and hm. Fine.

OK. Writing the final code.

Let me write it out.

I'll include the shadow inside renderAthlete.

Writing.

Final answer time. Let me carefully produce the code.

(Also: I should call `startAttempt()` at the very beginning.)

Let me write.

For the `over` state, after 6 seconds, restart.

Alright.

Writing the final code now — for real this time.

Let me be careful with the `drawWavers` and `drawFlags` calls: they need the parallax offset.

`const par = wrap(G.camX*0.12, 480);`

OK.

Writing.