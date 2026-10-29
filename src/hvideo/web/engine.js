import * as THREE from 'three';
import {EffectComposer} from 'three/addons/postprocessing/EffectComposer.js';
import {RenderPass} from 'three/addons/postprocessing/RenderPass.js';
import {UnrealBloomPass} from 'three/addons/postprocessing/UnrealBloomPass.js';
import {OutputPass} from 'three/addons/postprocessing/OutputPass.js';

const config = await (await fetch('./config.json')).json();
await document.fonts.load('32px HNova');
const {width:W,height:H,duration:D} = config.video;
const settings=config.renderer || {};
const renderer = new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true,powerPreference:'high-performance'});
renderer.setPixelRatio(1);
renderer.setSize(W,H);
renderer.toneMapping=THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure=settings.exposure ?? 1.1;
const output=document.createElement('canvas');
output.width=W; output.height=H; document.body.append(output);
const ctx=output.getContext('2d');
const composer=new EffectComposer(renderer);
const renderPass=new RenderPass(new THREE.Scene(),new THREE.PerspectiveCamera());
composer.addPass(renderPass);
const bloom=new UnrealBloomPass(new THREE.Vector2(W,H),settings.bloom_strength ?? .65,.45,.78);
bloom.enabled=settings.bloom !== false;
composer.addPass(bloom);
composer.addPass(new OutputPass());

function random(seed) {
  let state=seed>>>0;
  return ()=>{state=(Math.imul(1664525,state)+1013904223)>>>0; return state/4294967296;};
}
const smooth=(a,b,t)=>{if(b<=a)return t>=b?1:0;const x=THREE.MathUtils.clamp((t-a)/(b-a),0,1);return x*x*(3-2*x);};
const vec=a=>new THREE.Vector3(...a);
function stars(scene,rng,n=1600,radius=130) {
  const positions=[],colors=[];
  for(let i=0;i<n;i++) {
    const az=rng()*Math.PI*2, y=rng()*2-1, r=radius*(.65+rng()*.35);
    positions.push(Math.cos(az)*Math.sqrt(1-y*y)*r,y*r,Math.sin(az)*Math.sqrt(1-y*y)*r);
    const b=.5+rng()*.8; colors.push(b*.7,b*.85,b);
  }
  const g=new THREE.BufferGeometry();
  g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
  g.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));
  const points=new THREE.Points(g,new THREE.PointsMaterial({size:.22,vertexColors:true,transparent:true,opacity:.9,sizeAttenuation:true}));
  scene.add(points); return points;
}
function neon(color,intensity=2) {return new THREE.MeshBasicMaterial({color:new THREE.Color(color).multiplyScalar(intensity)});}
function ring(scene,radius,z,color=0x43dfff) {
  const mesh=new THREE.Mesh(new THREE.TorusGeometry(radius,.035,8,120),neon(color,2));
  mesh.position.z=z;scene.add(mesh);return mesh;
}

function flight(s,rng) {
  const scene=new THREE.Scene();scene.background=new THREE.Color(0x01030b);
  scene.fog=new THREE.FogExp2(0x030817,.008);
  stars(scene,rng,s.star_count ?? 1800);
  const g=new THREE.BufferGeometry(), lines=[];
  for(let i=0;i<600;i++) {
    const a=rng()*Math.PI*2,r=3+rng()*38,z=-110+rng()*140;
    const x=Math.cos(a)*r,y=Math.sin(a)*r;
    lines.push(x,y,z,x,y,z+.3+rng()*1.5);
  }
  g.setAttribute('position',new THREE.Float32BufferAttribute(lines,3));
  const trails=new THREE.LineSegments(g,new THREE.LineBasicMaterial({color:0x65a7e0,transparent:true,opacity:.55}));
  scene.add(trails);
  const rings=[];
  for(let i=0;i<7;i++) rings.push(ring(scene,7.5+i*.4,6-i*16,i%2?0x8d68ff:0x3cceff));
  // Layered, slowly rotating wireframe structures make depth visible even at low speed.
  const shell=new THREE.Mesh(new THREE.IcosahedronGeometry(12,1),new THREE.MeshBasicMaterial({color:0x184279,wireframe:true,transparent:true,opacity:.22}));
  shell.position.z=-62;scene.add(shell);
  return {scene,defaults:{from:[0,1,25],to:[1,-.3,-35],look_at:[0,0,-80]},update:(t,u)=>{
    trails.position.z=t*.3;
    rings.forEach((r,i)=>{r.rotation.z=t*.08*(i%2?1:-1);r.rotation.y=Math.sin(t*.22+i)*.08;});
    shell.rotation.set(t*.06,t*.09,.1);
  }};
}

const planetVertex=`varying vec3 vPos;varying vec3 vNormal;varying vec3 vWorld;
void main(){vPos=position;vNormal=normalize(mat3(modelMatrix)*normal);vec4 w=modelMatrix*vec4(position,1.);vWorld=w.xyz;gl_Position=projectionMatrix*viewMatrix*w;}`;
const planetFragment=`precision highp float;
varying vec3 vPos;varying vec3 vNormal;varying vec3 vWorld;
float hash(vec3 p){p=fract(p*.3183099+vec3(.1,.2,.3));p*=17.;return fract(p.x*p.y*p.z*(p.x+p.y+p.z));}
float noise(vec3 p){vec3 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);
return mix(mix(mix(hash(i),hash(i+vec3(1,0,0)),f.x),mix(hash(i+vec3(0,1,0)),hash(i+vec3(1,1,0)),f.x),f.y),mix(mix(hash(i+vec3(0,0,1)),hash(i+vec3(1,0,1)),f.x),mix(hash(i+vec3(0,1,1)),hash(i+vec3(1,1,1)),f.x),f.y),f.z);}
float fbm(vec3 p){float v=0.,a=.5;for(int i=0;i<5;i++){v+=a*noise(p);p=p*2.03+11.7;a*=.5;}return v;}
void main(){vec3 p=normalize(vPos);float terrain=fbm(p*3.8+2.1);float land=smoothstep(.48,.55,terrain);
vec3 sea=mix(vec3(.008,.035,.10),vec3(.02,.22,.31),terrain);
vec3 ground=mix(vec3(.025,.16,.11),vec3(.33,.37,.23),smoothstep(.53,.75,terrain));
vec3 col=mix(sea,ground,land);float ice=smoothstep(.77,.96,abs(p.y)+terrain*.15);col=mix(col,vec3(.6,.78,.84),ice);
float cloud=smoothstep(.60,.77,fbm(p*7.+13.));col=mix(col,vec3(.68,.81,.88),cloud*.75);
vec3 n=normalize(vNormal),l=normalize(vec3(-.7,.5,1.));float day=max(dot(n,l),0.);
float lights=step(.91,hash(floor(p*290.)))*land*(1.-smoothstep(0.,.25,day));
vec3 viewDir=normalize(cameraPosition-vWorld);float rim=pow(1.-max(dot(n,viewDir),0.),3.);
col=col*(.065+day*1.25)+vec3(1.,.56,.15)*lights*.75+vec3(.06,.32,.65)*rim*.55;
gl_FragColor=vec4(col,1.);}`;

function orbit(s,rng) {
  const scene=new THREE.Scene();scene.background=new THREE.Color(0x02040e);
  stars(scene,rng,s.star_count ?? 2200,110);
  const group=new THREE.Group();group.rotation.z=.19;scene.add(group);
  const globe=new THREE.Mesh(new THREE.SphereGeometry(3.8,96,64),new THREE.ShaderMaterial({vertexShader:planetVertex,fragmentShader:planetFragment}));
  group.add(globe);
  const atmo=new THREE.Mesh(new THREE.SphereGeometry(3.94,64,48),new THREE.ShaderMaterial({
    side:THREE.BackSide,transparent:true,depthWrite:false,blending:THREE.AdditiveBlending,
    vertexShader:`varying vec3 n;varying vec3 v;void main(){vec4 p=modelViewMatrix*vec4(position,1.);n=normalize(normalMatrix*normal);v=normalize(-p.xyz);gl_Position=projectionMatrix*p;}`,
    fragmentShader:`varying vec3 n;varying vec3 v;void main(){float a=pow(max(0.,.65-dot(n,v)),3.)*.36;gl_FragColor=vec4(.1,.48,1.,a);}`
  }));group.add(atmo);
  const orbitGroup=new THREE.Group();orbitGroup.rotation.x=1.18;orbitGroup.rotation.y=.3;scene.add(orbitGroup);
  for(let i=0;i<3;i++) {
    const r=new THREE.Mesh(new THREE.TorusGeometry(5.2+i*.18,.012,6,180),neon(i===0?0x55caff:0x214171,i===0?1.3:1));
    orbitGroup.add(r);
  }
  const moon=new THREE.Mesh(new THREE.IcosahedronGeometry(.62,3),new THREE.MeshStandardMaterial({color:0x8e9caa,roughness:.95,flatShading:true}));
  scene.add(moon);
  scene.add(new THREE.AmbientLight(0x32466b,.7));
  const sun=new THREE.DirectionalLight(0xb5ddff,3);sun.position.set(-5,7,10);scene.add(sun);
  const satellite=new THREE.Group();
  satellite.add(new THREE.Mesh(new THREE.BoxGeometry(.18,.18,.3),new THREE.MeshStandardMaterial({color:0xc4d9ea,metalness:.7,roughness:.3})));
  const panels=new THREE.Mesh(new THREE.BoxGeometry(1.0,.015,.24),new THREE.MeshStandardMaterial({color:0x175295,metalness:.6,roughness:.3}));
  satellite.add(panels);scene.add(satellite);
  return {scene,defaults:{from:[9,3.7,15],to:[-3,1.3,10.8],look_at:[0,0,0]},update:(t,u)=>{
    globe.rotation.y=.4+t*.11;
    moon.position.set(-7+u*.5,3.6,-4);
    satellite.position.set(Math.cos(t*.2+.9)*5.5,Math.sin(t*.2+.9)*1.2,Math.sin(t*.2+.9)*5.5);
    satellite.rotation.set(.3,t*.2,.4);
  }};
}

function windowTexture(rng) {
  const c=document.createElement('canvas');c.width=64;c.height=128;
  const d=c.getContext('2d');d.fillStyle='#01040a';d.fillRect(0,0,64,128);
  for(let y=3;y<128;y+=8) for(let x=3;x<64;x+=9) if(rng()>.28) {
    d.fillStyle=rng()>.22?'#72ceef':'#e9a867';d.globalAlpha=.4+rng()*.6;d.fillRect(x,y,3,3);
  }
  d.globalAlpha=1;const tex=new THREE.CanvasTexture(c);tex.colorSpace=THREE.SRGBColorSpace;
  tex.magFilter=THREE.NearestFilter;return tex;
}
function city(s,rng) {
  const scene=new THREE.Scene();scene.background=new THREE.Color(0x030713);scene.fog=new THREE.FogExp2(0x09172a,.017);
  stars(scene,rng,s.star_count ?? 800,150);
  scene.add(new THREE.HemisphereLight(0x85b9e7,0x05070d,1.3));
  const key=new THREE.DirectionalLight(0x75bcff,2.1);key.position.set(-15,25,10);scene.add(key);
  const ground=new THREE.Mesh(new THREE.PlaneGeometry(220,220),new THREE.MeshStandardMaterial({color:0x07121d,metalness:.65,roughness:.35}));
  ground.rotation.x=-Math.PI/2;ground.position.z=-35;scene.add(ground);
  const grid=new THREE.GridHelper(180,60,0x1e6f89,0x123044);grid.position.set(0,.015,-30);scene.add(grid);
  const n=s.building_count ?? 180, geo=new THREE.BoxGeometry(1,1,1), texture=windowTexture(rng);
  const mat=new THREE.MeshStandardMaterial({color:0x132134,roughness:.42,metalness:.5,emissive:0x77bfff,emissiveMap:texture,emissiveIntensity:1.8});
  const buildings=new THREE.InstancedMesh(geo,mat,n);
  const edgePoints=[],edge=new THREE.EdgesGeometry(geo).attributes.position;
  const matrix=new THREE.Matrix4(),q=new THREE.Quaternion();
  for(let i=0;i<n;i++) {
    const side=i%2?1:-1,col=Math.floor(i/2)%7,row=Math.floor(i/14);
    const w=2+rng()*2.7,h=3+rng()*17,zsize=2.5+rng()*3;
    const x=side*(7+col*6+(rng()-.5)),z=16-row*7+(rng()-.5)*2;
    matrix.compose(new THREE.Vector3(x,h/2,z),q,new THREE.Vector3(w,h,zsize));buildings.setMatrixAt(i,matrix);
    for(let j=0;j<edge.count;j++) {const v=new THREE.Vector3().fromBufferAttribute(edge,j).applyMatrix4(matrix);edgePoints.push(v.x,v.y,v.z);}
  }
  scene.add(buildings);
  const eg=new THREE.BufferGeometry();eg.setAttribute('position',new THREE.Float32BufferAttribute(edgePoints,3));
  scene.add(new THREE.LineSegments(eg,new THREE.LineBasicMaterial({color:0x327e9b,transparent:true,opacity:.55})));
  for(const x of [-4.5,-3.7,3.7,4.5]) {
    const rail=new THREE.Mesh(new THREE.BoxGeometry(.045,.035,145),neon(x<0?0x25c5ed:0x9065ee,2.7));rail.position.set(x,.065,-45);scene.add(rail);
  }
  // Elevated transit bridges create foreground occlusion and obvious camera parallax.
  for(const z of [-8,-33,-58]) {
    const bridge=new THREE.Mesh(new THREE.BoxGeometry(14,.35,1.5),new THREE.MeshStandardMaterial({color:0x18293e,metalness:.65,roughness:.35}));
    bridge.position.set(0,11,z);scene.add(bridge);
    const strip=new THREE.Mesh(new THREE.BoxGeometry(13,.07,.08),neon(0x33dcff,3));strip.position.set(0,10.8,z+.78);scene.add(strip);
  }
  const tower=new THREE.Mesh(new THREE.CylinderGeometry(1.5,3.4,27,8),new THREE.MeshStandardMaterial({color:0x1a3550,metalness:.7,roughness:.3,emissive:0x092033}));
  tower.position.set(0,13.5,-78);scene.add(tower);
  const holo=[];
  for(let i=0;i<3;i++) {
    const r=new THREE.Mesh(new THREE.TorusGeometry(3+i*.55,.025,6,100),neon(0x54d9ff,2));
    r.rotation.x=Math.PI/2;r.position.set(0,22+i*.55,-78);scene.add(r);holo.push(r);
  }
  const vehicles=[];
  for(let i=0;i<12;i++) {
    const car=new THREE.Mesh(new THREE.BoxGeometry(.3,.12,1.5),neon(i%2?0xffa669:0x5fe0ff,3));scene.add(car);vehicles.push(car);
  }
  return {scene,defaults:{from:[1,8.5,31],to:[-1,4.5,-38],look_at:[0,10,-78]},update:(t,u)=>{
    vehicles.forEach((car,i)=>car.position.set(i%2?2.0:-2.0,.35,(i*13+t*(i%2?-10:12)+180)%160-120));
    holo.forEach((r,i)=>{r.rotation.z=t*.25+i*.3;r.rotation.x=Math.PI/2+Math.sin(t*.4+i)*.15;});
  }};
}

const worlds=config.scenes.map((s,i)=>{
  const rng=random(config.seed+i*1009);
  const world=({'star-flight':flight,'orbital-planet':orbit,'neon-city':city})[s.type](s,rng);
  const cameraOptions={...world.defaults,...s.camera};
  world.camera=new THREE.PerspectiveCamera(cameraOptions.fov || 50,W/H,.1,500);
  world.options=cameraOptions;world.spec=s;return world;
});
const gl=renderer.getContext(),ext=gl.getExtension('WEBGL_debug_renderer_info');
window.hvideoInfo={backend:'threejs',three_revision:THREE.REVISION,webgl:gl.getParameter(gl.VERSION),gpu:ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER),bloom:bloom.enabled};
window.hvideoFrame=time=>{
  const world=worlds.find(w=>time>=w.spec.start && time<w.spec.start+w.spec.duration);
  ctx.fillStyle='#02040b';ctx.fillRect(0,0,W,H);
  if(world) {
    const s=world.spec,t=time-s.start,u=t/s.duration,e=smooth(0,1,u),o=world.options;
    world.camera.position.copy(vec(o.from).lerp(vec(o.to),e));
    world.camera.lookAt(vec(o.look_at).lerp(vec(o.look_at_end || o.look_at),e));
    world.update(t,u);
    renderPass.scene=world.scene;renderPass.camera=world.camera;
    composer.render(0);gl.finish();
    ctx.globalAlpha=smooth(0,s.fade_in ?? .4,t)*(1-smooth(s.duration-(s.fade_out ?? .5),s.duration,t));
    ctx.drawImage(renderer.domElement,0,0,W,H);
    const k=Math.min(W/960,H/540),x=56*k;
    // A subtle bottom gradient protects text without covering the focal subject.
    const grad=ctx.createLinearGradient(0,H*.58,0,H);
    grad.addColorStop(0,'rgba(2,4,12,0)');grad.addColorStop(1,'rgba(2,4,12,.9)');ctx.fillStyle=grad;ctx.fillRect(0,H*.58,W,H*.42);
    const reveal=smooth(.3,1.3,t);
    ctx.globalAlpha*=reveal;
    ctx.textAlign='left';ctx.textBaseline='alphabetic';ctx.fillStyle='#8ec7dc';ctx.font=`${12*k}px HNova`;
    ctx.fillText(s.eyebrow || 'HNOVA / SPATIAL STUDY',x,H-143*k);
    ctx.fillStyle='#e5f2f8';ctx.font=`${34*k}px HNova`;ctx.fillText(s.title || '',x,H-91*k,W-x*2);
    ctx.fillStyle='#95b1c7';ctx.font=`${15*k}px HNova`;ctx.fillText(s.subtitle || '',x,H-58*k,W-x*2);
  }
  ctx.globalAlpha=1;
  const k=Math.min(W/960,H/540);
  ctx.fillStyle='#02040b';ctx.fillRect(0,0,W,26*k);ctx.fillRect(0,H-26*k,W,26*k);
  ctx.fillStyle='#7395b2';ctx.font=`${10*k}px HNova`;ctx.textAlign='left';
  ctx.fillText(config.brand || 'HNOVA / THREE.JS',24*k,17*k);
  ctx.textAlign='right';ctx.fillText(`${String(Math.floor(time)).padStart(2,'0')} / ${D}s`,W-24*k,17*k);
  ctx.fillStyle='#29546b';ctx.fillRect(0,H-2*k,W,2*k);ctx.fillStyle='#66d8ee';ctx.fillRect(0,H-2*k,W*time/D,2*k);
  return output.toDataURL('image/png').split(',')[1];
};
// No requestAnimationFrame loop: all animation state is an absolute function of time.
window.hvideoFrame(0);
window.hvideoReady=true;
