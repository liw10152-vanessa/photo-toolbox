#!/usr/bin/env python3
"""
照片批量排版生成 Word 文档（.docx）。

将多张照片按网格整齐排列到 Word A4 页面中，每张照片下方预留空白行
用于输入价格、备注等文字。适用于商品报价单、照片说明文档等场景。

用法示例：
  python3 layout_photos_word.py img1.jpg img2.jpg --output out.docx --per-page 6
  python3 layout_photos_word.py /path/to/photos --output out.docx --per-page 6
  python3 layout_photos_word.py img1.jpg img2.jpg --output out.docx --rows 2 --cols 3 --note-lines 3
"""

import argparse
import sys
from pathlib import Path

try:
    from docx import Document
    from docx.shared import Pt, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
except ImportError:
    print("错误：需要安装 python-docx 库。请运行：pip install python-docx", file=sys.stderr)
    sys.exit(1)

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp", ".heic", ".heif"}


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
        ratio = max(rows, cols) / min(rows, cols)
        empty = rows * cols - per_page
        score = ratio * 10 + empty
        if best is None or score < best[0]:
            best = (score, rows, cols)
    return best[1], best[2]


def set_cell_no_border(cell):
    """去除单元格边框，让布局看起来干净。"""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for edge in ('top', 'left', 'bottom', 'right'):
        border = OxmlElement(f'w:{edge}')
        border.set(qn('w:val'), 'nil')
        tcBorders.append(border)
    tcPr.append(tcBorders)


def add_note_lines(cell, note_lines):
    """在单元格中添加指定数量的空白备注行（带下划线，方便手写或打字）。"""
    for i in range(note_lines):
        note_para = cell.add_paragraph()
        note_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pPr = note_para._p.get_or_add_pPr()
        spacing = OxmlElement('w:spacing')
        spacing.set(qn('w:line'), '400')
        spacing.set(qn('w:lineRule'), 'auto')
        pPr.append(spacing)
        # 添加下划线空格，形成可输入的横线
        run = note_para.add_run("　" * 15)
        run.font.size = Pt(10.5)
        run.font.underline = True


def layout_grid_word(image_paths, output_path, per_page=6, rows=None, cols=None,
                     note_lines=2, photo_width_cm=5.5, page_margin_cm=1.5):
    """
    将照片按网格排版到 Word 文档中。

    Args:
        image_paths: 图片路径列表
        output_path: 输出 .docx 文件路径
        per_page: 每页照片数量
        rows/cols: 手动指定网格行列
        note_lines: 每张照片下方预留的备注行数
        photo_width_cm: 照片宽度（厘米）
        page_margin_cm: 页面边距（厘米）
    """
    if rows is None or cols is None:
        rows, cols = auto_grid(per_page)

    total_pages = (len(image_paths) + per_page - 1) // per_page
    doc = Document()

    # 设置页面边距（A4 默认）
    for section in doc.sections:
        section.top_margin = Cm(page_margin_cm)
        section.bottom_margin = Cm(page_margin_cm)
        section.left_margin = Cm(page_margin_cm)
        section.right_margin = Cm(page_margin_cm)

    # 设置默认字体
    style = doc.styles['Normal']
    style.font.name = '宋体'
    style.font.size = Pt(10.5)
    style.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

    for page_idx in range(total_pages):
        start = page_idx * per_page
        end = min(start + per_page, len(image_paths))
        page_images = image_paths[start:end]

        table = doc.add_table(rows=rows, cols=cols)
        table.alignment = 1  # 居中

        img_idx = 0
        for row_idx in range(rows):
            for col_idx in range(cols):
                cell = table.cell(row_idx, col_idx)
                set_cell_no_border(cell)
                cell.text = ""

                if img_idx < len(page_images):
                    img_path = page_images[img_idx]
                    img_idx += 1

                    # 照片
                    para = cell.paragraphs[0]
                    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    run = para.add_run()
                    try:
                        run.add_picture(str(img_path), width=Cm(photo_width_cm))
                    except Exception:
                        # 部分合法 JPEG 带特殊元数据时 python-docx 无法识别图片头，
                        # 用 PIL 重编码为标准 RGB JPEG 后重试一次
                        tmp = None
                        try:
                            from PIL import Image as PILImage
                            import tempfile
                            import os
                            fd, tmp = tempfile.mkstemp(suffix=".jpg")
                            os.close(fd)
                            with PILImage.open(img_path) as im:
                                im.convert("RGB").save(tmp, "JPEG", quality=92)
                            run = para.add_run()
                            run.add_picture(tmp, width=Cm(photo_width_cm))
                        except Exception as e2:
                            para.add_run(f"[图片加载失败: {img_path.name}]")
                            print(f"[警告] 图片加载失败: {img_path} - {e2}", file=sys.stderr)
                        finally:
                            if tmp and os.path.exists(tmp):
                                os.unlink(tmp)

                    # 备注空白行
                    add_note_lines(cell, note_lines)

        if page_idx < total_pages - 1:
            doc.add_page_break()

    doc.save(str(output_path))
    return total_pages, rows, cols


def main():
    parser = argparse.ArgumentParser(
        description="将多张照片按网格排版到 Word 文档中，每张照片下方预留备注空间",
    )
    parser.add_argument("inputs", nargs="+", help="图片文件路径或包含图片的文件夹")
    parser.add_argument("-o", "--output", required=True, help="输出 Word 文件路径 (.docx)")
    parser.add_argument("-n", "--per-page", type=int, default=6, help="每页照片数量（默认 6）")
    parser.add_argument("--rows", type=int, default=None, help="手动指定网格行数")
    parser.add_argument("--cols", type=int, default=None, help="手动指定网格列数")
    parser.add_argument("--note-lines", type=int, default=2, help="每张照片下方预留的备注行数（默认 2）")
    parser.add_argument("--photo-width", type=float, default=5.5, help="照片宽度，单位厘米（默认 5.5）")
    parser.add_argument("--margin", type=float, default=1.5, help="页面边距，单位厘米（默认 1.5）")
    parser.add_argument("--sort", choices=["name", "date", "none"], default="name",
                        help="排序方式：name=按文件名 / date=按修改时间 / none=输入顺序（默认 name）")

    args = parser.parse_args()
    image_paths = collect_images(args.inputs)

    if not image_paths:
        print("错误：未找到任何图片文件", file=sys.stderr)
        sys.exit(1)

    if args.sort == "name":
        image_paths.sort(key=lambda p: p.name.lower())
    elif args.sort == "date":
        image_paths.sort(key=lambda p: p.stat().st_mtime)

    print(f"找到 {len(image_paths)} 张图片")

    rows, cols = args.rows, args.cols
    if rows is None or cols is None:
        rows, cols = auto_grid(args.per_page)
        print(f"自动网格: {rows}行 × {cols}列")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    total_pages, rows, cols = layout_grid_word(
        image_paths, output_path,
        per_page=args.per_page, rows=rows, cols=cols,
        note_lines=args.note_lines, photo_width_cm=args.photo_width,
        page_margin_cm=args.margin,
    )

    file_size = output_path.stat().st_size
    print(f"\n✅ 生成完成: {output_path}")
    print(f"   页数: {total_pages}，网格: {rows}行 × {cols}列")
    print(f"   每张照片下方预留 {args.note_lines} 行备注空间")
    print(f"   文件大小: {file_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
