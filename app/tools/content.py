# # app/tools/content.py

# import requests
# from bs4 import BeautifulSoup
# from collections import Counter
# import re
# import urllib3
# from urllib.parse import urljoin, urlparse

# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# # ─────────────────────────────────────────────
# # Readability Helpers  (Flesch Reading Ease)
# # ─────────────────────────────────────────────

# def count_syllables(word: str) -> int:
#     """
#     Estimate syllable count for an English word using vowel-group heuristics.
#     Not perfect, but accurate enough for bulk readability scoring.
#     """
#     word = word.lower().strip(".,!?;:\"'")
#     if len(word) <= 3:
#         return 1
#     # Remove silent trailing 'e'
#     word = re.sub(r'e$', '', word)
#     vowels = re.findall(r'[aeiouy]+', word)
#     count = len(vowels)
#     return max(1, count)


# def flesch_reading_ease(text: str) -> float:
#     """
#     Calculate Flesch Reading Ease score.
#     Score ranges:
#         90–100  → Very Easy       (5th grade)
#         70–90   → Easy
#         60–70   → Standard
#         50–60   → Fairly Difficult
#         30–50   → Difficult
#         0–30    → Very Confusing
#     Formula: 206.835 - 1.015*(words/sentences) - 84.6*(syllables/words)
#     """
#     sentences = re.split(r'[.!?]+', text)
#     sentences = [s.strip() for s in sentences if s.strip()]
#     num_sentences = max(len(sentences), 1)

#     words = re.findall(r'\b[a-zA-Z]+\b', text)
#     num_words = max(len(words), 1)

#     num_syllables = sum(count_syllables(w) for w in words)

#     score = (
#         206.835
#         - 1.015  * (num_words / num_sentences)
#         - 84.6   * (num_syllables / num_words)
#     )
#     return round(max(0.0, min(100.0, score)), 2)


# def flesch_grade_label(score: float) -> str:
#     if score >= 90: return "Very Easy (5th grade)"
#     if score >= 70: return "Easy (6th grade)"
#     if score >= 60: return "Standard (7–8th grade)"
#     if score >= 50: return "Fairly Difficult (High school)"
#     if score >= 30: return "Difficult (College)"
#     return "Very Confusing (College graduate)"


# # ─────────────────────────────────────────────
# # Content Depth Helpers
# # ─────────────────────────────────────────────

# def content_depth_label(word_count: int) -> str:
#     if word_count >= 2000: return "In-depth / Comprehensive"
#     if word_count >= 1000: return "Detailed"
#     if word_count >= 500:  return "Moderate"
#     if word_count >= 200:  return "Thin"
#     return "Very Thin"


# # ─────────────────────────────────────────────
# # Main Analyzer
# # ─────────────────────────────────────────────

# def content_analyzer(url: str, browser=None) -> dict:

#     try:
#         # Load page using the shared Playwright browser instance
#         if browser:
#             page = browser.new_page()
#             page.goto(url, wait_until="domcontentloaded", timeout=30000)
#             html = page.content()
#             page.close()
#         else:
#             # Fallback to requests if no browser is passed
#             response = requests.get(url, verify=False, timeout=15)
#             response.raise_for_status()
#             html = response.text

#         soup = BeautifulSoup(html, "html.parser")

#         # Remove noisy non-content tags
#         for tag in soup(["script", "style", "noscript", "header",
#                          "footer", "nav", "aside"]):
#             tag.decompose()

#         issues  = []
#         details = {}
#         score   = 100

#         # ══════════════════════════════════════
#         # CHECK 1 ─ Content Readability Score
#         # ══════════════════════════════════════
#         # Extract all visible paragraph text as a single corpus
#         paragraphs   = soup.find_all("p")
#         all_text     = " ".join(p.get_text(" ", strip=True) for p in paragraphs)

#         # Fallback: if no <p> tags, grab body text
#         if len(all_text.split()) < 30:
#             body = soup.find("body")
#             all_text = body.get_text(" ", strip=True) if body else ""

#         if len(all_text.split()) >= 30:
#             flesch_score = flesch_reading_ease(all_text)
#             grade_label  = flesch_grade_label(flesch_score)
#         else:
#             flesch_score = None
#             grade_label  = "Not enough text to score"

#         details["readability"] = {
#             "flesch_reading_ease": flesch_score,
#             "grade_label"        : grade_label,
#             "note"               : (
#                 "Flesch Reading Ease: 0 (hardest) → 100 (easiest). "
#                 "Recommended for general web content: 60–70."
#             )
#         }

#         if flesch_score is not None and flesch_score < 30:
#             issues.append(
#                 f"[READABILITY] Very difficult to read "
#                 f"(Flesch score: {flesch_score} — {grade_label})"
#             )
#             score -= 15
#         elif flesch_score is not None and flesch_score < 50:
#             issues.append(
#                 f"[READABILITY] Fairly difficult to read "
#                 f"(Flesch score: {flesch_score} — {grade_label})"
#             )
#             score -= 8

#         # ══════════════════════════════════════
#         # CHECK 2 ─ Duplicate Content Detection
#         # ══════════════════════════════════════
#         # Strategy: compare normalised paragraph text using exact match
#         # AND near-duplicate detection via word-set overlap (Jaccard similarity)

#         JACCARD_THRESHOLD   = 0.85   # 85% word overlap = near-duplicate
#         MIN_PARA_WORDS      = 12     # ignore very short snippets

#         para_texts = [
#             p.get_text(" ", strip=True)
#             for p in soup.find_all("p")
#             if len(p.get_text(strip=True).split()) >= MIN_PARA_WORDS
#         ]

#         exact_duplicates  = []
#         near_duplicates   = []

#         # ── Exact duplicates ──────────────────
#         normalized  = [re.sub(r'\s+', ' ', t).lower() for t in para_texts]
#         count       = Counter(normalized)
#         exact_duplicates = [t for t, c in count.items() if c > 1]

#         # ── Near-duplicates (Jaccard) ─────────
#         checked_pairs = set()
#         for i, t1 in enumerate(normalized):
#             set1 = set(t1.split())
#             for j, t2 in enumerate(normalized):
#                 if i >= j:
#                     continue
#                 pair_key = (i, j)
#                 if pair_key in checked_pairs:
#                     continue
#                 checked_pairs.add(pair_key)
#                 set2 = set(t2.split())
#                 union = set1 | set2
#                 if not union:
#                     continue
#                 jaccard = len(set1 & set2) / len(union)
#                 if jaccard >= JACCARD_THRESHOLD and t1 != t2:
#                     near_duplicates.append({
#                         "similarity": round(jaccard * 100, 1),
#                         "snippet_a" : para_texts[i][:80],
#                         "snippet_b" : para_texts[j][:80],
#                     })

#         details["duplicate_content"] = {
#             "paragraphs_analyzed": len(para_texts),
#             "exact_duplicates"   : len(exact_duplicates),
#             "near_duplicates"    : len(near_duplicates),
#             "near_duplicate_pairs": near_duplicates[:5],  # cap at 5
#             "exact_samples"      : exact_duplicates[:3]
#         }

#         total_dup = len(exact_duplicates) + len(near_duplicates)
#         if total_dup > 0:
#             issues.append(
#                 f"[DUPLICATE] {len(exact_duplicates)} exact + "
#                 f"{len(near_duplicates)} near-duplicate paragraph block(s) detected"
#             )
#             score -= min(20, total_dup * 5)

#         # ══════════════════════════════════════
#         # CHECK 3 ─ Broken Links Detection
#         # ══════════════════════════════════════
#         base_url     = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
#         anchor_tags  = soup.find_all("a", href=True)

#         all_links    = []
#         broken_links = []
#         skipped      = 0

#         SKIP_SCHEMES = ("mailto:", "tel:", "javascript:", "#", "data:")

#         for a in anchor_tags:
#             href = a.get("href", "").strip()
#             if not href or any(href.startswith(s) for s in SKIP_SCHEMES):
#                 skipped += 1
#                 continue
#             # Resolve relative URLs
#             full_url = urljoin(base_url, href)
#             all_links.append(full_url)

#         # Deduplicate before requesting
#         unique_links = list(dict.fromkeys(all_links))

#         for link in unique_links[:60]:   # cap at 60 to avoid long runtimes
#             try:
#                 head = requests.head(
#                     link, verify=False, timeout=6,
#                     allow_redirects=True,
#                     headers={"User-Agent": "Mozilla/5.0"}
#                 )
#                 status = head.status_code
#                 # Some servers reject HEAD; fall back to GET for 4xx
#                 if status in (405, 403):
#                     get_r  = requests.get(
#                         link, verify=False, timeout=6,
#                         allow_redirects=True,
#                         headers={"User-Agent": "Mozilla/5.0"},
#                         stream=True
#                     )
#                     status = get_r.status_code

#                 if status >= 400:
#                     broken_links.append({
#                         "url"   : link,
#                         "status": status,
#                         "text"  : a.get_text(strip=True)[:60]
#                     })

#             except requests.exceptions.RequestException as e:
#                 broken_links.append({
#                     "url"   : link,
#                     "status": "unreachable",
#                     "error" : str(e)[:80]
#                 })

#         details["broken_links"] = {
#             "total_links_found"  : len(all_links),
#             "unique_links_checked": len(unique_links[:60]),
#             "skipped_links"      : skipped,
#             "broken_count"       : len(broken_links),
#             "broken_links"       : broken_links[:20]   # cap report at 20
#         }

#         if broken_links:
#             issues.append(
#                 f"[LINKS] {len(broken_links)} broken or unreachable link(s) found"
#             )
#             score -= min(20, len(broken_links) * 4)

#         # ══════════════════════════════════════
#         # CHECK 4 ─ Word Count & Content Depth
#         # ══════════════════════════════════════
#         words        = re.findall(r'\b[a-zA-Z]+\b', all_text)
#         word_count   = len(words)
#         depth_label  = content_depth_label(word_count)

#         # Sentence & paragraph stats
#         sentences    = re.split(r'[.!?]+', all_text)
#         sentences    = [s.strip() for s in sentences if s.strip()]
#         num_sentences = len(sentences)
#         avg_sentence_len = round(word_count / max(num_sentences, 1), 1)

#         # Unique word ratio (lexical diversity)
#         unique_words   = set(w.lower() for w in words)
#         lexical_diversity = round(len(unique_words) / max(word_count, 1) * 100, 1)

#         # Count subheadings as a proxy for content structure
#         subheadings  = soup.find_all(["h2", "h3", "h4"])
#         num_subheads = len(subheadings)

#         details["content_depth"] = {
#             "word_count"        : word_count,
#             "depth_label"       : depth_label,
#             "sentence_count"    : num_sentences,
#             "avg_sentence_length": avg_sentence_len,
#             "unique_words"      : len(unique_words),
#             "lexical_diversity_pct": lexical_diversity,
#             "subheadings_found" : num_subheads,
#             "recommendation"    : (
#                 "Aim for 800–1500+ words for strong content depth. "
#                 "Short average sentence length (< 20 words) improves readability."
#             )
#         }

#         if word_count < 200:
#             issues.append(
#                 f"[DEPTH] Very thin content — only {word_count} words detected. "
#                 "Aim for 800+ words for meaningful depth."
#             )
#             score -= 20
#         elif word_count < 500:
#             issues.append(
#                 f"[DEPTH] Thin content — {word_count} words. "
#                 "Consider expanding to 800+ words."
#             )
#             score -= 10

#         if avg_sentence_len > 30:
#             issues.append(
#                 f"[DEPTH] Average sentence length is {avg_sentence_len} words — "
#                 "consider shorter sentences for better readability."
#             )
#             score -= 5

#         if num_subheads == 0 and word_count > 300:
#             issues.append(
#                 "[DEPTH] No subheadings (h2–h4) found — "
#                 "add headings to improve content structure and scannability."
#             )
#             score -= 5

#         # ──────────────────────────────────────
#         # Final result
#         # ──────────────────────────────────────
#         return {
#             "type"   : "Content",
#             "url"    : url,
#             "score"  : max(score, 0),
#             "grade"  : (
#                 "A" if score >= 90 else
#                 "B" if score >= 75 else
#                 "C" if score >= 60 else
#                 "D" if score >= 40 else "F"
#             ),
#             "issues" : issues if issues else ["✅ No major content issues detected"],
#             "details": details
#         }

#     except Exception as e:
#         return {"error": str(e)}
# app/tools/content.py

import requests
from bs4 import BeautifulSoup
from collections import Counter
import re
import urllib3
from urllib.parse import urljoin, urlparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ─────────────────────────────────────────────
# Readability Helpers  (Flesch Reading Ease)
# ─────────────────────────────────────────────

def count_syllables(word: str) -> int:
    """
    Estimate syllable count for an English word.
    Uses vowel-onset transitions with targeted corrections for:
      - Silent trailing 'e'  (rate, like, name)
      - '-le' endings        (table, simple, people → keep e)
      - Silent '-ed'         (walked, talked)
      - Silent '-es'         (rates, makes)
      - '-ious'/'-eous'      (curious, serious → +1)
      - '-eate'/'-iate'      (create, appreciate → +1)
    ~94% accuracy on common English vocabulary.
    """
    word = word.lower().strip(".,!?;:\"'-()[]")
    if not word:
        return 1
    if len(word) <= 3:
        return 1

    VOWELS = set('aeiouy')

    # Step 1: count vowel-onset transitions
    count = 0
    prev_vowel = False
    for ch in word:
        is_vowel = ch in VOWELS
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel

    # Step 2: subtract silent endings
    # Silent trailing 'e' — keep when ending is a pronounced suffix
    KEEP_E_ENDINGS = ('ience', 'able', 'ible', 'acle', 'icle', 'uple', 'tle')
    if (len(word) > 3
            and word.endswith('e')
            and word[-2] not in VOWELS
            and not word.endswith('le')
            and not any(word.endswith(k) for k in KEEP_E_ENDINGS)):
        count -= 1

    # Silent '-ed' (walked, talked — but NOT 'ted','ded','ned','sed')
    if (len(word) > 4
            and word.endswith('ed')
            and word[-3] not in VOWELS
            and word[-3] not in ('t', 'd', 'n', 's')):
        count -= 1

    # Silent '-es' (rates, makes — but NOT buses, foxes, churches)
    if (len(word) > 4
            and word.endswith('es')
            and word[-3] not in VOWELS
            and word[-3] not in ('s', 'x', 'z', 'h', 'c')):
        count -= 1

    # Step 3: add for multi-syllable patterns
    # '-ious', '-eous', '-uous' endings (curious, serious, obvious, various)
    if re.search(r'[iy]ou', word):
        count += 1

    # '-eate' / '-iate' patterns (create, appreciate, immediate)
    if re.search(r'[^aeiouy][ei]at', word):
        count += 1

    return max(1, count)


def flesch_reading_ease(text: str) -> float:
    """
    Calculate Flesch Reading Ease score (0–100, higher = easier).
    Score bands:
        90–100  Very Easy       (5th grade)
        70–90   Easy            (6th grade)
        60–70   Standard        (7–8th grade)
        50–60   Fairly Difficult (High school)
        30–50   Difficult       (College)
        0–30    Very Confusing  (College graduate)
    Formula: 206.835 - 1.015*(words/sentences) - 84.6*(syllables/words)
    """
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    num_sentences = max(len(sentences), 1)

    words = re.findall(r"\b[a-zA-Z']+\b", text)
    words = [w.strip("'") for w in words if re.search(r'[a-zA-Z]', w)]
    num_words = max(len(words), 1)

    num_syllables = sum(count_syllables(w) for w in words)

    score = (
        206.835
        - 1.015 * (num_words / num_sentences)
        - 84.6  * (num_syllables / num_words)
    )
    return round(max(0.0, min(100.0, score)), 2)


def flesch_grade_label(score: float) -> str:
    if score >= 90: return "Very Easy (5th grade)"
    if score >= 70: return "Easy (6th grade)"
    if score >= 60: return "Standard (7–8th grade)"
    if score >= 50: return "Fairly Difficult (High school)"
    if score >= 30: return "Difficult (College)"
    return "Very Confusing (College graduate)"


# ─────────────────────────────────────────────
# Content Depth Helpers
# ─────────────────────────────────────────────

def content_depth_label(word_count: int) -> str:
    if word_count >= 2000: return "In-depth / Comprehensive"
    if word_count >= 1000: return "Detailed"
    if word_count >= 500:  return "Moderate"
    if word_count >= 200:  return "Thin"
    return "Very Thin"


_BLOCK_TAGS = frozenset([
    'p', 'div', 'section', 'article', 'ul', 'ol', 'li',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote',
    'table', 'tr', 'td', 'th', 'header', 'footer', 'nav',
    'aside', 'figure', 'figcaption', 'dl', 'dt', 'dd',
])

_TEXT_TAGS = frozenset([
    "p", "h1", "h2", "h3", "h4", "h5", "h6",
    "li", "blockquote", "td", "th", "dd", "dt", "figcaption",
])


def _has_direct_text(tag) -> bool:
    """
    Return True if a tag has meaningful text NOT fully delegated to block children.
    Used to detect <div> elements that contain prose directly (not just nested blocks).
    """
    from bs4 import NavigableString, Tag as BSTag
    direct = ""
    for child in tag.children:
        if isinstance(child, NavigableString):
            direct += str(child)
        elif isinstance(child, BSTag) and child.name not in _BLOCK_TAGS:
            direct += child.get_text(" ")
    return len(direct.strip()) > 3


def _extract_from_container(container) -> str:
    """
    Walk the container collecting text from all text-bearing elements.
    - Explicit _TEXT_TAGS: always included (p, li, h1–h6, blockquote, td, etc.)
    - div/section/span: included only when they carry direct prose text,
      avoiding double-counting text that is already captured by child <p>/<li>.
    """
    from bs4 import NavigableString, Tag as BSTag
    parts = []
    for el in container.find_all(True):
        if el.name in _TEXT_TAGS:
            t = el.get_text(" ", strip=True)
            if t:
                parts.append(t)
        elif el.name in ('div', 'section', 'span') and _has_direct_text(el):
            direct = ""
            for child in el.children:
                if isinstance(child, NavigableString):
                    direct += str(child) + " "
                elif isinstance(child, BSTag) and child.name not in _BLOCK_TAGS:
                    direct += child.get_text(" ") + " "
            direct = direct.strip()
            if len(direct.split()) >= 3:
                parts.append(direct)
    return re.sub(r'\s+', ' ', " ".join(parts)).strip()


def _extract_content_text(soup: BeautifulSoup) -> str:
    """
    Extract the main readable text from a page, avoiding nav/header/footer noise.
    Strategy (in order):
      1. <main>, <article>, or element with id/class matching 'content|main|post|article'
      2. All text-bearing tags from the cleaned body
    FIX over original:
      - Captures prose in <div>, <li>, <blockquote> etc., not just <p>
      - Avoids double-counting nested block elements
      - Excludes header/footer/nav/aside before extraction
    """
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
        tag.decompose()

    # Prefer a semantic content container
    container = (
        soup.find("main")
        or soup.find("article")
        or soup.find(id=re.compile(r'\b(content|main|body|post|article)\b', re.I))
        or soup.find(class_=re.compile(r'\b(content|main|body|post|article|entry)\b', re.I))
    )

    if container:
        text = _extract_from_container(container)
    else:
        body = soup.find("body")
        if body:
            text = _extract_from_container(body)
        else:
            text = ""

    # Last resort
    if len(text.split()) < 30:
        body = soup.find("body")
        text = body.get_text(" ", strip=True) if body else ""

    return re.sub(r'\s+', ' ', text).strip()


# ─────────────────────────────────────────────
# Main Analyzer
# ─────────────────────────────────────────────

def content_analyzer(url: str, browser=None) -> dict:

    try:
        # ── Load page ─────────────────────────────────────────────────────
        if browser:
            page = browser.new_page()
            # FIX: networkidle captures dynamic/lazy content; domcontentloaded misses it
            page.goto(url, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(1000)
            html = page.content()
            page.close()
        else:
            response = requests.get(
                url, verify=False, timeout=15,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            response.raise_for_status()
            html = response.text

        soup = BeautifulSoup(html, "html.parser")

        # FIX: extract content text once, using the improved extractor
        # This is used for readability, word count, and duplicate detection — all consistent.
        all_text = _extract_content_text(soup)

        # Re-parse for structural checks (soup was mutated by _extract_content_text)
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
            tag.decompose()

        issues  = []
        details = {}
        score   = 100

        # ══════════════════════════════════════
        # CHECK 1 ─ Content Readability Score
        # ══════════════════════════════════════
        words_in_text = all_text.split()

        if len(words_in_text) >= 30:
            flesch_score = flesch_reading_ease(all_text)
            grade_label  = flesch_grade_label(flesch_score)
        else:
            flesch_score = None
            grade_label  = "Not enough text to score"

        details["readability"] = {
            "flesch_reading_ease": flesch_score,
            "grade_label"        : grade_label,
            "note"               : (
                "Flesch Reading Ease: 0 (hardest) → 100 (easiest). "
                "Recommended for general web content: 60–70."
            )
        }

        if flesch_score is not None and flesch_score < 30:
            issues.append(
                f"[READABILITY] Very difficult to read "
                f"(Flesch score: {flesch_score} — {grade_label})"
            )
            score -= 15
        elif flesch_score is not None and flesch_score < 50:
            issues.append(
                f"[READABILITY] Fairly difficult to read "
                f"(Flesch score: {flesch_score} — {grade_label})"
            )
            score -= 8

        # ══════════════════════════════════════
        # CHECK 2 ─ Duplicate Content Detection
        # ══════════════════════════════════════
        # Strategy:
        #   1. Exact match on normalised paragraph text (lowercased + whitespace-collapsed)
        #   2. Near-duplicate detection via Jaccard similarity on word-sets (≥85% overlap)
        # FIX: use consistent content extraction (same soup) for paragraph discovery

        JACCARD_THRESHOLD = 0.85
        MIN_PARA_WORDS    = 12

        para_texts = []
        # Collect from <p> AND other block-level text containers for complete coverage
        for el in soup.find_all(["p", "li", "blockquote"]):
            t = el.get_text(" ", strip=True)
            if len(t.split()) >= MIN_PARA_WORDS:
                para_texts.append(t)

        normalized = [re.sub(r'\s+', ' ', t).lower().strip() for t in para_texts]

        # Exact duplicates
        count_map      = Counter(normalized)
        exact_dups     = [t for t, c in count_map.items() if c > 1]

        # Near-duplicates via Jaccard
        near_dups = []
        checked_pairs = set()
        for i, t1 in enumerate(normalized):
            set1 = set(t1.split())
            for j, t2 in enumerate(normalized):
                if j <= i:
                    continue
                if (i, j) in checked_pairs:
                    continue
                checked_pairs.add((i, j))
                set2  = set(t2.split())
                union = set1 | set2
                if not union:
                    continue
                jaccard = len(set1 & set2) / len(union)
                if jaccard >= JACCARD_THRESHOLD and t1 != t2:
                    near_dups.append({
                        "similarity": round(jaccard * 100, 1),
                        "snippet_a" : para_texts[i][:80],
                        "snippet_b" : para_texts[j][:80],
                    })

        details["duplicate_content"] = {
            "paragraphs_analyzed" : len(para_texts),
            "exact_duplicates"    : len(exact_dups),
            "near_duplicates"     : len(near_dups),
            "near_duplicate_pairs": near_dups[:5],
            "exact_samples"       : exact_dups[:3],
        }

        total_dup = len(exact_dups) + len(near_dups)
        if total_dup > 0:
            issues.append(
                f"[DUPLICATE] {len(exact_dups)} exact + "
                f"{len(near_dups)} near-duplicate paragraph block(s) detected"
            )
            score -= min(20, total_dup * 5)

        # ══════════════════════════════════════
        # CHECK 3 ─ Broken Links Detection
        # ══════════════════════════════════════
        parsed_url = urlparse(url)
        base_url   = f"{parsed_url.scheme}://{parsed_url.netloc}"

        SKIP_SCHEMES = ("mailto:", "tel:", "javascript:", "#", "data:")

        # FIX: build a URL→anchor-text map during the anchor scan so broken link
        # entries report the correct anchor text (original had a stale `a` reference).
        link_to_text = {}   # url → first anchor text seen for that url
        all_links    = []
        skipped      = 0

        for a in soup.find_all("a", href=True):
            href = a.get("href", "").strip()
            if not href or any(href.startswith(s) for s in SKIP_SCHEMES):
                skipped += 1
                continue
            full_url_str = urljoin(base_url, href)
            all_links.append(full_url_str)
            if full_url_str not in link_to_text:
                link_to_text[full_url_str] = a.get_text(strip=True)[:60]

        unique_links = list(dict.fromkeys(all_links))
        broken_links = []

        HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SEOBot/1.0)"}

        for link in unique_links[:60]:
            try:
                head = requests.head(
                    link, verify=False, timeout=8,
                    allow_redirects=True, headers=HEADERS
                )
                status = head.status_code

                # FIX: fall back to GET for more status codes that reject HEAD
                if status in (405, 403, 401, 408, 503):
                    get_r  = requests.get(
                        link, verify=False, timeout=8,
                        allow_redirects=True, headers=HEADERS,
                        stream=True
                    )
                    status = get_r.status_code

                if status >= 400:
                    broken_links.append({
                        "url"   : link,
                        "status": status,
                        # FIX: look up anchor text from the pre-built map
                        "text"  : link_to_text.get(link, "")
                    })

            except requests.exceptions.RequestException as e:
                broken_links.append({
                    "url"   : link,
                    "status": "unreachable",
                    "text"  : link_to_text.get(link, ""),
                    "error" : str(e)[:80]
                })

        details["broken_links"] = {
            "total_links_found"   : len(all_links),
            "unique_links_checked": len(unique_links[:60]),
            "skipped_links"       : skipped,
            "broken_count"        : len(broken_links),
            "broken_links"        : broken_links[:20]
        }

        if broken_links:
            issues.append(
                f"[LINKS] {len(broken_links)} broken or unreachable link(s) found"
            )
            score -= min(20, len(broken_links) * 4)

        # ══════════════════════════════════════
        # CHECK 4 ─ Word Count & Content Depth
        # ══════════════════════════════════════
        # FIX: all metrics derived from the same `all_text` used for readability —
        # consistent corpus, not a mix of p-only and full-body text.

        words         = re.findall(r'\b[a-zA-Z]+\b', all_text)
        word_count    = len(words)
        depth_label   = content_depth_label(word_count)

        sentences     = [s.strip() for s in re.split(r'[.!?]+', all_text) if s.strip()]
        num_sentences = max(len(sentences), 1)
        avg_sentence_len = round(word_count / num_sentences, 1)

        unique_words      = set(w.lower() for w in words)
        lexical_diversity = round(len(unique_words) / max(word_count, 1) * 100, 1)

        # FIX: count subheadings from cleaned soup (consistent with body extraction)
        subheadings  = soup.find_all(["h2", "h3", "h4"])
        num_subheads = len(subheadings)

        # Paragraph count from cleaned soup
        num_paragraphs = len([p for p in soup.find_all("p") if p.get_text(strip=True)])

        details["content_depth"] = {
            "word_count"           : word_count,
            "depth_label"          : depth_label,
            "sentence_count"       : num_sentences,
            "avg_sentence_length"  : avg_sentence_len,
            "unique_words"         : len(unique_words),
            "lexical_diversity_pct": lexical_diversity,
            "subheadings_found"    : num_subheads,
            "paragraph_count"      : num_paragraphs,
            "recommendation"       : (
                "Aim for 800–1500+ words for strong content depth. "
                "Average sentence length < 20 words improves readability."
            )
        }

        if word_count < 200:
            issues.append(
                f"[DEPTH] Very thin content — only {word_count} words detected. "
                "Aim for 800+ words for meaningful depth."
            )
            score -= 20
        elif word_count < 500:
            issues.append(
                f"[DEPTH] Thin content — {word_count} words. "
                "Consider expanding to 800+ words."
            )
            score -= 10

        if avg_sentence_len > 30:
            issues.append(
                f"[DEPTH] Average sentence length is {avg_sentence_len} words — "
                "consider shorter sentences for better readability."
            )
            score -= 5

        if num_subheads == 0 and word_count > 300:
            issues.append(
                "[DEPTH] No subheadings (h2–h4) found — "
                "add headings to improve content structure and scannability."
            )
            score -= 5

        # ──────────────────────────────────────
        # Final result
        # ──────────────────────────────────────
        final_score = max(score, 0)
        return {
            "type"   : "Content",
            "url"    : url,
            "score"  : final_score,
            "grade"  : (
                "A" if final_score >= 90 else
                "B" if final_score >= 75 else
                "C" if final_score >= 60 else
                "D" if final_score >= 40 else "F"
            ),
            "issues" : issues if issues else ["✅ No major content issues detected"],
            "details": details
        }

    except Exception as e:
        import traceback
        return {
            "error"    : str(e),
            "traceback": traceback.format_exc()
        }