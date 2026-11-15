import math
import numpy as np
import pytest
from backend.engine import Terrain,NoRoute

def test_flat_roundtrip():
 t=Terrain(np.zeros((8,8)),1);p,_=t.path((.5,-.5),(5.5,-5.5));m=t.metrics(p)
 assert m['horizontal_m']==pytest.approx(5*math.sqrt(2));assert m['ascent_m']==0
 back,_=t.path((5.5,-5.5),(.5,-.5));assert t.metrics(back)['surface_m']==pytest.approx(m['surface_m'])
def test_known_slope():
 z=np.tile(np.arange(8)*.1,(8,1));t=Terrain(z,1)
 assert t.slope[2,2]==pytest.approx(math.degrees(math.atan(.1)))
 p,_=t.path((.5,-.5),(5.5,-.5));assert t.metrics(p)['ascent_m']==pytest.approx(.5)
 with pytest.raises(NoRoute):t.path((.5,-.5),(5.5,-.5),max_slope=1)
def test_obstacle_nodata_and_corners():
 t=Terrain(np.zeros((8,8)),1);start=(.5,-.5);end=(5.5,-.5)
 direct,_=t.path(start,end);detour,_=t.path(start,end,blocked=[(2.5,-.5)])
 assert t.metrics(detour)['surface_m']>t.metrics(direct)['surface_m']
 t.valid[:,3]=False
 with pytest.raises(NoRoute):t.path(start,end)
 t=Terrain(np.zeros((2,2)),1);t.valid[0,1]=False;t.valid[1,0]=False
 with pytest.raises(NoRoute):t.path((.5,-.5),(1.5,-1.5))
def test_outside():
 t=Terrain(np.zeros((3,3)),1)
 for p in [(-1,0),(3,0),(0,-3)]:
  with pytest.raises(NoRoute):t.cell(p)
