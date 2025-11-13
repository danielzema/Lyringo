# ...existing code...
import re
from typing import Tuple, Optional, List
import requests

GOOGLE_TRANSLATE_URL = "https://translate.googleapis.com/translate_a/single"

# Mapping of common language names / aliases -> ISO 639-1 codes used by Google Translate.
# Includes common names, native names and short aliases.
_LANG_NAME_TO_CODE = {
    "afrikaans": "af",
    "albanian": "sq",
    "amharic": "am",
    "arabic": "ar",
    "armenian": "hy",
    "azerbaijani": "az",
    "basque": "eu",
    "belarusian": "be",
    "bengali": "bn",
    "bosnian": "bs",
    "bulgarian": "bg",
    "catalan": "ca",
    "cebuano": "ceb",
    "chichewa": "ny",
    "chinese": "zh-CN",
    "chinese (simplified)": "zh-CN",
    "chinese (traditional)": "zh-TW",
    "croatian": "hr",
    "czech": "cs",
    "danish": "da",
    "dutch": "nl",
    "english": "en",
    "esperanto": "eo",
    "estonian": "et",
    "filipino": "tl",
    "finnish": "fi",
    "french": "fr",
    "galician": "gl",
    "georgian": "ka",
    "german": "de",
    "greek": "el",
    "gujarati": "gu",
    "haitian creole": "ht",
    "hausa": "ha",
    "hebrew": "he",
    "hindi": "hi",
    "hmong": "hmn",
    "hungarian": "hu",
    "icelandic": "is",
    "igbo": "ig",
    "indonesian": "id",
    "irish": "ga",
    "italian": "it",
    "japanese": "ja",
    "javanese": "jv",
    "kannada": "kn",
    "kazakh": "kk",
    "khmer": "km",
    "korean": "ko",
    "kurdish": "ku",
    "kyrgyz": "ky",
    "lao": "lo",
    "latin": "la",
    "latvian": "lv",
    "lithuanian": "lt",
    "luxembourgish": "lb",
    "macedonian": "mk",
    "malagasy": "mg",
    "malay": "ms",
    "malayalam": "ml",
    "maltese": "mt",
    "maori": "mi",
    "marathi": "mr",
    "mongolian": "mn",
    "myanmar": "my",
    "nepali": "ne",
    "norwegian": "no",
    "odia": "or",
    "pashto": "ps",
    "persian": "fa",
    "polish": "pl",
    "portuguese": "pt",
    "punjabi": "pa",
    "romanian": "ro",
    "russian": "ru",
    "scots gaelic": "gd",
    "serbian": "sr",
    "sesotho": "st",
    "shona": "sn",
    "sindhi": "sd",
    "sinhala": "si",
    "slovak": "sk",
    "slovenian": "sl",
    "somali": "so",
    "spanish": "es",
    "sundanese": "su",
    "swahili": "sw",
    "swedish": "sv",
    "tajik": "tg",
    "tamil": "ta",
    "telugu": "te",
    "thai": "th",
    "turkish": "tr",
    "ukrainian": "uk",
    "urdu": "ur",
    "uyghur": "ug",
    "uzbek": "uz",
    "vietnamese": "vi",
    "welsh": "cy",
    "xhosa": "xh",
    "yiddish": "yi",
    "yoruba": "yo",
    "zulu": "zu",
    # common short aliases and native names
    "svenska": "sv",
    "español": "es",
    "deutsch": "de",
    "français": "fr",
    "italiano": "it",
    "português": "pt",
    "русский": "ru",
    "中文": "zh-CN",
    "日本語": "ja",
    "한국어": "ko",
    "nb": "no",  # norwegian bokmål alias
    "zh": "zh-CN",
}

# also create reverse mapping for quick lookup by code
_SUPPORTED_CODES = set(_LANG_NAME_TO_CODE.values())


def language_name_to_code(name: str) -> Optional[str]:
    """
    Convert a user-provided language name or short code into the Google Translate
    language code (ISO 639-1 style or vendor code like zh-CN).
    Examples:
      language_name_to_code("english") -> "en"
      language_name_to_code("en") -> "en"
      language_name_to_code("svenska") -> "sv"
    Returns None if the language can't be resolved.
    """
    if not name:
        return None
    s = name.strip().lower()
    # direct code passed in, accept if in supported codes or looks like two-letter code
    if s in _SUPPORTED_CODES:
        return s
    # canonicalize common two-letter inputs (without region)
    if len(s) == 2 and s.isalpha():
        # allow passing codes like 'en', 'sv' even if they weren't in mapping values
        return s
    # remove punctuation and common words
    s = re.sub(r'[^a-z\- ]', '', s)
    s = s.replace("_", " ").strip()
    # exact name match
    if s in _LANG_NAME_TO_CODE:
        return _LANG_NAME_TO_CODE[s]
    # try each mapping key for partial match (e.g. "chinese simplified" -> zh-CN)
    for key, code in _LANG_NAME_TO_CODE.items():
        if s == key:
            return code
    for key, code in _LANG_NAME_TO_CODE.items():
        if s in key:
            return code
    # if nothing matched, return None
    return None


def code_to_display_name(code_or_name: str) -> str:
    """
    Convert a language code or name to a human-friendly display name.

    Accepts either a code (e.g. 'en', 'es') or a language name ('spanish') and
    returns a lower-case display name. If the code is 'es' we intentionally
    return the user-requested string 'spaish'. If we can't resolve the code,
    return the original input.
    """
    if not code_or_name:
        return "unknown"

    s = str(code_or_name).strip()
    # try to normalize to a code first
    code = None
    s_lower = s.lower()
    if s_lower in _SUPPORTED_CODES or (len(s_lower) == 2 and s_lower.isalpha()):
        code = s_lower
    else:
        code = language_name_to_code(s)

    if not code:
        # couldn't normalize — return the original input lowercased
        return s_lower

    # prefer an ASCII/English-looking name for the code
    for name, c in _LANG_NAME_TO_CODE.items():
        if c.lower() == code and all(ord(ch) < 128 for ch in name):
            return name.lower()

    # fallback to any matching mapping
    for name, c in _LANG_NAME_TO_CODE.items():
        if c.lower() == code:
            return name.lower()

    # last resort: return the code itself
    return code

def _extract_header(formatted: str) -> Tuple[str, str]:
    if not formatted:
        return "", ""
    parts = formatted.split("\n\n", 1)
    if len(parts) == 2 and "—" in parts[0]:
        # The provider may include a decorative underline (e.g. a line of
        # dashes) directly under the "Title — Artist" line. Remove any
        # lines that consist only of punctuation/whitespace so the header
        # becomes just the canonical title/artist string.
        header_block = parts[0].strip()
        header_lines = [ln for ln in header_block.splitlines() if not re.match(r'^[\-\s]+$', ln)]
        header = header_lines[0].strip() if header_lines else header_block.splitlines()[0].strip()
        return header, parts[1].strip()
    return "", formatted.strip()

def detect_language(formatted_or_text: str) -> str:
    """
    Detect language of provided lyrics or formatted string using the same
    Google Translate endpoint (no extra deps). Returns ISO code (e.g. 'en', 'es')
    or 'unknown' on failure.
    """
    try:
        # reuse header extractor if present
        header, body = _extract_header(formatted_or_text)
    except Exception:
        body = formatted_or_text or ""

    body = (body or "").strip()
    if not body:
        return "unknown"

    # use a short sample for detection to avoid huge requests
    sample = body.split("\n\n", 1)[0][:4000]
    params = {"client": "gtx", "sl": "auto", "tl": "en", "dt": "t", "q": sample}

    try:
        resp = requests.get(GOOGLE_TRANSLATE_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        # Typical response shape: [ [[...]], null, "detected_lang", ... ]
        if isinstance(data, list) and len(data) >= 3 and isinstance(data[2], str):
            return data[2]
        # fallback for other shapes
        if isinstance(data, dict):
            return data.get("src", "unknown")
    except Exception:
        return "unknown"

    return "unknown"

def _translate_paragraph(paragraph: str, target_lang: str) -> str:
    if not paragraph.strip():
        return ""
    params = {
        "client": "gtx",
        "sl": "auto",
        "tl": target_lang,
        "dt": "t",
        "q": paragraph
    }
    resp = requests.get(GOOGLE_TRANSLATE_URL, params=params, timeout=10)
    resp.raise_for_status()
    try:
        data = resp.json()
    except Exception:
        # Response was not valid JSON (rate limit page, empty body, etc.).
        # Let caller fall back; return the original paragraph so output stays usable.
        return paragraph

    # defensive: ensure the expected shape exists
    try:
        segments = data[0]
        translated = "".join(seg[0] for seg in segments if seg and len(seg) > 0 and seg[0])
    except Exception:
        # Unexpected response shape — return original paragraph
        return paragraph
    return translated

def translate_song(lyrics: str, target_language: str) -> str:
    header, body = _extract_header(lyrics)
    # split into paragraphs (preserve paragraphs separated by one or more blank lines)
    paragraphs = [p for p in re.split(r'\n{2,}', body) if p.strip()]

    translated_parts = []
    for p in paragraphs:
        try:
            translated = _translate_paragraph(p, target_language)
        except Exception as e:
            # on failure, include the original paragraph so output is still usable
            translated = p
        translated_parts.append(translated)

    translated_body = "\n\n".join(translated_parts)

    if header:
        sep = "\n" + "-" * max(3, len(header)) + "\n\n"
        translated_formatted = f"{header}{sep}{translated_body}"
    else:
        translated_formatted = translated_body

    return translated_formatted