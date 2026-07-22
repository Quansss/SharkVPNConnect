#!/usr/bin/env python3
"""
迅鲨云联机客户端 - 简化版(纯 tkinter,无外部依赖)
"""
import os
import sys
import ctypes
import json
import hashlib
import subprocess
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime, timedelta
from pathlib import Path
import urllib.request
import zipfile
import shutil
import platform as _platform

# 平台标识
IS_WINDOWS = sys.platform == "win32"
IS_MACOS = sys.platform == "darwin"

def is_admin():
    """检查是否以管理员身份运行（macOS/Linux 不强制，返回 True）"""
    if not IS_WINDOWS:
        return True
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def run_as_admin():
    """以管理员身份重新启动程序（仅 Windows）"""
    if not IS_WINDOWS:
        return False
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后的 exe
        executable = sys.executable
        params = ''
    else:
        # Python 脚本
        executable = sys.executable
        params = f'"{os.path.abspath(__file__)}"'

    ret = ctypes.windll.shell32.ShellExecuteW(
        None,           # hwnd
        'runas',        # lpOperation (请求 UAC 提升)
        executable,     # lpFile
        params,         # lpParameters
        None,           # lpDirectory
        1               # nShowCmd (SW_SHOWNORMAL)
    )

    # ret > 32 表示成功
    return ret > 32


TASK_NAME = "XunShaYunLinkTool"


def install_admin_task():
    """一次性安装最高权限计划任务(创建后双击桌面快捷方式免UAC)（仅 Windows）"""
    if not IS_WINDOWS:
        return False, "仅 Windows 支持此功能"
    if not getattr(sys, 'frozen', False):
        return False, "仅打包后的 EXE 可安装"

    exe = sys.executable
    # /rl highest 让任务直接以管理员权限运行,触发时不弹 UAC
    cmd = ['schtasks', '/create', '/tn', TASK_NAME,
           '/tr', f'"{exe}"', '/sc', 'once', '/st', '00:00',
           '/rl', 'highest', '/f']
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        return False, f"创建任务失败: {r.stderr.strip()}"

    # 同步创建桌面快捷方式,目标为 schtasks /run,触发任务以绕过 UAC
    desktop = Path(os.environ.get('USERPROFILE', '')) / 'Desktop'
    shortcut = desktop / '迅鲨云联机助手.lnk'
    ps = (
        f"$s = (New-Object -COM WScript.Shell).CreateShortcut('{shortcut}');"
        f"$s.TargetPath = 'schtasks.exe';"
        f"$s.Arguments = '/run /tn {TASK_NAME}';"
        f"$s.WorkingDirectory = '%WINDIR%\\System32';"
        f"$s.IconLocation = '{exe}';"
        f"$s.Description = '迅鲨云联机助手(免UAC管理员启动)';"
        f"$s.Save()"
    )
    r2 = subprocess.run(['powershell', '-NoProfile', '-Command', ps],
                        capture_output=True, text=True)
    if r2.returncode != 0:
        return True, f"任务已创建,但桌面快捷方式失败: {r2.stderr.strip()}"
    return True, f"已安装!请使用桌面\"迅鲨云联机助手\"快捷方式启动,以后不会再弹UAC。"


def uninstall_admin_task():
    """卸载管理员计划任务和快捷方式"""
    if not IS_WINDOWS:
        return
    subprocess.run(['schtasks', '/delete', '/tn', TASK_NAME, '/f'],
                   capture_output=True)
    desktop = Path(os.environ.get('USERPROFILE', '')) / 'Desktop'
    shortcut = desktop / '迅鲨云联机助手.lnk'
    if shortcut.exists():
        try:
            shortcut.unlink()
        except Exception:
            pass


def has_admin_task():
    """检查计划任务是否已存在"""
    if not IS_WINDOWS:
        return False
    r = subprocess.run(['schtasks', '/query', '/tn', TASK_NAME],
                       capture_output=True, text=True)
    return r.returncode == 0

# 配置
APP_NAME = "迅鲨云联机助手"
VERSION = "1.0.0"
NETWORK_CONFIG = {
    "server": "sharkconnect.sharkos.cn:11010",
    "protocol": "tcp",
    "network_name": "palworld",
    "network_secret": "PALWORLD2024SECRET"
}

class LicenseManager:
    """授权管理器"""
    SECRET = "PALWORLD_2024_AUTH"

    def __init__(self):
        self.app_dir = Path(os.environ.get('LOCALAPPDATA', '')) / 'PalworldClient'
        self.app_dir.mkdir(parents=True, exist_ok=True)
        self.license_file = self.app_dir / 'license.dat'
        self.machine_id = self._get_machine_id()

    def _get_machine_id(self):
        """获取机器唯一标识"""
        try:
            import platform
            machine = platform.machine()
            processor = platform.processor()
            node = platform.node()
            data = f"{machine}_{processor}_{node}"
            return hashlib.md5(data.encode()).hexdigest()[:16].upper()
        except:
            return hashlib.md5(os.environ.get('COMPUTERNAME', 'UNKNOWN').encode()).hexdigest()[:16].upper()

    def generate_license(self, machine_id, days=30):
        """生成授权码(静态方法,用于生成器)"""
        data = f"{machine_id}_{days}_{self.SECRET}"
        return hashlib.sha256(data.encode()).hexdigest()[:24].upper()

    def validate_license(self, license_key):
        """验证授权码"""
        try:
            # 尝试不同天数
            for days in [7, 30, 90, 365, 999]:
                expected = self.generate_license(self.machine_id, days)
                if license_key.upper() == expected:
                    expiry = datetime.now() + timedelta(days=days)
                    self._save_license(license_key, expiry)
                    return True, expiry
            return False, None
        except Exception as e:
            return False, str(e)

    def _save_license(self, key, expiry):
        """保存授权信息"""
        data = {
            "key": key,
            "expiry": expiry.isoformat(),
            "machine_id": self.machine_id
        }
        with open(self.license_file, 'w') as f:
            json.dump(data, f)

    def check_license(self):
        """检查授权状态"""
        try:
            if not self.license_file.exists():
                return False, "未授权", None

            with open(self.license_file, 'r') as f:
                data = json.load(f)

            # 检查机器ID
            if data.get('machine_id') != self.machine_id:
                return False, "授权与机器不匹配", None

            # 检查有效期
            expiry = datetime.fromisoformat(data['expiry'])
            if datetime.now() > expiry:
                return False, "授权已过期", expiry

            days_left = (expiry - datetime.now()).days
            return True, f"授权有效 (剩余 {days_left} 天)", expiry

        except Exception as e:
            return False, f"授权验证失败: {e}", None

class EasyTierManager:
    """EasyTier 管理器（内置资源自动释放，无需联网下载）"""

    # 启动时需要的文件（按平台不同）
    if IS_WINDOWS:
        REQUIRED_FILES = ['easytier-core.exe', 'wintun.dll', 'WinDivert64.sys', 'Packet.dll']
    elif IS_MACOS:
        REQUIRED_FILES = ['easytier-core', 'easytier-cli']
    else:
        REQUIRED_FILES = ['easytier-core']

    def __init__(self):
        if IS_WINDOWS:
            self.app_dir = Path(os.environ.get('LOCALAPPDATA', '')) / 'PalworldClient'
            self.app_dir.mkdir(parents=True, exist_ok=True)
            self.easytier_path = self.app_dir / 'easytier-core.exe'
        elif IS_MACOS:
            # macOS: 使用用户可写目录，避免 .app bundle 只读问题
            self.app_dir = Path.home() / 'Library' / 'Application Support' / 'SharkVPNConnect' / 'bin'
            self.app_dir.mkdir(parents=True, exist_ok=True)
            self.easytier_path = self.app_dir / 'easytier-core'
        else:
            base = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
            self.app_dir = base
            self.easytier_path = base / 'easytier-core'
        self.process = None

    def _find_bundled_dir(self):
        """查找内置资源目录（必须包含 REQUIRED_FILES 所有文件）"""
        required = set(self.REQUIRED_FILES)

        def _check_dir(d):
            if not d or not d.exists() or not d.is_dir():
                return None
            if all((d / f).is_file() for f in required):
                return d
            return None

        # 候选根目录
        roots = []
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            roots.append(Path(meipass))
        if getattr(sys, 'frozen', False):
            roots.append(Path(sys.executable).parent)
            # macOS BUNDLE 结构：COLLECT name 可能作为子目录
            if IS_MACOS:
                roots.append(Path(sys.executable).parent / '迅鲨加速器')
        else:
            roots.append(Path(__file__).parent)

        # 1) 浅层查找（根 / bin / bundled）
        for r in roots:
            for d in [r, r / 'bin', r / 'bundled']:
                hit = _check_dir(d)
                if hit:
                    return hit

        # 2) macOS 兜底：在 exe 附近递归查找（限定深度）
        if IS_MACOS and getattr(sys, 'frozen', False):
            base = Path(sys.executable).parent
            try:
                for p in base.glob('**/easytier-core'):
                    if p.is_file() and _check_dir(p.parent):
                        return p.parent
            except Exception:
                pass
        return None

    def _extract_bundled(self, log_callback=None):
        """从内置资源释放到 app_dir"""
        bundled_dir = self._find_bundled_dir()
        if not bundled_dir:
            return False

        if log_callback:
            log_callback("正在从内置资源安装 EasyTier...")

        for fname in self.REQUIRED_FILES:
            src = bundled_dir / fname
            dst = self.app_dir / fname
            if src.exists() and not dst.exists():
                try:
                    shutil.copy2(str(src), str(dst))
                    if log_callback:
                        log_callback(f"  已安装: {fname}")
                except Exception as e:
                    if log_callback:
                        log_callback(f"  安装 {fname} 失败: {e}")
                    return False
        return True

    def is_installed(self):
        """检查是否已安装"""
        return self.easytier_path.exists()

    def install(self, log_callback=None):
        """一键安装：先尝试内置资源，失败再下载"""
        # 1. 优先用内置资源
        if self._find_bundled_dir():
            if self._extract_bundled(log_callback):
                if log_callback:
                    log_callback("EasyTier 安装完成（内置版本）")
                return True
            if log_callback:
                log_callback("内置资源安装失败,尝试联网下载...")

        # 2. 备用：联网下载
        return self._download(log_callback)

    def _download(self, log_callback=None):
        """联网下载 EasyTier（备用）"""
        try:
            url = "https://github.com/EasyTier/EasyTier/releases/download/v2.6.4/easytier-windows-x86_64-v2.6.4.zip"
            temp_zip = self.app_dir / 'temp_easytier.zip'

            if log_callback:
                log_callback("正在下载 EasyTier...")

            urllib.request.urlretrieve(url, str(temp_zip))

            if log_callback:
                log_callback("正在解压...")

            with zipfile.ZipFile(temp_zip, 'r') as zf:
                for name in zf.namelist():
                    base_name = name.split('/')[-1]
                    if base_name in self.REQUIRED_FILES:
                        target = self.app_dir / base_name
                        if log_callback:
                            log_callback(f"提取 {base_name}...")
                        with zf.open(name) as src:
                            with open(target, 'wb') as dst:
                                dst.write(src.read())

            temp_zip.unlink()

            if log_callback:
                log_callback("EasyTier 安装完成(联网下载)")

            return True

        except Exception as e:
            if log_callback:
                log_callback(f"下载失败: {e}")
            return False

    # 兼容旧接口
    def download(self, log_callback=None):
        return self.install(log_callback)

    def start(self, log_callback=None):
        """启动 EasyTier"""
        try:
            if not self.is_installed():
                return False, "EasyTier 未安装"

            # macOS 下确保二进制有可执行权限
            if IS_MACOS and os.path.exists(str(self.easytier_path)):
                try:
                    os.chmod(str(self.easytier_path), 0o755)
                except Exception:
                    pass

            cmd = [
                str(self.easytier_path),
                "-p", f"{NETWORK_CONFIG['protocol']}://{NETWORK_CONFIG['server']}",
                "--network-name", NETWORK_CONFIG['network_name'],
                "--network-secret", NETWORK_CONFIG['network_secret'],
                "--hostname", f"Player-{int(time.time()) % 10000}",
                "-d",                         # DHCP 自动分配虚拟 IP
                "--no-listener"
            ]

            popen_kwargs = dict(
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            if IS_WINDOWS:
                # 启动进程(隐藏窗口)
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                popen_kwargs['startupinfo'] = startupinfo
                popen_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

            self.process = subprocess.Popen(cmd, **popen_kwargs)

            # 启动日志线程
            def log_reader():
                for line in self.process.stdout:
                    if log_callback:
                        log_callback(line.strip())

            threading.Thread(target=log_reader, daemon=True).start()

            return True, "EasyTier 已启动"

        except Exception as e:
            return False, str(e)

    def stop(self):
        """停止 EasyTier"""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except:
                self.process.kill()
            self.process = None
            return True, "EasyTier 已停止"
        return False, "EasyTier 未运行"

    def is_running(self):
        """检查是否在运行"""
        return self.process is not None and self.process.poll() is None

class MainApp:
    """主应用"""

    def __init__(self):
        self.root = tk.Tk()
        # 设置窗口图标（支持 PyInstaller 打包后从临时目录读取）
        try:
            if getattr(sys, 'frozen', False):
                icon_path = Path(sys._MEIPASS) / "icon.ico"
            else:
                icon_path = Path(__file__).parent / "icon.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except Exception:
            pass  # 图标加载失败不影响主程序
        self.root.title(f"{APP_NAME} v{VERSION}")
        self.root.update_idletasks()
        w, h = 520, 420
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.resizable(False, False)
        # 深色窗体
        self.BG = "#0a0e1a"
        self.CARD = "#131826"
        self.CARD2 = "#1a2138"
        self.BORDER = "#1f2a40"
        self.ACCENT = "#00d4ff"      # 青
        self.ACCENT2 = "#b16cff"     # 紫
        self.OK = "#00ff88"          # 绿
        self.BAD = "#ff4d6d"         # 红
        self.WARN = "#ffaa00"        # 橙
        self.TEXT = "#e6edf3"
        self.SUB = "#8b95a8"
        self.root.configure(bg=self.BG)
        try:
            self.root.attributes('-alpha', 0.97)
        except Exception:
            pass

        self.license_mgr = LicenseManager()
        self.easytier_mgr = EasyTierManager()

        # 启动管理员检查:如果不是管理员则自动提升
        if not is_admin():
            root_msg = tk.Tk()
            root_msg.withdraw()
            if messagebox.askyesno(
                "需要管理员权限",
                "本程序需要以管理员身份运行,\n才能创建虚拟网卡连接服务器。\n\n点击\uff02是\uff02以管理员身份重新启动。"
            ):
                if run_as_admin():
                    sys.exit(0)
            root_msg.destroy()
        else:
            # 已获得管理员:如果还没有创建常驻计划任务,问用户是否要一键安装
            # 装好后以后双击桌面快捷方式直接管理员启动,不再弹UAC
            if not has_admin_task():
                root_msg = tk.Tk()
                root_msg.withdraw()
                if messagebox.askyesno(
                    "一键安装",
                    "检测到你是首次以管理员身份运行。\n\n"
                    "推荐安装\uff02管理员服务\uff02:"
                    "只需授权这一次,以后双击桌面快捷方式\n"
                    "就能直接以管理员身份启动,不再弹UAC。\n\n"
                    "现在安装吗?"
                ):
                    ok, msg = install_admin_task()
                    messagebox.showinfo("安装结果", msg)
                root_msg.destroy()

        self.setup_ui()
        self.check_license()

    def _neon_button(self, parent, text, color, command):
        """绘制一个霓虹按钮，返回 (canvas, set_enabled)"""
        h = 52
        canvas = tk.Canvas(parent, height=h, bg=self.CARD,
                           highlightthickness=0, cursor='hand2')
        state = {'enabled': False, 'hover': False, 'text': text,
                 'color': color, 'command': command}
        canvas._state = state

        def draw():
            canvas.delete('all')
            w = canvas.winfo_width()
            if w < 4: w = 240
            r = 8
            if not state['enabled']:
                bg = self.CARD2
                bd = self.BORDER
                fg = "#4a5568"
            elif state['hover']:
                bg = state['color']
                bd = state['color']
                fg = self.BG
            else:
                # 暗化颜色作为背景
                bg = self._darken(state['color'], 0.55)
                bd = state['color']
                fg = state['color']
            # 背景填充(4圆弧 + 4矩形)
            canvas.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, fill=bg, outline='')
            canvas.create_arc(w-2*r, 0, w, 2*r, start=0, extent=90, fill=bg, outline='')
            canvas.create_arc(0, h-2*r, 2*r, h, start=180, extent=90, fill=bg, outline='')
            canvas.create_arc(w-2*r, h-2*r, w, h, start=270, extent=90, fill=bg, outline='')
            canvas.create_rectangle(r, 0, w-r, h, fill=bg, outline='')
            canvas.create_rectangle(0, r, w, h-r, fill=bg, outline='')
            # 边框(4圆弧 + 4线)
            canvas.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, outline=bd, width=2, style='arc')
            canvas.create_arc(w-2*r, 0, w, 2*r, start=0, extent=90, outline=bd, width=2, style='arc')
            canvas.create_arc(0, h-2*r, 2*r, h, start=180, extent=90, outline=bd, width=2, style='arc')
            canvas.create_arc(w-2*r, h-2*r, w, h, start=270, extent=90, outline=bd, width=2, style='arc')
            canvas.create_line(r, 0, w-r, 0, fill=bd, width=2)
            canvas.create_line(r, h, w-r, h, fill=bd, width=2)
            canvas.create_line(0, r, 0, h-r, fill=bd, width=2)
            canvas.create_line(w, r, w, h-r, fill=bd, width=2)
            # 文字
            canvas.create_text(w//2, h//2, text=state['text'],
                               font=("Microsoft YaHei", 14, "bold"), fill=fg)

        def on_click(_):
            if state['enabled'] and state['command']:
                state['command']()
        def on_enter(_):
            if state['enabled']:
                state['hover'] = True; draw()
        def on_leave(_):
            state['hover'] = False; draw()

        canvas.bind('<Configure>', lambda e: draw())
        canvas.bind('<Button-1>', on_click)
        canvas.bind('<Enter>', on_enter)
        canvas.bind('<Leave>', on_leave)
        draw()
        return canvas, lambda en: (state.update({'enabled': en}), draw())

    def _darken(self, hex_color, factor):
        h = hex_color.lstrip('#')
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        r = max(0, int(r * (1-factor))); g = max(0, int(g * (1-factor))); b = max(0, int(b * (1-factor)))
        return f'#{r:02x}{g:02x}{b:02x}'

    def _status_dot(self, color):
        """创建一个带辉光的状态点"""
        c = tk.Canvas(self.root, width=14, height=14, bg=self.CARD,
                      highlightthickness=0)
        # 外圈晕
        c.create_oval(1, 1, 13, 13, fill=self._darken(color, 0.7), outline='')
        # 内圈
        c.create_oval(3, 3, 11, 11, fill=color, outline='')
        return c

    def setup_ui(self):
        """设置界面 - 游戏霓虹风"""
        # 主容器
        main = tk.Frame(self.root, bg=self.BG)
        main.pack(fill=tk.BOTH, expand=True, padx=22, pady=18)

        # -- 标题区 --
        title_row = tk.Frame(main, bg=self.BG)
        title_row.pack(fill=tk.X, pady=(0, 4))
        # 用 emoji 装饰
        tk.Label(title_row, text="⚡ 迅鲨云联机助手", bg=self.BG, fg=self.ACCENT,
                 font=("Microsoft YaHei", 22, "bold")).pack(side=tk.LEFT)

        # 装饰线
        line = tk.Frame(main, bg=self.BG, height=2)
        line.pack(fill=tk.X, pady=(6, 12))
        # 画渐变装饰线
        deco = tk.Canvas(line, height=2, bg=self.BG, highlightthickness=0)
        deco.pack(fill=tk.X)
        def _draw_line(event=None):
            deco.delete('all')
            w = deco.winfo_width()
            if w < 4: return
            # 左半:青→紫
            for i in range(0, w//2, 2):
                t = i / (w//2)
                r = int((1-t)*0 + t*0xb1)
                g = int((1-t)*0x66 + t*0x6c)
                b = int((1-t)*0x80 + t*0xff)
                deco.create_line(i, 0, i+1, 2, fill=f'#{r:02x}{g:02x}{b:02x}')
            # 右半:紫→青
            for i in range(w//2, w, 2):
                t = (i - w//2) / (w//2)
                r = int((1-t)*0xb1 + t*0x00)
                g = int((1-t)*0x6c + t*0x66)
                b = int((1-t)*0xff + t*0x80)
                deco.create_line(i, 0, i+1, 2, fill=f'#{r:02x}{g:02x}{b:02x}')
        deco.bind('<Configure>', _draw_line)

        # -- 卡片 1: 状态 + 授权 + 机器码 --
        card1 = tk.Frame(main, bg=self.CARD, highlightbackground=self.BORDER,
                         highlightthickness=1)
        card1.pack(fill=tk.X, pady=(0, 12))

        # 状态行
        status_row = tk.Frame(card1, bg=self.CARD)
        status_row.pack(fill=tk.X, padx=18, pady=(14, 6))
        self.status_dot = self._status_dot(self.SUB)
        self.status_dot.pack(side=tk.LEFT, padx=(0, 10), pady=2)
        self.status_text = tk.Label(status_row, text="未启动", bg=self.CARD,
                                     fg=self.SUB, font=("Microsoft YaHei", 12, "bold"))
        self.status_text.pack(side=tk.LEFT)

        # 分隔
        tk.Frame(card1, bg=self.BORDER, height=1).pack(fill=tk.X, padx=18, pady=4)

        # 授权行
        license_row = tk.Frame(card1, bg=self.CARD)
        license_row.pack(fill=tk.X, padx=18, pady=6)
        tk.Label(license_row, text="授权", bg=self.CARD, fg=self.SUB,
                 font=("Microsoft YaHei", 10)).pack(side=tk.LEFT)
        self.license_label = tk.Label(license_row, text="检查中...", bg=self.CARD,
                                       fg=self.WARN, font=("Microsoft YaHei", 11, "bold"))
        self.license_label.pack(side=tk.LEFT, padx=(8, 0))
        self.license_btn = tk.Label(license_row, text="查看", bg=self.CARD2, fg=self.ACCENT,
                                     font=("Microsoft YaHei", 9), padx=12, pady=4,
                                     cursor="hand2")
        self.license_btn.pack(side=tk.RIGHT)
        self.license_btn.bind('<Button-1>', lambda e: self.show_license_info())
        self.license_btn.bind('<Enter>', lambda e: self.license_btn.config(bg=self.ACCENT, fg=self.BG))
        self.license_btn.bind('<Leave>', lambda e: self.license_btn.config(bg=self.CARD2, fg=self.ACCENT))

        # 分隔
        tk.Frame(card1, bg=self.BORDER, height=1).pack(fill=tk.X, padx=18, pady=4)

        # 机器码行
        machine_row = tk.Frame(card1, bg=self.CARD)
        machine_row.pack(fill=tk.X, padx=18, pady=(6, 14))
        tk.Label(machine_row, text="机器码", bg=self.CARD, fg=self.SUB,
                 font=("Microsoft YaHei", 10)).pack(side=tk.LEFT)
        tk.Label(machine_row, text=self.license_mgr.machine_id, bg=self.CARD, fg=self.TEXT,
                 font=("Consolas", 11, "bold")).pack(side=tk.LEFT, padx=(8, 0))
        self.copy_chip = tk.Label(machine_row, text="复制", bg=self.CARD2, fg=self.ACCENT,
                                   font=("Microsoft YaHei", 9), padx=12, pady=4,
                                   cursor="hand2")
        self.copy_chip.pack(side=tk.RIGHT)
        self.copy_chip.bind('<Button-1>', lambda e: self.copy_text(self.license_mgr.machine_id))
        self.copy_chip.bind('<Enter>', lambda e: self.copy_chip.config(bg=self.ACCENT, fg=self.BG))
        self.copy_chip.bind('<Leave>', lambda e: self.copy_chip.config(bg=self.CARD2, fg=self.ACCENT))

        # —— 卡片 2: 加速按钮 ——
        card2 = tk.Frame(main, bg=self.CARD, highlightbackground=self.BORDER,
                         highlightthickness=1)
        card2.pack(fill=tk.X)
        btn_row = tk.Frame(card2, bg=self.CARD)
        btn_row.pack(fill=tk.X, padx=14, pady=18)
        # 等宽两列
        btn_row.columnconfigure(0, weight=1, uniform='btn')
        btn_row.columnconfigure(1, weight=1, uniform='btn')
        self.start_canvas, set_start_en = self._neon_button(btn_row, "⚡ 开始加速", self.OK,
                                                             self.start_network)
        self.start_canvas.grid(row=0, column=0, sticky='nsew', padx=(0, 6))
        self.stop_canvas, set_stop_en = self._neon_button(btn_row, "⏹ 结束加速", self.BAD,
                                                            self.stop_network)
        self.stop_canvas.grid(row=0, column=1, sticky='nsew', padx=(6, 0))
        self.set_start_enabled = set_start_en
        self.set_stop_enabled = set_stop_en

        # -- 底部状态 --
        self.status_chip = tk.Label(self.root, text="  就绪  ", bg=self.CARD, fg=self.SUB,
                                     font=("Microsoft YaHei", 9), padx=14, pady=4)
        self.status_chip.pack(side=tk.BOTTOM, pady=(0, 12))

    def log(self, message):
        """添加日志(现在不显示,只保留接口)"""
        pass

    def _set_status(self, text, color=None):
        """更新底部状态 + 状态点"""
        self.status_chip.config(text=f"  {text}  ", fg=color or self.SUB)

    def _set_status_dot(self, color, text):
        """更新顶部状态指示灯"""
        self.status_dot.delete('all')
        self.status_dot.create_oval(1, 1, 13, 13, fill=self._darken(color, 0.7), outline='')
        self.status_dot.create_oval(3, 3, 11, 11, fill=color, outline='')
        self.status_text.config(text=text, fg=color)

    def copy_text(self, text):
        """复制文本"""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self._set_status(f"已复制: {text}", self.OK)
        self.root.after(2000, lambda: self._set_status("就绪", self.SUB))

    def check_license(self):
        """检查授权"""
        valid, msg, expiry = self.license_mgr.check_license()
        self.update_license_ui(valid, msg)

    def update_license_ui(self, valid, msg):
        """更新授权界面"""
        if valid:
            self.license_label.config(text=msg, foreground=self.OK)
            self.license_btn.unbind('<Button-1>')
            self.license_btn.bind('<Button-1>', lambda e: self.show_license_info())
            self.set_start_enabled(True)
        else:
            self.license_label.config(text=msg, foreground=self.BAD)
            self.license_btn.unbind('<Button-1>')
            self.license_btn.bind('<Button-1>', lambda e: self.show_license_dialog())
            self.set_start_enabled(False)

    def show_license_dialog(self):
        """显示授权对话框(暗色主题)"""
        dialog = tk.Toplevel(self.root)
        dialog.title("输入授权码")
        dialog.update_idletasks()
        w, h = 520, 360
        sw = dialog.winfo_screenwidth()
        sh = dialog.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        dialog.geometry(f"{w}x{h}+{x}+{y}")
        dialog.configure(bg=self.BG)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        # 机器码区域
        tk.Label(dialog, text="你的机器码", bg=self.BG, fg=self.SUB,
                 font=("Microsoft YaHei", 9)).pack(anchor=tk.W, padx=20, pady=(20, 4))
        machine_label = tk.Label(dialog, text=self.license_mgr.machine_id,
                                  font=("Consolas", 13, "bold"),
                                  fg=self.ACCENT, bg=self.CARD,
                                  padx=14, pady=10)
        machine_label.pack(fill=tk.X, padx=20)

        # 复制机器码按钮
        copy_btn = tk.Label(dialog, text=" 复制机器码 ", bg=self.CARD2, fg=self.ACCENT,
                            font=("Microsoft YaHei", 9), padx=12, pady=6,
                            cursor="hand2")
        copy_btn.pack(anchor=tk.W, padx=20, pady=(6, 0))
        copy_btn.bind('<Button-1>', lambda e: self.copy_text(self.license_mgr.machine_id))
        copy_btn.bind('<Enter>', lambda e: copy_btn.config(bg=self.ACCENT, fg=self.BG))
        copy_btn.bind('<Leave>', lambda e: copy_btn.config(bg=self.CARD2, fg=self.ACCENT))

        # 授权码输入
        tk.Label(dialog, text="输入授权码(24位)", bg=self.BG, fg=self.SUB,
                 font=("Microsoft YaHei", 9)).pack(anchor=tk.W, padx=20, pady=(16, 4))
        license_var = tk.StringVar()
        entry_frame = tk.Frame(dialog, bg=self.CARD)
        entry_frame.pack(fill=tk.X, padx=20)
        license_entry = tk.Entry(entry_frame, textvariable=license_var,
                                  font=("Consolas", 13, "bold"),
                                  bg=self.CARD, fg=self.OK,
                                  insertbackground=self.OK,
                                  relief=tk.FLAT, bd=0)
        license_entry.pack(fill=tk.X, padx=4, pady=8)
        license_entry.focus()

        def do_validate():
            key = license_var.get().strip().upper()
            if not key:
                messagebox.showerror("错误", "请输入授权码", parent=dialog)
                return
            valid, expiry = self.license_mgr.validate_license(key)
            if valid:
                days_left = (expiry - datetime.now()).days
                messagebox.showinfo("成功",
                    f"授权成功!\n有效期至: {expiry.strftime('%Y-%m-%d')}\n剩余天数: {days_left} 天",
                    parent=dialog)
                self.update_license_ui(True, f"授权有效 (剩余 {days_left} 天)")
                dialog.destroy()
            else:
                messagebox.showerror("错误",
                    "授权码无效!\n请检查:\n1. 机器码是否正确\n2. 授权码是否完整\n3. 是否过期",
                    parent=dialog)

        # 按钮区域
        btn_frame = tk.Frame(dialog, bg=self.BG)
        btn_frame.pack(fill=tk.X, padx=20, pady=20)
        cancel_btn = tk.Label(btn_frame, text=" 取消 ", bg=self.CARD, fg=self.SUB,
                               font=("Microsoft YaHei", 10), padx=18, pady=8,
                               cursor="hand2")
        cancel_btn.pack(side=tk.RIGHT, padx=(8, 0))
        cancel_btn.bind('<Button-1>', lambda e: dialog.destroy())
        cancel_btn.bind('<Enter>', lambda e: cancel_btn.config(bg=self.CARD2, fg=self.TEXT))
        cancel_btn.bind('<Leave>', lambda e: cancel_btn.config(bg=self.CARD, fg=self.SUB))
        ok_btn = tk.Label(btn_frame, text=" 验证 ", bg=self.OK, fg=self.BG,
                          font=("Microsoft YaHei", 10, "bold"), padx=18, pady=8,
                          cursor="hand2")
        ok_btn.pack(side=tk.RIGHT)
        ok_btn.bind('<Button-1>', lambda e: do_validate())
        ok_btn.bind('<Enter>', lambda e: ok_btn.config(bg=self._darken(self.OK, 0.2)))
        ok_btn.bind('<Leave>', lambda e: ok_btn.config(bg=self.OK))

        license_entry.bind('<Return>', lambda e: do_validate())

    def show_license_info(self):
        """显示授权信息"""
        valid, msg, expiry = self.license_mgr.check_license()
        if valid:
            messagebox.showinfo("授权信息",
                f"授权状态: 有效\n"
                f"有效期至: {expiry.strftime('%Y-%m-%d %H:%M')}\n"
                f"机器码: {self.license_mgr.machine_id}\n\n"
                f"如需延期,请联系管理员获取新的授权码。")

    def start_network(self):
        """开启加速"""
        # 检查 EasyTier — 如果没有，先静默尝试从内置资源释放
        if not self.easytier_mgr.is_installed():
            bundled_dir = self.easytier_mgr._find_bundled_dir()
            if bundled_dir:
                # 有内置资源，静默释放，不弹窗
                self._set_status("首次启动,正在准备 EasyTier...", self.WARN)
                if not self.easytier_mgr._extract_bundled(lambda m: self._set_status(m, self.WARN)):
                    messagebox.showerror("错误", "内置资源安装失败")
                    self._set_status("准备失败", self.BAD)
                    return
            else:
                # 没有内置资源，才询问是否联网下载
                if messagebox.askyesno("安装", "EasyTier 未安装,是否自动下载?"):
                    self._set_status("正在下载 EasyTier...", self.WARN)
                    if not self.easytier_mgr.download(lambda m: self._set_status(m, self.WARN)):
                        messagebox.showerror("错误", "下载失败,请检查网络连接")
                        self._set_status("下载失败", self.BAD)
                        return
                else:
                    return

        # 启动
        self._set_status("正在开启...", self.WARN)
        success, msg = self.easytier_mgr.start(lambda m: None)

        if success:
            self._set_status_dot(self.OK, "加速已开启")
            self._set_status("加速已开启", self.OK)
            self.set_start_enabled(False)
            self.set_stop_enabled(True)
        else:
            self._set_status_dot(self.BAD, "连接失败")
            self._set_status(f"启动失败: {msg}", self.BAD)
            messagebox.showerror("错误", msg)

    def stop_network(self):
        """结束加速"""
        success, msg = self.easytier_mgr.stop()
        if success:
            self._set_status_dot(self.SUB, "未启动")
            self._set_status("加速已结束", self.SUB)
            self.set_start_enabled(True)
            self.set_stop_enabled(False)

    def run(self):
        """运行"""
        self.root.mainloop()

if __name__ == "__main__":
    app = MainApp()
    app.run()
