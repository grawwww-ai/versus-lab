```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Track &amp; Field — Long Jump</title>
<style>
  html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#101725}
  body{display:grid;place-items:center}
  canvas{width:min(100vw,177.78vh);height:min(100vh,56.25vw);image-rendering:pixelated;image-rendering:crisp-edges;display:block}
</style>
</head>
<body>
<canvas id="game" width="640" height="360" aria-label="Track and Field long jump game"></canvas>
<script>
(() => {
"use strict";
const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");
ctx.imageSmoothingEnabled = false;

const W=640,H=360, BOARD=350, GROUND=252, PX_PER_M=20, WR=8.95;
const keys=new Set();
let state="title", stateTime=0, frame=0, demo=true, titleTime=0;
let attempt=1, marks=[null,null,null], best=0, power=12, lastTap="", runnerX=72;
let angle=24, lockedAngle=24, angleClock=0, runFrames=0, footY=GROUND;
let vx=0,vy=0,flightFrames=0,flightLog=[], replayPos=0, landingX=0, foul=false;
let particles=[], crowdShift=0, nextTap=0, matchTimer=0, resultTimer=0;
let flash=0, message="", messageTime=0;

const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const rect=(x,y,w,h,c)=>{ctx.fillStyle=c;ctx.fillRect(Math.round(x),Math.round(y),Math.round(w),Math.round(h));};
const line=(x1,y1,x2,y2,c,width=1)=>{ctx.strokeStyle=c;ctx.lineWidth=width;ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke();};
const text=(s,x,y,size=10,color="#fff",align="left")=>{
  ctx.font=`bold ${size}px monospace`;ctx.textAlign=align;ctx.textBaseline="top";
  ctx.fillStyle="#101725";ctx.fillText(s,x+1,y+1);
  ctx.fillStyle=color;ctx.fillText(s,x,y);
};
function panel(x,y,w,h,fill="#101c30",edge="#75dcf1"){
  rect(x,y,w,h,edge);rect(x+1,y+1,w-2,h-2,"#07111f");rect(x+3,y+3,w-6,h-6,fill);
}
function hash(n){let x=Math.sin(n*127.1+311.7)*43758.5453;return x-Math.floor(x);}
function startMatch(){
  attempt=1;marks=[null,null,null];best=0;matchTimer=0;startAttempt();
}
function startAttempt(){
  state="run";stateTime=0;runFrames=0;runnerX=72;footY=GROUND;power=12;lastTap="";
  angleClock=Math.random()*70;angle=24;lockedAngle=24;nextTap=0;flightLog=[];particles=[];
  foul=false;flash=0;message="ALTERNATE LEFT / RIGHT";messageTime=1.5;
}
function addTap(which){
  if(state!=="run"||demo)return;
  if(which===lastTap)return;
  lastTap=which;power=clamp(power+13,0,100);
  flash=.12;
}
function launch(){
  if(state!=="run")return;
  lockedAngle=angle;
  if(runnerX>BOARD){doFoul();return;}
  state="flight";stateTime=0;flightFrames=0;flightLog=[];
  const p=power/100;
  vx=2.75+p*.72;
  vy=-(5.05+lockedAngle*.034);
  footY=GROUND;
  message="";messageTime=0;
}
function doFoul(){
  state="mark";stateTime=0;foul=true;landingX=BOARD;
  marks[attempt-1]=null;message="FOUL — TAKE-OFF PAST THE BOARD";messageTime=1.1;
}
function land(){
  footY=GROUND;landingX=clamp(runnerX,BOARD+8,620);
  const dist=Math.max(0,(landingX-BOARD)/PX_PER_M);
  marks[attempt-1]=dist;best=Math.max(best,dist);
  state="replay";stateTime=0;replayPos=0;
  for(let i=0;i<18;i++){
    particles.push({x:landingX+(Math.random()-.5)*12,y:GROUND-2-Math.random()*4,
      vx:(Math.random()-.5)*2.6,vy:-Math.random()*2.4-0.3,life:.6+Math.random()*.6});
  }
}
function finishAttempt(){
  if(attempt<3){attempt++;startAttempt();}
  else{state="results";stateTime=0;resultTimer=0;}
}
function keyDown(e){
  const k=e.key.toLowerCase();
  if(["arrowleft","arrowright"," ","arrowup","arrowdown"].includes(k))e.preventDefault();
  if(keys.has(k))return;keys.add(k);
  if(k==="p"){
    demo=!demo;
    if(demo&&(state==="title"||state==="results"))startMatch();
    message=demo?"AUTOPLAY DEMO: ON":"AUTOPLAY DEMO: OFF";messageTime=1.25;
  }
  if(k==="enter"){
    if(state==="title"||state==="results")startMatch();
    else if(state==="mark")finishAttempt();
  }
  if(k==="a"||k==="arrowleft")addTap("L");
  if(k==="d"||k==="arrowright")addTap("R");
  if((k===" "||k==="arrowup")&&state==="run"&&!demo)launch();
}
function keyUp(e){keys.delete(e.key.toLowerCase());}
window.addEventListener("keydown",keyDown);
window.addEventListener("keyup",keyUp);

function update(dt){
  const f=dt*60;frame+=f;crowdShift+=f;stateTime+=dt;
  if(messageTime>0)messageTime-=dt;
  if(state==="title"){
    titleTime+=dt;
    if(demo&&titleTime>1.7)startMatch();
  }else if(state==="run"){
    runFrames+=f;angleClock+=f;
    angle=12+28*(.5+.5*Math.sin(angleClock*.045));
    power=Math.max(0,power-.045*f);
    if(demo){
      // AI builds a strong alternating cadence, then times a clean takeoff.
      if(runFrames>=nextTap){power=clamp(power+10,0,100);nextTap=runFrames+7.3;}
      const near=runnerX>=BOARD-12;
      if(near){
        runnerX=Math.min(runnerX,BOARD-5);
        if(angle>=19&&angle<=30)launch();
        else if(runFrames>170){angle=24;launch();}
      }else{
        runnerX+= (1.55+power*.0205)*f;
      }
    }else{
      runnerX+=(1.55+power*.0205)*f;
      if(runnerX>BOARD){runnerX=BOARD+1;doFoul();}
    }
  }else if(state==="flight"){
    flightFrames+=f;
    runnerX+=vx*f;footY+=vy*f;vy+=.235*f;
    flightLog.push({x:runnerX,y:footY,frame:flightFrames});
    if(footY>=GROUND&&vy>0)land();
  }else if(state==="replay"){
    replayPos+=f*.56;
    particles.forEach(p=>{p.x+=p.vx*f;p.y+=p.vy*f;p.vy+=.12*f;p.life-=dt;});
    particles=particles.filter(p=>p.life>0);
    if(replayPos>=flightLog.length){state="mark";stateTime=0;}
  }else if(state==="mark"){
    particles.forEach(p=>{p.x+=p.vx*f;p.y+=p.vy*f;p.vy+=.12*f;p.life-=dt;});
    particles=particles.filter(p=>p.life>0);
    if(stateTime>1.65)finishAttempt();
  }else if(state==="results"){
    resultTimer+=dt;
    if(demo&&resultTimer>5.2)startMatch();
  }
}

function drawSky(){
  const sky=["#55c9f4","#78d9f4","#a4e8f4","#d4f3ef"];
  sky.forEach((c,i)=>rect(0,i*24,W,24,c));
  // drifting blocky clouds
  for(let i=0;i<5;i++){
    const x=((i*151-frame*.22)%(W+100)+W+100)%(W+100)-45;
    const y=24+(i%3)*20;
    rect(x+8,y,32,6,"#f4ffff");rect(x,y+6,48,8,"#f4ffff");
    rect(x+5,y+14,34,3,"#d4f4f4");rect(x+13,y-3,18,5,"#f4ffff");
  }
  // distant skyline and stadium roof
  rect(0,86,W,9,"#eaf8ee");rect(0,95,W,10,"#536b81");
  rect(0,99,W,4,"#283d56");
  for(let x=0;x<W;x+=32){
    rect(x,91,18,4,"#6b8093");
    rect(x+19,88,4,10,"#e5f2ec");
  }
  // grandstand tiers
  rect(0,103,W,116,"#243953");
  for(let row=0;row<7;row++){
    const y=108+row*15;
    rect(0,y,W,2,row%2?"#3a526b":"#425a72");
    for(let col=0;col<80;col++){
      const x=col*9+((row%2)*4);
      const r=hash(row*200+col);
      const colors=["#ffd462","#f45d65","#f4f1dd","#50d4c2","#72a7f3","#e99bdb","#f08d4c"];
      const c=colors[Math.floor(r*colors.length)];
      const bob=Math.sin(frame*.12+col*.73+row)*1.8;
      rect(x,y+4+bob,5,5,c);
      rect(x+1,y+1+bob,3,3,"#f4c7a4");
      if((col+row)%4===0)line(x+2,y+7+bob,x-1,y+3+bob,c,2);
      else if((col+row)%4===2)line(x+4,y+7+bob,x+7,y+3+bob,c,2);
    }
  }
  // stadium banners
  rect(0,211,W,8,"#132a3d");rect(0,215,W,3,"#e9c84f");
  for(let x=12;x<W;x+=78){
    rect(x,195,59,13,"#087b84");
    text(["GO!","JUMP","TRACK","FIELD"][Math.floor(x/78)%4],x+29,197,8,"#fff","center");
  }
}
function drawFlag(x,y,color,phase){
  rect(x,y,2,46,"#e8ecdf");rect(x-2,y+44,6,3,"#9c6748");
  const wave=Math.sin(frame*.12+phase)*3;
  ctx.fillStyle=color;ctx.beginPath();ctx.moveTo(x+2,y+2);ctx.lineTo(x+24+wave,y+7);ctx.lineTo(x+2,y+14);ctx.closePath();ctx.fill();
  rect(x+4,y+6,11,2,"#fff1bb");
}
function drawTrack(){
  rect(0,219,W,22,"#418b4b");
  rect(0,238,W,5,"#27663b");
  // runway and pit
  rect(0,243,363,34,"#c64e52");
  rect(0,243,363,4,"#f07c68");
  for(let x=-20;x<363;x+=26)rect(x,249,18,2,"#d96960");
  rect(0,274,363,4,"#9c3b48");
  rect(363,245,257,48,"#d9b66d");
  rect(363,245,257,5,"#f2d28b");
  for(let i=0;i<120;i++){
    const x=367+hash(i+8)*249,y=252+hash(i+400)*38;
    rect(x,y,2,1,i%3===0?"#c49c55":"#ead08e");
  }
  // foul board and takeoff stripe
  rect(BOARD-3,238,7,6,"#fff4bf");
  rect(BOARD-2,239,5,4,"#ed4b54");
  rect(BOARD,244,2,31,"#f7f2d5");
  text("FOUL LINE",BOARD-13,224,6,"#fff7dc","center");
  // pit retaining wall
  rect(363,293,257,5,"#9a7449");rect(363,298,257,3,"#644d3b");
  // record line across pit
  const wrx=BOARD+WR*PX_PER_M;
  line(wrx,244,wrx,290,"#e8494e",2);
  for(let y=247;y<290;y+=8)rect(wrx-3,y,7,2,"#fff0cc");
  rect(wrx-29,229,59,13,"#a52c38");
  text("WORLD RECORD",wrx,231,7,"#fff","center");
  // best mark / current mark
  if(best>0){
    const bx=BOARD+best*PX_PER_M;
    rect(bx-1,249,2,41,"#63ecda");
    rect(bx-5,248,10,3,"#63ecda");
  }
  if((state==="replay"||state==="mark"||state==="results")&&!foul&&marks[attempt-1]!=null){
    const mx=BOARD+marks[attempt-1]*PX_PER_M;
    rect(mx-2,258,4,23,"#684d34");rect(mx-4,258,8,2,"#fff1bc");
  }
  // measuring tape and yard lines
  rect(363,303,257,22,"#ead28e");
  rect(363,303,257,2,"#fff0bd");
  for(let m=0;m<=12;m++){
    const x=BOARD+m*PX_PER_M;
    if(x>618)continue;
    const major=m%2===0;
    rect(x,304,major?2:1,major?14:8,"#594d39");
    if(major)text(String(m),x,317,7,"#493d30","center");
  }
  text("MEASURE • METRES",491,330,7,"#c9dddf","center");
  rect(0,299,363,30,"#9d3946");
  text("LONG JUMP  /  RUNWAY",181,308,8,"#ffe3b1","center");
  // foreground edge
  rect(0,333,W,27,"#111b2a");rect(0,333,W,2,"#536b77");
}
function drawAthlete(x,y,pose="run",phase=frame,lean=0){
  // Pixel-block sprite, anchored at the feet.  Shoes and limbs animate independently.
  ctx.save();ctx.translate(Math.round(x),Math.round(y));
  const bob=pose==="run"?Math.max(0,Math.sin(phase*.48))*2:0;
  const tilt=pose==="run"?lean:0;
  ctx.translate(0,-bob);ctx.rotate(tilt);
  const skin="#f0b27d",shirt="#efcf37",shorts="#3154a0",shoe="#f5eee0";
  // trailing shadow
  ctx.restore();
  if(pose==="run"||pose==="land") {
    ctx.save();ctx.globalAlpha=.24;rect(x-11,y-1,22,3,"#302a2a");ctx.restore();
  }
  ctx.save();ctx.translate(Math.round(x),Math.round(y-bob));ctx.rotate(tilt);
  if(pose==="run"){
    const s=Math.sin(phase*.48),c=Math.cos(phase*.48);
    // legs
    line(-2,-10,-5+s*7,-4,skin,4);line(-5+s*7,-4,-8+s*12,0,skin,4);
    line(2,-10,5-s*7,-5,skin,4);line(5-s*7,-5,7-s*12,0,skin,4);
    line(-8+s*12,0,-4+s*12,0,shoe,3);line(7-s*12,0,11-s*12,0,shoe,3);
    // arms
    line(-3,-22,-7-c*5,-17,skin,3);line(-7-c*5,-17,-5-c*8,-13,skin,3);
    line(3,-22,7+c*5,-18,skin,3);line(7+c*5,-18,9+c*8,-21,skin,3);
    rect(-5,-24,10,13,shirt);rect(-5,-13,10,5,shorts);
    rect(-4,-34,9,9,skin);rect(-5,-36,10,4,"#342b2a");rect(3,-31,2,2,"#252532");
    rect(-6,-25,12,3,"#ffe76b");
  }else if(pose==="flight"){
    // compact airborne tuck, arms forward
    line(-2,-10,3,-5,skin,4);line(3,-5,8,-8,skin,4);
    line(2,-10,7,-7,skin,4);line(7,-7,10,-10,skin,4);
    line(-8,-23,-12,-28,skin,3);line(-12,-28,-8,-31,skin,3);
    line(7,-23,12,-27,skin,3);line(12,-27,15,-25,skin,3);
    rect(-5,-24,11,13,shirt);rect(-5,-13,10,5,shorts);
    rect(-4,-34,9,9,skin);rect(-5,-36,10,4,"#342b2a");rect(3,-31,2,2,"#252532");
    rect(-6,-25,12,3,"#ffe76b");
  }else{
    // landing / recovered pose
    line(-2,-10,-9,-5,skin,4);line(-9,-5,-14,-4,skin,4);
    line(2,-10,9,-6,skin,4);line(9,-6,14,-5,skin,4);
    line(-14,-4,-9,-3,shoe,3);line(14,-5,19,-4,shoe,3);
    line(-4,-22,-10,-28,skin,3);line(4,-22,10,-27,skin,3);
    rect(-5,-24,10,13,shirt);rect(-5,-13,10,5,shorts);
    rect(-4,-34,9,9,skin);rect(-5,-36,10,4,"#342b2a");rect(3,-31,2,2,"#252532");
    rect(-6,-25,12,3,"#ffe76b");
  }
  ctx.restore();
}
function drawHUD(){
  rect(0,0,W,78,"#101c30");rect(0,76,W,3,"#e2bd4f");
  text("TRACK & FIELD",12,7,12,"#f7d34d");
  text("LONG JUMP",13,24,8,"#dff6f4");
  for(let i=0;i<3;i++){
    const x=13+i*32;
    panel(x,41,27,22,i+1===attempt?"#74452e":"#1c2d43",i+1===attempt?"#ffd453":"#546b7a");
    text(String(i+1),x+13,46,10,i+1===attempt?"#ffe36a":"#9fb3bc","center");
    if(marks[i]!=null)text(marks[i].toFixed(1),x+13,57,6,"#e7f4dd","center");
    else if(i+1<attempt)text("FOUL",x+13,57,5,"#ff7878","center");
  }
  text(demo?"DEMO  [P]":"PLAYER  [P: DEMO]",112,49,7,demo?"#70f0d2":"#d4e7e9");
  // speed meter
  panel(208,10,143,55,"#172b41","#648292");
  text("RUN SPEED",216,15,8,"#d8edf0");
  text(String(Math.round(power)).padStart(3,"0")+"%",342,15,8,"#ffdc63","right");
  rect(218,31,123,12,"#070e18");
  for(let i=0;i<10;i++)rect(220+i*12,33,9,8,(power>(i+1)*10)?"#f4c943":"#28384a");
  text("A / ←",218,48,7,"#d9eef0");text("ALTERNATE",280,48,7,"#ffffff","center");text("D / →",340,48,7,"#d9eef0","right");
  // angle selector
  panel(358,10,112,55,"#172b41","#648292");
  text("TAKE-OFF",366,15,8,"#d8edf0");text("ANGLE",366,26,7,"#91aab5");
  text(`${Math.round(state==="flight"||state==="replay"||state==="mark"?lockedAngle:angle)}°`,456,17,14,"#ffdc63","right");
  rect(367,46,91,4,"#08121e");
  for(let a=10;a<=45;a+=5){
    let xx=367+(a-10)/35*91;rect(xx,44,1,8,"#90a8ad");
  }
  let shown=state==="flight"||state==="replay"||state==="mark"?lockedAngle:angle;
  let needle=367+(shown-10)/35*91;rect(needle-2,42,5,12,"#ffdf5a");
  // scoreboard
  panel(480,8,148,59,"#17283b","#d4b448");
  text("OLYMPIC STADIUM",554,13,8,"#f6d65c","center");
  text("BEST",490,29,7,"#a8c1ca");text(best?best.toFixed(1)+" m":"— —",621,27,12,"#fff4d1","right");
  text("WORLD  8.95 m",554,48,8,"#ff8582","center");
  // prompts / transient message
  if(state==="run"){
    const prompt=demo?"AUTOPILOT • TIMING TAKE-OFF":"SPACE / ↑  JUMP AT THE BOARD";
    text(prompt,320,82,8,demo?"#f9df7a":"#ffffff","center");
  }
  if(messageTime>0&&message){
    panel(169,92,302,24,"#26354a","#ffdf65");
    text(message,320,99,9,"#fff4c2","center");
  }
  if(state==="replay"){
    panel(241,88,158,23,"#762b39","#ffdd56");
    text("◀  SLOW-MO REPLAY  ▶",320,95,9,"#fff4d1","center");
  }
}
function drawTapeReadout(){
  if((state==="replay"||state==="mark"||state==="results")&&!foul&&marks[attempt-1]!=null){
    const d=marks[attempt-1],x=BOARD+d*PX_PER_M;
    panel(446,277,160,23,"#17283b","#f0ce55");
    text(`JUMP  ${d.toFixed(1)} m`,526,284,11,"#fff1b2","center");
    line(BOARD,270,x,270,"#fff4c1",1);
  }
}
function drawParticles(){
  particles.forEach(p=>{rect(p.x,p.y,3,3,p.life>.25?"#fff1bf":"#e0c27f");});
}
function drawTitle(){
  rect(0,0,W,H,"#07111e");drawSky();drawTrack();drawFlag(78,129,"#f4c83d",1);drawFlag(581,128,"#e7525d",2);
  panel(94,69,452,208,"#132a3e","#f3cc4e");
  text("TRACK & FIELD",320,91,22,"#ffdb51","center");
  text("LONG JUMP",320,121,14,"#e9fbf1","center");
  rect(156,145,328,2,"#5a8890");
  drawAthlete(214,222,"run",frame,0);
  text("ALTERNATE KEYS TO BUILD SPEED",343,159,9,"#d6e9e7","center");
  text("A / ←   THEN   D / →",343,176,11,"#ffdf66","center");
  text("TIME YOUR JUMP AT THE BOARD",343,198,9,"#d6e9e7","center");
  text("SPACE / ↑  •  THREE ATTEMPTS",343,214,9,"#d6e9e7","center");
  text("P  TO TOGGLE AUTOPLAY DEMO",320,244,9,"#75f1d1","center");
  text("DEMO STARTING…",320,292,8,"#ffffff","center");
}
function drawResults(){
  rect(0,0,W,H,"#0a1422");
  drawSky();drawTrack();
  panel(105,48,430,265,"#142b40","#f1cd50");
  text("EVENT RESULTS",320,64,18,"#ffdd5c","center");
  text("MEN'S LONG JUMP",320,89,9,"#d2e9e9","center");
  line(137,106,503,106,"#66838c",1);
  for(let i=0;i<3;i++){
    const y=120+i*35;
    text(`ATTEMPT ${i+1}`,151,y,9,"#c1d4d8");
    const val=marks[i]==null?"FOUL":marks[i].toFixed(1)+" m";
    text(val,476,y,11,marks[i]==null?"#ff8582":"#fff0b8","right");
    if(marks[i]!=null&&marks[i]===best)text("BEST",492,y+2,7,"#70eed2");
  }
  rect(143,228,354,2,"#66838c");
  text("PERSONAL BEST",204,244,9,"#c1d4d8");
  text(best?best.toFixed(1)+" m":"NO MARK",454,239,16,"#ffe15d","right");
  text("WORLD RECORD   8.95 m",320,270,9,"#ff8582","center");
  text(demo?"NEXT DEMO IN A MOMENT":"ENTER TO PLAY   •   P TO TOGGLE DEMO",320,294,8,"#ffffff","center");
}
function render(){
  if(state==="title"){drawTitle();return;}
  if(state==="results"){drawResults();return;}
  drawSky();
  drawFlag(67,132,"#f4c83d",1);drawFlag(596,128,"#ec5659",3);
  drawTrack();
  drawHUD();
  // Replay uses recorded positions; otherwise draw the live athlete.
  if(state==="replay"&&flightLog.length){
    const i=Math.min(flightLog.length-1,Math.floor(replayPos));
    const p=flightLog[i];drawAthlete(p.x,p.y,"flight",p.frame,0);
    // faint ghost trail
    if(i>7){const q=flightLog[i-7];ctx.save();ctx.globalAlpha=.19;drawAthlete(q.x,q.y,"flight",q.frame,0);ctx.restore();}
  }else if(state==="flight"){
    drawAthlete(runnerX,footY,"flight",frame,0);
  }else if(state==="mark"&&!foul){
    drawAthlete(landingX,GROUND,"land",frame,0);
  }else if(state==="run"){
    const lean=clamp((1.55+power*.0205)*.055,-.1,.2);
    drawAthlete(runnerX,GROUND,"run",frame,lean);
  }
  drawParticles();
  drawTapeReadout();
  if(state==="mark"&&foul){
    panel(174,128,292,55,"#752d38","#ffd24d");
    text("FOUL",320,136,17,"#fff0a4","center");
    text("TAKE-OFF FOOT CROSSED THE LINE",320,160,8,"#fff","center");
  }
  if(state==="mark"&&!foul&&marks[attempt-1]!=null){
    panel(205,111,230,34,"#183345","#79ead0");
    text(`MEASURED  ${marks[attempt-1].toFixed(1)} m`,320,121,12,"#fff2ba","center");
  }
  if(state==="results")drawResults();
}
let last=performance.now();
function loop(now){
  const dt=Math.min(.04,(now-last)/1000);last=now;
  update(dt);render();requestAnimationFrame(loop);
}
requestAnimationFrame(loop);
})();
</script>
</body>
</html>
```