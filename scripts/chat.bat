@echo off
rem hipfire chat - interactive conversation with Qwen3.8-27B
rem 256K context via VMM KV backend + DFlash + MTP speculative decoding.

set HIPFIRE_HOME=D:\ai\hipfire
set ROCM_PATH=C:\Program Files\AMD\ROCm\7.2
set HIP_PATH=C:\Program Files\AMD\ROCm\7.2
set HIPFIRE_ROCM_PATH=C:\Program Files\AMD\ROCm\7.2
rem Enable VMM KV backend for 256K context on Windows
set HIPFIRE_UNSAFE_WINDOWS_VMM_KV=1
set PATH=%HIPFIRE_HOME%\bin;%PATH%

cd /d "%HIPFIRE_HOME%"
"D:\ai\hipfire\bin\hipfire.exe" chat --model "D:\ai\hipfire\models\qwen3.8-27b\qwen3.8-27b.mq4-xts" --kv-backend vmm --max-seq 262144 --spec auto %*
