#!/usr/bin/env python3
"""Comparativas reales de dos GLB renderizados con exactamente el mismo rasterizador."""
from PIL import Image, ImageDraw, ImageFont
import sys
from pathlib import Path

def main(before,after,fullout,closeout):
    a=Image.open(before).convert('RGB');b=Image.open(after).convert('RGB')
    if a.size!=b.size:
        raise RuntimeError('Las vistas deben tener exactamente la misma resolucion')
    w,h=a.size
    dest=Image.new('RGB',(w,h*2),'#eee9e2')
    dest.paste(a,(0,0));dest.paste(b,(0,h))
    pen=ImageDraw.Draw(dest)
    for y,s in [(0,'BASE · Maniqui v0.2b'),(h,'CANDIDATO · Maniqui v0.3 — NO APROBADO')]:
        pen.rectangle((0,y,w,y+29),fill='#252830')
        pen.text((16,y+8),s,fill='white')
    Path(fullout).parent.mkdir(parents=True,exist_ok=True)
    dest.save(fullout)
    block=w//4
    y0,y1=int(h*0.12),int(h*0.52)
    zoom=Image.new('RGB',(block*4,(y1-y0)*2),'#eee9e2')
    for i in range(4):
        region=(i*block,y0,(i+1)*block,y1)
        zoom.paste(a.crop(region),(i*block,0))
        zoom.paste(b.crop(region),(i*block,y1-y0))
    d=ImageDraw.Draw(zoom)
    d.rectangle((0,0,block*4,26),fill='#242832'); d.text((14,7),'CABEZA · ANTES (fila superior) / DESPUES (fila inferior)',fill='white')
    zoom.save(closeout)
    print('Capturas comparativas:',fullout,closeout)
if __name__=='__main__':
    if len(sys.argv)!=5:raise SystemExit('Uso: comparar_v03.py antes.png despues.png completo.png cabezas.png')
    main(*sys.argv[1:])
