"""Speed test for hipfire server — measures prefill and decode at realistic prompt lengths.

Requirements:
  - hipfire serve running on http://127.0.0.1:11435 (start with serve.bat)
  - Python 3.8+ (stdlib only)

Usage:
  python speed_test.py                 # run all tests
  python speed_test.py --url http://127.0.0.1:11435
  python speed_test.py --model qwen3.8:27b-mq4-xts
  python speed_test.py --quick         # skip the 13K-token test
"""
import argparse
import json
import sys
import time
import urllib.request
import urllib.error

DEFAULT_URL = "http://127.0.0.1:11435"
DEFAULT_MODEL = "qwen3.8:27b-mq4-xts"


def get_model_id(base_url):
    """Fetch the first model ID from /v1/models; fall back to DEFAULT_MODEL."""
    try:
        req = urllib.request.Request(f"{base_url}/v1/models")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        models = data.get("data", [])
        # Prefer the short alias over the full path
        for m in models:
            if ":" in m.get("id", ""):
                return m["id"]
        if models:
            return models[0]["id"]
    except Exception:
        pass
    return DEFAULT_MODEL


def send_request(base_url, model, prompt_text, max_tokens, label, timeout=300):
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt_text}],
        "max_tokens": max_tokens,
        "stream": False,
        "temperature": 0.0,
    }).encode()
    req = urllib.request.Request(
        f"{base_url}/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    start = time.time()
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as e:
        print(f"\n  ERROR ({label}): HTTP {e.code} — {e.read().decode()[:200]}")
        return
    except Exception as e:
        print(f"\n  ERROR ({label}): {e}")
        return
    elapsed = time.time() - start
    data = json.loads(resp.read())

    u = data.get("usage", {})
    t = data.get("timings", {})
    h = data.get("hipfire", {})

    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(f"  prompt_tokens:      {u.get('prompt_tokens')}")
    print(f"  completion_tokens: {u.get('completion_tokens')}")
    print(f"  wall_time:          {elapsed:.2f}s")
    print(f"  ---")
    if t:
        print(f"  prefill_tok_s:     {t.get('prefill_tok_s')}")
        print(f"  decode_tok_s:      {t.get('decode_tok_s')}")
        print(f"  ttft_ms:            {t.get('ttft_ms')}")
        print(f"  ---")
        print(f"  dflash:            {t.get('dflash')}")
        print(f"  mtp:               {t.get('mtp')}")
        print(f"  tau (accept_rate): {t.get('tau')}")
        print(f"  cycles:            {t.get('cycles')}")
    if h:
        print(f"  ---")
        print(f"  hipfire tok_s:     {h.get('tok_s')}")
        print(f"  execution_mode:    {h.get('execution_mode')}")


def main():
    parser = argparse.ArgumentParser(description="hipfire speed test")
    parser.add_argument("--url", default=DEFAULT_URL, help=f"serve URL (default: {DEFAULT_URL})")
    parser.add_argument("--model", default=None, help="model ID (auto-detected if omitted)")
    parser.add_argument("--quick", action="store_true", help="skip the 13K-token test")
    args = parser.parse_args()

    # Auto-detect model ID
    model = args.model or get_model_id(args.url)
    print(f"Using model: {model}")
    print(f"Server: {args.url}")

    # --- Decode speed test (short prompt, long generation) ---
    send_request(args.url, model, "Write a short poem about autumn.", 128, "Decode test (128 tok)")

    # --- Prefill speed tests (increasing prompt length) ---
    sentences = "The quick brown fox jumps over the lazy dog. "
    tests = [
        (100, "~1300 tok prefill", 32, 120),
        (400, "~5200 tok prefill", 32, 180),
    ]
    if not args.quick:
        tests.append((1000, "~13000 tok prefill", 32, 300))

    for n_sent, label, max_tok, timeout in tests:
        prompt = sentences * n_sent + "Now answer: what is 2+2? Answer in one word."
        send_request(args.url, model, prompt, max_tok, label, timeout=timeout)

    print(f"\n{'='*60}")
    print("  Done. Server tested.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()