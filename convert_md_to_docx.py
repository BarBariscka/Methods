"""
Конвертер Markdown → DOCX для всех файлов из presentations/slides/*.md
"""
import os
import re
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

SLIDES_DIR = os.path.join(os.path.dirname(__file__), "presentations", "slides")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "presentations", "output")

# Цвета
TITLE_COLOR = RGBColor(0x1A, 0x56, 0xFF)      # Синий заголовок
HEADING_COLOR = RGBColor(0x2E, 0x2E, 0x2E)     # Тёмный для h2-h6
BODY_COLOR = RGBColor(0x33, 0x33, 0x33)        # Основной текст
CODE_COLOR = RGBColor(0x24, 0x29, 0x2E)        # Текст кода
HIGHLIGHT_COLOR = RGBColor(0xFF, 0x6B, 0x00)    # Акцент
TABLE_HEADER_BG = RGBColor(0x44, 0x72, 0xC4)    # Синий фон заголовка таблицы
TABLE_ROW_BG = RGBColor(0xF2, 0xF2, 0xF2)       # Светлый фон строк


def parse_markdown(md_content):
    """Парсит markdown на блоки: заголовки, текст, код, списки, таблицы."""
    blocks = []
    lines = md_content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]

        # Заголовок
        if line.startswith('# '):
            blocks.append(("heading", 1, line[2:].strip()))
            i += 1
        elif line.startswith('## '):
            blocks.append(("heading", 2, line[3:].strip()))
            i += 1
        elif line.startswith('### '):
            blocks.append(("heading", 3, line[4:].strip()))
            i += 1
        elif line.startswith('#### '):
            blocks.append(("heading", 4, line[5:].strip()))
            i += 1

        # Блок кода
        elif line.startswith('```'):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                code_lines.append(lines[i])
                i += 1
            blocks.append(("code", 0, '\n'.join(code_lines)))
            i += 1

        # Таблица
        elif line.startswith('|'):
            table_lines = [line]
            i += 1
            while i < len(lines) and lines[i].startswith('|'):
                table_lines.append(lines[i])
                i += 1
            blocks.append(("table", 0, '\n'.join(table_lines)))

        # Цитата
        elif line.startswith('> '):
            blocks.append(("quote", 0, line[2:].strip()))
            i += 1

        # Маркированный список
        elif re.match(r'^[-*]\s+', line):
            items = []
            while i < len(lines) and re.match(r'^[-*]\s+', lines[i]):
                items.append(re.sub(r'^[-*]\s+', '', lines[i]).strip())
                i += 1
            blocks.append(("bullet_list", 0, items))

        # Нумерованный список
        elif re.match(r'^\d+\.\s+', line):
            items = []
            while i < len(lines) and re.match(r'^\d+\.\s+', lines[i]):
                items.append(re.sub(r'^\d+\.\s+', '', lines[i]).strip())
                i += 1
            blocks.append(("numbered_list", 0, items))

        # Горизонтальная линия
        elif line.strip() == '---':
            blocks.append(("hr", 0, ""))
            i += 1

        # Пустая строка
        elif line.strip() == '':
            blocks.append(("blank", 0, ""))
            i += 1

        # Обычный текст (возможно с **bold**)
        else:
            text = line.strip()
            if text:
                blocks.append(("text", 0, text))
            i += 1

    return blocks


def add_block_to_doc(doc, block):
    """Добавляет блок в документ."""
    btype, level, content = block

    if btype == "heading":
        h = doc.add_heading(content, level=level)
        for run in h.runs:
            run.font.color.rgb = TITLE_COLOR if level == 1 else HEADING_COLOR
        doc.add_paragraph()  # отступ

    elif btype == "code":
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(6)
        run = p.add_run(content)
        run.font.name = "Consolas"
        run.font.size = Pt(10)
        run.font.color.rgb = CODE_COLOR
        # Фон через shading
        pPr = p._element.get_or_add_pPr()
        shd = pPr.makeelement(qn('w:shd'), {
            qn('w:fill'): "F0F0F0",
            qn('w:val'): "clear"
        })
        pPr.append(shd)

    elif btype == "table":
        rows = content.strip().split('\n')
        if len(rows) < 2:
            return
        # Парсим строки таблицы
        table_data = []
        for row in rows:
            cells = [c.strip() for c in row.split('|')[1:-1]]
            table_data.append(cells)

        # Убираем строку с разделителями
        if len(table_data) > 1 and all(c.startswith('-') for c in table_data[1]):
            table_data = [table_data[0]] + table_data[2:]

        if table_data:
            num_rows = len(table_data)
            num_cols = max(len(r) for r in table_data)
            table = doc.add_table(rows=num_rows, cols=num_cols)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER

            for r_idx, row_data in enumerate(table_data):
                for c_idx, cell_text in enumerate(row_data):
                    cell = table.cell(r_idx, c_idx)
                    cell.text = cell_text
                    for paragraph in cell.paragraphs:
                        for run in paragraph.runs:
                            run.font.size = Pt(10)
                            run.font.name = "Times New Roman"
                            if r_idx == 0:
                                run.font.bold = True
                                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                                # Фон заголовка
                                tc = cell._element
                                tcPr = tc.get_or_add_tcPr()
                                shd = tcPr.makeelement(qn('w:shd'), {
                                    qn('w:fill'): "4472C4",
                                    qn('w:val'): "clear"
                                })
                                tcPr.append(shd)
                            else:
                                run.font.color.rgb = BODY_COLOR
                                # Чередование фона
                                if r_idx % 2 == 0:
                                    tc = cell._element
                                    tcPr = tc.get_or_add_tcPr()
                                    shd = tcPr.makeelement(qn('w:shd'), {
                                        qn('w:fill'): "F2F2F2",
                                        qn('w:val'): "clear"
                                    })
                                    tcPr.append(shd)

            doc.add_paragraph()

    elif btype == "quote":
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(1)
        run = p.add_run(f"> {content}")
        run.font.italic = True
        run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
        run.font.size = Pt(11)

    elif btype == "bullet_list":
        for item in content:
            p = doc.add_paragraph(item, style='List Bullet')
            p.paragraph_format.space_after = Pt(2)
            for run in p.runs:
                run.font.size = Pt(11)

    elif btype == "numbered_list":
        for item in content:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.space_after = Pt(2)
            for run in p.runs:
                run.font.size = Pt(11)

    elif btype == "hr":
        p = doc.add_paragraph()
        pPr = p._element.get_or_add_pPr()
        pBdr = pPr.makeelement(qn('w:pBdr'), {})
        bottom = pBdr.makeelement(qn('w:bottom'), {
            qn('w:val'): "single",
            qn('w:sz'): "6",
            qn('w:space'): "1",
            qn('w:color'): "AAAAAA"
        })
        pBdr.append(bottom)
        pPr.append(pBdr)

    elif btype == "blank":
        pass  # пропускаем

    elif btype == "text":
        # Обработка **bold**
        parts = re.split(r'\*\*(.+?)\*\*', content)
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                run = p.add_run(part[2:-2])
                run.font.bold = True
                run.font.color.rgb = HIGHLIGHT_COLOR
                run.font.size = Pt(11)
            else:
                run = p.add_run(part)
                run.font.size = Pt(11)
                run.font.color.rgb = BODY_COLOR
                run.font.name = "Times New Roman"


def process_file(filepath, output_dir):
    """Конвертирует один markdown-файл в DOCX."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    doc = Document()

    # Настройки страницы
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(2)
    section.right_margin = Cm(2)
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)

    # Шрифт по умолчанию
    style = doc.styles['Normal']
    font = style.font
    font.name = "Times New Roman"
    font.size = Pt(12)

    blocks = parse_markdown(content)

    for block in blocks:
        add_block_to_doc(doc, block)

    basename = os.path.basename(filepath).replace('.md', '')
    output_path = os.path.join(output_dir, f"{basename}.docx")
    doc.save(output_path)
    print(f"  ✓ Создан: {output_path}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    md_files = sorted([
        f for f in os.listdir(SLIDES_DIR)
        if f.endswith('.md')
    ])

    print(f"Найдено {len(md_files)} файлов...\n")

    for md_file in md_files:
        filepath = os.path.join(SLIDES_DIR, md_file)
        process_file(filepath, OUTPUT_DIR)

    print(f"\nГотово! Все DOCX файлы в: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
