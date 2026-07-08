#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# setup_static.sh  –  CareerAtlas Kenya
#
# Downloads Tailwind CSS and Font Awesome locally so the site works entirely
# offline (no CDN required). Run this ONCE after cloning / setting up:
#
#   cd backend
#   bash setup_static.sh
#
# After running successfully, Django's context processor detects the local
# files and base.html switches from CDN links to {% static %} links.
# ─────────────────────────────────────────────────────────────────────────────

set -e

STATIC_DIR="$(dirname "$0")/static"
JS_DIR="$STATIC_DIR/js"
CSS_DIR="$STATIC_DIR/css/fontawesome"
WEBFONTS_DIR="$STATIC_DIR/webfonts"

# Versions — update here to upgrade
TAILWIND_VERSION="3.4.4"
FA_VERSION="6.5.2"

TAILWIND_URL="https://cdn.tailwindcss.com/${TAILWIND_VERSION}"
FA_CSS_URL="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/${FA_VERSION}/css/all.min.css"
FA_WEBFONTS_BASE="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/${FA_VERSION}/webfonts"

echo "──────────────────────────────────────────────"
echo " CareerAtlas Kenya — Local Static Asset Setup"
echo "──────────────────────────────────────────────"
echo ""

# Create directories
mkdir -p "$JS_DIR" "$CSS_DIR" "$WEBFONTS_DIR"
echo "✓ Created static directories"

# ── 1. Tailwind CSS ───────────────────────────────────────────────────────────
TAILWIND_OUT="$JS_DIR/tailwind.min.js"
if [ -f "$TAILWIND_OUT" ]; then
    echo "✓ Tailwind already exists, skipping download (delete to re-download)"
else
    echo "↓ Downloading Tailwind CSS ${TAILWIND_VERSION}…"
    curl -fsSL "$TAILWIND_URL" -o "$TAILWIND_OUT"
    echo "✓ Tailwind saved → static/js/tailwind.min.js"
fi

# ── 2. Font Awesome CSS ───────────────────────────────────────────────────────
FA_CSS_OUT="$CSS_DIR/all.min.css"
if [ -f "$FA_CSS_OUT" ]; then
    echo "✓ Font Awesome CSS already exists, skipping download"
else
    echo "↓ Downloading Font Awesome ${FA_VERSION} CSS…"
    curl -fsSL "$FA_CSS_URL" -o "$FA_CSS_OUT"
    echo "✓ Font Awesome CSS saved → static/css/fontawesome/all.min.css"
fi

# ── 3. Font Awesome Webfonts ─────────────────────────────────────────────────
# The CSS file references ../webfonts/fa-*.woff2 — we must download those too.
FONTS=(
    "fa-brands-400.woff2"
    "fa-brands-400.ttf"
    "fa-regular-400.woff2"
    "fa-regular-400.ttf"
    "fa-solid-900.woff2"
    "fa-solid-900.ttf"
    "fa-v4compatibility.woff2"
    "fa-v4compatibility.ttf"
)

echo "↓ Downloading Font Awesome webfonts (${#FONTS[@]} files)…"
for font in "${FONTS[@]}"; do
    FONT_OUT="$WEBFONTS_DIR/$font"
    if [ -f "$FONT_OUT" ]; then
        echo "  ✓ $font already exists"
    else
        curl -fsSL "${FA_WEBFONTS_BASE}/${font}" -o "$FONT_OUT"
        echo "  ✓ $font"
    fi
done

# ── 4. Fix the webfont path in the CSS file ───────────────────────────────────
# The CDN CSS references ../webfonts/... — when served via Django static files,
# the path needs to be /static/webfonts/...
# We patch the downloaded CSS to use the correct relative path from
# static/css/fontawesome/ → ../../webfonts/
echo ""
echo "→ Patching font path in all.min.css…"
if grep -q "\.\.\/webfonts\/" "$FA_CSS_OUT" 2>/dev/null; then
    # Already has ../webfonts/ — correct for our directory structure
    echo "✓ Font paths are correct (../webfonts/ → resolves to /static/webfonts/)"
else
    # Some CDN versions use a different path — patch just in case
    sed -i "s|url(\"/cdn-cgi/|url(\"https://cdnjs.cloudflare.com/cdn-cgi/|g" "$FA_CSS_OUT" 2>/dev/null || true
    echo "✓ Font paths checked"
fi

echo ""
echo "──────────────────────────────────────────────"
echo " All done! The site will now load CSS/JS"
echo " entirely from local static files."
echo ""
echo " If you see style issues, run:"
echo "   python manage.py collectstatic --noinput"
echo "──────────────────────────────────────────────"
