# macOS 桌面客户端

固件不用改。KVM 卡在 macOS 上是普通 vendor HID（VID `413d` / PID `2107`），采集卡是 UVC。

不做全局 Event Tap。窗口焦点内键盘和绝对鼠标可用；Command / Cmd+Tab 等系统键请用 **键盘 → 系统快捷键**。捕获鼠标期间 Cmd+Q 不会退出客户端，而是发给被控机。

## 系统依赖

```bash
brew install hidapi
```

Python 3.10–3.13。用 uv 安装其余依赖：

```bash
cd Client
uv sync
uv run python Mini-KVM.py
```

自定义 HID 一般不需要额外权限。摄像头（采集卡）走系统相机权限：

- `uv run python Mini-KVM.py`：权限记在终端 / Python 上，采集卡经常申请不到
- 请打包成 `.app` 再打开采集卡：

```bash
cd Client
chmod +x compiler-macos.sh
./compiler-macos.sh
open build_macos/Mini-KVM.app
```

包内 `Info.plist` 带有 `NSCameraUsageDescription` 和 `NSMicrophoneUsageDescription`。首次连接采集卡时允许相机（以及可选的麦克风）。若曾经拒绝，到 **系统设置 → 隐私与安全性 → 相机** 里打开 **KVM Card Mini**。

配置和错误日志在 `~/Library/Application Support/KVM Card Mini/`。客户端内置 Web KVM 默认端口是 **5001**（AirPlay Receiver 占用 5000）。

## 使用注意

- Qt 在 macOS 上 `nativeScanCode()` 经常是 0，客户端改用 `nativeVirtualKey()` 映射到 PC Set-1。
- Command 映射为被控机的 Windows/Meta 键。
- 释放鼠标捕获：Right Ctrl 或菜单 **鼠标 → 释放鼠标**（Mac 键盘很少用 Right Ctrl）。
- 相对鼠标可用；若指针异常，改回绝对模式。
- 捕获鼠标后，指针在窗口内移动就会发给被控机（视频层上有一层几乎透明的 overlay）。
- 子窗口（设备设置、自定义按键、指示灯、数字键盘等）可以拉高，避免按钮被裁切。
