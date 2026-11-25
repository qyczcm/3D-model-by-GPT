import os
os.environ['QT_QPA_PLATFORM']='offscreen'
import FreeCAD as App, Part
from FreeCAD import Vector as V
from PySide import QtGui, QtCore
try:
    from PySide import QtWidgets
except ImportError:
    QtWidgets=QtGui
app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
font_id=QtGui.QFontDatabase.addApplicationFont(r'C:\Windows\Fonts\msyh.ttc')
font_names=QtGui.QFontDatabase.applicationFontFamilies(font_id)
assert font_names, 'Chinese font could not load'
font_family=font_names[0]
root=r'C:\Users\boxing\Desktop\硬件电路\拳击相关\3D'
base=os.path.join(root,'透明对称弧面罩_v3_铁柱槽')
upper=Part.read(base+'_上罩.step');lower=Part.read(base+'_下罩.step')
pcb=Part.read(r'C:\Users\boxing\Downloads\发光拳击球3D_PCB1_2_2026-11-13.step')
img=QtGui.QImage(1600,900,QtGui.QImage.Format_ARGB32);img.fill(QtGui.QColor('white'))
p=QtGui.QPainter(img);p.setRenderHint(QtGui.QPainter.Antialiasing)
def text(x,y,s,size=22,color='#263445'):
    p.setPen(QtGui.QColor(color));p.setFont(QtGui.QFont(font_family,size));p.drawText(x,y,s)
text(55,62,'v3 · 贯通铁柱槽 / 接口收紧',30)
text(55,110,'以下为实际 STEP 几何截面；蓝色为罩体，深色为电路板与元件。',17)
scale=15
def section(shape,x):
    face=Part.Face(Part.makePolygon([V(x,-45,-15),V(x,10,-15),V(x,10,20),V(x,-45,20),V(x,-45,-15)]))
    return shape.section(face)
def panel(center,x,title):
    text(center-290,180,title,23)
    def point(y,z):return QtCore.QPointF(center+(y+15.7215)*scale,510-(z-0.8)*scale)
    p.setPen(QtGui.QPen(QtGui.QColor('#d5dce4'),1,QtCore.Qt.DashLine))
    p.drawLine(point(-36,0.8),point(4,0.8))
    for shape,color,width in [(upper,'#16849e',2.5),(lower,'#16849e',2.5),(pcb,'#324962',1.6)]:
        sec=section(shape,x)
        p.setPen(QtGui.QPen(QtGui.QColor(color),width))
        for e in sec.Edges:
            vs=e.discretize(Deflection=0.025)
            for a,b in zip(vs[:-1],vs[1:]):p.drawLine(point(a.y,a.z),point(b.y,b.z))
    p.setPen(QtGui.QPen(QtGui.QColor('#d97a18'),2));p.setBrush(QtGui.QColor('#f6c889'))
    p.drawEllipse(point(-15.7215,5.25),scale,scale)
    p.setBrush(QtCore.Qt.NoBrush)
    text(center-110,280,'Ø2 mm 铁柱',19,'#a45a0c')
    p.setPen(QtGui.QPen(QtGui.QColor('#a45a0c'),1.5));p.drawLine(point(-15.7215,6.25),QtCore.QPointF(center,290))
panel(405,17.9545,'主罩中部截面')
panel(1195,38.65,'接口端壁截面')
text(65,752,'槽宽 2.2 mm · 圆弧槽底壁厚 1.2 mm · 沿 PCB 长度方向贯通',20)
text(65,800,'铁柱底部高于模型最高元件约 1 mm；接口预留约 0.25 mm 名义装配间隙。',18)
text(65,848,'装配间隙不代表发泡密封；上下壳锁合结构尚未设计。',17,'#616d7b')
p.end();assert img.save(base+'_截面预览.png')
print('Preview saved')
