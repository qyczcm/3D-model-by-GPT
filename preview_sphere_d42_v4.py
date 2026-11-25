"""Load and preview the finished D42 model through the existing local RPC."""
import xmlrpc.client,socket
socket.setdefaulttimeout(70)
rpc=xmlrpc.client.ServerProxy('http://127.0.0.1:9875',allow_none=True)
code=r'''
import os
import FreeCAD as App,FreeCADGui as Gui
d42_dir=r'C:\Users\boxing\Desktop\硬件电路\拳击相关\3D\球形外壳_D42_V4_USB露出4mm'
d42_name='球形外壳_D42_V4_USB露出4mm'
d42_path=os.path.join(d42_dir,d42_name+'.FCStd')
d42_doc=next((d for d in App.listDocuments().values() if os.path.normcase(os.path.normpath(d.FileName))==os.path.normcase(os.path.normpath(d42_path))),None)
if d42_doc is None:d42_doc=App.openDocument(d42_path)
App.setActiveDocument(d42_doc.Name)
for o in d42_doc.Objects:
    if hasattr(o,'Shape'):
        o.ViewObject.Visibility=True
        o.touch()
for o in [d42_doc.UpperShell,d42_doc.LowerShell]:
    o.ViewObject.ShapeColor=(.70,.90,.96)
    o.ViewObject.LineColor=(.17,.42,.50)
    o.ViewObject.Transparency=65
    o.ViewObject.DisplayMode='Flat Lines'
    o.ViewObject.LineWidth=1.0
    o.ViewObject.Deviation=.1
d42_doc.PCBReference.ViewObject.ShapeColor=(.12,.28,.57)
d42_doc.PCBReference.ViewObject.DisplayMode='Flat Lines'
d42_doc.RodReference.ViewObject.ShapeColor=(.92,.52,.10)
d42_doc.recompute()
Gui.activeDocument().activeView().viewAxonometric()
Gui.activeDocument().activeView().fitAll()
Gui.updateGui()
d42_doc.save()
print('D42 model loaded and saved:',d42_doc.FileName)
'''
r=rpc.execute_code(code,60)
print(r,flush=True)
assert r.get('success'),r
r=rpc.execute_code("Gui.activeDocument().activeView().saveImage(os.path.join(d42_dir,d42_name+'_装配预览.png'),1500,1200,'White')\nprint('Preview saved')",60)
print(r,flush=True)
assert r.get('success'),r
