# hipfire-windows：AMD Strix Halo 上的 Windows 原生 hipfire 支持

在 **Windows 11** 上以 **256K 上下文** 运行 **Qwen3.8-27B**，启用 **DFlash 推测解码**，实现 Strix Halo（gfx1151 / Radeon 8060S）上已知最快的推理速度。

## 性能

同硬件（Strix Halo，128GB 统一内存），同模型（Qwen3.8-27B，~4.5 bpw）：

| 指标 | 本项目（hipfire + DFlash） | 社区最佳方案 | 提速倍数 |
|------|:---:|:---:|:---:|
| 预填充 8K | **982 tok/s** | 440 tok/s（Vulkan fork） | **2.2 倍** |
| 预填充 32K | **882 tok/s** | 252 tok/s（llama.cpp Vulkan） | **3.5 倍** |
| 预填充 128K | **504 tok/s** | 115 tok/s（llama.cpp ROCm） | **4.4 倍** |
| 解码（最佳） | **54.3 tok/s** | 31.8 tok/s（llama.cpp MTP） | **1.7 倍** |

完整基准测试数据：[`benchmarks/benchmark-2026-10-21.json`](benchmarks/benchmark-2026-10-21.json)

## 本项目解决了什么

hipfire 是专为 AMD GPU 优化的 Rust 原生 LLM 推理引擎，默认仅支持 Linux。本项目通过 **两个补丁** 让它在 Windows 上原生运行：

1. **VMM KV 后端解锁** — hipfire 因段别名 bug 在 Windows 上拒绝 VMM（虚拟内存映射）KV 后端。该 bug 已在 `rdna-compute::dispatch` 中修复（全量预留映射，不再增长），因此我们添加环境变量 `HIPFIRE_UNSAFE_WINDOWS_VMM_KV=1` 来解除拒绝。这解锁了 Windows 上的 256K 上下文。

2. **UMA 内存信息修复** — 在 UMA APU（Strix Halo）上，hipfire 查询 `/proc/meminfo` 来估算 GTT 分配可用的主机内存。这是 Linux 专属路径，在 Windows 上会失败。我们添加了 `#[cfg(windows)]` 提前返回，直接信任 `hipMemGetInfo` 返回的值。

## 硬件要求

- AMD Ryzen AI Max+ 395（Strix Halo）配 Radeon 8060S（gfx1151）
- 128GB 统一 LPDDR5X 内存（64GB 分配为显存）
- Windows 11（LTSC 或普通版均可）
- 已安装 AMD HIP SDK 7.2+
- 约 18GB 可用显存用于模型推理（模型 15GB + DFlash 1.2GB + MTP 0.2GB + 视觉塔 0.9GB + KV 缓存按上下文长度分配）

> **关于显存**：Strix Halo 是 UMA 架构，128GB 统一内存中 64GB 默认分配为"显存"（UMA carve-out）。256K 上下文 Q8 KV 缓存约占 9GB，加权重共需 ~18GB 显存。如需更多可用内存，可在 BIOS 中调整 UMA carve-out。

## 快速开始

### 1. 获取二进制文件

**方式 A — 下载预编译版本（推荐）**

从 [Releases](https://github.com/fxhack/hipfire-windows/releases) 下载 `hipfire-windows-v1.0.0.zip`，解压得到 4 个 .exe 文件。

**方式 B — 从源码编译**

```bash
cd /path/to/hipfire-src
git apply patches/0001-vmm-kv-windows-override.patch
git apply patches/0002-windows-uma-meminfo-fix.patch
cargo build --release
```

将编译出的 4 个 .exe 放到一个目录中（如 `D:\hipfire`），并把 `scripts/` 下的 .bat 脚本也复制过去。

### 2. 下载模型文件

从 [hipfire-models/Qwen3.8-27B](https://huggingface.co/hipfire-models/qwen3.8-27b) 下载以下文件到 `<HIPFIRE_HOME>\models\qwen3.8-27b\`：

| 文件 | 大小 | 用途 |
|------|------|------|
| `qwen3.8-27b.mq4-xts` | 15.0 GB | 主模型（trunk） |
| `qwen38-27b-dflash-mq4.hfq` | 1.21 GB | DFlash 推测解码 drafter |
| `qwen3.8-27b.mtp` | 226 MB | MTP 多 Token 预测头 |
| `qwen3.8-27b-vision.hfq` | 928 MB | 视觉塔（多模态图片输入，可选） |

### 3. 配置

将 [`scripts/config.example.toml`](scripts/config.example.toml) 复制为 `<HIPFIRE_HOME>\config.toml`，把所有 `<HIPFIRE_HOME>` 占位符替换为你的实际路径（用正斜杠 `/` 或双反斜杠 `\\`）。

### 4. 启动

双击 `serve.bat`，等待模型加载完成（首次约 15-30 秒）。

```bat
serve.bat          :: 启动 HTTP 服务（端口 11435，带 Web UI）
bench.bat          :: 基准测试
chat.bat           :: 交互式命令行聊天
speed_test.py      :: Python 速度测试脚本
```

服务启动后访问 http://127.0.0.1:11435/ui 即可使用 Web 聊天界面。

### 5. API 使用

服务兼容 OpenAI API 格式：

```python
import openai

client = openai.OpenAI(base_url="http://127.0.0.1:11435/v1", api_key="none")

response = client.chat.completions.create(
    model="qwen3.8:27b-mq4-xts",
    messages=[{"role": "user", "content": "Hello!"}],
    max_tokens=512,
)
print(response.choices[0].message.content)
```

## 补丁说明

| 补丁文件 | 修改文件 | 改动行数 | 说明 |
|---------|---------|:---:|------|
| `0001-vmm-kv-windows-override.patch` | `crates/hipfire-config/src/devices.rs` | +29 / -1 | 添加 `HIPFIRE_UNSAFE_WINDOWS_VMM_KV` 环境变量，解除 Windows 上 VMM KV 后端的拒绝 |
| `0002-windows-uma-meminfo-fix.patch` | `crates/rdna-compute/src/dispatch.rs` | +9 / -0 | 在 `device_mem_info` 中添加 `#[cfg(windows)]` 提前返回，跳过 `/proc/meminfo` 查询 |

## gfx1151 限制说明

以下功能在 gfx1151（RDNA3 / Strix Halo）上 **不可用**，需要 gfx1201（RDNA4）或 legacy KV 后端：

| 功能 | 要求 | 状态 |
|------|------|------|
| `serve.multi_slot`（多 slot 并发） | `kv_backend=legacy`（与 VMM 256K 冲突） | ❌ 不可用 |
| `serve.vmm_batch`（VMM 连续批处理） | gfx1201+ | ❌ 不可用 |
| FP8 WMMA 路由 | gfx1201+ | ❌ 不可用 |
| KV 量化降精度（FWHT/Lloyd） | gfx1201 或 legacy backend | ❌ 不可用 |

当前使用 **noslots 顺序模式** + `session_cache_disk` 磁盘落盘：会话被 evict 时 KV 写入磁盘而非丢弃，下次同对话可 restore 而非 cold prefill。

## 基准测试方法

- **引擎**：hipfire serve（OpenAI 兼容 API，端口 11435）
- **模型**：Qwen3.8-27B mq4-xts（4.46 bpw）+ DFlash MQ4V2 drafter
- **KV 后端**：VMM（全量预留映射，Q8 缓存）
- **上下文长度**：262,144 tokens
- **并发**：1（单流）
- **温度**：0.0（贪心采样）
- **重复次数**：每个数据点 3 次，取中位数
- **总请求数**：21 次（7 个长度 × 3 次重复），成功率 100%

## 仓库结构

```
hipfire-windows/
├── README.md                          # 本文件
├── LICENSE                            # Apache-2.0
├── patches/
│   ├── 0001-vmm-kv-windows-override.patch
│   └── 0002-windows-uma-meminfo-fix.patch
├── scripts/
│   ├── serve.bat                      # HTTP 服务启动脚本（256K + DFlash + 视觉）
│   ├── bench.bat                      # 基准测试启动脚本
│   ├── chat.bat                       # 交互式聊天启动脚本
│   ├── speed_test.py                  # Python 速度测试脚本
│   └── config.example.toml            # hipfire 配置示例
├── benchmarks/
│   └── benchmark-2026-10-21.json      # 完整基准测试数据
└── video/                             # 抖音宣传视频素材
```

## 致谢

- [hipfire](https://github.com/warpfront/hipfire) by Kaden Schutt et al. — 本项目所补丁的推理引擎
- [hipfire-models/Qwen3.8-27B](https://huggingface.co/hipfire-models/qwen3.8-27b) — 量化模型权重
- 社区基准测试数据来源：d9bl.cn、akougkas.io、SteelPh0enix/llama.cpp-qwen4exp、pwilkin/strix-halo

## 许可证

Apache-2.0（与 hipfire 上游一致）