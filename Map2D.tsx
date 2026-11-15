import {useEffect,useMemo,useRef,useState} from 'react';
import type {MapProps} from './Terrain3D';
import type {Point} from './types';
import {toSvg} from './coordinates';
export default function Map2D(p:MapProps){
 const svg=useRef<SVGSVGElement>(null),[size,setSize]=useState({w:800,h:650}),[tileStatus,setTileStatus]=useState({key:'',ok:0,bad:0});
 useEffect(()=>{const o=new ResizeObserver(entries=>setSize({w:entries[0].contentRect.width,h:entries[0].contentRect.height}));o.observe(svg.current!);return()=>o.disconnect();},[]);
 const height=p.view.width*size.h/size.w,x0=p.view.cx-p.view.width/2,y0=-p.view.cy-height/2;
 const points=(a:Point[])=>a.map(v=>toSvg(v).join(',')).join(' ');
 function world(clientX:number,clientY:number):Point{let v=new DOMPoint(clientX,clientY).matrixTransform(svg.current!.getScreenCTM()!.inverse());return[v.x,-v.y];}
 function zoom(factor:number,anchor:Point=[p.view.cx,p.view.cy]){let minimum=p.layers.online&&p.layers.basemap==='HiRISE'?.32:p.layers.basemap==='CTX'?10:2;let width=Math.max(size.w*minimum,Math.min(4000,p.view.width*factor)),ratio=width/p.view.width;p.onView({cx:anchor[0]+(p.view.cx-anchor[0])*ratio,cy:anchor[1]+(p.view.cy-anchor[1])*ratio,width});}
 const pointers=useRef(new Map<number,Point>()),drag=useRef<{screen:Point;view:typeof p.view;distance?:number;moved:boolean}|null>(null);
 const tiles=useMemo(()=>{
  if(!p.layers.online||!['HiRISE','CTX'].includes(p.layers.basemap))return [];
  let R=3396190,rad=Math.PI/180,cos=Math.cos(18.4663*rad),z=Math.max(0,Math.min(p.layers.basemap==='HiRISE'?17:13,Math.ceil(Math.log2(180*rad*R/(256*(p.view.width/size.w)))))),span=180/2**z;
  let west=(x0+4351286)/(R*cos)/rad,east=(x0+p.view.width+4351286)/(R*cos)/rad,north=(-y0+1094535)/R/rad,south=(-y0-height+1094535)/R/rad;
  let out=[];for(let row=Math.floor((90-north)/span);row<=Math.floor((90-south)/span);row++)for(let col=Math.floor((west+180)/span);col<=Math.floor((east+180)/span);col++)out.push({z,row,col,x:R*cos*(-180+col*span)*rad-4351286,y:-(R*(90-row*span)*rad-1094535),w:R*cos*span*rad,h:R*span*rad});return out.length<=80?out:[];
 },[p.view,p.layers,size]);
 const tileKey=JSON.stringify(tiles.map(t=>[t.z,t.row,t.col]))+p.layers.basemap;
 useEffect(()=>setTileStatus({key:tileKey,ok:0,bad:0}),[tileKey]);
 useEffect(()=>{const f=(e:Event)=>zoom((e as CustomEvent).detail);document.addEventListener('marswalk:zoom2d',f);return()=>document.removeEventListener('marswalk:zoom2d',f);});
 const url=p.layers.basemap==='PLACES'?'/data/frontend/terrain_texture.png':'/runtime/'+p.layers.basemap+'.png';
 const returnStart=p.route?.legs.at(-1)?.start_index||0;
 function marker(point:Point,id:string,label:string,color:string,ship=false){return <g key={id} className="map-marker" role="button" tabIndex={0} aria-label={label} onKeyDown={e=>{if(e.key==='Enter')p.onSite(id);}} onClick={e=>{e.stopPropagation();p.onSite(id);}} data-marker="true">{ship?<path d={`M${point[0]},${-point[1]-12}l11,20 -22,0Z`} fill={color} stroke="#132026" strokeWidth={3}/>:<circle cx={point[0]} cy={-point[1]} r={7*p.view.width/900} fill={color} stroke="#132026" strokeWidth={2*p.view.width/900}/>}<text x={point[0]+12*p.view.width/900} y={-point[1]+5*p.view.width/900} fontSize={14*p.view.width/900} fill="#f4f2e8" paintOrder="stroke" stroke="#10191e" strokeWidth={4*p.view.width/900}>{label}</text></g>;}
 return <><svg ref={svg} className="map-svg" viewBox={`${x0} ${y0} ${p.view.width} ${height}`} role="img" aria-label="Local Jezero 2D map" onWheel={e=>{zoom(e.deltaY>0?1.2:.8,world(e.clientX,e.clientY));}}
  onPointerDown={e=>{if((e.target as Element).closest('[data-marker]'))return;svg.current!.setPointerCapture(e.pointerId);pointers.current.set(e.pointerId,[e.clientX,e.clientY]);let values=[...pointers.current.values()];drag.current={screen:[e.clientX,e.clientY],view:{...p.view},moved:false,distance:values.length===2?Math.hypot(values[0][0]-values[1][0],values[0][1]-values[1][1]):undefined};}}
  onPointerMove={e=>{let w=world(e.clientX,e.clientY);p.onInspect(w);if(!drag.current)return;pointers.current.set(e.pointerId,[e.clientX,e.clientY]);let d=drag.current,dx=e.clientX-d.screen[0],dy=e.clientY-d.screen[1];if(pointers.current.size===2&&d.distance){let a=[...pointers.current.values()],distance=Math.hypot(a[0][0]-a[1][0],a[0][1]-a[1][1]);zoom(d.distance/distance);d.distance=distance;d.moved=true;}else if(Math.hypot(dx,dy)>4&&!p.mode){d.moved=true;p.onView({cx:d.view.cx-dx*d.view.width/size.w,cy:d.view.cy+dy*d.view.width/size.w,width:d.view.width});}}}
  onPointerUp={e=>{const d=drag.current;pointers.current.delete(e.pointerId);drag.current=null;if(d&&!d.moved)p.onPick(world(e.clientX,e.clientY));}} onPointerCancel={()=>{drag.current=null;pointers.current.clear();}}>
 <defs><pattern id="outside" width="30" height="30" patternUnits="userSpaceOnUse"><path d="M0 0L30 30" stroke="#35434b" strokeWidth="1"/></pattern></defs><rect x={x0} y={y0} width={p.view.width} height={height} fill="url(#outside)"/>
 <image href={url} x={0} y={0} width={1200} height={1300}/>
 {tiles.map(t=><image key={`${p.layers.basemap}/${t.z}/${t.row}/${t.col}`} href={`/api/v1/tiles/${p.layers.basemap}/${t.z}/${t.row}/${t.col}.png`} x={t.x} y={t.y} width={t.w} height={t.h} onLoad={()=>setTileStatus(s=>s.key===tileKey?{...s,ok:s.ok+1}:s)} onError={()=>setTileStatus(s=>s.key===tileKey?{...s,bad:s.bad+1}:s)}/>)}
 {p.layers.slope&&<image href="/runtime/slope.png" x={0} y={0} width={1200} height={1300} opacity={.65}/>}
 {p.layers.geology&&p.geo.features.map((f,i)=>{let polygons=f.geometry.type==='Polygon'?[f.geometry.coordinates]:f.geometry.coordinates;return <path key={f.id||i} className="geology-shape" d={polygons.map((poly:Point[][])=>poly.map(ring=>'M'+ring.map(v=>toSvg(v).join(',')).join('L')+'Z').join('')).join('')} fill={['#a1aa7e','#b9897b','#b9897b','#d4b46e','#8caab8'][i%5]} fillOpacity={p.layers.opacity*.3} stroke="#d7c596" strokeOpacity={p.layers.opacity} strokeWidth={1.2*p.view.width/900} fillRule="evenodd" onClick={e=>{e.stopPropagation();p.onSite('geo:'+i);}}/>;})}
 {p.layers.history&&p.history.features.map((f,i)=><polyline key={i} points={points(f.geometry.coordinates)} fill="none" stroke="#c4a2e4" strokeDasharray="6 5" strokeWidth={2*p.view.width/900}/>)}
 {p.alternatives.filter(r=>r!==p.route).map((r,i)=><polyline key={i} points={points(r.geometry.coordinates)} fill="none" stroke="#c5d4dc" opacity={.4} strokeWidth={3*p.view.width/900} strokeDasharray="4 7"/>)}
 {p.route&&<g onPointerMove={e=>{let w=world(e.clientX,e.clientY),nearest=0,d=Infinity;p.route!.geometry.coordinates.forEach((point,i)=>{let distance=Math.hypot(point[0]-w[0],point[1]-w[1]);if(distance<d){d=distance;nearest=i;}});p.onFocus(nearest);}}><polyline points={points(p.route.geometry.coordinates.slice(0,returnStart+1))} fill="none" stroke="#6ee0da" strokeWidth={6*p.view.width/900} strokeLinejoin="round"/><polyline points={points(p.route.geometry.coordinates.slice(returnStart))} fill="none" stroke="#f4ad71" strokeWidth={3*p.view.width/900} strokeDasharray={`${6*p.view.width/900} ${5*p.view.width/900}`}/></g>}
 <rect x={0} y={0} width={1200} height={1300} fill="none" stroke="#dfb883" strokeDasharray="14 10" strokeWidth={2*p.view.width/900}/>
 {marker(p.base,'base','Spacecraft · simulated','#f4ad71',true)}{p.sites.map(s=>marker([s.position.x,s.position.y],s.id,s.name,'#7be0d4'))}
 {p.layers.observations&&p.observations.filter(o=>o.position).map(o=>marker(o.position,'note:'+o.id,'User note','#c9a6ec'))}
 {p.progress&&<circle cx={p.progress.position[0]} cy={-p.progress.position[1]} r={7*p.view.width/900} fill="#fff4d8" stroke="#e88153" strokeWidth={3*p.view.width/900}/>}
 {p.focus!==null&&p.route&&<circle cx={p.route.geometry.coordinates[p.focus][0]} cy={-p.route.geometry.coordinates[p.focus][1]} r={6*p.view.width/900} fill="white"/>}
 </svg><div className="map-scale"><i style={{width:Math.min(180,100/p.view.width*size.w)}}/>100 m</div><div className="tile-status">{p.layers.online?`WMTS ${tiles[0]?.z??'outside coverage'} · ${tileStatus.ok}/${tiles.length} tiles · ${tileStatus.bad} missing`:'Local basemap · works offline'}<br/>Rectangle = DEM domain · outside: no routing</div></>;
}
