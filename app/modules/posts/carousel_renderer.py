import colorsys
import io
import os
from typing import List, Dict, Union

from PIL import Image, ImageDraw, ImageFont

CANVAS_SIZE = 1080
MARGIN = 90

FONT_DIR = r"C:\Windows\Fonts"
FONT_BOLD = os.path.join(FONT_DIR, "segoeuib.ttf")
FONT_REGULAR = os.path.join(FONT_DIR, "segoeui.ttf")

BG_COLOR = (8, 11, 17)
TITLE_COLOR = (255, 255, 255)
BODY_COLOR = (205, 212, 224)
HINT_COLOR = (130, 138, 150)
LINKEDIN_BLUE = (0, 119, 181)

ACCENT_CYAN = tuple(round(c * 255) for c in colorsys.hls_to_rgb(185 / 360, 0.5, 1.0))
ACCENT_PURPLE = tuple(round(c * 255) for c in colorsys.hls_to_rgb(275 / 360, 0.65, 1.0))


def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    words = text.split()
    if not words:
        return []
    lines = []
    current = words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _body_paragraphs(content: Union[str, List[str]]) -> List[str]:
    if isinstance(content, list):
        return [str(p).strip() for p in content if str(p).strip()]
    text = str(content or "")
    return [line.strip().lstrip("•").strip() for line in text.split("\n") if line.strip()]


def _draw_gradient_bar(draw: ImageDraw.ImageDraw, width: int, y: int, height: int):
    for x in range(width):
        t = x / max(width - 1, 1)
        r = round(ACCENT_CYAN[0] + (ACCENT_PURPLE[0] - ACCENT_CYAN[0]) * t)
        g = round(ACCENT_CYAN[1] + (ACCENT_PURPLE[1] - ACCENT_CYAN[1]) * t)
        b = round(ACCENT_CYAN[2] + (ACCENT_PURPLE[2] - ACCENT_CYAN[2]) * t)
        draw.line([(x, y), (x, y + height)], fill=(r, g, b))


def _render_slide(slide: Dict, index: int, total: int) -> Image.Image:
    img = Image.new("RGB", (CANVAS_SIZE, CANVAS_SIZE), BG_COLOR)
    draw = ImageDraw.Draw(img)
    content_width = CANVAS_SIZE - 2 * MARGIN

    _draw_gradient_bar(draw, CANVAS_SIZE, 0, 14)

    title = str(slide.get("title") or "")
    is_cover = index == 0
    title_size = 74 if is_cover else 58
    title_font = _font(FONT_BOLD, title_size)
    title_lines = _wrap_text(draw, title, title_font, content_width)

    paragraphs = _body_paragraphs(slide.get("content"))
    has_bullets = len(paragraphs) > 1
    bullet_prefix = "•  "

    # Auto-shrink body font if content would overflow the slide.
    for candidate_size in (40, 34, 28, 24):
        body_font = _font(FONT_REGULAR, candidate_size)
        line_gap = int(candidate_size * 0.45)
        para_gap = int(candidate_size * 0.6)
        bullet_indent = draw.textlength(bullet_prefix, font=body_font) if has_bullets else 0
        wrap_width = content_width - bullet_indent
        total_body_height = 0
        wrapped_paragraphs = []
        for para in paragraphs:
            lines = _wrap_text(draw, para, body_font, wrap_width)
            wrapped_paragraphs.append(lines)
            total_body_height += len(lines) * (candidate_size + line_gap) + para_gap

        title_height = len(title_lines) * int(title_size * 1.25)
        available_height = CANVAS_SIZE - 2 * MARGIN - title_height - 100
        if total_body_height <= available_height or candidate_size == 24:
            break

    y = MARGIN + 40
    for line in title_lines:
        draw.text((MARGIN, y), line, font=title_font, fill=TITLE_COLOR)
        y += int(title_size * 1.25)

    y += 50
    text_x = MARGIN + bullet_indent
    for lines in wrapped_paragraphs:
        for i, line in enumerate(lines):
            if has_bullets and i == 0:
                draw.text((MARGIN, y), bullet_prefix, font=body_font, fill=BODY_COLOR)
            draw.text((text_x, y), line, font=body_font, fill=BODY_COLOR)
            y += candidate_size + line_gap
        y += para_gap

    footer_font = _font(FONT_REGULAR, 30)
    counter_text = f"{index + 1} / {total}"
    counter_width = draw.textlength(counter_text, font=footer_font)
    draw.text(
        (CANVAS_SIZE - MARGIN - counter_width, CANVAS_SIZE - MARGIN),
        counter_text,
        font=footer_font,
        fill=LINKEDIN_BLUE,
    )

    if index < total - 1:
        draw.text((MARGIN, CANVAS_SIZE - MARGIN), "Swipe to read \u2192", font=footer_font, fill=HINT_COLOR)

    return img


def render_carousel_pdf(slides: List[Dict]) -> bytes:
    """
    Renders carousel slide JSON (as produced by the AI generator) into a single
    multi-page PDF sized for LinkedIn's document-post carousel format.
    """
    if not slides:
        raise ValueError("No slides to render")

    sorted_slides = sorted(slides, key=lambda s: s.get("slide", 0))
    images = [_render_slide(slide, i, len(sorted_slides)) for i, slide in enumerate(sorted_slides)]

    buffer = io.BytesIO()
    images[0].save(buffer, format="PDF", save_all=True, append_images=images[1:])
    return buffer.getvalue()
