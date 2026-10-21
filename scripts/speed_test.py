"""Speed test for hipfire server - measures prefill and decode at realistic prompt lengths."""
import json
import time
import urllib.request

BASE = "http://127.0.0.1:11435/v1/chat/completions"
MODEL = "qwen3.8:27b-mq4-xts"

def send_request(prompt_text, max_tokens, label):
    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt_text}],
        "max_tokens": max_tokens,
        "stream": False
    }).encode()
    req = urllib.request.Request(BASE, data=payload, headers={"Content-Type": "application/json"})
    start = time.time()
    resp = urllib.request.urlopen(req, timeout=300)
    data = json.loads(resp.read())
    elapsed = time.time() - start

    u = data.get("usage", {})
    t = data.get("timings", {})
    h = data.get("hipfire", {})

    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(f"  prompt_tokens:      {u.get('prompt_tokens')}")
    print(f"  completion_tokens:  {u.get('completion_tokens')}")
    print(f"  wall_time:          {elapsed:.2f}s")
    print(f"  ---")
    print(f"  prefill_tok_s:      {t.get('prefill_tok_s')}")
    print(f"  decode_tok_s:       {t.get('decode_tok_s')}")
    print(f"  ttft_ms:            {t.get('ttft_ms')}")
    print(f"  ---")
    print(f"  dflash:             {t.get('dflash')}")
    print(f"  mtp:                {t.get('mtp')}")
    print(f"  tau (accept_rate):  {t.get('tau')}")
    print(f"  cycles:             {t.get('cycles')}")
    print(f"  ---")
    print(f"  hipfire tok_s:      {h.get('tok_s')}")
    print(f"  execution_mode:     {h.get('execution_mode')}")

# Build prompts of increasing size
sentences = "The quick brown fox jumps over the lazy dog. "
for n_sent, label in [(100, "~1300 tok prefill"), (400, "~5200 tok prefill"), (1000, "~13000 tok prefill")]:
    prompt = sentences * n_sent + "Now answer: what is 2+2? Answer in one word."
    send_request(prompt, 32, label)

print("\n" + "="*60)
print("  Done. Server tested.")
print("="*60)
