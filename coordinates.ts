import type {Point} from './types';
export const Z_ORIGIN=-2500;
export function toScene(p:Point,z:number,exaggeration=1):[number,number,number]{return[p[0]-600,(z-Z_ORIGIN)*exaggeration,-p[1]-650];}
export function fromScene(x:number,up:number,south:number,exaggeration=1):[number,number,number]{return[x+600,-south-650,up/exaggeration+Z_ORIGIN];}
export function toSvg(p:Point):Point{return[p[0],-p[1]];}
export function toMars(p:Point):Point{let r=3396190,rad=Math.PI/180;return[(p[0]+4351286)/(r*Math.cos(18.4663*rad))/rad,(p[1]+1094535)/r/rad];}
