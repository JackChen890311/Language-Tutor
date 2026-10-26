"""The app's visual language: design tokens, global CSS, and small HTML helpers.

Everything visual is centralised here so that pages only describe *what* to
show, never *how* it looks. :func:`inject` is called once from ``ui/app.py``.

Every colour token is emitted as a ``light-dark()`` pair, so the custom markup
follows Streamlit's active theme instantly — including when the user switches
theme from the app menu, which does not trigger a rerun. Streamlit's own
widgets are themed through ``.streamlit/config.toml``.
"""

from __future__ import annotations

import html
from dataclasses import dataclass

import streamlit as st


@dataclass(frozen=True)
class Palette:
    bg: str
    surface: str
    surface_alt: str
    border: str
    text: str
    muted: str
    accent: str
    accent_hover: str
    accent_soft: str
    accent_border: str
    on_accent: str
    on_danger: str
    shadow: str
    shadow_hover: str
    success: str
    success_soft: str
    danger: str
    danger_soft: str
    ring_track: str


LIGHT = Palette(
    bg="#FBFAF8",
    surface="#FFFFFF",
    surface_alt="#F3F0EA",
    border="#E4DED4",
    text="#1F1B16",
    muted="#7A7168",
    accent="#A85E12",
    accent_hover="#8F4D0D",
    accent_soft="rgba(168, 94, 18, 0.10)",
    accent_border="rgba(168, 94, 18, 0.30)",
    on_accent="#FFFFFF",
    on_danger="#FFFFFF",
    shadow="rgba(31, 27, 22, 0.06)",
    shadow_hover="rgba(31, 27, 22, 0.14)",
    success="#2E7D4F",
    success_soft="rgba(46, 125, 79, 0.12)",
    danger="#B3261E",
    danger_soft="rgba(179, 38, 30, 0.10)",
    ring_track="rgba(31, 27, 22, 0.08)",
)

DARK = Palette(
    bg="#141310",
    surface="#1C1A16",
    surface_alt="#23201B",
    border="#2E2B25",
    text="#F2EDE6",
    muted="#A79E92",
    accent="#E8A44C",
    accent_hover="#F0B568",
    accent_soft="rgba(232, 164, 76, 0.14)",
    accent_border="rgba(232, 164, 76, 0.32)",
    on_accent="#201608",
    on_danger="#201608",
    shadow="rgba(0, 0, 0, 0.40)",
    shadow_hover="rgba(0, 0, 0, 0.55)",
    success="#7BD8A0",
    success_soft="rgba(123, 216, 160, 0.14)",
    danger="#FF8A80",
    danger_soft="rgba(255, 138, 128, 0.14)",
    ring_track="rgba(242, 237, 230, 0.10)",
)


def esc(value: object) -> str:
    """HTML-escape dynamic text before dropping it into custom markup."""
    return html.escape(str(value))


def _pair(light: str, dark: str) -> str:
    return f"light-dark({light}, {dark})"


def _token_css() -> str:
    tokens = {
        "--lt-bg": _pair(LIGHT.bg, DARK.bg),
        "--lt-surface": _pair(LIGHT.surface, DARK.surface),
        "--lt-surface-2": _pair(LIGHT.surface_alt, DARK.surface_alt),
        "--lt-border": _pair(LIGHT.border, DARK.border),
        "--lt-text": _pair(LIGHT.text, DARK.text),
        "--lt-muted": _pair(LIGHT.muted, DARK.muted),
        "--lt-accent": _pair(LIGHT.accent, DARK.accent),
        "--lt-accent-hover": _pair(LIGHT.accent_hover, DARK.accent_hover),
        "--lt-accent-soft": _pair(LIGHT.accent_soft, DARK.accent_soft),
        "--lt-accent-border": _pair(LIGHT.accent_border, DARK.accent_border),
        "--lt-on-accent": _pair(LIGHT.on_accent, DARK.on_accent),
        "--lt-on-danger": _pair(LIGHT.on_danger, DARK.on_danger),
        "--lt-shadow-color": _pair(LIGHT.shadow, DARK.shadow),
        "--lt-shadow-hover-color": _pair(LIGHT.shadow_hover, DARK.shadow_hover),
        "--lt-success": _pair(LIGHT.success, DARK.success),
        "--lt-success-soft": _pair(LIGHT.success_soft, DARK.success_soft),
        "--lt-danger": _pair(LIGHT.danger, DARK.danger),
        "--lt-danger-soft": _pair(LIGHT.danger_soft, DARK.danger_soft),
        "--lt-ring-track": _pair(LIGHT.ring_track, DARK.ring_track),
    }
    body = "\n".join(f"  {name}: {value};" for name, value in tokens.items())
    return f".stApp {{\n{body}\n}}\n"


_BASE_CSS = """
/* ---------- shell ------------------------------------------------------ */
.stApp { background: var(--lt-bg); color: var(--lt-text); }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"] { right: 0.6rem; }
[data-testid="stAppDeployButton"], [data-testid="stStatusWidget"], footer {
    display: none !important;
}
#MainMenu button { color: var(--lt-muted) !important; border-radius: 0.6rem; }
#MainMenu button:hover { background: var(--lt-accent-soft) !important; color: var(--lt-accent) !important; }
[data-testid="stMainMenu"] { display: block; }
[data-testid="stMainBlockContainer"] {
    max-width: 1180px;
    padding-top: 2.4rem;
    padding-bottom: 5.5rem;
    margin: 0 auto;
}
[data-testid="stBottomBlockContainer"] { max-width: 1180px; }

/* ---------- typography ------------------------------------------------- */
.stApp h1 { font-size: 1.9rem; line-height: 1.15; letter-spacing: -0.02em; }
.stApp h2 { font-size: 1.35rem; letter-spacing: -0.01em; }
.stApp h3 { font-size: 1.1rem; }
.stApp p, .stApp li { line-height: 1.62; }
.stApp [data-testid="stMarkdownContainer"] a { text-decoration-line: underline;
    text-decoration-thickness: 1px; text-underline-offset: 2px; }

/* ---------- sidebar ---------------------------------------------------- */
[data-testid="stSidebar"] { background: var(--lt-surface-2); }
[data-testid="stSidebar"] [data-testid="stSidebarContent"] { padding-top: 0.4rem; }
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { padding-top: 0.6rem; }

div[class*="st-key-nav_"] button {
    width: 100%;
    justify-content: flex-start;
    text-align: left;
    border-radius: 11px;
    padding: 0.5rem 0.75rem;
    font-size: 0.95rem;
    font-weight: 550;
    border: 1px solid transparent;
    box-shadow: none;
    transition: background 0.16s ease, color 0.16s ease, border-color 0.16s ease;
}
div[class*="st-key-nav_"] button > div,
div[class*="st-key-nav_"] button span {
    justify-content: flex-start !important;
    text-align: left !important;
    width: 100%;
}
div[class*="st-key-nav_"] button[data-testid="stBaseButton-tertiary"] {
    background: transparent;
    color: var(--lt-text);
    opacity: 0.86;
}
div[class*="st-key-nav_"] button[data-testid="stBaseButton-tertiary"]:hover {
    background: var(--lt-accent-soft);
    color: var(--lt-accent);
    opacity: 1;
}
div[class*="st-key-nav_"] button[data-testid="stBaseButton-primary"] {
    background: var(--lt-accent-soft);
    border-color: var(--lt-accent-border);
    color: var(--lt-accent);
    box-shadow: inset 3px 0 0 var(--lt-accent);
}
div[class*="st-key-nav_"] button[data-testid="stBaseButton-primary"]:hover {
    background: var(--lt-accent-soft);
    color: var(--lt-accent-hover);
}

/* sidebar session list */
div[class*="st-key-chat_sessions"] button {
    width: 100%;
    justify-content: flex-start !important;
    text-align: left !important;
    padding: 0.32rem 0.55rem;
    font-size: 0.86rem;
    font-weight: 500;
    border-radius: 0.55rem;
    box-shadow: none;
    min-height: 0;
}
div[class*="st-key-chat_sessions"] button > div,
div[class*="st-key-chat_sessions"] button span {
    justify-content: flex-start !important;
    text-align: left !important;
    width: 100%;
}
div[class*="st-key-chat_sessions"] button[data-testid="stBaseButton-tertiary"] {
    background: transparent;
    color: var(--lt-text);
    opacity: 0.8;
}
div[class*="st-key-chat_sessions"] button[data-testid="stBaseButton-tertiary"]:hover {
    background: var(--lt-accent-soft);
    color: var(--lt-accent);
    opacity: 1;
}
div[class*="st-key-chat_sessions"] button[data-testid="stBaseButton-primary"] {
    background: var(--lt-accent-soft);
    color: var(--lt-accent);
    border-color: var(--lt-accent-border);
}
div[class*="st-key-chat_sessions"] [data-testid="stHorizontalBlock"] {
    gap: 0.25rem;
}

.lt-brand {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    padding: 0.15rem 0.2rem 0.9rem;
}
.lt-brand-mark {
    display: grid;
    place-items: center;
    width: 2.5rem;
    height: 2.5rem;
    flex: none;
    border-radius: 0.8rem;
    background: var(--lt-accent);
    color: var(--lt-on-accent);
    font-size: 1.2rem;
    box-shadow: 0 6px 16px var(--lt-accent-soft);
}
.lt-brand-name { font-size: 1rem; font-weight: 700; letter-spacing: -0.01em; }
.lt-brand-sub { font-size: 0.72rem; color: var(--lt-muted); }
.lt-langpair {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    margin: 0 0 0.9rem 0.2rem;
    padding: 0.24rem 0.65rem;
    border-radius: 999px;
    background: var(--lt-surface);
    border: 1px solid var(--lt-border);
    color: var(--lt-text);
    font-size: 0.82rem;
    font-weight: 600;
}
.lt-langpair .lt-arrow { color: var(--lt-accent); font-weight: 700; }
.lt-sidefoot {
    margin-top: 1rem;
    padding-top: 0.9rem;
    border-top: 1px solid var(--lt-border);
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
}
.lt-sidefoot-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 0.78rem;
    color: var(--lt-muted);
}
.lt-sidefoot-row b { color: var(--lt-text); }
.lt-dots { display: inline-flex; gap: 0.28rem; }
.lt-dot {
    width: 0.45rem;
    height: 0.45rem;
    border-radius: 50%;
    background: var(--lt-ring-track);
}
.lt-dot.is-on { background: var(--lt-success); }

/* ---------- buttons ---------------------------------------------------- */
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button {
    border-radius: 0.65rem;
    font-weight: 550;
    transition: transform 0.14s ease, background 0.16s ease, border-color 0.16s ease,
        box-shadow 0.16s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    transform: translateY(-1px);
}
button[data-testid="stBaseButton-primary"] {
    background: var(--lt-accent);
    border-color: var(--lt-accent);
    color: var(--lt-on-accent);
    box-shadow: 0 4px 14px var(--lt-accent-soft);
}
button[data-testid="stBaseButton-primary"]:hover {
    background: var(--lt-accent-hover);
    border-color: var(--lt-accent-hover);
    color: var(--lt-on-accent);
}
button[data-testid="stBaseButton-secondary"]:hover {
    border-color: var(--lt-accent-border);
    color: var(--lt-accent);
}

/* ---------- surfaces --------------------------------------------------- */
div[class*="st-key-ltcard_"], div[class*="st-key-ltcardhover_"] {
    background: var(--lt-surface);
    border: 1px solid var(--lt-border);
    border-radius: 1rem;
    padding: 1.05rem 1.15rem;
    box-shadow: 0 1px 2px var(--lt-shadow-color);
    transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}
div[class*="st-key-ltcardhover_"]:hover {
    transform: translateY(-2px);
    border-color: var(--lt-accent-border);
    box-shadow: 0 12px 28px var(--lt-shadow-hover-color);
}
.lt-card {
    background: var(--lt-surface);
    border: 1px solid var(--lt-border);
    border-radius: 1rem;
    padding: 1.05rem 1.15rem;
    box-shadow: 0 1px 2px var(--lt-shadow-color);
}

/* ---------- page header ------------------------------------------------ */
.lt-pagehead {
    display: flex;
    align-items: center;
    gap: 0.9rem;
    margin: 0 0 1.5rem;
    animation: lt-fade 0.35s ease both;
}
.lt-pagehead-icon {
    display: grid;
    place-items: center;
    width: 3rem;
    height: 3rem;
    border-radius: 0.9rem;
    background: var(--lt-accent-soft);
    border: 1px solid var(--lt-accent-border);
    font-size: 1.45rem;
    flex: none;
}
.lt-pagehead-title {
    margin: 0;
    font-size: 1.9rem;
    line-height: 1.15;
    letter-spacing: -0.02em;
    font-weight: 700;
}
.lt-pagehead-sub {
    margin: 0.15rem 0 0;
    color: var(--lt-muted);
    font-size: 0.93rem;
}

/* ---------- section header --------------------------------------------- */
.lt-section {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 0.75rem;
    margin: 1.6rem 0 0.75rem;
}
.lt-section-title {
    font-size: 1.05rem;
    font-weight: 650;
    letter-spacing: -0.01em;
}
.lt-section-title .lt-ico { margin-right: 0.45rem; }
.lt-section-cap { color: var(--lt-muted); font-size: 0.82rem; }

/* ---------- hero ------------------------------------------------------- */
.lt-hero {
    position: relative;
    overflow: hidden;
    background:
        radial-gradient(120% 140% at 100% 0%, var(--lt-accent-soft) 0%, transparent 58%),
        var(--lt-surface);
    border: 1px solid var(--lt-border);
    border-radius: 1.25rem;
    padding: 1.6rem 1.75rem;
    box-shadow: 0 1px 2px var(--lt-shadow-color);
    animation: lt-fade 0.4s ease both;
}
.lt-hero::after {
    content: "";
    position: absolute;
    right: -3rem;
    top: -3rem;
    width: 11rem;
    height: 11rem;
    border-radius: 50%;
    background: var(--lt-accent-soft);
    pointer-events: none;
}
.lt-hero-greet { color: var(--lt-muted); font-size: 0.9rem; font-weight: 550; }
.lt-hero-title {
    margin: 0.3rem 0 0.35rem;
    font-size: 1.75rem;
    line-height: 1.2;
    letter-spacing: -0.02em;
    font-weight: 700;
}
.lt-hero-title .lt-hl { color: var(--lt-accent); }
.lt-hero-sub { margin: 0; color: var(--lt-muted); font-size: 0.92rem; max-width: 48ch; }

.lt-chiprow { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.9rem; }
.lt-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.22rem 0.65rem;
    border-radius: 999px;
    background: var(--lt-accent-soft);
    border: 1px solid var(--lt-accent-border);
    color: var(--lt-accent);
    font-size: 0.78rem;
    font-weight: 600;
    line-height: 1.5;
}
.lt-chip.is-muted {
    background: var(--lt-surface-2);
    border-color: var(--lt-border);
    color: var(--lt-muted);
}

/* ---------- stats ------------------------------------------------------ */
.lt-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 0.75rem;
    margin-top: 1rem;
}
.lt-stat {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    background: var(--lt-surface);
    border: 1px solid var(--lt-border);
    border-radius: 1rem;
    padding: 0.95rem 1rem;
    box-shadow: 0 1px 2px var(--lt-shadow-color);
    transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}
.lt-stat:hover {
    transform: translateY(-2px);
    border-color: var(--lt-accent-border);
    box-shadow: 0 12px 28px var(--lt-shadow-hover-color);
}
.lt-stat-icon {
    display: grid;
    place-items: center;
    width: 2.4rem;
    height: 2.4rem;
    flex: none;
    border-radius: 0.75rem;
    background: var(--lt-accent-soft);
    font-size: 1.15rem;
}
.lt-stat-value {
    font-size: 1.4rem;
    font-weight: 700;
    line-height: 1.15;
    letter-spacing: -0.02em;
}
.lt-stat-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--lt-muted);
    font-weight: 600;
}
.lt-stat-hint { font-size: 0.74rem; color: var(--lt-muted); margin-top: 0.05rem; }

/* ---------- activity strip --------------------------------------------- */
.lt-activity {
    display: flex;
    gap: 0.5rem;
    margin-top: 0.35rem;
}
.lt-day { flex: 1; text-align: center; min-width: 0; }
.lt-day-name {
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--lt-muted);
    font-weight: 600;
}
.lt-day-dot {
    width: 1.55rem;
    height: 1.55rem;
    margin: 0.35rem auto 0;
    border-radius: 50%;
    background: var(--lt-ring-track);
    border: 1px solid var(--lt-border);
    transition: transform 0.15s ease;
}
.lt-day.is-on .lt-day-dot {
    background: var(--lt-accent);
    border-color: var(--lt-accent);
    box-shadow: 0 0 0 3px var(--lt-accent-soft);
}
.lt-day.is-today .lt-day-dot { transform: scale(1.08); }
.lt-day.is-today .lt-day-name { color: var(--lt-accent); }

/* ---------- empty state ------------------------------------------------ */
.lt-empty {
    text-align: center;
    padding: 2.4rem 1.25rem;
    border: 1px dashed var(--lt-border);
    border-radius: 1.1rem;
    background: var(--lt-surface);
    animation: lt-fade 0.35s ease both;
}
.lt-empty-icon { font-size: 2.1rem; line-height: 1; }
.lt-empty-title { margin-top: 0.6rem; font-size: 1.05rem; font-weight: 650; }
.lt-empty-body { margin: 0.3rem auto 0; max-width: 46ch; color: var(--lt-muted); font-size: 0.9rem; }

/* ---------- stepper ---------------------------------------------------- */
.lt-steps { display: flex; align-items: center; gap: 0.2rem; flex-wrap: wrap; }
.lt-step { display: flex; align-items: center; gap: 0.4rem; }
.lt-step-dot {
    display: grid;
    place-items: center;
    width: 1.55rem;
    height: 1.55rem;
    border-radius: 50%;
    border: 1px solid var(--lt-border);
    background: var(--lt-surface-2);
    color: var(--lt-muted);
    font-size: 0.7rem;
    font-weight: 700;
    flex: none;
}
.lt-step-label { font-size: 0.82rem; font-weight: 600; color: var(--lt-muted); }
.lt-step.is-done .lt-step-dot {
    background: var(--lt-accent-soft);
    border-color: var(--lt-accent-border);
    color: var(--lt-accent);
}
.lt-step.is-done .lt-step-label { color: var(--lt-text); }
.lt-step.is-active .lt-step-dot {
    background: var(--lt-accent);
    border-color: var(--lt-accent);
    color: var(--lt-on-accent);
}
.lt-step.is-active .lt-step-label { color: var(--lt-accent); }
.lt-step-line {
    width: 1.6rem;
    height: 1px;
    background: var(--lt-border);
    margin: 0 0.25rem;
}

/* ---------- score ring ------------------------------------------------- */
.lt-score {
    display: flex;
    align-items: center;
    gap: 1.4rem;
    flex-wrap: wrap;
}
.lt-ring {
    --pct: 0;
    width: 7.5rem;
    height: 7.5rem;
    border-radius: 50%;
    display: grid;
    place-items: center;
    background: conic-gradient(
        var(--lt-accent) calc(var(--pct) * 1%),
        var(--lt-ring-track) 0
    );
    flex: none;
}
.lt-ring-inner {
    width: 5.9rem;
    height: 5.9rem;
    border-radius: 50%;
    background: var(--lt-surface);
    display: grid;
    place-items: center;
    text-align: center;
}
.lt-ring-value { font-size: 1.6rem; font-weight: 700; letter-spacing: -0.02em; }
.lt-ring-label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em;
    color: var(--lt-muted); font-weight: 600; }
.lt-score-copy { font-size: 0.95rem; }
.lt-score-copy strong { font-size: 1.15rem; }

/* ---------- chat ------------------------------------------------------- */
[data-testid="stChatMessage"] {
    background: var(--lt-surface);
    border: 1px solid var(--lt-border);
    border-radius: 1rem;
    padding: 0.85rem 1rem;
    margin-bottom: 0.35rem;
    box-shadow: 0 1px 2px var(--lt-shadow-color);
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    background: var(--lt-accent-soft);
    border-color: var(--lt-accent-border);
}
[data-testid="stChatMessageAvatarUser"] {
    background: var(--lt-accent-soft) !important;
    color: var(--lt-accent) !important;
}
[data-testid="stChatMessageAvatarAssistant"] {
    background: var(--lt-accent) !important;
    color: var(--lt-on-accent) !important;
}
[data-testid="stChatMessageContent"] { color: var(--lt-text); }
[data-testid="stChatInput"] > div {
    border-radius: 1rem;
    border-color: var(--lt-border);
    background: var(--lt-surface);
    box-shadow: 0 1px 2px var(--lt-shadow-color);
}
[data-testid="stBottom"] { background: linear-gradient(transparent, var(--lt-bg) 40%); }

/* suggestion rail toggle, inline just above the composer */
div[class*="st-key-chat_toolbar"] {
    margin: 0 0 0.3rem;
}
div[class*="st-key-chat_toolbar"] [data-testid="stElementContainer"] {
    width: 100%;
}
div[class*="st-key-chat_toolbar"] .stButton {
    display: flex;
    width: 100%;
    justify-content: flex-end;
}
div[class*="st-key-chat_toolbar"] .stButton button {
    display: flex;
    width: auto;
    min-height: 2rem;
    height: 2rem;
    padding: 0 0.8rem;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 550;
    line-height: 1;
    box-shadow: none;
}
div[class*="st-key-chat_toolbar"] .stButton button[data-testid="stBaseButton-tertiary"] {
    background: var(--lt-surface);
    border: 1px solid var(--lt-border);
    color: var(--lt-muted);
}
div[class*="st-key-chat_toolbar"] .stButton button[data-testid="stBaseButton-tertiary"]:hover {
    border-color: var(--lt-accent-border);
    color: var(--lt-accent);
    transform: none;
}

/* speakable sentence + its play button */
div[class*="st-key-speak_"] {
    border-left: 3px solid var(--lt-accent);
    background: var(--lt-accent-soft);
    border-radius: 0.5rem;
    padding: 0.3rem 0.7rem;
    margin: 0.35rem 0;
}
div[class*="st-key-speak_"] p { margin: 0; font-weight: 600; }

/* ---------- danger zone ------------------------------------------------ */
div[class*="st-key-ltcard_danger_"] {
    background: var(--lt-danger-soft);
    border-color: color-mix(in srgb, var(--lt-danger) 30%, transparent);
}
div[class*="st-key-ltcard_danger_"] .lt-section-title { color: var(--lt-danger); }
div[class*="st-key-ltcard_danger_"] button[data-testid="stBaseButton-secondary"] {
    color: var(--lt-danger);
    border-color: color-mix(in srgb, var(--lt-danger) 40%, transparent);
}
div[class*="st-key-ltcard_danger_"] button[data-testid="stBaseButton-primary"] {
    background: var(--lt-danger);
    border-color: var(--lt-danger);
    color: var(--lt-on-danger);
}
div[class*="st-key-ltcard_danger_"] button[data-testid="stBaseButton-primary"]:hover {
    background: var(--lt-danger);
    border-color: var(--lt-danger);
    color: var(--lt-on-danger);
    filter: brightness(1.08);
}

/* ---------- expanders --------------------------------------------------- */
[data-testid="stExpander"] details,
[data-testid="stExpander"] > div > details {
    border: 1px solid var(--lt-border);
    border-radius: 0.7rem;
    background: transparent;
}
[data-testid="stExpander"] summary {
    font-size: 0.84rem;
    font-weight: 600;
    color: var(--lt-muted);
    padding: 0.25rem 0.7rem;
}
[data-testid="stExpander"] summary:hover { color: var(--lt-accent); }

/* ---------- flashcard -------------------------------------------------- */
.lt-flash { text-align: center; padding: 1.3rem 0 0.7rem; }
.lt-flash-word { font-size: 2.6rem; font-weight: 700; letter-spacing: -0.02em; line-height: 1.2; }
.lt-flash-reading { font-size: 1rem; color: var(--lt-muted); margin-top: 0.2rem; }
.lt-flash-translation { font-size: 1.15rem; font-weight: 600; margin-top: 0.9rem; }

/* ---------- word / topic cards ---------------------------------------- */
div[data-testid="stLayoutWrapper"]:has(> div[class*="st-key-word_rail"]) {
    position: sticky;
    top: 1.2rem;
    align-self: flex-start;
    height: fit-content;
}
div[class*="st-key-word_rail"] {
    max-height: calc(100vh - 3rem);
    overflow-y: auto;
    padding-right: 0.15rem;
    scrollbar-width: thin;
}
@media (max-width: 900px) {
    div[data-testid="stLayoutWrapper"]:has(> div[class*="st-key-word_rail"]) {
        position: static;
    }
    div[class*="st-key-word_rail"] {
        max-height: none;
        overflow: visible;
        padding-right: 0;
    }
}
.lt-word {
    font-size: 1.3rem;
    font-weight: 700;
    line-height: 1.3;
    color: var(--lt-text);
    overflow-wrap: anywhere;
}
.lt-reading {
    font-size: 0.82rem;
    font-weight: 500;
    color: var(--lt-muted);
    margin-left: 0.35rem;
}
.lt-translation {
    font-size: 0.92rem;
    color: var(--lt-text);
    opacity: 0.8;
    margin-top: 0.1rem;
}
.lt-example {
    font-size: 0.86rem;
    color: var(--lt-muted);
    font-style: italic;
    margin-top: 0.35rem;
    line-height: 1.45;
}
.lt-divider { height: 1px; background: var(--lt-border); margin: 0.7rem 0 0.55rem; }

/* suggestion cards (chat / lesson side rail) */
div[class*="st-key-wchip_"] {
    background: var(--lt-surface);
    border: 1px solid var(--lt-border);
    border-radius: 1rem;
    padding: 0.7rem 0.75rem 0.5rem;
    margin-bottom: 0.5rem;
    box-shadow: 0 1px 2px var(--lt-shadow-color);
    transition: transform 0.16s ease, border-color 0.16s ease, background 0.16s ease,
        box-shadow 0.16s ease;
}
div[class*="st-key-wchip_"]:hover {
    transform: translateY(-1px);
    border-color: var(--lt-accent-border);
    background: var(--lt-accent-soft);
    box-shadow: 0 12px 28px var(--lt-shadow-hover-color);
}
.lt-wchip-word {
    font-size: 1.12rem;
    font-weight: 650;
    line-height: 1.25;
    overflow-wrap: anywhere;
}
.lt-wchip-reading { font-size: 0.8rem; color: var(--lt-muted); margin-top: 0.05rem; }
div[class*="st-key-wchip_"] button {
    min-height: 0;
    padding: 0.18rem 0.5rem;
    font-size: 0.8rem;
    border-radius: 0.55rem;
    box-shadow: none;
}

/* ---------- thinking shimmer ------------------------------------------ */
.lt-skeleton { display: flex; flex-direction: column; gap: 0.55rem; padding: 0.35rem 0; }
.lt-skeleton span {
    display: block;
    height: 0.7rem;
    border-radius: 999px;
    background: linear-gradient(
        90deg,
        var(--lt-surface-2) 25%,
        var(--lt-accent-soft) 50%,
        var(--lt-surface-2) 75%
    );
    background-size: 200% 100%;
    animation: lt-shimmer 1.4s ease-in-out infinite;
}
.lt-skeleton span:nth-child(1) { width: 88%; }
.lt-skeleton span:nth-child(2) { width: 96%; }
.lt-skeleton span:nth-child(3) { width: 62%; }

/* ---------- misc ------------------------------------------------------- */
.lt-muted { color: var(--lt-muted); font-size: 0.85rem; }
.lt-right { text-align: right; }
.lt-tagrow { display: flex; flex-wrap: wrap; gap: 0.3rem; margin: 0.55rem 0 0.35rem; }
.lt-tag {
    font-size: 0.7rem;
    padding: 0.1rem 0.5rem;
    border-radius: 999px;
    background: var(--lt-surface-2);
    color: var(--lt-muted);
    white-space: nowrap;
}
.lt-tag.is-accent {
    background: var(--lt-accent-soft);
    border: 1px solid var(--lt-accent-border);
    color: var(--lt-accent);
}
.lt-quiz-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.6rem;
    margin-bottom: 0.35rem;
}
.lt-quiz-num {
    display: inline-grid;
    place-items: center;
    min-width: 1.6rem;
    height: 1.6rem;
    padding: 0 0.35rem;
    border-radius: 0.55rem;
    background: var(--lt-accent-soft);
    color: var(--lt-accent);
    font-size: 0.78rem;
    font-weight: 700;
}
.lt-ok, .lt-no {
    border-radius: 0.8rem;
    padding: 0.7rem 0.9rem;
    margin-bottom: 0.45rem;
    border: 1px solid var(--lt-border);
}
.lt-ok { background: var(--lt-success-soft); border-color: color-mix(in srgb, var(--lt-success) 35%, transparent); }
.lt-no { background: var(--lt-danger-soft); border-color: color-mix(in srgb, var(--lt-danger) 35%, transparent); }
.lt-ok-title { color: var(--lt-success); font-weight: 650; }
.lt-no-title { color: var(--lt-danger); font-weight: 650; }

/* ---------- motion ----------------------------------------------------- */
@keyframes lt-fade {
    from { opacity: 0; transform: translateY(4px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes lt-shimmer {
    from { background-position: 200% 0; }
    to   { background-position: -200% 0; }
}
@media (prefers-reduced-motion: reduce) {
    .stApp *, .stApp *::before, .stApp *::after {
        animation-duration: 0.001ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.001ms !important;
    }
}
"""


def inject() -> None:
    """Install design tokens and global CSS. Call once, right after set_page_config."""
    st.markdown(f"<style>{_token_css()}{_BASE_CSS}</style>", unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Presentational helpers
# --------------------------------------------------------------------------


def page_header(icon: str, title: str, subtitle: str | None = None) -> None:
    sub = f'<p class="lt-pagehead-sub">{esc(subtitle)}</p>' if subtitle else ""
    st.html(
        f'<div class="lt-pagehead">'
        f'<div class="lt-pagehead-icon">{esc(icon)}</div>'
        f'<div><h1 class="lt-pagehead-title">{esc(title)}</h1>{sub}</div>'
        f"</div>"
    )


def section_header(title: str, caption: str | None = None, icon: str | None = None) -> None:
    caption_html = f'<span class="lt-section-cap">{esc(caption)}</span>' if caption else ""
    icon_html = f'<span class="lt-ico">{esc(icon)}</span>' if icon else ""
    st.html(
        f'<div class="lt-section">'
        f'<span class="lt-section-title">{icon_html}{esc(title)}</span>'
        f"{caption_html}</div>"
    )


def hero(
    title_html: str,
    greeting: str | None = None,
    subtitle: str | None = None,
    chips: list[str] | None = None,
) -> None:
    """A soft gradient banner. ``title_html`` is trusted markup."""
    greeting_html = f'<div class="lt-hero-greet">{esc(greeting)}</div>' if greeting else ""
    subtitle_html = f'<p class="lt-hero-sub">{esc(subtitle)}</p>' if subtitle else ""
    chips_html = ""
    if chips:
        chips_html = (
            '<div class="lt-chiprow">'
            + "".join(f'<span class="lt-chip">{c}</span>' for c in chips)
            + "</div>"
        )
    st.html(
        f'<div class="lt-hero">{greeting_html}'
        f'<div class="lt-hero-title">{title_html}</div>'
        f"{subtitle_html}{chips_html}</div>"
    )


def empty_state(icon: str, title: str, body: str = "") -> None:
    body_html = f'<p class="lt-empty-body">{esc(body)}</p>' if body else ""
    st.html(
        f'<div class="lt-empty"><div class="lt-empty-icon">{esc(icon)}</div>'
        f'<div class="lt-empty-title">{esc(title)}</div>{body_html}</div>'
    )


def stat_grid(items: list[tuple[str, str, str, str | None]]) -> None:
    """Render metric cards. Items are (icon, value, label, hint|None)."""
    cards = []
    for icon, value, label, hint in items:
        hint_html = f'<div class="lt-stat-hint">{esc(hint)}</div>' if hint else ""
        cards.append(
            f'<div class="lt-stat"><div class="lt-stat-icon">{esc(icon)}</div>'
            f'<div><div class="lt-stat-value">{esc(value)}</div>'
            f'<div class="lt-stat-label">{esc(label)}</div>{hint_html}</div></div>'
        )
    st.html(f'<div class="lt-stats">{"".join(cards)}</div>')


def activity_strip(days: list[tuple[str, bool, bool]]) -> None:
    """Render a 7-day activity strip. Items are (weekday, active, is_today)."""
    cells = []
    for name, active, today in days:
        classes = "lt-day"
        if active:
            classes += " is-on"
        if today:
            classes += " is-today"
        cells.append(
            f'<div class="{classes}"><div class="lt-day-name">{esc(name)}</div>'
            f'<div class="lt-day-dot"></div></div>'
        )
    st.html(f'<div class="lt-activity">{"".join(cells)}</div>')


def stepper(steps: list[str], active: int) -> None:
    """Render a compact phase stepper; ``active`` is a zero-based index."""
    parts = []
    for i, label in enumerate(steps):
        state = "is-done" if i < active else ("is-active" if i == active else "")
        parts.append(
            f'<div class="lt-step {state}"><div class="lt-step-dot">{i + 1}</div>'
            f'<div class="lt-step-label">{esc(label)}</div></div>'
        )
        if i < len(steps) - 1:
            parts.append('<div class="lt-step-line"></div>')
    st.html(f'<div class="lt-steps">{"".join(parts)}</div>')


def score_ring(percent: int, correct: int, total: int) -> None:
    st.html(
        f'<div class="lt-score"><div class="lt-ring" style="--pct:{int(percent)}">'
        f'<div class="lt-ring-inner"><div><div class="lt-ring-value">{int(percent)}%</div>'
        f'<div class="lt-ring-label">score</div></div></div></div>'
        f'<div class="lt-score-copy"><strong>{correct} / {total}</strong> answers correct'
        f'<div class="lt-muted">Keep going — every attempt sharpens recall.</div></div></div>'
    )


def chip(label: str, muted: bool = False) -> str:
    cls = "lt-chip is-muted" if muted else "lt-chip"
    return f'<span class="{cls}">{label}</span>'


def tag(label: str, accent: bool = False) -> str:
    cls = "lt-tag is-accent" if accent else "lt-tag"
    return f'<span class="{cls}">{esc(label)}</span>'


# --------------------------------------------------------------------------
# Pure helpers (unit-tested, no Streamlit calls)
# --------------------------------------------------------------------------


def greeting_for_hour(hour: int) -> str:
    """A friendly time-of-day greeting for a 24h clock hour."""
    if 5 <= hour < 12:
        return "Good morning"
    if 12 <= hour < 18:
        return "Good afternoon"
    if 18 <= hour < 23:
        return "Good evening"
    return "Late-night study session"


def activity_days(
    reviewed_dates: list[str], today_iso: str, days: int = 7
) -> list[tuple[str, bool, bool]]:
    """Last ``days`` calendar days as (weekday, active, is_today) tuples.

    ``reviewed_dates`` may contain duplicate or malformed ISO date strings.
    """
    from datetime import date, timedelta

    try:
        today = date.fromisoformat(today_iso)
    except ValueError:
        return []

    active: set[str] = set()
    for raw in reviewed_dates:
        try:
            active.add(date.fromisoformat(str(raw)[:10]).isoformat())
        except ValueError:
            continue

    out: list[tuple[str, bool, bool]] = []
    for offset in range(days - 1, -1, -1):
        day = today - timedelta(days=offset)
        iso = day.isoformat()
        out.append((day.strftime("%a"), iso in active, day == today))
    return out
