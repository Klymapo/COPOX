"""Assemble same-camera Blender GLB captures; does not synthesize imagery."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path('build/g2c9')
CAPTURES = ROOT / 'captures_tpose'
OUTPUT = ROOT / 'COMPARATIVA_T_POSE_REAL.png'
CANDIDATES = [('G2-C8 · BASE', 'COLOR'),
              ('G2-C9 H · INVISIBLE', 'HUECOS'),
              ('G2-C9 F · RECHAZADO', 'GLABELA')]
VIEWS = [('frontal', 'T pose esquelética · frontal'),
         ('perfil_derecho', 'T pose esquelética · perfil'),
         ('detalle_rostro', 'Rostro · mismo encuadre')]


def main():
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 19)
    result = Image.new('RGB', (1920, 1995), (40, 40, 40))
    pen = ImageDraw.Draw(result)
    for row, (view, caption) in enumerate(VIEWS):
        for col, (label, candidate) in enumerate(CANDIDATES):
            source = CAPTURES / candidate / (view + '.png')
            frame = Image.open(source).convert('RGB')
            assert frame.size == (640, 640)
            result.paste(frame, (col * 640, row * 665 + 25))
            pen.text((col * 640 + 8, row * 665 + 3),
                     label + ' | ' + caption, fill='white', font=font)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    result.save(OUTPUT)
    print(OUTPUT)


if __name__ == '__main__':
    main()
