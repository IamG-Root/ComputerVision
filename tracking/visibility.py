"""Optional soft visibility weighting, never a hard gate for unverified geometry."""
import math

def inside(point, polygon):
    x,y = point; result = False
    for a,b in zip(polygon, polygon[1:]+polygon[:1]):
        if (a[1]>y)!=(b[1]>y) and x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:
            result = not result
    return result

def quality(point, geometry):
    if not geometry:
        return 1.0
    polygon = geometry.get('polygon', [])
    margin = geometry.get('margin', .5)
    if not polygon or inside(point, polygon):
        score = 1.0
    else:
        distance = float('inf')
        for a,b in zip(polygon,polygon[1:]+polygon[:1]):
            dx,dy = b[0]-a[0], b[1]-a[1]
            t = max(0,min(1,((point[0]-a[0])*dx+(point[1]-a[1])*dy)/max(1e-12,dx*dx+dy*dy)))
            distance = min(distance, math.hypot(point[0]-a[0]-t*dx,point[1]-a[1]-t*dy))
        score = 1.0 if distance <= margin else .5
    if any(inside(point,p) for p in geometry.get('exclusions', [])):
        score *= .5
    return score

def footprint(x,z,height,pitch,hfov,vfov,orientation):
    """Same angular ray convention as module/utils.py. None if horizon crosses FOV."""
    out=[]
    pitch=math.radians(pitch)
    for h,v in [(-1,-1),(1,-1),(1,1),(-1,1)]:
        rx=math.tan(math.radians(h*hfov/2))
        ry=-math.tan(math.radians(v*vfov/2))
        ydir=math.cos(pitch)*ry-math.sin(pitch)
        zdir=math.sin(pitch)*ry+math.cos(pitch)
        if ydir>=-1e-6:
            return None
        wx,wz=rx*(-height/ydir),zdir*(-height/ydir)
        transforms={1:(wx,wz),2:(wz,-wx),3:(-wx,-wz),4:(-wz,wx)}
        dx,dz=transforms[orientation]
        out.append([x+dx,z+dz])
    return out
