"""
AgriNova — Simulated ESP32-CAM (OV3660) frame renderer.

No physical camera is wired up yet, so this procedurally renders a plausible
field-view frame (unique per farm, reacting to pan/tilt) that stands in for
the real camera feed. The Robot/Camera endpoints are shaped exactly like a
real ESP32-CAM integration (GET a frame, POST a pan/tilt move, POST a
capture) so swapping in real hardware later requires no frontend changes.
"""

import base64
import io
import math
import random
from datetime import datetime, timezone

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 480, 320


def _farm_palette(farm_id: int) -> dict:
    rng = random.Random(farm_id * 104729)
    hue_shift = rng.uniform(-15, 15)
    return {
        "sky_top": (int(120 + hue_shift), 190, 235),
        "sky_bottom": (200, 225, 210),
        "field_light": (int(90 + hue_shift), 165, 70),
        "field_dark": (int(60 + hue_shift), 120, 45),
        "row_count": rng.randint(9, 14),
    }


def render_frame(farm_id: int, pan_deg: int, tilt_deg: int) -> str:
    palette = _farm_palette(farm_id)
    img = Image.new("RGB", (WIDTH, HEIGHT), palette["sky_top"])
    draw = ImageDraw.Draw(img)

    horizon = HEIGHT * 0.42 - (tilt_deg * 1.2)
    horizon = max(40, min(HEIGHT - 60, horizon))

    for y in range(0, int(horizon)):
        t = y / max(horizon, 1)
        color = tuple(
            int(palette["sky_top"][i] * (1 - t) + palette["sky_bottom"][i] * t) for i in range(3)
        )
        draw.line([(0, y), (WIDTH, y)], fill=color)

    draw.rectangle([0, horizon, WIDTH, HEIGHT], fill=palette["field_light"])

    pan_offset = (pan_deg / 90.0) * 60
    row_count = palette["row_count"]
    row_spacing = WIDTH / row_count
    for i in range(-2, row_count + 2):
        x = i * row_spacing + pan_offset
        draw.polygon(
            [
                (x, HEIGHT),
                (x + row_spacing * 0.35, HEIGHT),
                (x + row_spacing * 0.15 + (WIDTH / 2 - x) * 0.15, horizon),
                (x + row_spacing * 0.05 + (WIDTH / 2 - x) * 0.15, horizon),
            ],
            fill=palette["field_dark"],
        )

    sun_x = WIDTH * 0.8 - pan_offset * 0.5
    sun_y = horizon * 0.35
    draw.ellipse([sun_x - 18, sun_y - 18, sun_x + 18, sun_y + 18], fill=(255, 236, 160))

    now_label = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
    label = f"AgriNova CAM  |  Farm #{farm_id}  |  Pan {pan_deg}°  Tilt {tilt_deg}°  |  {now_label}"
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    draw.rectangle([0, HEIGHT - 22, WIDTH, HEIGHT], fill=(0, 0, 0))
    draw.text((6, HEIGHT - 18), label, fill=(210, 255, 210), font=font)

    rec_pulse = int(abs(math.sin(datetime.now().timestamp() * 2)) * 255)
    draw.ellipse([WIDTH - 22, 8, WIDTH - 10, 20], fill=(rec_pulse, 30, 30))

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=78)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"
