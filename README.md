# blitz-devtools-frontend

A minimal build of the [Chrome DevTools frontend](https://github.com/ChromeDevTools/devtools-frontend)
for inspecting [Blitz](https://github.com/DioxusLabs/blitz) documents through Blitz's Chrome DevTools
Protocol server. It only includes the panels Blitz supports (Elements, Console and Network), which makes
it about half the size of the frontend that ships with Chrome.

The crate embeds the frontend as a brotli-compressed archive (about 2 MB) for CDP servers to serve
locally.

## Building

```sh
./scripts/build.sh
```

This checks out devtools-frontend (with [depot_tools](https://commondatastorage.googleapis.com/chrome-infra-docs/flat/depot_tools/docs/html/depot_tools_tutorial.html))
at the revision pinned in `scripts/build.sh`, applies `overlay/` (an entrypoint and shell that only
register the panels Blitz supports), builds it in release mode, and packages the files reachable from
`devtools_app.html` into `dist/` and `dist.tar.br`. The first run downloads about 3 GB.

## Publishing

CI builds and checks every push and pull request. To publish to crates.io, bump the version in
`Cargo.toml` and run the workflow manually with "publish crate" ticked (it needs a
`CARGO_REGISTRY_TOKEN` secret), or run `./scripts/build.sh && cargo publish` locally.

## License

The frontend is licensed under the BSD-3-Clause license of devtools-frontend (see `LICENSE`). It bundles
third-party code under the MIT, BSD-3-Clause and Apache-2.0 licenses, whose license texts are included
in the archive under `LICENSES/`.
