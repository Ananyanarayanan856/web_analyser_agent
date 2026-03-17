# from playwright.sync_api import sync_playwright
# from bs4 import BeautifulSoup
# import re
# import urllib3

# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# # ─────────────────────────────────────────────
# # WCAG 2.1 Color Contrast Helpers
# # ─────────────────────────────────────────────

# def hex_to_rgb(hex_color: str) -> tuple:
#     """Convert a 6-digit hex color string to an (R, G, B) tuple."""
#     hex_color = hex_color.strip("#")
#     return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


# def relative_luminance(rgb: tuple) -> float:
#     """Calculate WCAG relative luminance from an RGB tuple."""
#     def linearize(c):
#         c /= 255.0
#         return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

#     r, g, b = rgb
#     return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)


# def contrast_ratio(hex1: str, hex2: str) -> float:
#     """Return the WCAG contrast ratio between two hex colors."""
#     lum1 = relative_luminance(hex_to_rgb(hex1))
#     lum2 = relative_luminance(hex_to_rgb(hex2))
#     lighter = max(lum1, lum2)
#     darker  = min(lum1, lum2)
#     return (lighter + 0.05) / (darker + 0.05)


# def parse_hex_color(style: str, prop: str) -> str | None:
#     """
#     Extract a hex color value for a CSS property from an inline style string.
#     Supports both 3-digit (#abc) and 6-digit (#aabbcc) hex values.
#     """
#     pattern = rf'{prop}:\s*#([0-9a-fA-F]{{3}}(?:[0-9a-fA-F]{{3}})?)'
#     match = re.search(pattern, style, re.IGNORECASE)
#     if not match:
#         return None
#     raw = match.group(1)
#     # Expand shorthand #abc → #aabbcc
#     if len(raw) == 3:
#         raw = "".join(c * 2 for c in raw)
#     return raw.lower()


# # ─────────────────────────────────────────────
# # Main Analyzer
# # ─────────────────────────────────────────────

# def accessibility_analyzer(url: str, browser=None) -> dict:

#     try:

#         # ─────────────────────────────────────
#         # Load page using Playwright
#         # ─────────────────────────────────────
#         if browser:
#             page = browser.new_page()
#             page.goto(url, wait_until="domcontentloaded", timeout=30000)
#             html = page.content()
#             page.close()
#         else:
#             with sync_playwright() as p:
#                 temp_browser = p.chromium.launch(headless=True)
#                 page = temp_browser.new_page()
#                 page.goto(url, wait_until="domcontentloaded", timeout=30000)
#                 html = page.content()
#                 temp_browser.close()

#         soup = BeautifulSoup(html, "html.parser")

#         issues  = []
#         details = {}
#         score   = 100

#         # ══════════════════════════════════════
#         # CHECK 1 ─ Missing ALT / Text Alternatives
#         #           Covers ALL media elements, not just <img>
#         # ══════════════════════════════════════
#         #
#         # Elements checked:
#         #   <img>                 → alt attribute
#         #   <area>                → alt attribute (image maps)
#         #   <input type="image">  → alt attribute
#         #   <video>               → <track kind="captions/subtitles"> or aria-label
#         #   <audio>               → <track> or aria-label / title
#         #   <canvas>              → aria-label or fallback text content
#         #   <svg>                 → <title> child or aria-label
#         #   <object>              → fallback text, aria-label, or title
#         #   <embed>               → aria-label or title
#         #   <iframe>              → title or aria-label

#         missing_alt_report = []

#         # ── <img> ──────────────────────────────
#         for img in soup.find_all("img"):
#             alt = img.get("alt")
#             is_decorative = (
#                 img.get("role") == "presentation" or
#                 img.get("aria-hidden") == "true"
#             )
#             if not is_decorative:
#                 if alt is None or alt.strip() == "":
#                     missing_alt_report.append({
#                         "tag"    : "img",
#                         "issue"  : "Missing or empty alt attribute",
#                         "snippet": str(img)[:120]
#                     })

#         # ── <area> (image maps) ────────────────
#         for area in soup.find_all("area"):
#             if not area.get("alt", "").strip() and area.get("href"):
#                 missing_alt_report.append({
#                     "tag"    : "area",
#                     "issue"  : "Linked <area> missing alt attribute",
#                     "snippet": str(area)[:120]
#                 })

#         # ── <input type="image"> ───────────────
#         for inp in soup.find_all("input", attrs={"type": "image"}):
#             if not inp.get("alt", "").strip():
#                 missing_alt_report.append({
#                     "tag"    : "input[type=image]",
#                     "issue"  : "Image input missing alt attribute",
#                     "snippet": str(inp)[:120]
#                 })

#         # ── <video> ────────────────────────────
#         for video in soup.find_all("video"):
#             has_caption_track = any(
#                 t.get("kind", "").lower() in ("captions", "subtitles")
#                 for t in video.find_all("track")
#             )
#             has_aria = (
#                 bool(video.get("aria-label", "").strip()) or
#                 bool(video.get("aria-labelledby", "").strip())
#             )
#             if not has_caption_track and not has_aria:
#                 missing_alt_report.append({
#                     "tag"    : "video",
#                     "issue"  : "Video missing captions/subtitles track or ARIA label",
#                     "snippet": str(video)[:120]
#                 })

#         # ── <audio> ────────────────────────────
#         for audio in soup.find_all("audio"):
#             has_track = bool(audio.find("track"))
#             has_aria  = (
#                 bool(audio.get("aria-label", "").strip()) or
#                 bool(audio.get("aria-labelledby", "").strip())
#             )
#             has_title = bool(audio.get("title", "").strip())
#             if not any([has_track, has_aria, has_title]):
#                 missing_alt_report.append({
#                     "tag"    : "audio",
#                     "issue"  : "Audio missing accessible label or transcript track",
#                     "snippet": str(audio)[:120]
#                 })

#         # ── <canvas> ───────────────────────────
#         for canvas in soup.find_all("canvas"):
#             has_aria     = (
#                 bool(canvas.get("aria-label", "").strip()) or
#                 bool(canvas.get("aria-labelledby", "").strip())
#             )
#             has_fallback = bool(canvas.get_text(strip=True))
#             has_role     = bool(canvas.get("role", "").strip())
#             if not any([has_aria, has_fallback, has_role]):
#                 missing_alt_report.append({
#                     "tag"    : "canvas",
#                     "issue"  : "Canvas missing aria-label or fallback text content",
#                     "snippet": str(canvas)[:120]
#                 })

#         # ── <svg> ──────────────────────────────
#         for svg in soup.find_all("svg"):
#             is_decorative = svg.get("aria-hidden") == "true"
#             if not is_decorative:
#                 has_title = bool(svg.find("title"))
#                 has_aria  = (
#                     bool(svg.get("aria-label", "").strip()) or
#                     bool(svg.get("aria-labelledby", "").strip())
#                 )
#                 if not has_title and not has_aria:
#                     missing_alt_report.append({
#                         "tag"    : "svg",
#                         "issue"  : "SVG missing <title> element or aria-label",
#                         "snippet": str(svg)[:120]
#                     })

#         # ── <object> ───────────────────────────
#         for obj in soup.find_all("object"):
#             has_fallback = bool(obj.get_text(strip=True))
#             has_aria     = (
#                 bool(obj.get("aria-label", "").strip()) or
#                 bool(obj.get("aria-labelledby", "").strip())
#             )
#             has_title = bool(obj.get("title", "").strip())
#             if not any([has_fallback, has_aria, has_title]):
#                 missing_alt_report.append({
#                     "tag"    : "object",
#                     "issue"  : "Object element missing fallback text or accessible label",
#                     "snippet": str(obj)[:120]
#                 })

#         # ── <embed> ────────────────────────────
#         for embed in soup.find_all("embed"):
#             has_aria  = (
#                 bool(embed.get("aria-label", "").strip()) or
#                 bool(embed.get("aria-labelledby", "").strip())
#             )
#             has_title = bool(embed.get("title", "").strip())
#             if not has_aria and not has_title:
#                 missing_alt_report.append({
#                     "tag"    : "embed",
#                     "issue"  : "Embed missing aria-label or title attribute",
#                     "snippet": str(embed)[:120]
#                 })

#         # ── <iframe> ───────────────────────────
#         for iframe in soup.find_all("iframe"):
#             has_title = bool(iframe.get("title", "").strip())
#             has_aria  = (
#                 bool(iframe.get("aria-label", "").strip()) or
#                 bool(iframe.get("aria-labelledby", "").strip())
#             )
#             if not has_title and not has_aria:
#                 missing_alt_report.append({
#                     "tag"    : "iframe",
#                     "issue"  : "Iframe missing title or aria-label attribute",
#                     "snippet": str(iframe)[:120]
#                 })

#         # Group violations by tag for the detail report
#         by_tag = {}
#         for r in missing_alt_report:
#             by_tag.setdefault(r["tag"], []).append(r["issue"])

#         details["missing_alt"] = {
#             "total_violations": len(missing_alt_report),
#             "by_tag"          : by_tag,
#             "snippets"        : [r["snippet"] for r in missing_alt_report[:10]]
#         }

#         if missing_alt_report:
#             tag_summary = ", ".join(
#                 f"{tag}×{len(v)}" for tag, v in by_tag.items()
#             )
#             issues.append(
#                 f"[ALT] {len(missing_alt_report)} element(s) missing text alternatives "
#                 f"— {tag_summary}"
#             )
#             score -= min(20, len(missing_alt_report) * 2)

#         # ══════════════════════════════════════
#         # CHECK 2 ─ ARIA label validation
#         # ══════════════════════════════════════
#         interactive_tags  = ["button", "a", "input", "select", "textarea"]
#         interactive_roles = {
#             "button", "link", "menuitem", "tab", "checkbox",
#             "radio", "switch", "option", "combobox"
#         }

#         interactive_els = soup.find_all(interactive_tags)
#         interactive_els += [
#             el for el in soup.find_all(role=True)
#             if el.get("role") in interactive_roles
#         ]
#         # Deduplicate
#         seen = set()
#         unique_interactive = []
#         for el in interactive_els:
#             eid = id(el)
#             if eid not in seen:
#                 seen.add(eid)
#                 unique_interactive.append(el)

#         missing_aria = []
#         for el in unique_interactive:
#             has_aria_label      = bool(el.get("aria-label", "").strip())
#             has_aria_labelledby = bool(el.get("aria-labelledby", "").strip())
#             has_text            = bool(el.get_text(strip=True))
#             has_title           = bool(el.get("title", "").strip())
#             has_placeholder     = bool(el.get("placeholder", "").strip())
#             if not any([has_aria_label, has_aria_labelledby,
#                         has_text, has_title, has_placeholder]):
#                 missing_aria.append(el)

#         details["aria_labels"] = {
#             "total_interactive": len(unique_interactive),
#             "missing_aria"     : len(missing_aria),
#             "snippets"         : [str(el)[:120] for el in missing_aria[:5]]
#         }

#         if missing_aria:
#             issues.append(
#                 f"[ARIA] {len(missing_aria)}/{len(unique_interactive)} "
#                 "interactive elements missing accessible labels"
#             )
#             score -= min(15, len(missing_aria) * 2)

#         # ══════════════════════════════════════
#         # CHECK 3 ─ Form label validation
#         # ══════════════════════════════════════
#         SKIP_INPUT_TYPES = {"hidden", "submit", "button", "image", "reset"}
#         inputs = [
#             inp for inp in soup.find_all("input")
#             if inp.get("type", "text").lower() not in SKIP_INPUT_TYPES
#         ]
#         inputs += soup.find_all(["select", "textarea"])

#         unlabeled_inputs = []

#         for inp in inputs:
#             input_id = inp.get("id")

#             has_explicit_label = (
#                 bool(input_id) and bool(soup.find("label", attrs={"for": input_id}))
#             )
#             has_wrapping_label = bool(inp.find_parent("label"))
#             has_aria = (
#                 bool(inp.get("aria-label", "").strip()) or
#                 bool(inp.get("aria-labelledby", "").strip())
#             )
#             has_title = bool(inp.get("title", "").strip())

#             if not any([has_explicit_label, has_wrapping_label, has_aria, has_title]):
#                 unlabeled_inputs.append(inp)

#         details["form_labels"] = {
#             "total_inputs"    : len(inputs),
#             "unlabeled_inputs": len(unlabeled_inputs),
#             "snippets"        : [str(inp)[:120] for inp in unlabeled_inputs[:5]]
#         }

#         if unlabeled_inputs:
#             issues.append(
#                 f"[FORM] {len(unlabeled_inputs)}/{len(inputs)} form inputs missing labels"
#             )
#             score -= min(15, len(unlabeled_inputs) * 3)

#         # ══════════════════════════════════════
#         # CHECK 4 ─ Semantic HTML structure
#         # ══════════════════════════════════════
#         SEMANTIC_TAGS = {
#             "header"  : "Page header landmark",
#             "nav"     : "Navigation landmark",
#             "main"    : "Main content landmark",
#             "footer"  : "Page footer landmark",
#             "section" : "Sectioning content",
#             "article" : "Independent content block",
#             "aside"   : "Complementary content",
#         }

#         ROLE_EQUIVALENTS = {
#             "header" : "banner",
#             "nav"    : "navigation",
#             "main"   : "main",
#             "footer" : "contentinfo",
#             "aside"  : "complementary",
#         }

#         missing_semantic = []
#         present_semantic = []

#         for tag, description in SEMANTIC_TAGS.items():
#             found_tag  = bool(soup.find(tag))
#             role_eq    = ROLE_EQUIVALENTS.get(tag)
#             found_role = bool(soup.find(attrs={"role": role_eq})) if role_eq else False

#             if found_tag or found_role:
#                 present_semantic.append(tag)
#             else:
#                 missing_semantic.append(f"<{tag}> ({description})")

#         details["semantic_structure"] = {
#             "present": present_semantic,
#             "missing": missing_semantic,
#         }

#         if missing_semantic:
#             issues.append(
#                 "[SEMANTIC] Missing tags: " + ", ".join(missing_semantic)
#             )
#             score -= 10

#         # ══════════════════════════════════════
#         # CHECK 5 ─ Color Contrast (WCAG 2.1 AA)
#         # ══════════════════════════════════════
#         # Normal text  → 4.5 : 1 minimum
#         # Large text   → 3.0 : 1 minimum  (≥18pt or ≥14pt bold)
#         THRESHOLD_NORMAL = 4.5
#         THRESHOLD_LARGE  = 3.0

#         styled_elements = soup.find_all(style=True)
#         contrast_issues = []

#         for el in styled_elements:
#             style  = el.get("style", "")
#             fg_hex = parse_hex_color(style, "color")
#             bg_hex = parse_hex_color(style, "background-color")

#             if fg_hex and bg_hex:
#                 ratio = contrast_ratio(fg_hex, bg_hex)

#                 font_size_match   = re.search(r'font-size:\s*([\d.]+)(px|pt|em|rem)', style, re.I)
#                 font_weight_match = re.search(r'font-weight:\s*(bold|[7-9]\d{2})', style, re.I)
#                 is_large_text     = False

#                 if font_size_match:
#                     size    = float(font_size_match.group(1))
#                     unit    = font_size_match.group(2).lower()
#                     size_pt = size * (1 if unit == "pt" else
#                                       0.75 if unit == "px" else 12)
#                     if size_pt >= 18 or (size_pt >= 14 and font_weight_match):
#                         is_large_text = True

#                 threshold       = THRESHOLD_LARGE if is_large_text else THRESHOLD_NORMAL
#                 threshold_label = "large text" if is_large_text else "normal text"

#                 if ratio < threshold:
#                     contrast_issues.append({
#                         "element" : el.name,
#                         "fg"      : f"#{fg_hex}",
#                         "bg"      : f"#{bg_hex}",
#                         "ratio"   : round(ratio, 2),
#                         "required": threshold,
#                         "type"    : threshold_label,
#                         "snippet" : str(el)[:100]
#                     })

#         details["color_contrast"] = {
#             "elements_checked"  : len(styled_elements),
#             "contrast_failures" : len(contrast_issues),
#             "failures"          : contrast_issues[:10]
#         }

#         if contrast_issues:
#             issues.append(
#                 f"[CONTRAST] {len(contrast_issues)} element(s) fail WCAG AA contrast ratio"
#             )
#             score -= min(10, len(contrast_issues) * 2)

#         # ──────────────────────────────────────
#         # Final result
#         # ──────────────────────────────────────
#         return {
#             "type"   : "Accessibility",
#             "url"    : url,
#             "score"  : max(score, 0),
#             "grade"  : (
#                 "A" if score >= 90 else
#                 "B" if score >= 75 else
#                 "C" if score >= 60 else
#                 "D" if score >= 40 else "F"
#             ),
#             "issues" : issues if issues else ["✅ No major accessibility issues detected"],
#             "details": details
#         }

#     except Exception as e:

#         return {
#             "error": f"Accessibility analysis failed: {str(e)}"
#         }
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ─────────────────────────────────────────────
# WCAG 2.1 Color Contrast Helpers
# ─────────────────────────────────────────────

def hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.strip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def relative_luminance(rgb: tuple) -> float:
    def linearize(c):
        c /= 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)


def contrast_ratio(hex1: str, hex2: str) -> float:
    lum1 = relative_luminance(hex_to_rgb(hex1))
    lum2 = relative_luminance(hex_to_rgb(hex2))
    lighter = max(lum1, lum2)
    darker  = min(lum1, lum2)
    return (lighter + 0.05) / (darker + 0.05)


def parse_color_to_hex(style: str, prop: str) -> str | None:
    """
    Parse a CSS color value from an inline style string.
    Supports: #rrggbb, #rgb, rgb(r,g,b), rgba(r,g,b,a).
    Returns 6-digit lowercase hex or None.
    """
    hex_pattern = rf'{prop}\s*:\s*#([0-9a-fA-F]{{3}}(?:[0-9a-fA-F]{{3}})?)\b'
    hex_match = re.search(hex_pattern, style, re.IGNORECASE)
    if hex_match:
        raw = hex_match.group(1)
        if len(raw) == 3:
            raw = "".join(c * 2 for c in raw)
        return raw.lower()

    rgb_pattern = rf'{prop}\s*:\s*rgba?\(\s*(\d{{1,3}})\s*,\s*(\d{{1,3}})\s*,\s*(\d{{1,3}})'
    rgb_match = re.search(rgb_pattern, style, re.IGNORECASE)
    if rgb_match:
        r, g, b = (min(255, int(rgb_match.group(i))) for i in (1, 2, 3))
        return f"{r:02x}{g:02x}{b:02x}"

    return None


def parse_computed_rgb(color_str: str) -> str | None:
    """Parse a computed style color string (rgb/rgba) to hex. Returns None for transparent."""
    if not color_str or color_str.strip() in ("transparent", "inherit", "initial", ""):
        return None
    rgba_match = re.match(r'rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d.]+)\s*\)', color_str.strip())
    if rgba_match:
        if float(rgba_match.group(4)) == 0:
            return None  # fully transparent
        r, g, b = int(rgba_match.group(1)), int(rgba_match.group(2)), int(rgba_match.group(3))
        return f"{r:02x}{g:02x}{b:02x}"
    rgb_match = re.match(r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', color_str.strip())
    if rgb_match:
        r, g, b = int(rgb_match.group(1)), int(rgb_match.group(2)), int(rgb_match.group(3))
        return f"{r:02x}{g:02x}{b:02x}"
    return parse_color_to_hex(f"color:{color_str}", "color")


def _is_large_text(font_size_str: str, font_weight_str: str) -> bool:
    """Return True if element qualifies as large text per WCAG (≥18pt or ≥14pt bold)."""
    if not font_size_str:
        return False
    fs_match = re.match(r'([\d.]+)(px|pt)', font_size_str.strip())
    if not fs_match:
        return False
    size_pt = float(fs_match.group(1)) * (1 if fs_match.group(2) == "pt" else 0.75)
    bold = font_weight_str in ("bold", "700", "800", "900") or \
           (font_weight_str.isdigit() and int(font_weight_str) >= 700)
    return size_pt >= 18 or (size_pt >= 14 and bold)


def _has_accessible_label(el, soup=None) -> bool:
    """
    Unified WCAG-compliant label check.
    Accepts: aria-labelledby (resolved), aria-label, <label for=id>,
             wrapping <label>, title.
    Deliberately does NOT accept: placeholder (WCAG 2.1 Failure F65).
    Text content is NOT checked here — callers handle it per-element-type.
    """
    # 1. aria-labelledby — resolve referenced element
    labelledby = el.get("aria-labelledby", "").strip()
    if labelledby and soup:
        ref_el = soup.find(id=labelledby)
        if ref_el and ref_el.get_text(strip=True):
            return True
    elif labelledby:
        return True  # can't resolve, assume present

    # 2. aria-label
    if el.get("aria-label", "").strip():
        return True

    # 3. Explicit <label for="id">
    if soup:
        el_id = el.get("id")
        if el_id and soup.find("label", attrs={"for": el_id}):
            return True

    # 4. Wrapping <label>
    if el.find_parent("label"):
        return True

    # 5. title attribute
    if el.get("title", "").strip():
        return True

    return False


# ─────────────────────────────────────────────
# Main Analyzer
# ─────────────────────────────────────────────

def accessibility_analyzer(url: str, browser=None) -> dict:

    try:

        # ─────────────────────────────────────
        # Load page using Playwright
        # ─────────────────────────────────────
        def run_page_logic(b):
            page = b.new_page()
            page.goto(url, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(1000)

            # Pull computed styles for accurate contrast checking
            # This captures CSS-class-based colors that inline parsing misses
            computed_styles = page.evaluate("""() => {
                const TEXT_TAGS = new Set(['p','span','h1','h2','h3','h4','h5','h6',
                    'a','li','td','th','label','button','div','section','article',
                    'header','footer','nav','aside','main']);
                const results = [];
                const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT);
                let count = 0;
                while (walker.nextNode() && count < 300) {
                    const el = walker.currentNode;
                    if (!TEXT_TAGS.has(el.tagName.toLowerCase())) continue;
                    const text = (el.innerText || '').trim();
                    if (!text) continue;
                    const cs = window.getComputedStyle(el);
                    results.push({
                        tag       : el.tagName.toLowerCase(),
                        fg        : cs.color,
                        bg        : cs.backgroundColor,
                        fontSize  : cs.fontSize,
                        fontWeight: cs.fontWeight,
                        text      : text.slice(0, 40)
                    });
                    count++;
                }
                return results;
            }""")

            html = page.content()
            page.close()
            return html, computed_styles

        if browser:
            html, computed_styles = run_page_logic(browser)
        else:
            with sync_playwright() as p:
                temp_browser = p.chromium.launch(headless=True)
                html, computed_styles = run_page_logic(temp_browser)
                temp_browser.close()

        soup   = BeautifulSoup(html, "html.parser")
        issues  = []
        details = {}
        score   = 100

        # ══════════════════════════════════════
        # CHECK 1 — Missing ALT / Text Alternatives
        # ══════════════════════════════════════

        missing_alt_report = []

        for img in soup.find_all("img"):
            alt = img.get("alt")
            is_decorative = (
                img.get("role") == "presentation" or
                img.get("aria-hidden") == "true"
            )
            if not is_decorative:
                if alt is None:
                    missing_alt_report.append({"tag": "img", "issue": "Missing alt attribute entirely",          "snippet": str(img)[:120]})
                elif alt.strip() == "":
                    missing_alt_report.append({"tag": "img", "issue": "Empty alt on non-decorative image",       "snippet": str(img)[:120]})

        for area in soup.find_all("area"):
            if not area.get("alt", "").strip() and area.get("href"):
                missing_alt_report.append({"tag": "area",           "issue": "Linked <area> missing alt",        "snippet": str(area)[:120]})

        for inp in soup.find_all("input", attrs={"type": "image"}):
            if not inp.get("alt", "").strip():
                missing_alt_report.append({"tag": "input[type=image]", "issue": "Image input missing alt",       "snippet": str(inp)[:120]})

        for video in soup.find_all("video"):
            has_caption = any(t.get("kind","").lower() in ("captions","subtitles") for t in video.find_all("track"))
            has_aria    = bool(video.get("aria-label","").strip()) or bool(video.get("aria-labelledby","").strip())
            if not has_caption and not has_aria:
                missing_alt_report.append({"tag": "video",          "issue": "Video missing captions track",     "snippet": str(video)[:120]})

        for audio in soup.find_all("audio"):
            has_track = bool(audio.find("track"))
            has_aria  = bool(audio.get("aria-label","").strip()) or bool(audio.get("aria-labelledby","").strip())
            has_title = bool(audio.get("title","").strip())
            if not any([has_track, has_aria, has_title]):
                missing_alt_report.append({"tag": "audio",          "issue": "Audio missing accessible label",   "snippet": str(audio)[:120]})

        for canvas in soup.find_all("canvas"):
            has_aria     = bool(canvas.get("aria-label","").strip()) or bool(canvas.get("aria-labelledby","").strip())
            has_fallback = bool(canvas.get_text(strip=True))
            has_role     = bool(canvas.get("role","").strip())
            if not any([has_aria, has_fallback, has_role]):
                missing_alt_report.append({"tag": "canvas",         "issue": "Canvas missing aria-label",        "snippet": str(canvas)[:120]})

        for svg in soup.find_all("svg"):
            if svg.get("aria-hidden") != "true":
                has_title = bool(svg.find("title"))
                has_aria  = bool(svg.get("aria-label","").strip()) or bool(svg.get("aria-labelledby","").strip())
                if not has_title and not has_aria:
                    missing_alt_report.append({"tag": "svg",        "issue": "SVG missing <title> or aria-label","snippet": str(svg)[:120]})

        for obj in soup.find_all("object"):
            has_fallback = bool(obj.get_text(strip=True))
            has_aria     = bool(obj.get("aria-label","").strip()) or bool(obj.get("aria-labelledby","").strip())
            has_title    = bool(obj.get("title","").strip())
            if not any([has_fallback, has_aria, has_title]):
                missing_alt_report.append({"tag": "object",         "issue": "Object missing fallback/label",    "snippet": str(obj)[:120]})

        for embed in soup.find_all("embed"):
            has_aria  = bool(embed.get("aria-label","").strip()) or bool(embed.get("aria-labelledby","").strip())
            has_title = bool(embed.get("title","").strip())
            if not has_aria and not has_title:
                missing_alt_report.append({"tag": "embed",          "issue": "Embed missing aria-label/title",   "snippet": str(embed)[:120]})

        for iframe in soup.find_all("iframe"):
            has_title = bool(iframe.get("title","").strip())
            has_aria  = bool(iframe.get("aria-label","").strip()) or bool(iframe.get("aria-labelledby","").strip())
            if not has_title and not has_aria:
                missing_alt_report.append({"tag": "iframe",         "issue": "Iframe missing title/aria-label",  "snippet": str(iframe)[:120]})

        by_tag = {}
        for r in missing_alt_report:
            by_tag.setdefault(r["tag"], []).append(r["issue"])

        details["missing_alt"] = {
            "total_violations": len(missing_alt_report),
            "by_tag"          : by_tag,
            "snippets"        : [r["snippet"] for r in missing_alt_report[:10]]
        }

        if missing_alt_report:
            tag_summary = ", ".join(f"{tag}×{len(v)}" for tag, v in by_tag.items())
            issues.append(f"[ALT] {len(missing_alt_report)} element(s) missing text alternatives — {tag_summary}")
            score -= min(20, len(missing_alt_report) * 2)

        # ══════════════════════════════════════
        # CHECK 2 — ARIA label validation
        # FIX: Scope to button/<a href> only (not form inputs — those handled in Check 3)
        # FIX: Use _has_accessible_label() — respects <label for=id>, no placeholder
        # FIX: <a> without href excluded (not keyboard-focusable per WCAG)
        # ══════════════════════════════════════

        INTERACTIVE_ROLES = {
            "button", "link", "menuitem", "tab", "checkbox",
            "radio", "switch", "option", "combobox"
        }

        aria_candidates = []
        for el in soup.find_all("button"):
            aria_candidates.append(el)
        for el in soup.find_all("a"):
            if el.get("href") is not None:   # only anchors with href are interactive
                aria_candidates.append(el)
        for el in soup.find_all(attrs={"role": True}):
            if el.get("role") in INTERACTIVE_ROLES:
                aria_candidates.append(el)

        seen = set()
        unique_aria = []
        for el in aria_candidates:
            eid = id(el)
            if eid not in seen:
                seen.add(eid)
                unique_aria.append(el)

        missing_aria = []
        for el in unique_aria:
            has_text = bool(el.get_text(strip=True))   # text content valid for button/a
            if not _has_accessible_label(el, soup) and not has_text:
                missing_aria.append(el)

        details["aria_labels"] = {
            "total_interactive": len(unique_aria),
            "missing_aria"     : len(missing_aria),
            "snippets"         : [str(el)[:120] for el in missing_aria[:5]]
        }

        if missing_aria:
            issues.append(
                f"[ARIA] {len(missing_aria)}/{len(unique_aria)} "
                "interactive elements missing accessible labels"
            )
            score -= min(15, len(missing_aria) * 2)

        # ══════════════════════════════════════
        # CHECK 3 — Form label validation
        # FIX: Use _has_accessible_label() — no placeholder, respects <label for=id>
        # ══════════════════════════════════════

        SKIP_INPUT_TYPES = {"hidden", "submit", "button", "image", "reset"}
        inputs = [
            inp for inp in soup.find_all("input")
            if inp.get("type", "text").lower() not in SKIP_INPUT_TYPES
        ]
        inputs += soup.find_all(["select", "textarea"])

        unlabeled_inputs = []
        for inp in inputs:
            if not _has_accessible_label(inp, soup):
                unlabeled_inputs.append(inp)

        details["form_labels"] = {
            "total_inputs"    : len(inputs),
            "unlabeled_inputs": len(unlabeled_inputs),
            "snippets"        : [str(inp)[:120] for inp in unlabeled_inputs[:5]]
        }

        if unlabeled_inputs:
            issues.append(f"[FORM] {len(unlabeled_inputs)}/{len(inputs)} form inputs missing labels")
            score -= min(15, len(unlabeled_inputs) * 3)

        # ══════════════════════════════════════
        # CHECK 4 — Semantic HTML structure
        # ══════════════════════════════════════

        SEMANTIC_TAGS = {
            "header" : "Page header landmark",
            "nav"    : "Navigation landmark",
            "main"   : "Main content landmark",
            "footer" : "Page footer landmark",
            "section": "Sectioning content",
            "article": "Independent content block",
            "aside"  : "Complementary content",
        }
        ROLE_EQUIVALENTS = {
            "header": "banner",
            "nav"   : "navigation",
            "main"  : "main",
            "footer": "contentinfo",
            "aside" : "complementary",
        }

        missing_semantic = []
        present_semantic = []

        for tag, description in SEMANTIC_TAGS.items():
            found_tag  = bool(soup.find(tag))
            role_eq    = ROLE_EQUIVALENTS.get(tag)
            found_role = bool(soup.find(attrs={"role": role_eq})) if role_eq else False
            if found_tag or found_role:
                present_semantic.append(tag)
            else:
                missing_semantic.append(f"<{tag}> ({description})")

        details["semantic_structure"] = {
            "present": present_semantic,
            "missing": missing_semantic,
        }

        if missing_semantic:
            issues.append("[SEMANTIC] Missing tags: " + ", ".join(missing_semantic))
            score -= 10

        # ══════════════════════════════════════
        # CHECK 5 — Color Contrast (WCAG 2.1 AA)
        # FIX: Use computed styles from Playwright — captures CSS class colors
        # FIX: parse_color_to_hex() now handles rgb() and rgba()
        # FIX: Fully transparent backgrounds skipped
        # FIX: Deduplication prevents duplicate fg/bg pair reports
        # ══════════════════════════════════════

        THRESHOLD_NORMAL = 4.5
        THRESHOLD_LARGE  = 3.0

        contrast_issues    = []
        seen_contrast_keys = set()

        # Pass 1: computed styles (CSS class colors from Playwright)
        for item in computed_styles:
            fg_hex = parse_computed_rgb(item.get("fg", ""))
            bg_hex = parse_computed_rgb(item.get("bg", ""))
            if not fg_hex or not bg_hex:
                continue
            dedup_key = f"{fg_hex}|{bg_hex}"
            if dedup_key in seen_contrast_keys:
                continue
            seen_contrast_keys.add(dedup_key)

            ratio  = contrast_ratio(fg_hex, bg_hex)
            large  = _is_large_text(item.get("fontSize",""), item.get("fontWeight",""))
            thresh = THRESHOLD_LARGE if large else THRESHOLD_NORMAL

            if ratio < thresh:
                contrast_issues.append({
                    "element"    : item["tag"],
                    "fg"         : f"#{fg_hex}",
                    "bg"         : f"#{bg_hex}",
                    "ratio"      : round(ratio, 2),
                    "required"   : thresh,
                    "type"       : "large text" if large else "normal text",
                    "text_sample": item.get("text", "")[:40],
                    "source"     : "computed"
                })

        # Pass 2: inline styles (catches any elements missed by tree walker)
        for el in soup.find_all(style=True):
            style  = el.get("style", "")
            fg_hex = parse_color_to_hex(style, "color")
            bg_hex = parse_color_to_hex(style, "background-color")
            if not fg_hex or not bg_hex:
                continue
            dedup_key = f"{fg_hex}|{bg_hex}"
            if dedup_key in seen_contrast_keys:
                continue
            seen_contrast_keys.add(dedup_key)

            ratio = contrast_ratio(fg_hex, bg_hex)
            fs_match = re.search(r'font-size:\s*([\d.]+)(px|pt|em|rem)', style, re.I)
            fw_match = re.search(r'font-weight:\s*(bold|[7-9]\d{2})', style, re.I)
            large = False
            if fs_match:
                size = float(fs_match.group(1)); unit = fs_match.group(2).lower()
                size_pt = size if unit=="pt" else (size * 0.75 if unit=="px" else size * 12)
                if size_pt >= 18 or (size_pt >= 14 and fw_match):
                    large = True
            thresh = THRESHOLD_LARGE if large else THRESHOLD_NORMAL
            if ratio < thresh:
                contrast_issues.append({
                    "element" : el.name,
                    "fg"      : f"#{fg_hex}",
                    "bg"      : f"#{bg_hex}",
                    "ratio"   : round(ratio, 2),
                    "required": thresh,
                    "type"    : "large text" if large else "normal text",
                    "source"  : "inline"
                })

        details["color_contrast"] = {
            "elements_checked"  : len(computed_styles) + len(soup.find_all(style=True)),
            "contrast_failures" : len(contrast_issues),
            "failures"          : contrast_issues[:10]
        }

        if contrast_issues:
            issues.append(f"[CONTRAST] {len(contrast_issues)} element(s) fail WCAG AA contrast ratio")
            score -= min(10, len(contrast_issues) * 2)

        # ──────────────────────────────────────
        # Final result
        # ──────────────────────────────────────
        final_score = max(score, 0)
        return {
            "type"   : "Accessibility",
            "url"    : url,
            "score"  : final_score,
            "grade"  : (
                "A" if final_score >= 90 else
                "B" if final_score >= 75 else
                "C" if final_score >= 60 else
                "D" if final_score >= 40 else "F"
            ),
            "issues" : issues if issues else ["✅ No major accessibility issues detected"],
            "details": details
        }

    except Exception as e:
        import traceback
        return {
            "error"    : f"Accessibility analysis failed: {str(e)}",
            "traceback": traceback.format_exc()
        }