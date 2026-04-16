# Charts & Visualization — Matplotlib

Tạo chart images để embed vào PDF, DOCX, PPTX.

## Setup — Style Consistent

```python
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

# Color palette — match document color system
COLORS = {
    'primary': '#2B579A',
    'primary_dark': '#1B3A65',
    'accent': '#2E75B6',
    'success': '#28A745',
    'danger': '#DC3545',
    'text': '#333333',
    'text_light': '#666666',
    'border': '#D9D9D9',
    'bg_light': '#F2F7FB',
}

# Multi-series palette (up to 6 series)
SERIES_COLORS = ['#2B579A', '#2E75B6', '#28A745', '#F39C12', '#DC3545', '#8E44AD']

# Font setup — Be Vietnam Pro if available, else Arial
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Be Vietnam Pro', 'Arial', 'DejaVu Sans'],
    'font.size': 11,
    'axes.titlesize': 14,
    'axes.labelsize': 12,
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'axes.edgecolor': COLORS['border'],
    'axes.grid': True,
    'grid.alpha': 0.3,
    'grid.color': COLORS['border'],
})
```

## Bar Chart

```python
def create_bar_chart(categories, values, title, ylabel, output_path,
                     color=None, figsize=(8, 5), horizontal=False):
    """Bar chart — vertical or horizontal."""
    fig, ax = plt.subplots(figsize=figsize)
    color = color or COLORS['primary']

    if horizontal:
        bars = ax.barh(categories, values, color=color, height=0.6)
        ax.set_xlabel(ylabel)
        ax.invert_yaxis()
    else:
        bars = ax.bar(categories, values, color=color, width=0.6)
        ax.set_ylabel(ylabel)

    ax.set_title(title, fontweight='bold', color=COLORS['primary_dark'], pad=15)

    # Value labels
    for bar in bars:
        if horizontal:
            ax.text(bar.get_width() + max(values)*0.01, bar.get_y() + bar.get_height()/2,
                    f'{bar.get_width():,.0f}', va='center', fontsize=9, color=COLORS['text'])
        else:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.01,
                    f'{bar.get_height():,.0f}', ha='center', fontsize=9, color=COLORS['text'])

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    return output_path
```

## Grouped Bar Chart

```python
def create_grouped_bar(categories, series_dict, title, ylabel, output_path,
                       figsize=(10, 6)):
    """Grouped bar chart — multiple series side by side."""
    import numpy as np
    fig, ax = plt.subplots(figsize=figsize)

    x = np.arange(len(categories))
    n = len(series_dict)
    width = 0.8 / n

    for i, (label, values) in enumerate(series_dict.items()):
        offset = (i - n/2 + 0.5) * width
        bars = ax.bar(x + offset, values, width, label=label,
                      color=SERIES_COLORS[i % len(SERIES_COLORS)])

    ax.set_ylabel(ylabel)
    ax.set_title(title, fontweight='bold', color=COLORS['primary_dark'], pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.legend()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    return output_path
```

## Line Chart

```python
def create_line_chart(x_data, series_dict, title, xlabel, ylabel, output_path,
                      figsize=(10, 6)):
    """Line chart — trend over time."""
    fig, ax = plt.subplots(figsize=figsize)

    for i, (label, values) in enumerate(series_dict.items()):
        ax.plot(x_data, values, marker='o', linewidth=2, markersize=6,
                label=label, color=SERIES_COLORS[i % len(SERIES_COLORS)])

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontweight='bold', color=COLORS['primary_dark'], pad=15)
    ax.legend()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    return output_path
```

## Pie Chart

```python
def create_pie_chart(labels, values, title, output_path, figsize=(8, 8)):
    """Pie chart — proportions."""
    fig, ax = plt.subplots(figsize=figsize)
    colors = SERIES_COLORS[:len(labels)]

    wedges, texts, autotexts = ax.pie(
        values, labels=labels, autopct='%1.1f%%',
        colors=colors, startangle=90,
        textprops={'fontsize': 11}
    )
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')

    ax.set_title(title, fontweight='bold', color=COLORS['primary_dark'], pad=20)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    return output_path
```

## Embed Chart vào Documents

### PDF (fpdf2)
```python
pdf.add_page()
pdf.add_heading('Biểu Đồ Doanh Thu', level=2)
pdf.image('/tmp/chart.png', x=15, w=180)  # x=15mm, width=180mm
```

### DOCX (python-docx)
```python
from docx.shared import Inches
doc.add_heading('Biểu Đồ Doanh Thu', level=2)
doc.add_picture('/tmp/chart.png', width=Inches(6.0))
# Center the image
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
```

### PPTX (python-pptx)
```python
from pptx.util import Inches
slide.shapes.add_picture('/tmp/chart.png',
    Inches(1.5), Inches(2.0), width=Inches(10))
```

## Tips

1. **Luôn dùng `dpi=150`** cho charts embed — đủ rõ, file không quá lớn
2. **`bbox_inches='tight'`** để trim whitespace
3. **Close figure** sau khi save: `plt.close()` — tránh memory leak
4. **Temp files**: save chart vào `/tmp/chart_xxx.png`, xóa sau khi embed
5. **Vietnamese labels**: matplotlib render OK nếu font Be Vietnam Pro đã cài
