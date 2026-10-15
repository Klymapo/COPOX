"""Immutable, versioned delivery bundles. No previous package is overwritten."""
from pathlib import Path
import zipfile,json,hashlib
root=Path('build/g2c4_continuacion');docs=Path('docs/maniqui/g2c4/continuacion_2026-10-15');target=Path('/workspace')
sources=json.loads((root/'godot/sources.json').read_text())
common=[(p,'reportes/'+str(p.relative_to(docs))) for p in docs.rglob('*') if p.is_file()]
common += [(p,'codigo/'+p.name) for p in Path('tools/maniqui').glob('g2c4_*.py')]
common += [(Path('tools/maniqui/g2c4_godot.gd'),'codigo/g2c4_godot.gd'),(Path('tools/maniqui/g2c4_validate.cjs'),'codigo/g2c4_validate.cjs')]
common += [(Path('docs/maniqui/g2c4/CONTINUACION_2026-10-15.md'),'reportes/INVESTIGACION.md')]
jobs={
 'MAESTROS_SIN_APROBAR':[(Path(p),'modelos/'+Path(p).name) for p in sources.values()],
 'GODOT472_COMPAT_LIMITADA':[(p,'godot/'+p.name) for p in (root/'godot').iterdir() if p.is_file() and p.suffix in ('.glb','.json','.gd','.godot','.log','.cjs')],
 'CAPTURAS_REPORTES':[(p,str(p.relative_to(root))) for p in [root/'index.html',*list((root/'laminas').glob('*.png')),*list((root/'godot/captures_v3').rglob('*.png'))]]}
manifest=[]
for kind,items in jobs.items():
 path=target/f'COPOX_G2C4_CONTINUACION_{kind}_2026-10-15.zip'
 if path.exists():raise FileExistsError(path)
 with zipfile.ZipFile(path,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p,name in items+common:z.write(p,name)
 with zipfile.ZipFile(path) as z:assert z.testzip() is None
 manifest.append({'path':str(path),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(docs/'PAQUETES.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
