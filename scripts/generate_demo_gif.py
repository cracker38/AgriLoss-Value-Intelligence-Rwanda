from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "demo" / "agri_loss_dashboard_demo.gif"


def add_text(draw, text, position, size=32, color=(255, 255, 255), bold=False):
    font_path = "C:/Windows/Fonts/arial.ttf"
    font = ImageFont.truetype(font_path, size=size)
    draw.text(position, text, fill=color, font=font)


def make_frame(title: str, subtitle: str, bars: list[int]):
    width, height = 1200, 700
    image = Image.new("RGB", (width, height), color=(16, 24, 32))
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle((40, 30, width - 40, height - 30), radius=24, fill=(25, 41, 58))
    add_text(draw, title, (70, 60), size=46)
    add_text(draw, subtitle, (70, 115), size=20, color=(163, 180, 198))

    card_positions = [
        (70, 170, 280, 250),
        (330, 170, 540, 250),
        (590, 170, 800, 250),
        (850, 170, 1060, 250),
    ]
    card_values = ["42k", "18k", "8.4", "74%"]
    labels = ["Rows", "Crop records", "Avg loss", "Coverage"]
    for idx, box in enumerate(card_positions):
        x1, y1, x2, y2 = box
        draw.rounded_rectangle((x1, y1, x2, y2), radius=18, fill=(37, 52, 71))
        add_text(draw, labels[idx], (x1 + 18, y1 + 20), size=18, color=(163, 180, 198))
        add_text(draw, card_values[idx], (x1 + 18, y1 + 70), size=32)

    chart_x = 70
    chart_y = 300
    chart_w = 1060
    chart_h = 300
    draw.rounded_rectangle((chart_x, chart_y, chart_x + chart_w, chart_y + chart_h), radius=16, fill=(17, 31, 41))

    max_value = max(bars) if bars else 1
    bar_gap = 18
    bar_width = (chart_w - 80 - bar_gap * (len(bars) - 1)) // len(bars)
    start_x = chart_x + 50
    for index, value in enumerate(bars):
        bar_h = int((value / max_value) * 200)
        x = start_x + index * (bar_width + bar_gap)
        y = chart_y + 220 - bar_h
        draw.rounded_rectangle((x, y, x + bar_width, chart_y + 220), radius=10, fill=(38, 166, 154))
        add_text(draw, str(index + 1), (x + bar_width // 2 - 6, chart_y + 232), size=12, color=(255, 255, 255))

    add_text(draw, "Top crops", (chart_x + 20, chart_y + 14), size=20, color=(255, 255, 255))
    return image


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    frames = [
        make_frame("AgriLoss Rwanda", "Seasonal agricultural survey dashboard", [60, 80, 55, 10, 90, 75]),
        make_frame("AgriLoss Rwanda", "Crop and loss monitoring", [45, 110, 70, 25, 95, 80]),
        make_frame("AgriLoss Rwanda", "Public-safe descriptive analytics", [70, 95, 65, 18, 88, 72]),
    ]
    frames[0].save(
        OUTPUT,
        save_all=True,
        append_images=frames[1:],
        loop=0,
        duration=800,
    )
    print(f"Created demo GIF at {OUTPUT}")


if __name__ == "__main__":
    main()
