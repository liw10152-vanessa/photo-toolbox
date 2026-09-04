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
        "center-low": ((img_w - txt_w) // 2, int(img_h * 0.60) - txt_h // 2),
    }
    return positions.get(position, positions["center-low"])


def add_single_watermark(img_path, text, position="center-low", opacity=128,
                         font_size=None, color=(255, 255, 255), margin_ratio=0.03,
                         tile_gap_ratio=0.15, angle=30, max_size=0):
    """
    给单张图片添加文字水印，返回加水印后的 PIL Image（RGBA）。

    Args:
        img_path: 图片路径
        text: 水印文字
        position: 位置 center-low(默认)/center/bottom-right/bottom-left/top-right/top-left/tile
        opacity: 不透明度 0-255（越小越透明）
        font_size: 字体像素大小，None 则按图片宽度自适应
        color: 文字颜色 RGB 元组
        margin_ratio: 边距占图片短边的比例
        tile_gap_ratio: 平铺时间距占图片宽度的比例
        angle: 水印旋转角度（tile 默认 30）
        max_size: 输出长边上限像素，0=不缩放（提速用，超长边图等比缩小）
    """
    img = Image.open(img_path)
    img = ImageOps.exif_transpose(img)
    # 提速：超大图先等比缩放到长边 max_size（0 表示不缩放，保持原分辨率）
    if max_size and max(img.size) > max_size:
        ratio = max_size / float(max(img.size))
        img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)
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
        # 先画深色描边提高在浅色背景上的可读性
        stroke_color = (0, 0, 0, min(opacity, 100))
        if angle != 0:
            # 角标/居中模式支持旋转：先在独立小图层画文字，再旋转后贴到目标位置
            pad = 4
            text_layer = Image.new("RGBA", (txt_w + pad * 2, txt_h + pad * 2), (0, 0, 0, 0))
            tdraw = ImageDraw.Draw(text_layer)
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                tdraw.text((pad + dx, pad + dy), text, font=font, fill=stroke_color)
            tdraw.text((pad, pad), text, font=font, fill=txt_color)
            text_layer = text_layer.rotate(angle, expand=True, resample=Image.BICUBIC)
            w, h = text_layer.size
            x, y = calc_position(position, img_w, img_h, w, h, margin)
            overlay.alpha_composite(text_layer, (x, y))
        else:
            x, y = calc_position(position, img_w, img_h, txt_w, txt_h, margin)
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
    parser.add_argument("--position", default="center-low",
                        choices=["center-low", "center", "bottom-right", "bottom-left", "top-right", "top-left", "tile"],
                        help="水印位置：center-low(默认，正中偏下)/center/bottom-right/bottom-left/top-right/top-left/tile(平铺)")
    parser.add_argument("--opacity", type=int, default=128, help="不透明度 0-255，默认 128（半透明）")
    parser.add_argument("--font-size", type=int, default=None, help="字体大小（像素），默认按图片宽度自适应")
    parser.add_argument("--color", default="255,255,255", help="文字颜色 R,G,B，默认白色 255,255,255")
    parser.add_argument("--angle", type=int, default=None,
                        help="水印旋转角度（度），角标/居中模式可指定；平铺模式不填默认 30")
    parser.add_argument("--max-size", type=int, default=4000,
                        help="输出长边上限像素，默认 4000（超大图等比缩小提速，0=不缩放保持原分辨率）")
    parser.add_argument("--format", dest="fmt", choices=["jpeg", "png"], default="jpeg",
                        help="输出格式：jpeg(默认，质量92)/png(无损更清晰，文件更大)")
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

    # 旋转角度：平铺默认 30 度，角标/居中默认 0 度（可用 --angle 覆盖）
    angle = args.angle if args.angle is not None else (30 if args.position == "tile" else 0)

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
                angle=angle, max_size=args.max_size,
            )
            ext = "png" if args.fmt == "png" else "jpg"
            out_path = output_dir / f"{img_path.stem}{args.suffix}.{ext}"
            if args.fmt == "png":
                result.save(str(out_path), "PNG")
            else:
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
