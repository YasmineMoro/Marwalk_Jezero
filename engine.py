"""Experimental Mars raster routing. All spatial quantities use local Mars metres."""
import heapq
import math
import numpy as np

VERSION = 'mars-grid-2.1-native-edges'

def walking_factor(dz, horizontal):
    """Demonstration assumption, NOT a validated astronaut walking law."""
    grade = np.asarray(dz) / np.asarray(horizontal)
    return 1 + 3*np.abs(grade) + 2*np.maximum(grade, 0)

class NoRoute(ValueError):
    pass

class Terrain:
    def __init__(self, z, step=5, slope=None, valid=None, native_z=None, native_slope=None):
        self.z = np.asarray(z, dtype=float)
        self.step = step
        gy, gx = np.gradient(self.z, step)
        self.slope = np.degrees(np.arctan(np.hypot(gx, gy))) if slope is None else slope
        self.valid = np.isfinite(self.z) if valid is None else valid & np.isfinite(self.z)
        self.native_z = native_z
        self.native_slope = native_slope
        self.edges = {}
        if native_z is not None:
            # Every coarse edge is checked at each native pixel centre, never a stride-5 shortcut.
            rr, cc = np.indices(self.z.shape)
            rr, cc = rr*step+int(step//2), cc*step+int(step//2)
            self.z = native_z[rr, cc].astype(float)
            for dr,dc in ((0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)):
                distance=math.hypot(dr,dc)
                total=np.zeros(self.z.shape); time_cost=total.copy(); maximum=total.copy();ok=np.ones(self.z.shape,dtype=bool)
                previous=self.z
                for k in range(1,int(step)+1):
                    r,c=rr+dr*k,cc+dc*k
                    inside=(r>=0)&(r<native_z.shape[0])&(c>=0)&(c<native_z.shape[1])
                    r=np.clip(r,0,native_z.shape[0]-1);c=np.clip(c,0,native_z.shape[1]-1)
                    elevation=native_z[r,c];delta=elevation-previous
                    ok &= inside & np.isfinite(elevation) & np.isfinite(previous)
                    if dr and dc:
                        ar=np.clip(rr+dr*k,0,native_z.shape[0]-1);ac=np.clip(cc+dc*(k-1),0,native_z.shape[1]-1)
                        br=np.clip(rr+dr*(k-1),0,native_z.shape[0]-1);bc=np.clip(cc+dc*k,0,native_z.shape[1]-1)
                        ok &= np.isfinite(native_z[ar,ac]) & np.isfinite(native_z[br,bc])
                    maximum=np.maximum(maximum,np.degrees(np.arctan2(np.abs(delta),distance)))
                    surface=np.hypot(distance,delta);total+=surface;time_cost+=surface*walking_factor(delta,distance)
                    previous=elevation
                self.edges[dr,dc]=(ok,maximum,total,time_cost)

    def cell(self, point):
        x, y = point
        r, c = int(math.floor(-y / self.step)), int(math.floor(x / self.step))
        if not (0 <= r < self.z.shape[0] and 0 <= c < self.z.shape[1]):
            raise NoRoute('Point outside DEM coverage')
        return r, c

    def point(self, cell):
        r, c = cell
        return [(c+.5)*self.step, -(r+.5)*self.step]

    def path(self, start, goal, max_slope=30, weight=0, blocked=(), criterion='slope_cost'):
        s, g = self.cell(start), self.cell(goal)
        allowed = self.valid & (self.slope <= max_slope)
        for p in blocked:
            allowed[self.cell(p)] = False
        if not allowed[s] or not allowed[g]:
            raise NoRoute('Start or destination blocked by slope, obstacle or NoData')
        q = [(0, 0, s)]
        costs, prev = {s: 0.}, {}
        expanded = 0
        while q:
            _, cost, u = heapq.heappop(q)
            if cost != costs[u]: continue
            expanded += 1
            if u == g: break
            for dr, dc in ((0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)):
                v = u[0]+dr, u[1]+dc
                if not (0 <= v[0] < allowed.shape[0] and 0 <= v[1] < allowed.shape[1]) or not allowed[v]: continue
                if dr and dc and (not allowed[u[0]+dr,u[1]] or not allowed[u[0],u[1]+dc]): continue
                d = self.step*math.hypot(dr,dc)
                direction_slope = math.degrees(math.atan2(abs(self.z[v]-self.z[u]), d))
                if direction_slope > max_slope: continue
                surface=math.hypot(d,self.z[v]-self.z[u])
                time_cost=surface*float(walking_factor(self.z[v]-self.z[u],d))
                if self.edges:
                    ok,maximum,surfaces,times=self.edges[dr,dc]
                    if not ok[u] or maximum[u]>max_slope:continue
                    surface,time_cost=surfaces[u],times[u]
                edge_cost=time_cost if criterion=='estimated_time' else surface if criterion=='distance' else d*(1+weight*(max(self.slope[u],self.slope[v])/30)**2)
                nc = cost+edge_cost
                if nc < costs.get(v, float('inf')):
                    costs[v], prev[v] = nc, u
                    h = self.step*math.hypot(v[0]-g[0],v[1]-g[1])
                    heapq.heappush(q,(nc+h,nc,v))
        if g not in costs: raise NoRoute('No path: constraints are incompatible with terrain coverage')
        cells, u = [g], g
        while u != s:
            u = prev[u]; cells.append(u)
        cells.reverse()
        return cells, expanded

    def metrics(self, cells):
        if self.native_z is not None:
            dense=[]
            for a,b in zip(cells,cells[1:]):
                dr,dc=b[0]-a[0],b[1]-a[1]
                dense.extend((a[0]*int(self.step)+int(self.step//2)+dr*k,a[1]*int(self.step)+int(self.step//2)+dc*k) for k in range(int(self.step)))
            last=cells[-1];dense.append((last[0]*int(self.step)+int(self.step//2),last[1]*int(self.step)+int(self.step//2)))
            points=[(c+.5,-r-.5) for r,c in dense]
            z=[float(self.native_z[c]) for c in dense]
            local_slopes=[float(self.native_slope[c]) for c in dense]
        else:
            points = [self.point(c) for c in cells]
            z = [float(self.z[c]) for c in cells]
            local_slopes=[float(self.slope[c]) for c in cells]
        dist = [math.dist(a,b) for a,b in zip(points,points[1:])]
        dz = np.diff(z)
        surface = [math.hypot(d,h) for d,h in zip(dist,dz)]
        time_distance=sum(s*float(walking_factor(h,d)) for s,h,d in zip(surface,dz,dist))
        return dict(coordinates=points, elevations_m=z, horizontal_m=sum(dist), surface_m=sum(surface),time_distance_m=time_distance,
                    ascent_m=float(sum(max(0,h) for h in dz)), descent_m=float(sum(max(0,-h) for h in dz)),
                    max_local_slope_deg=float(max(local_slopes)),max_constraint_slope_deg=float(max(self.slope[c] for c in cells)),
                    mean_local_slope_deg=float(np.mean(local_slopes)),
                    profile=[{'distance_m':float(d),'elevation_m':h} for d,h in zip(np.r_[0,np.cumsum(dist)],z)],
                    example_segment=None if not dist else dict(horizontal_m=dist[0],delta_h_m=float(dz[0]),slope_deg=math.degrees(math.atan2(dz[0],dist[0]))))
