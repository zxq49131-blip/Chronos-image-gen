# zhexueqi-image-gen

Generate images through the zhexueqi.xyz API.

This patched version fixes the working endpoint/model defaults and SSE parsing used by the current API response.

## Quick Start

```bash
export ZHEXUEQI_TOKEN="zxq_..."
python zhexueqi_gen.py "a crisp 2D game inventory icon of wooden logs, transparent background"
```

Windows PowerShell:

```powershell
$env:ZHEXUEQI_TOKEN="zxq_..."
python .\zhexueqi_gen.py "a crisp 2D game inventory icon of wooden logs, transparent background"
```

## Defaults

- Endpoint: `https://hk-api.zhexueqi.xyz/responses`
- Model: `gpt-image-2`
- Quality: `low`
- Size: `1024x1024`
- Format: `png`
- Streaming: enabled

Override the endpoint when needed:

```bash
export ZHEXUEQI_URL="https://hk-api.zhexueqi.xyz/responses"
```

## Usage

```text
python zhexueqi_gen.py "prompt" [options]

Options:
  -n N          Number of images (1-10, default 1)
  -q QUALITY    low | medium | high (default low)
  -s SIZE       e.g. 1024x1024, 2048x2048, 2880x2880, auto
  -f FORMAT     png | webp (default png)
  -r PATH       Reference image path (repeatable)
  -o DIR        Output directory (default output)
  -m MODEL      gpt-image-2 (default) | grok-imagine-image
```

## Examples

```bash
python zhexueqi_gen.py "a cozy colony sim main menu background, painterly, warm dawn" -q high -s 2048x2048 -o output/main_menu
python zhexueqi_gen.py "a crisp game inventory icon of stone chunks, transparent background" -n 4 -q medium -s 1024x1024 -o output/icons
python zhexueqi_gen.py "redraw this as a clean UI icon" -r reference.png -q medium -s 1024x1024
```

## Patch Notes

- Changed the default endpoint from `https://zhexueqi.xyz/respones` to `https://hk-api.zhexueqi.xyz/responses`.
- Changed the default model from `gpt-5.5` to `gpt-image-2`.
- Added `ZHEXUEQI_URL` environment override.
- Fixed SSE parsing for top-level `partial_image_b64` events as well as nested `item` image fields.
- Kept multi-token parallel generation behavior.

## Token Notes

`ZHEXUEQI_TOKEN` must be an image-generation group key. Non-image/chat-only keys may fail authorization.

Do not commit real tokens.
