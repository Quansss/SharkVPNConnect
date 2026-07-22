#!/usr/bin/env python3
"""
构建脚本 - 使用 PyInstaller 打包成 exe
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_pyinstaller():
    """检查并安装 pyinstaller"""
    try:
        import PyInstaller
        return True
    except ImportError:
        print("正在安装 PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        return True

def build():
    """构建 exe"""
    # 兼容本地和 CI 环境
    if os.environ.get("GITHUB_WORKSPACE"):
        base_dir = Path(os.environ["GITHUB_WORKSPACE"])
    else:
        base_dir = Path(__file__).parent.resolve()
    
    print("=" * 60)
    print("Palworld 联机客户端 - 构建脚本")
    print("=" * 60)
    
    # 检查 PyInstaller
    print("\n[1/5] 检查 PyInstaller...")
    check_pyinstaller()
    
    # 清理旧文件
    print("\n[2/5] 清理旧文件...")
    for folder in ["build", "dist"]:
        folder_path = base_dir / folder
        if folder_path.exists():
            shutil.rmtree(folder_path)
            print(f"  已删除: {folder}")
    
    # 构建客户端
    print("\n[3/5] 构建客户端 (迅鲨加速器.exe)...")
    # 内置 EasyTier 资源（避免下载失败）
    et_dir = base_dir / "easytier-extract" / "easytier-windows-x86_64"
    et_files = ['easytier-core.exe', 'wintun.dll', 'WinDivert64.sys', 'Packet.dll']
    add_data_args = []
    for f in et_files:
        src = et_dir / f
        if src.exists():
            # 用单文件方式逐个加，避免把整目录（包括 web/embed）都塞进去
            add_data_args += ['--add-data', f'{src};bundled']
        else:
            print(f"  ⚠ 缺失: {src}")
    print(f"  打包内置文件: {[f for f in et_files if (et_dir / f).exists()]}")

    # 图标（打包进 EXE，运行时从当前目录加载 icon.ico）
    icon_path = base_dir / "icon.ico"
    icon_arg = []
    if icon_path.exists():
        icon_arg = ['--icon', str(icon_path)]
        # 同步把 icon.ico 打包，运行时从 sys._MEIPASS 或当前目录读取
        add_data_args += ['--add-data', f'{icon_path};.']
        print(f"  使用图标: {icon_path.name} ({icon_path.stat().st_size / 1024:.1f} KB)")
    else:
        print("  ⚠ 未找到 icon.ico，将使用默认图标")

    client_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "迅鲨加速器",
        *icon_arg,
        *add_data_args,
        str(base_dir / "simple_client.py")
    ]
    
    result = subprocess.run(client_cmd, cwd=base_dir, capture_output=True, text=True)
    if result.returncode != 0:
        print("错误:", result.stderr)
        return False
    print("  客户端构建完成")
    
    # 构建授权生成器
    print("\n[4/5] 构建授权生成器 (LicenseGenerator.exe)...")
    gen_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "LicenseGenerator",
        str(base_dir / "simple_generator.py")
    ]
    
    result = subprocess.run(gen_cmd, cwd=base_dir, capture_output=True, text=True)
    if result.returncode != 0:
        print("错误:", result.stderr)
        return False
    print("  授权生成器构建完成")
    
    # 创建发布目录
    print("\n[5/5] 创建发布包...")
    release_dir = base_dir / "release" / "迅鲨加速器-v1.0.0"
    release_dir.mkdir(parents=True, exist_ok=True)

    # 复制 exe
    dist_dir = base_dir / "dist"
    shutil.copy(dist_dir / "迅鲨加速器.exe", release_dir)
    shutil.copy(dist_dir / "LicenseGenerator.exe", release_dir)
    # RegisterTool.exe 可选（如果单独构建过）
    if (dist_dir / "RegisterTool.exe").exists():
        shutil.copy(dist_dir / "RegisterTool.exe", release_dir)
    
    # 创建配置文件
    config = {
        "server": "sharkconnect.sharkos.cn:11010",
        "protocol": "tcp",
        "network_name": "palworld",
        "network_secret": "PALWORLD2024SECRET",
        "game_server": "10.144.0.1:8211"
    }
    import json
    with open(release_dir / "server_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    # 创建说明文件
    readme = """迅鲨加速器 v1.0.0
================================

文件说明
--------
迅鲨加速器.exe        - 客户端程序（给朋友使用）
LicenseGenerator.exe  - 授权码生成器（你自己使用）
RegisterTool.exe      - 注册机（本地授权码生成）
server_config.json    - 服务器配置文件

使用流程
--------
1. 【你】运行 RegisterTool.exe 生成授权码
2. 【朋友】运行 迅鲨加速器.exe，复制机器码发给你
3. 【你】在注册机中粘贴机器码、选择天数，生成授权码
4. 【朋友】在加速器中输入授权码，验证通过
5. 【朋友】点击"开始加速"，等待连接成功
6. 【朋友】启动游戏，加入多人游戏
7. 【朋友】输入服务器地址: 10.144.0.1:8211

授权说明
--------
- 每个授权码绑定一台机器
- 支持 7/30/90/180/365 天有效期，也可自定义
- 过期后需要重新授权

技术支持
--------
如有问题请联系服务器管理员。
"""
    with open(release_dir / "README.txt", "w", encoding="utf-8") as f:
        f.write(readme)
    
    # 打包成 zip
    zip_path = base_dir / "release" / "迅鲨加速器-v1.0.0.zip"
    shutil.make_archive(
        str(zip_path).replace(".zip", ""),
        'zip',
        release_dir
    )
    
    # 输出结果
    print("\n" + "=" * 60)
    print("构建完成!")
    print("=" * 60)
    print(f"发布包: {zip_path}")
    print(f"大小: {zip_path.stat().st_size / 1024:.1f} KB")
    print("=" * 60)
    print("\n文件列表:")
    for f in sorted(release_dir.iterdir()):
        size = f.stat().st_size / 1024
        print(f"  {f.name:30} {size:>8.1f} KB")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        build()
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")
