---
name: zhexueqi-image-gen
description: Call image generation models through the aichronos.xyz Images API. Use this skill when the user wants to generate images via the aichronos.xyz API, needs to set up image generation from this endpoint, or asks about calling image models without an OpenAI API key. Covers token setup, model selection, the `/v1/images/generations` API format, size/quality constraints, and multi-token parallel generation.
---

# aichronos.xyz Image Generation

Generate images via `https://aichronos.xyz/v1/images/generations` using `gpt-image-2.5-sunburst` by default. No OpenAI API key required; use a provider token from an image-generation/image-generation subscription group.

Model selection rules:
- Tell users the supported image models are `gpt-image-2.5-sunburst` and `grok-imagine-image`.
- Default to `gpt-image-2.5-sunburst`.
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
POST https://aichronos.xyz/v1/images/generations
Authorization: Bearer $ZHEXUEQI_TOKEN
Content-Type: application/json
```

### Request Payload

```json
{
  "model": "gpt-image-2.5-sunburst",
  "prompt": "Generate a photorealistic image of a red apple on a white table",
  "n": 1,
  "response_format": "b64_json",
  "quality": "high",
  "size": "2048x2048",
  "output_format": "png"
}
```

### Critical Parameters

| Parameter | Value | Why |
|-----------|-------|-----|
| `prompt` | Non-empty string | Image description to generate |
| `n` | `1` | Number of requested images |
| `response_format` | `"b64_json"` | Return image bytes inline and avoid a separate image download |
| `quality` | `"low"`, `"medium"`, or `"high"` | Requested output quality |
| `output_format` | `"png"` or `"webp"` | Returned image encoding |

### Input Formats

**Text-to-image:**
```json
{"prompt": "Generate an image of a cat"}
```

Use `/v1/images/edits` for reference-image editing. Do not send `input`, `tools`, `tool_choice`, or `stream` to this endpoint.

## Response Parsing

The API returns a JSON response. Images are in `data[].b64_json`:

```json
{"data":[{"b64_json":"iVBORw0KGgo..."}]}
```

### Extraction Function

```python
import json

def parse_images_response(payload: dict) -> list[str]:
    """Extract base64 images from an Images API JSON response."""
    return [item["b64_json"] for item in payload.get("data", [])
            if isinstance(item, dict) and isinstance(item.get("b64_json"), str)]
```

## Complete Python Script

```python
#!/usr/bin/env python3
"""zhexueqi_gen.py — Generate images via aichronos.xyz API."""
import os, sys, json, base64, time
import requests
from pathlib import Path

ZHEXUEQI_URL = "https://aichronos.xyz/v1/images/generations"

def load_tokens():
    tokens = []
    for key in ("ZHEXUEQI_TOKEN", "ZHEXUEQI_TOKEN_2", "ZHEXUEQI_TOKEN_3",
                "ZHEXUEQI_TOKEN_4", "ZHEXUEQI_TOKEN_5"):
        if os.environ.get(key):
            tokens.append(os.environ[key])
    if not tokens:
        raise SystemExit("Set ZHEXUEQI_TOKEN environment variable")
    return tokens

def parse_images_response(payload):
    return [item["b64_json"] for item in payload.get("data", [])
            if isinstance(item, dict) and isinstance(item.get("b64_json"), str)]

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
            images = parse_images_response(r.json())
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
             out_dir="images/generations"):
    tokens = load_tokens()
    payload = {
        "model": "gpt-image-2.5-sunburst",
        "prompt": prompt,
        "n": 1,
        "response_format": "b64_json",
        "quality": quality,
        "size": size,
        "output_format": output_format,
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
    p = argparse.ArgumentParser(description="aichronos.xyz image generation")
    p.add_argument("prompt")
    p.add_argument("-n", type=int, default=1, help="Number of images (1-4)")
    p.add_argument("-q", "--quality", default="low", choices=["low","medium","high"])
    p.add_argument("-s", "--size", default="1024x1024")
    p.add_argument("-f", "--format", default="png", choices=["png","webp"])
    p.add_argument("-o", "--out-dir", default="images/generations")
    args = p.parse_args()
    generate(args.prompt, n=args.n, quality=args.quality, size=args.size,
             output_format=args.format, out_dir=args.out_dir)
```

## Available Models

| Model | Notes |
|-------|-------|
| **gpt-image-2.5-sunburst** | Default model. Use unless the user explicitly requests another model. |
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
| 504 Gateway Timeout | Upstream generation took too long | Retry with a lower quality or smaller size |
| Model returns no image | Invalid Images API response | Send `prompt` and parse `data[].b64_json` |
| 401 Token verification failed | Token expired or invalid | Get a new token |
| Reference image is needed | Generations endpoint is text-only | Use `/v1/images/edits` |
| Slow generation | High quality + large size | Use medium quality, 1K/2K, or add more tokens |
