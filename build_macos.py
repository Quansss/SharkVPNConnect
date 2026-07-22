#!/usr/bin/env python3
"""
macOS 构建脚本 - 支持 Apple Silicon (M1/M2/M3/M4) 和 Intel

注意：必须在 macOS 上执行此脚本
Windows 上无法直接打包 .app，但可以生成 macOS 用的 spec 文件
"""
import os
import sys
import platform
import io

# 强制 UTF-8 输出（避免 Windows CI 环境的 cp1252 编码问题）
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass
import subprocess
import shutil
from pathlib import Path

def check_platform():
    """检查是否在 macOS 上运行"""
    if platform.system() != "Darwin":
        print("⚠️  警告: 此脚本应在 macOS 上执行")
        print(f"   当前系统: {platform.system()}")
        return False
    return True

def check_arch():
    """检测 Mac 架构"""
    arch = platform.machine()
    if arch == "arm64":
        return "arm64", "Apple Silicon (M1/M2/M3/M4)"
    elif arch == "x86_64":
        return "x86_64", "Intel"
    else:
        return arch, "未知"

def check_pyinstaller():
    """检查 PyInstaller"""
    try:
        import PyInstaller
        return True
    except ImportError:
        print("正在安装 PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        return True

def download_macos_easytier(base_dir, arch):
    """下载 macOS 版 EasyTier"""
    et_dir = base_dir / "easytier-extract" / f"easytier-macos-{arch}"
    et_dir.mkdir(parents=True, exist_ok=True)
    
    # EasyTier GitHub releases URL（锁定到具体版本，避免 latest 不稳定）
    EASYTIER_VERSION = "v2.6.4"
    if arch == "arm64":
        url = f"https://github.com/EasyTier/EasyTier/releases/download/{EASYTIER_VERSION}/easytier-macos-aarch64-{EASYTIER_VERSION}.zip"
    else:
        url = f"https://github.com/EasyTier/EasyTier/releases/download/{EASYTIER_VERSION}/easytier-macos-x86_64-{EASYTIER_VERSION}.zip"
    
    print(f"  下载 EasyTier for {arch}...")
    zip_path = base_dir / f"easytier-macos-{arch}.zip"
    subprocess.run(["curl", "-L", "-o", str(zip_path), url], check=True)
    
    # 解压
    print(f"  解压到 {et_dir}...")
    subprocess.run(["unzip", "-o", str(zip_path), "-d", str(et_dir)], check=True)
    
    files = list(et_dir.glob("*"))
    print(f"  包含文件: {[f.name for f in files]}")
    return et_dir

def build_macos_app(base_dir, arch, et_dir):
    """构建 macOS .app"""
    
    et_files = ['easytier-core', 'easytier-cli']
    add_data_args = []
    for f in et_files:
        src = et_dir / f
        if src.exists():
            add_data_args += ['--add-data', f'{src}:bundled']
        else:
            print(f"  ⚠ 缺失: {src}")
    
    spec_path = base_dir / f"迅鲨加速器-macos-{arch}.spec"
    
    # 写 spec 文件
    icon_icns = base_dir / "icon.icns"
    icon_section = f"icon=str(icon_icns) if icon_icns.exists() else None,"
    icon_section_lines = f"    icon={repr(str(icon_icns))} if icon_icns.exists() else None,\n"
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
# macOS {arch} 构建 spec
import sys
from pathlib import Path

block_cipher = None
base_dir = Path(r"{base_dir}")
et_dir = base_dir / "easytier-extract" / "easytier-macos-{arch}"
icon_icns = base_dir / "icon.icns"

a = Analysis(
    [str(base_dir / "simple_client.py")],
    pathex=[str(base_dir)],
    binaries=[],
    datas=[],
    hiddenimports=['tkinter'],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='迅鲨加速器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    target_arch='{arch}',
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='迅鲨加速器',
)
app = BUNDLE(
    coll,
    name='迅鲨加速器.app',
{icon_section_lines}    bundle_identifier='com.shark.vpnconnect',
    info_plist={{
        'CFBundleName': '迅鲨加速器',
        'CFBundleDisplayName': '迅鲨加速器',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
        'LSUIElement': False,
    }},
)
'''
    
    spec_path.write_text(spec_content, encoding='utf-8')
    print(f"  生成 spec: {spec_path}")
    
    print(f"  开始 PyInstaller 打包 ({arch})...")
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--clean", str(spec_path)],
        cwd=base_dir,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print("错误:", result.stderr)
        return False
    return True

def create_dmg(app_path, output_path, arch):
    """创建 DMG 安装包"""
    print(f"  创建 DMG 安装包...")
    if subprocess.run(["which", "create-dmg"], capture_output=True).returncode == 0:
        subprocess.run([
            "create-dmg",
            "--volname", f"迅鲨加速器-{arch}",
            "--window-pos", "200", "120",
            "--window-size", "600", "400",
            "--icon-size", "100",
            "--icon", "迅鲨加速器.app", "175", "190",
            "--app-drop-link", "425", "190",
            str(output_path),
            str(app_path.parent)
        ])
    else:
        print("  ⚠ 未安装 create-dmg，跳过 DMG 创建")
        print("  安装命令: brew install create-dmg")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--arch", choices=["arm64", "x86_64"], default=None,
                        help="目标架构（默认自动检测主机架构）")
    args, _ = parser.parse_known_args()
    
    print("=" * 60)
    print("迅鲨加速器 - macOS 构建脚本")
    print("=" * 60)
    
    is_macos = check_platform()
    host_arch, host_arch_name = check_arch()
    
    # 目标架构（CLI 传参优先，否则跟随主机）
    arch = args.arch or host_arch
    arch_name = "Apple Silicon (M1/M2/M3/M4)" if arch == "arm64" else "Intel / x86_64"
    print(f"\n主机架构: {host_arch_name} ({host_arch})")
    print(f"目标架构: {arch_name} ({arch})")
    
    # 如果要构建 x86_64 但主机是 arm64，提示需要 Rosetta
    if arch == "x86_64" and host_arch == "arm64":
        print("\n⚠️  检测到 Apple Silicon 上构建 Intel 版本")
        print("   需要在 Rosetta 2 下运行 Python：")
        print("   arch -x86_64 python3 build_macos.py --arch x86_64")
        if is_macos:
            # 检查是否真的在 Rosetta 下运行
            import subprocess as _sp
            res = _sp.run(["sysctl", "-n", "sysctl.proc_translated"], capture_output=True, text=True)
            if res.stdout.strip() == "1":
                print("   ✅ 确认在 Rosetta 转译模式下运行")
            else:
                print("   ❌ 当前未在 Rosetta 模式！请用 'arch -x86_64' 前缀重新运行")
                sys.exit(1)
    
    if not is_macos:
        print("\n继续生成构建配置，但不实际打包...")
    
    # 自动检测项目目录（兼容本地和 CI）
    if os.environ.get("GITHUB_WORKSPACE"):
        base_dir = Path(os.environ["GITHUB_WORKSPACE"])
    elif is_macos:
        base_dir = Path(__file__).parent.resolve()
    else:
        base_dir = Path(__file__).parent.resolve()
    
    print(f"项目目录: {base_dir}")
    
    print("\n[1/4] 检查 PyInstaller...")
    check_pyinstaller()
    
    print(f"\n[2/4] 下载 EasyTier macOS {arch} 版...")
    et_dir = download_macos_easytier(base_dir, arch)
    
    print(f"\n[3/4] 构建 .app ({arch})...")
    if build_macos_app(base_dir, arch, et_dir):
        app_path = base_dir / "dist" / "迅鲨加速器.app"
        if app_path.exists():
            print(f"  ✅ 打包成功: {app_path}")
            
            # 验证产物架构
            if is_macos:
                import subprocess as _sp
                main_bin = app_path / "Contents" / "MacOS" / "迅鲨加速器"
                if main_bin.exists():
                    res = _sp.run(["file", str(main_bin)], capture_output=True, text=True)
                    print(f"  架构信息: {res.stdout.strip()}")
            
            print(f"\n[4/4] 创建 DMG...")
            dmg_path = base_dir / f"迅鲨加速器-v1.0.0-macOS-{arch}.dmg"
            create_dmg(app_path, dmg_path, arch)
        else:
            print("  ⚠ 未找到生成的 .app")
    
    print("\n" + "=" * 60)
    print("完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
