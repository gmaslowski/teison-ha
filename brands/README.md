# Home Assistant "brands" assets for `teison`

This directory stages the logo/icon assets that Home Assistant's frontend uses to
display the **Teison EV Charger** integration. They are **not** consumed from this
repo at runtime — Home Assistant loads brand assets from the central
[home-assistant/brands](https://github.com/home-assistant/brands) repository. These
files are kept here only so they are version-controlled and ready to contribute.

## Files

Staged under `custom_integrations/teison/`:

| File          | Dimensions | Purpose                                    |
|---------------|------------|--------------------------------------------|
| `icon.png`    | 256 x 256  | Square icon                                |
| `icon@2x.png` | 512 x 512  | Square icon, hDPI (2x)                     |
| `logo.png`    | 410 x 128  | Full wordmark logo                         |
| `logo@2x.png` | 820 x 256  | Full wordmark logo, hDPI (2x)              |

All four are 8-bit RGBA PNGs with a transparent background, trimmed to the artwork.

Source artwork: the official Teison wordmark from https://www.teison.com/
(`https://d.bjyyb.net/sites/64500/64807/1779427417916318764605591552.webp`,
the flat-blue "Teison" wordmark with the green-leaf dot over the "i"), converted
from WebP to PNG and rescaled.

## home-assistant/brands requirements (why the files look the way they do)

From the brands repo spec:

- **Format:** PNG, 8-bit RGBA, **transparent background** (no white/solid box).
- **Trimmed:** no surrounding transparent padding around the artwork (the `icon.*`
  square is the one intentional exception — see caveat below).
- **`icon.png` must be exactly 256 x 256** and **`icon@2x.png` exactly 512 x 512**,
  both square.
- **`logo.*`** is the full/wide logo; keep `logo.png` height <= 128 px and width
  <= 512 px. `logo@2x.png` is exactly double `logo.png`.
- File names are lowercase; the `@2x` variants are literal.

## Caveat — square icon quality (needs a human decision)

Teison ships only a **horizontal wordmark**; there is no dedicated square brand
mark / symbol. `icon.png` / `icon@2x.png` here are the wordmark centered on a
transparent square canvas (letterboxed). This is valid (square, transparent,
correct sizes) but the artwork occupies only a thin horizontal band, so it reads
small at icon sizes. A brands reviewer may prefer a purpose-designed square mark
(e.g. the "T" or the leaf glyph). If so, a designer should supply a proper square
`icon.png` before/after the PR. The `logo.*` files need no such caveat.

## How to contribute these to home-assistant/brands

1. Fork https://github.com/home-assistant/brands and clone your fork.
2. Create the target directory and copy these four files into it:

   ```bash
   mkdir -p custom_integrations/teison
   cp /path/to/teison-ha/brands/custom_integrations/teison/*.png \
      custom_integrations/teison/
   ```

   > Note the `custom_integrations/` prefix (not `core_integrations/`) — `teison`
   > is a HACS custom integration.

3. Validate locally with the brands repo's own tooling (run from the brands repo
   root):

   ```bash
   python3 -m script  # runs the brands image validation (sizes, format, alpha, trim)
   ```

   (See the brands repo `README.md` / `script/` for the exact current command;
   they also run this validation in CI on the PR.)

4. Commit and open a PR against `home-assistant/brands` titled something like
   `Add teison`. The PR must contain only the `custom_integrations/teison/` files.

## After the PR is merged

Once `teison` exists in home-assistant/brands, the HACS validation no longer needs
to skip the brands check. Drop the `ignore: brands` line from
`.github/workflows/validate.yml`:

```yaml
      - uses: hacs/action@main
        with:
          category: integration
          # Drop once teison is added to home-assistant/brands (logo/icon PR).
          ignore: brands   # <-- remove this line (and the comment above it)
```
