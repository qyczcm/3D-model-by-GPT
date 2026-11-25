"""Shorten V2 protection neck for an exact 4 mm USB protrusion."""
import os, json
import FreeCAD as App, Part
from FreeCAD import Vector as V
from build_sphere_d44_v2_neck import ROOT, NX, CZ, rr

NAME='球形外壳_D44_V3_USB露出4mm'
OUT=os.path.join(ROOT,NAME)
os.makedirs(OUT,exist_ok=True)
dest=os.path.join(OUT,NAME+'.FCStd')
assert not os.path.exists(dest), 'V3 already exists'
doc=App.openDocument(os.path.join(ROOT,'球形外壳_D44_V2_护颈','球形外壳_D44_V2_护颈.FCStd'))
up,low=doc.UpperShell,doc.LowerShell
old_up,old_low=up.Shape.copy(),low.Shape.copy()
pcb=doc.PCBReference.Shape
usb_front=pcb.BoundBox.YMin
tip=usb_front+4.0
trim=Part.makeBox(100,tip+70,100,V(-30,-70,-50))
upper=old_up.cut(trim)
lower=old_low.cut(trim)
# Rebuild the 1.5 mm nose wall at its new position. This station crosses the
# PCB tongue, so the aperture includes both the connector and a PCB-edge slot.
collar=Part.Face(rr(tip,15,-4.97,3.8,2)).extrude(V(0,1.5,0))
usb_void=Part.Face(rr(tip-0.5,9.44,-3.37,1.1,0.3)).extrude(V(0,3,0))
pcb_void=Part.makeBox(19.668-8.0224,3,2.1001,V(8.0224,tip-0.5,-0.25))
collar=collar.cut(usb_void.fuse(pcb_void)).removeSplitter()
upper_collar=collar.common(Part.makeBox(100,100,50,V(-30,-60,CZ)))
lower_collar=collar.common(Part.makeBox(100,100,50,V(-30,-60,CZ-50)))
# Continue the existing lower tongue / upper socket at both sides.
for x in [NX-6.8,NX+6.1]:
    socket=Part.makeBox(1.0,20,1.35,V(x-0.15,tip-0.15,CZ))
    upper_collar=upper_collar.cut(socket)
upper=upper.fuse(upper_collar).removeSplitter()
lower=lower.fuse(lower_collar).removeSplitter()
for label,s in [('upper',upper),('lower',lower)]:
    assert s.isValid() and len(s.Solids)==1,(label,s.isValid(),len(s.Solids))
    # The straight nose is planar; the exact bounding minimum is its front face.
    assert abs(s.BoundBox.YMin-tip)<1e-6,(label,s.BoundBox.YMin,tip)
assert upper.common(lower).Volume<1e-6,'Shell clash'
clashes=[]
for i,s in enumerate(pcb.Solids):
    if collar.BoundBox.intersect(s.BoundBox):
        vol=collar.common(s).Volume
        if vol>1e-6: clashes.append((i,vol))
assert not clashes,clashes
# The sphere, U groove and root transitions are behind this unchanged plane.
keep=Part.makeBox(100,80,100,V(-30,-38,-50))
for old,new in [(old_up,upper),(old_low,lower)]:
    a,b=old.common(keep),new.common(keep)
    assert a.cut(b).Volume+b.cut(a).Volume<1e-6,'Sphere or root modified'
assert collar.common(doc.RodReference.Shape).Volume<1e-6,'Rod clash'
up.Shape,low.Shape=upper,lower
up.Label='上罩—USB露出4mm'
low.Label='下罩—USB露出4mm'
doc.Label='球形外壳 D44 V3 — USB露出4mm'
p=doc.NeckParameters
for key,val in [('USBProtrusion',4.0),('NeckFrontY',tip),('ShortenedBy',tip+48.8),('PCBTongueExposed',tip-(-46.7187))]:
    if key not in p.PropertiesList:p.addProperty('App::PropertyFloat',key,'Dimensions_mm')
    setattr(p,key,val)
p.Notes='USB前端相对保护颈端面露出4mm；PCB板舌前端随之露出约1.46mm。端面含USB和PCB板边避让开口，保留1.5mm端壁及两侧搭接。球体、U槽和内部支撑沿用V2。需实际线材试插并对接口周边封胶。'
doc.recompute()
doc.saveAs(dest)
for shape,label in [(upper,'上罩'),(lower,'下罩')]:
    path=os.path.join(OUT,NAME+'_'+label+'.step')
    shape.exportStep(path)
    result=Part.read(path)
    assert result.isValid() and len(result.Solids)==1
    assert abs(result.BoundBox.YMin-usb_front-4.0)<1e-5
Part.makeCompound([upper,lower]).exportStep(os.path.join(OUT,NAME+'_上下壳.step'))
report={'usb_front_y':usb_front,'shell_front_y':tip,'usb_protrusion_mm':tip-usb_front,
        'neck_shortened_mm':tip+48.8,'pcb_tongue_exposed_mm':tip+46.7187,
        'valid_single_solid_halves':True,'shell_interference_mm3':upper.common(lower).Volume,
        'new_PCB_collisions':clashes,'sphere_U_slot_and_root_unchanged':True,
        'exported_STEP_readback_passed':True}
with open(os.path.join(OUT,'validation.json'),'w',encoding='utf-8') as f:json.dump(report,f,indent=2)
print(json.dumps(report),flush=True)
print('Saved V3',flush=True)
