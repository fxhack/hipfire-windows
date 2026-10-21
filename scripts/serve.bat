@echo off
rem hipfire serve - OpenAI-compatible HTTP service
rem Qwen3.8-27B mq4-xts on Strix Halo gfx1151
rem 256K context via VMM KV backend + vision + DFlash + MTP
rem
rem IMPORTANT: Keep this cmd window open! Closing it kills the serve process.
rem            Do NOT use -d (detach) on Windows - daemon gets SIGTERM after a
rem            few requests, losing DFlash/vision and forcing JIT recompile.
rem
rem Usage:
rem   serve.bat                  (27B model, port 11435, with UI)
rem   serve.bat --port 8080      (override port)
rem   serve.bat --no-prewarm     (skip model preload)

set HIPFIRE_HOME=D:\ai\hipfire
set ROCM_PATH=C:\Program Files\AMD\ROCm\7.2
set HIP_PATH=C:\Program Files\AMD\ROCm\7.2
set HIPFIRE_ROCM_PATH=C:\Program Files\AMD\ROCm\7.2
rem Enable VMM KV backend for 256K context on Windows (full-reservation map, no growth)
set HIPFIRE_UNSAFE_WINDOWS_VMM_KV=1
rem Enable vision tower (multimodal: image input via OpenAI /v1/chat/completions)
set HIPFIRE_VISION_MODE=on
set PATH=%HIPFIRE_HOME%\bin;%PATH%

cd /d "%HIPFIRE_HOME%"
echo [hipfire] serve - model: qwen3.8-27b.mq4-xts (256K VMM + vision + DFlash)
echo [hipfire] GPU: gfx1151 (Strix Halo), ROCm 7.2
echo [hipfire] Config: %HIPFIRE_HOME%\config.toml
echo [hipfire] Port: 11435
echo [hipfire] Chat UI: http://127.0.0.1:11435/ui
echo [hipfire] Multimodal: vision tower ON (qwen3.8-27b-vision.hfq)
echo [hipfire] Speculation: MTP + DFlash (--spec auto)
echo [hipfire] NOTE: First 2-3 requests will be slow (JIT compile).
echo [hipfire]       After that, decode 45-79 tok/s, prefill ~1000 tok/s.
echo [hipfire] Ctrl+C to stop. Keep this window open!
echo.
"D:\ai\hipfire\bin\hipfire.exe" serve --model "D:\ai\hipfire\models\qwen3.8-27b\qwen3.8-27b.mq4-xts" --vision "D:\ai\hipfire\models\qwen3.8-27b\qwen3.8-27b-vision.hfq" --kv-backend vmm --max-seq 262144 --spec auto --ui %*
pause
