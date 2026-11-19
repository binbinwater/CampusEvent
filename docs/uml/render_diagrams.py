from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path("docs/uml")
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1800, 1250
BG = "#FFFFFF"
INK = "#1D2935"
MUTED = "#687583"
BRAND = "#1D4E89"
BRAND_SOFT = "#E7EFF9"
ACCENT = "#E76F51"
ACCENT_SOFT = "#FCEEE9"
MINT = "#2A9D8F"
MINT_SOFT = "#E1F4F0"
LINE = "#CBD6DF"
PANEL = "#F8FAFC"

REG = "C:/Windows/Fonts/msyh.ttc"
BOLD = "C:/Windows/Fonts/msyhbd.ttc"


def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else REG, size)


F_TITLE = font(42, True)
F_H2 = font(28, True)
F_NAME = font(25, True)
F_BODY = font(21)
F_SMALL = font(18)
F_TINY = font(16)
F_ACTOR = font(23, True)


def canvas(title, subtitle="", height=H):
    image = Image.new("RGB", (W, height), BG)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, W, 10), fill=BRAND)
    draw.text((80, 38), title, font=F_TITLE, fill=INK)
    if subtitle:
        draw.text((82, 95), subtitle, font=F_SMALL, fill=MUTED)
    return image, draw


def box(draw, xy, title, lines, fill=BG, outline=BRAND, title_fill=BRAND, title_size=25):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=14, fill=fill, outline=outline, width=2)
    draw.rectangle((x1 + 1, y1 + 1, x2 - 1, y1 + 54), fill=title_fill)
    draw.text(((x1 + x2) / 2, y1 + 28), title, font=font(title_size, True), fill="white", anchor="mm")
    y = y1 + 70
    for line in lines:
        draw.text((x1 + 20, y), line, font=F_BODY, fill=INK)
        y += 32


def text_center(draw, xy, text, font_obj, fill=INK):
    x1, y1, x2, y2 = xy
    draw.multiline_text(
        ((x1 + x2) / 2, (y1 + y2) / 2),
        text,
        font=font_obj,
        fill=fill,
        anchor="mm",
        align="center",
        spacing=8,
    )


def arrow(draw, start, end, color=BRAND, width=3, dash=False, label=None, label_offset=(0, 0)):
    x1, y1 = start
    x2, y2 = end
    if dash:
        # dashed line: draw short segments
        total = max(abs(x2 - x1), abs(y2 - y1))
        if total == 0:
            return
        for i in range(0, int(total), 18):
            t1 = i / total
            t2 = min((i + 10) / total, 1)
            draw.line(
                (x1 + (x2 - x1) * t1, y1 + (y2 - y1) * t1, x1 + (x2 - x1) * t2, y1 + (y2 - y1) * t2),
                fill=color,
                width=width,
            )
    else:
        draw.line((x1, y1, x2, y2), fill=color, width=width)
    # arrow head
    dx, dy = x2 - x1, y2 - y1
    length = max((dx * dx + dy * dy) ** 0.5, 1)
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    size = 16
    draw.polygon(
        [
            (x2, y2),
            (x2 - ux * size + px * size * 0.55, y2 - uy * size + py * size * 0.55),
            (x2 - ux * size - px * size * 0.55, y2 - uy * size - py * size * 0.55),
        ],
        fill=color,
    )
    if label:
        mx = (x1 + x2) / 2 + label_offset[0]
        my = (y1 + y2) / 2 + label_offset[1]
        draw.text((mx, my), label, font=F_SMALL, fill=color, anchor="mm")


def dashed_arrow(draw, start, end, color=BRAND, label=None):
    arrow(draw, start, end, color=color, width=2, dash=True, label=label)


def actor(draw, x, y, label):
    # head
    draw.ellipse((x - 22, y, x + 22, y + 44), outline=INK, width=3, fill=BG)
    # body
    draw.line((x, y + 44, x, y + 104), fill=INK, width=3)
    # arms
    draw.line((x - 42, y + 65, x + 42, y + 65), fill=INK, width=3)
    # legs
    draw.line((x, y + 104, x - 35, y + 155), fill=INK, width=3)
    draw.line((x, y + 104, x + 35, y + 155), fill=INK, width=3)
    draw.text((x, y + 170), label, font=F_ACTOR, fill=INK, anchor="ma")


# ---------------------------------------------------------------- use case
image, draw = canvas(
    "实验二 · CampusEvent 用例图",
    "固定演示账号分为 Student 与 Admin；无注册和复杂权限。",
)
# system boundary
draw.rounded_rectangle((410, 170, 1390, 1120), radius=24, fill=PANEL, outline=BRAND, width=3)
draw.text((900, 205), "CampusEvent 校园活动系统", font=F_H2, fill=BRAND, anchor="mm")
actor(draw, 150, 430, "Student\n学生")
actor(draw, 1650, 430, "Admin\n管理员")

use_cases = {
    "browse": (660, 285, 1140, 390, "浏览活动\n按名称筛选"),
    "register": (660, 430, 1140, 535, "提交报名\n检查开始时间、重复与名额"),
    "cancel": (660, 575, 1140, 680, "取消自己的\n待审核/已通过报名"),
    "mine": (660, 720, 1140, 825, "查看我的报名\n与站内消息"),
    "create": (660, 865, 1140, 970, "创建/编辑/删除活动\n设置报名方式与容量"),
    "approve": (660, 1010, 1140, 1115, "审批待审核报名\n批准时复核名额"),
}
for _, (x1, y1, x2, y2, text) in use_cases.items():
    draw.ellipse((x1, y1, x2, y2), fill=BG, outline=BRAND, width=3)
    text_center(draw, (x1, y1, x2, y2), text, F_BODY)

# Student links
for key in ("browse", "register", "cancel", "mine"):
    x1, y1, x2, y2, _ = use_cases[key]
    arrow(draw, (205, 510), (x1, (y1 + y2) / 2), color=BRAND, width=2)
# Admin links
for key in ("create", "approve", "browse"):
    x1, y1, x2, y2, _ = use_cases[key]
    arrow(draw, (1595, 510), (x2, (y1 + y2) / 2), color=ACCENT, width=2)
# no include arrows: the two central rules are described in the use-case document
draw.text((450, 1170), "图 1  用例图（初版，不含 CR 变更）", font=F_SMALL, fill=MUTED)
image.save(OUT / "use-case.png")

# ---------------------------------------------------------------- class diagram
image, draw = canvas(
    "实验二 · CampusEvent UML 类图（baseline-v1）",
    "策略抽象负责初始状态；名额检查由 RegistrationService 作为公共规则统一执行。",
    height=1360,
)
# Student
box(
    draw,
    (60, 145, 430, 390),
    "Student",
    ["- student_id: String", "- name: String"],
    fill=BG,
    outline="#7A8FA6",
    title_fill="#596B80",
)
# Activity
box(
    draw,
    (700, 145, 1170, 410),
    "Activity",
    [
        "- id: int",
        "- title/category/location",
        "- start_at: DateTime",
        "- capacity: int",
        "- policy_type: String",
        "+ is_full()",
    ],
    fill=BG,
    outline=BRAND,
)
# Message
box(
    draw,
    (1320, 145, 1740, 390),
    "Message",
    ["- student_id: String", "- activity_id: int", "- content: String", "- is_read: bool"],
    fill=BG,
    outline="#7A8FA6",
    title_fill="#596B80",
)
# Registration
box(
    draw,
    (60, 505, 430, 790),
    "Registration",
    [
        "- id: int",
        "- activity_id: int",
        "- student_id: String",
        "- status: enum",
        "+ is_active()",
    ],
    fill=BG,
    outline=BRAND,
)
# RegistrationService
box(
    draw,
    (700, 505, 1210, 815),
    "RegistrationService",
    [
        "+ register(activity, student)",
        "+ cancel(registration, student)",
        "+ approve(registration)",
        "+ reject(registration)",
        "# _check_capacity()",
    ],
    fill=MINT_SOFT,
    outline=MINT,
    title_fill=MINT,
)
# EventPublisher
box(
    draw,
    (1320, 505, 1740, 760),
    "EventPublisher",
    ["- subscribers: list", "+ publish(event)"],
    fill=ACCENT_SOFT,
    outline=ACCENT,
    title_fill=ACCENT,
)
# Policy interface
box(
    draw,
    (480, 880, 840, 1010),
    "«interface»\nRegistrationPolicy",
    ["+ initial_status(): String"],
    fill=BRAND_SOFT,
    outline=BRAND,
    title_size=20,
)
# Direct
box(
    draw,
    (420, 1050, 720, 1190),
    "DirectRegistrationPolicy",
    ["+ initial_status(): approved"],
    fill=BG,
    outline=BRAND,
    title_fill="#4A74A6",
    title_size=18,
)
# Review
box(
    draw,
    (760, 1050, 1060, 1190),
    "ReviewRegistrationPolicy",
    ["+ initial_status(): pending"],
    fill=BG,
    outline=BRAND,
    title_fill="#4A74A6",
    title_size=18,
)
# Subscriber interface
box(
    draw,
    (1320, 880, 1660, 1010),
    "«interface»\nEventSubscriber",
    ["+ handle(event)"],
    fill=ACCENT_SOFT,
    outline=ACCENT,
    title_size=20,
)
# Observer
box(
    draw,
    (1320, 1050, 1740, 1200),
    "MessageNotificationObserver",
    ["+ handle(event)", "+ write message"],
    fill=BG,
    outline=ACCENT,
    title_fill="#C95C42",
    title_size=21,
)
# Relationships
draw.line((245, 390, 245, 505), fill=INK, width=2)
draw.text((260, 442), "1      *", font=F_SMALL, fill=MUTED)
draw.line((800, 410, 430, 505), fill=INK, width=2)
draw.text((590, 438), "1      *", font=F_SMALL, fill=MUTED)
draw.line((430, 650, 700, 650), fill=INK, width=2)
draw.text((540, 625), "uses", font=F_SMALL, fill=MUTED)
arrow(draw, (700, 815), (660, 880), color=MUTED, width=2, label="uses")
draw.line((1210, 615, 1320, 615), fill=ACCENT, width=2)
draw.text((1225, 590), "publishes", font=F_SMALL, fill=ACCENT)
dashed_arrow(draw, (1490, 760), (1490, 880), color=ACCENT)
dashed_arrow(draw, (1490, 1050), (1490, 1010), color=ACCENT)
dashed_arrow(draw, (570, 1050), (570, 1010), color=BRAND)
dashed_arrow(draw, (910, 1050), (800, 1010), color=BRAND)
draw.text((150, 1285), "注：虚线箭头表示实现或依赖；Activity / Registration / Message 由 Repository 持久化，图中省略 Repository 以保持可读性。", font=F_SMALL, fill=MUTED)
image.save(OUT / "class.png")

# ---------------------------------------------------------------- sequence register
image, draw = canvas(
    "实验二 · 直接/审核报名时序图",
    "报名事务先提交，再发布报名事件；通知失败不回滚报名。",
)
participants = [
    ("学生", 130),
    ("活动详情路由", 395),
    ("RegistrationService", 690),
    ("RegistrationPolicy", 965),
    ("Repository", 1210),
    ("EventPublisher", 1430),
    ("MessageObserver", 1680),
]
for name, x in participants:
    draw.rounded_rectangle((x - 105, 175, x + 105, 245), radius=12, fill=BRAND if name != "RegistrationPolicy" else MINT, outline=BRAND)
    draw.multiline_text((x, 210), name, font=F_SMALL, fill="white", anchor="mm", align="center")
    draw.line((x, 245, x, 1120), fill=LINE, width=2, )


def msg(draw, x1, x2, y, label, color=BRAND, dashed=False, selfx=None):
    if selfx is not None:
        draw.arc((selfx + 8, y - 60, selfx + 190, y + 30), start=270, end=90, fill=color, width=2)
        arrow(draw, (selfx + 170, y + 10), (selfx + 18, y + 10), color=color, width=2, dash=dashed)
        draw.text((selfx + 30, y - 72), label, font=F_SMALL, fill=color)
        return
    arrow(draw, (x1, y), (x2, y), color=color, width=2, dash=dashed)
    draw.text(((x1 + x2) / 2, y - 20), label, font=F_SMALL, fill=color, anchor="ma")


msg(draw, 130, 395, 320, "POST /register")
msg(draw, 395, 690, 375, "register(activity, student)")
msg(draw, 690, 1210, 430, "读取活动与有效报名")
msg(draw, 690, 1210, 485, "统计已通过人数（<= capacity）")
msg(draw, 690, 965, 540, "initial_status()", color=MINT)
draw.text((820, 566), "direct → approved / review → pending", font=F_TINY, fill=MUTED)
msg(draw, 690, 1210, 620, "插入报名 + COMMIT")
draw.rounded_rectangle((680, 655, 1510, 715), radius=8, fill=MINT_SOFT, outline=MINT)
draw.text((700, 675), "事务已提交：通知故障不会回滚已合法提交的报名", font=F_SMALL, fill="#1F655D")
msg(draw, 690, 1430, 760, "publish(RegistrationEvent)")
msg(draw, 1430, 1680, 815, "handle(event)")
msg(draw, 1680, 1210, 875, "写入站内消息 + COMMIT")
msg(draw, 690, 395, 975, "成功状态", dashed=True)
msg(draw, 395, 130, 1040, "303 返回详情页", dashed=True)
draw.text((1250, 1120), "图 3  报名时序图（直接报名与审核报名共用，仅初始状态不同）", font=F_SMALL, fill=MUTED)
image.save(OUT / "sequence-register.png")

# ---------------------------------------------------------------- sequence approve
image, draw = canvas(
    "实验二 · 管理员审批时序图",
    "批准时在同一个 BEGIN IMMEDIATE 事务中复核名额，再提交并通知。",
)
participants = [
    ("管理员", 130),
    ("审批路由", 405),
    ("RegistrationService", 700),
    ("Repository", 995),
    ("SQLite 事务", 1225),
    ("EventPublisher", 1470),
    ("MessageObserver", 1690),
]
for name, x in participants:
    draw.rounded_rectangle((x - 105, 175, x + 105, 245), radius=12, fill=BRAND, outline=BRAND)
    draw.multiline_text((x, 210), name, font=F_SMALL, fill="white", anchor="mm", align="center")
    draw.line((x, 245, x, 1120), fill=LINE, width=2)
msg(draw, 130, 405, 320, "POST /approve")
msg(draw, 405, 700, 375, "approve(registration)")
msg(draw, 700, 995, 430, "读取待审核报名")
msg(draw, 700, 1225, 485, "BEGIN IMMEDIATE")
msg(draw, 700, 995, 540, "统计 approved；复核 capacity")
msg(draw, 700, 1225, 600, "UPDATE approved + COMMIT")
msg(draw, 700, 1470, 670, "publish(approved)")
msg(draw, 1470, 1690, 725, "handle(event)")
msg(draw, 1690, 995, 780, "写入站内消息")
msg(draw, 700, 405, 880, "失败：名额已满 / 状态已变化", color=ACCENT, dashed=True)
msg(draw, 405, 130, 945, "303 返回详情页", dashed=True)
draw.text((760, 1095), "图 4  审批时序图（仅 pending 可审批；通知失败不回滚审批结果）", font=F_SMALL, fill=MUTED)
image.save(OUT / "sequence-approve.png")

print("generated", [p.name for p in OUT.glob("*.png")])