# -*- coding: utf-8 -*-
"""Generate 郭登奇 resume PDF from restructured Word content, referencing original PDF layout."""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Register Chinese fonts ──
FONT_DIR = r"C:\Windows\Fonts"
pdfmetrics.registerFont(TTFont("SimHei",  os.path.join(FONT_DIR, "simhei.ttf")))
pdfmetrics.registerFont(TTFont("MsYaHei",  os.path.join(FONT_DIR, "msyh.ttc"), subfontIndex=0))
pdfmetrics.registerFont(TTFont("SimSun",  os.path.join(FONT_DIR, "simsun.ttc"), subfontIndex=0))
pdfmetrics.registerFont(TTFont("SimKai",  os.path.join(FONT_DIR, "simkai.ttf")))

# ── Color palette ──
CLR_NAME     = HexColor("#1a1a2e")
CLR_SECTION  = HexColor("#16213e")
CLR_ACCENT   = HexColor("#0f3460")
CLR_BODY     = HexColor("#2c2c2c")
CLR_LIGHT    = HexColor("#666666")
CLR_LINE     = HexColor("#cccccc")
CLR_TAG_BG   = HexColor("#e8edf3")

# ── Styles ──
sName = ParagraphStyle("Name", fontName="MsYaHei", fontSize=22, leading=28,
                        textColor=CLR_NAME, spaceAfter=2*mm)
sContact = ParagraphStyle("Contact", fontName="SimSun", fontSize=10, leading=14,
                           textColor=CLR_LIGHT, spaceAfter=1*mm)
sSubtitle = ParagraphStyle("Subtitle", fontName="SimKai", fontSize=10.5, leading=14,
                            textColor=CLR_ACCENT, spaceAfter=4*mm)
sSection = ParagraphStyle("Section", fontName="SimHei", fontSize=13, leading=18,
                           textColor=CLR_SECTION, spaceBefore=5*mm, spaceAfter=2*mm)
sBody = ParagraphStyle("Body", fontName="SimSun", fontSize=10, leading=16,
                         textColor=CLR_BODY, spaceAfter=1*mm)
sBullet = ParagraphStyle("Bullet", fontName="SimSun", fontSize=9.5, leading=15,
                           textColor=CLR_BODY, leftIndent=12, spaceAfter=1*mm,
                           bulletIndent=0, bulletFontName="SimSun")
sJobTitle = ParagraphStyle("JobTitle", fontName="SimHei", fontSize=10.5, leading=15,
                            textColor=CLR_NAME, spaceBefore=3*mm, spaceAfter=1*mm)
sSmall = ParagraphStyle("Small", fontName="SimSun", fontSize=9, leading=13,
                          textColor=CLR_LIGHT, spaceAfter=0.5*mm)

# ── Helper ──
def section(title):
    return [
        HRFlowable(width="100%", thickness=0.5, color=CLR_LINE, spaceBefore=3*mm, spaceAfter=0),
        Paragraph(title, sSection),
    ]

def bullet(text):
    return Paragraph(f"\u2022  {text}", sBullet)

def job_block(company, role, period, bullets):
    items = []
    # Use a table for company/role/period alignment
    row = [
        Paragraph(f"<b>{company}</b>", ParagraphStyle("co", parent=sJobTitle, spaceBefore=0, spaceAfter=0)),
        Paragraph(f"{role}", ParagraphStyle("role", parent=sSmall, alignment=2)),
        Paragraph(period, ParagraphStyle("per", parent=sSmall, alignment=2)),
    ]
    t = Table([row], colWidths=[90*mm, 45*mm, 35*mm])
    t.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ("TOPPADDING", (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 1),
    ]))
    items.append(t)
    for b in bullets:
        items.append(bullet(b))
    return items

# ── Build document ──
OUT = r"D:\vscode\project\agent-meet\output\郭登奇-重构版.pdf"
doc = SimpleDocTemplate(
    OUT, pagesize=A4,
    leftMargin=18*mm, rightMargin=18*mm,
    topMargin=15*mm, bottomMargin=15*mm,
)

story = []

# ── Header ──
story.append(Paragraph("\u90ed\u767b\u5947", sName))
story.append(Paragraph(
    "\u7537 | 26\u5c81 | 13277409137 | 2713553860@qq.com | \u671f\u671b\u57ce\u5e02\uff1a\u6b66\u6c49",
    sContact))
story.append(Paragraph(
    "Java\u540e\u7aef / AI\u5de5\u7a0b\u65b9\u5411 | \u8fd13\u5e74\u5de5\u4f5c\u7ecf\u9a8c",
    sSubtitle))

# ── 个人优势 ──
story.extend(section("\u4e2a\u4eba\u4f18\u52bf"))
advantages = [
    "\u2460 AI\u5de5\u7a0b\u843d\u5730\uff1a\u6709LLM\u5e94\u7528\u4ece0\u52301\u843d\u5730\u7ecf\u9a8c\uff0c\u5b9e\u8df5\u8fc7LangGraph\u72b6\u6001\u673a\u7f16\u6392\u3001RAG\u6df7\u5408\u68c0\u7d22\u3001interrupt/resume\u4eba\u673a\u4ea4\u4e92\u7b49\u6838\u5fc3\u6a21\u5f0f",
    "\u2461 \u540e\u7aef\u5de5\u7a0b\u57fa\u7840\uff1a3\u5e74Java\u540e\u7aef\u5f00\u53d1\u7ecf\u9a8c\uff0c\u53c2\u4e0e\u8fc7\u524d\u540e\u7aef\u5206\u79bb\u67b6\u6784\u5347\u7ea7\u3001\u5355\u4f53\u5411\u591a\u670d\u52a1\u62c6\u5206\u8fc1\u79fb\uff0c\u5177\u5907\u5206\u5e03\u5f0f\u9501\u3001\u7f13\u5b58\u4f18\u5316\u7b49\u751f\u4ea7\u5b9e\u8df5",
    "\u2462 \u8de8\u57df\u534f\u4f5c\u4e0e\u95ee\u9898\u5b9a\u754c\uff1a\u5de5\u4f5c\u957f\u671f\u5bf9\u63a5\u76f8\u673a\u3001\u901a\u4fe1\u3001\u5185\u6838SDK\u3001\u4e91\u670d\u52a1\u3001\u5361\u7247\u52a8\u6548\u7b49\u591a\u4e2a\u9886\u57df\u56e2\u961f\uff0c\u80fd\u5728\u591a\u65b9\u4f9d\u8d56\u573a\u666f\u4e0b\u5feb\u901f\u5b9a\u754c\u95ee\u9898\u3001\u63a8\u52a8\u89e3\u51b3\u65b9\u6848\u843d\u5730",
    "\u2463 \u72ec\u7acb\u4ea4\u4ed8\u80fd\u529b\uff1a\u540e\u7aef\u4e3a\u4e3b\uff0c\u53ef\u72ec\u7acb\u5b8c\u6210\u524d\u7aef\u9875\u9762\u5f00\u53d1\u4e0e\u8054\u8c03\uff0c\u5177\u5907\u4ece\u9700\u6c42\u5230\u4e0a\u7ebf\u7684\u5b8c\u6574\u95ed\u73af\u80fd\u529b",
]
for a in advantages:
    story.append(Paragraph(a, sBody))

# ── 专业技能 ──
story.extend(section("\u4e13\u4e1a\u6280\u80fd"))
skills = [
    ("\u540e\u7aef", "Spring Boot \u00b7 Spring Cloud \u00b7 MyBatis-Plus \u00b7 Seata \u00b7 OpenFeign"),
    ("AI/\u5927\u6a21\u578b", "LangGraph \u00b7 Spring AI \u00b7 RAG\uff08\u6df7\u5408\u68c0\u7d22 / \u67e5\u8be2\u6539\u5199\uff09 \u00b7 pgvector \u00b7 Prompt Engineering"),
    ("\u6570\u636e", "MySQL \u00b7 Redis \u00b7 Canal \u00b7 pgvector"),
    ("\u8fd0\u7ef4", "Docker \u00b7 Git \u00b7 JVM\u8c03\u4f18"),
    ("\u524d\u7aef", "JavaScript \u00b7 ArkTS\uff08\u4e86\u89e3\uff09"),
]
for cat, detail in skills:
    story.append(Paragraph(f"<b>{cat}</b>\uff1a{detail}", sBody))

# ── 项目经历 ──
story.extend(section("\u9879\u76ee\u7ecf\u5386"))

# Agent Meet
story.extend(job_block(
    "Agent Meet \u2014 AI\u81ea\u9002\u5e94\u6a21\u62df\u9762\u8bd5\u5e73\u53f0",
    "\u5168\u6808\u5de5\u7a0b\u5e08\uff08\u4e2a\u4eba\u9879\u76ee\uff09", "2026.04 - 2026.06",
    [
        "\u57fa\u4e8e LangGraph StateGraph \u6784\u5efa\u9762\u8bd5\u5bf9\u8bdd\u6d41\u7a0b\uff0c\u901a\u8fc7 add_conditional_edges \u58f0\u660e\u5f0f\u8868\u8fbe\u8ffd\u95ee/\u8df3\u8fc7/\u63d0\u793a\u7b49\u6761\u4ef6\u5206\u652f\uff0c\u65b0\u589e\u8282\u70b9\u53ea\u9700\u6ce8\u518c\u8282\u70b9\u4e0e\u8fb9\uff0c\u4e0d\u5f71\u54cd\u5df2\u6709\u903b\u8f91",
        "\u4f7f\u7528 LangGraph interrupt/resume \u539f\u8bed\u5b9e\u73b0\u4eba\u673a\u4ea4\u4e92\u6682\u505c\u4e0e\u6062\u590d\uff0c\u89e3\u51b3\u957f\u65f6\u9762\u8bd5\u573a\u666f\u4e0b HTTP \u8fde\u63a5\u4e22\u5931\u95ee\u9898\uff1b\u5728 FastAPI \u4e0e LangGraph \u6570\u636e\u683c\u5f0f\u4e0d\u5339\u914d\u5904\u8bbe\u8ba1\u6865\u63a5\u5c42",
        "\u5b9e\u73b0\u53cc\u5c42\u8bb0\u5fc6\u673a\u5236\uff1a\u77ed\u671f\u8bb0\u5fc6\u5b58\u4e8e AgentState \u5b9e\u65f6\u66f4\u65b0\uff0c\u76f4\u63a5\u5f71\u54cd\u6a21\u578b\u51b3\u7b56\uff1b\u957f\u671f\u8bb0\u5fc6\u9762\u8bd5\u7ed3\u675f\u540e\u6279\u91cf\u6301\u4e45\u5316\u81f3\u6570\u636e\u5e93\uff0c\u652f\u6301\u8de8\u4f1a\u8bdd\u8fde\u7eed\u8bad\u7ec3",
        "\u7ed3\u5408 pgvector \u5411\u91cf\u68c0\u7d22\u4e0e BM25 \u5173\u952e\u8bcd\u68c0\u7d22\u5b9e\u73b0\u6df7\u5408\u53ec\u56de\uff0c\u52a0\u6743\u91cd\u6392\u540e\u53d6 TopK \u8f93\u5165 LLM\uff0c\u89e3\u51b3\u5355\u4e00\u5411\u91cf\u68c0\u7d22\u5728\u7cbe\u786e\u672f\u8bed\u5339\u914d\u4e0a\u7684\u9057\u6f0f",
    ]
))

# mall-ai
story.extend(job_block(
    "mall-ai \u2014 \u667a\u80fd\u7535\u5546\u5bfc\u8d2d\u5e73\u53f0",
    "\u5168\u6808\u5de5\u7a0b\u5e08\uff08\u4e2a\u4eba\u9879\u76ee\uff09", "2026.04 - 2026.06",
    [
        "\u57fa\u4e8e Spring AI + DeepSeek-V3 \u6784\u5efa RAG \u5bfc\u8d2d\u7cfb\u7edf\uff0c\u5b9e\u73b0\u5411\u91cf\u68c0\u7d22\u4e0e\u5173\u952e\u8bcd\u6df7\u5408\u53ec\u56de\uff0cSSE \u6d41\u5f0f\u8f93\u51fa\u54cd\u5e94\u7ed3\u679c",
        "\u8bbe\u8ba1\u89c4\u5219\u9a71\u52a8\u7684\u610f\u56fe\u8def\u7531\u5c42\uff0c\u901a\u8fc7\u6b63\u5219\u5339\u914d\u524d\u7f6e\u5206\u6d41\uff0c\u4e8b\u5b9e\u67e5\u8be2\u76f4\u63a5\u8d70\u7f13\u5b58\u8df3\u8fc7 LLM \u8c03\u7528\uff0c\u964d\u4f4e\u65e0\u6548\u63a8\u7406\u5f00\u9500",
        "\u8f93\u5165\u5c42\u5f15\u5165\u6b63\u5219\u68c0\u6d4b\u9632\u8303 prompt \u6ce8\u5165\uff0c\u670d\u52a1\u5c42\u5b9e\u73b0\u6a21\u578b\u964d\u7ea7\u7b56\u7565\uff0c\u4fdd\u969c\u7cfb\u7edf\u53ef\u7528\u6027",
        "\u901a\u8fc7 OpenFeign \u4e0e\u539f\u6709 Java \u7535\u5546\u670d\u52a1\u96c6\u6210\uff0c\u590d\u7528\u65e2\u6709\u6570\u636e\u5e93\u4e0e JWT \u9274\u6743\u4f53\u7cfb\uff0c\u907f\u514d\u91cd\u590d\u5efa\u8bbe",
    ]
))

# ── 工作经历 ──
story.extend(section("\u5de5\u4f5c\u7ecf\u5386"))

story.extend(job_block(
    "\u4e2d\u8f6f\u56fd\u9645\u6709\u9650\u516c\u53f8\uff08\u5916\u6d3e\u534e\u4e3a\u7ec8\u7aefBG\uff09",
    "Java\u540e\u7aef\u5f00\u53d1", "2024.09 - 2026.04",
    [
        "\u6269\u5c55 Home \u6570\u636e\u6a21\u578b\uff0c\u65b0\u589e type \u4e0e relationDevInfo \u5b57\u6bb5\uff0c\u8bbe\u8ba1\u5e76\u5b9e\u73b0\u8f66 Home \u521b\u5efa\u3001\u67e5\u8be2\u3001\u8bbe\u5907\u4fe1\u606f\u66f4\u65b0\u63a5\u53e3",
        "\u5b9e\u73b0\u4e24\u5957\u8f66 Home \u81ea\u52a8\u521b\u5efa\u6d41\u7a0b\uff1a\u8f66\u673a\u767b\u5f55\u65f6\u57fa\u4e8e\u8f66\u67b6\u53f7\u6821\u9a8c\u89e6\u53d1\u521b\u5efa\uff1b\u7ed1\u5b9a\u9e3f\u8499\u667a\u884c\u8f66\u8f86\u540e\u4e91\u7aef\u81ea\u52a8\u89e6\u53d1\u6ce8\u518c\u4e0e Home \u5173\u8054",
        "\u9488\u5bf9 Home \u521b\u5efa\u5f15\u5165 Redisson \u5206\u5e03\u5f0f\u9501\u5b9e\u73b0\u4e92\u65a5\u8bbf\u95ee\uff0c\u9632\u6b62\u5e76\u53d1\u573a\u666f\u4e0b\u91cd\u590d\u521b\u5efa\uff0c\u4fdd\u969c\u4e00\u8f66\u4e00 Home \u6570\u636e\u4e00\u81f4\u6027",
        "\u8bbe\u8ba1 VIN \u517c\u5bb9\u5339\u914d\u903b\u8f91\uff0c\u89e3\u51b3\u8f66\u673a\u5b8c\u6574 VIN \u4e0e\u4e91\u4e91\u540e\u516d\u4f4d VIN \u7684\u683c\u5f0f\u5dee\u5f02\uff1b\u65b0\u589e\u6309 type \u67e5\u8be2\u63a5\u53e3\u5e76\u5f15\u5165\u7f13\u5b58\uff0c\u964d\u4f4e\u6570\u636e\u5e93\u538b\u529b",
    ]
))

story.extend(job_block(
    "\u4e1c\u839e\u5e02\u6da6\u4e0a\u91d1\u5c5e\u6750\u6599\u6709\u9650\u516c\u53f8",
    "\u5168\u6808\u5de5\u7a0b\u5e08", "2024.05 - 2024.08",
    [
        "\u53c2\u4e0e\u516c\u53f8\u7ba1\u7406\u7cfb\u7edf\uff08RuoYi \u6846\u67b6\uff09\u5f00\u53d1\u4e0e\u7ef4\u62a4\uff0c\u8d1f\u8d23\u62a5\u4ef7\u3001\u51fa\u5165\u5e93\u7b49\u6a21\u5757\u7684\u529f\u80fd\u6269\u5c55\u4e0e\u6570\u636e\u8868\u8bbe\u8ba1",
        "\u5f00\u53d1\u516c\u53f8\u5b98\u65b9\u5c0f\u7a0b\u5e8f\uff0c\u5b9e\u73b0\u62a5\u4ef7\u903b\u8f91\u4e0e Excel \u6279\u91cf\u5bfc\u51fa\u529f\u80fd",
    ]
))

story.extend(job_block(
    "\u5bcc\u58eb\u5eb7\u5de5\u4e1a\u4e92\u8054\u7f51\u80a1\u4efd\u6709\u9650\u516c\u53f8",
    "\u7cfb\u7edf\u5de5\u7a0b\u5e08", "2022.07 - 2024.05",
    [
        "\u8d1f\u8d23\u7cbe\u786e\u62a5\u4ef7\u3001\u6a21\u5177\u51fa\u5165\u5e93\u3001\u6743\u9650\u914d\u7f6e\u7b49\u6838\u5fc3\u6a21\u5757\u7684\u63a5\u53e3\u5f00\u53d1\u4e0e\u8054\u8c03",
        "\u53c2\u4e0e\u7cfb\u7edf\u524d\u540e\u7aef\u5206\u79bb\u67b6\u6784\u5347\u7ea7\uff0c\u7531 JSP \u8fc1\u79fb\u81f3 Vue + Spring Boot\uff0c\u5236\u5b9a\u7edf\u4e00 API \u89c4\u8303",
        "\u53c2\u4e0e\u5355\u4f53\u670d\u52a1\u5411\u591a\u670d\u52a1\u67b6\u6784\u8fc1\u79fb\uff0c\u8d1f\u8d23\u62a5\u4ef7\u4e0e\u4ed3\u50a8\u6a21\u5757\u7684\u670d\u52a1\u5316\u62c6\u5206",
    ]
))

# ── 教育经历 ──
story.extend(section("\u6559\u80b2\u7ecf\u5386"))
story.append(Paragraph(
    "<b>\u9ec4\u5188\u5e08\u8303\u5b66\u9662</b>\u3000\u672c\u79d1 \u00b7 \u7f51\u7edc\u5de5\u7a0b\u3000\u30002018 - 2022",
    sBody))

# ── 资格证书 ──
story.extend(section("\u8d44\u683c\u8bc1\u4e66"))
story.append(Paragraph("\u5927\u5b66\u82f1\u8bed\u56db\u7ea7", sBody))

# ── Generate ──
doc.build(story)
print(f"PDF generated: {OUT}")
