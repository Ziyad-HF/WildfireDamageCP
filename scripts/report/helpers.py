import copy, sys
from lxml import etree
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION
from pptx.oxml.ns import qn

TPL, OUT, IMG = sys.argv[1], sys.argv[2], sys.argv[3]
GREEN, GOLD, MINT, GREY, RED, LGREEN = (RGBColor.from_string(c) for c in ("275D37", "F1CC00", "EDF5F0", "8B9088", "C00000", "4EA72E"))
BODY, WHITE, DGREY = RGBColor.from_string("4A4A48"), RGBColor(255, 255, 255), RGBColor.from_string("505050")
FONT = "Roboto"

prs = Presentation(TPL)
LAY = prs.slide_layouts[7]  # Content 5: green band, gold title


# ---------- helpers ----------
def txt(shapes, x, y, w, h, text, size=16, bold=False, color=BODY, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, italic=False):
    tb = shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05); tf.margin_top = tf.margin_bottom = Inches(0.02)
    lines = text if isinstance(text, list) else [text]
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        segs = ln if isinstance(ln, list) else [(ln, bold, color, size)]
        for s in segs:
            t, b, c, sz = s
            r = p.add_run(); r.text = t; f = r.font
            f.name = FONT; f.size = Pt(sz); f.bold = b; f.italic = italic; f.color.rgb = c
    return tb


def box(shapes, x, y, w, h, fill=MINT, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, dash=False, lw=1.5, adj=0.12):
    s = shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = adj
    if fill is None: s.fill.background()
    else: s.fill.solid(); s.fill.fore_color.rgb = fill
    if line is None: s.line.fill.background()
    else:
        s.line.color.rgb = line; s.line.width = Pt(lw)
        if dash:
            from pptx.enum.dml import MSO_LINE
            s.line.dash_style = MSO_LINE.DASH
    s.shadow.inherit = False
    s.text_frame.text = ""
    return s


def label(shape, text, size=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER):
    tf = shape.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(0.06); tf.margin_top = tf.margin_bottom = Inches(0.02)
    lines = text if isinstance(text, list) else [text]
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.alignment = align
        segs = ln if isinstance(ln, list) else [(ln, bold, color, size)]
        for t, b, c, sz in segs:
            r = p.add_run(); r.text = t; r.font.name = FONT; r.font.size = Pt(sz); r.font.bold = b; r.font.color.rgb = c


def chip(shapes, x, y, w, h, text, fill=GOLD, color=GREEN, size=12, line=None, dash=False):
    s = box(shapes, x, y, w, h, fill=fill, line=line, dash=dash, adj=0.5)
    label(s, text, size=size, color=color); return s


def arrow(shapes, x, y, w=0.45, h=0.38, color=GREEN):
    s = shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid(); s.fill.fore_color.rgb = color; s.line.fill.background(); s.shadow.inherit = False
    return s


def pic(shapes, path, x, y, w=None, h=None):
    return shapes.add_picture(f"{IMG}/{path}", Inches(x), Inches(y), Inches(w) if w else None, Inches(h) if h else None)


def kpi(shapes, x, y, w, h, num, lab, key=False):
    b = box(shapes, x, y, w, h, fill=GREEN if key else MINT)
    label(b, [[(num, True, GOLD if key else GREEN, 30)], [(lab, False, WHITE if key else DGREY, 14)]])
    return b


def card(shapes, x, y, w, h, title, line, accent=GREEN, tsize=17, lsize=14):
    b = box(shapes, x, y, w, h, fill=MINT, adj=0.08)
    a = box(shapes, x, y + 0.08, 0.09, h - 0.16, fill=accent, shape=MSO_SHAPE.RECTANGLE)
    t = txt(shapes, x + 0.2, y + 0.08, w - 0.3, h - 0.16, [[(title, True, GREEN, tsize)], [(line, False, BODY, lsize)]], anchor=MSO_ANCHOR.MIDDLE)
    return [b, a, t]


def group(slide, shapes_list):
    """Move existing shapes into one group shape (one animation target)."""
    return slide.shapes.add_group_shape(shapes=list(shapes_list))


def new_slide(title, notes):
    s = prs.slides.add_slide(LAY)
    for ph in list(s.placeholders):
        if ph.placeholder_format.idx == 0:
            ph.text_frame.text = title
            for r in ph.text_frame.paragraphs[0].runs:
                r.font.name = FONT; r.font.size = Pt(36); r.font.bold = True; r.font.color.rgb = GOLD
        elif ph.placeholder_format.idx == 10:
            ph._element.getparent().remove(ph._element)
    s.notes_slide.notes_text_frame.text = notes
    return s


def animate(slide, clicks):
    """clicks: list of (effect, [shape,...]); effect 'fade' or 'wipe'. One click per entry."""
    cid = [3]
    def nid():
        cid[0] += 1; return cid[0]
    pars = []
    for eff, shapes_ in clicks:
        inner = []
        for k, shp in enumerate(shapes_):
            sid = shp.shape_id
            pid, sub, filt = ("10", "0", "fade") if eff == "fade" else ("22", "8", "wipe(left)")
            node = "clickEffect" if k == 0 else "withEffect"
            inner.append(f'''<p:par><p:cTn id="{nid()}" presetID="{pid}" presetClass="entr" presetSubtype="{sub}" fill="hold" nodeType="{node}"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>
<p:set><p:cBhvr><p:cTn id="{nid()}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn><p:tgtEl><p:spTgt spid="{sid}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr><p:to><p:strVal val="visible"/></p:to></p:set>
<p:animEffect transition="in" filter="{filt}"><p:cBhvr><p:cTn id="{nid()}" dur="400"/><p:tgtEl><p:spTgt spid="{sid}"/></p:tgtEl></p:cBhvr></p:animEffect></p:childTnLst></p:cTn></p:par>''')
        pars.append(f'''<p:par><p:cTn id="{nid()}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/></p:stCondLst><p:childTnLst><p:par><p:cTn id="{nid()}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>{"".join(inner)}</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>''')
    xml = f'''<p:timing xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst><p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>{"".join(pars)}</p:childTnLst></p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst><p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq></p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>'''
    el = etree.fromstring(xml)
    sld = slide._element
    old = sld.find(qn("p:timing"))
    old = sld.find(qn("p:timing"))
    if old is not None: sld.remove(old)
    ext = sld.find(qn("p:extLst"))
    if ext is not None: ext.addprevious(el)
    else: sld.append(el)


