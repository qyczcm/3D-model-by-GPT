"""Extend D44 V1 with a split PCB protection neck; preserve the sphere and U slot."""
import os, json, math
import FreeCAD as App, Part
from FreeCAD import Vector as V
ROOT=r'C:\Users\boxing\Desktop\硬件电路\拳击相关\3D'
OUT=os.path.join(ROOT,'球形外壳_D44_V2_护颈')
CX,CY,CZ=13.98905,-11.97335,0.8
NX=13.8452

def rr(y,width,bottom,top,r):
    xl,xh=NX-width/2,NX+width/2
    p=lambda x,z:V(x,y,z)
    q=r/math.sqrt(2)
    edges=[Part.makeLine(p(xl+r,bottom),p(xh-r,bottom)),
        Part.Arc(p(xh-r,bottom),p(xh-r+q,bottom+r-q),p(xh,bottom+r)).toShape(),
        Part.makeLine(p(xh,bottom+r),p(xh,top-r)),
        Part.Arc(p(xh,top-r),p(xh-r+q,top-r+q),p(xh-r,top)).toShape(),
        Part.makeLine(p(xh-r,top),p(xl+r,top)),
        Part.Arc(p(xl+r,top),p(xl+r-q,top-r+q),p(xl,top-r)).toShape(),
        Part.makeLine(p(xl,top-r),p(xl,bottom+r)),
        Part.Arc(p(xl,bottom+r),p(xl+r-q,bottom+r-q),p(xl+r,bottom)).toShape()]
    return Part.Wire(edges)

def log(s): print(s,flush=True)

def build():
    os.makedirs(OUT,exist_ok=True)
    dest=os.path.join(OUT,'球形外壳_D44_V2_护颈.FCStd')
    # Rebuild only this task's V2 output; the source V1 is always preserved.
    source=os.path.join(ROOT,'球形外壳_D44_V1','球形外壳_D44_V1.FCStd')
    doc=App.openDocument(source)
    up=doc.getObject('UpperShell');low=doc.getObject('LowerShell')
    oldup,oldlow=up.Shape.copy(),low.Shape.copy()
    pcb=doc.getObject('PCBReference').Shape
    rod=doc.getObject('RodReference').Shape
    sphere=Part.makeSphere(22,V(CX,CY,CZ))
    topclip=Part.makeBox(100,120,50,V(-30,-70,CZ))
    lowclip=Part.makeBox(100,120,50,V(-30,-70,CZ-50))
    # A quadratic taper flattens toward the straight nose. Keep the connector
    # length extruded: an unconstrained long loft makes its underside too thin.
    profiles=[rr(-28-10*t,15+9*(1-t)**2,-4.97-7.03*(1-t)**2,3.8,2)
              for t in [0,0.25,0.5,0.75,1]]
    transition=Part.makeLoft(profiles,True,False)
    straight=Part.Face(rr(-48.8,15,-4.97,3.8,2)).extrude(V(0,10.8,0))
    neck_solid=transition.fuse(straight).removeSplitter()
    cavity=Part.Face(rr(-47.3,11.8456,-3.47,2.3,0.65)).extrude(V(0,23,0))
    # Opening follows the connector body, rather than exposing the board tongue.
    aperture=Part.Face(rr(-53,9.44,-3.37,1.1,0.3)).extrude(V(0,6.2,0))
    neck=neck_solid.cut(cavity).cut(aperture).cut(sphere).removeSplitter()
    log('Protective neck geometry created')
    added_upper=neck.common(topclip)
    added_lower=neck.common(lowclip)
    # Two longitudinal internal lap rails add alignment and a gluing overlap.
    rails=[]; sockets=[]
    for x in [NX-6.8,NX+6.1]:
        rail=Part.makeBox(0.7,16,1.6,V(x,-48.5,0.4)).common(neck_solid).cut(cavity).cut(aperture).cut(sphere)
        rails.append(rail)
        sockets.append(Part.makeBox(1.0,16.3,1.35,V(x-0.15,-48.65,0.8)).cut(sphere))
    rail_shape=rails[0].fuse(rails[1])
    socket_shape=sockets[0].fuse(sockets[1])
    added_lower=added_lower.fuse(rail_shape).removeSplitter()
    added_upper=added_upper.cut(socket_shape).removeSplitter()
    upper=oldup.fuse(added_upper).removeSplitter()
    lower=oldlow.fuse(added_lower).removeSplitter()
    log('Split halves and neck lap rails created')
    for name,s in [('upper',upper),('lower',lower)]:
        assert s.isValid() and len(s.Solids)==1,(name,s.isValid(),len(s.Solids))
    assert upper.common(lower).Volume<1e-6,'Upper/lower clash'
    assert oldup.cut(upper).Volume<1e-6 and oldlow.cut(lower).Volume<1e-6,'Original shell was removed'
    # Nothing new is allowed to enter the existing U-slot or the seated tooling rod.
    slot=Part.makeCylinder(2,80,V(NX,-60,7.4),V(0,1,0)).fuse(Part.makeBox(4,80,30,V(NX-2,-60,7.4)))
    additions=added_upper.fuse(added_lower)
    assert additions.common(slot).Volume<1e-6,'U-slot changed'
    assert additions.common(rod).Volume<1e-6,'Tooling rod clash'
    clashes=[]
    for i,s in enumerate(pcb.Solids):
        if additions.BoundBox.intersect(s.BoundBox):
            volume=additions.common(s).Volume
            if volume>1e-6:clashes.append({'solid':i,'volume':volume,'bounds':str(s.BoundBox)})
    log(json.dumps({'clashes':clashes}))
    assert not clashes,'PCB collision'
    log('Geometry and PCB checks passed')
    up.Shape=upper;low.Shape=lower
    up.Label='上罩—原球面U槽＋PCB保护颈'
    low.Label='下罩—原球面止口＋PCB保护颈'
    doc.Label='球形外壳 D44 V2 — PCB保护颈，仅露USB口'
    params=doc.addObject('App::FeaturePython','NeckParameters')
    params.Label='保护颈与USB出口参数'
    for key,val in [('NeckTipWidth',15),('NeckNominalTop',3.8),('NeckTipBottom',-4.97),
                    ('USBOpeningWidth',9.44),('USBOpeningHeight',4.47),('USBBodyClearance',0.25),
                    ('NoseWall',1.5),('StraightBottomWall',1.5),('NeckLapThickness',0.7),('NeckLapHeight',1.2),
                    ('NeckLapSideGap',0.15),('NeckLapTopGap',0.15)]:
        params.addProperty('App::PropertyFloat',key,'Dimensions_mm');setattr(params,key,val)
    params.addProperty('App::PropertyString','Notes')
    params.Notes='原球体与4mmU槽未去料。延伸颈包覆板舌及USB本体，端口露出约0.46mm。护颈两侧有搭接导轨；接口边缘、两侧接缝和球壳接缝均需封胶。实际线材试插后定稿。'
    doc.getObject('DesignParameters').AssemblyNotes='先试装通电与线材插拔检查，再连续涂胶闭合；护颈两侧接缝与USB本体周围另行封胶，勿堵USB插口。未设计螺丝；固化时需夹具。'
    doc.recompute();doc.saveAs(dest)
    for shape,label in [(upper,'上罩'),(lower,'下罩')]:
        path=os.path.join(OUT,'球形外壳_D44_V2_护颈_'+label+'.step')
        shape.exportStep(path)
        check=Part.read(path);assert check.isValid() and len(check.Solids)==1
    Part.makeCompound([upper,lower]).exportStep(os.path.join(OUT,'球形外壳_D44_V2_护颈_上下壳.step'))
    report={'valid_single_solids':True,'new_pcb_interference_mm3':0,'shell_interference_mm3':upper.common(lower).Volume,
            'original_shell_removed_mm3':oldup.cut(upper).Volume+oldlow.cut(lower).Volume,
            'U_slot_intrusion_mm3':additions.common(slot).Volume,
            'tooling_rod_interference_mm3':additions.common(rod).Volume,
            'neck_tip_y':-48.8,'straight_bottom_wall_mm':1.5,'usb_front_y':pcb.BoundBox.YMin,
            'usb_protrusion_mm':-48.8-pcb.BoundBox.YMin}
    with open(os.path.join(OUT,'validation.json'),'w',encoding='utf-8') as f:json.dump(report,f,indent=2)
    log(json.dumps(report));log('Saved '+dest)

if __name__=='__main__':build()
