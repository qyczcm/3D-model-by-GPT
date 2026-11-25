"""Read-only enclosure sizing study; does not modify any FCStd model."""
import os,json,math
import FreeCAD as App,Part
import numpy as np
from FreeCAD import Vector as V
ROOT=r'C:\Users\boxing\Desktop\硬件电路\拳击相关\3D'
doc=App.openDocument(os.path.join(ROOT,'球形外壳_D44_V3_USB露出4mm','球形外壳_D44_V3_USB露出4mm.FCStd'))
pcb=doc.PCBReference.Shape
clip=Part.makeBox(80,70,60,V(-20,-26.1,-30))
main_solids=[]
samples=[]
for i,s in enumerate(pcb.Solids):
    if s.BoundBox.YMax < -26.1: continue
    m=s if s.BoundBox.YMin>=-26.1 else s.common(clip)
    if m.isNull(): continue
    main_solids.append(m)
    pts=m.tessellate(0.01)[0]
    samples.extend((p.x,p.y,p.z,i) for p in pts)
main=Part.makeCompound(main_solids)
arr=np.asarray(samples)
pts=arr[:,:3]
current=np.array([13.98905,-11.97335,0.8])
centered=np.array([13.98905,-12.991,0.8])
def radius(c):return float(np.sqrt(((pts-c)**2).sum(axis=1)).max())
best=centered.copy()
for step in [0.5,0.1,0.02,0.005]:
    for repeat in range(30):
        options=[best+np.array([dx*step,dy*step,0]) for dx in [-1,0,1] for dy in [-1,0,1]]
        nxt=min(options,key=radius)
        if radius(nxt)>=radius(best)-1e-10:break
        best=nxt
centers={'current':current,'main_board_centered':centered,'optimized_xy':best}
out={'study_scope':'PCB geometry behind y=-26.1; port tongue remains in a redesigned neck. Supports and seam require redesign.',
     'sample_count':len(pts),'sample_tolerance_mm':0.01,'centers':{},'options':[]}
for name,c in centers.items():
    distances=np.sqrt(((pts-c)**2).sum(axis=1))
    worst=int(np.argmax(distances))
    # Board substrate alone sets the worst radial clearance in the seam plane.
    substrate=pts[arr[:,3]==0]
    xy_rad=float(np.sqrt(((substrate[:,:2]-c[:2])**2).sum(axis=1)).max())
    out['centers'][name]={'xyz':c.tolist(),'component_envelope_radius':float(distances[worst]),
        'worst_point_and_solid_index':arr[worst].tolist(),'substrate_xy_radius':xy_rad}
    print(name,out['centers'][name],flush=True)
for name in ['current','main_board_centered']:
    c=centers[name]
    xy_req=out['centers'][name]['substrate_xy_radius']
    for diameter,wall,lip in [(44,1.5,0.8),(42,1.5,0.8),(41,1.5,0.8),(40,1.5,0.8),(40,1.2,0.6),(39,1.2,0.6),(38,1.2,0.6)]:
        r=diameter/2
        inner=Part.makeSphere(r-wall,V(*c))
        outside=0.0
        # Bounding boxes are conservative: skip all solids whose entire box is
        # inside the sphere, rather than boolean hundreds of small components.
        for s in main_solids:
            b=s.BoundBox
            far2=sum(max(abs(lo-cc),abs(hi-cc))**2 for lo,hi,cc in
                     [(b.XMin,b.XMax,c[0]),(b.YMin,b.YMax,c[1]),(b.ZMin,b.ZMax,c[2])])
            if far2>(r-wall)**2:outside+=s.cut(inner).Volume
        # Match the original lower-shell male lap/anchor in the PCB height band.
        joint_outer=Part.makeCylinder(r-wall+0.5,2.8,V(c[0],c[1],-0.2))
        joint_inner=Part.makeCylinder(r-wall-lip,2.8,V(c[0],c[1],-0.2))
        joint=joint_outer.cut(joint_inner)
        joint_clash=0.0
        for s in main_solids:
            b=s.BoundBox
            if b.ZMax < -0.2 or b.ZMin>2.6:continue
            far_xy2=max(abs(b.XMin-c[0]),abs(b.XMax-c[0]))**2+max(abs(b.YMin-c[1]),abs(b.YMax-c[1]))**2
            if far_xy2>(r-wall-lip)**2:joint_clash+=s.common(joint).Volume
        item={'center':name,'diameter':diameter,'wall':wall,'lip':lip,
              'spherical_clearance_sample_mm':r-wall-radius(c),'body_outside_inner_sphere_mm3':outside,
              'joint_radial_clearance_sample_mm':r-wall-lip-xy_req,'joint_interference_mm3':joint_clash,
              'sphere_volume_reduction_percent':100*(1-(diameter/44)**3)}
        out['options'].append(item)
        print(item,flush=True)
path=os.path.join(ROOT,'diameter_optimization_analysis.json')
with open(path,'w',encoding='utf-8') as f:json.dump(out,f,indent=2)
print('Analysis saved',flush=True)
