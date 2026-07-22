#!/usr/bin/env python3
"""
macOS 构建脚本 - 支持 Apple Silicon (M1/M2/M3/M4) 和 Intel

注意：必须在 macOS 上执行此脚本
Windows 上无法直接打包 .app，但可以生成 macOS 用的 spec 文件
"""
import os
import sys
import platform

# 强制 UTF-8 输出
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass
import subprocess
from pathlib import Path


def check_platform():
    if platform.system() != "Darwin":
        print("⚠️  警告: 此脚本应在 macOS 上执行")
        print(f"   当前系统: {platform.system()}")
        return False
    return True


def check_arch():
    arch = platform.machine()
    if arch == "arm64":
        return "arm64", "Apple Silicon (M1/M2/M3/M4)"
    elif arch == "x86_64":
        return "x86_64", "Intel"
    else:
        return arch, "未知"


def check_pyinstaller():
    try:
        import PyInstaller
        return True
    except ImportError:
        print("正在安装 PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        return True


def download_macos_easytier(base_dir, arch):
    """下载 macOS 版 EasyTier，返回含二进制的目录"""
    extract_root = base_dir / "easytier-extract" / f"easytier-macos-{arch}"
    extract_root.mkdir(parents=True, exist_ok=True)

    EASYTIER_VERSION = "v2.6.4"
    if arch == "arm64":
        zip_name = f"easytier-macos-aarch64-{EASYTIER_VERSION}.zip"
    else:
        zip_name = f"easytier-macos-x86_64-{EASYTIER_VERSION}.zip"

    url = f"https://github.com/EasyTier/EasyTier/releases/download/{EASYTIER_VERSION}/{zip_name}"
    zip_path = base_dir / f"easytier-macos-{arch}.zip"

    print(f"  下载: {url}")
    r = subprocess.run(["curl", "-sL", "-o", str(zip_path), url], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  curl 失败: {r.stderr}")
        sys.exit(1)

    size = zip_path.stat().st_size
    print(f"  下载完成: {size} bytes ({size//1024//1024} MB)")
    if size < 10000:
        print(f"  ⚠️  文件可能过小（{size} bytes），内容: {zip_path.read_bytes()[:200]}")
        sys.exit(1)

    print(f"  解压到 {extract_root}...")
    subprocess.run(["unzip", "-o", str(zip_path), "-d", str(extract_root)], check=True, capture_output=True)
    zip_path.unlink()

    # 找到实际的二进制目录（zip 嵌套一层：easytier-macos-x86_64-v2.6.4/easytier-core）
    # 搜索 easytier-core 或 easytier-cli 所在位置
    candidates = list(extract_root.glob("*/"))
    all_files = list(extract_root.glob("**/*"))
    print(f"  解压内容: {[str(f) for f in all_files[:10]]}")

    # 找到含 easytier-core 的目录
    for f in all_files:
        if f.name in ('easytier-core', 'easytier-cli'):
            et_dir = f.parent
            print(f"  ✅ 找到二进制: {f.name}，位于 {et_dir}")
            return et_dir

    print(f"  ❌ 未找到 easytier-core！目录内容:")
    for f in all_files:
        print(f"    {f}")
    sys.exit(1)


def build_macos_app(base_dir, arch, et_dir):
    """构建 macOS .app（包含 easytier 二进制）"""

    # 确认二进制真实存在
    et_binaries = []
    for fname in ['easytier-core', 'easytier-cli']:
        src = et_dir / fname
        if src.exists():
            et_binaries.append((str(src), fname))
            print(f"  ✅ 找到 {fname} ({src.stat().st_size // 1024} KB)")
        else:
            print(f"  ⚠️  缺失: {src}")

    icon_icns = base_dir / "icon.icns"
    icon_line = f"icon={repr(str(icon_icns))}," if icon_icns.exists() else ""

    # 构建 binaries 参数字符串（供 spec 使用）
    binaries_repr = "[\n"
    for src, name in et_binaries:
        # macOS binaries: ('/abs/path', 'dest_subdir/')
        binaries_repr += f"    (r'{src}', 'bin/{name}'),\n"
    binaries_repr += "]"

    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
import sys, os
from pathlib import Path
from PyInstaller.building.api import EXE, COLLECT, PYZ
from PyInstaller.building.macOS import BUNDLE

block_cipher = None

binaries = {binaries_repr}

# tkinter 完整导入（macOS 关键）
hiddenimports = [
    'tkinter', 'tkinter.ttk', 'tkinter.scrolledtext',
    'tkinter.messagebox', 'tkinter.filedialog',
]

a = Analysis(
    [str(Path(__file__).parent / "simple_client.py")],
    pathex=[],
    binaries=binaries,
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts,
    exclude_binaries=True,
    name='迅鲨加速器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False, upx=False,
    console=False,
    disable_windowed_traceback=False,
    target_arch='{arch}',
)
coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False, upx=False,
    name='迅鲨加速器',
)
app = BUNDLE(
    coll,
    name='迅鲨加速器.app',
    {icon_line}
    bundle_identifier='com.shark.vpnconnect',
    info_plist={{
        'CFBundleName': '迅鲨加速器',
        'CFBundleDisplayName': '迅鲨加速器',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
        'LSUIElement': False,
        'NSPrincipalClass': 'NSApplication',
    }},
)
'''

    spec_path = base_dir / f"spec-macos-{arch}.spec"
    spec_path.write_text(spec_content, encoding='utf-8')
    print(f"  生成 spec: {spec_path}")

    print(f"  运行 PyInstaller ({arch})...")
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", str(spec_path)],
        cwd=base_dir,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("STDOUT:", result.stdout[-2000:] if result.stdout else "(empty)")
        print("STDERR:", result.stderr[-2000:] if result.stderr else "(empty)")
        return False

    # 【关键】给 .app 内所有文件加执行权限
    app_path = base_dir / "dist" / "迅鲨加速器.app"
    if app_path.exists():
        print("  修复执行权限...")
        for root, dirs, files in os.walk(app_path / "Contents" / "MacOS"):
            for fname in files:
                os.chmod(os.path.join(root, fname), 0o755)
        for root, dirs, files in os.walk(app_path / "Contents" / "Resources"):
            for fname in files:
                os.chmod(os.path.join(root, fname), 0o755)
        print("  权限修复完成")

    return True


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--arch", choices=["arm64", "x86_64"], default=None)
    args, _ = parser.parse_known_args()

    print("=" * 60)
    print("迅鲨加速器 - macOS 构建脚本")
    print("=" * 60)

    is_macos = check_platform()
    host_arch, host_arch_name = check_arch()

    arch = args.arch or host_arch
    arch_name = "Apple Silicon" if arch == "arm64" else "Intel / x86_64"
    print(f"\n主机架构: {host_arch_name} ({host_arch})")
    print(f"目标架构: {arch_name} ({arch})")

    # Rosetta 检测
    if arch == "x86_64" and host_arch == "arm64":
        print("\n⚠️  Apple Silicon 主机构建 Intel 版本")
        if is_macos:
            r = subprocess.run(["sysctl", "-n", "sysctl.proc_translated"], capture_output=True, text=True)
            if r.stdout.strip() == "1":
                print("  ✅ Rosetta 2 模式运行中")
            else:
                print("  ❌ 未在 Rosetta 模式！需要: arch -x86_64 python3 build_macos.py --arch x86_64")
                sys.exit(1)

    if not is_macos:
        print("\n非 macOS 环境，仅生成 spec 配置...")

    base_dir = Path(__file__).parent.resolve()
    if os.environ.get("GITHUB_WORKSPACE"):
        base_dir = Path(os.environ["GITHUB_WORKSPACE"])

    print(f"项目目录: {base_dir}")

    print("\n[1/4] 检查 PyInstaller...")
    check_pyinstaller()

    print(f"\n[2/4] 下载 EasyTier macOS {arch}...")
    et_dir = download_macos_easytier(base_dir, arch)

    print(f"\n[3/4] 构建 .app ({arch})...")
    if not build_macos_app(base_dir, arch, et_dir):
        sys.exit(1)

    app_path = base_dir / "dist" / "迅鲨加速器.app"
    if app_path.exists():
        print(f"\n  ✅ .app 生成成功: {app_path}")

        # 验证架构
        if is_macos:
            main_bin = app_path / "Contents" / "MacOS" / "迅鲨加速器"
            if main_bin.exists():
                r = subprocess.run(["file", str(main_bin)], capture_output=True, text=True)
                print(f"  架构验证: {r.stdout.strip()}")

            # 验证 easytier-core 是否在 app 里
            for root, dirs, files in os.walk(app_path):
                for f in files:
                    if 'easytier' in f:
                        full = os.path.join(root, f)
                        r2 = subprocess.run(["file", full], capture_output=True, text=True)
                        print(f"  {f}: {r2.stdout.strip()}")

        print("\n[4/4] 创建 zip...")
        zip_path = base_dir / f"迅鲨加速器-v1.0.0-macOS-{arch}.zip"
        r = subprocess.run(
            ["zip", "-r", str(zip_path), "迅鲨加速器.app"],
            cwd=app_path.parent,
            capture_output=True, text=True
        )
        if r.returncode == 0:
            print(f"  ✅ zip 生成: {zip_path} ({zip_path.stat().st_size // 1024 // 1024} MB)")
        else:
            print(f"  zip 失败: {r.stderr}")

    print("\n" + "=" * 60)
    print("构建完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
