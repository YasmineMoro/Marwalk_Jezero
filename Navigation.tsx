export const destinations = [
  {id:'map', label:'Map', caption:'Explore Jezero', icon:'◈'},
  {id:'mission', label:'Mission', caption:'Plan your route', icon:'↗'},
  {id:'science', label:'Science', caption:'Sites and detours', icon:'◇'},
  {id:'simulation', label:'Exploration', caption:'Play the mission', icon:'▷'},
  {id:'journal', label:'Notebook', caption:'Notes and report', icon:'▤'},
  {id:'environment', label:'Environment', caption:'MEDA context', icon:'◌'},
  {id:'sources', label:'Sources', caption:'Data and limitations', icon:'≋'},
] as const;
export type Page = typeof destinations[number]['id'];
export function pageFromHash():Page {
  const value=location.hash.slice(1);
  return destinations.some(d=>d.id===value)?value as Page:'map';
}
export default function Navigation({page}:{page:Page}) {
  return <nav className="workspace-nav" aria-label="Main navigation">
    <span className="nav-label">EXPLORATION WORKSPACE</span>
    {destinations.map(d=><a key={d.id} href={'#'+d.id} aria-current={page===d.id?'page':undefined}>
      <span className="nav-icon" aria-hidden="true">{d.icon}</span><span><b>{d.label}</b><small>{d.caption}</small></span>
    </a>)}
    <div className="nav-foot"><span className="live-dot"/> Local data<small>Jezero · 1.2 × 1.3 km<br/>Scientific prototype</small></div>
  </nav>;
}
