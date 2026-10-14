import sys, numpy as np; sys.path.insert(0,'.'); import render; from PIL import Image
tris = render.gather(sys.argv[1]); b=(np.array([-0.27,0.53,-0.27]), np.array([0.27,0.97,0.27]))
sheet = Image.new('RGB', (600*3, 600), 'white')
for i,y in enumerate((0, 25, 60)): sheet.paste(render.render(tris, y, W=600, H=600, bounds=b), (600*i, 0))
sheet.save(sys.argv[2])
