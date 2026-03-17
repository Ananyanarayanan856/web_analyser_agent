# # # app/tools/seo.py

# # import time
# # import requests
# # from bs4 import BeautifulSoup
# # from urllib.parse import urlparse
# # from collections import Counter
# # import re
# # import urllib3
# # from playwright.sync_api import sync_playwright

# # urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# # STOPWORDS = {
# #     "the","and","a","to","of","in","i","is","that","it","on","you","this","for","but","with",
# #     "are","have","be","at","or","as","was","so","if","out","not","we","my","by","all","what",
# #     "can","an","your","from","up","about","which","there","has","more","when","will","do",
# #     "how","their","they","its"
# # }


# # def seo_analyzer(url: str):

# #     try:

# #         # -----------------------------
# #         # PERFORMANCE ANALYSIS (PLAYWRIGHT)
# #         # -----------------------------
# #         with sync_playwright() as p:

# #             browser = p.chromium.launch(headless=True)
# #             page = browser.new_page()

# #             start_time = time.time()

# #             response = page.goto(url, wait_until="load", timeout=30000)

# #             total_load_time = time.time() - start_time

# #             # Browser performance metrics
# #             perf = page.evaluate(
# #                 """() => {
# #                     const perf = window.performance;
# #                     const timing = perf.timing;

# #                     return {
# #                         ttfb: timing.responseStart - timing.requestStart,
# #                         domInteractive: timing.domInteractive - timing.navigationStart,
# #                         loadEventEnd: timing.loadEventEnd - timing.navigationStart
# #                     }
# #                 }"""
# #             )

# #             # Core Web Vitals
# #             web_vitals = page.evaluate(
# #                 """() => {
# #                     let fcp = 0;
# #                     let lcp = 0;

# #                     const paints = performance.getEntriesByType('paint');
# #                     paints.forEach(p => {
# #                         if (p.name === 'first-contentful-paint') {
# #                             fcp = p.startTime;
# #                         }
# #                     });

# #                     const lcpEntries = performance.getEntriesByType('largest-contentful-paint');
# #                     if (lcpEntries.length > 0) {
# #                         lcp = lcpEntries[lcpEntries.length - 1].startTime;
# #                     }

# #                     return {fcp, lcp};
# #                 }"""
# #             )

# #             html = page.content()

# #             browser.close()

# #         soup = BeautifulSoup(html, "html.parser")

# #         issues = []
# #         score = 100

# #         # -----------------------------
# #         # META TITLE
# #         # -----------------------------
# #         title = soup.title.get_text(strip=True) if soup.title else None

# #         if not title:
# #             issues.append("Missing meta title")
# #             score -= 10

# #         elif len(title) < 30 or len(title) > 60:
# #             issues.append("Meta title length should be 30–60 characters")
# #             score -= 5


# #         # -----------------------------
# #         # META DESCRIPTION
# #         # -----------------------------
# #         desc_tag = soup.find("meta", attrs={"name": "description"})
# #         description = desc_tag.get("content") if desc_tag else None

# #         if not description:
# #             issues.append("Missing meta description")
# #             score -= 10

# #         elif len(description) < 120 or len(description) > 160:
# #             issues.append("Meta description length should be 120–160 characters")
# #             score -= 5


# #         # -----------------------------
# #         # HEADER STRUCTURE
# #         # -----------------------------
# #         h1_tags = soup.find_all("h1")
# #         h2_tags = soup.find_all("h2")
# #         h3_to_h6 = soup.find_all(["h3","h4","h5","h6"])

# #         if len(h1_tags) == 0:
# #             issues.append("Missing H1 tag")
# #             score -= 10

# #         elif len(h1_tags) > 1:
# #             issues.append(f"Multiple H1 tags detected ({len(h1_tags)})")
# #             score -= 5

# #         if not h2_tags and h3_to_h6:
# #             issues.append("Header hierarchy issue: H3-H6 used without H2")
# #             score -= 5


# #         # -----------------------------
# #         # KEYWORD DENSITY
# #         # -----------------------------
# #         text = soup.get_text(separator=" ").lower()

# #         words = re.findall(r'\b[a-z]{3,}\b', text)
# #         filtered_words = [w for w in words if w not in STOPWORDS]

# #         keyword_analysis = []

# #         if filtered_words:

# #             total_words = len(filtered_words)
# #             counter = Counter(filtered_words)

# #             top_keywords = counter.most_common(5)

# #             for word, count in top_keywords:

# #                 density = (count / total_words) * 100

# #                 keyword_analysis.append({
# #                     "keyword": word,
# #                     "density": round(density,2)
# #                 })

# #                 if density > 8:
# #                     issues.append(f"Possible keyword stuffing for '{word}' ({density:.2f}%)")
# #                     score -= 10


# #         # -----------------------------
# #         # IMAGE ALT ATTRIBUTES
# #         # -----------------------------
# #         images = soup.find_all("img")

# #         missing_alt = [img for img in images if not img.get("alt")]

# #         if missing_alt:
# #             issues.append(
# #                 f"{len(missing_alt)} images missing ALT attributes out of {len(images)} images"
# #             )
# #             score -= min(10, len(missing_alt)*2)


# #         # -----------------------------
# #         # SITEMAP DETECTION
# #         # -----------------------------
# #         try:

# #             parsed = urlparse(url)
# #             base = f"{parsed.scheme}://{parsed.netloc}"

# #             sitemap = requests.head(f"{base}/sitemap.xml", timeout=5, verify=False)

# #             if sitemap.status_code >= 400:
# #                 issues.append("sitemap.xml not detected")

# #         except Exception:
# #             pass


# #         # -----------------------------
# #         # PERFORMANCE METRICS
# #         # -----------------------------
# #         performance = {
# #             "TTFB": round(perf["ttfb"]/1000,3),
# #             "FCP": round(web_vitals["fcp"]/1000,3),
# #             "LCP": round(web_vitals["lcp"]/1000,3),
# #             "DOM Interactive": round(perf["domInteractive"]/1000,3),
# #             "Total Page Load Time": round(total_load_time,3)
# #         }


# #         return {

# #             "type": "SEO",

# #             "score": max(score,0),

# #             "performance": performance,

# #             "top_keywords": keyword_analysis,

# #             "issues": issues if issues else ["No major SEO issues found"]

# #         }


# #     except Exception as e:
# #         return {"error": f"SEO analysis failed: {str(e)}"}
# # app/tools/seo.py

# import time
# import requests
# from bs4 import BeautifulSoup
# from urllib.parse import urlparse
# from collections import Counter
# import re
# import urllib3
# from playwright.sync_api import sync_playwright

# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# STOPWORDS = {
#     "the","and","a","to","of","in","i","is","that","it","on","you","this","for","but","with",
#     "are","have","be","at","or","as","was","so","if","out","not","we","my","by","all","what",
#     "can","an","your","from","up","about","which","there","has","more","when","will","do",
#     "how","their","they","its","also","been","were","had","he","she","his","her","him","them",
#     "than","then","no","just","into","over","such","these","those","would","could","should"
# }

# # ─────────────────────────────────────────────
# # Core Web Vitals Thresholds  (Google 2024)
# # ─────────────────────────────────────────────
# # LCP  : ≤2.5s good, ≤4.0s needs improvement, >4.0s poor
# # FCP  : ≤1.8s good, ≤3.0s needs improvement, >3.0s poor
# # TTFB : ≤0.8s good, ≤1.8s needs improvement, >1.8s poor
# # TBT  : ≤200ms good (proxy for FID/INP)

# CWV_THRESHOLDS = {
#     "LCP" : {"good": 2.5,  "poor": 4.0,  "unit": "s"},
#     "FCP" : {"good": 1.8,  "poor": 3.0,  "unit": "s"},
#     "TTFB": {"good": 0.8,  "poor": 1.8,  "unit": "s"},
#     "TBT" : {"good": 0.2,  "poor": 0.6,  "unit": "s"},
#     "DOM_Interactive": {"good": 3.8, "poor": 7.3, "unit": "s"},
# }


# def _cwv_rating(metric: str, value_seconds: float) -> str:
#     t = CWV_THRESHOLDS.get(metric)
#     if not t:
#         return "n/a"
#     if value_seconds <= t["good"]:
#         return "Good"
#     if value_seconds <= t["poor"]:
#         return "Needs Improvement"
#     return "Poor"


# def seo_analyzer(url: str, browser=None) -> dict:

#     try:

#         # ══════════════════════════════════════
#         # LOAD PAGE  (Playwright)
#         # ══════════════════════════════════════
        
#         def run_page_logic(b):
#             page = b.new_page()
#             start_time = time.time()
#             page.goto(url, wait_until="load", timeout=30000)
            
#             # Wait a few frames for layout/paint to occur 
#             page.wait_for_timeout(1500)
            
#             total_load_time = time.time() - start_time

#             # Navigation timing
#             perf = page.evaluate("""() => {
#                 const t = window.performance.timing;
#                 return {
#                     ttfb          : t.responseStart   - t.requestStart,
#                     domInteractive: t.domInteractive  - t.navigationStart,
#                     loadEventEnd  : t.loadEventEnd    - t.navigationStart
#                 };
#             }""")

#             # Core Web Vitals
#             web_vitals = page.evaluate("""() => {
#                 let fcp = 0, lcp = 0, tbt = 0;

#                 const paints = performance.getEntriesByType('paint');
#                 paints.forEach(p => {
#                     if (p.name === 'first-contentful-paint') fcp = p.startTime;
#                 });

#                 const lcpEntries = performance.getEntriesByType('largest-contentful-paint');
#                 if (lcpEntries.length > 0)
#                     lcp = lcpEntries[lcpEntries.length - 1].startTime;

#                 // TBT  = sum of (long-task blocking time > 50ms)
#                 const longTasks = performance.getEntriesByType('longtask');
#                 longTasks.forEach(t => { tbt += Math.max(0, t.duration - 50); });

#                 return { fcp, lcp, tbt };
#             }""")

#             html = page.content()
#             page.close()
#             return total_load_time, perf, web_vitals, html

#         if browser:
#             total_load_time, perf, web_vitals, html = run_page_logic(browser)
#         else:
#             with sync_playwright() as p:
#                 temp_browser = p.chromium.launch(headless=True)
#                 total_load_time, perf, web_vitals, html = run_page_logic(temp_browser)
#                 temp_browser.close()

#         soup   = BeautifulSoup(html, "html.parser")
#         issues = []
#         score  = 100

#         # ══════════════════════════════════════
#         # CHECK 1 ─ Meta Title
#         # ══════════════════════════════════════
#         # Google truncates at ~60 chars; titles below 50 are too short to rank well.
#         title_tag = soup.title
#         title     = title_tag.get_text(strip=True) if title_tag else None

#         meta_title_detail = {
#             "value"     : title,
#             "length"    : len(title) if title else 0,
#             "optimal"   : "50–60 characters",
#         }

#         if not title:
#             issues.append("[TITLE] Missing meta title")
#             score -= 10
#             meta_title_detail["status"] = "Missing"
#         elif len(title) < 50:
#             issues.append(
#                 f"[TITLE] Too short ({len(title)} chars) — aim for 50–60 characters"
#             )
#             score -= 5
#             meta_title_detail["status"] = "Too Short"
#         elif len(title) > 60:
#             issues.append(
#                 f"[TITLE] Too long ({len(title)} chars) — Google truncates after 60"
#             )
#             score -= 5
#             meta_title_detail["status"] = "Too Long"
#         else:
#             meta_title_detail["status"] = "Good"

#         # ══════════════════════════════════════
#         # CHECK 2 ─ Meta Description
#         # ══════════════════════════════════════
#         desc_tag    = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
#         description = desc_tag.get("content", "").strip() if desc_tag else None

#         meta_desc_detail = {
#             "value"  : description,
#             "length" : len(description) if description else 0,
#             "optimal": "120–160 characters",
#         }

#         if not description:
#             issues.append("[META DESC] Missing meta description")
#             score -= 10
#             meta_desc_detail["status"] = "Missing"
#         elif len(description) < 120:
#             issues.append(
#                 f"[META DESC] Too short ({len(description)} chars) — aim for 120–160"
#             )
#             score -= 5
#             meta_desc_detail["status"] = "Too Short"
#         elif len(description) > 160:
#             issues.append(
#                 f"[META DESC] Too long ({len(description)} chars) — may be truncated in SERPs"
#             )
#             score -= 5
#             meta_desc_detail["status"] = "Too Long"
#         else:
#             meta_desc_detail["status"] = "Good"

#         # ══════════════════════════════════════
#         # CHECK 3 ─ Header Hierarchy  (H1–H6)
#         # ══════════════════════════════════════
#         # Rules:
#         #   • Exactly one H1
#         #   • Headings must not skip levels (e.g. H1 → H3 without H2)
#         #   • H2–H6 must not exist without an H1
#         #   • Capture heading text for the output

#         heading_map = {}
#         for level in range(1, 7):
#             tags = soup.find_all(f"h{level}")
#             heading_map[f"h{level}"] = [t.get_text(strip=True) for t in tags]

#         h1_count = len(heading_map["h1"])

#         header_detail = {tag: texts for tag, texts in heading_map.items()}

#         if h1_count == 0:
#             issues.append("[HEADERS] Missing H1 tag — every page must have exactly one H1")
#             score -= 10
#         elif h1_count > 1:
#             issues.append(
#                 f"[HEADERS] {h1_count} H1 tags found — only one H1 is allowed per page"
#             )
#             score -= 5

#         # Full hierarchy check: detect any level-skipping
#         all_headings = soup.find_all(re.compile(r'^h[1-6]$'))
#         prev_level   = 0
#         hierarchy_ok = True

#         for h in all_headings:
#             level = int(h.name[1])
#             if prev_level > 0 and level > prev_level + 1:
#                 issues.append(
#                     f"[HEADERS] Heading level skipped: H{prev_level} → H{level} "
#                     f'("{h.get_text(strip=True)[:50]}")'
#                 )
#                 score -= 5
#                 hierarchy_ok = False
#             prev_level = level

#         header_detail["hierarchy_valid"] = hierarchy_ok

#         # ══════════════════════════════════════
#         # CHECK 4 ─ Keyword Density & Relevance
#         # ══════════════════════════════════════
#         # Standards:
#         #   • Ideal density: 1–3%
#         #   • >4% triggers a stuffing warning  (old 8% threshold was too lenient)
#         #   • Check if top keywords appear in title / description (relevance)

#         body_text      = soup.get_text(separator=" ").lower()
#         words          = re.findall(r'\b[a-z]{3,}\b', body_text)
#         filtered_words = [w for w in words if w not in STOPWORDS]

#         keyword_analysis = []
#         stuffing_found   = False

#         if filtered_words:
#             total_words  = len(filtered_words)
#             counter      = Counter(filtered_words)
#             top_keywords = counter.most_common(10)  # analyse top 10, report top 5

#             title_lower = (title or "").lower()
#             desc_lower  = (description or "").lower()

#             for word, count in top_keywords[:5]:
#                 density = round((count / total_words) * 100, 2)

#                 in_title = word in title_lower
#                 in_desc  = word in desc_lower

#                 keyword_analysis.append({
#                     "keyword"   : word,
#                     "count"     : count,
#                     "density"   : density,
#                     "in_title"  : in_title,
#                     "in_desc"   : in_desc,
#                     "relevance" : "High" if in_title and in_desc else
#                                   "Medium" if in_title or in_desc else "Low"
#                 })

#                 # Keyword stuffing: >4% is a red flag
#                 if density > 4.0:
#                     issues.append(
#                         f"[KEYWORDS] Possible stuffing: '{word}' appears at {density}% density "
#                         f"(recommended: 1–3%)"
#                     )
#                     score -= min(10, round((density - 4) * 2))
#                     stuffing_found = True

#             # Flag if no top keyword appears in title (relevance gap)
#             top_3_words = [kw["keyword"] for kw in keyword_analysis[:3]]
#             if not any(w in title_lower for w in top_3_words):
#                 issues.append(
#                     "[KEYWORDS] Top content keywords not found in meta title — "
#                     "consider aligning title with main topic"
#                 )
#                 score -= 5

#         # ══════════════════════════════════════
#         # CHECK 5 ─ Image ALT Attributes
#         # ══════════════════════════════════════
#         # Catches both missing alt AND empty alt on non-decorative images

#         images      = soup.find_all("img")
#         missing_alt = []

#         for img in images:
#             alt           = img.get("alt")
#             is_decorative = (
#                 img.get("role") == "presentation" or
#                 img.get("aria-hidden") == "true"
#             )
#             if not is_decorative:
#                 if alt is None or alt.strip() == "":
#                     missing_alt.append(img.get("src", "")[:80])

#         alt_detail = {
#             "total_images"  : len(images),
#             "missing_alt"   : len(missing_alt),
#             "missing_srcs"  : missing_alt[:5]
#         }

#         if missing_alt:
#             issues.append(
#                 f"[ALT] {len(missing_alt)}/{len(images)} images missing ALT attributes"
#             )
#             score -= min(10, len(missing_alt) * 2)

#         # ══════════════════════════════════════
#         # CHECK 6 ─ Sitemap & Robots.txt
#         # ══════════════════════════════════════
#         parsed   = urlparse(url)
#         base_url = f"{parsed.scheme}://{parsed.netloc}"

#         sitemap_detail = {
#             "sitemap_xml"  : None,
#             "robots_txt"   : None,
#             "sitemap_in_robots": False
#         }

#         # ── sitemap.xml ──────────────────────
#         try:
#             sitemap_resp = requests.head(
#                 f"{base_url}/sitemap.xml", timeout=6, verify=False
#             )
#             if sitemap_resp.status_code < 400:
#                 sitemap_detail["sitemap_xml"] = "Found"
#             else:
#                 sitemap_detail["sitemap_xml"] = f"Not found (HTTP {sitemap_resp.status_code})"
#                 issues.append("[SITEMAP] sitemap.xml not found — submit one via Google Search Console")
#                 score -= 5
#         except Exception:
#             sitemap_detail["sitemap_xml"] = "Unreachable"
#             issues.append("[SITEMAP] sitemap.xml could not be reached")

#         # ── robots.txt ────────────────────────
#         try:
#             robots_resp = requests.get(
#                 f"{base_url}/robots.txt", timeout=6, verify=False
#             )
#             if robots_resp.status_code < 400:
#                 robots_content = robots_resp.text
#                 sitemap_detail["robots_txt"] = "Found"

#                 # Check if robots.txt references a sitemap
#                 if re.search(r'^Sitemap:', robots_content, re.MULTILINE | re.IGNORECASE):
#                     sitemap_detail["sitemap_in_robots"] = True
#                 else:
#                     issues.append(
#                         "[ROBOTS] robots.txt found but does not contain a Sitemap: directive"
#                     )
#                     score -= 3

#                 # Check if robots.txt is blocking crawlers
#                 if re.search(r'Disallow:\s*/', robots_content):
#                     issues.append(
#                         "[ROBOTS] robots.txt contains a broad 'Disallow: /' rule — "
#                         "verify crawlers are not being blocked unintentionally"
#                     )
#                     score -= 5

#             else:
#                 sitemap_detail["robots_txt"] = f"Not found (HTTP {robots_resp.status_code})"
#                 issues.append(
#                     "[ROBOTS] robots.txt not found — recommended for all public websites"
#                 )
#                 score -= 5

#         except Exception:
#             sitemap_detail["robots_txt"] = "Unreachable"
#             issues.append("[ROBOTS] robots.txt could not be reached")

#         # ══════════════════════════════════════
#         # CHECK 7 ─ Performance & Core Web Vitals
#         # ══════════════════════════════════════
#         lcp_s   = round(web_vitals["lcp"]  / 1000, 3)
#         fcp_s   = round(web_vitals["fcp"]  / 1000, 3)
#         ttfb_s  = round(perf["ttfb"]       / 1000, 3)
#         tbt_s   = round(web_vitals["tbt"]  / 1000, 3)
#         dom_s   = round(perf["domInteractive"] / 1000, 3)
#         load_s  = round(total_load_time, 3)

#         performance = {
#             "TTFB"             : {"value": ttfb_s, "unit": "s", "rating": _cwv_rating("TTFB", ttfb_s)},
#             "FCP"              : {"value": fcp_s,  "unit": "s", "rating": _cwv_rating("FCP",  fcp_s)},
#             "LCP"              : {"value": lcp_s,  "unit": "s", "rating": _cwv_rating("LCP",  lcp_s)},
#             "TBT"              : {"value": tbt_s,  "unit": "s", "rating": _cwv_rating("TBT",  tbt_s)},
#             "DOM_Interactive"  : {"value": dom_s,  "unit": "s", "rating": _cwv_rating("DOM_Interactive", dom_s)},
#             "Total_Load_Time"  : {"value": load_s, "unit": "s", "rating": "n/a"},
#         }

#         # Deduct score for poor Core Web Vitals
#         for metric, data in performance.items():
#             if data["rating"] == "Poor":
#                 issues.append(
#                     f"[PERF] {metric} is {data['value']}s — Poor "
#                     f"(threshold: {CWV_THRESHOLDS.get(metric, {}).get('poor', '?')}s)"
#                 )
#                 score -= 8
#             elif data["rating"] == "Needs Improvement":
#                 issues.append(
#                     f"[PERF] {metric} is {data['value']}s — Needs Improvement"
#                 )
#                 score -= 4

#         # ──────────────────────────────────────
#         # Final Result
#         # ──────────────────────────────────────
#         return {
#             "type"       : "SEO",
#             "url"        : url,
#             "score"      : max(score, 0),
#             "grade"      : (
#                 "A" if score >= 90 else
#                 "B" if score >= 75 else
#                 "C" if score >= 60 else
#                 "D" if score >= 40 else "F"
#             ),
#             "issues"     : issues if issues else ["✅ No major SEO issues found"],
#             "details"    : {
#                 "meta_title"      : meta_title_detail,
#                 "meta_description": meta_desc_detail,
#                 "headers"         : header_detail,
#                 "keywords"        : keyword_analysis,
#                 "images"          : alt_detail,
#                 "sitemap_robots"  : sitemap_detail,
#             },
#             "performance": performance,
#         }

#     except Exception as e:
#         return {"error": f"SEO analysis failed: {str(e)}"}
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from collections import Counter
import re
import urllib3
from playwright.sync_api import sync_playwright

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

STOPWORDS = {
    "the","and","a","to","of","in","i","is","that","it","on","you","this","for","but","with",
    "are","have","be","at","or","as","was","so","if","out","not","we","my","by","all","what",
    "can","an","your","from","up","about","which","there","has","more","when","will","do",
    "how","their","they","its","also","been","were","had","he","she","his","her","him","them",
    "than","then","no","just","into","over","such","these","those","would","could","should"
}

# ─────────────────────────────────────────────
# Core Web Vitals Thresholds  (Google 2024)
# ─────────────────────────────────────────────
# LCP  : ≤2.5s good, ≤4.0s needs improvement, >4.0s poor
# FCP  : ≤1.8s good, ≤3.0s needs improvement, >3.0s poor
# TTFB : ≤0.8s good, ≤1.8s needs improvement, >1.8s poor
# TBT  : ≤200ms good (proxy for FID/INP)

CWV_THRESHOLDS = {
    "LCP" : {"good": 2.5,  "poor": 4.0,  "unit": "s"},
    "FCP" : {"good": 1.8,  "poor": 3.0,  "unit": "s"},
    "TTFB": {"good": 0.8,  "poor": 1.8,  "unit": "s"},
    "TBT" : {"good": 0.2,  "poor": 0.6,  "unit": "s"},
    "DOM_Interactive": {"good": 3.8, "poor": 7.3, "unit": "s"},
}


def _cwv_rating(metric: str, value_seconds: float) -> str:
    t = CWV_THRESHOLDS.get(metric)
    if not t:
        return "n/a"
    if value_seconds <= t["good"]:
        return "Good"
    if value_seconds <= t["poor"]:
        return "Needs Improvement"
    return "Poor"


def seo_analyzer(url: str, browser=None) -> dict:

    try:

        # ══════════════════════════════════════
        # LOAD PAGE  (Playwright)
        # ══════════════════════════════════════

        def run_page_logic(b):
            page = b.new_page()

            # ── Inject PerformanceObserver BEFORE navigation ──────────────────
            # This is critical: LCP, CLS, and long-task observers must be
            # registered before the page starts loading so no entries are missed.
            page.add_init_script("""
                window.__perf = { lcp: 0, cls: 0, tbt: 0, fcp: 0 };
                try {
                    // LCP
                    new PerformanceObserver((list) => {
                        const entries = list.getEntries();
                        if (entries.length)
                            window.__perf.lcp = entries[entries.length - 1].startTime;
                    }).observe({ type: 'largest-contentful-paint', buffered: true });

                    // CLS
                    new PerformanceObserver((list) => {
                        list.getEntries().forEach(e => {
                            if (!e.hadRecentInput) window.__perf.cls += e.value;
                        });
                    }).observe({ type: 'layout-shift', buffered: true });

                    // Long Tasks → TBT
                    new PerformanceObserver((list) => {
                        list.getEntries().forEach(t => {
                            window.__perf.tbt += Math.max(0, t.duration - 50);
                        });
                    }).observe({ type: 'longtask', buffered: true });
                } catch(e) {}
            """)

            start_time = time.time()
            page.goto(url, wait_until="networkidle", timeout=60000)

            # Extra wait so paint/LCP observers fire after layout
            page.wait_for_timeout(2000)

            total_load_time = time.time() - start_time

            # ── Collect all metrics in one evaluate call ───────────────────────
            metrics = page.evaluate("""() => {
                // ── Navigation Timing API (Level 2 preferred, fallback legacy) ──
                const navEntries = performance.getEntriesByType('navigation');
                let ttfb = 0, domInteractive = 0, loadEventEnd = 0;

                if (navEntries.length) {
                    const nav = navEntries[0];
                    ttfb          = nav.responseStart  - nav.startTime;
                    domInteractive = nav.domInteractive;
                    loadEventEnd  = nav.loadEventEnd;
                } else {
                    // Legacy fallback
                    const t = window.performance.timing;
                    ttfb          = t.responseStart   - t.requestStart;
                    domInteractive = t.domInteractive  - t.navigationStart;
                    loadEventEnd  = t.loadEventEnd    - t.navigationStart;
                }

                // ── FCP from paint entries ──────────────────────────────────
                let fcp = 0;
                performance.getEntriesByType('paint').forEach(p => {
                    if (p.name === 'first-contentful-paint') fcp = p.startTime;
                });

                // ── LCP / TBT from pre-registered observers ─────────────────
                const lcp = window.__perf ? window.__perf.lcp : 0;
                const tbt = window.__perf ? window.__perf.tbt : 0;
                const cls = window.__perf ? window.__perf.cls : 0;

                // ── Headings: all levels in document order ───────────────────
                const headingData = {};
                for (let i = 1; i <= 6; i++) {
                    headingData['h' + i] = Array.from(
                        document.querySelectorAll('h' + i)
                    ).map(h => h.innerText.trim());
                }

                const headingsOrdered = Array.from(
                    document.querySelectorAll('h1,h2,h3,h4,h5,h6')
                ).map(h => ({
                    level : parseInt(h.tagName[1]),
                    text  : h.innerText.trim()
                }));

                // ── Images: full, accurate data ──────────────────────────────
                const images = Array.from(document.images).map(img => ({
                    src        : img.currentSrc || img.getAttribute('src') || '',
                    alt        : img.getAttribute('alt'),          // null = missing, '' = empty
                    hasAlt     : img.hasAttribute('alt'),
                    role       : img.getAttribute('role'),
                    ariaHidden : img.getAttribute('aria-hidden'),
                    width      : img.naturalWidth,
                    height     : img.naturalHeight,
                    complete   : img.complete
                }));

                // ── Meta tags ────────────────────────────────────────────────
                const titleEl = document.querySelector('title');
                const title   = titleEl ? titleEl.innerText.trim() : null;

                const descEl  = document.querySelector('meta[name="description"], meta[name="Description"]');
                const desc    = descEl ? descEl.getAttribute('content') : null;

                // ── Canonical ────────────────────────────────────────────────
                const canonEl  = document.querySelector('link[rel="canonical"]');
                const canonical = canonEl ? canonEl.getAttribute('href') : null;

                // ── Open Graph / Twitter Card ────────────────────────────────
                const ogTitle  = document.querySelector('meta[property="og:title"]');
                const ogDesc   = document.querySelector('meta[property="og:description"]');
                const ogImage  = document.querySelector('meta[property="og:image"]');
                const twCard   = document.querySelector('meta[name="twitter:card"]');

                // ── Body text for keyword analysis ───────────────────────────
                const bodyText = document.body ? document.body.innerText : '';

                return {
                    ttfb, domInteractive, loadEventEnd,
                    fcp, lcp, tbt, cls,
                    headingData, headingsOrdered,
                    images,
                    title, desc, canonical,
                    ogTitle  : ogTitle  ? ogTitle.getAttribute('content')  : null,
                    ogDesc   : ogDesc   ? ogDesc.getAttribute('content')   : null,
                    ogImage  : ogImage  ? ogImage.getAttribute('content')  : null,
                    twCard   : twCard   ? twCard.getAttribute('content')   : null,
                    bodyText
                };
            }""")

            html = page.content()
            page.close()
            return total_load_time, metrics, html

        if browser:
            total_load_time, metrics, html = run_page_logic(browser)
        else:
            with sync_playwright() as p:
                temp_browser = p.chromium.launch(
                    headless=True,
                    args=["--enable-blink-features=LargestContentfulPaint"]
                )
                total_load_time, metrics, html = run_page_logic(temp_browser)
                temp_browser.close()

        soup   = BeautifulSoup(html, "html.parser")
        issues = []
        score  = 100

        # ══════════════════════════════════════
        # CHECK 1 ─ Meta Title
        # ══════════════════════════════════════
        title = metrics.get("title") or ""
        title = title.strip() if title else None

        # Fallback to BeautifulSoup if JS returned nothing
        if not title:
            title_tag = soup.title
            title = title_tag.get_text(strip=True) if title_tag else None

        meta_title_detail = {
            "value"  : title,
            "length" : len(title) if title else 0,
            "optimal": "50–60 characters",
        }

        if not title:
            issues.append("[TITLE] Missing meta title")
            score -= 10
            meta_title_detail["status"] = "Missing"
        elif len(title) < 50:
            issues.append(f"[TITLE] Too short ({len(title)} chars) — aim for 50–60 characters")
            score -= 5
            meta_title_detail["status"] = "Too Short"
        elif len(title) > 60:
            issues.append(f"[TITLE] Too long ({len(title)} chars) — Google truncates after 60")
            score -= 5
            meta_title_detail["status"] = "Too Long"
        else:
            meta_title_detail["status"] = "Good"

        # ══════════════════════════════════════
        # CHECK 2 ─ Meta Description
        # ══════════════════════════════════════
        description = metrics.get("desc")
        if description is not None:
            description = description.strip() or None

        # Fallback to BeautifulSoup
        if not description:
            desc_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
            description = desc_tag.get("content", "").strip() if desc_tag else None

        meta_desc_detail = {
            "value"  : description,
            "length" : len(description) if description else 0,
            "optimal": "120–160 characters",
        }

        if not description:
            issues.append("[META DESC] Missing meta description")
            score -= 10
            meta_desc_detail["status"] = "Missing"
        elif len(description) < 120:
            issues.append(f"[META DESC] Too short ({len(description)} chars) — aim for 120–160")
            score -= 5
            meta_desc_detail["status"] = "Too Short"
        elif len(description) > 160:
            issues.append(f"[META DESC] Too long ({len(description)} chars) — may be truncated in SERPs")
            score -= 5
            meta_desc_detail["status"] = "Too Long"
        else:
            meta_desc_detail["status"] = "Good"

        # ══════════════════════════════════════
        # CHECK 3 ─ Header Hierarchy  (H1–H6)
        # ══════════════════════════════════════
        # Use JS-extracted data (rendered DOM) — more accurate than BeautifulSoup
        # for JS-heavy pages; BS4 used as fallback only.

        js_heading_data    = metrics.get("headingData", {})
        js_headings_ordered = metrics.get("headingsOrdered", [])

        # Build heading_map from JS results; fallback to BS4 per level
        heading_map = {}
        for level in range(1, 7):
            key = f"h{level}"
            js_texts = js_heading_data.get(key)
            if js_texts is not None:
                heading_map[key] = js_texts
            else:
                # BeautifulSoup fallback
                tags = soup.find_all(key)
                heading_map[key] = [t.get_text(strip=True) for t in tags]

        h1_count = len(heading_map.get("h1", []))

        header_detail = {tag: texts for tag, texts in heading_map.items()}
        header_detail["total_headings"] = sum(len(v) for v in heading_map.values())

        if h1_count == 0:
            issues.append("[HEADERS] Missing H1 tag — every page must have exactly one H1")
            score -= 10
        elif h1_count > 1:
            issues.append(f"[HEADERS] {h1_count} H1 tags found — only one H1 is allowed per page")
            score -= 5

        # Hierarchy check using ordered list from JS (or fallback via BS4)
        if js_headings_ordered:
            ordered_headings = js_headings_ordered
        else:
            ordered_headings = [
                {"level": int(h.name[1]), "text": h.get_text(strip=True)}
                for h in soup.find_all(re.compile(r'^h[1-6]$'))
            ]

        prev_level   = 0
        hierarchy_ok = True
        for h in ordered_headings:
            level = h["level"]
            if prev_level > 0 and level > prev_level + 1:
                issues.append(
                    f"[HEADERS] Heading level skipped: H{prev_level} → H{level} "
                    f'("{h["text"][:50]}")'
                )
                score -= 5
                hierarchy_ok = False
            prev_level = level

        header_detail["hierarchy_valid"] = hierarchy_ok

        # ══════════════════════════════════════
        # CHECK 4 ─ Keyword Density & Relevance
        # ══════════════════════════════════════
        # Use rendered body text from JS (captures dynamic content)
        body_text = metrics.get("bodyText", "")
        if not body_text:
            body_text = soup.get_text(separator=" ")

        body_lower     = body_text.lower()
        words          = re.findall(r'\b[a-z]{3,}\b', body_lower)
        filtered_words = [w for w in words if w not in STOPWORDS]

        keyword_analysis = []

        if filtered_words:
            total_words  = len(filtered_words)
            counter      = Counter(filtered_words)
            top_keywords = counter.most_common(10)

            title_lower = (title or "").lower()
            desc_lower  = (description or "").lower()

            for word, count in top_keywords[:5]:
                density = round((count / total_words) * 100, 2)

                in_title = word in title_lower
                in_desc  = word in desc_lower

                keyword_analysis.append({
                    "keyword"  : word,
                    "count"    : count,
                    "density"  : density,
                    "in_title" : in_title,
                    "in_desc"  : in_desc,
                    "relevance": (
                        "High"   if in_title and in_desc else
                        "Medium" if in_title or in_desc  else "Low"
                    )
                })

                if density > 4.0:
                    issues.append(
                        f"[KEYWORDS] Possible stuffing: '{word}' appears at {density}% density "
                        f"(recommended: 1–3%)"
                    )
                    score -= min(10, round((density - 4) * 2))

            top_3_words = [kw["keyword"] for kw in keyword_analysis[:3]]
            if not any(w in title_lower for w in top_3_words):
                issues.append(
                    "[KEYWORDS] Top content keywords not found in meta title — "
                    "consider aligning title with main topic"
                )
                score -= 5

        # ══════════════════════════════════════
        # CHECK 5 ─ Image ALT Attributes
        # ══════════════════════════════════════
        # Use JS image data (rendered DOM, includes lazy-loaded & dynamic images)
        js_images = metrics.get("images", [])

        # Fallback: extract from BeautifulSoup if JS returned nothing
        if not js_images:
            js_images = []
            for img in soup.find_all("img"):
                js_images.append({
                    "src"       : img.get("src", ""),
                    "alt"       : img.get("alt"),          # None = attribute absent
                    "hasAlt"    : img.has_attr("alt"),
                    "role"      : img.get("role"),
                    "ariaHidden": img.get("aria-hidden"),
                    "width"     : 0,
                    "height"    : 0,
                    "complete"  : True,
                })

        total_images = len(js_images)
        missing_alt  = []
        empty_alt    = []
        all_missing_srcs = []

        for img in js_images:
            is_decorative = (
                img.get("role") == "presentation" or
                img.get("ariaHidden") == "true"
            )
            if is_decorative:
                continue

            has_attr = img.get("hasAlt", img.get("alt") is not None)
            alt_val  = img.get("alt")

            src_short = (img.get("src") or "")[:80]

            if not has_attr:
                # alt attribute is completely absent
                missing_alt.append(src_short)
                all_missing_srcs.append(src_short)
            elif alt_val is not None and alt_val.strip() == "":
                # alt="" on non-decorative image
                empty_alt.append(src_short)
                all_missing_srcs.append(src_short)

        alt_detail = {
            "total_images"       : total_images,
            "missing_alt_count"  : len(missing_alt),
            "empty_alt_count"    : len(empty_alt),
            "total_issues"       : len(all_missing_srcs),
            "missing_alt_srcs"   : missing_alt[:10],   # up to 10 examples
            "empty_alt_srcs"     : empty_alt[:10],
        }

        if missing_alt:
            issues.append(
                f"[ALT] {len(missing_alt)}/{total_images} images missing ALT attribute entirely"
            )
            score -= min(10, len(missing_alt) * 2)

        if empty_alt:
            issues.append(
                f"[ALT] {len(empty_alt)}/{total_images} non-decorative images have empty ALT (alt=\"\")"
            )
            score -= min(5, len(empty_alt))

        # ══════════════════════════════════════
        # CHECK 6 ─ Sitemap & Robots.txt
        # ══════════════════════════════════════
        parsed   = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        sitemap_detail = {
            "sitemap_xml"      : None,
            "robots_txt"       : None,
            "sitemap_in_robots": False,
        }

        # ── sitemap.xml ──────────────────────
        try:
            sitemap_resp = requests.head(
                f"{base_url}/sitemap.xml", timeout=8, verify=False,
                allow_redirects=True
            )
            if sitemap_resp.status_code < 400:
                sitemap_detail["sitemap_xml"] = "Found"
            else:
                sitemap_detail["sitemap_xml"] = f"Not found (HTTP {sitemap_resp.status_code})"
                issues.append("[SITEMAP] sitemap.xml not found — submit one via Google Search Console")
                score -= 5
        except Exception as e:
            sitemap_detail["sitemap_xml"] = f"Unreachable ({str(e)[:60]})"
            issues.append("[SITEMAP] sitemap.xml could not be reached")

        # ── robots.txt ────────────────────────
        try:
            robots_resp = requests.get(
                f"{base_url}/robots.txt", timeout=8, verify=False,
                allow_redirects=True
            )
            if robots_resp.status_code < 400:
                robots_content = robots_resp.text
                sitemap_detail["robots_txt"] = "Found"

                if re.search(r'^Sitemap\s*:', robots_content, re.MULTILINE | re.IGNORECASE):
                    sitemap_detail["sitemap_in_robots"] = True
                else:
                    issues.append(
                        "[ROBOTS] robots.txt found but does not contain a Sitemap: directive"
                    )
                    score -= 3

                # Broad disallow check — only flag if it applies to all user-agents
                ua_block = re.findall(
                    r'User-agent:\s*\*.*?(?=User-agent:|\Z)',
                    robots_content,
                    re.DOTALL | re.IGNORECASE
                )
                for block in ua_block:
                    if re.search(r'^Disallow:\s*/\s*$', block, re.MULTILINE):
                        issues.append(
                            "[ROBOTS] robots.txt contains a broad 'Disallow: /' rule — "
                            "verify crawlers are not being blocked unintentionally"
                        )
                        score -= 5
                        break

            else:
                sitemap_detail["robots_txt"] = f"Not found (HTTP {robots_resp.status_code})"
                issues.append("[ROBOTS] robots.txt not found — recommended for all public websites")
                score -= 5

        except Exception as e:
            sitemap_detail["robots_txt"] = f"Unreachable ({str(e)[:60]})"
            issues.append("[ROBOTS] robots.txt could not be reached")

        # ══════════════════════════════════════
        # CHECK 7 ─ Performance & Core Web Vitals
        # ══════════════════════════════════════
        # All values come from the single JS evaluate() call above.
        # PerformanceObserver was injected before navigation → LCP is accurate.

        ttfb_raw = metrics.get("ttfb", 0) or 0
        fcp_raw  = metrics.get("fcp",  0) or 0
        lcp_raw  = metrics.get("lcp",  0) or 0
        tbt_raw  = metrics.get("tbt",  0) or 0
        dom_raw  = metrics.get("domInteractive", 0) or 0

        ttfb_s = round(ttfb_raw / 1000, 3)
        fcp_s  = round(fcp_raw  / 1000, 3)
        lcp_s  = round(lcp_raw  / 1000, 3)
        tbt_s  = round(tbt_raw  / 1000, 3)
        dom_s  = round(dom_raw  / 1000, 3)
        load_s = round(total_load_time, 3)

        # If LCP is 0 but FCP is > 0, use FCP as a proxy (common for simple pages)
        if lcp_s == 0 and fcp_s > 0:
            lcp_s = fcp_s

        performance = {
            "TTFB"           : {"value": ttfb_s, "unit": "s", "rating": _cwv_rating("TTFB", ttfb_s)},
            "FCP"            : {"value": fcp_s,  "unit": "s", "rating": _cwv_rating("FCP",  fcp_s)},
            "LCP"            : {"value": lcp_s,  "unit": "s", "rating": _cwv_rating("LCP",  lcp_s)},
            "TBT"            : {"value": tbt_s,  "unit": "s", "rating": _cwv_rating("TBT",  tbt_s)},
            "DOM_Interactive": {"value": dom_s,  "unit": "s", "rating": _cwv_rating("DOM_Interactive", dom_s)},
            "Total_Load_Time": {"value": load_s, "unit": "s", "rating": "n/a"},
        }

        for metric, data in performance.items():
            if data["rating"] == "Poor":
                issues.append(
                    f"[PERF] {metric} is {data['value']}s — Poor "
                    f"(threshold: {CWV_THRESHOLDS.get(metric, {}).get('poor', '?')}s)"
                )
                score -= 8
            elif data["rating"] == "Needs Improvement":
                issues.append(f"[PERF] {metric} is {data['value']}s — Needs Improvement")
                score -= 4

        # ──────────────────────────────────────
        # Final Result
        # ──────────────────────────────────────
        final_score = max(score, 0)
        return {
            "type"       : "SEO",
            "url"        : url,
            "score"      : final_score,
            "grade"      : (
                "A" if final_score >= 90 else
                "B" if final_score >= 75 else
                "C" if final_score >= 60 else
                "D" if final_score >= 40 else "F"
            ),
            "issues"     : issues if issues else ["✅ No major SEO issues found"],
            "details"    : {
                "meta_title"      : meta_title_detail,
                "meta_description": meta_desc_detail,
                "headers"         : header_detail,
                "keywords"        : keyword_analysis,
                "images"          : alt_detail,
                "sitemap_robots"  : sitemap_detail,
            },
            "performance": performance,
        }

    except Exception as e:
        import traceback
        return {"error": f"SEO analysis failed: {str(e)}", "traceback": traceback.format_exc()}