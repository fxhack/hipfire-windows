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
- 128GB 统一 LPDDR5X 内存
- Windows 11（LTSC 或普通版均可）
- 已安装 AMD HIP SDK 7.2+
- 约 18GB 可用显存/内存（用于模型 + KV 缓存 + 侧边包）

## 快速开始

### 1. 应用补丁到 hipfire 源码

```bash
cd /path/to/hipfire-src
git apply patches/0001-vmm-kv-windows-override.patch
git apply patches/0002-windows-uma-meminfo-fix.patch
cargo build --release
```

### 2. 下载模型文件

从 [hipfire-models/Qwen3.8-27B](https://huggingface.co/hipfire-models/qwen3.8-27b) 下载：

| 文件 | 大小 | 用途 |
|------|------|------|
| `qwen3.8-27b.mq4-xts` | 15.0 GB | 主模型（trunk） |
| `qwen38-27b-dflash-mq4.hfq` | 1.21 GB | DFlash 推测解码 drafter |
| `qwen3.8-27b.mtp` | 226 MB | MTP 多 Token 预测头 |
| `qwen3.8-27b-vision.hfq` | 928 MB | 视觉塔（多模态图片输入） |

### 3. 配置

将 [`scripts/config.example.toml`](scripts/config.example.toml) 复制到 `~/.hipfire/config.toml` 并修改路径。

### 4. 启动

```bat
serve.bat
```

或使用附带的脚本：`serve.bat`（HTTP 服务）、`bench.bat`（基准测试）、`chat.bat`（交互式聊天）。

## 补丁说明

| 补丁文件 | 修改文件 | 改动行数 | 说明 |
|---------|---------|:---:|------|
| `0001-vmm-kv-windows-override.patch` | `crates/hipfire-config/src/devices.rs` | +29 / -1 | 添加 `HIPFIRE_UNSAFE_WINDOWS_VMM_KV` 环境变量，解除 Windows 上 VMM KV 后端的拒绝 |
| `0002-windows-uma-meminfo-fix.patch` | `crates/rdna-compute/src/dispatch.rs` | +9 / -0 | 在 `device_mem_info` 中添加 `#[cfg(windows)]` 提前返回，跳过 `/proc/meminfo` 查询 |

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
└── benchmarks/
    └── benchmark-2026-10-21.json      # 完整基准测试数据
```

## 致谢

- [hipfire](https://github.com/warpfront/hipfire) by Kaden Schutt et al. — 本项目所补丁的推理引擎
- [hipfire-models/Qwen3.8-27B](https://huggingface.co/hipfire-models/qwen3.8-27b) — 量化模型权重
- 社区基准测试数据来源：d9bl.cn、akougkas.io、SteelPh0enix/llama.cpp-qwen4exp、pwilkin/strix-halo

## 许可证

Apache-2.0（与 hipfire 上游一致）
