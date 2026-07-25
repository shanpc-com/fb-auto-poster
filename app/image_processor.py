from __future__ import annotations
from io import BytesIO
from pathlib import Path
import textwrap
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps
from .validators import UA


def _font(size: int, bold: bool = False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            pass
    return ImageFont.load_default()


def _download_image(url: str, timeout: int) -> Image.Image:
    r = requests.get(url, headers=UA, timeout=timeout, allow_redirects=True)
    r.raise_for_status()
    return Image.open(BytesIO(r.content)).convert("RGB")


def prepare_post_image(title: str, image_url: str, output: Path, timeout: int = 25) -> tuple[Path, str]:
    """Create a Facebook-ready JPEG. Uses remote artwork when available, otherwise a branded title card."""
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas = Image.new("RGB", (1200, 630), (20, 28, 45))
    draw = ImageDraw.Draw(canvas)

    used = "generated_card"
    if image_url:
        try:
            src = _download_image(image_url, timeout)
            src = ImageOps.fit(src, (1200, 630), method=Image.Resampling.LANCZOS)
            canvas.paste(src)
            overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            od.rectangle((0, 350, 1200, 630), fill=(0, 0, 0, 175))
            canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
            draw = ImageDraw.Draw(canvas)
            used = "remote_image"
        except Exception:
            used = "generated_card"

    # Decorative card background when no remote image exists.
    if used == "generated_card":
        for y in range(630):
            ratio = y / 629
            c = (int(24 + 20 * ratio), int(34 + 34 * ratio), int(58 + 65 * ratio))
            draw.line((0, y, 1200, y), fill=c)
        draw.rounded_rectangle((75, 65, 1125, 565), radius=34, fill=(255, 255, 255), outline=(225, 230, 240), width=3)
        draw.rounded_rectangle((110, 105, 270, 265), radius=28, fill=(34, 103, 255))
        draw.text((158, 132), "S", font=_font(92, True), fill=(255, 255, 255))
        text_x, text_y, max_chars = 320, 120, 28
        title_fill = (20, 28, 45)
        sub_fill = (78, 88, 110)
    else:
        text_x, text_y, max_chars = 70, 395, 38
        title_fill = (255, 255, 255)
        sub_fill = (230, 235, 245)

    lines = textwrap.wrap(title.strip() or "Software Download", width=max_chars)[:3]
    font = _font(54 if len(lines) <= 2 else 46, True)
    y = text_y
    for line in lines:
        draw.text((text_x, y), line, font=font, fill=title_fill)
        y += font.size + 8
    draw.text((text_x, y + 15), "Latest Version • Windows Software", font=_font(27), fill=sub_fill)
    if used == "generated_card":
        draw.rounded_rectangle((320, 420, 610, 490), radius=18, fill=(34, 103, 255))
        draw.text((365, 437), "Download Now", font=_font(28, True), fill=(255, 255, 255))

    canvas.save(output, "JPEG", quality=90, optimize=True, progressive=True)
    return output, used
