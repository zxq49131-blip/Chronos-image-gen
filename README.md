# zhexueqi-image-gen
[中文文档](README_CN.md)
Generate images via [zhexueqi.xyz](https://zhexueqi.xyz) API — no OpenAI key required.

## Quick Start

```bash
# 1. Set your token
export ZHEXUEQI_TOKEN="zxq_..."

# 2. Install deps
pip install requests

# 3. Generate
python zhexueqi_gen.py "a photorealistic red apple on a white table"
```

## Usage

```
python zhexueqi_gen.py "prompt" [options]

Options:
  -n N          Number of images (1-10, default 1)
  -q QUALITY    low | medium | high (default low)
  -s SIZE       e.g. 1024x1024, 2048x2048, 2880x2880, auto
  -f FORMAT     png | webp (default png)
  -r PATH       Reference image (repeatable)
  -o DIR        Output directory (default output)
  -m MODEL      gpt-5.5 (default) | gpt-5.4 | gpt-5.4-mini
```

### Examples

```bash
# Basic
python zhexueqi_gen.py "a sunset over mountains"

# High quality, 2K
python zhexueqi_gen.py "a futuristic city" -q high -s 2048x2048

# 4 images parallel (with multiple tokens)
python zhexueqi_gen.py "a cute cat" -n 4

# With reference image
python zhexueqi_gen.py "draw a hat on this cat" -r cat.png -r style_ref.png
```

### Multiple Tokens

For parallel generation with `-n > 1`, add more tokens:

```
export ZHEXUEQI_TOKEN="zxq_xxx"
export ZHEXUEQI_TOKEN_2="zxq_yyy"
```

Calls are distributed across tokens for faster generation.

## Claude Code Skill

```bash
npx skills add https://github.com/zxq49131-blip/zhexueqi-image-gen
```

Then just ask Claude Code to generate images — it will use this skill.

## API Details

Uses the OpenAI Responses API format:

- Endpoint: `POST https://zhexueqi.xyz/respones`
- Model: `gpt-5.5` with `image_generation` tool
- Streaming: SSE (`stream: true` to bypass 60s gateway timeout)
- Auth: `Bearer` token header

See [SKILL.md](SKILL.md) for full API reference, response parsing, and troubleshooting.

## Models

| Model | Speed | Notes |
|-------|-------|-------|
| gpt-5.5 | ~30-70s | Best overall |
| gpt-5.4 | ~30-120s | All sizes work with streaming |
| gpt-5.4-mini | ~20-120s | Fastest for small/low quality |

All models support reference images and all sizes when using `stream: true`.



## License

MIT
