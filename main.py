import math
import traceback

import flet as ft

# ---------- FIXED FEE RULES ----------
RATE_PER_UNIT = 487
MISC_FEE = 3700
MIN_DOWN_PAYMENT = 3500
MIN_UNITS, MAX_UNITS = 1, 25
UNITS_DECIMALS = 2  # total units may have decimals, e.g. 23.5

# Standard rates used when "Configure Fee" is OFF  <-- edit if your notes differ
STANDARD_LAB_FEE = 3429.30
STANDARD_HANDS_ON_FEE = 2341.86

# Allowed number of lab / hands-on subjects (5 and above is not accepted)
MIN_LAB_SUBJECTS, MAX_LAB_SUBJECTS = 0, 4
MIN_HANDS_ON_SUBJECTS, MAX_HANDS_ON_SUBJECTS = 0, 4

# Unit balance: every lab / hands-on subject needs at least this many units,
# so (lab subjects + hands-on subjects) can never be more than the units.
MIN_UNITS_PER_SUBJECT = 1

# Share of the remaining balance paid at each exam
EXAMS = [
    ("Prelim", 0.15),
    ("1st Grading", 0.25),
    ("2nd Grading", 0.15),
    ("Midterm", 0.30),
    ("Finals", 0.15),
]

# ---------- APP IDENTITY + COLORS TAKEN FROM THE BCT LOGO ----------
APP_NAME = "BCT Tuition Calculator"
SCHOOL_NAME = "Baguio College of Technology"
APP_VERSION = "5.4"

# ---------- ABOUT US: type your group members' names here ----------
DEVELOPERS = [
    "[Add your name]",
    "[Add groupmate name]",
    "[Add groupmate name]",
]
AI_CO_DEVELOPER = "Claude (AI assistant by Anthropic)"
BCT_MAROON = "#8B1B12"
BCT_GOLD = "#F1D04B"

# ---------- BACKGROUND PRESETS (top color -> bottom color) ----------
PRESETS = {
    "BCT": {
        "light": ["#FFF8EA", "#F6DCCB", "#E9AAA0"],
        "dark": ["#190606", "#4A0F0C", "#8B1B12"],
        "seed": BCT_MAROON,
        "swatch": [BCT_GOLD, BCT_MAROON],
        "glow": (BCT_GOLD, "#D94A3D"),
    },
    "Sunset": {
        "light": ["#FFE2B8", "#FFB48F", "#F27AA0"],
        "dark": ["#1E1B4B", "#9D3C72", "#FF8A4C"],
        "seed": ft.Colors.DEEP_ORANGE,
    },
    "Ocean": {
        "light": ["#D6F1FF", "#8CCBF2", "#5FA3E8"],
        "dark": ["#06182E", "#0B3A63", "#1B6FA8"],
        "seed": ft.Colors.BLUE,
    },
    "Forest": {
        "light": ["#DDF6D8", "#9ADBA0", "#5FB38A"],
        "dark": ["#07241A", "#0E4D3A", "#2E8B64"],
        "seed": ft.Colors.GREEN,
    },
    "Lavender": {
        "light": ["#EDE3FF", "#C9B6F5", "#F0B5E0"],
        "dark": ["#1C1233", "#3F2A73", "#8A5CC0"],
        "seed": ft.Colors.DEEP_PURPLE,
    },
    "Midnight": {
        "light": ["#E3E8F2", "#B6C2D9", "#8E9CB8"],
        "dark": ["#05070D", "#0E1424", "#1C2540"],
        "seed": ft.Colors.INDIGO,
    },
}
CUSTOM_SWATCH = ["#FF9A9E", "#A18CD1", "#84FAB0"]
DEFAULT_GLASS = 70  # 0 = solid, 100 = frosted glass


def money(amount):
    return f"{amount:,.2f}"


def to_int(text, default):
    """Empty box -> default. Otherwise a whole number (ValueError if not)."""
    text = (text or "").strip()
    return int(text) if text else default


def to_float(text, default):
    """Empty box -> default. Otherwise a finite number (ValueError if not)."""
    text = (text or "").strip().replace(",", "")
    if not text:
        return default
    value = float(text)
    if not math.isfinite(value):
        raise ValueError("not a finite number")
    return value


def parse_units(text):
    """Total units: a number such as 18 or 23.5 (up to UNITS_DECIMALS decimals).
    Raises ValueError if it is not a valid finite number."""
    value = float((text or "").strip())
    if not math.isfinite(value):
        raise ValueError("not a finite number")
    scaled = value * 10 ** UNITS_DECIMALS
    if abs(scaled - round(scaled)) > 1e-9:
        raise ValueError("too many decimal places")
    return round(value, UNITS_DECIMALS)


def fmt_units(value):
    """18.0 -> '18', 23.5 -> '23.5'."""
    return f"{value:g}"


def valid_hex(text):
    """Return '#RRGGBB' if text is a valid 6-digit hex color, else None."""
    value = (text or "").strip().lstrip("#")
    if len(value) == 6 and all(c in "0123456789abcdefABCDEF" for c in value):
        return "#" + value
    return None


def vertical_gradient(colors):
    return ft.LinearGradient(
        begin=ft.Alignment(0, -1),
        end=ft.Alignment(0, 1),
        colors=colors,
    )


def cover_fit():
    # Name differs between Flet versions (BoxFit in newer, ImageFit in older)
    for name in ("BoxFit", "ImageFit"):
        enum = getattr(ft, name, None)
        if enum is not None:
            return enum.COVER
    return None


def build(page: ft.Page):
    page.title = APP_NAME
    page.padding = 0

    state = {"mode": "system", "preset": "BCT", "image_url": None, "image": None}
    glass_cards = []
    field_fill = ft.Colors.with_opacity(0.6, ft.Colors.SURFACE_CONTAINER_HIGHEST)

    # ======================= small helpers =======================
    def glass(content):
        # A Column inside a card stretches its children to the full card width,
        # so text boxes fill the card in portrait AND landscape.
        if type(content).__name__ == "Column":
            content.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        card = ft.Container(content=content, padding=20, border_radius=24)
        glass_cards.append(card)
        return card

    def heading(text):
        return ft.Text(text, size=16, weight=ft.FontWeight.BOLD)

    def field(label, hint="", numeric=True, **extra):
        # Boxes start EMPTY: the hint is a grey placeholder, so you can tap
        # and type straight away without deleting anything first.
        return ft.TextField(
            label=label,
            hint_text=hint,
            keyboard_type=ft.KeyboardType.NUMBER if numeric else ft.KeyboardType.TEXT,
            filled=True,
            bgcolor=field_fill,
            border=ft.InputBorder.NONE,
            border_radius=14,
            **extra,
        )

    def line(label, amount, bold=False):
        weight = ft.FontWeight.BOLD if bold else ft.FontWeight.NORMAL
        return ft.Row(
            [
                ft.Text(label, weight=weight, expand=True),
                ft.Text(money(amount), weight=weight),
            ]
        )

    def info_line(label, value):
        return ft.Row(
            [
                ft.Text(label),
                ft.Text(value, weight=ft.FontWeight.BOLD, expand=True,
                        text_align=ft.TextAlign.RIGHT),
            ]
        )

    # ======================= theme / background / glass =======================
    def is_dark():
        if state["mode"] == "dark":
            return True
        if state["mode"] == "light":
            return False
        try:
            return page.platform_brightness == ft.Brightness.DARK
        except Exception:
            return False

    def apply_theme():
        page.theme_mode = {
            "system": ft.ThemeMode.SYSTEM,
            "light": ft.ThemeMode.LIGHT,
            "dark": ft.ThemeMode.DARK,
        }[state["mode"]]
        preset = PRESETS.get(state["preset"])
        seed = preset["seed"] if preset else ft.Colors.INDIGO
        page.theme = ft.Theme(color_scheme_seed=seed)
        page.dark_theme = ft.Theme(color_scheme_seed=seed)

    def apply_background():
        if state["preset"] == "Custom":
            colors = [
                valid_hex(custom_top.value) or CUSTOM_SWATCH[0],
                valid_hex(custom_bottom.value) or CUSTOM_SWATCH[1],
            ]
        else:
            colors = PRESETS[state["preset"]]["dark" if is_dark() else "light"]
        background.gradient = vertical_gradient(colors)

        # optional custom image (only in Custom mode)
        link = (custom_image.value or "").strip()
        wanted = None
        if state["preset"] == "Custom" and link.lower().startswith(("http://", "https://")):
            wanted = link
        if wanted != state["image_url"]:
            if state["image"] is not None and state["image"] in stack.controls:
                stack.controls.remove(state["image"])
            state["image"] = None
            if wanted:
                picture = ft.Image(
                    src=wanted,
                    fit=cover_fit(),
                    left=0,
                    top=0,
                    right=0,
                    bottom=0,
                )
                stack.controls.insert(1, picture)
                state["image"] = picture
            state["image_url"] = wanted
        blob_one.visible = state["image"] is None
        blob_two.visible = state["image"] is None
        glow = PRESETS.get(state["preset"], {}).get("glow", ("#FFFFFF", None))
        blob_one.bgcolor = glow[0]
        blob_two.bgcolor = glow[1] or ft.Colors.PRIMARY
        apply_accent()

    def apply_accent():
        # BCT preset: maroon button/title in light mode, gold in dark mode
        if state["preset"] == "BCT":
            dark = is_dark()
            compute_button.style = ft.ButtonStyle(
                bgcolor=BCT_GOLD if dark else BCT_MAROON,
                color=BCT_MAROON if dark else "#FFFFFF",
            )
            title_text.color = BCT_GOLD if dark else BCT_MAROON
        else:
            compute_button.style = None
            title_text.color = None

    def apply_glass(level):
        # level 0 = solid card, level 100 = see-through frosted glass
        opacity = 1.0 - 0.65 * level / 100
        sigma = 28 * level / 100
        fill = ft.Colors.with_opacity(opacity, ft.Colors.SURFACE)
        for card in glass_cards:
            card.bgcolor = fill
            card.blur = ft.Blur(sigma, sigma) if sigma >= 1 else None

    def refresh_swatches():
        for name, box in swatches.items():
            if name == state["preset"]:
                box.content = ft.Icon(ft.Icons.CHECK, color=ft.Colors.WHITE)
            elif name == "Custom":
                box.content = ft.Icon(ft.Icons.PALETTE, color=ft.Colors.WHITE)
            else:
                box.content = None
        preset_label.value = state["preset"]
        custom_box.visible = state["preset"] == "Custom"

    # ======================= settings handlers =======================
    def on_mode(e):
        state["mode"] = e.control.value
        apply_theme()
        apply_background()
        page.update()

    def choose_preset(name):
        state["preset"] = name
        refresh_swatches()
        apply_theme()
        apply_background()
        page.update()

    def on_custom(e=None):
        apply_background()
        page.update()

    def on_glass(e):
        apply_glass(e.control.value)
        page.update()

    def toggle_settings(e):
        settings_card.visible = not settings_card.visible
        page.update()

    def on_brightness(e=None):
        if state["mode"] == "system":
            apply_background()
            page.update()

    page.on_platform_brightness_change = on_brightness

    # ======================= Configure Fee =======================
    # The ON/OFF switch and its info note live in the settings card (gear icon).
    # The "Configure Fee" card with the rate fields only shows on the home
    # screen while the switch is ON. When it is OFF the card is hidden, so
    # Student details sits at the top, followed by the assessment.
    def on_configure(e):
        enabled = configure_switch.value
        configure_card.visible = enabled
        standard_note.visible = not enabled
        page.update()

    configure_switch = ft.Switch(value=False, on_change=on_configure)
    lab_rate = field("Lab fee per subject", f"{STANDARD_LAB_FEE:.2f}")
    hands_rate = field("Hands-on fee per subject", f"{STANDARD_HANDS_ON_FEE:.2f}")
    standard_note = ft.Text(
        f"Using standard rates: Lab {money(STANDARD_LAB_FEE)}, "
        f"Hands-on {money(STANDARD_HANDS_ON_FEE)}",
        size=13,
    )
    fee_info = ft.Row(
        [
            ft.Icon(ft.Icons.INFO_OUTLINE, size=18),
            ft.Text(
                "Lab and hands-on fees are charged per subject. Turn this on to type "
                "your own rates, for example when the school's rates change. "
                "Turn it off to use the standard rates. A box left empty also uses its standard rate.",
                size=12,
                color=ft.Colors.ON_SURFACE_VARIANT,
                expand=True,
            ),
        ],
        vertical_alignment=ft.CrossAxisAlignment.START,
    )
    configure_card = glass(
        ft.Column(
            [heading("Configure Fee"), lab_rate, hands_rate],
            spacing=12,
        )
    )
    configure_card.visible = False

    # ======================= student inputs + results =======================
    # text keyboard on purpose: the phone's number pad has no decimal point,
    # and units can be like 23.5
    units = field(
        f"Total units enrolled ({MIN_UNITS}-{MAX_UNITS}, decimals allowed)",
        "e.g. 23.5",
        numeric=False,
    )
    lab = field(
        f"Number of subjects with LAB ({MIN_LAB_SUBJECTS}-{MAX_LAB_SUBJECTS})", "0"
    )
    hands_on = field(
        f"Total number of hands-on subjects ({MIN_HANDS_ON_SUBJECTS}-{MAX_HANDS_ON_SUBJECTS})",
        "0",
    )
    down = field(f"Down payment (min {MIN_DOWN_PAYMENT})", str(MIN_DOWN_PAYMENT))

    student_id = field("ID Number", "e.g. 2024-0001", numeric=False)
    student_name = field("Name (Last, First, M.I.)", "e.g. Dela Cruz, Juan A.", numeric=False)
    student_course = field("Course", "e.g. BSIT", numeric=False)

    error = ft.Text(color=ft.Colors.ERROR)
    results = ft.Column(spacing=6)
    results_card = glass(results)
    results_card.visible = False

    def fail(message):
        error.value = message
        page.update()

    def calculate(e):
        error.value = ""
        results.controls.clear()
        results_card.visible = False
        try:
            # ----- student information (shown above the assessment) -----
            id_text = " ".join((student_id.value or "").split())
            name_text = " ".join((student_name.value or "").split())
            course_text = " ".join((student_course.value or "").split())
            if not id_text:
                return fail("Please enter your ID number.")
            if not name_text:
                return fail("Please enter your name (Last, First, M.I.).")
            if not course_text:
                return fail("Please enter your course.")

            # ----- read the boxes (an empty box uses its placeholder default) -----
            units_text = (units.value or "").strip()
            if not units_text:
                return fail("Please enter your total units.")
            try:
                unit_count = parse_units(units_text)
            except ValueError:
                return fail(
                    f"Units must be a number such as 18 or 23.5 "
                    f"(up to {UNITS_DECIMALS} decimals)."
                )
            try:
                lab_count = to_int(lab.value, 0)
                hands_count = to_int(hands_on.value, 0)
            except ValueError:
                return fail("Lab and hands-on subjects must be whole numbers.")
            try:
                if configure_switch.value:
                    lab_fee_rate = to_float(lab_rate.value, STANDARD_LAB_FEE)
                    hands_fee_rate = to_float(hands_rate.value, STANDARD_HANDS_ON_FEE)
                else:
                    lab_fee_rate = STANDARD_LAB_FEE
                    hands_fee_rate = STANDARD_HANDS_ON_FEE
                down_pay = to_float(down.value, MIN_DOWN_PAYMENT)
            except ValueError:
                return fail("Please enter valid amounts (numbers only).")

            # ----- limits -----
            if lab_fee_rate < 0 or hands_fee_rate < 0:
                return fail("Rates cannot be negative.")
            if not MIN_UNITS <= unit_count <= MAX_UNITS:
                return fail(
                    f"Units must be from {MIN_UNITS} to {MAX_UNITS} "
                    f"(decimals like 23.5 are allowed)."
                )
            if not MIN_LAB_SUBJECTS <= lab_count <= MAX_LAB_SUBJECTS:
                return fail(
                    f"Subjects with LAB must be from {MIN_LAB_SUBJECTS} to "
                    f"{MAX_LAB_SUBJECTS} ({MAX_LAB_SUBJECTS + 1} and above is not accepted)."
                )
            if not MIN_HANDS_ON_SUBJECTS <= hands_count <= MAX_HANDS_ON_SUBJECTS:
                return fail(
                    f"Hands-on subjects must be from {MIN_HANDS_ON_SUBJECTS} to "
                    f"{MAX_HANDS_ON_SUBJECTS} ({MAX_HANDS_ON_SUBJECTS + 1} and above is not accepted)."
                )

            # ----- unit balance -----
            subject_count = lab_count + hands_count
            covered = int(unit_count // MIN_UNITS_PER_SUBJECT)
            if subject_count > covered:
                return fail(
                    f"Units don't balance: {lab_count} lab + {hands_count} hands-on = "
                    f"{subject_count} subjects, but {fmt_units(unit_count)} unit(s) cover only "
                    f"{covered}. Each lab or hands-on subject needs at least "
                    f"{MIN_UNITS_PER_SUBJECT} unit."
                )

            # ----- assessment (rounded to centavos so every line adds up) -----
            tuition = round(RATE_PER_UNIT * unit_count, 2)
            lab_fee = round(lab_fee_rate * lab_count, 2)
            hands_fee = round(hands_fee_rate * hands_count, 2)
            total = round(tuition + MISC_FEE + lab_fee + hands_fee, 2)

            if down_pay < MIN_DOWN_PAYMENT:
                return fail(f"Down payment must be at least {MIN_DOWN_PAYMENT}.")
            if down_pay > total:
                return fail("Down payment cannot be more than the total assessment.")

            down_pay = round(down_pay, 2)
            balance = round(total - down_pay, 2)

            # exam payments: the last one absorbs any leftover centavo, so the
            # schedule always adds up exactly to the remaining balance
            installments = []
            running = 0.0
            for index, (name, share) in enumerate(EXAMS):
                if index == len(EXAMS) - 1:
                    amount = round(balance - running, 2)
                else:
                    amount = round(balance * share, 2)
                    running = round(running + amount, 2)
                installments.append((name, share, amount))

            results.controls.extend(
                [
                    heading("Student information"),
                    info_line("ID Number", id_text),
                    info_line("Name", name_text),
                    info_line("Course", course_text),
                    ft.Divider(),
                    heading("Assessment"),
                    line(f"Tuition ({fmt_units(unit_count)} x {RATE_PER_UNIT})", tuition),
                    line("Miscellaneous fee", MISC_FEE),
                    line(f"Laboratory fee ({lab_count} x {money(lab_fee_rate)})", lab_fee),
                    line(f"Hands-on fee ({hands_count} x {money(hands_fee_rate)})", hands_fee),
                    ft.Divider(),
                    line("TOTAL ASSESSMENT", total, bold=True),
                    ft.Divider(),
                    heading("Payment breakdown"),
                    line("Down payment", down_pay),
                    line("Remaining balance", balance, bold=True),
                ]
            )
            for name, share, amount in installments:
                results.controls.append(line(f"{name} ({share:.0%})", amount))

            results_card.visible = True
            page.update()
        except Exception as ex:
            fail(f"Something went wrong: {ex}")

    # ======================= settings card =======================
    mode_group = ft.RadioGroup(
        value="system",
        on_change=on_mode,
        content=ft.Row(
            [
                ft.Radio(value="system", label="System"),
                ft.Radio(value="light", label="Light"),
                ft.Radio(value="dark", label="Dark"),
            ],
            wrap=True,
        ),
    )

    preset_label = ft.Text("BCT", weight=ft.FontWeight.BOLD)
    swatches = {}
    for name in list(PRESETS) + ["Custom"]:
        colors = (
            PRESETS[name].get("swatch", PRESETS[name]["light"])
            if name in PRESETS
            else CUSTOM_SWATCH
        )
        swatches[name] = ft.Container(
            width=46,
            height=46,
            border_radius=23,
            tooltip=name,
            gradient=vertical_gradient(colors),
            on_click=lambda e, n=name: choose_preset(n),
        )

    custom_top = field("Top color (hex)", "#FFB38A", numeric=False, on_change=on_custom)
    custom_bottom = field("Bottom color (hex)", "#F27AA0", numeric=False, on_change=on_custom)
    custom_image = field(
        "Image link (optional)",
        "https://... then press Enter",
        numeric=False,
        on_submit=on_custom,
        on_blur=on_custom,
    )
    custom_box = ft.Column(
        [custom_top, custom_bottom, custom_image],
        spacing=12,
        visible=False,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )

    glass_slider = ft.Slider(
        min=0, max=100, divisions=20, value=DEFAULT_GLASS, on_change=on_glass
    )

    about_section = ft.Column(
        [
            heading("About Us"),
            ft.Text(f"{APP_NAME} v{APP_VERSION}", weight=ft.FontWeight.BOLD),
            ft.Text(
                SCHOOL_NAME,
                size=12,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            ft.Text("Developers", size=13, weight=ft.FontWeight.BOLD),
            *[ft.Text(f"\u2022 {name}", size=13) for name in DEVELOPERS],
            ft.Text(
                f"\u2022 {AI_CO_DEVELOPER} \u2013 AI co-developer",
                size=13,
            ),
        ],
        spacing=4,
    )

    settings_card = glass(
        ft.Column(
            [
                heading("Appearance"),
                mode_group,
                ft.Divider(),
                ft.Row([heading("Background"), preset_label],
                       alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row(list(swatches.values()), wrap=True, spacing=10, run_spacing=10),
                custom_box,
                ft.Divider(),
                heading("Glass style"),
                glass_slider,
                ft.Row(
                    [
                        ft.Text("Solid", size=12),
                        ft.Text("Frosted glass", size=12),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Divider(),
                ft.Row(
                    [heading("Configure Fee"), configure_switch],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                fee_info,
                standard_note,
                ft.Divider(),
                about_section,
            ],
            spacing=12,
        )
    )
    settings_card.visible = False

    # ======================= layers =======================
    background = ft.Container(left=0, top=0, right=0, bottom=0)
    blob_one = ft.Container(
        width=240,
        height=240,
        border_radius=120,
        bgcolor=ft.Colors.WHITE,
        opacity=0.35,
        left=-70,
        top=80,
    )
    blob_two = ft.Container(
        width=280,
        height=280,
        border_radius=140,
        bgcolor=ft.Colors.PRIMARY,
        opacity=0.25,
        right=-90,
        bottom=140,
    )

    compute_button = ft.FilledButton(
        "Compute", on_click=calculate, expand=True, height=48
    )
    title_text = ft.Text(APP_NAME, size=20, weight=ft.FontWeight.BOLD)
    header = glass(
        ft.Row(
            [
                ft.Image(src="logo.png", width=56, height=56),
                ft.Column(
                    [
                        title_text,
                        ft.Text(
                            SCHOOL_NAME,
                            size=12,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                    ],
                    spacing=2,
                    expand=True,
                ),
                ft.IconButton(icon=ft.Icons.SETTINGS, on_click=toggle_settings),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )

    info_card = glass(
        ft.Column(
            [
                heading("Student information"),
                student_id,
                student_name,
                student_course,
            ],
            spacing=12,
        )
    )
    details_card = glass(
        ft.Column(
            [
                heading("Student details"),
                units,
                lab,
                hands_on,
                down,
                ft.Row([compute_button]),
                error,
            ],
            spacing=12,
        )
    )
    # phone upright: 1 column (full width); landscape / wider screens: 2 columns
    info_card.col = {"xs": 12, "sm": 6}
    details_card.col = {"xs": 12, "sm": 6}
    student_row = ft.ResponsiveRow([info_card, details_card], spacing=16, run_spacing=16)

    content = ft.Container(
        left=0,
        top=0,
        right=0,
        bottom=0,
        padding=20,
        content=ft.SafeArea(
            content=ft.Column(
                [
                    header,
                    settings_card,
                    configure_card,
                    student_row,
                    results_card,
                    ft.Container(height=24),
                ],
                scroll=ft.ScrollMode.AUTO,
                spacing=16,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            )
        ),
    )

    stack = ft.Stack([background, blob_one, blob_two, content], expand=True)

    # ======================= first paint =======================
    apply_theme()
    apply_background()
    apply_glass(DEFAULT_GLASS)
    refresh_swatches()
    page.add(stack)


def main(page: ft.Page):
    # If anything goes wrong while building the screen, show the error as
    # text instead of leaving a blank page.
    try:
        build(page)
    except Exception:
        page.add(ft.Text(traceback.format_exc(), selectable=True))
        page.update()


ft.run(main, assets_dir="assets")
