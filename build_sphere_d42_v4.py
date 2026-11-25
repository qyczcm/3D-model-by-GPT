"""Rebuild V3 at D42, preserving the original D44 files and PCB geometry."""
import os,json,hashlib
import FreeCAD as App,Part
from FreeCAD import Vector as V
from build_sphere_d44_v2_neck import ROOT,rr,NX

NAME='球形外壳_D42_V4_USB露出4mm'
OUT=os.path.join(ROOT,NAME)
PREVIOUS=os.path.join(ROOT,'球形外壳_D44_V3_USB露出4mm','球形外壳_D44_V3_USB露出4mm.FCStd')
CX,CY,CZ=13.98905,-12.991,0.8
R,WALL=21.0,1.5

def log(value): print(value,flush=True)
def digest(path):
    with open(path,'rb') as f:return hashlib.sha256(f.read()).hexdigest()
def ring(ro,ri,z,h):
    return Part.makeCylinder(ro,h,V(CX,CY,z)).cut(Part.makeCylinder(ri,h,V(CX,CY,z)))

def build():
    os.makedirs(OUT,exist_ok=True)
    dest=os.path.join(OUT,NAME+'.FCStd')
    assert not os.path.exists(dest),'Refusing to overwrite existing V4'
    previous_hash=digest(PREVIOUS)
    doc=App.openDocument(PREVIOUS)
    pcb=doc.PCBReference.Shape.copy()
    rod=doc.RodReference.Shape.copy()
    tip=pcb.BoundBox.YMin+4
    outer=Part.makeSphere(R,V(CX,CY,CZ))
    inner=Part.makeSphere(R-WALL,V(CX,CY,CZ))
    topclip=Part.makeBox(100,120,50,V(-30,-70,CZ))
    lowclip=Part.makeBox(100,120,50,V(-30,-70,CZ-50))
    shell=outer.cut(inner)
    upper,lower=shell.common(topclip),shell.common(lowclip)
    # Same 0.8 mm male lap and 0.2 mm radial adhesive gap as V3.
    collar=ring(20,18.7,-0.2,1).common(outer)
    lip=ring(19.5,18.7,CZ,1.8).cut(ring(19.6,19.3,1.4,0.4))
    socket=ring(19.7,18.5,CZ,2)
    lower=lower.multiFuse([collar,lip]).removeSplitter()
    upper=upper.cut(socket).removeSplitter()
    groove_void=Part.makeCylinder(2,80,V(NX,-60,7.4),V(0,1,0)).fuse(Part.makeBox(4,80,30,V(NX-2,-60,7.4)))
    groove_outer=Part.makeCylinder(3.5,80,V(NX,-60,7.4),V(0,1,0)).fuse(Part.makeBox(7,80,30,V(NX-3.5,-60,7.4)))
    upper=upper.fuse(groove_outer.common(outer).cut(groove_void)).cut(groove_void).removeSplitter()
    log('D42 sphere, lap and 4 mm groove created')
    seats=[(.2,-12,1.8,2),(.2,-24,1.8,2),(25.9,-5,1.8,2),(25.9,-20,1.8,2),(6.5,-26.9,1.5,1.8),(19.7,-26.9,1.5,1.8)]
    lower_features=[];upper_features=[]
    for x,y,w,h in seats:
        lower_features.append(Part.makeBox(w,h,29.9,V(x,y,-30)).common(outer))
        upper_features.append(Part.makeBox(w,h,30,V(x,y,1.7501)).common(outer))
    fences=[(-.7,-12,1.5017,2),(-.7,-24,1.5017,2),(27.1764,-5,1.5,2),(27.1764,-20,1.5,2),(7,.214,2,1.5),(20,.214,2,1.5),(4,-27.7,2,1.5),(22,-27.7,2,1.5)]
    for x,y,w,h in fences:
        lower_features.append(Part.makeBox(w,h,30.7,V(x,y,-30)).common(outer))
        upper_features.append(Part.makeBox(w,h,30,V(x,y,.9)).common(outer))
    lower=lower.multiFuse(lower_features).removeSplitter()
    upper=upper.multiFuse(upper_features).removeSplitter()
    pcb_exit=Part.makeBox(11.6456,33.9,2.1001,V(8.0224,-60,-.25))
    lower=lower.cut(pcb_exit).removeSplitter()
    upper=upper.cut(pcb_exit).cut(groove_void).removeSplitter()
    log('Supports rebuilt against the smaller sphere')
    # Begin the rounded transition wholly inside the sphere so no exposed
    # loft end-cap remains at the shoulder. Keep the USB segment straight.
    profiles=[rr(-26.5-11.5*t,15+7*(1-t)**2,-4.97-5.53*(1-t)**2,3.8,2)
              for t in [0,.25,.5,.75,1]]
    transition=Part.makeLoft(profiles,True,False)
    straight=Part.Face(rr(tip,15,-4.97,3.8,2)).extrude(V(0,-38-tip,0))
    neck_outer=transition.fuse(straight).removeSplitter()
    cavity=Part.Face(rr(tip+1.5,11.8456,-3.47,2.3,.65)).extrude(V(0,-24.3-(tip+1.5),0))
    usb_exit=Part.Face(rr(tip-.5,9.44,-3.37,1.1,.3)).extrude(V(0,3,0))
    neck=neck_outer.cut(cavity).cut(usb_exit).cut(pcb_exit).cut(outer).removeSplitter()
    neck_up,neck_low=neck.common(topclip),neck.common(lowclip)
    for x in [NX-6.8,NX+6.1]:
        # V3 rails began ahead of the new nose before it was trimmed; retain
        # their exposed-front form and continue them through the new shoulder.
        rail=Part.makeBox(.7,-32.5-tip,1.6,V(x,tip,.4)).common(neck_outer).cut(cavity).cut(usb_exit).cut(pcb_exit).cut(outer)
        rail_socket=Part.makeBox(1,-32.35-(tip-.15),1.35,V(x-.15,tip-.15,.8)).cut(outer)
        neck_low=neck_low.fuse(rail)
        neck_up=neck_up.cut(rail_socket)
    upper=upper.fuse(neck_up).removeSplitter()
    lower=lower.fuse(neck_low).removeSplitter()
    log('Protection neck rebuilt; USB exposure kept at 4 mm')
    for label,shape in [('upper',upper),('lower',lower)]:
        assert shape.isValid() and len(shape.Solids)==1,(label,shape.isValid(),len(shape.Solids))
        assert abs(shape.BoundBox.YMin-tip)<1e-6,(label,'nose position')
        assert abs(shape.BoundBox.XLength-42)<1e-5,(label,'diameter',shape.BoundBox.XLength)
    assert upper.common(lower).Volume<1e-6,'Halves overlap'
    assert upper.common(rod).Volume<1e-6 and lower.common(rod).Volume<1e-6,'Rod interference'
    assert upper.common(groove_void).Volume<1e-6 and lower.common(groove_void).Volume<1e-6,'Groove obstruction'
    clashes=[]
    for i,solid in enumerate(pcb.Solids):
        for label,shape in [('upper',upper),('lower',lower)]:
            if shape.BoundBox.intersect(solid.BoundBox):
                vol=shape.common(solid).Volume
                if vol>1e-6:clashes.append({'solid':i,'shell':label,'volume':vol})
        if i%100==0:log('PCB collision check '+str(i))
    assert not clashes,clashes
    log('Complete PCB and component collision checks passed')
    doc.UpperShell.Shape=upper;doc.LowerShell.Shape=lower
    doc.UpperShell.Label='上罩—D42／4mmU槽／USB露出4mm'
    doc.LowerShell.Label='下罩—D42／胶封止口／PCB支撑'
    doc.Label='球形外壳 D42 V4 — 主板居中，USB露出4mm'
    p=doc.DesignParameters
    p.SphereDiameter=42;p.ShellWall=1.5;p.BoardOffsetTowardPort=0
    for key,value in [('SphereCenterX',CX),('SphereCenterY',CY),('SphereCenterZ',CZ),('CenterShiftTowardUSB',1.01765)]:
        if key not in p.PropertiesList:p.addProperty('App::PropertyLength',key,'Dimensions')
        setattr(p,key,value)
    p.AssemblyNotes='D42重建版，PCB和铁柱坐标未变。保留胶封止口，未增加卡扣或螺丝。试装通电及插拔后连续封胶，固化时使用夹具。'
    n=doc.NeckParameters
    n.Notes='USB露出4mm；PCB板舌前端露出约1.46mm。保护颈过渡已适配D42球体。端壁和直段底壁1.5mm；接口和上下壳接缝需封胶。'
    if 'PreviousVersion' not in p.PropertiesList:p.addProperty('App::PropertyString','PreviousVersion','Version')
    p.PreviousVersion=PREVIOUS
    doc.recompute();doc.saveAs(dest)
    exports=[]
    for label,shape in [('上罩',upper),('下罩',lower)]:
        path=os.path.join(OUT,NAME+'_'+label+'.step')
        shape.exportStep(path)
        check=Part.read(path)
        assert check.isValid() and len(check.Solids)==1
        assert abs(check.BoundBox.XLength-42)<1e-4
        assert abs(check.BoundBox.YMin-pcb.BoundBox.YMin-4)<1e-4
        exports.append(path)
    assembly_path=os.path.join(OUT,NAME+'_上下壳.step')
    Part.makeCompound([upper,lower]).exportStep(assembly_path)
    check=Part.read(assembly_path)
    assert check.isValid() and len(check.Solids)==2
    assert digest(PREVIOUS)==previous_hash,'Previous file changed'
    report={'sphere_diameter_mm':42,'main_wall_mm':1.5,'center_xyz_mm':[CX,CY,CZ],
        'center_shift_toward_USB_mm':1.01765,'slot_width_mm':4,'rod_diameter_mm':2,
        'usb_protrusion_mm':tip-pcb.BoundBox.YMin,'pcb_clashes':clashes,
        'single_solid_halves':True,'shell_overlap_mm3':upper.common(lower).Volume,
        'groove_obstruction_mm3':0,'rod_collision_mm3':0,
        'groove_floor_to_highest_component_mm':3.9-pcb.BoundBox.ZMax,
        'STEP_roundtrip_passed':True,'previous_model_preserved':True,'previous_sha256':previous_hash,
        'previous_model_path':PREVIOUS,'validation_limits':'Geometric checks only; printing, adhesive and foaming process need prototype verification.'}
    with open(os.path.join(OUT,'validation.json'),'w',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
    log(json.dumps(report,ensure_ascii=True));log('D42 V4 saved')

if __name__=='__main__':build()
