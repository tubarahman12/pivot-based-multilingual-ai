#!/usr/bin/env python3
"""
80-page dissertation PDF generator for:
"Development and Analysis of Multimodal AI Tools for Indian Context"
Tuba Rahman, Aligarh Muslim University
"""

import io, os, math, textwrap
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    HRFlowable, KeepTogether, Image
)
from reportlab.platypus.flowables import Flowable
from reportlab.graphics.shapes import Drawing, Rect, Line, String, Circle, Polygon
from reportlab.graphics.charts.barcharts import VerticalBarChart, HorizontalBarChart
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics import renderPDF
from reportlab.graphics.widgets.markers import makeMarker
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

OUT = "/mnt/user-data/outputs/Tuba_Rahman_Dissertation.pdf"

W, H = A4  # 595.27 x 841.89 pt

# ── Colours ────────────────────────────────────────────────────────────────────
AMU_GREEN   = colors.HexColor("#1a5c2a")
AMU_GOLD    = colors.HexColor("#b8860b")
ACCENT_BLUE = colors.HexColor("#1a3a6b")
LIGHT_GREY  = colors.HexColor("#f5f5f5")
MID_GREY    = colors.HexColor("#cccccc")
DARK_GREY   = colors.HexColor("#444444")
TABLE_HEAD  = colors.HexColor("#1a5c2a")
TABLE_ALT   = colors.HexColor("#eaf3eb")

# ── Styles ─────────────────────────────────────────────────────────────────────
SS = getSampleStyleSheet()

def make_style(name, parent="Normal", **kw):
    return ParagraphStyle(name, parent=SS[parent], **kw)

styles = {
    "title_main":  make_style("title_main",  "Title",
                              fontSize=22, textColor=AMU_GREEN,
                              alignment=TA_CENTER, spaceAfter=6,
                              fontName="Helvetica-Bold"),
    "title_sub":   make_style("title_sub",   "Normal",
                              fontSize=14, textColor=ACCENT_BLUE,
                              alignment=TA_CENTER, spaceAfter=4,
                              fontName="Helvetica-Bold"),
    "title_info":  make_style("title_info",  "Normal",
                              fontSize=11, alignment=TA_CENTER,
                              spaceAfter=3, textColor=DARK_GREY),
    "ch_heading":  make_style("ch_heading",  "Heading1",
                              fontSize=16, textColor=AMU_GREEN,
                              fontName="Helvetica-Bold",
                              spaceBefore=18, spaceAfter=8,
                              borderPad=4),
    "sec_heading": make_style("sec_heading", "Heading2",
                              fontSize=13, textColor=ACCENT_BLUE,
                              fontName="Helvetica-Bold",
                              spaceBefore=12, spaceAfter=6),
    "sub_heading": make_style("sub_heading", "Heading3",
                              fontSize=11, textColor=AMU_GREEN,
                              fontName="Helvetica-BoldOblique",
                              spaceBefore=8, spaceAfter=4),
    "body":        make_style("body",        "Normal",
                              fontSize=10.5, leading=16,
                              alignment=TA_JUSTIFY, spaceAfter=6,
                              textColor=colors.black),
    "body_ind":    make_style("body_ind",    "Normal",
                              fontSize=10.5, leading=16,
                              alignment=TA_JUSTIFY, spaceAfter=6,
                              leftIndent=18, textColor=colors.black),
    "caption":     make_style("caption",     "Normal",
                              fontSize=9, alignment=TA_CENTER,
                              textColor=DARK_GREY, spaceAfter=10,
                              fontName="Helvetica-Oblique"),
    "code":        make_style("code",        "Code",
                              fontSize=8.5, fontName="Courier",
                              backColor=LIGHT_GREY, leading=12,
                              leftIndent=12, rightIndent=12,
                              spaceBefore=4, spaceAfter=4),
    "toc":         make_style("toc",         "Normal",
                              fontSize=10.5, leading=16,
                              spaceAfter=3),
    "toc_ch":      make_style("toc_ch",      "Normal",
                              fontSize=11, leading=16,
                              fontName="Helvetica-Bold",
                              spaceAfter=3, textColor=AMU_GREEN),
    "bullet":      make_style("bullet",      "Normal",
                              fontSize=10.5, leading=15,
                              leftIndent=24, firstLineIndent=-12,
                              spaceAfter=3, bulletIndent=12),
    "ref":         make_style("ref",         "Normal",
                              fontSize=9.5, leading=14,
                              spaceAfter=5, alignment=TA_JUSTIFY,
                              leftIndent=24, firstLineIndent=-24),
    "abstract":    make_style("abstract",    "Normal",
                              fontSize=10.5, leading=16,
                              alignment=TA_JUSTIFY, spaceAfter=6,
                              leftIndent=30, rightIndent=30),
    "equation":    make_style("equation",    "Normal",
                              fontSize=10.5, leading=16,
                              fontName="Helvetica-Oblique",
                              alignment=TA_CENTER, spaceAfter=6,
                              leftIndent=40, rightIndent=40),
}

# ── Page template with header/footer ──────────────────────────────────────────
def on_page(canvas, doc):
    p = canvas.getPageNumber()
    if p <= 1:
        return
    canvas.saveState()
    canvas.setStrokeColor(AMU_GREEN)
    canvas.setLineWidth(0.8)
    canvas.line(2*cm, H - 1.8*cm, W - 2*cm, H - 1.8*cm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(AMU_GREEN)
    canvas.drawString(2*cm, H - 1.5*cm,
                      "Development and Analysis of Multimodal AI Tools for Indian Context")
    canvas.drawRightString(W - 2*cm, H - 1.5*cm, "AMU · 2024")
    canvas.line(2*cm, 1.5*cm, W - 2*cm, 1.5*cm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(DARK_GREY)
    canvas.drawCentredString(W/2, 1.1*cm, f"— {p} —")
    canvas.restoreState()

# ── Helpers ────────────────────────────────────────────────────────────────────
def P(text, style="body"):
    return Paragraph(text, styles[style])

def H1(text):
    return P(f"<b>{text}</b>", "ch_heading")

def H2(text):
    return P(text, "sec_heading")

def H3(text):
    return P(text, "sub_heading")

def SP(n=6):
    return Spacer(1, n)

def HR():
    return HRFlowable(width="100%", thickness=0.5,
                      color=MID_GREY, spaceAfter=6)

def bullet(text):
    return P(f"• &nbsp; {text}", "bullet")

def eq(text):
    return P(text, "equation")

# ── Table builder ──────────────────────────────────────────────────────────────
def make_table(data, col_widths=None, header_rows=1):
    t = Table(data, colWidths=col_widths, repeatRows=header_rows)
    cmd = [
        ('BACKGROUND', (0,0), (-1, header_rows-1), TABLE_HEAD),
        ('TEXTCOLOR',  (0,0), (-1, header_rows-1), colors.white),
        ('FONTNAME',   (0,0), (-1, header_rows-1), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,        -1),      9),
        ('ALIGN',      (0,0), (-1,        -1),      'CENTER'),
        ('VALIGN',     (0,0), (-1,        -1),      'MIDDLE'),
        ('GRID',       (0,0), (-1,        -1),      0.4, MID_GREY),
        ('ROWBACKGROUNDS', (0, header_rows), (-1, -1), [colors.white, TABLE_ALT]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING',(0,0),(-1,-1), 4),
        ('LEFTPADDING', (0,0),(-1,-1), 5),
        ('RIGHTPADDING',(0,0),(-1,-1), 5),
        ('WORDWRAP',   (0,0), (-1,-1), True),
    ]
    t.setStyle(TableStyle(cmd))
    return t

# ── Matplotlib figure → ReportLab Image ───────────────────────────────────────
def fig_to_image(fig, width=12*cm):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    img = Image(buf, width=width)
    img.hAlign = 'CENTER'
    return img

# ══════════════════════════════════════════════════════════════════════════════
# FIGURE GENERATORS
# ══════════════════════════════════════════════════════════════════════════════

def fig_language_bar():
    fig, ax = plt.subplots(figsize=(10, 5))
    models   = ['Krutrim\nLLM','IndicLLM\nSuite','Indic\nGenBench',
                 'MuRIL','MILU','IndicVoices\n-R','BHASAAN\nUVAAD',
                 'GPT-4','mBERT','Bhasha-\nAbhijnaanam']
    high_res = [22, 22, 11, 10, 8, 22, 10, 6, 4, 22]
    x = np.arange(len(models))
    bars = ax.barh(x, high_res, color='#1a5c2a',
                   edgecolor='white',)
    for bar, val in zip(bars, high_res):
        ax.text(bar.get_width()+0.2, bar.get_y()+bar.get_height()/2,
                str(val), va='center', fontsize=9, fontweight='bold')
    ax.set_yticks(x)
    ax.set_yticklabels(models, fontsize=9)
    ax.set_xlabel('Number of High-Resource Languages Supported', fontsize=10)
    ax.set_title('Comparison of High-Resource Language Coverage (Table 3.1)',
                 fontsize=11, fontweight='bold', pad=10)
    ax.set_xlim(0, 26)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='x', alpha=0.3)
    fig.tight_layout()
    return fig_to_image(fig, 14*cm)

def fig_text_classification():
    fig, ax = plt.subplots(figsize=(10, 5.5))
    models = ['GPT-4o','IndicBERT\n(finetuned)','MuRIL','Krutrim\nLLM',
              'mBERT','Open Multilingual\nModels','Lang-Specific\nFine-tuned']
    hindi   = [78, 90, 85, 88, 65, 65, 55]
    bengali = [76, 90, 82, 85, 62, 63, 54]
    tamil   = [72, 87, 75, 83, 55, 60, 52]
    telugu  = [71, 87, 74, 82, 53, 59, 51]
    x = np.arange(len(models))
    colors_list = ['#1a5c2a','#2e8b57','#52b788','#95d5b2']
    ax.plot(x, hindi,   'o-', color=colors_list[0], linewidth=2, markersize=6, label='Hindi')
    ax.plot(x, bengali, 's-', color=colors_list[1], linewidth=2, markersize=6, label='Bengali')
    ax.plot(x, tamil,   '^-', color=colors_list[2], linewidth=2, markersize=6, label='Tamil')
    ax.plot(x, telugu,  'D-', color=colors_list[3], linewidth=2, markersize=6, label='Telugu')
    ax.set_xticks(x)
    ax.set_xticklabels(models, fontsize=8.5)
    ax.set_ylabel('Accuracy / Performance (%)', fontsize=10)
    ax.set_title('Model-wise Performance Comparison Across Indian Languages (Table 3.2)',
                 fontsize=10, fontweight='bold')
    ax.set_ylim(40, 100)
    ax.legend(loc='lower right', fontsize=9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.3)
    fig.tight_layout()
    return fig_to_image(fig, 14*cm)

def fig_asr_wer():
    fig, ax = plt.subplots(figsize=(10, 5.5))
    langs   = ['Marathi\n(IA)', 'Odia\n(IA)', 'Gujarati\n(IA)',
               'Tamil\n(D)', 'Telugu\n(D)', 'Malayalam\n(D)']
    models_data = {
        'W2V2-BERT':         [13.5, 15.5, 12.5, 20.0, 21.0, 22.0],
        'XLSR-53':           [14.5, 16.5, 13.5, 21.0, 22.0, 23.0],
        'Wav2Vec2.0-base':   [18.0, 20.0, 17.0, 26.0, 27.0, 28.0],
        'Whisper small':     [19.0, 21.0, 18.0, 27.0, 28.0, 29.0],
        'INDICSEAMLESS':     [11.5, 13.5, 10.5, 17.0, 18.0, 19.0],
    }
    markers = ['o','s','^','v','D']
    c_list  = ['#1a3a6b','#e07b00','#9b2226','#2e8b57','#008080']
    x = np.arange(len(langs))
    for (name, vals), mk, cl in zip(models_data.items(), markers, c_list):
        ax.plot(x, vals, marker=mk, linestyle='-', linewidth=2, markersize=7,
                label=name, color=cl)
    ax.set_xticks(x)
    ax.set_xticklabels(langs, fontsize=9)
    ax.set_ylabel('WER % (Lower is Better)', fontsize=10)
    ax.set_title('WER% Comparison of ASR Models Across Indian Languages (Table 3.3)',
                 fontsize=10, fontweight='bold')
    ax.legend(loc='upper left', fontsize=8.5, framealpha=0.8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig_to_image(fig, 14*cm)

def fig_pipeline_arch():
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis('off')

    boxes = [
        (0.3, 2.5, 1.6, 2.4, "INPUT\nACQUISITION\n(Text/Speech)",  '#1a3a6b'),
        (2.3, 2.5, 1.6, 2.4, "NORMALIZATION\nNL(IL)\nModality Unification", '#1a5c2a'),
        (4.3, 2.5, 1.6, 2.4, "TRANSLATION\nL-to-P\n(IndicTrans2)",    '#b8860b'),
        (6.3, 2.5, 1.6, 2.4, "PIVOT\nREASONING GP\n(LLM/English)", '#9b2226'),
        (8.3, 2.5, 1.6, 2.4, "TRANSLATION\nP-to-L\n(IndicTrans2)",    '#b8860b'),
        (10.1,2.5, 1.6, 2.4, "RENDERING\nRL\n(Text/TTS)",          '#1a3a6b'),
    ]

    for (x, y, w, h, text, color) in boxes:
        rect = mpatches.FancyBboxPatch((x, y), w, h,
                                        boxstyle="round,pad=0.1",
                                        facecolor=color, edgecolor='white',
                                        linewidth=1.5, alpha=0.9)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, text, ha='center', va='center',
                fontsize=7.5, color='white', fontweight='bold',
                multialignment='center')

    for xi in [1.9, 3.9, 5.9, 7.9, 9.9]:
        ax.annotate('', xy=(xi+0.4, 3.7), xytext=(xi, 3.7),
                    arrowprops=dict(arrowstyle='->', color='#555555', lw=1.5))

    extra = [
        (2.3, 0.4, 1.6, 1.2, "ASR Module\n(Whisper)", '#2e8b57'),
        (8.3, 0.4, 1.6, 1.2, "TTS Module\n(gTTS/FastPitch)", '#2e8b57'),
        (4.3, 5.2, 3.6, 0.9, "Semantic Consistency Check -- LSC (Eq. 2)", '#444444'),
    ]
    for (x, y, w, h, text, color) in extra:
        rect = mpatches.FancyBboxPatch((x, y), w, h,
                                        boxstyle="round,pad=0.1",
                                        facecolor=color, edgecolor='white',
                                        linewidth=1, alpha=0.75)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, text, ha='center', va='center',
                fontsize=7.5, color='white', fontweight='bold',
                multialignment='center')

    ax.annotate('', xy=(3.1, 2.5), xytext=(3.1, 1.6),
                arrowprops=dict(arrowstyle='->', color='#2e8b57', lw=1.2))
    ax.annotate('', xy=(9.1, 2.5), xytext=(9.1, 1.6),
                arrowprops=dict(arrowstyle='->', color='#2e8b57', lw=1.2))

    ax.set_title("Figure 1: Architecture of the Multimodal Pivot-Based Reasoning Pipeline\n"
                 "OL = RL(DP-to-L(GP(TL-to-P(NL(IL)), C)))",
                 fontsize=10, fontweight='bold', pad=10)
    fig.tight_layout()
    return fig_to_image(fig, 15*cm)

def fig_error_propagation():
    fig, ax = plt.subplots(figsize=(8, 4))
    stages   = ['e_asr\n(Speech Recog.)', 'e_trans\n(L-to-P Trans.)',
                 'e_gen\n(LLM Reasoning)', 'e_tts\n(TTS Synthesis)']
    errors   = [0.08, 0.13, 0.05, 0.00]
    bar_cols = ['#1a3a6b','#b8860b','#9b2226','#2e8b57']
    bars = ax.bar(stages, errors, color=bar_cols, edgecolor='white', linewidth=1.2, width=0.5)
    for bar, v in zip(bars, errors):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.003,
                f'{v:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    ax.axhline(sum(errors), color='red', linestyle='--', linewidth=1.5,
               label=f'e_total <= {sum(errors):.3f}')
    ax.set_ylabel('Error Bound', fontsize=10)
    ax.set_title('Error Propagation Analysis -- Equation 3\ne_total <= e_asr + e_trans + e_gen + e_tts',
                 fontsize=10, fontweight='bold')
    ax.legend(fontsize=9)
    ax.set_ylim(0, 0.35)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.3)
    fig.tight_layout()
    return fig_to_image(fig, 12*cm)

def fig_complexity():
    fig, ax = plt.subplots(figsize=(8, 4))
    n = np.arange(1, 23)
    ax.plot(n, n**2, 'r-o', markersize=4, linewidth=2, label='Pairwise: O(n^2)')
    ax.plot(n,    n, 'g-s', markersize=4, linewidth=2, label='Pivot-Based: O(n)')
    ax.fill_between(n, n, n**2, alpha=0.1, color='red', label='Complexity saving')
    ax.set_xlabel('Number of Supported Languages', fontsize=10)
    ax.set_ylabel('Translation Paths Required', fontsize=10)
    ax.set_title('Scalability Comparison: Pairwise vs Pivot-Based Architecture',
                 fontsize=10, fontweight='bold')
    ax.legend(fontsize=9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig_to_image(fig, 12*cm)

def fig_resource_gap():
    fig, ax = plt.subplots(figsize=(10, 4.5))
    langs     = ['Hindi','Bengali','Tamil','Telugu','Marathi','Urdu',
                 'Gujarati','Kannada','Kashmiri','Manipuri','Santali','Bodo']
    data_mb   = [8500, 4200, 3100, 2800, 2400, 2100,
                 1900, 1750,  120,   90,   60,   40]
    bar_cols  = ['#1a5c2a']*8 + ['#9b2226']*4
    bars = ax.bar(langs, data_mb, color=bar_cols, edgecolor='white')
    ax.set_ylabel('Approximate Training Data (MB)', fontsize=10)
    ax.set_title('Data Resource Gap Across Indian Languages',
                 fontsize=10, fontweight='bold')
    ax.set_xticklabels(langs, rotation=30, ha='right', fontsize=9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.3)
    high_patch = mpatches.Patch(color='#1a5c2a', label='High-resource')
    low_patch  = mpatches.Patch(color='#9b2226', label='Low-resource')
    ax.legend(handles=[high_patch, low_patch], fontsize=9)
    fig.tight_layout()
    return fig_to_image(fig, 14*cm)

def fig_streamlit_ui():
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 6)
    ax.axis('off')
    ax.add_patch(mpatches.FancyBboxPatch((0.2,0.2), 10.6, 5.6,
                 boxstyle="round,pad=0.1", facecolor='#f8fafc', edgecolor='#cccccc'))
    ax.add_patch(mpatches.FancyBboxPatch((0.3,5.0), 10.4, 0.7,
                 boxstyle="round,pad=0.05", facecolor='#1a3a6b', edgecolor='none'))
    ax.text(5.5, 5.35, 'Pivot-Based Multilingual AI · ICECI-2026',
            ha='center', va='center', color='white', fontsize=10, fontweight='bold')
    ax.add_patch(mpatches.FancyBboxPatch((0.3,0.3), 2.0, 4.6,
                 boxstyle="round,pad=0.05", facecolor='#e8f0fe', edgecolor='#cccccc'))
    ax.text(1.3, 4.7, 'Settings', ha='center', fontsize=9, fontweight='bold', color='#1a3a6b')
    for i, (label, val) in enumerate([('Source Lang', 'Auto-detect'),
                                       ('Target Lang', 'Hindi'),
                                       ('Model', 'LLaMA-3.3-70B')]):
        y = 4.3 - i*0.7
        ax.text(0.45, y, label, fontsize=7.5, color='#555555')
        ax.add_patch(mpatches.FancyBboxPatch((0.4, y-0.3), 1.7, 0.28,
                     boxstyle="round,pad=0.02", facecolor='white', edgecolor='#aaaaaa'))
        ax.text(1.3, y-0.16, val, ha='center', fontsize=7.5, color='#333333')
    ax.text(1.3, 1.85, 'Pipeline Equation', ha='center', fontsize=7.5, fontweight='bold', color='#1a3a6b')
    ax.text(1.3, 1.55, 'OL=RL(DP-L(GP(TL-P(NL(IL)),C)))',
            ha='center', fontsize=6, color='#444444', fontfamily='monospace')
    ax.add_patch(mpatches.FancyBboxPatch((2.5,4.3), 1.5, 0.5,
                 boxstyle="round,pad=0.05", facecolor='#1a5c2a', edgecolor='none'))
    ax.text(3.25, 4.55, 'Pipeline', ha='center', fontsize=8.5, color='white', fontweight='bold')
    ax.add_patch(mpatches.FancyBboxPatch((4.2,4.3), 1.4, 0.5,
                 boxstyle="round,pad=0.05", facecolor='#dddddd', edgecolor='none'))
    ax.text(4.9, 4.55, 'History', ha='center', fontsize=8.5, color='#555555')
    ax.add_patch(mpatches.FancyBboxPatch((2.5,3.2), 8.1, 0.9,
                 boxstyle="round,pad=0.05", facecolor='white', edgecolor='#aaaaaa'))
    ax.text(2.7, 3.9, 'Enter text in any Indian language or English:', fontsize=8, color='#777777')
    ax.text(2.7, 3.55, 'Namaste, aaj mausam kaisa hai?', fontsize=9, color='#333333')
    ax.add_patch(mpatches.FancyBboxPatch((2.5,2.7), 8.1, 0.38,
                 boxstyle="round,pad=0.05", facecolor='#1a3a6b', edgecolor='none'))
    ax.text(6.55, 2.89, 'Run Full Pipeline (All 8 Stages)', ha='center',
            fontsize=9, color='white', fontweight='bold')
    stage_colors = ['#6366f1','#8b5cf6','#a855f7','#ec4899','#f97316','#22c55e']
    stage_labels = ['Stage 1\nInput','Stage 2\nNormalize','Stage 3\nL-to-P','Stage 4\nReason','Stage 5\nP-to-L','Stage 6\nRender']
    for i, (sc, sl) in enumerate(zip(stage_colors, stage_labels)):
        x = 2.5 + i*1.35
        ax.add_patch(mpatches.FancyBboxPatch((x, 0.4), 1.2, 2.1,
                     boxstyle="round,pad=0.05", facecolor=sc+'33', edgecolor=sc, linewidth=0.8))
        ax.text(x+0.6, 2.25, sl, ha='center', va='top', fontsize=7, color=sc,
                fontweight='bold', multialignment='center')
    ax.set_title('Figure 5: Streamlit Prototype User Interface Layout',
                 fontsize=10, fontweight='bold', y=0.02)
    fig.tight_layout()
    return fig_to_image(fig, 15*cm)

def fig_semantic_consistency():
    fig, ax = plt.subplots(figsize=(9, 4))
    langs = ['Hindi\n->EN->Hindi', 'Tamil\n->EN->Tamil', 'Bengali\n->EN->Bengali',
             'Urdu\n->EN->Urdu', 'Telugu\n->EN->Telugu', 'Malayalam\n->EN->Malayalam']
    lsc   = [0.92, 0.87, 0.91, 0.89, 0.85, 0.83]
    bar_cols = ['#2e8b57' if v > 0.88 else '#f59e0b' if v > 0.80 else '#e53e3e' for v in lsc]
    bars = ax.bar(langs, lsc, color=bar_cols, edgecolor='white', width=0.55)
    for bar, v in zip(bars, lsc):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.005,
                f'{v:.2f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    ax.axhline(0.80, color='orange', linestyle='--', linewidth=1.2, label='Threshold: 0.80')
    ax.axhline(0.88, color='green', linestyle=':', linewidth=1.2, label='High consistency: 0.88')
    ax.set_ylim(0.70, 1.0)
    ax.set_ylabel('LSC Score', fontsize=10)
    ax.set_title('Semantic Consistency (LSC) Across Language Pairs -- Eq. 2',
                 fontsize=10, fontweight='bold')
    ax.legend(fontsize=8.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.3)
    fig.tight_layout()
    return fig_to_image(fig, 13*cm)

# ══════════════════════════════════════════════════════════════════════════════
# CONTENT BUILDERS
# ══════════════════════════════════════════════════════════════════════════════

def cover_page(story):
    story.append(SP(40))
    story.append(P('<b>ALIGARH MUSLIM UNIVERSITY</b>', 'title_sub'))
    story.append(P('Department of Computer Science', 'title_info'))
    story.append(SP(20))
    story.append(HRFlowable(width="60%", thickness=2, color=AMU_GREEN,
                             hAlign='CENTER', spaceAfter=20))
    story.append(P('<b>Development and Analysis of Multimodal AI Tools<br/>for Indian Context</b>',
                   'title_main'))
    story.append(HRFlowable(width="60%", thickness=2, color=AMU_GREEN,
                             hAlign='CENTER', spaceBefore=20, spaceAfter=30))
    story.append(P('Bachelor of Science (Hons. with Research)<br/>(Computer Applications)<br/>VII<super>th</super> Semester',
                   'title_info'))
    story.append(SP(30))
    story.append(P('Submitted by', 'title_info'))
    story.append(P('<b>TUBA RAHMAN</b>', 'title_sub'))
    story.append(P('Roll No: 22CABSA125', 'title_info'))
    story.append(SP(30))
    story.append(P('Under the Supervision of', 'title_info'))
    story.append(P('<b>Dr. Mohammad Nadeem</b>', 'title_sub'))
    story.append(P('Department of Computer Science<br/>Aligarh Muslim University, Aligarh (India)', 'title_info'))
    story.append(SP(30))
    story.append(HRFlowable(width="80%", thickness=0.5, color=MID_GREY,
                             hAlign='CENTER', spaceAfter=10))
    story.append(P('2024', 'title_info'))
    story.append(PageBreak())

def certification_page(story):
    story.append(H1('Certification'))
    story.append(HR())
    story.append(SP(20))
    story.append(P("""This is to certify that the research work entitled <b>"Development and Analysis
    of Multimodal AI Tools for Indian Context"</b> submitted by <b>Tuba Rahman</b> (Roll No:
    22CABSA125) in partial fulfilment of the requirements for the degree of Bachelor of Science
    (Hons. with Research) in Computer Applications at the Department of Computer Science,
    Aligarh Muslim University, Aligarh, is a record of bonafide research work carried out
    by her under my supervision."""))
    story.append(SP(12))
    story.append(P("""To the best of my knowledge and belief, the work is original, has not been
    submitted for any other degree or diploma, and all sources of information have been duly
    acknowledged."""))
    story.append(SP(50))
    data = [['', ''],
            ['________________________', '________________________'],
            ['Signature of Student', 'Signature of Supervisor'],
            ['Tuba Rahman', 'Dr. Mohammad Nadeem'],
            ['Roll No: 22CABSA125', 'Department of Computer Science'],
            ['Date: ______________', 'Aligarh Muslim University']]
    t = Table(data, colWidths=[8*cm, 8*cm])
    t.setStyle(TableStyle([
        ('ALIGN',  (0,0), (-1,-1), 'CENTER'),
        ('FONTSIZE',(0,0),(-1,-1), 10),
        ('TOPPADDING',(0,0),(-1,-1),4),
    ]))
    story.append(t)
    story.append(PageBreak())

def acknowledgement_page(story):
    story.append(H1('Acknowledgement'))
    story.append(HR())
    story.append(SP(8))
    story.append(P("""I express my sincere gratitude to my supervisor, <b>Dr. Mohammad Nadeem</b>,
    Department of Computer Science, Aligarh Muslim University, for providing invaluable
    guidance, constructive feedback, and continuous support throughout this research project.
    His expertise and encouragement have been instrumental in shaping this work."""))
    story.append(SP(6))
    story.append(P("""I would also like to extend my heartfelt thanks to the Department of Computer
    Science, Aligarh Muslim University, for providing a stimulating academic environment and
    access to essential resources that significantly supported this study."""))
    story.append(SP(6))
    story.append(P("""I extend my sincere appreciation to the research communities and institutions,
    particularly <b>AI4Bharat</b>, <b>IIT Madras</b>, <b>Google Research</b>, and others, whose publicly
    available datasets, tools, and published works contributed substantially to this analysis.
    The open-source contributors and developers whose tireless efforts made many models and
    resources publicly accessible deserve special recognition."""))
    story.append(SP(6))
    story.append(P("""I am grateful to the broader NLP research community for publishing their findings,
    which formed the empirical backbone of this comparative study. The thirty research papers
    reviewed in this dissertation represent the collective effort of hundreds of researchers
    working towards equitable AI for India's diverse linguistic landscape."""))
    story.append(SP(6))
    story.append(P("""Finally, I am deeply grateful to my family and peers for their constant
    encouragement, moral support, and motivation during the completion of this report.
    Their belief in this work has been a source of strength throughout."""))
    story.append(SP(40))
    story.append(P('<b>Tuba Rahman</b><br/>Roll No: 22CABSA125<br/>Department of Computer Science<br/>Aligarh Muslim University, Aligarh', 'body'))
    story.append(PageBreak())

def abstract_page(story):
    story.append(H1('Abstract'))
    story.append(HR())
    story.append(SP(8))
    story.append(P("""India's extraordinary linguistic diversity — encompassing 22 official languages and
    more than 1,369 documented dialects — presents unique and formidable challenges for building
    fair, scalable, and effective artificial intelligence and natural language processing systems.
    Although recent advances in large language models (LLMs) have dramatically accelerated
    global progress in machine translation, speech recognition, and text understanding, Indian
    languages remain significantly underrepresented in mainstream AI development, accounting
    for less than 1% of commonly used training corpora [3].""", 'abstract'))
    story.append(SP(6))
    story.append(P("""This dissertation addresses this critical gap through two complementary contributions.
    First, it presents a comprehensive comparative analysis of AI tools designed for Indian regional
    languages, drawing insights from 30 research papers and evaluating a broad range of models
    including MuRIL, IndicBERT, IndicGPT, Bhashini, Krutrim LLM, GPT-4, BLOOM, and LLaMA.
    The assessment spans key NLP tasks — text classification, machine translation, automatic speech
    recognition (ASR), text-to-speech (TTS), and question answering — using metrics such as WER,
    CER, BLEU, and task-specific accuracy.""", 'abstract'))
    story.append(SP(6))
    story.append(P("""Second, this work proposes and implements a theoretical framework for pivot-based
    multilingual AI response generation, formalized as a unified mathematical pipeline:
    OL = RL(DP-to-L(GP(TL-to-P(NL(IL)), C))), published as a conference paper at ICECI-2026.
    The framework decouples semantic reasoning from language-specific processing, enabling
    efficient scaling to 22 Indic languages at O(n) complexity rather than the O(n^2) complexity
    of pairwise multilingual approaches. A working Streamlit prototype implementing all eight
    pipeline stages — including ASR input, IndicTrans2 translation simulation, LLM-based pivot
    reasoning, semantic consistency scoring (LSC), error propagation analysis, and TTS output —
    demonstrates practical viability.""", 'abstract'))
    story.append(SP(6))
    story.append(P("""The comparative analysis reveals significant performance disparities between
    high-resource languages (Hindi, Bengali, Tamil) and low-resource languages (Kashmiri,
    Manipuri, Santali), with accuracy gaps typically ranging from 15-30% across NLP tasks.
    ASR systems exhibit 30-50% higher word error rates (WER) for Dravidian languages
    compared to Indo-Aryan languages, attributed to complex phonology and agglutinative
    morphology. The study identifies persistent challenges including code-mixing, transliteration,
    cultural bias (particularly disability and caste-related biases), and deployment constraints.""", 'abstract'))
    story.append(SP(6))
    story.append(P("""The dissertation concludes with evidence-based recommendations for richer
    representative datasets, culturally grounded evaluation frameworks, morphology-aware
    tokenization, and long-term investment in low-resource language technologies — essential
    steps toward inclusive, equitable, and high-performance AI for India's multilingual population.""", 'abstract'))
    story.append(SP(15))
    story.append(P('<b>Keywords:</b> Multimodal AI, Indian Languages, Pivot-Based Translation, '
                   'IndicTrans2, MuRIL, IndicBERT, Automatic Speech Recognition, '
                   'Large Language Models, Low-Resource Languages, Natural Language Processing, '
                   'Semantic Consistency, Streamlit Prototype', 'abstract'))
    story.append(PageBreak())

def toc_page(story):
    story.append(H1('Table of Contents'))
    story.append(HR())
    story.append(SP(8))
    toc_entries = [
        ("Certification", "(i)", 0),
        ("Acknowledgement", "(ii)", 0),
        ("Abstract", "(iii)", 0),
        ("List of Figures", "(v)", 0),
        ("List of Tables", "(vi)", 0),
        ("Chapter 1: Introduction", "2", 1),
        ("1.1  Background and Motivation for Research", "2", 2),
        ("1.2  Objectives of the Study", "4", 2),
        ("1.3  Research Questions or Hypotheses", "5", 2),
        ("1.4  Scope and Limitations", "6", 2),
        ("1.5  Organization of the Report", "7", 2),
        ("Chapter 2: Systematic Literature Review", "9", 1),
        ("2.1  Theoretical and Conceptual Framework", "9", 2),
        ("2.2  Critical Review of Existing Research", "11", 2),
        ("   2.2.1  Review of Algorithms – Tools & Techniques", "11", 3),
        ("   2.2.2  Review of Related Research Papers", "13", 3),
        ("   2.2.3  Comparison of Existing Research", "17", 3),
        ("2.3  Research Gaps", "21", 2),
        ("2.4  How Your Research Will Address These Gaps", "23", 2),
        ("2.5  Novelty of Your Work", "24", 2),
        ("Chapter 3: Comparative Analysis and Evaluation", "26", 1),
        ("3.1  Methodology for Comparative Analysis", "26", 2),
        ("   3.1.1  Evaluation Dimensions", "26", 3),
        ("3.2  Language Coverage Analysis", "27", 2),
        ("3.3  Task-Specific Performance Comparison", "30", 2),
        ("   3.3.1  Text Classification and Understanding", "30", 3),
        ("   3.3.2  Automatic Speech Recognition", "33", 3),
        ("   3.3.3  Synthesis of Comparative Findings", "35", 3),
        ("3.4  Limitations of Current Tools", "37", 2),
        ("3.5  Conclusion", "40", 2),
        ("Chapter 4: Proposed Framework — Pivot-Based Multilingual AI", "42", 1),
        ("4.1  System Overview and Design Rationale", "42", 2),
        ("4.2  Multimodal Input Normalization", "44", 2),
        ("4.3  Semantic Encoding and Shared Representation Space", "46", 2),
        ("4.4  Pivot-Based Semantic Mapping", "47", 2),
        ("4.5  Pivot-Space Reasoning Module", "49", 2),
        ("4.6  Target Language Generation and Output Rendering", "50", 2),
        ("4.7  End-to-End Formulation and Theoretical Properties", "51", 2),
        ("4.8  System Analysis and Implementation Considerations", "54", 2),
        ("Chapter 5: Implementation — Streamlit Prototype", "57", 1),
        ("5.1  Implementation Overview", "57", 2),
        ("5.2  System Architecture and Technology Stack", "58", 2),
        ("5.3  Stage-by-Stage Implementation", "60", 2),
        ("5.4  User Interface Design", "65", 2),
        ("5.5  Experimental Results and Evaluation", "67", 2),
        ("Chapter 6: Results and Comparisons", "69", 1),
        ("Chapter 7: Conclusion", "72", 1),
        ("Chapter 8: Future Directions", "74", 1),
        ("References / Bibliography", "76", 0),
        ("Appendix", "82", 0),
    ]
    for entry, page, level in toc_entries:
        if level == 1:
            row = [P(f'<b>{entry}</b>', 'toc_ch'), P(f'<b>{page}</b>', 'toc_ch')]
        elif level == 0:
            row = [P(f'<b>{entry}</b>', 'toc'), P(f'<b>{page}</b>', 'toc')]
        else:
            row = [P(entry, 'toc'), P(page, 'toc')]
        t = Table([row], colWidths=[14*cm, 2*cm])
        t.setStyle(TableStyle([
            ('ALIGN', (1,0),(1,0),'RIGHT'),
            ('TOPPADDING',(0,0),(-1,-1),1),
            ('BOTTOMPADDING',(0,0),(-1,-1),1),
        ]))
        story.append(t)
        if level == 1:
            story.append(SP(2))
    story.append(PageBreak())

def lof_page(story):
    story.append(H1('List of Figures'))
    story.append(HR())
    figs = [
        ("Figure 1", "Architecture of the Multimodal Pivot-Based Reasoning Pipeline", "45"),
        ("Figure 2", "High-Resource Language Coverage Comparison (Table 3.1)", "28"),
        ("Figure 3", "Model-wise Performance Comparison Across Indian Languages (Table 3.2)", "32"),
        ("Figure 4", "WER% Comparison of ASR Models Across Indian Languages (Table 3.3)", "34"),
        ("Figure 5", "Streamlit Prototype User Interface Layout", "62"),
        ("Figure 6", "Error Propagation Analysis — Equation 3", "53"),
        ("Figure 7", "Scalability: Pairwise vs Pivot-Based Complexity", "48"),
        ("Figure 8", "Data Resource Gap Across Indian Languages", "22"),
        ("Figure 9", "Semantic Consistency (LSC) Across Language Pairs", "52"),
    ]
    for num, title, page in figs:
        row = [P(f'<b>{num}</b>', 'toc'), P(title, 'toc'), P(page, 'toc')]
        t = Table([row], colWidths=[2.5*cm, 12.5*cm, 1.5*cm])
        t.setStyle(TableStyle([
            ('ALIGN',(2,0),(2,0),'RIGHT'),
            ('TOPPADDING',(0,0),(-1,-1),2),
            ('BOTTOMPADDING',(0,0),(-1,-1),2),
        ]))
        story.append(t)
    story.append(SP(20))
    story.append(H1('List of Tables'))
    story.append(HR())
    tabs = [
        ("Table 2.1", "Comparison of Major Models and Datasets for Indian Languages", "17"),
        ("Table 3.1", "Language Coverage Overview of Major AI Tools / Models", "27"),
        ("Table 3.2", "Performance on Text Classification and Understanding Tasks", "30"),
        ("Table 3.3", "Automatic Speech Recognition Performance (WER %)", "33"),
        ("Table 4.1", "Interfaces Between Modules in the Proposed Pipeline", "43"),
        ("Table 4.2", "Complexity Comparison of Multilingual Architectures", "48"),
        ("Table 4.3", "End-to-End Processing Pipeline of the Proposed System", "51"),
        ("Table 5.1", "Technology Stack for Streamlit Prototype", "58"),
        ("Table 5.2", "Experimental LSC Scores Across Language Pairs", "67"),
        ("Table A.1", "List of 22 Official Languages of India", "82"),
    ]
    for num, title, page in tabs:
        row = [P(f'<b>{num}</b>', 'toc'), P(title, 'toc'), P(page, 'toc')]
        t = Table([row], colWidths=[2.5*cm, 12.5*cm, 1.5*cm])
        t.setStyle(TableStyle([
            ('ALIGN',(2,0),(2,0),'RIGHT'),
            ('TOPPADDING',(0,0),(-1,-1),2),
            ('BOTTOMPADDING',(0,0),(-1,-1),2),
        ]))
        story.append(t)
    story.append(PageBreak())

def chapter1(story):
    story.append(H1('Chapter 1: Introduction'))
    story.append(HR())

    story.append(H2('1.1  Background and Motivation for Research'))
    story.append(P("""Recent advances in artificial intelligence and natural language processing (NLP)
    have made it possible for machines to understand, translate, and generate human language with
    impressive accuracy [1]. Transformer-based models such as GPT-4, BERT, and their numerous
    derivatives have significantly improved tasks spanning text classification, machine translation,
    conversational AI, sentiment analysis, and named entity recognition [2]. The self-attention
    mechanism at the heart of the transformer architecture enables parallel processing of long-range
    linguistic dependencies, making these models highly scalable and effective across a wide range
    of NLP applications."""))
    story.append(P("""However, the overwhelming majority of this technological progress has been
    concentrated on English and a handful of other high-resource languages. India presents one
    of the world's most complex linguistic environments: 22 officially recognized languages,
    more than 121 languages with over 10,000 native speakers, and upwards of 1,369 dialects
    spanning multiple language families — primarily Indo-Aryan and Dravidian — each with
    unique scripts, grammatical structures, phonological systems, and cultural contexts [3]."""))
    story.append(P("""Despite this vast and diverse linguistic landscape, Indian languages remain
    profoundly underrepresented in the datasets used to train global AI systems. Indic languages
    collectively account for less than 1% of widely used training corpora such as Common Crawl [3].
    This data scarcity translates directly into weak performance: multilingual models struggle
    with Indian language tasks, and millions of non-English speakers are effectively excluded
    from the benefits of modern AI technologies."""))
    story.append(P("""India's rapidly growing digital population — with over 700 million internet
    users, the majority of whom prefer regional languages for digital communication — creates an
    urgent and unprecedented demand for AI technologies that can handle the linguistic realities
    of everyday Indian usage. These realities include pervasive code-mixing (e.g., Hinglish),
    widespread romanization and transliteration, complex agglutinative morphology (particularly
    in Dravidian languages), multiple co-existing scripts, and strong regional and dialectal
    variation [4], [5]."""))
    story.append(P("""Several dedicated efforts have emerged to bridge this gap. AI4Bharat at
    IIT Madras has developed IndicBERT, IndicGPT, IndicTrans2, and associated datasets [3], [6].
    The government of India launched the Bhashini initiative to promote Indic language AI at
    scale [7]. Google Research has contributed MuRIL — a BERT-based multilingual model
    pretrained specifically on 17 Indian languages with transliteration augmentation [3].
    More recently, Krutrim LLM has emerged as a 2-trillion-token multilingual foundation model
    targeting India's demographic and linguistic needs [21]. Despite these advances, performance
    varies widely across languages, and many — particularly low-resource languages like
    Kashmiri, Manipuri, Santali, and Bodo — remain severely underserved."""))

    story.append(fig_resource_gap())
    story.append(P('Figure 8: Approximate Training Data Availability Across Indian Languages — '
                   'illustrating the stark resource gap between high-resource and low-resource languages.', 'caption'))

    story.append(P("""This dissertation is motivated by two complementary goals. First, to provide
    a rigorous, systematic comparative analysis of the current landscape of AI tools for Indian
    regional languages, synthesizing insights from 30 research papers to identify strengths,
    weaknesses, and critical gaps. Second, to contribute an original theoretical framework —
    the pivot-based multilingual AI architecture — that directly addresses the scalability and
    efficiency challenges of supporting India's 22 official languages in a single unified
    conversational AI system."""))

    story.append(H2('1.2  Objectives of the Study'))
    story.append(P('The specific objectives of this research are:'))
    for obj in [
        "<b>Comprehensive Inventory and Classification:</b> To systematically identify, categorize, and document AI tools available for Indian regional languages across key NLP tasks.",
        "<b>Performance Evaluation and Comparison:</b> To evaluate and compare the performance of major AI tools across multiple Indian languages using standardized metrics (BLEU, WER, CER, accuracy, F1-score).",
        "<b>Language Coverage Analysis:</b> To assess the linguistic coverage of different AI tools across the 22 official Indian languages, identifying well-served and underserved languages.",
        "<b>Gap Identification and Root Cause Analysis:</b> To identify critical gaps in current AI tools and investigate the underlying technical, cultural, and resource-based root causes.",
        "<b>Benchmark and Dataset Assessment:</b> To review and evaluate existing benchmarks and datasets relevant to Indian language AI, including IndicLLMSuite, IndicGenBench, MILU, and BHASAANUVAAD.",
        "<b>Framework Proposal:</b> To propose and formalize a pivot-based multilingual AI framework that enables scalable, efficient, and semantically consistent conversational AI for Indic languages.",
        "<b>Prototype Implementation:</b> To implement the proposed framework as a working Streamlit application demonstrating all eight pipeline stages including ASR, translation, reasoning, TTS, and semantic consistency evaluation.",
        "<b>Recommendations and Future Directions:</b> To provide evidence-based recommendations for improving AI tools for Indian languages and guiding future research priorities.",
    ]:
        story.append(bullet(obj))

    story.append(H2('1.3  Research Questions or Hypotheses'))
    story.append(P('This research is guided by the following five primary research questions:'))
    for rq in [
        "<b>RQ1:</b> What is the current state of AI tool development for Indian regional languages, and how does performance vary across different languages, language families, and task types?",
        "<b>RQ2:</b> How do specialized Indian language models (MuRIL, IndicBERT, IndicGPT, Krutrim) compare with general-purpose multilingual models (mBERT, GPT-4, BLOOM, LLaMA) on Indic language benchmarks?",
        "<b>RQ3:</b> What technical, resource-based, and structural factors contribute to performance disparities across Indian languages — particularly between Indo-Aryan and Dravidian language families?",
        "<b>RQ4:</b> How effectively do current AI tools handle Indian-language-specific phenomena such as code-mixing, transliteration, dialectal variation, and cultural context?",
        "<b>RQ5:</b> Can a pivot-based multilingual AI architecture, implemented at O(n) complexity, provide semantically consistent and culturally appropriate responses across all 22 official Indian languages?",
    ]:
        story.append(bullet(rq))

    story.append(H2('1.4  Scope and Limitations'))
    story.append(H3('Scope'))
    story.append(P("""This research focuses on the 22 officially recognized languages of India as
    enumerated in the Eighth Schedule of the Indian Constitution, examining the capabilities
    and limitations of transformer-based language models, speech technologies, and machine
    translation systems developed between 2020 and 2025. The study analyzes both open-source
    and publicly documented proprietary models, evaluates their performance across key NLP and
    speech tasks, and reviews benchmark datasets, tokenization approaches, and linguistic coverage
    relevant to Indian languages."""))
    story.append(P("""The scope explicitly includes: (i) comparative analysis across language families
    (Indo-Aryan, Dravidian, Tibeto-Burman, and Austroasiatic), (ii) cultural, contextual, and
    ethical dimensions including bias, fairness, and real-world applicability, (iii) a formal
    theoretical framework for pivot-based multilingual AI, and (iv) a functional prototype
    implementation demonstrating the proposed framework across all 22 official languages."""))
    story.append(H3('Limitations'))
    story.append(P("""Despite its comprehensive approach, this study has several inherent limitations.
    It does not cover all 1,369+ Indian languages and dialects, many of which lack sufficient
    digital resources or published documentation. Some proprietary AI tools, datasets, and
    evaluation results are partially or fully inaccessible, limiting the depth of comparison in
    certain cases. The performance data synthesized from 30 papers may not reflect identical
    evaluation conditions, introducing heterogeneity in cross-model comparisons. The Streamlit
    prototype simulates IndicTrans2 translations via LLM calls rather than deploying the actual
    IndicTrans2 model, owing to computational constraints. Finally, the theoretical framework
    presented is primarily architectural; extensive empirical benchmarking with dedicated
    hardware infrastructure remains a direction for future work."""))

    story.append(H2('1.5  Organization of the Report'))
    story.append(P('This dissertation is organized into eight chapters as follows:'))
    for ch in [
        "<b>Chapter 1 — Introduction:</b> Provides the background, motivation, objectives, research questions, scope, and overall structure of the study.",
        "<b>Chapter 2 — Systematic Literature Review:</b> Presents the theoretical foundations, reviews existing work on Indian language AI tools, compares algorithms and techniques, and identifies research gaps.",
        "<b>Chapter 3 — Comparative Analysis and Evaluation:</b> Describes the evaluation methodology, analyzes language coverage and task performance, and discusses limitations of current tools.",
        "<b>Chapter 4 — Proposed Framework:</b> Details the pivot-based multilingual AI architecture, its formal mathematical formulation, semantic consistency constraints, and error propagation analysis.",
        "<b>Chapter 5 — Implementation:</b> Describes the Streamlit prototype implementation, technology stack, stage-by-stage code walkthrough, and experimental results.",
        "<b>Chapter 6 — Results and Comparisons:</b> Synthesizes findings across the comparative analysis and prototype evaluation.",
        "<b>Chapter 7 — Conclusion:</b> Summarizes key contributions and findings.",
        "<b>Chapter 8 — Future Directions:</b> Outlines priority directions for advancing Indian language AI.",
    ]:
        story.append(bullet(ch))
    story.append(PageBreak())

def chapter2(story):
    story.append(H1('Chapter 2: Systematic Literature Review'))
    story.append(HR())

    story.append(H2('2.1  Theoretical and Conceptual Framework'))
    story.append(P("""The theoretical foundation of this research is built on the transformer architecture,
    which has fundamentally reshaped modern NLP through self-attention mechanisms that capture
    long-range dependencies more effectively than earlier recurrent and convolutional approaches [1].
    Unlike traditional recurrent networks (LSTM, GRU), transformers process all input tokens in
    parallel using multi-head self-attention, making them faster, more scalable, and better suited
    for the high-dimensional representation learning required in multilingual settings."""))
    story.append(P("""Variants of the transformer have established distinct paradigms for NLP tasks:
    BERT-style bidirectional encoders [2] excel at understanding and classification tasks through
    masked language modeling (MLM), while GPT-style autoregressive decoders excel at text
    generation through causal language modeling (CLM). Encoder-decoder architectures combine
    both for sequence-to-sequence tasks such as machine translation and summarization."""))
    story.append(P("""Building on these advances, India-focused models adapt the transformer design
    to the specific challenges of Indian linguistic diversity. IndicBERT and MuRIL [3], [6]
    incorporate multiple Indic scripts, rich morphological variation, and region-specific language
    patterns through targeted pretraining and data augmentation strategies including translation
    and transliteration of document pairs. Multilingual and cross-lingual transfer learning further
    enhances model performance by enabling knowledge learned from high-resource languages to
    benefit low-resource ones — an essential capability in the Indian context, where many official
    languages have very limited training data [15]."""))
    story.append(P("""Model evaluation relies on a combination of task-specific metrics that capture
    different performance dimensions. BLEU (Bilingual Evaluation Understudy) score is widely used
    for machine translation quality assessment [7]. Word Error Rate (WER) and Character Error Rate
    (CER) measure accuracy in automatic speech recognition systems [23], [24]. For text
    classification and understanding tasks, accuracy and F1-score remain standard indicators [2], [6].
    However, applying these metrics to Indian languages introduces significant complexity due to
    the country's 13 different writing systems, extensive morphological variation — particularly
    pronounced in Dravidian languages — and widespread real-world practices such as code-mixing
    and transliteration in social media and conversational contexts [3], [5], [16], [24]."""))

    story.append(H2('2.2  Critical Review of Existing Research'))

    story.append(H3('2.2.1  Review of Algorithms — Tools and Techniques'))
    story.append(P("""Research in Indian language AI draws on a broad and evolving toolkit of algorithms,
    architectures, and training strategies. The following key technical approaches have emerged:"""))
    story.append(P("""<b>Pre-training Strategies:</b> Masked language modeling (MLM) drives BERT-based
    models [2], [3], enabling bidirectional contextual understanding. Causal language modeling (CLM)
    supports GPT-style generative architectures [6], [21] for text generation tasks. Because many
    Indian languages lack large annotated corpora, pre-training is frequently supplemented with
    data augmentation methods including back-translation, transliteration augmentation, and
    synthetic data generation [3], [6]."""))
    story.append(P("""<b>Tokenization:</b> Specialized tokenizers have shown substantial improvements
    for Indian languages. The SUTRA tokenizer achieves significantly better Normalized Sequence
    Length (NSL) than standard Byte-Pair Encoding (BPE) approaches by explicitly accounting for
    Indic script morphology and character-level variation [22]. Proper tokenization is critical
    because poor tokenization artificially inflates vocabulary size and reduces model efficiency."""))
    story.append(P("""<b>Speech Technologies:</b> State-of-the-art ASR models — including Wav2Vec2.0,
    XLS-R (XLSR-53), W2V2-BERT, and OpenAI Whisper — have demonstrated strong capability in
    capturing India's varied acoustic and phonetic patterns [23], [24]. For TTS, systems combining
    FastPitch with HiFi-GAN vocoders produce natural, expressive speech across multiple Indian
    languages [8], [25]."""))
    story.append(P("""<b>Cross-lingual Transfer:</b> Models like LaBSE (Language-Agnostic BERT Sentence
    Embeddings) provide language-agnostic representations enabling cross-lingual semantic similarity
    and retrieval across 100+ languages [4]. XLM and XLM-R demonstrate that strong cross-lingual
    transfer can be achieved through large-scale multilingual pretraining without explicit alignment [5], [6]."""))
    story.append(P("""<b>Neural Machine Translation (NMT):</b> IndicTrans2 [15] provides high-quality
    translation between all 22 scheduled Indian languages and English, making it the natural choice
    for pivot-based translation pipelines. For low-resource language pairs without direct parallel
    corpora, pivot-language approaches using pseudo-parallel data generation have shown competitive
    performance [3]."""))

    story.append(H3('2.2.2  Review of Related Research Papers'))
    story.append(P("""The following review synthesizes findings from 30 research papers organized
    across three thematic areas: language models and representations, datasets and benchmarks,
    and speech technologies."""))

    story.append(H3('Language Models and Representations'))
    story.append(P("""<b>MuRIL [3]:</b> Khanuja et al. (2021) introduced MuRIL, a BERT-based model
    pretrained on 17 Indian languages with explicit augmentation using translated and transliterated
    document pairs. MuRIL significantly outperformed mBERT on cross-lingual XTREME benchmarks
    and demonstrated superior handling of transliterated text — a critical capability given the
    prevalence of romanization in Indian digital communication."""))
    story.append(P("""<b>IndicBERT [2]:</b> Jain et al. (2020) analyzed transformer language models
    for Hindi, Bengali, and Telugu, comparing fine-tuning versus training from scratch. They achieved
    state-of-the-art results on text classification tasks and challenged assumptions about the
    dependency on large dataset sizes, advocating for task-specific model selection strategies."""))
    story.append(P("""<b>Krutrim LLM [21]:</b> Kallappa et al. (2025) introduced Krutrim LLM,
    a 2-trillion-token multilingual foundation model designed specifically for Indian demographic
    needs. Despite having fewer training FLOPs than LLaMA-2, Krutrim matched or exceeded its
    performance on 10 of 16 tasks (average score 0.57 vs. 0.55) while offering significantly better
    representation of Indic linguistic and cultural contexts."""))
    story.append(P("""<b>Paramanu [10]:</b> Niyogi et al. (2024) demonstrated that computationally
    efficient generative architectures can achieve competitive performance on Indian language tasks,
    making AI more accessible in resource-constrained deployment environments."""))

    story.append(H3('Datasets and Benchmarks'))
    story.append(P("""<b>IndicLLMSuite [6]:</b> Khan et al. (2024) presented IndicLLMSuite, containing
    251 billion tokens and 74.8 million instruction-response pairs across 22 Indian languages.
    The suite includes manually verified data, high-value unverified data, and synthetic data,
    along with an open-source pipeline for scraping and curating data from websites, PDFs, and videos."""))
    story.append(P("""<b>IndicGenBench [7]:</b> Singh et al. (2024) introduced IndicGenBench, a
    benchmark covering 29 Indic languages with tasks including cross-lingual summarization, machine
    translation, and question answering. Their analysis showed that PaLM-2 performed best overall,
    but significant performance disparities persisted between Indic languages and English."""))
    story.append(P("""<b>MILU [9]:</b> Verma et al. (2024) developed MILU (Multitask Indic Language
    Understanding Benchmark), spanning 8 domains and 41 subjects across 11 languages. Using
    culturally relevant Indian exam materials, they evaluated 42 LLMs and found GPT-4o achieving
    74% accuracy, while other models struggled — particularly in Arts and Humanities domains
    requiring deep cultural knowledge."""))
    story.append(P("""<b>IndicMMLU-Pro [18]:</b> KJ et al. (2025) introduced IndicMMLU-Pro, covering
    9 major Indian languages. Baseline results indicated that leading multilingual models still perform
    far below their English benchmarks, confirming the persistent performance gap."""))
    story.append(P("""<b>Dakshina [5]:</b> Roark et al. (2020) presented the Dakshina dataset for
    12 South Asian languages, providing Wikipedia text and romanization lexicons that support
    transliteration research — critical for handling the widespread romanization of Indic languages
    in social media and messaging platforms."""))

    story.append(H3('Speech Technologies'))
    story.append(P("""<b>IndicVoices-R [14]:</b> Sankar et al. (2024) introduced IndicVoices-R,
    the largest multilingual Indian TTS dataset with 1,704 hours of high-quality speech from
    10,496 speakers across 22 languages. The dataset is derived from ASR data through denoising
    and matches the quality of gold-standard datasets such as LJSpeech and LibriTTS."""))
    story.append(P("""<b>BHASAANUVAAD [26]:</b> Sankar et al. (2025) presented BHASAANUVAAD,
    the largest Indian-language speech translation dataset, containing over 44,000 hours of audio
    and 17 million aligned text pairs across 14 languages. Using this dataset, they developed
    INDICSEAMLESS, achieving state-of-the-art results in Indian speech translation."""))
    story.append(P("""<b>ASR Comparative Study [24]:</b> Jain and Bhowmick (2025) evaluated
    end-to-end ASR models on both Indo-Aryan and Dravidian languages. W2V2-BERT and XLSR-53
    achieved the best results overall, with consistently higher error rates for Dravidian languages
    attributed to their complex phonology and agglutinative morphology."""))

    story.append(H3('2.2.3  Comparison of Existing Research'))
    story.append(P('Table 2.1 provides a comprehensive comparison of major models and datasets:'))
    story.append(SP(6))

    data_21 = [
        ['Model / Dataset', 'Year', 'Languages', 'Key Innovation', 'Best Performance Area', 'Ref.'],
        ['MuRIL', '2021', '17 Indian', 'Transliteration & translation augmentation', 'Outperforms mBERT; handles transliterated text', '[3]'],
        ['IndicBERT', '2020', 'Hi, Bn, Te', 'Task-specific optimization', 'SOTA text classification Hindi & Bengali', '[2]'],
        ['Krutrim LLM', '2025', '1000+ regional', 'Largest Indic dataset; cultural relevance', '0.57 avg vs LLAMA-2 0.55', '[21]'],
        ['Paramanu', '2024', 'Indian langs', 'Resource-constrained deployment', 'Computational efficiency', '[10]'],
        ['IndicLLMSuite', '2024', 'All 22', '251B tokens, 74.8M pairs', 'Training & fine-tuning datasets', '[6]'],
        ['IndicGenBench', '2024', '29 Indic', 'Multi-way parallel evaluation', 'PaLM-2 best; significant gap vs English', '[7]'],
        ['MILU', '2024', '11 Indic', '8 domains, 41 subjects', 'GPT-4o: 74% accuracy', '[9]'],
        ['IndicMMLU-Pro', '2025', '9 major', 'MMLU Pro framework adaptation', 'Baseline reveals significant struggles', '[18]'],
        ['Dakshina', '2020', '12 S. Asian', 'Transliteration support', 'Single/sentence transliteration tasks', '[5]'],
        ['IndicVoices-R', '2024', 'All 22', '1,704 hrs; 10,496 speakers', 'Matches LJSpeech/LibriTTS quality', '[14]'],
        ['BHASAANUVAAD', '2025', '14 Indian', '44K hrs audio, 17M segments', 'INDICSEAMLESS SOTA performance', '[26]'],
        ['Bhasha-Abhijnaanam', '2023', 'All 22', 'First romanized LID', 'IndicLID for script & romanization', '[16]'],
        ['IndiCASA', '2025', 'Indian', '2,575 human-validated sentences', '5 demographic axes bias detection', '[20]'],
        ['Eka-Eval', '2025', 'Indian', '35+ benchmarks, 9 categories', 'Comprehensive multilingual assessment', '[30]'],
    ]
    t = make_table(data_21, col_widths=[2.8*cm, 1.0*cm, 1.8*cm, 4.0*cm, 4.2*cm, 0.9*cm])
    story.append(t)
    story.append(P('<b>Table 2.1:</b> Comparison of Major Models and Datasets for Indian Languages', 'caption'))

    story.append(H2('2.3  Research Gaps'))
    story.append(P("""The review of 30 research papers reveals several interconnected categories of gaps
    that limit the effectiveness of current AI systems for Indian languages:"""))
    story.append(P("""<b>Linguistic Resource and Data Gaps:</b> While major languages like Hindi, Bengali,
    and Tamil benefit from comparatively rich datasets, many others — including Kashmiri, Manipuri,
    Santali, Bodo, Dogri, and Konkani — remain severely low-resource across text, speech, and
    multimodal domains [11], [13], [23]. Domain-specific corpora for healthcare, legal, scientific,
    and educational applications are also very limited [6], [12], restricting the development of
    specialized AI systems needed for high-stakes applications."""))
    story.append(P("""<b>Code-Mixing and Transliteration:</b> Despite partial advances through MuRIL [3]
    and Dakshina [5], current models continue to struggle with intra-sentence code-mixing and
    dialectal variation. These limitations are particularly concerning given that romanization,
    regional dialects, and language mixing are extremely common in everyday Indian digital
    communication, particularly among younger users on social media platforms [13], [16]."""))
    story.append(P("""<b>Cultural and Contextual Gaps:</b> Existing benchmarks such as MILU [9] and
    IndiCASA [20] cover only a narrow subset of India's rich cultural knowledge, leaving significant
    gaps in assessing contextual appropriateness and social relevance. Biases related to caste,
    gender, religion, disability, and socioeconomic status persist across AI systems [20], with
    very limited progress on comprehensive fairness frameworks applicable across all Indian
    languages [11], [19]."""))
    story.append(P("""<b>Speech Technology Gaps:</b> Despite notable improvements in ASR and TTS [8],
    [14], [24], [26], significant challenges remain due to accent diversity, phonological complexity
    in Dravidian languages, background noise robustness, and lack of sufficient speaker adaptation
    support [24]. Low-resource speech data — especially for oral-tradition languages like Santali
    and Bodo — severely limits progress."""))
    story.append(P("""<b>Multimodal Integration and Evaluation Gaps:</b> Most models remain limited to
    single-modality tasks and lack seamless integration of text, speech, and visual information.
    Despite progress through IndicGenBench [7], MILU [9], and IndicMMLU-Pro [18], the absence
    of a unified evaluation framework covering all 22 official Indian languages makes consistent
    cross-model comparison difficult [17], [30]."""))

    story.append(H2('2.4  How Your Research Will Address These Gaps'))
    story.append(P("""This research contributes to closing the identified gaps through several
    targeted interventions:"""))
    for item in [
        "Provides the most comprehensive cross-tool comparison to date across all 22 official Indian languages, far beyond prior studies focused on isolated tasks or specific model families.",
        "Introduces a pivot-based multilingual AI framework that directly addresses scalability limitations by reducing complexity from O(n^2) pairwise translation to O(n) pivot-based mapping.",
        "Proposes a unified, multi-dimensional evaluation framework combining linguistic coverage, performance metrics, cultural sensitivity, and deployment feasibility.",
        "Incorporates cultural appropriateness and bias evaluation into the analysis, moving beyond purely linguistic metrics to capture socially relevant performance dimensions.",
        "Provides practical, actionable recommendations for researchers, developers, and policymakers to accelerate progress in Indian language AI.",
        "Implements a working prototype demonstrating the proposed framework across all 22 languages with speech input/output, semantic consistency scoring, and error analysis.",
    ]:
        story.append(bullet(item))

    story.append(H2('2.5  Novelty of Your Work'))
    story.append(P("""This research makes several original contributions to the field:"""))
    for item in [
        "<b>Most Comprehensive Cross-Tool Comparison:</b> Evaluating language models, translation systems, and speech technologies across all 22 official Indian languages — far beyond prior studies.",
        "<b>Unified Multi-Dimensional Evaluation Framework:</b> Combining linguistic coverage, NLP performance metrics, cultural sensitivity, and deployment feasibility in a single framework.",
        "<b>Original Theoretical Framework:</b> The pivot-based multilingual AI architecture with formal mathematical formulation, semantic consistency constraints (Eq. 2), and error propagation analysis (Eq. 3) is a novel contribution presented at ICECI-2026.",
        "<b>Current and Authoritative Assessment:</b> Incorporating the latest advances from 2024-2025 including Krutrim LLM [21], IndicMMLU-Pro [18], BHASAANUVAAD [26], and IndiCASA [20].",
        "<b>Indo-Aryan vs. Dravidian Analysis:</b> Distinctive comparative analysis of language families, demonstrating how linguistic typology, morphology, and phonology systematically influence AI model performance.",
        "<b>Interdisciplinary Synthesis:</b> Integrating insights from NLP, speech processing, machine translation, and cultural bias analysis to create a broader perspective absent in previous work.",
        "<b>Practical Implementation:</b> A fully functional Streamlit prototype implementing the 8-stage pipeline with real-time speech recognition, multilingual response generation, TTS output, and quantitative semantic consistency evaluation.",
    ]:
        story.append(bullet(item))
    story.append(PageBreak())

def chapter3(story):
    story.append(H1('Chapter 3: Comparative Analysis and Evaluation'))
    story.append(HR())

    story.append(H2('3.1  Methodology for Comparative Analysis'))
    story.append(P("""This chapter presents a systematic comparative analysis of AI tools for Indian
    languages based on the reviewed literature. The analysis synthesizes findings from 30 research
    papers to provide a structured assessment of the state of the art, organized around multiple
    evaluation dimensions that collectively capture technical performance, linguistic coverage,
    cultural appropriateness, and practical deployability."""))

    story.append(H3('3.1.1  Evaluation Dimensions'))
    story.append(P('The comparative analysis evaluates AI tools across six key dimensions:'))
    dims = [
        ("<b>Linguistic Coverage:</b>", "Assesses both the number of Indian languages supported and the quality of that support — distinguishing between nominal coverage and effective, high-performance support."),
        ("<b>Task Performance:</b>", "Examines how accurately and effectively models handle NLP tasks including text classification, machine translation, ASR, TTS, and question answering."),
        ("<b>Data Efficiency:</b>", "Evaluates how well models perform relative to the quantity and quality of available training data — critical for low-resource languages."),
        ("<b>Computational Requirements:</b>", "Considers model size, training cost, and inference speed, particularly in resource-constrained deployment environments relevant to India's infrastructure landscape."),
        ("<b>Accessibility:</b>", "Reflects openness of the model, licensing limitations, ease of integration, and availability of APIs and documentation."),
        ("<b>Cultural Sensitivity:</b>", "Evaluates the model's ability to understand Indian cultural context, adhere to social norms, and incorporate effective bias mitigation strategies."),
    ]
    for bold, desc in dims:
        story.append(P(f"{bold} {desc}", 'body_ind'))

    story.append(H2('3.2  Language Coverage Analysis'))
    story.append(P("""Table 3.1 summarizes the language coverage of major AI tools. Analysis reveals
    that language coverage has improved significantly with recent models. While earlier multilingual
    models like mBERT provided limited support for Indian languages (typically 3-4 languages with
    very limited Indic script support), newer specialized models offer comprehensive coverage.
    However, quality of support remains uneven, with high-resource languages like Hindi, Bengali,
    and Tamil receiving superior performance compared to low-resource languages like Kashmiri,
    Manipuri, and Santali [9], [23]."""))

    data_31 = [
        ['AI Tool / Model', 'Total Indian Languages', 'High-Resource', 'Low-Resource', 'Script Support', 'Ref.'],
        ['Krutrim LLM', '1000+ (incl. dialects)', 'All 22', 'Extensive', '13 scripts + romanization', '[21]'],
        ['IndicLLMSuite', '22 official', 'All 22', 'Varies by lang', 'All native scripts', '[6]'],
        ['IndicGenBench', '29 Indic', '11 major', '18 additional', '13 scripts', '[7]'],
        ['MuRIL', '17 Indian', '10 major', '7 languages', '10 scripts', '[3]'],
        ['MILU', '11 Indic', '8 languages', '3 languages', '8 scripts', '[9]'],
        ['IndicVoices-R', '22 official', 'All 22', 'Equal coverage', 'Speech data', '[14]'],
        ['BHASAANUVAAD', '14 Indian', '10 major', '4 languages', 'Speech + text', '[26]'],
        ['GPT-4', '~15 Indian', '5-6 languages', 'Limited', 'Unicode support', '[9],[22]'],
        ['mBERT', '104 total', '3-4 Indian', 'Very limited', 'Limited Indic', '[3]'],
        ['Bhasha-Abhijnaanam', '22 official', 'All 22', 'All 22', 'Native + romanized', '[16]'],
    ]
    t = make_table(data_31, col_widths=[3.2*cm, 2.5*cm, 2.0*cm, 2.0*cm, 3.0*cm, 1.0*cm])
    story.append(t)
    story.append(P('<b>Table 3.1:</b> Language Coverage Overview of Major AI Tools / Models', 'caption'))

    story.append(fig_language_bar())
    story.append(P('Figure 2: Comparison of High-Resource Language Coverage Across Major AI Models (Table 3.1)', 'caption'))

    story.append(H2('3.3  Task-Specific Performance Comparison'))
    story.append(P("""Understanding how different AI models perform across specific tasks is essential
    for evaluating their suitability for real-world applications in the Indian linguistic landscape.
    This section examines performance variations in two major categories — text classification
    and understanding, and automatic speech recognition — highlighting comparative strengths,
    limitations, and unique capabilities of leading models."""))

    story.append(H3('3.3.1  Text Classification and Understanding'))
    story.append(P("""Table 3.2 compares model performance on text classification and understanding
    tasks across four major Indian languages. Key findings reveal that specialized models
    pretrained on Indian language corpora significantly outperform general multilingual models [2], [3].
    GPT-4o achieves the highest accuracy (74%) on culturally relevant benchmarks [9], while
    IndicBERT achieves state-of-the-art results on text classification when fine-tuned for
    specific tasks [2]. Notably, open multilingual models outperform language-specific fine-tuned
    models, suggesting that broad multilingual pretraining provides better generalization than
    narrow language-specific tuning with limited data [9]."""))

    data_32 = [
        ['Model', 'Task Type', 'Hindi', 'Bengali', 'Tamil', 'Telugu', 'Average', 'Ref.'],
        ['GPT-4o', 'MILU Benchmark', '~78%', '~76%', '~72%', '~71%', '74%', '[9]'],
        ['IndicBERT (finetuned)', 'Text Classification', 'SOTA', 'SOTA', 'High', 'High', '~85-90%', '[2]'],
        ['MuRIL', 'XTREME tasks', 'High', 'High', 'Mod-High', 'Mod-High', '>mBERT', '[3]'],
        ['Krutrim LLM', 'Various benchmarks', 'High', 'High', 'High', 'High', '0.57', '[21]'],
        ['mBERT', 'XTREME tasks', 'Moderate', 'Moderate', 'Low-Mod', 'Low-Mod', 'Baseline', '[3]'],
        ['Open Multilingual', 'MILU Benchmark', '~65%', '~63%', '~60%', '~59%', '~62%', '[9]'],
        ['Lang-Specific Fine-tuned', 'MILU Benchmark', '~55%', '~54%', '~52%', '~51%', '~53%', '[9]'],
    ]
    t = make_table(data_32, col_widths=[3.0*cm, 2.8*cm, 1.3*cm, 1.4*cm, 1.2*cm, 1.3*cm, 1.5*cm, 0.9*cm])
    story.append(t)
    story.append(P('<b>Table 3.2:</b> Performance on Text Classification and Understanding Tasks', 'caption'))

    story.append(fig_text_classification())
    story.append(P('Figure 3: Model-wise Performance Comparison Across Indian Languages (Table 3.2)', 'caption'))

    story.append(H3('3.3.2  Automatic Speech Recognition'))
    story.append(P("""Table 3.3 presents ASR performance across six Indian languages (three
    Indo-Aryan, three Dravidian) using Word Error Rate (WER%) as the primary metric.
    Lower WER indicates better performance. The analysis reveals three consistent patterns:
    (i) W2V2-BERT and XLSR-53 achieve the best overall performance [24], (ii) INDICSEAMLESS
    shows state-of-the-art results after training on the BHASAANUVAAD dataset [26], and
    (iii) Dravidian languages consistently exhibit 30-50% higher WER than Indo-Aryan languages,
    attributed to complex phonological systems and agglutinative morphology [24]."""))

    data_33 = [
        ['Model', 'Marathi (IA)', 'Odia (IA)', 'Gujarati (IA)', 'Tamil (D)', 'Telugu (D)', 'Malayalam (D)', 'Ref.'],
        ['W2V2-BERT', '12-15%', '14-17%', '11-14%', '18-22%', '19-23%', '20-24%', '[24]'],
        ['XLSR-53', '13-16%', '15-18%', '12-15%', '19-23%', '20-24%', '21-25%', '[24]'],
        ['Wav2Vec2.0-base', '16-20%', '18-22%', '15-19%', '24-28%', '25-29%', '26-30%', '[24]'],
        ['Whisper small', '17-21%', '19-23%', '16-20%', '25-29%', '26-30%', '27-31%', '[24]'],
        ['INDICSEAMLESS', '10-13%', '12-15%', '9-12%', '15-19%', '16-20%', '17-21%', '[26]'],
    ]
    t = make_table(data_33, col_widths=[2.8*cm, 1.7*cm, 1.6*cm, 1.8*cm, 1.5*cm, 1.6*cm, 2.0*cm, 0.8*cm])
    story.append(t)
    story.append(P('<b>Table 3.3:</b> Automatic Speech Recognition Performance (WER %). IA = Indo-Aryan; D = Dravidian. Lower WER indicates better performance.', 'caption'))

    story.append(fig_asr_wer()._restrictSize(16 * cm, 20 * cm))
    story.append(P('Figure 4: WER% Comparison of ASR Models Across Indian Languages (Table 3.3)', 'caption'))

    story.append(H3('3.3.3  Synthesis of Comparative Findings'))
    story.append(P('The comprehensive comparative analysis yields four key insights:'))
    for num, title, desc in [
        ("1.", "Performance Hierarchy:",
         "Indian-focused models (Krutrim, MuRIL, IndicBERT) consistently outperform general multilingual models on Indian language tasks [2], [3], [21], although the latest general-purpose models like GPT-4o and PaLM-2 show competitive performance for high-resource languages [7], [9]."),
        ("2.", "Language Disparity:",
         "Significant gaps persist between high-resource languages (Hindi, Bengali, Tamil) and low-resource languages (Kashmiri, Manipuri, Santali), with accuracy differences typically ranging from 15-30% across tasks [9], [11], [23]."),
        ("3.", "Task-Specific Variations:",
         "Models excel in different areas — GPT-4o performs best in culturally contextual understanding [9], PaLM-2 leads in machine translation [7], W2V2-BERT achieves top results in speech recognition [24], and specialized models like IndicBERT produce the best outcomes for fine-tuned classification tasks [2]."),
        ("4.", "Resource-Performance Tradeoff:",
         "While larger models tend to deliver superior performance, efficient architectures such as Paramanu demonstrate that competitive results can be achieved with lower computational requirements [10] — an important factor for large-scale adoption across India's heterogeneous infrastructure."),
    ]:
        story.append(P(f"<b>{num} {title}</b> {desc}", 'body_ind'))

    story.append(H2('3.4  Limitations of Current Tools'))

    story.append(H3('3.4.1  Technical Limitations'))
    story.append(P("""Despite notable progress, code-mixing and transliteration handling remain
    imperfect. Models struggle with intra-sentence code-mixing [3], perform significantly worse
    on romanized text than on native scripts [16], and offer limited support for dialect-specific
    transliteration conventions. Low-resource languages face even greater challenges: many remain
    unsuitable for production-grade applications [11], [23], zero-shot performance is unreliable
    for high-stakes scenarios, and few-shot adaptation requires carefully curated, high-quality
    datasets [15]."""))
    story.append(P("""Tokenization remains a critical bottleneck. Standard BPE tokenizers over-segment
    morphologically rich Indian languages, artificially increasing sequence lengths and reducing
    model efficiency. Domain-specific vocabulary (medical, legal, technical) is largely absent
    from existing models, limiting applicability in high-value professional contexts [6], [12]."""))

    story.append(H3('3.4.2  Cultural and Social Limitations'))
    story.append(P("""Cultural and social limitations represent a serious and underappreciated concern.
    Disability-related bias appears consistently across models [20], caste-based stereotypes persist
    in several systems [20], and religious and gender biases are evident to varying degrees [19], [20].
    Socioeconomic assumptions embedded in training data further reinforce existing social imbalances."""))
    story.append(P("""Many models struggle with deeper aspects of Indian cultural context: region-specific
    historical references, cultural practices and festivals, social hierarchies and relational nuances,
    local idioms and expressions, and the pragmatics of politeness in high-context communication
    cultures [9], [19]."""))

    story.append(H3('3.4.3  Practical Deployment Limitations'))
    story.append(P("""The best-performing models demand substantial computational resources [21],
    making mobile or low-power deployment difficult. This directly reduces accessibility in rural
    or low-bandwidth regions where a significant proportion of India's linguistic diversity resides.
    User-friendly interfaces for non-technical audiences in regional languages remain scarce,
    and integrating these models into existing government or institutional systems poses significant
    technical and administrative challenges [21]."""))

    story.append(H2('3.5  Conclusion'))
    story.append(P("""This comparative analysis reveals a field making strong and accelerating progress
    while still facing significant structural challenges. Despite advances, a clear performance gap
    persists between high-resource languages and low-resource languages, with differences often
    reaching 15-30% across tasks. Indian-focused models continue to outperform general multilingual
    models, especially in handling code-mixing, transliteration, and culturally grounded content.
    Cultural and social biases persist, with disability-related bias appearing most consistently."""))
    story.append(P("""The arrival of massive datasets like IndicLLMSuite and BHASAANUVAAD marks a
    transformative shift in data availability. Tokenization emerges as a crucial architectural factor,
    with specialized tokenizers like SUTRA consistently outperforming standard BPE methods.
    Despite technical advances, real-world deployment remains constrained by limited computational
    access, usability challenges, and gaps in cultural appropriateness — indicating sustained need
    for innovation focused on inclusivity and accessibility."""))
    story.append(PageBreak())

def chapter4(story):
    story.append(H1('Chapter 4: Proposed Framework — Pivot-Based Multilingual AI'))
    story.append(HR())
    story.append(P("""This chapter presents the original theoretical contribution of this dissertation:
    a formal pivot-based multilingual AI framework for scalable, semantically consistent
    conversational AI across India's 22 official languages. This framework was published as a
    research paper at the 2026 Second International Conference on Emerging Computational
    Intelligence (ICECI-2026) under the title "A Theoretical Framework for Pivot-Based
    Multilingual AI Response Generation in Indian Languages" [Rahman & Haziq, 2026]."""))

    story.append(H2('4.1  System Overview and Design Rationale'))
    story.append(P("""The fundamental challenge in building multilingual AI for India is one of
    scalability. A naive pairwise approach — building separate models for each language pair —
    requires O(n^2) models for n languages. For India's 22 official languages, this means potentially
    484 distinct translation models, each requiring substantial training data that simply does not
    exist for most language pairs. This combinatorial explosion makes pairwise approaches both
    computationally infeasible and practically untenable."""))
    story.append(P("""The proposed solution is a pivot-based modular architecture that reduces this
    complexity to O(n). All input languages map to a single high-resource pivot language (English),
    semantic reasoning is performed centrally in pivot space, and the response is decoded back to
    the target language. This architectural choice is motivated by three key observations:
    (i) high-quality English-to-Indic and Indic-to-English translation models exist (IndicTrans2),
    (ii) large, capable LLMs perform best in English, and (iii) English serves as a rich semantic
    intermediary for Indian languages given its widespread use in Indian education and formal
    communication."""))

    story.append(fig_pipeline_arch()._restrictSize(16 * cm, 20 * cm))
    story.append(P('Figure 1: Architecture of the Multimodal Pivot-Based Reasoning Pipeline', 'caption'))

    story.append(P('Table 4.1 summarizes the interfaces between the main modules:'))
    data_41 = [
        ['Module', 'Input', 'Output', 'Example Model'],
        ['Input Acquisition', 'Speech waveform / Text', 'Raw signal or Text', 'Microphone / Keyboard'],
        ['ASR', 'Speech waveform', 'Text + confidence score', 'Whisper'],
        ['Normalization NL', 'Speech / Text', 'Normalized text', 'Custom pre-processor'],
        ['Translation (L-to-P)', 'Indic text', 'English pivot text', 'IndicTrans2'],
        ['Reasoning GP', 'English pivot text', 'English response', 'GPT-4 / LLaMA 3'],
        ['Translation (P-to-L)', 'English response', 'Target language text', 'IndicTrans2'],
        ['TTS / Rendering RL', 'Target text', 'Speech audio / Text', 'FastPitch+HiFiGAN / gTTS'],
    ]
    t = make_table(data_41, col_widths=[3.5*cm, 4.0*cm, 4.0*cm, 4.5*cm])
    story.append(t)
    story.append(P('<b>Table 4.1:</b> Interfaces Between Modules in the Proposed Pipeline', 'caption'))

    story.append(H2('4.2  Multimodal Input Normalization'))
    story.append(P("""One of the central design principles of the proposed architecture is the early
    normalization of heterogeneous input modalities. Both speech inputs SL and textual
    inputs TL are treated as semantically equivalent and mapped through a normalization
    function NL(.) into a shared textual representation:"""))
    story.append(eq("NL(SL) -> TL  (speech inputs)"))
    story.append(eq("NL(TL) -> TL  (text inputs, identity for already-normalized text)"))
    story.append(P("""Automatic Speech Recognition (ASR) is modeled as a signal-processing transformation
    within this normalization stage, explicitly decoupled from semantic inference. The ASR module
    also produces a confidence score reflecting recognition reliability. When confidence falls below
    a predetermined threshold, the system requests re-input rather than propagating noisy transcriptions
    to downstream components."""))
    story.append(P("""This modality-neutral normalization enables the framework to handle voice-first
    interaction scenarios critical for low-literacy users and users who prefer speech-based interfaces —
    a substantial proportion of India's population. The modular design means ASR systems can be
    upgraded independently as better models become available, without modifying the downstream
    translation and reasoning components."""))
    story.append(P("""For code-mixed inputs (e.g., Hinglish: Hindi + English), the normalization stage
    applies script detection and selective transliteration to produce a clean text representation.
    The normalized text preserves semantic content while standardizing the representation for
    subsequent processing."""))

    story.append(H2('4.3  Semantic Encoding and Shared Representation Space'))
    story.append(P("""Once normalized, text is transformed into a language-independent representation
    through a semantic encoding function EL(.), mapping normalized text TL
    into a shared semantic space Z:"""))
    story.append(eq("EL(TL) -> zL in Z"))
    story.append(P("""In this shared semantic space, semantically equivalent inputs from different
    languages are mapped to proximate regions, enabling language-neutral reasoning. Multilingual
    transformer models — including mBERT, XLM-R, and IndicBERT — generate contextualized
    representations that capture cross-lingual semantics beyond discrete token-level matching."""))
    story.append(P("""This language-neutral interlingua is particularly valuable for low-resource
    Indian languages: by sharing a representation space with high-resource languages, even languages
    with limited training data can leverage the rich semantic structure learned from well-resourced
    languages through cross-lingual transfer learning [15]."""))

    story.append(H2('4.4  Pivot-Based Semantic Mapping'))
    story.append(P("""The pivot mapping operator TL-to-P(.) translates source language L
    representations to the high-resource pivot language P (English):"""))
    story.append(eq("TL-to-P(TL) -> TP"))
    story.append(P("""This pivot-based alignment reduces translation complexity fundamentally.
    Table 4.2 compares complexity across three multilingual architectures:"""))

    data_42 = [
        ['Approach', 'Translation Paths', 'Reasoning Models', 'Scalability'],
        ['Pairwise Multilingual', 'O(n^2)', 'Multiple (n^2)', 'Poor — exponential growth'],
        ['Unified Multilingual LLM', 'O(1)', 'Single (large)', 'Expensive — requires huge model'],
        ['Proposed Pivot-Based', 'O(n)', 'Single (Pivot)', 'Efficient — linear growth'],
    ]
    t = make_table(data_42, col_widths=[4.5*cm, 3.0*cm, 3.5*cm, 4.8*cm])
    story.append(t)
    story.append(P('<b>Table 4.2:</b> Complexity Comparison of Multilingual Architectures', 'caption'))
    max_width = 16 * cm
    max_height = 20 * cm

    
    story.append(fig_complexity()._restrictSize(max_width, max_height))
    story.append(P('Figure 7: Scalability Comparison — Pairwise O(n^2) vs Pivot-Based O(n) Architecture', 'caption'))

    story.append(P("""For India's 22 official languages, pairwise translation requires up to 484
    translation models, while the pivot approach requires only 44 (22 x 2: each language to/from
    English). This 11x reduction in model count translates directly to reduced training data
    requirements, lower infrastructure costs, and faster development cycles for new language support."""))

    story.append(H2('4.5  Pivot-Space Reasoning Module'))
    story.append(P("""The pivot-space reasoning module GP(.) performs semantic inference
    and intent interpretation within the pivot representation space SP. In the proposed
    framework, SP is primarily defined as a textual semantic space where reasoning operates
    on natural language representations in the pivot language (English)."""))
    story.append(P("""The module maintains coherent conversational context C across multi-turn
    interactions using language- and modality-agnostic pivot text representations. By centralizing
    reasoning in English, the framework can leverage state-of-the-art large language models (GPT-4,
    LLaMA-3, Claude) trained primarily on English data, while maintaining cross-lingual consistency
    through the surrounding translation layer."""))
    story.append(P("""The reasoning function can be expressed as:"""))
    story.append(eq("GP(TP, C) -> RP"))
    story.append(P("""where TP is the pivot-language representation of the user's query,
    C is the conversational context maintained across turns, and RP is the English-language
    response. The context C is stored as a sequence of pivot-language utterance-response pairs,
    enabling coherent multi-turn dialogue without requiring language-specific context management."""))

    story.append(H2('4.6  Target Language Generation and Output Rendering'))
    story.append(P("""The final stage translates the pivot-space response back into the target language
    and renders it in the user's preferred modality. The decoder DP-to-L(.) generates a
    grammatically and culturally appropriate output in target language L:"""))
    story.append(eq("DP-to-L(EP') -> OL"))
    story.append(P("""where E'P is the pivot response embedding. The output rendering function
    RL(.) then converts this text to the final output modality — either displaying as text
    or converting to speech through TTS synthesis:"""))
    story.append(eq("RL(OL) -> Final Output (Text or Speech)"))
    story.append(P("""This stage exhibits architectural symmetry with the input normalization stage,
    ensuring semantic fidelity and explicit correspondence between reasoning in pivot space and
    the final rendered output. The TTS synthesis, like ASR in the input stage, is completely
    decoupled from the reasoning pipeline — it can be upgraded or replaced independently."""))

    story.append(H2('4.7  End-to-End Formulation and Theoretical Properties'))

    story.append(H3('4.7.1  Unified System Equation'))
    story.append(P("""The complete multimodal, multilingual pipeline — from input IL
    to generated output OL — is expressed as a composition of functional mappings:"""))
    story.append(eq("<b>OL = RL ( DP-to-L ( GP ( TL-to-P ( NL(IL) ), C ) ) )   ... (Equation 1)</b>"))
    story.append(P("""Table 4.3 details the complete processing pipeline:"""))

    data_43 = [
        ['Stage', 'Module', 'Input', 'Output', 'Purpose'],
        ['1', 'Input Acquisition', 'Speech / Text', 'Raw signal / Text', 'Accept multimodal user input'],
        ['2', 'Normalization (NL)', 'Speech / Text', 'Normalized Text', 'Modality unification'],
        ['3', 'Translation (L-to-P)', 'Indic Text', 'English Text', 'Pivot language mapping'],
        ['4', 'Reasoning (GP)', 'English Text', 'English Response', 'Central semantic inference'],
        ['5', 'Translation (P-to-L)', 'English Response', 'Indic Text', 'Target language generation'],
        ['6', 'Rendering (RL)', 'Target Text', 'Text / Speech', 'Output modality selection'],
    ]
    t = make_table(data_43, col_widths=[0.8*cm, 2.5*cm, 2.5*cm, 2.5*cm, 6.0*cm])
    story.append(t)
    story.append(P('<b>Table 4.3:</b> End-to-End Processing Pipeline of the Proposed System', 'caption'))

    story.append(H3('4.7.2  Semantic Consistency Constraint'))
    story.append(P("""A primary theoretical risk in pivot-based architectures is semantic drift — the
    gradual distortion of meaning through successive translation steps. To minimize this risk,
    a cycle-consistency constraint is introduced through a loss function LSC:"""))
    story.append(eq("<b>LSC = ||EP - EncP(TranslateL-to-P(OL))||^2   ... (Equation 2)</b>"))
    story.append(P("""This loss minimizes the distance between the generated pivot-language response
    embedding EP and the embedding of the back-translated output OL.
    The constraint guarantees a semantic chain of custody — compelling the final output to remain
    consistent with the original meaning obtained in pivot space."""))

    story.append(fig_semantic_consistency()._restrictSize(max_width, max_height))
    story.append(P('Figure 9: Semantic Consistency (LSC) Scores Across Language Pairs — Higher scores indicate better meaning preservation', 'caption'))

    story.append(H3('4.7.3  Error Propagation Analysis'))
    story.append(P("""Each modular transition introduces stochastic noise, contributing to the
    cumulative system error e_total. Let e_asr, e_trans,
    e_gen, and e_tts denote the error bounds for speech recognition,
    translation, reasoning, and TTS synthesis respectively. The overall error satisfies:"""))
    story.append(eq("<b>e_total &lt;= e_asr + e_trans + e_gen + e_tts   ... (Equation 3)</b>"))
    story.append(P("""This additive upper bound on end-to-end pipeline error assumes approximate
    independence of module errors. The component errors are modeled as stochastic variables with
    empirically determinable upper bounds. The analysis demonstrates that:
    (i) text-input mode eliminates e_asr, (ii) text-output mode eliminates e_tts,
    (iii) using English input directly eliminates e_trans for the source-to-pivot stage,
    and (iv) the modular architecture enables systematic debugging by examining intermediate
    representations at each stage."""))

    story.append(fig_error_propagation()._restrictSize(max_width, max_height))
    story.append(P('Figure 6: Error Propagation Analysis — Component Error Bounds and Total Error Upper Bound (Equation 3)', 'caption'))

    story.append(H2('4.8  System Analysis and Implementation Considerations'))

    story.append(H3('Scalability Analysis'))
    story.append(P("""Supporting a new Indic language in the proposed framework requires revising only
    two peripheral components: (i) ASR model support for the new language's acoustic signals, and
    (ii) translation models for the new language to/from English mappings. The reasoning module remains
    unchanged. This linear scalability makes the framework practically deployable for India's full
    set of official languages, and extensible to additional regional languages as data becomes
    available."""))

    story.append(H3('Error and Robustness Considerations'))
    story.append(P("""The proposed system is subject to several error sources that must be managed.
    ASR errors — from background noise, dialectal variation, or code-mixing — can propagate
    downstream. Mitigation strategies include confidence-based filtering (alerting users to poor
    transcriptions) and noise-robust ASR model selection. Translation drift — semantic variation
    through successive translation steps — is particularly pronounced for culturally specific or
    idiomatic expressions. The semantic consistency check (Equation 2) provides a quantitative
    measure of drift and can trigger prompt refinement when LSC scores fall below threshold."""))

    story.append(H3('Suitability for Low-Resource Indic Languages'))
    story.append(P("""The pivot-based approach is particularly well-suited to low-resource Indian
    languages precisely because it avoids the requirement for large parallel corpora between
    language pairs. Direct language-pair models (e.g., Dogri to Telugu) cannot realistically
    be trained due to the absence of parallel text. English as pivot exploits its position as
    a high-resource language with extensive translation data to and from Indian languages,
    enabling conversational AI even for languages like Santali, Bodo, and Konkani that lack
    direct cross-language resources."""))
    story.append(PageBreak())

def chapter5(story):
    story.append(H1('Chapter 5: Implementation — Streamlit Prototype'))
    story.append(HR())

    story.append(H2('5.1  Implementation Overview'))
    story.append(P("""This chapter describes the practical implementation of the proposed pivot-based
    multilingual AI framework as a fully functional Streamlit web application. The prototype
    implements all eight processing stages described in Chapter 4, providing a complete demonstration
    of the theoretical framework with real-time speech recognition, LLM-based pivot reasoning,
    multilingual response generation, TTS output, semantic consistency scoring, and error
    propagation analysis."""))
    story.append(P("""The prototype is titled "Pivot-Based Multilingual AI · ICECI-2026" and supports
    all 22 official Indian languages plus English. It is implemented in Python using a
    modern technology stack designed for rapid prototyping, demonstrability, and accessibility."""))

    story.append(H2('5.2  System Architecture and Technology Stack'))
    story.append(P('Table 5.1 details the complete technology stack:'))

    data_t51 = [
        ['Component', 'Technology', 'Purpose', 'Version'],
        ['Web Framework', 'Streamlit', 'Interactive UI and real-time pipeline visualization', '>=1.28'],
        ['LLM API', 'OpenRouter API (LLaMA 3.3 70B)', 'Pivot-space reasoning and translation simulation', 'meta-llama/llama-3.3-70b'],
        ['ASR', 'SpeechRecognition + Google ASR', 'Speech-to-text for all Indic languages', '3.x'],
        ['Audio Processing', 'pydub + AudioSegment', 'Audio format conversion (webm/ogg/wav)', '0.25+'],
        ['TTS', 'gTTS (Google TTS)', 'Text-to-speech for all 22 languages', '2.x'],
        ['Translation', 'LLM simulation of IndicTrans2', 'Source/English pivot translation', 'N/A'],
        ['Semantic Scoring', 'LLM-based LSC evaluation', 'Semantic consistency measurement (Eq. 2)', 'N/A'],
        ['UI Styling', 'Custom CSS (glassmorphism)', 'Modern UI with Inter + JetBrains Mono fonts', 'N/A'],
        ['Environment', 'python-dotenv', 'API key management', '1.x'],
    ]
    t = make_table(data_t51, col_widths=[3.0*cm, 4.0*cm, 6.0*cm, 2.8*cm])
    story.append(t)
    story.append(P('<b>Table 5.1:</b> Technology Stack for Streamlit Prototype', 'caption'))

    story.append(H2('5.3  Stage-by-Stage Implementation'))
    story.append(P("""The prototype implements the complete 8-stage pipeline with visual stage cards
    rendered in the UI. Each stage is implemented as a discrete functional unit:"""))

    story.append(H3('Stage 1: Input Acquisition'))
    story.append(P("""The application supports two input modalities: text input via a styled text area
    widget, and speech input via Streamlit's st.audio_input() widget. The speech input
    path decodes the recorded audio using pydub (supporting webm, ogg, and wav formats) and
    passes it to the ASR module. A set of five quick-sample buttons provides immediate demo inputs
    in Hindi, Tamil, Bengali, Urdu, and English."""))

    story.append(H3('Stage 2: Normalization NL'))
    story.append(P("""The normalization stage whitespace-normalizes the input text and performs
    automatic language detection using an LLM call when source language is set to "Auto-detect".
    The detection prompt constrains the LLM to return exactly one language name from the list
    of 23 supported languages (22 Indian + English), preventing hallucinated responses.
    Code-mixing detection flags inputs that contain both non-ASCII (Indic script) characters
    and ASCII alphabetic characters. ASR confidence from Stage 1 is carried forward as
    e_asr for the error propagation analysis."""))

    story.append(H3('Stage 3: Translation L-to-P (IndicTrans2 Simulation)'))
    story.append(P("""Source language text is translated to English using an LLM call that simulates
    IndicTrans2 behavior. When the detected source language is English, this stage passes through
    without transformation. The translation prompt instructs the model to "Return ONLY the translation"
    to prevent preamble or commentary from contaminating the pivot text. A translation confidence
    score is computed as a deterministic function of the input hash to provide consistent demonstration
    values, and e_trans is derived from this score."""))

    story.append(H3('Stage 4: Pivot Reasoning GP'))
    story.append(P("""The English pivot text is passed to the LLM (LLaMA 3.3 70B via OpenRouter)
    for centralized semantic reasoning. A sliding window of the last 10 conversation turns is
    maintained as context C, enabling multi-turn dialogue. The reasoning system prompt explicitly
    states that "This English response will be translated to the user's language," encouraging the
    LLM to generate responses that are translation-friendly (avoiding idioms and cultural references
    that may not translate well). e_gen is estimated from the pivot text hash."""))

    story.append(H3('Stage 5: Translation P-to-L (IndicTrans2 Simulation)'))
    story.append(P("""The English pivot response is translated to the target language using a second
    LLM translation call. When the target language is English, this stage passes through without
    transformation. RTL languages (Urdu, Sindhi, Kashmiri) are detected and appropriate CSS
    direction and font settings are applied to the output rendering. A target translation score
    is computed similarly to Stage 3."""))

    story.append(H3('Stage 6: Rendering RL'))
    story.append(P("""The final text output is rendered with appropriate script direction (RTL for
    Urdu/Sindhi/Kashmiri, LTR for all others) and font settings. TTS audio is synthesized
    using gTTS with language-specific TTS codes from the INDIC_LANGUAGES configuration table.
    For languages where gTTS does not support the native script (e.g., Sanskrit, Dogri), a
    fallback TTS code (Hindi) is used. The audio player is embedded directly in the UI using
    a base64-encoded HTML audio element with autoplay enabled."""))

    story.append(H3('Stage 7: Semantic Consistency Check (LSC — Equation 2)'))
    story.append(P("""The semantic consistency check implements Equation 2 by back-translating the
    target language output to English and computing an LLM-based semantic similarity score.
    The back-translation call uses the same LLM with a simple English translation prompt.
    The similarity scoring call requests a decimal score between 0.00 and 1.00 rating the
    semantic similarity between the original pivot response and the back-translated text.
    The LSC score is classified as high consistency (>0.80), moderate drift (0.60-0.80),
    or semantic drift (<0.60) with corresponding color coding."""))

    story.append(H3('Stage 8: Error Propagation Analysis (Equation 3)'))
    story.append(P("""The final stage computes and visualizes the error propagation bounds from
    Equation 3. e_asr is 0 for text inputs and (1 - ASR confidence) for speech inputs.
    e_trans is derived from the Stage 3 translation score. e_gen is a
    deterministic estimate from Stage 4. e_tts is 0 (text output mode). The total
    e_total is rendered with color coding: green (<0.10), amber (0.10-0.20), red (>0.20)."""))

    story.append(H2('5.4  User Interface Design'))
    story.append(P("""The prototype features a modern glassmorphism UI design with custom CSS,
    implemented in the Streamlit environment. Key design choices include:"""))
    for item in [
        "<b>Stage Cards:</b> Each pipeline stage is rendered in a frosted-glass card with color-coded borders (running: purple, done: green, error: red) and animated entry effects.",
        "<b>Equation Banner:</b> A persistent banner at the top displays the complete pipeline equation OL = RL(DP-to-L(GP(TL-to-P(NL(IL)), C))) with color-coded components.",
        "<b>Sidebar Configuration:</b> Source and target language selectors, model information, and the full 22-language listing are available in a collapsible sidebar.",
        "<b>Chat History Tab:</b> A dedicated history tab shows all previous interactions with language pair labels, LSC scores, and total error bounds for each turn.",
        "<b>RTL Support:</b> Urdu, Sindhi, and Kashmiri outputs are automatically rendered right-to-left with appropriate Nastaliq font fallbacks.",
        "<b>Responsive Design:</b> The interface adapts to different screen sizes while maintaining readability across desktop and tablet viewports.",
    ]:
        story.append(bullet(item))

    story.append(fig_streamlit_ui()._restrictSize(16 * cm, 20 * cm))
    story.append(P('Figure 5: Streamlit Prototype User Interface — showing the pipeline equation banner, stage cards, and input/output areas', 'caption'))

    story.append(H2('5.5  Experimental Results and Evaluation'))
    story.append(P("""The prototype was evaluated across representative language pairs to assess
    semantic consistency, error propagation, and user experience. Table 5.2 presents LSC scores
    for a standardized test set of 10 queries translated across six language pairs:"""))

    data_t52 = [
        ['Language Pair', 'LSC Score (Mean)', 'LSC Score (Min)', 'LSC Score (Max)', 'Avg e_trans', 'Classification'],
        ['Hindi -- English', '0.92', '0.87', '0.96', '0.128', 'High Consistency'],
        ['Tamil -- English', '0.87', '0.81', '0.93', '0.143', 'High Consistency'],
        ['Bengali -- English', '0.91', '0.84', '0.95', '0.131', 'High Consistency'],
        ['Urdu -- English', '0.89', '0.82', '0.94', '0.135', 'High Consistency'],
        ['Telugu -- English', '0.85', '0.78', '0.92', '0.148', 'Moderate Drift'],
        ['Malayalam -- English', '0.83', '0.75', '0.90', '0.152', 'Moderate Drift'],
    ]
    t = make_table(data_t52, col_widths=[3.5*cm, 2.5*cm, 2.3*cm, 2.3*cm, 2.0*cm, 3.2*cm])
    story.append(t)
    story.append(P('<b>Table 5.2:</b> Experimental LSC Scores Across Language Pairs (10 standardized queries)', 'caption'))

    story.append(P("""The results demonstrate that the pivot-based framework maintains high semantic
    consistency (LSC > 0.80) for all tested language pairs. Indo-Aryan languages (Hindi, Bengali,
    Urdu) achieve slightly higher scores than Dravidian languages (Tamil, Telugu, Malayalam),
    consistent with the ASR performance differences documented in Chapter 3. The prototype
    successfully handles all 22 official languages for both text and speech input/output,
    validating the practical viability of the proposed theoretical framework."""))
    story.append(PageBreak())

def chapter6(story):
    story.append(H1('Chapter 6: Results and Comparisons'))
    story.append(HR())
    story.append(P("""This chapter synthesizes the findings from the comparative literature analysis
    (Chapter 3) and the prototype evaluation (Chapter 5) to provide an integrated assessment of
    the state of AI tools for Indian languages and the contribution of the proposed framework."""))

    story.append(H2('6.1  Key Findings from Comparative Analysis'))
    story.append(P("""<b>Language Coverage:</b> Language coverage has improved dramatically with
    recent specialized models. Krutrim LLM (2025) supports 1000+ regional languages including
    dialects, while IndicLLMSuite covers all 22 official languages with 251B training tokens.
    In contrast, mBERT (2019) supported only 3-4 Indian languages with limited script coverage,
    illustrating the remarkable progress over six years of dedicated research [3], [21]."""))
    story.append(P("""<b>Performance Hierarchy:</b> A consistent performance hierarchy emerges:
    Indian-focused specialized models (Krutrim, MuRIL, IndicBERT) outperform generic multilingual
    models (mBERT, general BLOOM) on Indian language tasks, while the latest general-purpose
    frontier models (GPT-4o, PaLM-2) are increasingly competitive for high-resource languages
    due to their scale and RLHF alignment [7], [9], [21]."""))
    story.append(P("""<b>High-Resource vs. Low-Resource Gap:</b> The performance gap between
    high-resource and low-resource Indian languages remains the most persistent challenge.
    Accuracy differences of 15-30% across NLP tasks and WER differences of 30-50% in ASR
    are attributable to data scarcity, morphological complexity, and script diversity [9], [11], [23].
    Despite the massive datasets now available (IndicLLMSuite: 251B tokens), coverage remains
    uneven across the 22 official languages."""))
    story.append(P("""<b>Cultural Bias:</b> Cultural and social biases — particularly disability-related
    bias — appear most consistently across models evaluated on IndiCASA [20]. Caste-based, gender,
    and socioeconomic biases are also present but less consistently measured. This represents a
    serious ethical concern for deploying AI systems in high-stakes Indian contexts including
    healthcare, education, and governance."""))
    story.append(P("""<b>Tokenization Impact:</b> Specialized tokenizers like SUTRA consistently
    outperform standard BPE approaches for Indian languages, achieving better Normalized Sequence
    Length (NSL) by respecting Indic script morphology [22]. This finding underscores that
    architectural choices upstream of the model itself — particularly tokenization — have
    significant impact on downstream performance."""))

    story.append(H2('6.2  Comparison of Framework with Existing Approaches'))
    story.append(P("""The proposed pivot-based framework compares favorably with existing multilingual
    approaches on three key dimensions:"""))
    story.append(P("""<b>Scalability:</b> The O(n) complexity of the pivot approach enables support for
    all 22 Indian languages with only 44 translation models (22 x 2: each to/from English),
    compared to up to 484 for pairwise approaches. This makes the framework practically deployable
    with existing technology (IndicTrans2 covers all 22 x English pairs)."""))
    story.append(P("""<b>Semantic Consistency:</b> The LSC-based semantic consistency check (Eq. 2)
    provides a quantitative, automated measure of meaning preservation — a capability absent from
    most existing multilingual pipeline approaches. Mean LSC scores of 0.83-0.92 across tested
    language pairs confirm that semantic fidelity is maintained through the pivot process."""))
    story.append(P("""<b>Modularity and Upgradeability:</b> The clean separation between ASR,
    translation, reasoning, and TTS modules enables independent upgrades. As better models
    become available (e.g., replacing the LLM-simulated translation with actual IndicTrans2 inference),
    the system improves without requiring architectural changes."""))

    story.append(H2('6.3  Limitations of This Work'))
    story.append(P("""<b>Translation Simulation:</b> The prototype uses LLM-simulated translation rather
    than actual IndicTrans2 inference due to computational and deployment constraints. Real IndicTrans2
    would likely achieve higher BLEU scores and potentially different LSC profiles, particularly for
    low-resource languages where LLM translation quality is less reliable."""))
    story.append(P("""<b>Benchmark Scale:</b> The LSC evaluation uses a limited test set (10 queries
    per language pair) and relies on LLM-based semantic similarity scoring rather than human evaluation
    or embedding-based cosine similarity. Larger-scale evaluation with diverse query types and human
    judges would provide more robust performance estimates."""))
    story.append(P("""<b>Cultural Appropriateness:</b> The prototype does not currently implement
    culture-specific prompt engineering or culturally-aware response generation. Addressing cultural
    bias in the reasoning module remains an important direction for future work."""))
    story.append(PageBreak())

def chapter7(story):
    story.append(H1('Chapter 7: Conclusion'))
    story.append(HR())
    story.append(P("""This dissertation has presented a comprehensive study of AI tools for Indian
    regional languages, integrating a systematic comparative analysis with an original theoretical
    framework and its practical prototype implementation."""))
    story.append(P("""The comparative analysis, drawing on 30 research papers and evaluating models
    including MuRIL, IndicBERT, Krutrim LLM, GPT-4, BLOOM, and LLaMA across key NLP and speech
    tasks, reveals a field in rapid transition. The last five years have seen transformative progress:
    from mBERT's limited 3-4 language coverage to Krutrim's 1000+ language support, from
    sparse ASR models to BHASAANUVAAD's 44,000-hour multilingual speech translation dataset,
    and from narrow task-specific models to general-purpose LLMs increasingly competitive on
    Indian language benchmarks."""))
    story.append(P("""The proposed pivot-based multilingual AI framework makes several original
    contributions. Formally, it provides the unified system equation
    OL = RL(DP-to-L(GP(TL-to-P(NL(IL)), C))) as a rigorous mathematical characterization of the
    complete multimodal multilingual pipeline. The semantic consistency constraint (Eq. 2)
    provides a theoretically grounded, computationally tractable measure of meaning preservation
    through successive translation steps. The error propagation bound (Eq. 3) enables systematic
    reasoning about cumulative pipeline errors and guides strategies for error mitigation. The
    scalability analysis demonstrates that O(n) pivot complexity makes the framework practically
    feasible for India's full complement of 22 official languages."""))
    story.append(P("""The Streamlit prototype validates the practical viability of the framework,
    achieving LSC scores of 0.83-0.92 across tested language pairs and successfully handling
    all 22 Indian languages with both text and speech input/output. The modular eight-stage
    architecture enables transparent visualization of each processing step, making the system
    interpretable and debuggable — important qualities for deployment in high-stakes contexts."""))
    story.append(P("""Despite this progress, significant challenges remain. The performance gap between
    high-resource and low-resource languages persists at 15-30% across tasks. Cultural and social
    biases — particularly related to disability, caste, gender, and socioeconomic status — remain
    embedded in current AI systems. Real-world deployment is constrained by computational requirements,
    usability barriers, and limited cultural appropriateness. These challenges are not merely
    technical — they reflect structural inequities in data availability, research investment,
    and institutional prioritization that require sustained, coordinated effort to address."""))
    story.append(P("""The path forward for inclusive, equitable AI for India requires simultaneous
    progress on multiple fronts: expanding high-quality datasets for low-resource languages,
    developing culturally grounded evaluation frameworks, building computationally efficient
    models suitable for deployment on low-power devices, and establishing governance frameworks
    that ensure AI benefits are equitably distributed across India's extraordinarily diverse
    linguistic landscape."""))
    story.append(PageBreak())

def chapter8(story):
    story.append(H1('Chapter 8: Future Directions'))
    story.append(HR())
    story.append(P("""Building on the findings and contributions of this dissertation, the following
    priority directions are identified for future research:"""))

    story.append(H2('8.1  Advancing Linguistic Resources and Model Design'))
    for item in [
        "<b>Low-Resource Language Datasets:</b> Systematic collection and curation of high-quality text and speech datasets for severely low-resource languages including Santali, Bodo, Dogri, Konkani, and Manipuri. Community-driven data collection initiatives following the IndicVoices-R model [14] offer a scalable pathway.",
        "<b>Morphology-Aware Architectures:</b> Development of tokenizers and neural architectures that explicitly model the rich morphological structure of Dravidian and agglutinative Indic languages, building on the SUTRA tokenizer findings [22].",
        "<b>Unified Evaluation Benchmark:</b> Creation of a comprehensive evaluation benchmark covering all 22 official Indian languages across core NLP tasks (classification, translation, QA, summarization, generation), addressing the fragmentation identified in Chapter 2.",
        "<b>Domain-Specific Models:</b> Development of specialized models for high-impact domains — healthcare, legal, agricultural, and educational AI — where general-purpose models fail due to domain vocabulary gaps [6], [12].",
    ]:
        story.append(bullet(item))

    story.append(H2('8.2  Cultural, Ethical, and Inclusive AI Development'))
    for item in [
        "<b>Bias Detection and Mitigation:</b> Robust, language-specific bias detection frameworks covering the five demographic axes identified by IndiCASA [20]: caste, gender, religion, disability, and socioeconomic status, with active mitigation strategies.",
        "<b>Culturally Grounded Evaluation:</b> Development of culturally grounded evaluation methods that assess not just linguistic accuracy but contextual appropriateness, cultural sensitivity, and pragmatic correctness in Indian communication contexts.",
        "<b>Indigenous Language Preservation:</b> Extension of AI support to endangered and indigenous languages outside the 22 official languages, preserving India's extraordinary linguistic heritage.",
    ]:
        story.append(bullet(item))

    story.append(H2('8.3  Scalable, Efficient, and Multimodal Systems'))
    for item in [
        "<b>Actual IndicTrans2 Integration:</b> Replacing the LLM-simulated translation in the prototype with actual IndicTrans2 inference [15] to achieve production-quality translation quality, particularly for low-resource language pairs.",
        "<b>Edge Deployment:</b> Development of quantized, distilled model variants suitable for deployment on edge devices (mobile phones, tablets) in low-bandwidth environments, leveraging architectures like Paramanu [10].",
        "<b>Multimodal Extension:</b> Extension of the pivot-based framework to incorporate visual modalities (image understanding, document processing, sign language), enabling truly multimodal AI assistance for India's diverse user needs.",
        "<b>6G Network Integration:</b> Exploration of ultra-low latency edge intelligence architectures enabled by emerging 6G network technologies [13], [14] to support real-time multilingual conversational AI at scale.",
        "<b>Pivot Language Generalization:</b> Investigation of alternative or multiple pivot languages (e.g., Hindi as a supplementary pivot for Hindi-belt languages) to reduce translation error for language pairs that are closer to Hindi than to English.",
    ]:
        story.append(bullet(item))

    story.append(H2('8.4  Policy and Infrastructure Recommendations'))
    for item in [
        "Government and academic investment in systematic, long-term data collection for low-resource Indian languages through initiatives like Bhashini [7] with explicitly broadened scope beyond the current model.",
        "Standardization of evaluation protocols and benchmark datasets to enable meaningful cross-model comparison and track progress over time.",
        "Establishment of culturally diverse AI development teams that include speakers of all 22 official languages in the design, evaluation, and governance of AI systems.",
        "Open-source data sharing mandates for publicly funded AI research on Indian languages to accelerate community progress and prevent duplication of effort.",
    ]:
        story.append(bullet(item))
    story.append(PageBreak())

def references(story):
    story.append(H1('References / Bibliography'))
    story.append(HR())
    refs = [
        "[1] S. Bengesi, H. El-Sayed, M. K. Sarker, Y. Houkpati, J. Irungu, and T. Oladunni, \"Advancements in Generative AI: A Comprehensive Review of GANs, GPT, Autoencoders, Diffusion Model, and Transformers,\" IEEE Access, vol. 12, pp. 69812-69837, 2024.",
        "[2] K. Jain, A. Deshpande, K. Shridhar, F. Laumann, and A. Dash, \"Indic-Transformers: An Analysis of Transformer Language Models for Indian Languages,\" arXiv:2011.02323 [cs], Nov. 2020.",
        "[3] S. Khanuja et al., \"MuRIL: Multilingual Representations for Indian Languages,\" arXiv:2103.10730 [cs], Apr. 2021.",
        "[4] F. Feng, Y. Yang, D. Cer, N. Arivazhagan, and W. Wang, \"Language-Agnostic BERT Sentence Embedding,\" in Proc. 60th Annual Meeting of the ACL (Vol. 1: Long Papers), Dublin, Ireland, pp. 878-891, ACL, May 2022.",
        "[5] B. Roark, L. Wolf-Sonkin, C. Kirov, S. J. Mielke, C. Johny, I. Demirsahin, and K. Hall, \"Processing South Asian Languages Written in the Latin Script: The Dakshina Dataset,\" 2020.",
        "[6] M. S. U. R. Khan et al., \"IndicLLMSuite: A Blueprint for Creating Pre-training and Fine-Tuning Datasets for Indian Languages,\" in Proc. 62nd Annual Meeting of the ACL (Long Papers), Bangkok, Thailand, 2024, pp. 15831-15879.",
        "[7] H. Singh, N. Gupta, S. Bharadwaj, D. Tewari, and P. Talukdar, \"IndicGenBench: A Multilingual Benchmark to Evaluate Generation Capabilities of LLMs on Indic Languages,\" arXiv:2404.16816 [cs], Aug. 2024.",
        "[8] G. K. Kumar, S. Praveen, P. Kumar, M. M. Khapra, and K. Nandakumar, \"Towards Building Text-To-Speech Systems for the Next Billion Users,\" arXiv:2211.09536 [cs], Feb. 2023.",
        "[9] S. Verma, V. Kumar, R. Murthy, and J. Sen, \"MILU: A Multi-task Indic Language Understanding Benchmark,\" arXiv:2411.02538 [cs], Feb. 2025.",
        "[10] M. Niyogi, Gyan AI Research, and A. Bhattacharya, \"Paramanu: A Family of Novel Efficient Generative Foundation Language Models for Indian Languages,\" 2024.",
        "[11] A. Joshi and S. Rawat, \"Evaluation of Large Language Models Using an Indian Language LGBTI+ Lexicon,\" AI Ethics Journal, vol. 4, no. 1, Nov. 2023.",
        "[12] S. P. Parida et al., \"Building pre-train LLM Dataset for the INDIC Languages: A Case Study on Hindi,\" arXiv:2407.09855 [cs], Jul. 2024.",
        "[13] A. Bazzi et al., \"Upper mid-band spectrum for 6G: Vision, opportunity and challenges,\" IEEE Communications Magazine, 2025.",
        "[14] A. Sankar et al., \"IndicVoices-R: Unlocking a Massive Multilingual Multi-speaker Speech Corpus for Scaling Indian TTS,\" arXiv:2409.05356 [cs], Oct. 2024.",
        "[15] J. Gala et al., \"IndicTrans2: Towards high-quality and accessible machine translation models for all 22 scheduled Indian languages,\" arXiv:2305.16307, 2023.",
        "[16] Y. Madhani, M. M. Khapra, and A. Kunchukuttan, \"Bhasha-Abhijnaanam: Native-script and Romanized Language Identification for 22 Indic Languages,\" arXiv:2305.15814 [cs], Oct. 2023.",
        "[17] I. Watts et al., \"PARIKSHA: A Large-Scale Investigation of Human-LLM Evaluator Agreement on Multilingual and Multi-Cultural Data,\" arXiv:2406.15053 [cs], Oct. 2024.",
        "[18] S. KJ et al., \"IndicMMLU-Pro: Benchmarking Indic Large Language Models on Multi-Task Language Understanding,\" arXiv:2501.15747 [cs], Jan. 2025.",
        "[19] M.-K. Mak and T. Luo, \"A framework for evaluating cultural bias and historical misconceptions in LLMs outputs,\" BenchCouncil Transactions on Benchmarks, Standards and Evaluations, vol. 5, no. 3, p. 100235, Sep. 2025.",
        "[20] S. G. S et al., \"IndiCASA: A Dataset and Bias Evaluation Framework in LLMs Using Contrastive Embedding Similarity in the Indian Context,\" arXiv:2510.02742 [cs], Oct. 2025.",
        "[21] A. Kallappa et al., \"Krutrim LLM: Multilingual Foundational Model for over a Billion People,\" arXiv:2502.09642 [cs], Feb. 2025.",
        "[22] S. Tamang and D. J. Bora, \"Evaluating Tokenizer Performance of Large Language Models Across Official Indian Languages,\" arXiv:2411.12240 [cs], Nov. 2024.",
        "[23] A. Vaidya, T. Prabhakar, D. George, and S. Shah, \"Analysis of Indic Language Capabilities in LLMs,\" arXiv:2501.13912 [cs], Jan. 2025.",
        "[24] P. Jain and A. Bhowmick, \"Comparative performance analysis of end-to-end ASR models on Indo-Aryan and Dravidian languages within India's linguistic landscape,\" EURASIP Journal on Audio, Speech, and Music Processing, vol. 2025, no. 1, p. 10, Feb. 2025.",
        "[25] A. Sankar et al., \"RASMALAI: Resources for Adaptive Speech Modeling in Indian Languages with Accents and Intonations,\" arXiv:2505.18609 [cs], May 2025.",
        "[26] A. Sankar et al., \"Towards Building Large Scale Datasets and State-of-the-Art Automatic Speech Translation Systems for 14 Indian Languages,\" arXiv:2411.04699 [cs], May 2025.",
        "[27] S. Shah et al., \"IndicST: Indian Multilingual Translation Corpus for Evaluating Speech Large Language Models,\" 2024.",
        "[28] B. Shankar, P. Jyothi, and P. Bhattacharyya, \"End-to-End Speech Translation: A Survey,\" 2024.",
        "[29] V. Bhat and P. Bhattacharyya, \"Survey: Automatic Speech Recognition for Indian Languages,\" 2024.",
        "[30] S. R. Sinha et al., \"Eka-Eval: A Comprehensive Evaluation Framework for Large Language Models in Indian Languages,\" arXiv:2507.01853 [cs], Jul. 2025.",
        "[31] T. Rahman and M. Haziq, \"A Theoretical Framework for Pivot-Based Multilingual AI Response Generation in Indian Languages,\" in 2026 Second International Conference on Emerging Computational Intelligence (ICECI-2026), IEEE, 2026.",
        "[32] G. Lample and A. Conneau, \"Cross-lingual language model pretraining,\" arXiv:1901.07291, 2019.",
        "[33] A. Conneau et al., \"Unsupervised cross-lingual representation learning at scale,\" in Proc. 58th Annual Meeting of the ACL, pp. 8440-8451, 2020.",
        "[34] H. Wu and H. Wang, \"Pivot language approach for phrase-based statistical machine translation,\" in Proc. 45th Annual Meeting of the ACL, Prague, pp. 856-863, Jun. 2007.",
        "[35] Y. Kim et al., \"Pivot-based transfer learning for neural machine translation between non-English languages,\" in Proc. EMNLP-IJCNLP 2019, Hong Kong, pp. 866-876, Nov. 2019.",
    ]
    for ref in refs:
        story.append(P(ref, 'ref'))
    story.append(PageBreak())

def appendix(story):
    story.append(H1('Appendix'))
    story.append(HR())

    story.append(H2('Appendix A: List of 22 Official Languages of India'))
    story.append(P("""The following languages are recognized in the Eighth Schedule of the
    Indian Constitution:"""))

    data_app = [
        ['No.', 'Language', 'Language Family', 'Primary Script', 'Approx. Speakers (millions)'],
        ['1', 'Hindi', 'Indo-Aryan', 'Devanagari', '550+'],
        ['2', 'Bengali', 'Indo-Aryan', 'Bengali', '265+'],
        ['3', 'Telugu', 'Dravidian', 'Telugu', '95+'],
        ['4', 'Marathi', 'Indo-Aryan', 'Devanagari', '95+'],
        ['5', 'Tamil', 'Dravidian', 'Tamil', '80+'],
        ['6', 'Urdu', 'Indo-Aryan', 'Perso-Arabic', '70+'],
        ['7', 'Gujarati', 'Indo-Aryan', 'Gujarati', '60+'],
        ['8', 'Kannada', 'Dravidian', 'Kannada', '55+'],
        ['9', 'Malayalam', 'Dravidian', 'Malayalam', '38+'],
        ['10', 'Odia', 'Indo-Aryan', 'Odia', '37+'],
        ['11', 'Punjabi', 'Indo-Aryan', 'Gurmukhi', '33+'],
        ['12', 'Assamese', 'Indo-Aryan', 'Assamese', '15+'],
        ['13', 'Maithili', 'Indo-Aryan', 'Devanagari/Tirhuta', '13+'],
        ['14', 'Sanskrit', 'Indo-Aryan', 'Devanagari', '0.025 (liturgical)'],
        ['15', 'Santali', 'Austroasiatic', 'Ol Chiki', '7+'],
        ['16', 'Kashmiri', 'Indo-Aryan', 'Perso-Arabic/Devanagari', '7+'],
        ['17', 'Nepali', 'Indo-Aryan', 'Devanagari', '2.9+'],
        ['18', 'Sindhi', 'Indo-Aryan', 'Perso-Arabic/Devanagari', '2.7+'],
        ['19', 'Konkani', 'Indo-Aryan', 'Devanagari/Kannada/Malayalam', '2.5+'],
        ['20', 'Dogri', 'Indo-Aryan', 'Devanagari', '2.3+'],
        ['21', 'Manipuri (Meitei)', 'Sino-Tibetan', 'Meitei Mayek/Bengali', '1.8+'],
        ['22', 'Bodo', 'Sino-Tibetan', 'Devanagari/Assamese', '1.4+'],
    ]
    t = make_table(data_app, col_widths=[0.8*cm, 2.5*cm, 2.8*cm, 4.2*cm, 3.5*cm])
    story.append(t)
    story.append(P('<b>Table A.1:</b> List of 22 Official Languages of India (Eighth Schedule)', 'caption'))

    story.append(SP(15))
    story.append(H2('Appendix B: Streamlit Application Configuration'))
    story.append(P("""The prototype application requires the following environment setup:"""))
    story.append(P("""<b>Dependencies:</b> streamlit, speechrecognition, pydub, gtts, requests,
    python-dotenv, openai (for OpenRouter compatibility)""", 'body_ind'))
    story.append(P("""<b>Environment Variables:</b> OPENROUTER_API_KEY must be set in a .env file
    in the application root directory.""", 'body_ind'))
    story.append(P("""<b>Model:</b> meta-llama/llama-3.3-70b-instruct via OpenRouter API
    (https://openrouter.ai/api/v1/chat/completions)""", 'body_ind'))
    story.append(P("""<b>Launch command:</b> streamlit run app.py""", 'body_ind'))

    story.append(SP(15))
    story.append(H2('Appendix C: Acknowledgment of Data Sources'))
    story.append(P("""This research report is based on the analysis of 30 research papers covering
    various aspects of AI tools for Indian regional languages. All papers are properly cited in
    the References section. Key data sources include:"""))
    for src in [
        "Academic papers from major NLP conferences (ACL, EMNLP, NAACL, INTERSPEECH)",
        "ArXiv preprints from leading research institutions including AI4Bharat, IIT Madras, Google Research",
        "Technical reports from AI4Bharat, IIT Madras, Google Research, and Ola AI (Krutrim)",
        "Published benchmarks and evaluation results from MILU, IndicGenBench, IndicMMLU-Pro, and Eka-Eval",
        "Open-source model documentation and technical papers from HuggingFace, GitHub, and institutional repositories",
        "Conference proceedings from ICECI-2026 (IEEE) including the co-authored paper [31]",
    ]:
        story.append(bullet(src))


# ══════════════════════════════════════════════════════════════════════════════
# MAIN BUILD
# ══════════════════════════════════════════════════════════════════════════════
def build():
    doc = SimpleDocTemplate(
        OUT,
        pagesize=A4,
        leftMargin=2.5*cm, rightMargin=2.5*cm,
        topMargin=2.5*cm, bottomMargin=2.5*cm,
        title="Development and Analysis of Multimodal AI Tools for Indian Context",
        author="Tuba Rahman",
        subject="BSc Hons. with Research Dissertation, AMU 2024",
    )

    story = []
    cover_page(story)
    certification_page(story)
    acknowledgement_page(story)
    abstract_page(story)
    toc_page(story)
    lof_page(story)
    chapter1(story)
    chapter2(story)
    chapter3(story)
    chapter4(story)
    chapter5(story)
    chapter6(story)
    chapter7(story)
    chapter8(story)
    references(story)
    appendix(story)

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f"PDF written to {OUT}")

if __name__ == "__main__":
    build()