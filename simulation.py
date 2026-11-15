"""Deterministic EVA timeline. Positions and observations are simulated."""
import math
from .engine import walking_factor
def state_at(route,mission,fraction):
    elapsed=mission['elapsed_min']+fraction*(route['total_min']-mission['elapsed_min'])
    cursor=mission['elapsed_min'];completed=list(mission.get('completed_sites',[]))
    coordinates=route['geometry']['coordinates'];position=coordinates[0]
    traversed=0.;phase='completed';next_site='base';remaining_stop=0.;direction=None
    for leg in route['legs']:
        duration=leg['travel_min'];target=leg['target_site']
        if elapsed<cursor+duration and duration>0:
            ratio=max(0,(elapsed-cursor)/duration);covered=0.;covered_distance=0.;pieces=[]
            for index in range(leg['start_index'],leg['end_index']):
                a,b=coordinates[index:index+2];horizontal=math.dist(a,b);dz=route['elevations_m'][index+1]-route['elevations_m'][index]
                distance=math.hypot(horizontal,dz);pieces.append((distance,distance*float(walking_factor(dz,horizontal))))
            goal=ratio*sum(cost for _,cost in pieces)
            for index in range(leg['start_index'],leg['end_index']):
                a,b=coordinates[index:index+2]
                distance,cost=pieces[index-leg['start_index']]
                if covered+cost>=goal:
                    t=(goal-covered)/cost if cost else 0
                    position=[a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])]
                    direction=(math.degrees(math.atan2(b[0]-a[0],b[1]-a[1]))+360)%360
                    covered_distance+=t*distance;break
                covered+=cost;covered_distance+=distance
            traversed+=covered_distance;phase='walking';next_site=target or 'base';break
        cursor+=duration;traversed+=leg['surface_m'];position=coordinates[leg['end_index']]
        stop=leg['observation_min']
        if elapsed<cursor+stop:
            phase='observation';next_site=target;remaining_stop=cursor+stop-elapsed;break
        cursor+=stop
        if target and target not in completed:completed.append(target)
    remaining_sites=[s for s in mission['sites'] if s not in completed]
    return dict(simulation=True,fraction=fraction,phase=phase,position=position,direction_deg=direction,elapsed_min=elapsed,
                remaining_distance_m=max(0,route['surface_m']-traversed),remaining_plan_min=max(0,route['total_min']-elapsed),
                completed_sites=completed,remaining_sites=remaining_sites,next_site=next_site,
                remaining_observation_min=remaining_stop,reserve_after_plan_min=mission['available_min']-route['total_min'])
