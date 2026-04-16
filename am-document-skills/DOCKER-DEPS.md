# Docker Dependencies — am-document-skills

Tất cả dependencies cần cài sẵn trong Docker image cho Another Me agents.

## System Packages (apt)

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    pandoc \
    poppler-utils \
    qpdf \
    fontconfig \
    libreoffice-calc \
    && rm -rf /var/lib/apt/lists/*
```

## Python Packages (pip)

```dockerfile
RUN pip install --no-cache-dir \
    python-docx \
    openpyxl \
    fpdf2 \
    python-pptx \
    reportlab \
    pdfplumber \
    pypdf \
    pandas \
    matplotlib
```

## Fonts — BẮT BUỘC

### Be Vietnam Pro (Tiếng Việt)

```dockerfile
RUN mkdir -p /usr/share/fonts/truetype/be-vietnam-pro && \
    for variant in Regular Bold Italic BoldItalic Medium SemiBold Light; do \
      curl -sL -o "/usr/share/fonts/truetype/be-vietnam-pro/BeVietnamPro-${variant}.ttf" \
        "https://raw.githubusercontent.com/google/fonts/main/ofl/bevietnampro/BeVietnamPro-${variant}.ttf"; \
    done && \
    fc-cache -f
```

### Inter (English)

Inter dùng variable font trên Google Fonts → cần convert sang static.
Cách đơn giản nhất: COPY pre-built static fonts vào image.

**Option A: Copy pre-built (recommended)**
```dockerfile
COPY fonts/inter/ /usr/share/fonts/truetype/inter/
RUN fc-cache -f
```

Cần chuẩn bị folder `fonts/inter/` chứa:
- Inter-Regular.ttf
- Inter-Bold.ttf
- Inter-Italic.ttf
- Inter-BoldItalic.ttf
- Inter-Medium.ttf
- Inter-SemiBold.ttf
- Inter-Light.ttf

**Option B: Build-time convert (slower, cần fonttools)**
```dockerfile
RUN pip install --no-cache-dir fonttools brotli && \
    mkdir -p /usr/share/fonts/truetype/inter && \
    curl -sL -o /tmp/Inter-Variable.ttf \
      "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf" && \
    curl -sL -o /tmp/Inter-Italic-Variable.ttf \
      "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter-Italic%5Bopsz%2Cwght%5D.ttf" && \
    python3 -c "
from fontTools.ttLib import TTFont
from fontTools.varLib.mutator import instantiateVariableFont
WEIGHTS = {'Light':300,'Regular':400,'Medium':500,'SemiBold':600,'Bold':700}
for name, wght in WEIGHTS.items():
    for src, suf in [('/tmp/Inter-Variable.ttf',''), ('/tmp/Inter-Italic-Variable.ttf','Italic')]:
        font = TTFont(src)
        inst = instantiateVariableFont(font, {'wght':wght,'opsz':14})
        out = name+suf if name!='Regular' or suf else name
        if name=='Regular' and suf: out = suf
        inst.save(f'/usr/share/fonts/truetype/inter/Inter-{out}.ttf')
" && \
    fc-cache -f && \
    rm -f /tmp/Inter-*.ttf

```

## Font Verification

Sau khi build image, verify:
```bash
# Phải trả về kết quả
fc-list | grep "Be Vietnam"
fc-list | grep "Inter"
```

## Summary — Copy-paste Dockerfile Block

```dockerfile
# === Document Skills Dependencies ===

# System
RUN apt-get update && apt-get install -y --no-install-recommends \
    pandoc poppler-utils qpdf fontconfig curl libreoffice-calc \
    && rm -rf /var/lib/apt/lists/*

# Python
RUN pip install --no-cache-dir \
    python-docx openpyxl fpdf2 python-pptx \
    reportlab pdfplumber pypdf pandas matplotlib

# Fonts — Be Vietnam Pro (Vietnamese)
RUN mkdir -p /usr/share/fonts/truetype/be-vietnam-pro && \
    for v in Regular Bold Italic BoldItalic Medium SemiBold Light; do \
      curl -sL -o "/usr/share/fonts/truetype/be-vietnam-pro/BeVietnamPro-${v}.ttf" \
        "https://raw.githubusercontent.com/google/fonts/main/ofl/bevietnampro/BeVietnamPro-${v}.ttf"; \
    done

# Fonts — Inter (English) — COPY pre-built static fonts
COPY fonts/inter/ /usr/share/fonts/truetype/inter/

# Rebuild font cache
RUN fc-cache -f
```
