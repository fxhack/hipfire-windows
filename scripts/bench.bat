@echo off
rem hipfire bench - benchmark Qwen3.8-27B on gfx1151
rem Measures prefill (pp) and decode (tg) throughput.
rem 256K context via VMM KV backend.

set HIPFIRE_HOME=D:\ai\hipfire
set ROCM_PATH=C:\Program Files\AMD\ROCm\7.2
set HIP_PATH=C:\Program Files\AMD\ROCm\7.2
set HIPFIRE_ROCM_PATH=C:\Program Files\AMD\ROCm\7.2
rem Enable VMM KV backend for 256K context on Windows
set HIPFIRE_UNSAFE_WINDOWS_VMM_KV=1
set PATH=%HIPFIRE_HOME%\bin;%PATH%

cd /d "%HIPFIRE_HOME%"
echo [hipfire] Benchmarking qwen3.8-27b.mq4-xts on gfx1151 (256K VMM)
echo.
"D:\ai\hipfire\bin\hipfire.exe" bench "D:\ai\hipfire\models\qwen3.8-27b\qwen3.8-27b.mq4-xts" --kv-backend vmm --max-seq 262144 --spec auto %*
pause
