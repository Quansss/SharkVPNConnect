# SharkVPNConnect / 迅鲨加速器

迅鲨云联机助手 - 基于 EasyTier 的游戏联机加速工具

## 项目结构

| 文件 | 说明 |
|------|------|
| simple_client.py | 主客户端 GUI（暗色游戏风格） |
| register_tool.py | 授权注册工具（白底简洁风格） |
| license_generator.py | 授权码生成器（服务端用） |
| build_exe.py | PyInstaller 打包脚本 |
| rebuild.bat | 一键重新构建 |
| icon.ico | 应用程序图标 |

## 主要功能

- EasyTier 虚拟组网客户端
- HMAC-SHA256 授权验证机制
- 支持按天数/到期日两种授权模式
- 内置 EasyTier 核心程序（免下载）

## 构建

```bash
python build_exe.py
```

## 版本

v1.0.0
