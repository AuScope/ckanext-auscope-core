"""Static checks of the shared theme CSS, bundles and assets (no CKAN app)."""
import pathlib
import re

import pytest
import yaml

from ckanext.auscope_core.plugin import _apply_default

PACKAGE_DIR = pathlib.Path(__file__).resolve().parent.parent
ASSETS_DIR = PACKAGE_DIR / "assets"
CSS_DIR = ASSETS_DIR / "css"
CSS_FILES = ["tokens.css", "base.css", "components.css", "branding.css"]
PUBLIC_DIR = PACKAGE_DIR / "public" / "auscope_core"
IMAGES_DIR = PUBLIC_DIR / "images"

TEXT_PAIRS = [  # >= 4.5
    ("--auscope-color-text", "--auscope-color-white"),
    ("--auscope-color-text", "--auscope-color-surface"),
    ("--auscope-color-primary", "--auscope-color-white"),
    ("--auscope-color-primary", "--auscope-color-surface"),
    ("--auscope-color-on-primary", "--auscope-color-primary"),
    ("--auscope-color-on-primary", "--auscope-color-primary-hover"),
    ("--auscope-color-primary-hover", "--auscope-color-white"),
    ("--auscope-footer-color", "--auscope-footer-bg"),
    ("--auscope-nav-active-color", "--auscope-masthead-bg"),
    ("--auscope-masthead-color", "--auscope-masthead-bg"),
    ("--auscope-home-search-color", "--auscope-home-search-bg"),
    ("--auscope-color-heading", "--auscope-home-search-bg"),
    ("--auscope-color-on-primary", "--auscope-home-search-tags-bg"),
]
NON_TEXT_PAIRS = [  # >= 3.0
    ("--auscope-focus-ring-color", "--auscope-color-white"),
    ("--auscope-focus-ring-color", "--auscope-color-surface"),
    ("--auscope-focus-ring-color", "--auscope-home-search-bg"),
    ("--auscope-nav-active-indicator", "--auscope-masthead-bg"),
]


# --- tiny CSS helpers -------------------------------------------------------

def _css(name):
    return (CSS_DIR / name).read_text(encoding="utf-8")


def _strip_comments(text):
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)


def rules(text):
    """Yield (selector, body) for each innermost declaration block.

    Selectors inside an at-rule are prefixed with the at-rule prelude.
    """
    text = _strip_comments(text)
    stack = []
    start = 0
    for i, ch in enumerate(text):
        if ch == "{":
            stack.append(" ".join(text[start:i].split()))
            start = i + 1
        elif ch == "}":
            body = text[start:i]
            selector = stack.pop()
            if "{" not in body and selector:
                prefix = " ".join(stack)
                yield (f"{prefix} {selector}".strip(), body)
            start = i + 1


def declarations(body):
    result = {}
    for part in body.split(";"):
        if ":" in part:
            prop, value = part.split(":", 1)
            result[prop.strip()] = " ".join(value.split())
    return result


def _selectors(selector_text):
    return [s.strip() for s in selector_text.split(",")]


def _blocks(name, selector):
    """Declarations of each rule in ``name`` whose selector is exactly ``selector``."""
    return [
        declarations(body)
        for sel, body in rules(_css(name))
        if _selectors(sel) == [selector]
    ]


def _tokens():
    tokens = {}
    for selector, body in rules(_css("tokens.css")):
        tokens.update(declarations(body))
    return tokens


def _resolve(name, tokens):
    value = tokens[name]
    while True:
        match = re.fullmatch(r"var\((--[\w-]+)\)", value)
        if not match:
            return value
        value = tokens[match.group(1)]


def _hex_to_rgb(value):
    value = value.lstrip("#")
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def _luminance(rgb):
    def channel(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(fg, bg):
    lighter, darker = sorted((_luminance(fg), _luminance(bg)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


# --- bundles ----------------------------------------------------------------

def test_css_bundle_preloads_tokens():
    bundles = yaml.safe_load((ASSETS_DIR / "webassets.yml").read_text())
    assert bundles["auscope_core-css"]["extra"]["preload"] == [
        "auscope_core/auscope_core-tokens"
    ]


# --- tokens -----------------------------------------------------------------

def test_every_used_token_is_defined():
    defined = set(_tokens())
    for name in CSS_FILES:
        used = set(re.findall(r"var\((--auscope-[\w-]+)", _strip_comments(_css(name))))
        assert used <= defined, f"{name}: undefined {sorted(used - defined)}"


@pytest.mark.parametrize("name", CSS_FILES)
def test_css_has_no_url_references(name):
    assert "url(" not in _css(name)


@pytest.mark.parametrize("fg, bg", TEXT_PAIRS)
def test_text_contrast(fg, bg):
    tokens = _tokens()
    ratio = _contrast(
        _hex_to_rgb(_resolve(fg, tokens)), _hex_to_rgb(_resolve(bg, tokens))
    )
    assert ratio >= 4.5, f"{fg} on {bg}: {ratio:.2f}"


@pytest.mark.parametrize("fg, bg", NON_TEXT_PAIRS)
def test_non_text_contrast(fg, bg):
    tokens = _tokens()
    ratio = _contrast(
        _hex_to_rgb(_resolve(fg, tokens)), _hex_to_rgb(_resolve(bg, tokens))
    )
    assert ratio >= 3.0, f"{fg} on {bg}: {ratio:.2f}"


def test_rgb_triplets_match_colours():
    tokens = _tokens()
    pairs = [name for name in tokens if f"{name}-rgb" in tokens]
    assert pairs
    for name in pairs:
        triplet = tuple(
            int(c) for c in _resolve(f"{name}-rgb", tokens).split(",")
        )
        assert triplet == _hex_to_rgb(_resolve(name, tokens)), name


@pytest.mark.parametrize("name", CSS_FILES)
def test_tokens_declared_only_on_root(name):
    for selector, body in rules(_css(name)):
        if any(p.startswith("--auscope-") for p in declarations(body)):
            if name == "tokens.css":
                assert selector == ":root"
            else:
                # Other files may only re-point tokens on component containers
                # (dark-surface rule); never define them globally.
                assert ":root" not in selector
    if name == "tokens.css":
        assert "[data-bs-theme" not in _css(name)


# --- dark surfaces and focus ------------------------------------------------

@pytest.mark.parametrize(
    "selector, value",
    [
        (".site-footer", "var(--auscope-footer-color)"),
        (".homepage .module-search .tags", "var(--auscope-color-on-primary)"),
    ],
)
def test_surfaces_set_focus_ring_and_heading_colour(selector, value):
    blocks = _blocks("branding.css", selector)
    assert blocks, selector
    merged = {}
    for block in blocks:
        assert block.get("--bs-heading-color") != "inherit"
        assert block.get("--auscope-focus-ring-color") != "inherit"
        merged.update(block)
    assert merged.get("--auscope-focus-ring-color") == value
    assert merged.get("--bs-heading-color") == value


def test_light_homepage_search_box_sets_its_text_colour():
    # CKAN 2.12.1 sets "color: #fff" on .homepage .module-search.
    blocks = _blocks("branding.css", ".homepage .module-search .search-form")
    assert len(blocks) == 1
    assert blocks[0]["color"] == "var(--auscope-home-search-color)"
    assert not _blocks("branding.css", ".homepage .module-search")


def test_homepage_search_button_has_inset_primary_ring():
    blocks = _blocks("branding.css", ".homepage .module-search .search-input .btn")
    assert len(blocks) == 1
    block = blocks[0]
    assert block["--auscope-focus-ring-color"] == "var(--auscope-color-primary)"
    assert block["--auscope-focus-ring-offset"].startswith("calc(-1")


def test_focus_rule_covers_ckan_outline_resets():
    focus_selectors = None
    for selector, body in rules(_css("base.css")):
        if "outline" in declarations(body) and ":focus-visible" in _selectors(selector):
            focus_selectors = _selectors(selector)
    assert focus_selectors is not None
    for expected in (
        ".page-header .nav-tabs li a:focus-visible",
        ".btn-close:focus-visible",
        ".accordion-button:focus-visible",
        ".navbar-toggler:focus-visible",
    ):
        assert expected in focus_selectors


# --- masthead ---------------------------------------------------------------

def test_logo_size_neutralises_ckan_limits():
    blocks = _blocks("branding.css", ".masthead .navbar .logo img")
    assert blocks
    block = blocks[0]
    assert block["min-block-size"] == "0"
    assert block["max-block-size"] == "none"


def test_nav_hover_block_covers_active_states():
    matches = [
        _selectors(selector)
        for selector, body in rules(_css("branding.css"))
        if declarations(body).get("background-color") == "var(--auscope-color-primary)"
        and ".masthead .main-navbar ul li:hover a" in _selectors(selector)
    ]
    assert len(matches) == 1
    selectors = matches[0]
    assert ".masthead .main-navbar ul li.active:hover a" in selectors
    assert ".masthead .main-navbar ul li.active a:focus-visible" in selectors


# --- assets -----------------------------------------------------------------

def test_every_image_is_licensed():
    licences = (PUBLIC_DIR / "ASSETS-LICENSES.md").read_text(encoding="utf-8")
    images = sorted(IMAGES_DIR.glob("*.png"))
    assert len(images) == 4
    for image in images:
        assert image.name in licences


# --- logo and favicon default rule -------------------------------------------

@pytest.mark.parametrize(
    "config_, expected",
    [
        ({"k": "/ckan.png"}, {"k": "/auscope.png"}),
        ({"k": "/custom.png"}, {"k": "/custom.png"}),
        ({"k": ""}, {"k": ""}),
        ({}, {}),
    ],
    ids=["default-replaced", "custom-kept", "empty-kept", "missing-unchanged"],
)
def test_apply_default(config_, expected):
    _apply_default(config_, "k", "/ckan.png", "/auscope.png")
    assert config_ == expected
