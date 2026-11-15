import {useEffect,useRef,useState} from 'react';
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {toScene,fromScene} from './coordinates';
import type {Geo,Grid,Layers,Observation,Point,Progress,Route,Site,View} from './types';
export interface MapProps {grid:Grid;sites:Site[];base:Point;route:Route|null;alternatives:Route[];geo:Geo;history:Geo;observations:Observation[];layers:Layers;progress:Progress|null;focus:number|null;view:View;mode:string;onPick:(p:Point)=>void;onSite:(id:string)=>void;onView:(v:View)=>void;onFocus:(i:number|null)=>void;onInspect:(p:Point)=>void;exaggeration:number}
export function displayHeight(grid:Grid,p:Point){let c=Math.max(0,Math.min(grid.width-1,(p[0]-grid.first_sample_local_m[0])/grid.spacing_m)),r=Math.max(0,Math.min(grid.height-1,(-p[1]+grid.first_sample_local_m[1])/grid.spacing_m));let x=Math.floor(c),y=Math.floor(r),xx=Math.min(grid.width-1,x+1),yy=Math.min(grid.height-1,y+1),u=c-x,v=r-y;return (1-v)*((1-u)*grid.heights_m[y][x]+u*grid.heights_m[y][xx])+v*((1-u)*grid.heights_m[yy][x]+u*grid.heights_m[yy][xx]);}
export default function Terrain3D(props:MapProps){
 const host=useRef<HTMLDivElement>(null),latest=useRef(props),cameraState=useRef<{position:THREE.Vector3;target:THREE.Vector3}|null>(null),[error,setError]=useState('');latest.current=props;
 useEffect(()=>{
  const div=host.current!,started=performance.now();let alive=true,renderer:THREE.WebGLRenderer;
  try{renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});}catch{setError('WebGL unavailable: use the 2D map.');return;}
  // Scene and pin design adapted from the user-provided Yasmina Viewer3D.
  // Retain native sample positioning, UVs, raycasting and all existing scientific layers.
  renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setClearColor('#0b0f14');renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFShadowMap;div.append(renderer.domElement);
  const scene=new THREE.Scene();scene.fog=new THREE.FogExp2('#0b0f14',.0004);
  const camera=new THREE.PerspectiveCamera(45,1,1,8000);camera.position.set(200,750,700);
  const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=!matchMedia('(prefers-reduced-motion: reduce)').matches;controls.dampingFactor=.05;controls.maxPolarAngle=Math.PI/2.05;controls.minDistance=80;controls.maxDistance=3500;controls.target.set(props.view.cx-600,0,-props.view.cy-650);
  if(cameraState.current){camera.position.copy(cameraState.current.position);controls.target.copy(cameraState.current.target);}controls.update();
  scene.add(new THREE.AmbientLight('#ffffff',.85));const sun=new THREE.DirectionalLight('#ffe5d0',1.8);sun.position.set(400,1000,600);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);sun.shadow.camera.left=-750;sun.shadow.camera.right=750;sun.shadow.camera.top=750;sun.shadow.camera.bottom=-750;sun.shadow.camera.far=2500;scene.add(sun);
  const geometry=new THREE.BufferGeometry(),positions=[],uv=[],indices=[];const grid=props.grid;
  for(let r=0;r<grid.height;r++)for(let c=0;c<grid.width;c++){let x=grid.first_sample_local_m[0]+c*grid.spacing_m,y=grid.first_sample_local_m[1]-r*grid.spacing_m;positions.push(...toScene([x,y],grid.heights_m[r][c],props.exaggeration));uv.push(x/1200,1+y/1300);}
  for(let r=0;r<grid.height-1;r++)for(let c=0;c<grid.width-1;c++){let a=r*grid.width+c,b=a+1,d=a+grid.width,e=d+1;indices.push(a,d,b,b,d,e);}
  geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));geometry.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));geometry.setIndex(indices);geometry.computeVertexNormals();
  const textureUrl=props.layers.basemap==='PLACES'?'/data/frontend/terrain_texture.png':'/runtime/'+props.layers.basemap+'.png';
  const texture=new THREE.TextureLoader().load(textureUrl,()=>render());texture.colorSpace=THREE.SRGBColorSpace;
  const terrain=new THREE.Mesh(geometry,new THREE.MeshStandardMaterial({map:texture,side:THREE.DoubleSide,roughness:.85,metalness:.1,flatShading:false}));terrain.receiveShadow=true;scene.add(terrain);
  let objects:THREE.Object3D[]=[];const markerMeshes:THREE.Object3D[]=[];
  function height(p:Point){return displayHeight(grid,p);}
  function line(points:Point[],color:string,dashed=false,opacity=1){if(points.length<2)return;let geo=new THREE.BufferGeometry().setFromPoints(points.map(p=>new THREE.Vector3(...toScene(p,height(p)+1.2,props.exaggeration))));let material=dashed?new THREE.LineDashedMaterial({color,dashSize:6,gapSize:4,depthTest:false,transparent:true,opacity}):new THREE.LineBasicMaterial({color,depthTest:false,transparent:true,opacity});let object=new THREE.Line(geo,material);if(dashed)object.computeLineDistances();object.renderOrder=5;scene.add(object);objects.push(object);}
  function marker(p:Point,color:string,id:string,label:string){
   const anchor=new THREE.Vector3(...toScene(p,height(p),props.exaggeration)),isBase=id==='base';
   let shape=isBase?new THREE.ConeGeometry(8,22,16):new THREE.SphereGeometry(6,16,16);if(isBase)shape.rotateX(Math.PI);
   let object=new THREE.Mesh(shape,new THREE.MeshStandardMaterial({color:isBase?'#e26338':color,roughness:.3,metalness:.3,emissive:color,emissiveIntensity:.35,depthTest:false}));object.position.copy(anchor).add(new THREE.Vector3(0,isBase?16:28,0));object.userData.id=id;object.renderOrder=10;scene.add(object);objects.push(object);markerMeshes.push(object);
   if(!isBase){const stem=new THREE.Mesh(new THREE.CylinderGeometry(1.2,1.2,28,8),new THREE.MeshBasicMaterial({color,depthTest:false}));stem.position.copy(anchor).add(new THREE.Vector3(0,14,0));scene.add(stem);objects.push(stem);}
   const canvas=document.createElement('canvas');canvas.width=400;canvas.height=64;let ctx=canvas.getContext('2d')!;ctx.fillStyle='#10191ee6';ctx.fillRect(0,0,400,64);ctx.font='24px system-ui';ctx.fillStyle='#ffffff';ctx.fillText(label,12,42);let tex=new THREE.CanvasTexture(canvas);let sprite=new THREE.Sprite(new THREE.SpriteMaterial({map:tex,depthTest:false}));sprite.position.copy(object.position).add(new THREE.Vector3(0,23,0));sprite.scale.set(135,22,1);sprite.renderOrder=11;scene.add(sprite);objects.push(sprite);}
  props.alternatives.forEach(r=>line(r.geometry.coordinates,'#87959d',true));
  if(props.route){const last=props.route.legs.at(-1)!;line(props.route.geometry.coordinates.slice(0,last.start_index+1),'#6ee0da');line(props.route.geometry.coordinates.slice(last.start_index),'#f4ad71',true);}
  if(props.layers.history)props.history.features.forEach(f=>line(f.geometry.coordinates,'#c8a1ee',true));
  if(props.layers.geology)props.geo.features.forEach(f=>{let polygons=f.geometry.type==='Polygon'?[f.geometry.coordinates]:f.geometry.coordinates;polygons.forEach((poly:Point[][])=>poly.forEach(ring=>line(ring,'#d9bd7d',true,props.layers.opacity)));});
  if(props.layers.slope){let tex=new THREE.TextureLoader().load('/runtime/slope.png',()=>render());let overlay=new THREE.Mesh(geometry,new THREE.MeshBasicMaterial({map:tex,transparent:true,opacity:.7,depthWrite:false,polygonOffset:true,polygonOffsetFactor:-1,side:THREE.DoubleSide}));scene.add(overlay);objects.push(overlay);}
  marker(props.base,'#f4ad71','base','Spacecraft · simulated');props.sites.forEach(s=>marker([s.position.x,s.position.y],'#6ee0da',s.id,s.name));
  if(props.layers.observations)props.observations.filter(o=>o.position).forEach(o=>marker(o.position,'#d0a3ef','note:'+o.id,'User note'));
  if(props.progress)marker(props.progress.position,'#fff3dd','progress','Simulated position');
  if(props.focus!==null&&props.route?.geometry.coordinates[props.focus])marker(props.route.geometry.coordinates[props.focus],'#ffffff','focus','Profil');
  const raycaster=new THREE.Raycaster(),pointer=new THREE.Vector2();let down=[0,0];
  const onDown=(e:PointerEvent)=>{down=[e.clientX,e.clientY];};
  const onUp=(e:PointerEvent)=>{if(Math.hypot(e.clientX-down[0],e.clientY-down[1])>5)return;let box=renderer.domElement.getBoundingClientRect();pointer.set((e.clientX-box.left)/box.width*2-1,-(e.clientY-box.top)/box.height*2+1);raycaster.setFromCamera(pointer,camera);let selected=raycaster.intersectObjects(markerMeshes)[0];if(selected){latest.current.onSite(selected.object.userData.id);return;}let hit=raycaster.intersectObject(terrain)[0];if(hit){let p=fromScene(hit.point.x,hit.point.y,hit.point.z,props.exaggeration);latest.current.onPick([p[0],p[1]]);latest.current.onInspect([p[0],p[1]]);}};
  renderer.domElement.addEventListener('pointerdown',onDown);renderer.domElement.addEventListener('pointerup',onUp);
  function render(){if(alive&&div.clientWidth&&div.clientHeight)renderer.render(scene,camera);}
  let frame=0;function animate(){if(!alive)return;frame=requestAnimationFrame(animate);if(div.clientWidth&&div.clientHeight)controls.update();}animate();
  controls.addEventListener('change',render);controls.addEventListener('end',()=>latest.current.onView({...latest.current.view,cx:controls.target.x+600,cy:-controls.target.z-650}));
  const resize=()=>{let w=div.clientWidth,h=div.clientHeight;if(!w||!h)return;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();render();};let observer=new ResizeObserver(resize);observer.observe(div);resize();div.dataset.viewer='yasmina-adapted';div.dataset.vertices=String(grid.width*grid.height);div.dataset.initializationMs=(performance.now()-started).toFixed(1);div.dataset.exaggeration=String(props.exaggeration);
  const fit=()=>{controls.target.set(0,0,0);camera.position.set(200,750,700);controls.update();render();};document.addEventListener('marswalk:fit3d',fit);
  const zoom=(e:Event)=>{let factor=(e as CustomEvent<number>).detail;camera.position.sub(controls.target).multiplyScalar(factor).add(controls.target);controls.update();render();};document.addEventListener('marswalk:zoom3d',zoom);
  return()=>{alive=false;cancelAnimationFrame(frame);cameraState.current={position:camera.position.clone(),target:controls.target.clone()};observer.disconnect();document.removeEventListener('marswalk:fit3d',fit);document.removeEventListener('marswalk:zoom3d',zoom);controls.dispose();scene.traverse(o=>{const m=o as THREE.Mesh;m.geometry?.dispose();let materials=Array.isArray(m.material)?m.material:[m.material];materials.filter(Boolean).forEach(mat=>{(mat as THREE.MeshStandardMaterial).map?.dispose();mat.dispose();});});sun.shadow.map?.dispose();renderer.dispose();div.replaceChildren();};
 },[props.grid,props.route,props.base,props.layers,props.observations,props.progress?.position[0],props.progress?.position[1],props.exaggeration,props.focus]);
 return <div className="three-host" ref={host} role="img" aria-label="Real Jezero terrain in 3D">{error&&<p role="alert">{error}</p>}<span className="three-caption">Real DEM · 5 m display · relief {props.exaggeration}× · graphical lighting, no solar date</span></div>;
}
