import React,{useEffect,useRef} from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import {COLORS,LABELS,risk,atTime} from './engine';
export default function TripMap({data,selected,onSelect,onCheckpoint,heat,forecastHour,load,showPoints}){
 const div=useRef(),map=useRef(),layers=useRef(),heatLayer=useRef(),last=useRef();
 useEffect(()=>{const m=L.map(div.current,{zoomControl:false,preferCanvas:true}).setView([39,-86.8],6);map.current=m;L.control.zoom({position:'bottomright'}).addTo(m);L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',maxZoom:19}).addTo(m);layers.current=L.layerGroup().addTo(m);heatLayer.current=L.layerGroup().addTo(m);const observer=new ResizeObserver(()=>m.invalidateSize());observer.observe(div.current);return()=>{observer.disconnect();m.remove();};},[]);
 useEffect(()=>{if(!map.current||!data)return;const g=layers.current;g.clearLayers();const bounds=[];const routes=[...data.routes].sort((a,b)=>(a.id===selected)-(b.id===selected));
 routes.forEach(r=>{const coords=r.geometry.coordinates.map(c=>[c[1],c[0]]);bounds.push(...coords);L.polyline(coords,{color:r.id===selected?'#173f41':'#879b9f',weight:r.id===selected?7:4,opacity:r.id===selected?1:.6}).on('click',()=>onSelect(r.id)).addTo(g);
 if(r.id===selected){for(let i=0;i<r.checkpoints.length-1;i++){const a=r.checkpoints[i],b=r.checkpoints[i+1];const level=a.risk===null||b.risk===null?null:Math.max(a.risk,b.risk);const cs=r.geometry.coordinates;const segment=[a.coord,...cs.slice(a.segmentIndex,b.segmentIndex),b.coord];
 L.polyline(segment.map(c=>[c[1],c[0]]),{color:level===null?'#8b93a2':COLORS[level],weight:4,opacity:1}).on('click',()=>onCheckpoint(a)).addTo(g);}
 if(showPoints)r.checkpoints.forEach((p,i)=>{L.circleMarker([p.coord[1],p.coord[0]],{radius:i===0||i===r.checkpoints.length-1?7:4,color:'#fff',weight:2,fillColor:p.risk===null?'#89939c':COLORS[p.risk],fillOpacity:1}).bindTooltip(`${i===0?'Start':i===r.checkpoints.length-1?'Arrival':`Mile ${Math.round(p.mile)}`} · ${p.risk===null?'Unknown':LABELS[p.risk]}`).on('click',()=>onCheckpoint(p)).addTo(g);});
 const ends=[r.checkpoints[0],r.checkpoints.at(-1)];ends.forEach((p,i)=>L.marker([p.coord[1],p.coord[0]],{icon:L.divIcon({className:'endpoint',html:i?'B':'A',iconSize:[28,28],iconAnchor:[14,14]})}).addTo(g));}
 });if(last.current!==data){map.current.fitBounds(bounds,{padding:[55,55],maxZoom:9});last.current=data;}
 },[data,selected,showPoints,onSelect,onCheckpoint]);
 useEffect(()=>{if(!heatLayer.current)return;heatLayer.current.clearLayers();if(!heat||!data)return;const iso=new Date(new Date(data.generatedAt).getTime()+forecastHour*3600000).toISOString();data.corridor.forEach(p=>{const value=risk(atTime(p.forecast,iso),load);if(value===null)return; // Layered translucent kernels, bounded dataset, Canvas renderer.
 [24000,16000,8000].forEach((radius,i)=>L.circle([p.coord[1],p.coord[0]],{radius,stroke:false,fillColor:COLORS[value],fillOpacity:[.06,.1,.14][i],interactive:false}).addTo(heatLayer.current));});},[data,heat,forecastHour,load]);
 return <div ref={div} className="map" aria-label="Route map with weather checkpoints"/>;
}
