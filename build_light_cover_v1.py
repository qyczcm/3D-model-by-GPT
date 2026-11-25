import FreeCAD as App, Part, Import, os, json
from FreeCAD import Vector
out=r'C:\Users\boxing\Desktop\硬件电路\拳击相关\3D'
source=r'C:\Users\boxing\Downloads\发光拳击球3D_PCB1_2_2026-11-13.step'
doc=App.newDocument('SymmetricLightCoverV1')
Import.insert(source,doc.Name)
refs=[o for o in doc.Objects if hasattr(o,'Shape') and not o.Shape.isNull()]
pcb=Part.read(source)
params=doc.addObject('App::FeaturePython','DesignParameters')
params.Label='设计参数（第一版外形样机）'
for name,val in [('Width',42.0),('Depth',38.0),('Height',22.0),('Wall',1.2),('RoundRadius',8.0),('MidplaneZ',0.8)]:
 params.addProperty('App::PropertyLength',name,'Dimensions');setattr(params,name,val)
cx,cy,cz=17.9545,-15.7215,0.8
outer=Part.makeBox(42,38,22,Vector(cx-21,cy-19,cz-11))
outer=outer.makeFillet(8,outer.Edges)
inner=Part.makeBox(39.6,35.6,19.6,Vector(cx-19.8,cy-17.8,cz-9.8))
inner=inner.makeFillet(6.8,inner.Edges)
hollow=outer.cut(inner)
# Symmetric side opening spanning the board tongue and underside USB body.
opening=Part.makeBox(20,12.8,10,Vector(33.8,-22.0805,cz-5))
hollow=hollow.cut(opening)
upper=hollow.common(Part.makeBox(100,100,50,Vector(-30,-60,cz)))
lower=hollow.common(Part.makeBox(100,100,50,Vector(-30,-60,cz-50)))
for name,label,shape in [('UpperCover','透明上罩',upper),('LowerCover','透明下罩',lower)]:
 obj=doc.addObject('PartDesign::Feature',name);obj.Label=label;obj.Shape=shape
 obj.ViewObject.ShapeColor=(0.72,0.91,0.96);obj.ViewObject.Transparency=75;obj.ViewObject.LineColor=(0.15,0.45,0.55)
 obj.addProperty('App::PropertyString','DesignNote');obj.DesignNote='上下镜像外形；壁厚1.2mm；固定结构及插头包胶空间待实物确认'
doc.recompute()
Gui.activeDocument().activeView().viewAxonometric();Gui.activeDocument().activeView().fitAll()
checks={'upper_valid':upper.isValid(),'lower_valid':lower.isValid(),'upper_solids':len(upper.Solids),'lower_solids':len(lower.Solids),'pcb_interference_mm3':round(hollow.common(pcb).Volume,6),'outer_dimensions_mm':[42,38,22],'shell_wall_mm':1.2}
print(json.dumps(checks))
base=os.path.join(out,'透明对称弧面罩_v1')
if os.path.exists(base+'.FCStd'): raise RuntimeError('Output already exists; not overwriting')
doc.saveAs(base+'.FCStd')
Part.export([doc.getObject('UpperCover'),doc.getObject('LowerCover')],base+'_外壳.step')
Gui.activeDocument().activeView().saveImage(base+'_预览.png',1400,1000,'White')

