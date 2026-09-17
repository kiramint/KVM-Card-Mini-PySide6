# Linux 桌面客户端

当前 `linux-port` 分支已补齐桌面客户端在 Linux 上跑起来所需的上位机缺口。固件不用改。本期只保证**绝对鼠标**和窗口焦点内键盘；不做 Linux 全局键钩，也不适配相对鼠标。

硬件侧：采集卡是标准 UVC，CH58x 是标准 HID，内核都能认。卡在上位机的部分见 `Docs/linux-port.md`。

## 系统依赖（Debian / Ubuntu / WSL）

```bash
sudo apt install python3-venv libhidapi-hidraw0 libhidapi-libusb0 \
  gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
  libxcb-cursor0 libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 \
  libxcb-keysyms1 libxcb-render-util0 libxcb-xkb1
```

- **hidapi**：Python `hidapi` 包需要系统 `libhidapi-*`
- **GStreamer**：Qt Multimedia 在 Linux 走 GStreamer + V4L2，MJPEG/JPEG 预览依赖 plugins-good/bad
- **libxcb-cursor0**：PySide6 窗口光标

建议用 Python 3.11 建 venv（`python3.11 -m venv .venv`）。默认 `python3` 若是 3.12+，安装 `pyqtdarktheme==2.1.0` 时需要 `--ignore-requires-python`。

## udev（打开 KVM 键鼠）

默认用户往往读不了 `/dev/hidraw*`，HID 打开会失败。

```bash
sudo cp Docs/udev/99-kvm-card-mini.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
sudo usermod -aG plugdev "$USER"
```

然后重新插拔 KVM 卡，并重新登录（组权限才生效）。

采集卡（常见 VID `345f`）走 V4L2，一般插上就能在设备列表里看到，名称不一定是 Windows 上的 `Kira Q0.5 Video`。

## venv 与启动

```bash
git checkout linux-port
cd Client
# 不要复用 Windows 下建的 .venv（里面是 Scripts/，Linux 用不了）
rm -rf .venv
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt --ignore-requires-python
python Mini-KVM.py
```

Windows 开发机额外安装 Windows 专用依赖：

```powershell
pip install -r requirements.txt -r requirements-windows.txt --ignore-requires-python
```

`requirements.txt` 只含公共依赖；`pyWinhook` / `pywin32` / `win32_setctime` 在 `requirements-windows.txt`。

## 使用注意

- 键盘：焦点在客户端窗口内即可把按键送到被控机。Linux 上 Qt 的 `nativeScanCode` 会先转成现有 Set-1 表。
- 鼠标：绝对模式按窗口坐标映射到 `0x0000–0x7FFF`。右 Ctrl 释放鼠标捕获。
- System hook、屏幕键盘、Windows 音频/设备管理器菜单在 Linux 上隐藏。
- 打包（Nuitka）本期不做，直接 `python Mini-KVM.py`。
