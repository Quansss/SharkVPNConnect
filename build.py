#!/usr/bin/env python3
"""
构建脚本 - 打包成 exe 安装包
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_cmd(cmd, cwd=None):
    """运行命令"""
    print(f">>> {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"错误: {result.stderr}")
        return False
    print(result.stdout)
    return True

def build():
    """构建 exe"""
    base_dir = Path("C:\\Users\\15062\\.qclaw\\workspace\\palworld-client-app")
    dist_dir = base_dir / "dist"
    build_dir = base_dir / "build"
    
    # 清理旧文件
    print("[1/5] 清理旧文件...")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        shutil.rmtree(build_dir)
    
    # 检查 pyinstaller
    print("[2/5] 检查依赖...")
    if not run_cmd("pip show pyinstaller"):
        print("安装 pyinstaller...")
        run_cmd("pip install pyinstaller")
    
    # 构建客户端
    print("[3/5] 构建客户端...")
    client_cmd = (
        f"pyinstaller --onefile --windowed --name PalworldClient "
        f"--icon=NONE "
        f"--add-data 'config.json;.' "
        f"{base_dir / 'client.py'}"
    )
    if not run_cmd(client_cmd, cwd=base_dir):
        print("客户端构建失败")
        return False
    
    # 构建授权生成器
    print("[4/5] 构建授权生成器...")
    gen_cmd = (
        f"pyinstaller --onefile --windowed --name LicenseGenerator "
        f"--icon=NONE "
        f"{base_dir / 'license_generator.py'}"
    )
    if not run_cmd(gen_cmd, cwd=base_dir):
        print("授权生成器构建失败")
        return False
    
    # 创建发布目录
    print("[5/5] 创建发布包...")
    release_dir = base_dir / "release" / "PalworldClient-v1.0.0"
    release_dir.mkdir(parents=True, exist_ok=True)
    
    # 复制文件
    shutil.copy(dist_dir / "PalworldClient.exe", release_dir)
    shutil.copy(dist_dir / "LicenseGenerator.exe", release_dir)
    
    # 创建配置文件
    config = {
        "server": "sharkconnect.sharkos.cn:11010",
        "protocol": "tcp",
        "network_name": "palworld",
        "network_secret": "PALWORLD2024SECRET",
        "game_server": "10.144.0.1:8211"
    }
    import json
    with open(release_dir / "config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    # 创建说明文件
    readme = """# Palworld 联机客户端 v1.0.0

## 文件说明

- **PalworldClient.exe** - 客户端程序（给朋友使用）
- **LicenseGenerator.exe** - 授权码生成器（你自己使用）
- **config.json** - 网络配置文件

## 使用流程

### 1. 生成授权码（你自己）
1. 运行 `LicenseGenerator.exe`
2. 让朋友提供他的机器码（运行 PalworldClient 可以看到）
3. 输入机器码，生成授权码
4. 把授权码发给朋友

### 2. 客户端使用（朋友）
1. 运行 `PalworldClient.exe`
2. 复制显示的机器码发给你
3. 收到授权码后，点击"输入授权码"
4. 填入授权码，验证通过
5. 点击"启动组网"
6. 等待显示连接成功
7. 启动帕鲁游戏，加入多人游戏
8. 输入服务器地址: 10.144.0.1:8211

## 授权说明

- 每个授权码绑定一台机器
- 授权码有效期可设置（7/30/90/365天）
- 过期后需要重新授权

## 技术支持

如有问题请联系服务器管理员。
"""
    with open(release_dir / "README.txt", "w", encoding="utf-8") as f:
        f.write(readme)
    
    # 打包
    zip_path = base_dir / "release" / "PalworldClient-v1.0.0.zip"
    shutil.make_archive(
        str(zip_path).replace(".zip", ""),
        'zip',
        release_dir
    )
    
    print(f"\n{'='*50}")
    print("  构建完成!")
    print(f"{'='*50}")
    print(f"  发布包: {zip_path}")
    print(f"  大小: {zip_path.stat().st_size / 1024 / 1024:.1f} MB")
    print(f"{'='*50}")
    print(f"\n文件列表:")
    for f in release_dir.iterdir():
        print(f"  - {f.name}")
    print(f"{'='*50}")

if __name__ == "__main__":
    build()
