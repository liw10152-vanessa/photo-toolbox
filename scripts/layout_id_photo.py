#!/usr/bin/env python3
"""
证件照排版工具：把人像照片裁切成证件照规格，并按相纸尺寸自动排版成可打印图。

用法示例：
  python3 layout_id_photo.py portrait.jpg --output id_sheet.png          # 默认一寸+5寸相纸
  python3 layout_id_photo.py portrait.jpg --spec 2寸 --paper 6寸 --output id.png
  python3 layout_id_photo.py portrait.jpg --spec 35x49 --paper 89x127 --output id.png
  python3 layout_id_photo.py portrait.jpg --single-dir ./single          # 同时输出单张证件照

尺寸标准（多来源核对，打印用 300dpi）：
  一寸 25x35mm、二寸 35x49mm、大一寸 33x48mm、护照 48x33mm
  5寸相纸 89x127mm、6寸相纸 102x152mm、A4 210x297mm
"""

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageOps

# 常用证件照规格（mm）
SPECS = {
    "1寸": (25, 35),
    "一寸": (25, 35),
    "2寸": (35, 49),
    "二寸": (35, 49),
    "大一寸": (33, 48),
    "小一寸": (22, 32),
    "护照": (33, 48),
}
# 常用相纸（mm）
PAPERS = {
    "5寸": (89, 127),
    "6寸": (102, 152),
    "A4": (210, 297),
}


def parse_dim(s, default_map, label):
    """解析 规格/相纸 参数：支持 '1寸'/'2寸' 等关键词，或 '宽x高mm' 自定义。"""
    s = str(s).strip().lower().replace(" ", "")
    # 关键词（忽略大小写）
    for key, val in default_map.items():
        if s == key.lower():
            return val
    # 自定义 宽x高（单位 mm）
    if "x" in s or "×" in s:
        parts = s.replace("×", "x").split("x")
        if len(parts) == 2:
            try:
                return (float(parts[0]), float(parts[1]))
            except ValueError:
                pass
    raise ValueError(f"无法识别的{label}: {s}（支持关键词或 '宽x高mm'，如 25x35）")


def crop_to_ratio(img, ratio_w, ratio_h, head_offset=0.12):
    """
    按目标宽高比裁切人像，默认头部靠上（证件照习惯）。
    head_offset: 0~1，0=裁切框顶部对齐原图顶部，0.5=居中，1=底部；默认 0.12 留少量顶部余量。
    """
    w, h = img.size
    target = ratio_w / ratio_h
    cur = w / h
    if cur > target:
        # 原图更宽：高度为限制，裁左右（水平居中），垂直无移动空间
        new_h = h
        new_w = int(round(h * target))
        x = (w - new_w) // 2
        y = 0
    else:
        # 原图更竖：宽度为限制，裁上下（垂直可移动），head_offset 控制头部位置
        new_w = w
        new_h = int(round(w / target))
        x = 0
        max_dy = h - new_h
        y = int(max_dy * max(0.0, min(1.0, head_offset)))
    return img.crop((x, y, x + new_w, y + new_h))


def build_sheet(portrait_path, spec=(25, 35), paper=(89, 127), dpi=300,
                head_offset=0.12, gap_mm=2.0, margin_mm=5.0,
                output=None, single_dir=None, bg=(255, 255, 255)):
    """
    生成证件照排版图。

    Returns:
        (sheet_image, rows, cols, count, spec_size, single_paths)
    """
    spec_w, spec_h = spec
    paper_w, paper_h = paper

    # 1. 读图 + EXIF 转正
    img = Image.open(portrait_path)
    img = ImageOps.exif_transpose(img)
    if img.mode != "RGB":
        img = img.convert("RGB")

    # 2. 裁切到证件照比例
    cropped = crop_to_ratio(img, spec_w, spec_h, head_offset=head_offset)

    # 3. 缩放到证件照实际打印尺寸（mm → px @dpi）
    px_per_mm = dpi / 25.4
    target_w = max(1, int(round(spec_w * px_per_mm)))
    target_h = max(1, int(round(spec_h * px_per_mm)))
    single = cropped.resize((target_w, target_h), Image.LANCZOS)

    # 4. 计算相纸排版行列数（间距/留白取整到像素，避免浮点坐标）
    gap = int(round(gap_mm * px_per_mm))
    margin = int(round(margin_mm * px_per_mm))
    sheet_w = int(round(paper_w * px_per_mm))
    sheet_h = int(round(paper_h * px_per_mm))
    cols = max(1, int((sheet_w - 2 * margin + gap) // (target_w + gap)))
    rows = max(1, int((sheet_h - 2 * margin + gap) // (target_h + gap)))
    count = rows * cols

    # 5. 画排版图（白底居中）
    sheet = Image.new("RGB", (sheet_w, sheet_h), bg)
    used_w = cols * target_w + (cols - 1) * gap
    used_h = rows * target_h + (rows - 1) * gap
    start_x = int(round((sheet_w - used_w) / 2))
    start_y = int(round((sheet_h - used_h) / 2))
    for r in range(rows):
        for c in range(cols):
            x = start_x + c * (target_w + gap)
            y = start_y + r * (target_h + gap)
            sheet.paste(single, (x, y))

    # 6. 输出
    single_paths = []
    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        sheet.save(output, "PNG", dpi=(dpi, dpi))
    if single_dir:
        Path(single_dir).mkdir(parents=True, exist_ok=True)
        sp = Path(single_dir) / f"{Path(portrait_path).stem}_single.png"
        single.save(str(sp), "PNG", dpi=(dpi, dpi))
        single_paths.append(sp)

    return sheet, rows, cols, count, (target_w, target_h), single_paths


def main():
    parser = argparse.ArgumentParser(description="证件照排版：裁切人像到证件照规格并按相纸排版")
    parser.add_argument("input", help="人像照片路径")
    parser.add_argument("-s", "--spec", default="1寸",
                        help="证件照规格：1寸(默认)/2寸/大一寸/小一寸/护照 或 '宽x高mm'（如 35x49）")
    parser.add_argument("-p", "--paper", default="5寸",
                        help="相纸尺寸：5寸(默认)/6寸/A4 或 '宽x高mm'（如 89x127）")
    parser.add_argument("--dpi", type=int, default=300, help="输出分辨率（打印默认 300）")
    parser.add_argument("--head-offset", type=float, default=0.12,
                        help="头部位置 0~1：0=裁切框顶部对齐原图顶部，0.12=头部靠上(默认)，0.5=居中")
    parser.add_argument("--gap", type=float, default=2.0, help="排版时间距（mm，默认 2）")
    parser.add_argument("--margin", type=float, default=5.0, help="相纸留白边距（mm，默认 5）")
    parser.add_argument("--bg", default="255,255,255", help="背景色 R,G,B（默认白）")
    parser.add_argument("-o", "--output", default=None, help="输出排版图路径（默认自动命名）")
    parser.add_argument("--single-dir", default=None, help="同时输出单张证件照到该文件夹（可选）")
    args = parser.parse_args()

    try:
        spec = parse_dim(args.spec, SPECS, "证件照规格")
        paper = parse_dim(args.paper, PAPERS, "相纸尺寸")
    except ValueError as e:
        print(f"错误：{e}", file=sys.stderr)
        sys.exit(1)

    try:
        bg = tuple(int(c.strip()) for c in args.bg.split(","))
        if len(bg) != 3:
            raise ValueError
    except ValueError:
        print("错误：--bg 格式应为 R,G,B", file=sys.stderr)
        sys.exit(1)

    output = args.output or f"id_photo_{args.spec.replace('x', 'X')}_{args.paper.replace('x', 'X')}.png"
    sheet, rows, cols, count, sz, singles = build_sheet(
        args.input, spec=spec, paper=paper, dpi=args.dpi,
        head_offset=args.head_offset, gap_mm=args.gap, margin_mm=args.margin,
        output=output, single_dir=args.single_dir, bg=bg,
    )

    print(f"✅ 证件照规格 {spec[0]:g}x{spec[1]:g}mm（单张 {sz[0]}x{sz[1]}px @{args.dpi}dpi）")
    print(f"✅ 相纸 {paper[0]:g}x{paper[1]:g}mm → 排版 {cols}x{rows} = {count} 张")
    print(f"✅ 排版图: {Path(output).resolve()}")
    for sp in singles:
        print(f"✅ 单张: {sp.resolve()}")


if __name__ == "__main__":
    main()
