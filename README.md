# forkKVM-Card-Mini

⌨️🖥️🖱️

Simple KVM Console to USB

一个简单的 KVM （Keyboard Video Mouse）设备控制卡，通过上位机程序控制被控设备的屏幕和键鼠

## About

桌面客户端（Windows / Linux / macOS）维护：[kiramint](https://github.com/kiramint/)。跨平台客户端、macOS 打包与文档有 Grok（xAI）协助。

本仓库改自：

- 原项目：[Jackadminx/KVM-Card-Mini](https://github.com/Jackadminx/KVM-Card-Mini)
- PySide6 重写：[ElluIFX](https://github.com/ElluIFX)（主题 / 音频路由 / 录制 / 截图 / 内置远程服务器，魔改自 Open-IP-KVM / 屏蔽系统键 / 剪贴板 / 无需系统支持的文件传输 / 特殊按键键盘等）

代码变动较大，不对原项目提 PR。

> [!TIP]
> 如果需要寻找一个非自制获取硬件的方案, 可参考[binnehot的文章](https://github.com/binnehot/KVM_over_USB_Q05)和[do21发现的问题](https://github.com/do21/KVM_over_USB_Q05)
>
> Linux 见 [Docs/linux.md](./Docs/linux.md)，macOS 见 [Docs/macos.md](./Docs/macos.md)。非 Windows 平台不做全局键钩，系统键请用「键盘 → 系统快捷键」。
>
> 客户端内置 Web KVM 默认端口为 **5001**（macOS 的 AirPlay Receiver 占用 5000）。`Server_Standalone` 仍默认 5000。
>
> 基于 WebUSB 的纯浏览器客户端见 web 分支，感谢 @wang3076

程序内 **关于** 菜单打开多页说明（关于 / 作者 / 致谢 / 许可）。

## Screenshot

![Screenshot1](./Docs/Images/Screenshot1.png)

![Screenshot1](./Docs/Images/Screenshot2.png)

## Development

依赖用 [uv](https://docs.astral.sh/uv/) 管理（`Client/pyproject.toml` + `Client/uv.lock`）。Windows 专用包带平台标记，其它系统不会安装。Python 3.10–3.13。

```bash
cd Client
uv sync
uv run python Mini-KVM.py
```

Nuitka 打包（`uv` 的 `packaging` 组）：

```bash
cd Client
./compiler-macos.sh                 # Apple Silicon → build_macos/*.app
INSTALL_DEPS=1 ./compiler-linux.sh  # amd64/arm64 AppImage → build_linux/*.AppImage
pwsh -File compiler-windows.ps1     # amd64 单文件 → build_windows/KVM-Card-Mini.exe
```

Windows 打包用 Python 3.11（amd64，才能装上 `pyWinhook` 轮子）；Linux / macOS 用 3.12。可用环境变量 `PYTHON_VERSION` 覆盖。

macOS 采集卡需要 `.app` 才能弹出相机权限：

```bash
cd Client
./compiler-macos.sh
open build_macos/Mini-KVM.app
```

macOS 包显示名 KVM Card Mini，bundle id `dev.kiramint.kvm-card-mini`。配置和错误日志在 `~/Library/Application Support/KVM Card Mini/`。窗口内鼠标跟踪需要这套 `.app` 里的 overlay，不要用完全透明遮罩。

推送仓库会跑 [`.github/workflows/build.yml`](./.github/workflows/build.yml)，产物：

| Artifact | 内容 | Runner |
|----------|------|--------|
| `KVM-Card-Mini-windows-amd64` | 单文件 `.exe` | `windows-latest` |
| `KVM-Card-Mini-linux-amd64` | AppImage | `ubuntu-24.04` |
| `KVM-Card-Mini-linux-arm64` | AppImage | `ubuntu-24.04-arm` |
| `KVM-Card-Mini-macos-arm64` | `.app` | `macos-15` |

给 Agent 的仓库说明见 [AGENTS.md](./AGENTS.md)。

> [!IMPORTANT]
> 因为 git 的问题, 文件夹 Client/data 似乎没自动从 Data 变更为 data, 请手动改名再编译, 如果直接用 release 文件的话可以无视, 这个版本把 data 编译进单文件了, 只需要直接运行 exe 即可。源码树会同时识别 `Data/` 和 `data/`。
