#!/usr/bin/env python3
"""
照片批量排版生成 PDF。

将多张照片按网格整齐排列到 PDF 页面中，支持自定义每页张数、
页面尺寸、边距、间距、输出质量等。照片保持原始比例，居中放置。

用法示例：
  python3 layout_photos.py img1.jpg img2.jpg ... --output out.pdf --per-page 9
  python3 layout_photos.py /path/to/photos/folder --output out.pdf --per-page 6
  python3 layout_photos.py img1.jpg img2.jpg --output out.pdf --rows 2 --cols 3 --dpi 150
"""

import argparse
import io
import os
import sys
from pathlib import Path

from PIL import Image, ImageOps
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

# 支持的图片扩展名
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp", ".heic", ".heif"}

# 预设页面尺寸 (宽, 高) 单位 pt
PAGE_SIZES = {
    "a4": A4,
    "letter": letter,
    "a3": (842, 1191),
    "a5": (420, 595),
    "4r": (4 * 72, 6 * 72),  # 4x6 英寸照片纸
}


def parse_page_size(size_str):
    """解析页面尺寸参数，返回 (width_pt, height_pt)。"""
    s = size_str.lower().strip()
    if s in PAGE_SIZES:
        return PAGE_SIZES[s]
    # 支持 宽x高 格式，单位 mm 或 pt，如 "210x297mm" 或 "595x842pt"
    import re
    m = re.match(r"^([\d.]+)\s*[x×]\s*([\d.]+)\s*(mm|pt)?$", s)
    if m:
        w = float(m.group(1))
        h = float(m.group(2))
        unit = m.group(3) or "pt"
        if unit == "mm":
            w = w * mm
            h = h * mm
        return (w, h)
    raise ValueError(f"无法识别页面尺寸: {size_str}，使用 a4/letter/a3/a5 或 宽x高mm")


def collect_images(inputs):
    """从输入路径列表中收集图片文件。输入可以是文件或文件夹。"""
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
        else:
            print(f"[警告] 不支持的文件类型，跳过: {p}", file=sys.stderr)
    return image_paths


def auto_grid(per_page):
    """根据每页张数自动计算最接近正方形的网格 (rows, cols)。"""
    if per_page <= 0:
        raise ValueError("每页张数必须大于 0")
    best = None
    for cols in range(1, per_page + 1):
        rows = (per_page + cols - 1) // cols
        if rows * cols < per_page:
            continue
        # 评价：行列比越接近 1 越好，同时尽量用满格子
        ratio = max(rows, cols) / min(rows, cols)
        empty = rows * cols - per_page
        score = ratio * 10 + empty
        if best is None or score < best[0]:
            best = (score, rows, cols)
    return best[1], best[2]


def load_image(path, target_w_px, target_h_px, fit="contain", quality=85):
    """
    加载图片，处理 EXIF 方向，缩放到目标像素尺寸，返回 JPEG 字节。

    fit:
      - contain: 保持比例，完整显示，可能留白
      - cover: 保持比例，裁剪填满格子
    """
    try:
        img = Image.open(path)
        # 处理 EXIF 旋转
        img = ImageOps.exif_transpose(img)
        # 转 RGB（去掉 alpha 通道，JPEG 不支持）
        if img.mode in ("RGBA", "P", "LA"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        src_w, src_h = img.size

        if fit == "cover":
            # 裁剪填满：缩放后裁剪中心
            scale = max(target_w_px / src_w, target_h_px / src_h)
            new_w = int(src_w * scale)
            new_h = int(src_h * scale)
            img = img.resize((new_w, new_h), Image.LANCZOS)
            left = (new_w - target_w_px) // 2
            top = (new_h - target_h_px) // 2
            img = img.crop((left, top, left + target_w_px, top + target_h_px))
        else:
            # contain：保持比例，完整显示
            scale = min(target_w_px / src_w, target_h_px / src_h)
            new_w = max(1, int(src_w * scale))
            new_h = max(1, int(src_h * scale))
            img = img.resize((new_w, new_h), Image.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        return buf.getvalue()
    except Exception as e:
        print(f"[错误] 处理图片失败 {path}: {e}", file=sys.stderr)
        return None


def layout_pdf(image_paths, output_path, per_page=9, rows=None, cols=None,
               page_size=A4, margin=16, gap=3, dpi=200, fit="contain",
               jpeg_quality=85, background=(255, 255, 255)):
    """
    主排版函数。将图片按网格排列生成 PDF。

    参数:
      image_paths: 图片路径列表
      output_path: 输出 PDF 路径
      per_page: 每页张数
      rows, cols: 手动指定行列（为 None 则自动计算）
      page_size: (宽, 高) pt
      margin: 页边距 pt
      gap: 图片间距 pt
      dpi: 输出 DPI（控制图片嵌入分辨率，影响文件大小）
      fit: contain 或 cover
      jpeg_quality: JPEG 压缩质量 1-100
      background: 背景色 RGB
    """
    if not image_paths:
        raise ValueError("没有找到任何图片")

    # 确定网格
    if rows and cols:
        grid_rows, grid_cols = rows, cols
        per_page = rows * cols
    else:
        grid_rows, grid_cols = auto_grid(per_page)

    page_w, page_h = page_size

    # 计算每个格子的尺寸（pt）
    content_w = page_w - 2 * margin
    content_h = page_h - 2 * margin
    cell_w = (content_w - gap * (grid_cols - 1)) / grid_cols
    cell_h = (content_h - gap * (grid_rows - 1)) / grid_rows

    if cell_w <= 0 or cell_h <= 0:
        raise ValueError("边距或间距过大，没有空间放置图片，请减小 margin 或 gap")

    # 格子对应的像素尺寸（按目标 DPI）
    cell_w_px = int(cell_w / 72 * dpi)
    cell_h_px = int(cell_h / 72 * dpi)

    c = canvas.Canvas(str(output_path), pagesize=page_size)
    c.setTitle("Photo Layout")

    total = len(image_paths)
    total_pages = (total + per_page - 1) // per_page

    for page_idx in range(total_pages):
        # 背景
        c.setFillColorRGB(background[0] / 255, background[1] / 255, background[2] / 255)
        c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

        start = page_idx * per_page
        end = min(start + per_page, total)
        page_images = image_paths[start:end]

        for i, img_path in enumerate(page_images):
            row = i // grid_cols
            col = i % grid_cols

            # 格子左下角坐标（reportlab 原点在左下角）
            cell_x = margin + col * (cell_w + gap)
            cell_y = page_h - margin - (row + 1) * cell_h - row * gap

            # 加载并缩放图片
            img_data = load_image(img_path, cell_w_px, cell_h_px, fit=fit, quality=jpeg_quality)
            if img_data is None:
                continue

            # 用 ImageReader 包装，获取实际尺寸
            img_reader = ImageReader(io.BytesIO(img_data))
            actual_w_px, actual_h_px = img_reader.getSize()

            # 像素转 pt
            actual_w_pt = actual_w_px / dpi * 72
            actual_h_pt = actual_h_px / dpi * 72

            # 在格子内居中
            draw_x = cell_x + (cell_w - actual_w_pt) / 2
            draw_y = cell_y + (cell_h - actual_h_pt) / 2

            # 嵌入图片
            c.drawImage(img_reader, draw_x, draw_y, width=actual_w_pt, height=actual_h_pt,
                        preserveAspectRatio=True, mask='auto')

        c.showPage()

    c.save()
    return total_pages, grid_rows, grid_cols


def main():
    parser = argparse.ArgumentParser(
        description="照片批量排版生成 PDF：将多张照片按网格整齐排列到 PDF 页面中。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s photo1.jpg photo2.jpg photo3.jpg --output out.pdf --per-page 9
  %(prog)s /path/to/photos --output out.pdf --per-page 6 --dpi 150
  %(prog)s img1.jpg img2.jpg --output out.pdf --rows 2 --cols 2 --page-size a4
  %(prog)s /path/to/photos --output out.pdf --per-page 4 --fit cover --gap 8
        """,
    )
    parser.add_argument("inputs", nargs="+", help="图片文件或包含图片的文件夹路径（可多个）")
    parser.add_argument("-o", "--output", required=True, help="输出 PDF 文件路径")
    parser.add_argument("-n", "--per-page", type=int, default=9, help="每页放置的照片数量（默认 9）")
    parser.add_argument("--rows", type=int, default=None, help="手动指定网格行数（需同时指定 --cols）")
    parser.add_argument("--cols", type=int, default=None, help="手动指定网格列数（需同时指定 --rows）")
    parser.add_argument("--page-size", default="a4", help="页面尺寸：a4/letter/a3/a5/4r 或 宽x高mm（默认 a4）")
    parser.add_argument("--margin", type=float, default=16, help="页边距，单位 pt（默认 16，约 0.22 英寸）")
    parser.add_argument("--gap", type=float, default=3, help="照片之间的间距，单位 pt（默认 3）")
    parser.add_argument("--dpi", type=int, default=200, help="图片嵌入分辨率 DPI（默认 200，越大越清晰但文件越大；屏幕查看 150 足够，打印用 300）")
    parser.add_argument("--fit", choices=["contain", "cover"], default="contain",
                        help="图片适配方式：contain=保持比例完整显示（可能留白），cover=裁剪填满格子（默认 contain）")
    parser.add_argument("--quality", type=int, default=85, help="JPEG 压缩质量 1-100（默认 85）")
    parser.add_argument("--sort", choices=["name", "date", "none"], default="name",
                        help="图片排序方式：name=按文件名，date=按修改时间，none=保持输入顺序（默认 name）")

    args = parser.parse_args()

    # 校验 rows/cols
    if (args.rows is None) != (args.cols is None):
        parser.error("--rows 和 --cols 必须同时指定")

    # 解析页面尺寸
    try:
        page_size = parse_page_size(args.page_size)
    except ValueError as e:
        parser.error(str(e))

    # 收集图片
    image_paths = collect_images(args.inputs)

    if not image_paths:
        print("[错误] 没有找到任何支持的图片文件", file=sys.stderr)
        sys.exit(1)

    # 排序
    if args.sort == "name":
        image_paths.sort(key=lambda p: p.name.lower())
    elif args.sort == "date":
        image_paths.sort(key=lambda p: p.stat().st_mtime)

    print(f"找到 {len(image_paths)} 张图片")

    # 确保输出目录存在
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 生成 PDF
    try:
        total_pages, grid_rows, grid_cols = layout_pdf(
            image_paths=image_paths,
            output_path=output_path,
            per_page=args.per_page,
            rows=args.rows,
            cols=args.cols,
            page_size=page_size,
            margin=args.margin,
            gap=args.gap,
            dpi=args.dpi,
            fit=args.fit,
            jpeg_quality=args.quality,
        )
    except Exception as e:
        print(f"[错误] 生成 PDF 失败: {e}", file=sys.stderr)
        sys.exit(1)

    file_size = output_path.stat().st_size
    size_mb = file_size / 1024 / 1024
    print(f"✅ 生成完成: {output_path}")
    print(f"   页数: {total_pages}，网格: {grid_rows}行 × {grid_cols}列")
    print(f"   文件大小: {size_mb:.2f} MB ({file_size} bytes)")


if __name__ == "__main__":
    main()
