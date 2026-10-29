"""Native-resolution Pillow scenes on a shared 960x540 design coordinate system."""
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from .timeline import smooth, envelope


def find_font(preferred=None):
    candidates = [preferred] if preferred else []
    candidates += ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"]
    for path in candidates:
        if path and Path(path).is_file():
            return str(path)
    raise FileNotFoundError("No CJK font found; set style.font to an installed .ttf/.ttc font")


class Canvas:
    def __init__(self, image, font):
        self.image, self.draw, self.font = image, ImageDraw.Draw(image), font
        self.scale = min(image.width/960, image.height/540)
        self.ox = (image.width - 960*self.scale)/2
        self.oy = (image.height - 540*self.scale)/2
        self.fonts = {}

    def point(self, x, y):
        return self.ox+x*self.scale, self.oy+y*self.scale

    def box(self, box):
        return (*self.point(*box[:2]), *self.point(*box[2:]))

    def line(self, points, color, width=1):
        self.draw.line(self.box(points), fill=color, width=max(1, round(width*self.scale)))

    def ellipse(self, box, color, width=None):
        if width is None:
            self.draw.ellipse(self.box(box), fill=color)
        else:
            self.draw.ellipse(self.box(box), outline=color, width=max(1, round(width*self.scale)))

    def arc(self, box, start, end, color, width=1):
        self.draw.arc(self.box(box), start, end, fill=color, width=max(1, round(width*self.scale)))

    def text(self, x, y, text, size, color, anchor="mm", max_width=None):
        # Shrink long titles to the supplied design width instead of clipping.
        pixels = max(8, round(size*self.scale))
        while True:
            if pixels not in self.fonts:
                self.fonts[pixels] = ImageFont.truetype(self.font, pixels)
            font = self.fonts[pixels]
            if max_width is None or font.getlength(text) <= max_width*self.scale or pixels <= 8:
                break
            pixels -= 1
        self.draw.text(self.point(x,y), text, font=font, fill=color, anchor=anchor)


class Renderer:
    def __init__(self, config):
        self.c = config
        self.w, self.h = config["video"]["width"], config["video"]["height"]
        self.font = find_font(config.get("style", {}).get("font"))
        self.accent = np.array(config.get("style", {}).get("accent", [65,210,225]))
        self.particles = {}
        for i,s in enumerate(config["scenes"]):
            rng = np.random.default_rng(config["seed"]+i)
            n = s.get("particles", 360)
            self.particles[s["id"]] = (rng.uniform(0,2*np.pi,n), rng.uniform(170,580,n), rng.uniform(.03,.13,n), rng.choice([1,1,1,2],n))
        scale = min(self.w/960, self.h/540)
        yy,xx = np.mgrid[0:self.h,0:self.w]
        glow = np.exp(-(((xx-self.w/2)/(240*scale))**2+((yy-(self.h/2-22*scale))/(180*scale))**2))
        base = np.zeros((self.h,self.w,3),dtype=np.uint8)
        for k,v in enumerate((5,10,22)):
            base[:,:,k] = np.clip(v+glow*self.accent[k]*.14,0,255)
        self.background = Image.fromarray(base)
        d = Canvas(self.background,self.font)
        for x in range(0,961,60): d.line((x,0,x,540),(11,22,36))
        for y in range(0,541,60): d.line((0,y,960,y),(11,22,36))

    def color(self, gain=1):
        return tuple(int(v) for v in np.clip(self.accent*gain,0,255))

    def ring(self, im, scene, local):
        # Normalize scene timing to the twelve-second reference choreography.
        t = local/scene["duration"]*12
        light = Image.new("RGB",im.size)
        d = Canvas(light,self.font)
        intro = smooth(0,1,t)
        collapse = smooth(.8,4.6,t)
        angles,radii,speeds,sizes = self.particles[scene["id"]]
        for a0,r0,speed,size in zip(angles,radii,speeds,sizes):
            a = a0+t*speed
            r = r0*(1-collapse)+(76+25*math.sin(a0*3))*collapse+7*math.sin(t*1.1+a0*2)*collapse
            x,y = 480+math.cos(a)*r*1.25,232+math.sin(a)*r*.65
            d.ellipse((x-size,y-size,x+size,y+size),self.color((.5+.45*math.sin(a0)**2)*intro))
        for j in range(3):
            reveal = smooth(3.4+j*.22,4.7+j*.22,t)
            r = 75+j*12+3*math.sin(t+j)
            d.arc((480-r*1.28,232-r*.67,480+r*1.28,232+r*.67),t*30+j*120,t*30+j*120+240*reveal,self.color(.8*reveal),2)
        if 4.8<t<6.5:
            r = 110+(t-4.8)*180
            d.ellipse((480-r,232-r*.6,480+r,232+r*.6),self.color(.6*(1-smooth(4.8,6.5,t))),2)
        glow = light.filter(ImageFilter.GaussianBlur(9*d.scale))
        im = Image.fromarray(np.minimum(np.asarray(im,dtype=np.uint16)+np.asarray(glow,dtype=np.uint16)*2+np.asarray(light,dtype=np.uint16),255).astype(np.uint8))
        d = Canvas(im,self.font)
        title = smooth(5,6,t)
        if title>0:
            d.text(480,346+12*(1-title),scene.get("title","从代码，到声光"),38,tuple(int(v*title) for v in (229,246,250)),max_width=830)
            d.text(480,397,scene.get("subtitle",""),18,tuple(int(v*title) for v in (130,173,191)),max_width=830)
        else:
            labels=scene.get("intro_labels",["正在生成粒子场","让秩序，从噪声中浮现"])
            d.text(480,380,labels[0 if t<2.7 else -1],24,(163,209,220),max_width=830)
        return im

    def title_card(self, im, scene, local):
        d = Canvas(im,self.font)
        reveal = float(smooth(0, min(.8,scene["duration"]/3), local))
        d.line((400,195,400+160*reveal,195),self.color(),3)
        d.text(480,262+15*(1-reveal),scene.get("title","HNova"),52,(229,246,250),max_width=830)
        d.text(480,326,scene.get("subtitle",""),22,(130,173,191),max_width=830)
        return im

    def frame(self, time):
        im = self.background.copy()
        for scene in self.c["scenes"]:
            if scene["start"] <= time < scene["start"]+scene["duration"]:
                local = time-scene["start"]
                im = self.ring(im,scene,local) if scene["type"]=="particle-ring" else self.title_card(im,scene,local)
                alpha = float(envelope(local,scene["duration"],scene.get("fade_in",.4),scene.get("fade_out",.6)))
                im = Image.blend(self.background,im,alpha)
                break
        if self.c.get("style",{}).get("show_hud",True):
            d = Canvas(im,self.font)
            d.text(42,30,self.c.get("brand","HNOVA / CODE STUDIO"),14,(135,174,190),"la",600)
            d.text(918,30,self.c.get("label","EXPERIMENT 001"),14,(100,135,156),"ra",250)
            d.line((42,497,918,497),(27,51,68),2)
            d.line((42,497,42+876*time/self.c["video"]["duration"],497),self.color(),2)
            d.text(42,510,"PROCEDURAL VISUALS + SYNTHESIZED SOUND",12,(97,137,158),"la")
            d.text(918,510,f'{time:05.2f} / {self.c["video"]["duration"]:.2f}',12,(97,137,158),"ra")
        return im
