"""Empaquetar fuentes y capturas sin tocar GLB anteriores. Tres ZIP independientes."""
from pathlib import Path
import zipfile,json,hashlib,html
root=Path.cwd();base=Path('build/g2c4');destination=root.parent
reports=sorted(Path('docs/maniqui/g2c4').rglob('*'))
code=sorted(Path('tools/maniqui').glob('g2c4_*'))
code=[x for x in code if x.is_file()]
# Offline evidence gallery; images are captures, no generated illustrations.
page=['<!doctype html><html lang="es"><meta charset="utf-8"><title>COPOX G2-C4 · evidencia real</title><style>body{font:16px system-ui;background:#eee;color:#222;margin:2rem}img{max-width:100%;height:auto}section{background:white;padding:1rem;margin:1rem 0}a{color:#125b9a}</style><h1>COPOX G2-C4 · SIN APROBAR</h1><p>B2: limpieza regional conservada. A/A2 y C rechazados. No ABC. Godot4.7.2 real; V3 inmutable. Las copias compatibles no tienen expresiones faciales funcionales.</p>']
for label in ['B2','A','A2','B','C']:
 page.append('<section><h2>'+label+'</h2>')
 for im in sorted((base/'laminas_finales').glob(label+'_*.png')):
  rel=im.relative_to(base);page.append(f'<h3>{html.escape(im.stem)}</h3><a href="{rel}"><img loading="lazy" src="{rel}"></a>')
 page.append('</section>')
page.append('</html>');(base/'index.html').write_text('\n'.join(page))
packages={
 'COPOX_G2C4_MAESTROS_SIN_APROBAR_2026-10-14.zip':[(Path('assets/maniqui/maniqui_v0_3_r3_g2c3_v3_rapado_oreja_izquierda_SIN_APROBAR.glb'),'V3_BASE_INMUTABLE.glb')]+[(x,'modelos/'+x.name) for x in sorted((base/'models').glob('*.glb'))]+[(x,str(x)) for x in reports+code if x.is_file()],
 'COPOX_G2C4_GODOT472_COMPAT_LIMITADA_2026-10-14.zip':[(x,'compat/'+x.name) for x in sorted((base/'godot').glob('*_compat.glb'))]+[(x,str(x)) for x in reports if x.is_file()],
 'COPOX_G2C4_CAPTURAS_REPORTES_2026-10-14.zip':[(base/'index.html','index.html')]+[(x,str(x.relative_to(base))) for folder in ['godot/captures','godot/captures_v2','godot/captures_v3','laminas','laminas_finales'] for x in sorted((base/folder).rglob('*.png'))]+[(x,'diagnostico/'+x.name) for x in sorted(base.glob('*.png'))]+[(x,str(x)) for x in reports+code if x.is_file()]+[(x,'diagnostico/'+x.name) for x in sorted((base/'godot').glob('godot_report*.json'))]
}
manifest={}
for name,files in packages.items():
 dest=destination/name
 if dest.exists():raise FileExistsError(dest)
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p,arc in files:z.write(p,arc)
 with zipfile.ZipFile(dest) as z:assert z.testzip() is None
 manifest[name]={'path':str(dest),'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'files':len(files)}
(base/'paquetes.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
