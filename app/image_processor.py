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


def prepare_post_image(title: str, image_url: str, output: Path, timeout: int = 25, category: str = "Software") -> tuple[Path, str]:
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
            od.rectangle((0, 0, 1200, 630), fill=(0, 0, 0, 45))
            od.rectangle((0, 330, 1200, 630), fill=(0, 0, 0, 190))
            canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
            draw = ImageDraw.Draw(canvas)
            used = "remote_image"
        except Exception:
            used = "generated_card"

    if used == "generated_card":
        for y in range(630):
            ratio = y / 629
            draw.line((0, y, 1200, y), fill=(int(20 + 24 * ratio), int(30 + 42 * ratio), int(54 + 72 * ratio)))
        draw.rounded_rectangle((65, 55, 1135, 575), radius=36, fill=(255, 255, 255), outline=(226, 231, 241), width=3)
        draw.rounded_rectangle((100, 95, 260, 255), radius=28, fill=(34, 103, 255))
        draw.text((148, 122), "S", font=_font(92, True), fill=(255, 255, 255))
        text_x, text_y, max_chars = 310, 112, 29
        title_fill, sub_fill = (20, 28, 45), (75, 86, 108)
        badge_y = 430
    else:
        text_x, text_y, max_chars = 65, 370, 38
        title_fill, sub_fill = (255, 255, 255), (232, 236, 245)
        badge_y = 65

    category_text = (category or "Software")[:32]
    badge_font = _font(23, True)
    box = draw.textbbox((0, 0), category_text, font=badge_font)
    badge_w = box[2] - box[0] + 38
    draw.rounded_rectangle((65, badge_y, 65 + badge_w, badge_y + 52), radius=16, fill=(34, 103, 255))
    draw.text((84, badge_y + 12), category_text, font=badge_font, fill=(255, 255, 255))

    lines = textwrap.wrap(title.strip() or "Software Download", width=max_chars)[:3]
    font = _font(52 if len(lines) <= 2 else 44, True)
    y = text_y
    for line in lines:
        draw.text((text_x, y), line, font=font, fill=title_fill)
        y += font.size + 8
    draw.text((text_x, y + 12), "Latest Version • Software Information", font=_font(26), fill=sub_fill)

    if used == "generated_card":
        draw.rounded_rectangle((310, 500, 625, 555), radius=16, fill=(20, 28, 45))
        draw.text((350, 513), "Latest Software Download", font=_font(22, True), fill=(255, 255, 255))

    canvas.save(output, "JPEG", quality=91, optimize=True, progressive=True)
    return output, used
