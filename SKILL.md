---
name: zhexueqi-image-gen
description: Call image generation models through the zhexueqi.xyz API. Use this skill when the user wants to generate images via the zhexueqi.xyz API, needs to set up image generation from this endpoint, or asks about calling image models without an OpenAI API key. Covers token setup, model selection, API format (Responses API + image_generation tool), streaming SSE parsing, reference images, size/quality constraints, and multi-token parallel generation.
---

# zhexueqi.xyz Image Generation

Generate images via `https://zhexueqi.xyz/responses` using `gpt-image-2` by default with the `image_generation` tool. No OpenAI API key required; use a provider token from an image-generation/image-generation subscription group.

Model selection rules:
- Tell users the supported image models are `gpt-image-2` and `grok-imagine-image`.
- Default to `gpt-image-2`.
- Use `grok-imagine-image` only when the user explicitly requests Grok.
- If the user does not provide a token/key and no `ZHEXUEQI_TOKEN` is set, ask them to set one.
- The token/key must belong to an image-generation or image-generation subscription group; general chat/API keys may fail authorization.

## Quick Start

```bash
# Set your token
export ZHEXUEQI_TOKEN="zxq_..."

# Generate an image
python zhexueqi_gen.py "a photorealistic red apple on a white table"
```

## Token Setup

Get a token from the API provider. Store it in an environment variable or `.env` file. If no token is provided and `ZHEXUEQI_TOKEN` is unset, stop and remind the user to set one before generation.

Important: the token must be from an image-generation or image-generation subscription group. Non-image/chat-only keys may be valid API keys but still fail for image generation.

```
ZHEXUEQI_TOKEN=zxq_xxxxxxxx
```

Optionally add more tokens for parallel generation when `n > 1`:

```
ZHEXUEQI_TOKEN_2=zxq_yyyyyyyy
ZHEXUEQI_TOKEN_3=zxq_zzzzzzzz
```

## API Format

### Endpoint

```
POST https://zhexueqi.xyz/responses
Authorization: Bearer $ZHEXUEQI_TOKEN
Content-Type: application/json
```

### Request Payload

```json
{
  "model": "gpt-image-2",
  "input": "Generate a photorealistic image of a red apple on a white table",
  "tools": [{
    "type": "image_generation",
    "action": "generate",
    "quality": "high",
    "size": "2048x2048",
    "output_format": "png"
  }],
  "tool_choice": "required",
  "stream": true
}
```

### Critical Parameters

| Parameter | Value | Why |
|-----------|-------|-----|
| `tools[].action` | `"generate"` | **Required.** Without this the model returns text instead of images |
| `tool_choice` | `"required"` | Force image generation; `"auto"` will often bypass the tool |
| `stream` | `true` | **Required for large images.** Non-stream requests hit a ~60s gateway timeout |

### Input Formats

**Plain text (no reference images):**
```json
"input": "Generate an image of a cat"
```

**With reference images (multi-modal):**
```json
"input": [
  {
    "role": "user",
    "content": [
      {"type": "input_image", "image_url": "data:image/png;base64,iVBORw0KGgo..."},
      {"type": "input_text", "text": "draw a blue square next to this cat"}
    ]
  }
]
```

## Response Parsing

The API returns an **SSE stream** (Server-Sent Events). Images are in `data:` lines:

```
data: {"partial_image_b64":"iVBORw0KGgo..."}
data: {"item":{"result":"iVBORw0KGgo...full image..."}}
```

### Extraction Function

```python
import json

def parse_sse_images(text: str) -> list[str]:
    """Extract base64 images from SSE stream. Prefers final over partial."""
    finals, partials = [], []
    for line in text.split("\n"):
        if not line.startswith("data: "):
            continue
        try:
            d = json.loads(line[6:])
            item = d.get("item", d) if isinstance(d, dict) else {}
            for key in ("result", "image_b64", "b64_json"):
                if key in item and isinstance(item[key], str) and len(item[key]) > 500:
                    finals.append(item[key])
                    break
            if "partial_image_b64" in item:
                partials.append(item["partial_image_b64"])
        except (json.JSONDecodeError, AttributeError):
            pass
    return finals if finals else partials
```

## Complete Python Script

```python
#!/usr/bin/env python3
"""zhexueqi_gen.py — Generate images via zhexueqi.xyz API."""
import os, sys, json, base64, time
import requests
from pathlib import Path

ZHEXUEQI_URL = "https://zhexueqi.xyz/responses"

def load_tokens():
    tokens = []
    for key in ("ZHEXUEQI_TOKEN", "ZHEXUEQI_TOKEN_2", "ZHEXUEQI_TOKEN_3",
                "ZHEXUEQI_TOKEN_4", "ZHEXUEQI_TOKEN_5"):
        if os.environ.get(key):
            tokens.append(os.environ[key])
    if not tokens:
        raise SystemExit("Set ZHEXUEQI_TOKEN environment variable")
    return tokens

def parse_sse_images(text):
    finals, partials = [], []
    for line in text.split("\n"):
        if not line.startswith("data: "):
            continue
        try:
            d = json.loads(line[6:])
            item = d.get("item", d) if isinstance(d, dict) else {}
            for key in ("result", "image_b64", "b64_json"):
                if key in item and isinstance(item[key], str) and len(item[key]) > 500:
                    finals.append(item[key])
                    break
            if "partial_image_b64" in item:
                partials.append(item["partial_image_b64"])
        except (json.JSONDecodeError, AttributeError):
            pass
    return finals if finals else partials

def generate_one(token, payload, call_index):
    for attempt in range(1, 4):
        try:
            r = requests.post(ZHEXUEQI_URL, json=payload,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                timeout=600)
            if r.status_code in (502, 503, 504):
                print(f"  call#{call_index} HTTP {r.status_code} (attempt {attempt}/3) — retrying...")
                time.sleep(2 ** attempt)
                continue
            r.raise_for_status()
            images = parse_sse_images(r.text)
            if images:
                return images[0]
            print(f"  call#{call_index} no image (attempt {attempt}/3)")
            time.sleep(2 ** attempt)
        except requests.Timeout:
            print(f"  call#{call_index} timeout (attempt {attempt}/3)")
            time.sleep(2 ** attempt)
        except Exception as e:
            if attempt < 3:
                print(f"  call#{call_index} {e} (attempt {attempt}/3)")
                time.sleep(2 ** attempt)
            else:
                raise
    raise RuntimeError(f"call#{call_index} failed after 3 attempts")

def generate(prompt, n=1, quality="low", size="1024x1024", output_format="png",
             ref_images=None, out_dir="output"):
    tokens = load_tokens()
    # Build payload
    if ref_images:
        content = [{"type": "input_image", "image_url": u} for u in ref_images]
        content.append({"type": "input_text", "text": prompt})
        fm_input = [{"role": "user", "content": content}]
    else:
        fm_input = prompt
    payload = {
        "model": "gpt-image-2",
        "input": fm_input,
        "tools": [{"type": "image_generation", "action": "generate",
                    "quality": quality, "size": size, "output_format": output_format}],
        "tool_choice": "required",
        "stream": True,
    }
    # Distribute calls across tokens
    per_token = [n // len(tokens)] * len(tokens)
    for i in range(n % len(tokens)):
        per_token[i] += 1
    call_args = []
    for ti, count in enumerate(per_token):
        for j in range(count):
            call_args.append((tokens[ti], len(call_args) + 1))
    print(f"Generating {n} image(s) with {len(tokens)} token(s)...")
    t0 = time.time()
    if len(call_args) == 1:
        results = [generate_one(call_args[0][0], payload, 1)]
    else:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        with ThreadPoolExecutor(max_workers=len(call_args)) as executor:
            futures = {executor.submit(generate_one, t, payload, i): i
                       for t, i in call_args}
            results = [None] * len(call_args)
            for f in as_completed(futures):
                idx = futures[f]
                try:
                    results[idx - 1] = f.result()
                except Exception as e:
                    print(f"  call#{idx} failed: {e}")
            results = [r for r in results if r]
    elapsed = time.time() - t0
    # Save results
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    for i, b64 in enumerate(results):
        ext = output_format if output_format == "webp" else "png"
        path = Path(out_dir) / f"generated_{i + 1}.{ext}"
        path.write_bytes(base64.b64decode(b64))
        print(f"Saved: {path} ({path.stat().st_size:,} bytes)")
    print(f"Done: {len(results)}/{n} images in {elapsed:.1f}s")
    return [str(Path(out_dir) / f"generated_{i + 1}.{ext}") for i in range(len(results))]

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="zhexueqi.xyz image generation")
    p.add_argument("prompt")
    p.add_argument("-n", type=int, default=1, help="Number of images (1-4)")
    p.add_argument("-q", "--quality", default="low", choices=["low","medium","high"])
    p.add_argument("-s", "--size", default="1024x1024")
    p.add_argument("-f", "--format", default="png", choices=["png","webp"])
    p.add_argument("-r", "--ref", action="append", help="Reference image path (repeatable)")
    p.add_argument("-o", "--out-dir", default="output")
    args = p.parse_args()
    refs = None
    if args.ref:
        refs = []
        for path in args.ref:
            b64 = base64.b64encode(Path(path).read_bytes()).decode()
            refs.append(f"data:image/png;base64,{b64}")
    generate(args.prompt, n=args.n, quality=args.quality, size=args.size,
             output_format=args.format, ref_images=refs, out_dir=args.out_dir)
```

## Available Models

| Model | Notes |
|-------|-------|
| **gpt-image-2** | Default model. Use unless the user explicitly requests another model. |
| **grok-imagine-image** | Grok image model. Use only when the user explicitly asks for Grok. |

## Size Constraints

| Constraint | Value |
|-----------|-------|
| Max edge length | 3840px |
| Edge multiple | 16px |
| Max total pixels | 8,294,400 |
| Max square | 2880×2880 |
| Max wide | 3840×2160 (16:9) |

Recommendation: use 2K (2048×2048) or below with `high` quality for reliable results within the gateway timeout. 4K only needed when detail is critical.

## Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| 504 Gateway Timeout | Non-stream mode hits 60s limit | Use `"stream": true` |
| Model returns text instead of image | Missing `action: "generate"` or `tool_choice: "auto"` | Set `"action": "generate"` + `"tool_choice": "required"` |
| 401 Token verification failed | Token expired or invalid | Get a new token |
| Reference image has no effect | Input format wrong | Use array input with `input_image` blocks |
| Slow generation | High quality + large size | Use medium quality, 1K/2K, or add more tokens |
