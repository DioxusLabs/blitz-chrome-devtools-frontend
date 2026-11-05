// Compress a file with brotli at maximum quality and a 16 MiB window
// (whole-archive brotli beats per-file compression on the frontend's many
// similar modules). Usage: compress.mjs <input> <output>
import fs from 'node:fs';
import zlib from 'node:zlib';

const [input, output] = process.argv.slice(2);
const data = fs.readFileSync(input);
fs.writeFileSync(output, zlib.brotliCompressSync(data, {
  params: {
    [zlib.constants.BROTLI_PARAM_QUALITY]: zlib.constants.BROTLI_MAX_QUALITY,
    [zlib.constants.BROTLI_PARAM_LGWIN]: 24,
    [zlib.constants.BROTLI_PARAM_SIZE_HINT]: data.length,
  },
}));
