//! A minimal build of the [Chrome DevTools frontend] (Elements, Console and
//! Network panels), for embedding in a Chrome DevTools Protocol server such
//! as Blitz's.
//!
//! Serve the files from [`files`] over HTTP and open
//! `http://HOST:PORT/devtools_app.html?ws=HOST:PORT/devtools/page/ID`, where
//! the `ws` parameter is the WebSocket address of the CDP target to inspect.
//! Serve `.js` files with a JavaScript `Content-Type`: browsers refuse to run
//! module scripts otherwise.
//!
//! The archive includes the license texts of devtools-frontend and the
//! third-party code it bundles, under `LICENSES/`.
//!
//! [Chrome DevTools frontend]: https://github.com/ChromeDevTools/devtools-frontend

use std::collections::HashMap;
use std::io::{self, Read};

/// The frontend's files, as a brotli-compressed ustar archive
pub static ARCHIVE: &[u8] = include_bytes!("../dist.tar.br");

/// The path of the frontend's page
pub const ENTRY_PATH: &str = "devtools_app.html";

/// Decompress and unpack [`ARCHIVE`] into a map from path (relative to the
/// frontend's root, e.g. `core/sdk/sdk.js`) to file contents
pub fn files() -> io::Result<HashMap<String, Vec<u8>>> {
    let mut tar = Vec::new();
    brotli_decompressor::Decompressor::new(ARCHIVE, 64 * 1024).read_to_end(&mut tar)?;

    let mut files = HashMap::new();
    let mut rest = &tar[..];
    // The archive ends with zeroed blocks
    while rest.len() >= 512 && rest[0] != 0 {
        let header = &rest[..512];
        let name = field(&header[0..100])?;
        let size = usize::from_str_radix(field(&header[124..136])?.trim(), 8)
            .map_err(|_| invalid("invalid entry size"))?;
        let end = 512 + size;
        let data = rest
            .get(512..end)
            .ok_or_else(|| invalid("truncated archive"))?;
        // Regular files only
        if matches!(header[156], b'0' | 0) {
            files.insert(name.to_string(), data.to_vec());
        }
        rest = rest.get(end.next_multiple_of(512)..).unwrap_or_default();
    }
    Ok(files)
}

/// A NUL-terminated ustar header field
fn field(bytes: &[u8]) -> io::Result<&str> {
    let len = bytes.iter().position(|&b| b == 0).unwrap_or(bytes.len());
    std::str::from_utf8(&bytes[..len]).map_err(|_| invalid("invalid header field"))
}

fn invalid(message: &str) -> io::Error {
    io::Error::new(io::ErrorKind::InvalidData, message)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn unpacks_the_frontend() {
        let files = files().unwrap();
        let entry = std::str::from_utf8(&files[ENTRY_PATH]).unwrap();
        // The page loads the devtools_app entrypoint, which must be present
        let script = "entrypoints/devtools_app/devtools_app.js";
        assert!(entry.contains(script));
        assert!(!files[script].is_empty());
        assert!(files.contains_key("core/i18n/locales/en-US.json"));
        assert!(files.contains_key("LICENSES/devtools-frontend.txt"));
    }
}
