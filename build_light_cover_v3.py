import FreeCAD as App, Part, os, json, time
from FreeCAD import Vector as V

ROOT = r'C:\Users\boxing\Desktop\硬件电路\拳击相关\3D'
BASE = os.path.join(ROOT, '透明对称弧面罩_v3_铁柱槽')
def log(message):
    print(message, flush=True)

def build():
    assert not os.path.exists(BASE + '.FCStd'), 'Output already exists'
    doc = App.openDocument(os.path.join(ROOT, '透明对称弧面罩_v2_定位版.FCStd'))
    doc.Label = '透明弧面罩 v3 — 贯通铁柱槽与收紧接口'
    up = doc.getObject('UpperCover')
    low = doc.getObject('LowerCover')
    pcb = Part.read(r'C:\Users\boxing\Downloads\发光拳击球3D_PCB1_2_2026-11-13.step')
    log('Loaded v2 and PCB')
    outer = Part.makeBox(42,38,22,V(-3.0455,-34.7215,-10.2))
    outer = outer.makeFillet(8,outer.Edges)
    inner = Part.makeBox(39.6,35.6,19.6,V(-1.8455,-33.5215,-9.0))
    inner = inner.makeFillet(6.8,inner.Edges)
    original_wall = outer.cut(inner)
    patch = original_wall.common(Part.makeBox(20,12.8,10,V(33.8,-22.0805,-4.2)))
    cutters = [Part.makeBox(16,11.685,2.1,V(33.5,-21.523,-0.25)),
               Part.makeBox(10,9.605,4.775,V(38.375,-20.524,-3.492)),
               Part.makeBox(2.2,3.7,1.1,V(37.701,-17.713,1.35))]
    clearance = cutters[0].multiFuse(cutters[1:])
    patch = patch.cut(clearance)
    upper_patch = patch.common(Part.makeBox(100,100,50,V(-30,-60,0.8)))
    lower_patch = patch.common(Part.makeBox(100,100,50,V(-30,-60,-49.2)))
    upper = up.Shape.fuse(upper_patch).removeSplitter()
    lower = low.Shape.fuse(lower_patch).removeSplitter()
    log('Reduced interface aperture')
    axis_y, axis_z = -15.7215, 5.35
    # 2.2 mm open U slot, 1.2 mm walls; seated rod bottom at z=4.25.
    channel_outer = Part.makeCylinder(2.3,60,V(-10,axis_y,axis_z),V(1,0,0)).fuse(
        Part.makeBox(60,4.6,20,V(-10,axis_y-2.3,axis_z)))
    slot = Part.makeCylinder(1.1,60,V(-10,axis_y,axis_z),V(1,0,0)).fuse(
        Part.makeBox(60,2.2,20,V(-10,axis_y-1.1,axis_z)))
    channel = channel_outer.common(outer).cut(slot)
    log('Built channel geometry')
    upper = upper.fuse(channel).cut(slot).cut(clearance).removeSplitter()
    log('United upper shell')
    assert upper.isValid() and lower.isValid()
    assert len(upper.Solids)==1 and len(lower.Solids)==1
    additions = channel.fuse(patch)
    collision_volume = 0.0
    # Only the additions can introduce new PCB collisions; v2 is already checked.
    for i,s in enumerate(pcb.Solids):
        if additions.BoundBox.intersect(s.BoundBox):
            collision_volume += additions.common(s).Volume
        if i % 100 == 0:
            log('PCB validation '+str(i))
    assert collision_volume < 1e-5, 'PCB interference: '+str(collision_volume)
    log('Validated PCB clearance')
    assert upper.common(lower).Volume < 1e-5
    rod = Part.makeCylinder(1,52,V(-8,axis_y,5.25),V(1,0,0))
    assert upper.common(rod).Volume < 1e-5
    # Conservative global vertical separation, avoiding expensive full-assembly distance search.
    vertical_gap = rod.BoundBox.ZMin - pcb.BoundBox.ZMax
    assert vertical_gap >= 0.999
    up.Shape=upper; low.Shape=lower
    up.Label='上罩—贯通U槽与定位压脚'
    low.Label='下罩—缩口与定位托台'
    params=doc.addObject('App::FeaturePython','RodSlotParameters')
    params.Label='铁柱槽与接口配合尺寸'
    for key,val in [('RodDiameter',2.0),('SlotWidth',2.2),('SlotWall',1.2),
                    ('SlotArcCenterZ',5.35),('SeatedRodAxisZ',5.25),
                    ('SlotCenterY',axis_y),('PortClearance',0.25)]:
        params.addProperty('App::PropertyFloat',key,'Dimensions_mm');setattr(params,key,val)
    params.addProperty('App::PropertyString','Notes')
    params.Notes='铁柱沿X方向贯通；柱底高于模型最高元件约1mm；接口0.25mm名义间隙非密封；上下壳锁合仍待设计'
    ref=doc.addObject('PartDesign::Feature','RodReference')
    ref.Label='直径2mm铁柱参考（不随外壳STEP导出）';ref.Shape=rod
    doc.recompute()
    doc.saveAs(BASE+'.FCStd')
    for shape,suffix in [(upper,'上罩'),(lower,'下罩')]:
        shape.exportStep(BASE+'_'+suffix+'.step')
        check=Part.read(BASE+'_'+suffix+'.step')
        assert check.isValid() and len(check.Solids)==1
    Part.makeCompound([upper,lower]).exportStep(BASE+'_外壳.step')
    result={'upper_valid':upper.isValid(),'lower_valid':lower.isValid(),
            'upper_solids':len(upper.Solids),'lower_solids':len(lower.Solids),
            'new_features_pcb_interference_mm3':collision_volume,
            'rod_global_vertical_clearance_mm':vertical_gap,'base':BASE}
    log(json.dumps(result,ensure_ascii=False))
    return result

if __name__=='__main__':
    build()
