"""Build the agreed spherical enclosure using FreeCAD's bundled Python.
All dimensions in mm. STEP exports exclude PCB and tooling rod.
"""
import os, json, math
import FreeCAD as App
import Part
from FreeCAD import Vector as V

ROOT = r'C:\Users\boxing\Desktop\硬件电路\拳击相关\3D'
OUT = os.path.join(ROOT, '球形外壳_D44_V1')
SOURCE = r'C:\Users\boxing\Downloads\20261124-发光拳击球.step'
CX, CY, CZ = 13.98905, -11.97335, 0.8
ROD_X = 13.8452
RADIUS, WALL = 22.0, 1.5
SLOT_WIDTH, SLOT_WALL, SLOT_AXIS_Z = 4.0, 1.5, 7.4

def log(s):
    print(s, flush=True)

def ring(ro, ri, z, h):
    return Part.makeCylinder(ro,h,V(CX,CY,z)).cut(Part.makeCylinder(ri,h,V(CX,CY,z)))

def build():
    os.makedirs(OUT, exist_ok=True)
    dest=os.path.join(OUT,'球形外壳_D44_V1.FCStd')
    assert not os.path.exists(dest), 'Existing model will not be overwritten'
    pcb=Part.read(SOURCE)
    outer=Part.makeSphere(RADIUS,V(CX,CY,CZ))
    inner=Part.makeSphere(RADIUS-WALL,V(CX,CY,CZ))
    shell=outer.cut(inner)
    topbox=Part.makeBox(100,120,50,V(-30,-70,CZ))
    bottombox=Part.makeBox(100,120,50,V(-30,-70,CZ-50))
    upper=shell.common(topbox)
    lower=shell.common(bottombox)
    log('Spherical envelope complete')

    # Male inner lap: 0.8 radial thickness, 1.8 axial engagement.
    # Anchor collar joins the male lap to the lower spherical wall.
    collar=ring(21.0,19.7,-0.2,1.0).common(outer)
    lip=ring(20.5,19.7,CZ,1.8)
    glue_pocket=ring(20.6,20.3,1.4,0.4)
    lip=lip.cut(glue_pocket)
    socket=ring(20.7,19.5,CZ,2.0)
    lower=lower.multiFuse([collar,lip]).removeSplitter()
    upper=upper.cut(socket).removeSplitter()
    log('Lap joint and adhesive reservoir complete')

    # External open U channel with continuous floor isolating the electronics.
    channel_outer=Part.makeCylinder(3.5,80,V(ROD_X,-60,SLOT_AXIS_Z),V(0,1,0)).fuse(
        Part.makeBox(7.0,80,30,V(ROD_X-3.5,-60,SLOT_AXIS_Z)))
    channel_void=Part.makeCylinder(2.0,80,V(ROD_X,-60,SLOT_AXIS_Z),V(0,1,0)).fuse(
        Part.makeBox(4.0,80,30,V(ROD_X-2,-60,SLOT_AXIS_Z)))
    channel_wall=channel_outer.common(outer).cut(channel_void)
    upper=upper.fuse(channel_wall).cut(channel_void).removeSplitter()
    log('4mm through channel complete')

    # Four board edge seats, plus a pair beside the tongue root.
    seats=[(0.2,-12,1.8,2),(0.2,-24,1.8,2),
           (25.9,-5,1.8,2),(25.9,-20,1.8,2),
           (6.5,-26.9,1.5,1.8),(19.7,-26.9,1.5,1.8)]
    low_add=[]; up_add=[]
    for x,y,w,d in seats:
        low_add.append(Part.makeBox(w,d,29.9,V(x,y,-30)).common(outer))
        up_add.append(Part.makeBox(w,d,30,V(x,y,1.7501)).common(outer))
    # Side fences provide 0.20mm nominal board clearance; seam gap 0.20mm.
    fences=[(-0.7,-12,1.5017,2),(-0.7,-24,1.5017,2),
            (27.1764,-5,1.5,2),(27.1764,-20,1.5,2),
            (7,0.214,2,1.5),(20,0.214,2,1.5),
            (4,-27.7,2,1.5),(22,-27.7,2,1.5)]
    for x,y,w,d in fences:
        low_add.append(Part.makeBox(w,d,30.7,V(x,y,-30)).common(outer))
        up_add.append(Part.makeBox(w,d,30,V(x,y,0.9)).common(outer))
    lower=lower.multiFuse(low_add).removeSplitter()
    upper=upper.multiFuse(up_add).removeSplitter()
    # The spherical exit crosses the bare tongue ahead of its two small components.
    # 0.25mm clearance around a 11.1456 x 1.6001mm board cross section.
    port=Part.makeBox(11.6456,33.9,2.1001,V(8.0224,-60,-0.25))
    lower=lower.cut(port).removeSplitter()
    upper=upper.cut(port).cut(channel_void).removeSplitter()
    log('Board supports and tongue exit complete')

    for name,shape in [('upper',upper),('lower',lower)]:
        assert shape.isValid() and len(shape.Solids)==1, name+' is not one valid solid'
    assert upper.common(lower).Volume < 1e-6, 'Shell interference'
    clashes=[]
    for i,s in enumerate(pcb.Solids):
        for name,shape in [('upper',upper),('lower',lower)]:
            if shape.BoundBox.intersect(s.BoundBox):
                volume=shape.common(s).Volume
                if volume>1e-6:
                    clashes.append({'solid':i,'shell':name,'volume':volume,'bounds':str(s.BoundBox)})
        if i % 100 == 0: log('PCB collision check '+str(i))
    log(json.dumps({'clashes':clashes}))
    assert not clashes, 'PCB collisions must be corrected'
    rod=Part.makeCylinder(1,52,V(ROD_X,-38,SLOT_AXIS_Z-1),V(0,1,0))
    assert rod.common(upper).Volume<1e-6 and rod.common(lower).Volume<1e-6
    # Trench separation conservatively bounded by its lowest outer wall point.
    min_channel_component_gap=SLOT_AXIS_Z-3.5-pcb.BoundBox.ZMax
    assert min_channel_component_gap>0.6
    log('Geometry validation complete')

    doc=App.newDocument('SphereD44V1')
    doc.Label='球形透光外壳 D44 V1 — 胶封止口与4mm工装槽'
    for name,label,shape in [('UpperShell','上半球—贯通槽与压脚',upper),
                             ('LowerShell','下半球—止口胶槽与支撑',lower),
                             ('PCBReference','新版PCB参考（不导出）',pcb),
                             ('RodReference','直径2mm铁柱参考（不导出）',rod)]:
        obj=doc.addObject('PartDesign::Feature',name);obj.Label=label;obj.Shape=shape
    params=doc.addObject('App::FeaturePython','DesignParameters')
    params.Label='尺寸与装配说明（修改尺寸需重运行源脚本）'
    values={'SphereDiameter':44,'ShellWall':1.5,'BoardOffsetTowardPort':1,
            'SlotWidth':4,'SlotWall':1.5,'SlotFloorZ':5.4,'RodDiameter':2,
            'RodAxisZ':6.4,'LapHeight':1.8,'LapThickness':0.8,
            'LapRadialGlueGap':0.2,'LapTopGap':0.2,
            'AdhesivePocketHeight':0.4,'AdhesivePocketDepth':0.2,
            'PortClearance':0.25,'PCBLowerGap':0.1,'PCBUpperGap':0.15,
            'PCBOverallVerticalPlay':0.25,'BoardSideGap':0.2}
    for key,value in values.items():
        params.addProperty('App::PropertyLength',key,'Dimensions');setattr(params,key,value)
    params.addProperty('App::PropertyString','AssemblyNotes')
    params.AssemblyNotes='先试装与通电检查，再连续涂胶闭合；接口板舌周围另行封胶。未设计螺丝；固化时需外部夹具。STEP不含PCB和铁柱。'
    params.addProperty('App::PropertyString','ValidationLimits')
    params.ValidationLimits='几何无干涉不代表已验证发泡密封/压力/温度。工艺、胶水与实物焊点仍须首件验证。'
    doc.recompute();doc.saveAs(dest)
    for shape,label in [(upper,'上罩'),(lower,'下罩')]:
        path=os.path.join(OUT,'球形外壳_D44_V1_'+label+'.step')
        shape.exportStep(path)
        again=Part.read(path)
        assert again.isValid() and len(again.Solids)==1
    Part.makeCompound([upper,lower]).exportStep(os.path.join(OUT,'球形外壳_D44_V1_上下壳.step'))
    report={'diameter_mm':44,'wall_mm':1.5,'upper_valid':upper.isValid(),
            'lower_valid':lower.isValid(),'upper_solids':len(upper.Solids),
            'lower_solids':len(lower.Solids),'pcb_clashes':clashes,
            'shell_interference_mm3':upper.common(lower).Volume,
            'channel_floor_to_highest_component_vertical_mm':min_channel_component_gap,
            'rod_bottom_to_highest_component_vertical_mm':rod.BoundBox.ZMin-pcb.BoundBox.ZMax,
            'overall_with_pcb_length_mm':CY+RADIUS-pcb.BoundBox.YMin}
    # Machine-generated validation output, not a hand-authored project file.
    with open(os.path.join(OUT,'validation.json'),'w',encoding='utf-8') as f:
        json.dump(report,f,ensure_ascii=False,indent=2)
    log(json.dumps(report,ensure_ascii=True))
    log('Saved '+dest)

if __name__=='__main__':
    build()
