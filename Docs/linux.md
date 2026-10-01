# Linux 桌面客户端

固件不用改。采集卡是标准 UVC，CH58x 是标准 HID。需要系统包、udev，以及用 uv 安装 Python 依赖。

窗口焦点内的键盘和绝对鼠标可用。Linux 不做全局键钩；Win / Alt+Tab 等系统键请用 **键盘 → 系统快捷键**。Wayland 上相对鼠标无法把指针锁在窗口中心，菜单里会提示。

## 系统依赖（Debian / Ubuntu）

```bash
sudo apt install python3-venv libhidapi-hidraw0 libhidapi-libusb0 \
  gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
  libxcb-cursor0 libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 \
  libxcb-keysyms1 libxcb-render-util0 libxcb-xkb1
```

- **hidapi**：Python 包需要系统 `libhidapi-*`
- **GStreamer**：Qt Multimedia 走 GStreamer + V4L2，MJPEG/JPEG 预览依赖 plugins-good/bad
- **libxcb-cursor0**：PySide6 窗口光标

建议 Python 3.10–3.13。

## udev（打开 KVM 键鼠）

默认用户往往读不了 `/dev/hidraw*`，HID 打开会失败。

```bash
sudo cp Docs/udev/99-kvm-card-mini.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
sudo usermod -aG plugdev "$USER"
```

然后重新插拔 KVM 卡，并重新登录（组权限才生效）。采集卡走 V4L2，一般插上就能在设备列表里看到，名称不一定和 Windows 相同。用户通常还需要在 `video` 组。

键鼠 HID 在 **设备 → 视频设备** 里查找，对话框会显示查找状态。未找到时点「重新查找」（同时刷新视频设备列表）。先启动客户端再插卡即可。udev 未生效时也会显示未找到。

## uv 与启动

```bash
cd Client
uv sync
uv run python Mini-KVM.py
```

Windows 专用包（`pyWinhook` / `pywin32`）带有平台标记，Linux 上不会安装。

## 打包（Nuitka AppImage）

本机架构一份 AppImage（amd64 或 arm64）：

```bash
cd Client
chmod +x compiler-linux.sh
INSTALL_DEPS=1 ./compiler-linux.sh
./build_linux/KVM-Card-Mini.AppImage
```

打包 Python 默认 3.12。`INSTALL_DEPS=1` 会 `apt` 安装 gcc、patchelf、libhidapi、GStreamer、xcb、`file` 和 `libfuse2`（Nuitka 下载的 `appimagetool` 本身是 AppImage，需要 `libfuse.so.2`）。打开 HID 仍需要上面的 udev 规则。GitHub Actions 会在 `ubuntu-24.04` 和 `ubuntu-24.04-arm` 上各打一份。

## 使用注意

- 键鼠 HID：打开 **设备 → 视频设备** 时查找。未找到可点「重新查找」，或用菜单「Reload Key/Mouse」。
- 键盘：焦点在客户端窗口内即可把按键送到被控机。
- 鼠标：绝对模式按窗口坐标映射。右 Ctrl 或菜单「释放鼠标」结束捕获。
- System hook、屏幕键盘、Windows 音频/设备管理器在 Linux 上隐藏。
