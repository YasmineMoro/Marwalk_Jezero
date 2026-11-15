"""One explicit Mars scientific/local/Three.js coordinate convention."""
ORIGIN=(4351286.,1094535.)
def local_to_projected(x,y):return x+ORIGIN[0],y+ORIGIN[1]
def projected_to_local(x,y):return x-ORIGIN[0],y-ORIGIN[1]
def local_to_scene(x,y,z,z_origin=-2500.):return x-600,z-z_origin,-y-650
def scene_to_local(x,up,south,z_origin=-2500.):return x+600,-south-650,up+z_origin
