Need SVG 800x600. Pelican riding bicycle: blue pelican, large beak, wings, tail feathers, feet on pedals. Bicycle: two wheels, frame, pedals, handlebars, red bike. Use path, circle, rect, gradients, opacity.

Let me design coordinates. Ground at y=500. Wheels: rear wheel center (220,470), front wheel center (580,470), radius 80. Frame: bottom bracket at (400,470). Seat tube from (400,470) to (360,340). Down tube from (400,470) to (540,360). Top tube from (360,340) to (540,350). Fork from (540,350) to (580,470). Chainstay from (220,470) to (400,470). Seatstay from (220,470) to (360,340). Handlebars at (540,330): stem, bar.

Pedal cranks at (400,470), crank length ~35. One pedal at (400+30,470+20)? Let's do pedal 1 at (425,495), pedal 2 at (375,445) (opposite). Pelican feet on pedals: pelican body above, legs from body to pedals.

Pelican: body ellipse around (330,300)? Sits on saddle at (350,330). Body: big blob path from ~ (230,300) to (420,280), tail feathers on left extending to (150,260) with feather lines. Wing on side of body. Neck: curve from top of body (400,280) to head (500,180). Head is circle at (505,175) radius 28. Beak: big pouch shape extending forward/down from (520,175) to (640,210), lower pouch path. Eye at (510,165).

Wing: path over body, maybe partially raised. Feet: legs from bottom of body (360,340) down to pedals.

Draw order: wheels (tires, rim, spokes, hub), frame (red), pedals, legs, body, wing, tail, neck, head, beak, eye.

Let me make red gradient, blue gradient.

Write code block.

Beak: top mandible path M515,160 L650,185 L645,195 L520,180 Z; pouch: M520,180 C560,240 620,230 645,195 L640,190 C600,215 560,215 525,182 Z approximately. Keep simple.

Tail feathers: 3 pointed shapes from (240,290) toward (140,250),(150,280),(150,300).

Pedal cranks: circle at (400,470) radius 10 (chainring), crank line to pedals.

Handlebars: line from (540,350) to (535,315), then bar path curve to (505,305), maybe with grips.

Let me just write the SVG.
