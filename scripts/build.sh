#!/usr/bin/env bash
# Build a minimal Chrome DevTools frontend for Blitz.
#
# Checks out devtools-frontend at $DEVTOOLS_REVISION (with depot_tools) into
# build/, copies overlay/ over it (a devtools_app entrypoint and shell that only
# register the panels Blitz supports), builds it in release mode (bundled and
# minified), then copies the files reachable from devtools_app.html (and the
# license texts) into dist/ and packs them into dist.tar.br, which the crate
# embeds.
set -euo pipefail

# The DevTools revision shipped in Chrome 158 stable
DEVTOOLS_REVISION="${DEVTOOLS_REVISION:-a7812cf737f651c890965e0c274dd52db2520d33}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/build"
SRC="$BUILD/devtools-frontend"
OUT="$SRC/out/BlitzNinja"

mkdir -p "$BUILD"
if [ ! -d "$BUILD/depot_tools" ]; then
  git clone --depth 1 https://chromium.googlesource.com/chromium/tools/depot_tools.git "$BUILD/depot_tools"
fi
export PATH="$BUILD/depot_tools:$PATH"

# Skip downloading the Emscripten toolchain (about 770 MB unpacked), which is
# only needed for DevTools' C++ debugging extension. (Chrome for Testing, which
# is only used by DevTools' tests, can't be skipped: custom_deps doesn't apply
# to GCS dependencies, and its DEPS condition can't be turned off without also
# dropping Node.)
cat > "$BUILD/.gclient" <<'EOF'
solutions = [
  {
    "name": "devtools-frontend",
    "url": "https://chromium.googlesource.com/devtools/devtools-frontend.git",
    "deps_file": "DEPS",
    "managed": False,
    "custom_deps": {},
    "custom_hooks": [
      {"name": "emscripten"},
    ],
  },
]
EOF

# Undo a previous overlay so the sync can check out the revision cleanly
if [ -d "$SRC/.git" ]; then
  git -C "$SRC" checkout -- front_end
fi
(cd "$BUILD" && gclient sync --revision "devtools-frontend@$DEVTOOLS_REVISION" --no-history --shallow)

cp -R "$ROOT/overlay/front_end/." "$SRC/front_end/"

# Ninja rather than Siso (the default), which rebuilds everything after the
# checkout is restored from CI's cache
(cd "$SRC" && gn gen "$OUT" --args='is_debug=false use_siso=false')
# Build the frontend and its file list, but not the default target: its
# assert_grd check fails because the panels we don't import aren't built
autoninja -C "$OUT" front_end :favicon :input_grd_files

python3 "$ROOT/scripts/package.py" "$SRC" "$OUT/gen" "$ROOT/dist" "$ROOT/dist.tar"
# devtools-frontend's bundled Node
vpython3 "$SRC/third_party/node/node.py" --output "$ROOT/scripts/compress.mjs" "$ROOT/dist.tar" "$ROOT/dist.tar.br"
rm "$ROOT/dist.tar"
echo "$(du -h "$ROOT/dist.tar.br" | cut -f1) $ROOT/dist.tar.br"
