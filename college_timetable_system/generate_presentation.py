from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.dml import MSO_THEME_COLOR

OUT = "College_Timetable_System_Presentation.pptx"

NAVY = RGBColor(20, 32, 51)
INK = RGBColor(35, 46, 61)
MUTED = RGBColor(103, 116, 132)
CORAL = RGBColor(237, 105, 83)
MINT = RGBColor(83, 184, 162)
GOLD = RGBColor(244, 190, 79)
PALE = RGBColor(244, 247, 246)
WHITE = RGBColor(255, 255, 255)
LINE = RGBColor(220, 228, 229)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank = prs.slide_layouts[6]


def add_bg(slide, color=WHITE):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    slide.shapes._spTree.remove(shape._element)
    slide.shapes._spTree.insert(2, shape._element)


def add_text(slide, text, x, y, w, h, size=18, color=INK, bold=False, font="Aptos", align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.vertical_anchor = valign
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return box


def add_rich_lines(slide, lines, x, y, w, h, size=17, color=INK, bullet=False):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.level = 0
        p.font.name = "Aptos"
        p.font.size = Pt(size)
        p.font.color.rgb = color
        p.space_after = Pt(10)
        if bullet:
            p.text = "• " + line
    return box


def rect(slide, x, y, w, h, fill, radius=False, line=None):
    kind = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    shape = slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line
    return shape


def circle(slide, x, y, d, fill):
    shape = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(d), Inches(d))
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.fill.background()
    return shape


def line(slide, x1, y1, x2, y2, color=LINE, width=1.5):
    shape = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    shape.line.color.rgb = color
    shape.line.width = Pt(width)
    return shape


def footer(slide, number):
    add_text(slide, "COLLEGE TIMETABLE SYSTEM", 0.55, 7.08, 4.0, 0.18, 8, MUTED, True)
    add_text(slide, f"{number:02d}", 12.25, 7.03, 0.5, 0.2, 9, MUTED, True, align=PP_ALIGN.RIGHT)


def title_block(slide, eyebrow, title, subtitle=None, number=None):
    add_text(slide, eyebrow.upper(), 0.65, 0.48, 5.5, 0.22, 10, CORAL, True)
    add_text(slide, title, 0.65, 0.82, 11.5, 0.7, 28, NAVY, True, font="Aptos Display")
    if subtitle:
        add_text(slide, subtitle, 0.68, 1.58, 10.7, 0.42, 13, MUTED)
    if number:
        footer(slide, number)


def metric(slide, x, y, value, label, accent):
    rect(slide, x, y, 2.3, 1.05, WHITE, True, LINE)
    rect(slide, x, y, 0.08, 1.05, accent)
    add_text(slide, value, x + 0.25, y + 0.18, 1.8, 0.35, 22, NAVY, True, font="Aptos Display")
    add_text(slide, label, x + 0.25, y + 0.63, 1.8, 0.2, 10, MUTED, True)

# 1. Cover
slide = prs.slides.add_slide(blank)
add_bg(slide, NAVY)
rect(slide, 8.65, -0.35, 5.1, 8.3, CORAL)
rect(slide, 9.2, 0.55, 3.85, 5.95, MINT, True)
for i in range(5):
    y = 1.15 + i * 0.9
    rect(slide, 9.62, y, 3.05, 0.52, WHITE, True)
    add_text(slide, ["MON  09:00  Programming", "TUE  10:00  Data Structures", "WED  11:00  Networks", "THU  09:00  Lab Session", "FRI  14:00  Project Work"][i], 9.82, y + 0.14, 2.65, 0.2, 9, NAVY, True)
circle(slide, 11.85, 5.73, 0.62, GOLD)
add_text(slide, "COLLEGE TIMETABLE SYSTEM", 0.75, 1.1, 5.7, 0.3, 12, MINT, True)
add_text(slide, "From timetable chaos\nto a clear week.", 0.72, 1.65, 7.2, 1.55, 38, WHITE, True, font="Aptos Display")
add_text(slide, "A role-based web platform for managing colleges, resources, and published schedules.", 0.78, 3.5, 6.6, 0.65, 17, RGBColor(215, 225, 228))
rect(slide, 0.78, 5.38, 2.15, 0.55, CORAL, True)
add_text(slide, "PROJECT PRESENTATION", 1.02, 5.56, 1.7, 0.17, 9, WHITE, True, align=PP_ALIGN.CENTER)
add_text(slide, "Built with Flask, SQLite, JavaScript, and an AI-assisted scheduling workflow", 0.8, 6.57, 6.6, 0.25, 10, RGBColor(173, 190, 195))

# 2. Why
slide = prs.slides.add_slide(blank)
add_bg(slide, PALE)
title_block(slide, "01 / The problem", "Scheduling is a coordination problem", "Every timetable is a shared puzzle: people, rooms, sections, and time all compete for the same space.", 2)
metric(slide, 0.75, 2.45, "05", "core data domains", CORAL)
metric(slide, 3.3, 2.45, "02", "admin roles", MINT)
metric(slide, 5.85, 2.45, "01", "published view", GOLD)
rect(slide, 0.75, 4.05, 11.8, 1.9, NAVY, True)
add_text(slide, "The old workflow", 1.08, 4.35, 2.0, 0.28, 13, MINT, True)
add_rich_lines(slide, ["Manual edits create conflicts", "Updates are hard to communicate", "Students and faculty need different views"], 1.08, 4.78, 5.2, 0.95, 15, WHITE, True)
line(slide, 6.75, 4.35, 6.75, 5.62, RGBColor(73, 90, 105), 1)
add_text(slide, "Design goal", 7.25, 4.35, 2.0, 0.28, 13, GOLD, True)
add_text(slide, "Make the schedule a dependable\nshared source of truth.", 7.25, 4.82, 4.5, 0.75, 22, WHITE, True, font="Aptos Display")

# 3. Solution
slide = prs.slides.add_slide(blank)
add_bg(slide, WHITE)
title_block(slide, "02 / The solution", "One system, three simple entry points", "The landing page routes each audience to the right experience without adding friction.", 3)
steps = [("A", "College Admin", "Manage one college's data and timetable", CORAL), ("S", "Super Admin", "Manage colleges, admins, and assignments", MINT), ("V", "View timetable", "Browse as a student or faculty member", GOLD)]
for i, (letter, heading, body, accent) in enumerate(steps):
    x = 0.85 + i * 4.05
    rect(slide, x, 2.55, 3.45, 2.3, PALE, True, LINE)
    circle(slide, x + 0.3, 2.88, 0.62, accent)
    add_text(slide, letter, x + 0.3, 3.02, 0.62, 0.18, 17, NAVY, True, align=PP_ALIGN.CENTER)
    add_text(slide, heading, x + 1.12, 2.94, 2.0, 0.25, 17, NAVY, True)
    add_text(slide, body, x + 0.32, 3.8, 2.8, 0.6, 13, MUTED)
    add_text(slide, "EXPLORE  →", x + 0.32, 4.45, 1.4, 0.18, 9, accent, True)
add_text(slide, "The result: less ambiguity at the front door, and a cleaner flow into the data behind it.", 0.9, 5.65, 10.9, 0.35, 16, NAVY, True)

# 4. Public viewer
slide = prs.slides.add_slide(blank)
add_bg(slide, PALE)
title_block(slide, "03 / Public experience", "A timetable people can actually find", "The public view is optimized for scanning: select a college, choose a perspective, and read the week.", 4)
rect(slide, 0.82, 2.35, 7.25, 3.55, WHITE, True, LINE)
add_text(slide, "College Timetables", 1.15, 2.68, 2.5, 0.25, 14, NAVY, True)
add_text(slide, "Find your timetable", 1.15, 3.1, 4.0, 0.42, 24, NAVY, True, font="Aptos Display")
add_text(slide, "Browse the latest published schedule by department, section, or faculty.", 1.15, 3.65, 5.6, 0.3, 11, MUTED)
rect(slide, 1.15, 4.22, 2.35, 0.48, PALE, True, LINE)
add_text(slide, "College  ▾", 1.35, 4.38, 1.6, 0.16, 10, MUTED, True)
rect(slide, 3.75, 4.22, 1.25, 0.48, MINT, True)
add_text(slide, "Student", 3.94, 4.38, 0.85, 0.16, 10, NAVY, True, align=PP_ALIGN.CENTER)
rect(slide, 5.12, 4.22, 1.35, 0.48, PALE, True, LINE)
add_text(slide, "Faculty", 5.36, 4.38, 0.85, 0.16, 10, MUTED, True, align=PP_ALIGN.CENTER)
add_text(slide, "Published schedule", 1.15, 5.02, 2.5, 0.2, 12, NAVY, True)
for i, day in enumerate(["MON", "TUE", "WED", "THU", "FRI"]):
    x = 1.15 + i * 1.2
    rect(slide, x, 5.38, 1.02, 0.27, NAVY, True)
    add_text(slide, day, x, 5.46, 1.02, 0.12, 8, WHITE, True, align=PP_ALIGN.CENTER)
add_text(slide, "Student and faculty modes keep the same schedule readable for two different needs.", 8.65, 2.7, 3.3, 1.0, 22, NAVY, True, font="Aptos Display")
add_rich_lines(slide, ["College directory", "Department and section filters", "Faculty-specific lookup", "Printable schedule view"], 8.68, 4.2, 3.6, 1.2, 13, MUTED, True)

# 5. Admin console
slide = prs.slides.add_slide(blank)
add_bg(slide, WHITE)
title_block(slide, "04 / Admin experience", "A control room for the academic week", "The dashboard centralizes master data, access control, timetable preview, and schedule generation.", 5)
rect(slide, 0.75, 2.35, 3.0, 3.65, NAVY, True)
add_text(slide, "TIMETABLE AI", 1.05, 2.75, 2.2, 0.22, 13, MINT, True)
add_text(slide, "Admin Dashboard", 1.05, 3.05, 2.3, 0.24, 13, WHITE, True)
for i, label in enumerate(["Dashboard", "Master Management", "View Timetable"]):
    y = 3.72 + i * 0.48
    if i == 0: rect(slide, 0.95, y - 0.08, 2.4, 0.38, CORAL, True)
    add_text(slide, ["▦", "⚙", "▤"][i] + "  " + label, 1.12, y, 2.1, 0.17, 10, WHITE if i == 0 else RGBColor(177, 196, 202), True)
rect(slide, 4.15, 2.35, 8.3, 3.65, PALE, True, LINE)
for i, (val, label, accent) in enumerate([("ONLINE", "system status", MINT), ("-- / 100", "optimization score", GOLD), ("CLEAR", "conflict state", CORAL)]):
    x = 4.52 + i * 2.55
    rect(slide, x, 2.75, 2.25, 0.95, WHITE, True, LINE)
    add_text(slide, val, x + 0.18, 2.98, 1.85, 0.22, 14, accent, True)
    add_text(slide, label, x + 0.18, 3.38, 1.85, 0.16, 9, MUTED, True)
rect(slide, 4.52, 4.05, 7.2, 1.25, NAVY, True)
add_text(slide, "AI Timetable Engine", 4.82, 4.3, 2.8, 0.25, 16, WHITE, True)
add_text(slide, "Constraint-satisfaction scheduling across departments, faculty availability, and lab assets.", 4.82, 4.7, 5.3, 0.25, 11, RGBColor(200, 217, 220))
rect(slide, 10.38, 4.32, 1.05, 0.48, CORAL, True)
add_text(slide, "RUN", 10.38, 4.49, 1.05, 0.15, 9, WHITE, True, align=PP_ALIGN.CENTER)

# 6. Workflow
slide = prs.slides.add_slide(blank)
add_bg(slide, PALE)
title_block(slide, "05 / Core workflow", "From master data to a published week", "A predictable workflow turns many small records into one schedule people can trust.", 6)
workflow = [("01", "Configure", "Colleges, departments, sections, subjects, faculty, rooms", CORAL), ("02", "Generate", "Run the AI-assisted timetable engine", MINT), ("03", "Review", "Filter by college, department, section, or faculty", GOLD), ("04", "Publish", "Expose the latest schedule in the public viewer", CORAL)]
for i, (n, head, body, accent) in enumerate(workflow):
    x = 0.75 + i * 3.1
    circle(slide, x + 0.08, 2.6, 0.72, accent)
    add_text(slide, n, x + 0.08, 2.84, 0.72, 0.16, 12, NAVY, True, align=PP_ALIGN.CENTER)
    if i < 3: line(slide, x + 0.82, 2.96, x + 2.95, 2.96, LINE, 2)
    add_text(slide, head, x, 3.65, 2.4, 0.27, 18, NAVY, True, font="Aptos Display")
    add_text(slide, body, x, 4.12, 2.45, 0.85, 12, MUTED)
rect(slide, 0.78, 5.55, 11.7, 0.6, WHITE, True, LINE)
add_text(slide, "The system keeps the data model explicit, so changes remain understandable and traceable.", 1.1, 5.76, 10.9, 0.2, 14, NAVY, True, align=PP_ALIGN.CENTER)

# 7. Architecture
slide = prs.slides.add_slide(blank)
add_bg(slide, WHITE)
title_block(slide, "06 / Architecture", "Lightweight stack, clear boundaries", "The project is intentionally small enough to run locally and structured enough to deploy as a web service.", 7)
arch = [("Browser", "HTML / CSS / JavaScript", CORAL), ("Flask app", "Routes, sessions, APIs", MINT), ("SQLite", "Persistent timetable data", GOLD)]
for i, (head, body, accent) in enumerate(arch):
    x = 1.0 + i * 4.1
    rect(slide, x, 2.7, 3.05, 1.45, PALE, True, LINE)
    rect(slide, x, 2.7, 3.05, 0.15, accent)
    add_text(slide, head, x + 0.28, 3.1, 2.4, 0.28, 19, NAVY, True, font="Aptos Display")
    add_text(slide, body, x + 0.28, 3.62, 2.4, 0.22, 11, MUTED)
    if i < 2: line(slide, x + 3.1, 3.42, x + 3.95, 3.42, NAVY, 2)
add_text(slide, "Security and deployment", 1.0, 5.0, 3.3, 0.28, 18, NAVY, True, font="Aptos Display")
add_rich_lines(slide, ["Server-side sessions protect admin routes", "Role-aware access separates super and college administration", "Render / Gunicorn deployment path is documented", "SQLite is suited to demos and small deployments"], 1.0, 5.45, 10.8, 1.15, 13, MUTED, True)

# 8. Value
slide = prs.slides.add_slide(blank)
add_bg(slide, NAVY)
title_block(slide, "07 / Value delivered", "A calmer Monday morning", "The product is about more than generating a grid. It is about making schedule changes legible to everyone who depends on them.", 8)
# override title colors for dark bg
for shape in slide.shapes:
    if hasattr(shape, "text") and shape.text and ("THE VALUE" in shape.text or "A calmer" in shape.text or "The product" in shape.text):
        for p in shape.text_frame.paragraphs:
            for run in p.runs: run.font.color.rgb = WHITE if "A calmer" in shape.text else RGBColor(202, 219, 220)
items = [("01", "Fewer conflicts", "Centralized records make resource collisions visible earlier.", CORAL), ("02", "Faster discovery", "Students and faculty get a direct path to their schedule.", MINT), ("03", "Better ownership", "Admin roles make responsibility explicit across colleges.", GOLD)]
for i, (n, head, body, accent) in enumerate(items):
    y = 2.55 + i * 1.18
    circle(slide, 0.95, y, 0.63, accent)
    add_text(slide, n, 0.95, y + 0.22, 0.63, 0.14, 11, NAVY, True, align=PP_ALIGN.CENTER)
    add_text(slide, head, 1.9, y + 0.02, 2.5, 0.25, 18, WHITE, True, font="Aptos Display")
    add_text(slide, body, 1.9, y + 0.4, 8.8, 0.26, 12, RGBColor(197, 214, 218))

# 9. Close
slide = prs.slides.add_slide(blank)
add_bg(slide, PALE)
rect(slide, 0, 5.95, 13.333, 1.55, CORAL)
add_text(slide, "NEXT", 0.82, 0.82, 1.2, 0.22, 11, CORAL, True)
add_text(slide, "A working foundation for smarter scheduling", 0.78, 1.25, 9.8, 0.72, 30, NAVY, True, font="Aptos Display")
add_text(slide, "The next step is to validate schedules with real institutional constraints, then scale the data layer for long-term use.", 0.82, 2.2, 7.2, 0.58, 15, MUTED)
rect(slide, 0.82, 3.35, 3.0, 0.62, NAVY, True)
add_text(slide, "DEMO THE LIVE SITE  →", 1.08, 3.57, 2.45, 0.17, 10, WHITE, True, align=PP_ALIGN.CENTER)
add_text(slide, "College Timetable System", 0.82, 6.38, 5.0, 0.25, 18, WHITE, True, font="Aptos Display")
add_text(slide, "Flask  •  SQLite  •  JavaScript  •  AI-assisted scheduling", 0.82, 6.78, 6.6, 0.2, 10, RGBColor(255, 229, 221))
add_text(slide, "Thank you", 10.3, 6.48, 2.1, 0.35, 23, WHITE, True, font="Aptos Display", align=PP_ALIGN.RIGHT)

prs.save(OUT)
print(OUT)
