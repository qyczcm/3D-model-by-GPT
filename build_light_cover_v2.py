import FreeCAD as App, Part, os, json
from FreeCAD import Vector
root=r'C:\Users\boxing\Desktop\硬件电路\拳击相关\3D'
base=os.path.join(root,'透明对称弧面罩_v2_定位版')
assert not os.path.exists(base+'.FCStd'), 'v2 exists'
doc=App.openDocument(os.path.join(root,'透明对称弧面罩_v1.FCStd'))
doc.Label='透明对称弧面罩 v2 — PCB定位试装版'
pcb=Part.read(r'C:\Users\boxing\Downloads\发光拳击球3D_PCB1_2_2026-11-13.step')
cx,cy,cz=17.9545,-15.7215,0.8
outer=Part.makeBox(42,38,22,Vector(cx-21,cy-19,cz-11));outer=outer.makeFillet(8,outer.Edges)
lower_features=[];upper_features=[]
# Four edge seats; right pair flank the connector root.
for x,y in [(0.2,-25),(0.2,-8),(33.7,-23.8),(33.7,-9.5)]:
 lower_features.append(Part.makeBox(2.3,2,10.1,Vector(x,y,-10.2)).common(outer))
 upper_features.append(Part.makeBox(2.3,2,10.1,Vector(x,y,1.7)).common(outer))
# Side fences have 0.2mm nominal clearance to the rectangular PCB main edges.
fences=[(-2.8,-25,3.367,2),(-2.8,-8,3.367,2),(35.142,-25,3.5,2),(35.142,-6,3.5,2),(16,-34,3,3.091),(16,-0.534,3,3.0)]
for x,y,w,d in fences:
 lower_features.append(Part.makeBox(w,d,10.9,Vector(x,y,-10.2)).common(outer))
 upper_features.append(Part.makeBox(w,d,10.9,Vector(x,y,0.9)).common(outer))
upper_obj=doc.getObject('UpperCover');lower_obj=doc.getObject('LowerCover')
new_lower=lower_obj.Shape.multiFuse(lower_features).removeSplitter()
new_upper=upper_obj.Shape.multiFuse(upper_features).removeSplitter()
checks={'upper_valid':new_upper.isValid(),'lower_valid':new_lower.isValid(),'upper_solids':len(new_upper.Solids),'lower_solids':len(new_lower.Solids),'upper_pcb_interference_mm3':new_upper.common(pcb).Volume,'lower_pcb_interference_mm3':new_lower.common(pcb).Volume,'cover_interference_mm3':new_upper.common(new_lower).Volume}
print(json.dumps(checks))
assert checks['upper_valid'] and checks['lower_valid'] and checks['upper_solids']==1 and checks['lower_solids']==1
assert max(checks['upper_pcb_interference_mm3'],checks['lower_pcb_interference_mm3'],checks['cover_interference_mm3'])<1e-5
for obj,shape,label in [(upper_obj,new_upper,'上罩—压脚与限位筋'),(lower_obj,new_lower,'下罩—托台与限位筋')]:
 obj.Shape=shape;obj.Label=label;obj.DesignNote='板上下各0.10mm名义间隙，板侧0.20mm；右侧两托台支撑接口根部；未含上下壳锁合结构；接触区铜箔与实物公差待核对'
 obj.ViewObject.Transparency=65
notes=doc.addObject('App::FeaturePython','FitNotes');notes.Label='定位与试装说明'
for key,value in [('VerticalTotalClearance',0.2),('SideClearance',0.2),('SupportWidth',2.3),('SupportLength',2.0)]:
 notes.addProperty('App::PropertyLength',key,'Fit');setattr(notes,key,value)
notes.addProperty('App::PropertyString','Warning');notes.Warning='闭合后限制PCB移动，非过盈夹紧。必须另行锁合上下壳。STEP不代表完整铜箔/焊点，试装前核对接触区。'
doc.recompute();Gui.activeDocument().activeView().viewAxonometric();Gui.activeDocument().activeView().fitAll()
doc.saveAs(base+'.FCStd')
for obj,suffix in [(upper_obj,'上罩'),(lower_obj,'下罩')]:
 obj.Shape.exportStep(base+'_'+suffix+'.step')
 test=Part.read(base+'_'+suffix+'.step');assert len(test.Solids)==1 and test.isValid()
Part.export([upper_obj,lower_obj],base+'_外壳.step')
# Exploded preview only; restore placements and transparency afterwards.
upper_obj.Placement.Base.z=14;lower_obj.Placement.Base.z=-14
upper_obj.ViewObject.Transparency=15;lower_obj.ViewObject.Transparency=15
doc.recompute();Gui.activeDocument().activeView().fitAll()
Gui.activeDocument().activeView().saveImage(base+'_分解预览.png',1400,1200,'White')
upper_obj.Placement.Base.z=0;lower_obj.Placement.Base.z=0
upper_obj.ViewObject.Transparency=65;lower_obj.ViewObject.Transparency=65
doc.recompute();Gui.activeDocument().activeView().fitAll()
print('Saved '+base)

