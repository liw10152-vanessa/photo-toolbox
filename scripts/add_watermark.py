#!/usr/bin/env python3
"""
照片一键加水印工具。

支持文字水印，可指定位置、透明度、大小、颜色，支持批量处理。
适用于发布宣传、版权保护、品牌露出等场景。

用法示例：
  python3 add_watermark.py img1.jpg img2.jpg --text "© 我的品牌" --output-dir ./watermarked
  python3 add_watermark.py /path/to/photos --text "样品" --position tile --opacity 60
  python3 add_watermark.py img.jpg --text "机密" --position center --font-size 80
"""

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}

# 各系统常见中文字体路径
FONT_CANDIDATES = [
    # macOS
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    # Windows
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    # Linux
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
]


def load_font(font_size):
    """按候选列表加载第一个可用的中文字体，失败则回退默认字体。"""
    for font_path in FONT_CANDIDATES:
        p = Path(font_path)
        if p.exists():
            try:
                return ImageFont.truetype(str(p), font_size)
            except Exception:
                continue
    print("[警告] 未找到中文字体，使用默认字体（中文可能显示为方块）", file=sys.stderr)
    return ImageFont.load_default()


def collect_images(inputs):
    image_paths = []
    for item in inputs:
        p = Path(item)
        if not p.exists():
            print(f"[警告] 路径不存在，跳过: {p}", file=sys.stderr)
            continue
        if p.is_dir():
            for f in sorted(p.iterdir()):
                if f.is_file() and f.suffix.lower() in IMAGE_EXTS:
                    image_paths.append(f)
        elif p.is_file() and p.suffix.lower() in IMAGE_EXTS:
            image_paths.append(p)
    return image_paths


def get_text_size(draw, text, font):
    """获取文字渲染尺寸（兼容不同 Pillow 版本）。"""
    if hasattr(draw, "textbbox"):
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    return draw.textsize(text, font=font)


def calc_position(position, img_w, img_h, txt_w, txt_h, margin):
    """根据位置关键词计算水印左上角坐标。"""
    positions = {
        "bottom-right": (img_w - txt_w - margin, img_h - txt_h - margin),
        "bottom-left": (margin, img_h - txt_h - margin),
        "top-right": (img_w - txt_w - margin, margin),
        "top-left": (margin, margin),
        "center": ((img_w - txt_w) // 2, (img_h - txt_h) // 2),
    }
    return positions.get(position, positions["bottom-right"])


def add_single_watermark(img_path, text, position="bottom-right", opacity=128,
                         font_size=None, color=(255, 255, 255), margin_ratio=0.03,
                         tile_gap_ratio=0.15, angle=30):
    """
    给单张图片添加文字水印，返回加水印后的 PIL Image（RGBA）。

    Args:
        img_path: 图片路径
        text: 水印文字
        position: 位置 bottom-right/bottom-left/top-right/top-left/center/tile
        opacity: 不透明度 0-255（越小越透明）
        font_size: 字体像素大小，None 则按图片宽度自适应
        color: 文字颜色 RGB 元组
        margin_ratio: 边距占图片短边的比例
        tile_gap_ratio: 平铺时间距占图片宽度的比例
        angle: 平铺水印旋转角度
    """
    img = Image.open(img_path)
    img = ImageOps.exif_transpose(img)
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    img_w, img_h = img.size

    # 字体大小自适应：默认取图片宽度的 5%
    if font_size is None:
        font_size = max(20, int(img_w * 0.05))
    font = load_font(font_size)

    # 透明图层
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    margin = int(min(img_w, img_h) * margin_ratio)
    txt_color = (color[0], color[1], color[2], opacity)

    if position == "tile":
        # 平铺水印
        txt_w, txt_h = get_text_size(draw, text, font)
        gap_x = int(img_w * tile_gap_ratio) + txt_w
        gap_y = int(img_h * tile_gap_ratio * 0.6) + txt_h

        # 创建一个大的平铺图层再旋转
        tile_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        tile_draw = ImageDraw.Draw(tile_layer)
        y = -gap_y
        while y < img_h + gap_y:
            x = -gap_x
            offset = (gap_x // 2) if int(y / gap_y) % 2 else 0
            while x < img_w + gap_x:
                tile_draw.text((x + offset, y), text, font=font, fill=txt_color)
                x += gap_x
            y += gap_y
        tile_layer = tile_layer.rotate(angle, expand=False, resample=Image.BICUBIC)
        overlay = tile_layer
    else:
        txt_w, txt_h = get_text_size(draw, text, font)
        x, y = calc_position(position, img_w, img_h, txt_w, txt_h, margin)
        # 先画深色描边提高在浅色背景上的可读性
        stroke_color = (0, 0, 0, min(opacity, 100))
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            draw.text((x + dx, y + dy), text, font=font, fill=stroke_color)
        draw.text((x, y), text, font=font, fill=txt_color)

    result = Image.alpha_composite(img, overlay)
    return result.convert("RGB")


def main():
    parser = argparse.ArgumentParser(
        description="给照片批量添加文字水印",
    )
    parser.add_argument("inputs", nargs="+", help="图片文件路径或包含图片的文件夹")
    parser.add_argument("-t", "--text", required=True, help="水印文字内容")
    parser.add_argument("-o", "--output-dir", default="./watermarked", help="输出文件夹（默认 ./watermarked）")
    parser.add_argument("--position", default="bottom-right",
                        choices=["bottom-right", "bottom-left", "top-right", "top-left", "center", "tile"],
                        help="水印位置：bottom-right(默认)/bottom-left/top-right/top-left/center/tile(平铺)")
    parser.add_argument("--opacity", type=int, default=128, help="不透明度 0-255，默认 128（半透明）")
    parser.add_argument("--font-size", type=int, default=None, help="字体大小（像素），默认按图片宽度自适应")
    parser.add_argument("--color", default="255,255,255", help="文字颜色 R,G,B，默认白色 255,255,255")
    parser.add_argument("--suffix", default="_wm", help="输出文件名后缀，默认 _wm")
    parser.add_argument("--quality", type=int, default=92, help="JPEG 输出质量 1-100，默认 92")

    args = parser.parse_args()

    image_paths = collect_images(args.inputs)
    if not image_paths:
        print("错误：未找到任何图片文件", file=sys.stderr)
        sys.exit(1)

    # 解析颜色
    try:
        color = tuple(int(c.strip()) for c in args.color.split(","))
        if len(color) != 3:
            raise ValueError
    except ValueError:
        print("错误：--color 格式应为 R,G,B，如 255,0,0", file=sys.stderr)
        sys.exit(1)

    # 透明度范围校验
    opacity = max(0, min(255, args.opacity))

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    success = 0
    failed = 0
    for img_path in image_paths:
        try:
            result = add_single_watermark(
                img_path, args.text,
                position=args.position, opacity=opacity,
                font_size=args.font_size, color=color,
            )
            out_path = output_dir / f"{img_path.stem}{args.suffix}.jpg"
            result.save(str(out_path), "JPEG", quality=args.quality)
            print(f"✅ {img_path.name} → {out_path.name}")
            success += 1
        except Exception as e:
            print(f"❌ {img_path.name} 处理失败: {e}", file=sys.stderr)
            failed += 1

    print(f"\n完成：成功 {success} 张，失败 {failed} 张")
    print(f"输出目录: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
