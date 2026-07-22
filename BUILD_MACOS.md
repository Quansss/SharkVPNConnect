# 迅鲨加速器 - macOS 打包指南

## 支持的架构

| 架构 | 标识 | 适用设备 |
|------|------|----------|
| Apple Silicon | `arm64` | M1 / M2 / M3 / M4 |
| Intel | `x86_64` | 2017 年前的 Mac |

## 前置要求

### 1. 准备 Mac 电脑
- **Apple Silicon (M系列)**：用于打包 `.app` 给 M 芯片用户
- **Intel Mac**：用于打包 `.app` 给 Intel 用户
- 或者一台 Apple Silicon Mac + Rosetta 2

### 2. 安装 Python 3.9+
```bash
brew install python@3.12
```

### 3. 安装 PyInstaller
```bash
pip3 install pyinstaller
```

### 4. （可选）安装 create-dmg 用于生成安装包
```bash
brew install create-dmg
```

## 打包步骤

### 在 Mac 上执行

```bash
# 1. 把整个项目文件夹传到 Mac（USB / 网盘 / git）
# 2. 进入项目目录
cd SharkVPNConnect

# 3. 运行 macOS 构建脚本
python3 build_macos.py

# 4. 脚本会自动：
#    - 检测 Mac 架构
#    - 下载对应版本的 EasyTier
#    - 打包成 .app
#    - 生成 DMG 安装包（如果装了 create-dmg）
```

### 产出物

```
dist/
├── 迅鲨加速器.app          # macOS 应用包
├── 迅鲨加速器              # 可执行文件
└── ...

迅鲨加速器-v1.0.0-macOS-arm64.dmg    # Apple Silicon 安装包
或
迅鲨加速器-v1.0.0-macOS-x86_64.dmg   # Intel 安装包
```

## macOS 代码签名（解决"无法打开"提示）

macOS 默认会拦截未签名的应用。两种解决方案：

### 方案 A：用户首次运行时手动允许
1. 双击 `.app`，系统提示"无法打开"
2. 打开 **系统设置 → 隐私与安全性**
3. 点击 **仍要打开**
4. 输入密码确认

### 方案 B：开发者签名（推荐）
需要 Apple Developer 账号（$99/年）：

```bash
# 用开发者证书签名
codesign --deep --force --options runtime \
  --sign "Developer ID Application: 你的名字 (TEAMID)" \
  迅鲨加速器.app

# 公证（Notarization）
xcrun notarytool submit 迅鲨加速器.app \
  --keychain-profile "AC_PASSWORD" \
  --wait
```

### 方案 C：临时绕过（最简单，仅开发测试用）
```bash
# 移除隔离属性
xattr -cr 迅鲨加速器.app
```

## 通用二进制（Universal Binary）

如果想一个 `.app` 同时支持 M 芯片和 Intel：

```bash
# 用 lipo 合并两个架构的二进制
lipo -create \
  dist-arm64/迅鲨加速器 \
  dist-x86_64/迅鲨加速器 \
  -output 迅鲨加速器-universal
```

或在 PyInstaller 中指定 `target_arch='universal2'`（需要较新版本）。

## EasyTier 资源说明

macOS 版的 EasyTier 不需要：
- ❌ `wintun.dll`（Windows 专用）
- ❌ `WinDivert64.sys`（Windows 专用）
- ❌ `Packet.dll`（Windows 专用）

只需要：
- ✅ `easytier-core`（主程序）
- ✅ `easytier-cli`（命令行工具，可选）

## TUN 设备权限

macOS 上创建 TUN 设备需要**管理员权限**或**特殊 entitlement**。

### 用户运行时的处理
应用首次创建 TUN 时会弹窗：
> "系统扩展已更新"
> 输入密码确认

或用 `sudo` 启动：
```bash
sudo /Applications/迅鲨加速器.app/Contents/MacOS/迅鲨加速器
```

## 已知问题

1. **Gatekeeper 拦截**：未签名应用首次打开会被拦截，需手动允许
2. **TUN 设备**：需要管理员授权（macOS 13+ 增加了更严格的限制）
3. **图标**：需要 `icon.icns` 格式（从 `icon.ico` 转换：`sips -s format icns icon.ico --out icon.icns`）

## 转换图标

```bash
# 从 PNG 转换
sips -s format icns icon.png --out icon.icns

# 从 ICO 转换（需要先转 PNG）
# Windows: 用在线工具或 ImageMagick
# Mac: 装 imagemagick
brew install imagemagick
convert icon.ico icon.png
sips -s format icns icon.png --out icon.icns
```
