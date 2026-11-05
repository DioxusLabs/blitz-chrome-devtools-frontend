#!/usr/bin/env python3
"""Package the files reachable from devtools_app.html out of a devtools-frontend
build.

Follows static imports, dynamic import() calls and
`new URL('...', import.meta.url)` references (workers, images) from the
devtools_app entrypoint, so other entrypoints and modules only used by panels
we don't register are left out. Copies them, plus the license texts of
devtools-frontend and the third-party code it bundles (into LICENSES/), to a
dist directory and writes a deterministic (sorted, zeroed timestamps and
owners) ustar archive of it.

Usage: package.py <devtools-frontend dir> <build gen dir> <dist dir> <tar file>
"""

import io
import json
import os
import re
import shutil
import sys
import tarfile

ENTRY = "devtools_app.html"
# Resources loaded via computed paths, which the reference scan can't find
ALWAYS = [
    "core/i18n/locales/en-US.json",
]

# `from"x"`, `import"x"`, `import("x")`, `export*from"x"` (minified or not)
MODULE_RE = re.compile(r"""(?:\bfrom|\bimport)\s*\(?\s*["']([^"'\s]+\.m?js)["']""")
URL_RE = re.compile(r"""new\s+URL\(\s*["']([^"'\s]+)["']\s*,\s*import\.meta\.url\s*\)""")
HTML_RE = re.compile(r"""<(?:script|link)[^>]+(?:src|href)=["']\./([^"']+)["']""")
LICENSE_FILE_RE = re.compile(r"^License File:\s*(\S+)", re.MULTILINE)


def references(path, text):
    if path.endswith(".html"):
        refs = HTML_RE.findall(text)
    elif path.endswith((".js", ".mjs")):
        refs = MODULE_RE.findall(text) + URL_RE.findall(text)
    else:
        return []
    base = os.path.dirname(path)
    out = []
    for ref in refs:
        if "://" in ref or ref.startswith("data:"):
            continue
        out.append(os.path.normpath(os.path.join(base, ref)))
    return out


def reachable_files(gen_dir):
    src = os.path.join(gen_dir, "front_end")
    shipped = {
        f.removeprefix("front_end/")
        for f in json.load(open(os.path.join(gen_dir, "input_grd_files.json")))
    }
    seen, missing = set(), set()
    queue = [ENTRY, *ALWAYS]
    while queue:
        rel = queue.pop()
        if rel in seen:
            continue
        seen.add(rel)
        if rel not in shipped:
            missing.add(rel)
            continue
        text = open(os.path.join(src, rel), encoding="utf-8", errors="replace").read()
        queue.extend(references(rel, text))
    if missing:
        print(f"{len(missing)} referenced files not in the build (ignored):")
        for rel in sorted(missing):
            print(f"  {rel}")
    return sorted(seen - missing)


def license_files(devtools_dir, files):
    """(dist path, source path) of the license of devtools-frontend and of each
    bundled third-party package"""
    licenses = [("LICENSES/devtools-frontend.txt", os.path.join(devtools_dir, "LICENSE"))]
    third_party = sorted({f.split("/")[1] for f in files if f.startswith("third_party/")})
    for name in third_party:
        pkg = os.path.join(devtools_dir, "front_end", "third_party", name)
        readme = open(os.path.join(pkg, "README.chromium"), encoding="utf-8").read()
        match = LICENSE_FILE_RE.search(readme)
        if not match:
            sys.exit(f"no 'License File:' in {pkg}/README.chromium")
        licenses.append((f"LICENSES/{name}.txt", os.path.join(pkg, match.group(1))))
    return licenses


def write_tar(dist_dir, tar_path):
    paths = sorted(
        os.path.relpath(os.path.join(root, f), dist_dir)
        for root, _, names in os.walk(dist_dir)
        for f in names
    )
    with tarfile.open(tar_path, "w", format=tarfile.USTAR_FORMAT) as tar:
        for rel in paths:
            # Readers can then rely on the plain 100-byte ustar name field
            assert len(rel) < 100, f"path too long for the archive: {rel}"
            data = open(os.path.join(dist_dir, rel), "rb").read()
            info = tarfile.TarInfo(rel)
            info.size = len(data)
            info.mode = 0o644
            info.mtime = 0
            tar.addfile(info, io.BytesIO(data))


def main(devtools_dir, gen_dir, dist_dir, tar_path):
    files = reachable_files(gen_dir)
    copies = [(f, os.path.join(gen_dir, "front_end", f)) for f in files]
    # Browsers request it from the server root
    copies.append(("favicon.ico", os.path.join(gen_dir, "favicon.ico")))
    copies += license_files(devtools_dir, files)

    shutil.rmtree(dist_dir, ignore_errors=True)
    total = 0
    for rel, src in copies:
        dst = os.path.join(dist_dir, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
        total += os.path.getsize(dst)
    write_tar(dist_dir, tar_path)
    print(f"{len(copies)} files, {total / 1e6:.2f} MB -> {dist_dir}, {tar_path}")


if __name__ == "__main__":
    main(*sys.argv[1:])
