#!/usr/bin/env python3
"""zhexueqi_gen.py — Generate images via zhexueqi.xyz API.
Usage: python zhexueqi_gen.py "a red apple" -q high -n 2 -s 2048x2048
"""
import os, sys, json, base64, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

ZHEXUEQI_URL = "https://zhexueqi.xyz/respones"


def load_tokens():
    tokens = []
    for key in ("ZHEXUEQI_TOKEN", "ZHEXUEQI_TOKEN_2", "ZHEXUEQI_TOKEN_3",
                "ZHEXUEQI_TOKEN_4", "ZHEXUEQI_TOKEN_5"):
        tok = os.environ.get(key, "").strip()
        if tok:
            tokens.append(tok)
    if not tokens:
        try:
            import dotenv
            dotenv.load_dotenv()
            for key in ("ZHEXUEQI_TOKEN", "ZHEXUEQI_TOKEN_2", "ZHEXUEQI_TOKEN_3"):
                tok = os.environ.get(key, "").strip()
                if tok:
                    tokens.append(tok)
        except ImportError:
            pass
    if not tokens:
        raise SystemExit("Set ZHEXUEQI_TOKEN environment variable or create a .env file")
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
            if "partial_image_b64" in item and isinstance(item["partial_image_b64"], str):
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
                print(f"  [#{call_index}] HTTP {r.status_code} (attempt {attempt}/3) — retrying...")
                time.sleep(2 ** attempt)
                continue
            if r.status_code in (401, 403):
                print(f"  [#{call_index}] Auth error — token may be invalid")
                r.raise_for_status()
            r.raise_for_status()
            images = parse_sse_images(r.text)
            if images:
                preferred = images[0]
                elapsed = r.elapsed.total_seconds()
                print(f"  [#{call_index}] OK ({elapsed:.1f}s, {len(preferred):,} chars)")
                return preferred
            print(f"  [#{call_index}] No image in response (attempt {attempt}/3)")
            time.sleep(2 ** attempt)
        except requests.Timeout:
            print(f"  [#{call_index}] timeout (attempt {attempt}/3)")
            time.sleep(2 ** attempt)
        except Exception as e:
            if attempt < 3:
                print(f"  [#{call_index}] {e} (attempt {attempt}/3)")
                time.sleep(2 ** attempt)
            else:
                raise
    raise RuntimeError(f"call#{call_index} failed after 3 attempts")


def generate(prompt, n=1, quality="low", size="1024x1024", output_format="png",
             ref_images=None, out_dir="output", model="gpt-5.5"):
    tokens = load_tokens()
    if ref_images:
        content = [{"type": "input_image", "image_url": u} for u in ref_images]
        content.append({"type": "input_text", "text": prompt})
        fm_input = [{"role": "user", "content": content}]
    else:
        fm_input = prompt
    payload = {
        "model": model,
        "input": fm_input,
        "tools": [{"type": "image_generation", "action": "generate",
                    "quality": quality, "size": size, "output_format": output_format}],
        "tool_choice": "required",
        "stream": True,
    }
    per_token = [n // len(tokens)] * len(tokens)
    for i in range(n % len(tokens)):
        per_token[i] += 1
    call_args = []
    for ti, count in enumerate(per_token):
        for j in range(count):
            call_args.append((tokens[ti], len(call_args) + 1))
    print(f"Generating {n} image(s) with {len(tokens)} token(s) | {size} {quality}...")
    t0 = time.time()
    if len(call_args) == 1:
        results = [generate_one(call_args[0][0], payload, 1)]
    else:
        with ThreadPoolExecutor(max_workers=len(call_args)) as executor:
            futures = {executor.submit(generate_one, t, payload, i): i for t, i in call_args}
            results = [None] * len(call_args)
            for f in as_completed(futures):
                idx = futures[f]
                try:
                    results[idx - 1] = f.result()
                except Exception as e:
                    print(f"  [#{idx}] failed: {e}")
            results = [r for r in results if r]
    elapsed = time.time() - t0
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    saved = []
    for i, b64 in enumerate(results):
        ext = output_format if output_format == "webp" else "png"
        path = Path(out_dir) / f"generated_{i + 1}.{ext}"
        path.write_bytes(base64.b64decode(b64))
        print(f"Saved: {path} ({path.stat().st_size:,} bytes)")
        saved.append(str(path))
    print(f"Done: {len(saved)}/{n} images in {elapsed:.1f}s")
    return saved


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="zhexueqi.xyz image generation")
    ap.add_argument("prompt", help="Image description")
    ap.add_argument("-n", type=int, default=1, help="Number of images (1-10)")
    ap.add_argument("-q", "--quality", default="low", choices=["low", "medium", "high"])
    ap.add_argument("-s", "--size", default="1024x1024", help="e.g. 2048x2048, 2880x2880, auto")
    ap.add_argument("-f", "--format", default="png", choices=["png", "webp"], dest="fmt")
    ap.add_argument("-r", "--ref", action="append", help="Reference image path (repeatable)")
    ap.add_argument("-o", "--out-dir", default="output")
    ap.add_argument("-m", "--model", default="gpt-5.5")
    args = ap.parse_args()
    refs = None
    if args.ref:
        refs = []
        for path in args.ref:
            b64 = base64.b64encode(Path(path).read_bytes()).decode()
            refs.append(f"data:image/png;base64,{b64}")
    generate(args.prompt, n=args.n, quality=args.quality, size=args.size,
             output_format=args.fmt, ref_images=refs, out_dir=args.out_dir, model=args.model)
