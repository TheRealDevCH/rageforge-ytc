from pathlib import Path
from PIL import Image

src = Path(__file__).with_name("ytc_icon_source.png")
out = Path(__file__).with_name("icon.ico")
img = Image.open(src).convert("RGBA")
sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
icons = [img.resize(s, Image.Resampling.LANCZOS) for s in sizes]
icons[-1].save(out, format="ICO", sizes=[(i.width, i.height) for i in icons])
print(out)
