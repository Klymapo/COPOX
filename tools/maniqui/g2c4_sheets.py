"""Láminas compuestas sólo de capturas reales de Godot, sin retoque del modelo."""
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
root=Path('build/g2c4/godot/captures_v3');out=Path('build/g2c4/laminas_finales');out.mkdir(exist_ok=True)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
viewsets={'cuatro_vistas':['frontal','perfil_izquierdo','perfil_derecho','posterior'],'detalles':['tres_cuartos_izquierdo','tres_cuartos_derecho','posterior_derecho','inferior_mandibula','detalle_oreja_derecha','detalle_ojos','detalle_ojo_izquierdo','detalle_ojo_derecho','detalle_union_cuello'],'poses':['pose_Nod_frontal','pose_HeadShake_perfil_derecho','pose_Wave_frontal','pose_Sit-pose_perfil_derecho']}
for k in ['A','A2','B','B2','C']:
 for group,views in viewsets.items():
  cols=3 if group=='detalles' else 4;blocks=(len(views)+cols-1)//cols
  sheet=Image.new('RGB',(480*cols,blocks*1000),'white');draw=ImageDraw.Draw(sheet)
  for i,v in enumerate(views):
   col=i%cols;block=i//cols
   for r,model in enumerate(['V3',k]):
    x=col*480;y=block*1000+r*500
    sheet.paste(Image.open(root/model/(v+'.png')).resize((480,480)),(x,y+20));draw.text((x+6,y+1),model+' | '+v.replace('_',' '),fill='black',font=font)
  sheet.save(out/f'{k}_{group}_antes_despues.png')
 views=['frontal','perfil_izquierdo','perfil_derecho','inferior_mandibula'];sheet=Image.new('RGB',(1920,510),'white');draw=ImageDraw.Draw(sheet)
 for i,v in enumerate(views):
  sheet.paste(Image.open(root/k/('editados_'+v+'.png')).resize((480,480)),(i*480,30));draw.text((i*480+6,7),k+' | TRIANGULOS EDITADOS | '+v,fill='black',font=font)
 sheet.save(out/f'{k}_triangulos_editados.png')
