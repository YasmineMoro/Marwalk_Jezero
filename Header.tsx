import {en} from './labels';
export default function Header({health,onNew}:{health:string;onNew:()=>void}) {
 return <header className="topbar branded-header">
  <a className="brand" href="#map" aria-label="MarsWalk by KAWKAB ZOMORODA — home">
   <span aria-hidden="true">◈</span><div><div className="brand-line"><strong>MarsWalk</strong><span className="team-credit">by KAWKAB ZOMORODA</span></div><small>{en.region}</small></div>
  </a>
  <span className="prototype">{en.prototype}</span>
  <div className="header-actions"><span className={'connection '+health} role="status">● {health==='ok'?'API online':health==='checking'?'Checking API…':'API offline'}</span><button onClick={onNew}>{en.newMission}</button></div>
  <div className="header-logos" aria-label="NASA and KAWKAB ZOMORODA logos">
   <span className="nasa-mark"><img src="/branding/nasa.webp" alt="NASA"/></span>
   <img className="team-mark" src="/branding/kawkab-zomoroda.png" alt="KAWKAB ZOMORODA team"/>
  </div>
 </header>;
}
