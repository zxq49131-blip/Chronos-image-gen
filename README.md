# Chronos Image Gen

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

Agent skill and CLI for image generation through the [aichronos.xyz](https://aichronos.xyz) Images API. No OpenAI API key required.

- **Repository:** [https://github.com/zxq49131-blip/Chronos-image-gen](https://github.com/zxq49131-blip/Chronos-image-gen)
- **Chinese docs:** [README_CN.md](README_CN.md)
- **API / agent skill:** [SKILL.md](SKILL.md)

## Features

- Text-to-image via `POST /v1/images/generations`
- Default model `gpt-image-2.5-sunburst`; optional `grok-imagine-image`
- Quality, size, and output format controls
- Multi-token parallel generation (`-n` + extra tokens)
- Usable as a Claude Code / Codex / Cursor skill
- Optional `.env` loading for local tokens

## Requirements

- Python 3.8+
- `requests`
- A token from an **image-generation** subscription group (chat-only keys may authenticate but still fail image calls)

```bash
pip install requests
# optional, enables automatic .env loading
pip install python-dotenv
```

## Quick Start

1. Copy `.env.example` to `.env` and put your token there, or export it in the shell.
2. Run the CLI.

### Environment variable

**bash / zsh**

```bash
export ZHEXUEQI_TOKEN="zxq_..."
python zhexueqi_gen.py "a photorealistic red apple on a white table"
```

**PowerShell**

```powershell
$env:ZHEXUEQI_TOKEN = "zxq_..."
python zhexueqi_gen.py "a photorealistic red apple on a white table"
```

### `.env` file

```env
ZHEXUEQI_TOKEN=zxq_xxxxxxxx
```

Do not commit real tokens. `.env` is gitignored.

## Clone

```bash
git clone https://github.com/zxq49131-blip/Chronos-image-gen.git
cd Chronos-image-gen
pip install requests
```

## CLI

```text
python zhexueqi_gen.py "prompt" [options]

Options:
  -n N          Number of images (default 1; recommended 1-10)
  -q QUALITY    low | medium | high (default low)
  -s SIZE       e.g. 1024x1024, 2048x2048, 2880x2880, auto
  -f FORMAT     png | webp (default png)
  -r PATH       Reference image path (repeatable)
  -o DIR        Output directory (default output)
  -m MODEL      gpt-image-2.5-sunburst (default) | grok-imagine-image
```

Images are saved as `output/generated_1.png` (or `.webp`).

### Examples

```bash
# Basic
python zhexueqi_gen.py "a sunset over mountains"

# High quality, 2K
python zhexueqi_gen.py "a futuristic city" -q high -s 2048x2048

# WebP output
python zhexueqi_gen.py "studio product shot of a glass bottle" -f webp

# Grok model
python zhexueqi_gen.py "a cute robot in a bookstore" -m grok-imagine-image

# 4 images in parallel (add extra tokens first)
python zhexueqi_gen.py "a cute cat" -n 4

# Custom output directory
python zhexueqi_gen.py "editorial fashion portrait" -o images/generations
```

The generations endpoint is text-to-image. For reference-image editing, use `/v1/images/edits` as described in [SKILL.md](SKILL.md). The CLI `-r` flag still exists for local experiments.

## Multiple Tokens

When `-n > 1`, extra tokens are used to run calls in parallel:

```bash
export ZHEXUEQI_TOKEN="zxq_xxx"
export ZHEXUEQI_TOKEN_2="zxq_yyy"
export ZHEXUEQI_TOKEN_3="zxq_zzz"
```

The script reads `ZHEXUEQI_TOKEN` through `ZHEXUEQI_TOKEN_5`. Work is split across whatever tokens are set. Example: `-n 4` with two tokens issues two calls per token at the same time.

## Models

| Model | Role |
|-------|------|
| `gpt-image-2.5-sunburst` | Default. Use unless another model is explicitly requested. |
| `grok-imagine-image` | Grok image model. Use only when Grok is requested. |

Recommendation: `2048x2048` (or smaller) with `high` quality for a good reliability/detail tradeoff. Use 4K only when extra detail is required.

## Size Constraints

| Constraint | Value |
|-----------|-------|
| Max edge length | 3840px |
| Edge multiple | 16px |
| Max total pixels | 8,294,400 |
| Max square | 2880x2880 |
| Max wide | 3840x2160 (16:9) |

## Agent Skill

Skill id in `SKILL.md`: `zhexueqi-image-gen`.

### Claude Code

```bash
npx skills add zxq49131-blip/Chronos-image-gen
```

After install, ask the agent to generate an image. It should pick up this skill.

### Codex / local skills folder

Clone or copy this repo into your skills directory, for example:

```bash
git clone https://github.com/zxq49131-blip/Chronos-image-gen.git ~/.codex/skills/chronos-image-gen
```

On Windows, that is typically `%USERPROFILE%\.codex\skills\chronos-image-gen`.

Set `ZHEXUEQI_TOKEN` before asking the agent to generate images. If no token is provided, the skill should stop and ask for one.

The token must belong to an image-generation subscription group.

## API

Canonical request format (see [SKILL.md](SKILL.md) for parsing and retries):

```http
POST https://aichronos.xyz/v1/images/generations
Authorization: Bearer $ZHEXUEQI_TOKEN
Content-Type: application/json
```

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

Images are returned as Base64 in `data[].b64_json`.

Do **not** send `input`, `tools`, `tool_choice`, or `stream` to this endpoint.

```bash
curl -s https://aichronos.xyz/v1/images/generations \
  -H "Authorization: Bearer $ZHEXUEQI_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-image-2.5-sunburst","prompt":"a red apple on a white table","n":1,"response_format":"b64_json","quality":"high","size":"2048x2048","output_format":"png"}'
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| 504 Gateway Timeout | Upstream generation took too long | Retry with lower quality or a smaller size |
| Response has no image | Payload is not Images API format | Send `prompt` and parse `data[].b64_json` |
| 401 / 403 | Token expired, invalid, or not in an image-generation group | Replace the token with an image-generation key |
| Reference image needed | Generations is text-only | Use `/v1/images/edits` |
| Slow generation | High quality + large size | Use medium quality, 1K/2K, or add more tokens |

## License

MIT. See [LICENSE](LICENSE).

Maintained at [github.com/zxq49131-blip/Chronos-image-gen](https://github.com/zxq49131-blip/Chronos-image-gen).