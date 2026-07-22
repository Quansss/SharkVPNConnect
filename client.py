#!/usr/bin/env python3
"""
Palworld 联机客户端 - 授权版
使用 EasyTier 命令行版本
"""
import os
import sys
import json
import hashlib
import subprocess
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime, timedelta
from pathlib import Path
import requests

# 配置
APP_NAME = "Palworld联机助手"
VERSION = "1.0.0"
NETWORK_CONFIG = {
    "server": "sharkconnect.sharkos.cn:11010",
    "protocol": "tcp",
    "network_name": "palworld",
    "network_secret": "PALWORLD2024SECRET",
    "game_server": "10.144.0.1:8211"
}

class LicenseManager:
    """授权管理器"""
    
    def __init__(self):
        self.license_file = Path(os.environ.get('LOCALAPPDATA', '')) / 'PalworldClient' / 'license.dat'
        self.license_file.parent.mkdir(parents=True, exist_ok=True)
        self.machine_id = self._get_machine_id()
    
    def _get_machine_id(self):
        """获取机器唯一标识"""
        try:
            import wmi
            c = wmi.WMI()
            for cpu in c.Win32_Processor():
                return hashlib.md5(cpu.ProcessorId.encode()).hexdigest()[:16]
        except:
            # 备用方案
            return hashlib.md5(os.environ.get('COMPUTERNAME', 'unknown').encode()).hexdigest()[:16]
    
    def generate_license_request(self):
        """生成授权请求码"""
        data = {
            "machine_id": self.machine_id,
            "timestamp": datetime.now().isoformat(),
            "app_version": VERSION
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:32]
    
    def validate_license(self, license_key):
        """验证授权码"""
        try:
            # 简单的本地验证（实际应该连接服务器验证）
            expected = hashlib.sha256(f"{self.machine_id}_PALWORLD_2024".encode()).hexdigest()[:24]
            if license_key.upper() == expected.upper():
                # 默认授权 30 天
                expiry = datetime.now() + timedelta(days=30)
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
    """EasyTier 管理器"""
    
    def __init__(self):
        self.process = None
        self.easytier_path = Path(os.environ.get('LOCALAPPDATA', '')) / 'PalworldClient' / 'easytier-core.exe'
        self.config_path = Path(os.environ.get('LOCALAPPDATA', '')) / 'PalworldClient' / 'config.json'
    
    def is_installed(self):
        """检查是否已安装"""
        return self.easytier_path.exists()
    
    def download_easytier(self, callback=None):
        """下载 EasyTier"""
        try:
            url = "https://github.com/EasyTier/EasyTier/releases/download/v2.6.4/easytier-windows-x86_64-v2.6.4.zip"
            
            if callback:
                callback("正在下载 EasyTier...")
            
            response = requests.get(url, stream=True, timeout=120)
            response.raise_for_status()
            
            # 保存到临时文件
            temp_zip = Path(os.environ.get('TEMP', '')) / 'easytier.zip'
            with open(temp_zip, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            if callback:
                callback("正在解压...")
            
            # 解压
            import zipfile
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                for file in zip_ref.namelist():
                    if 'easytier-core.exe' in file:
                        with zip_ref.open(file) as src:
                            with open(self.easytier_path, 'wb') as dst:
                                dst.write(src.read())
                        break
            
            # 清理
            temp_zip.unlink()
            
            if callback:
                callback("EasyTier 安装完成")
            
            return True
            
        except Exception as e:
            if callback:
                callback(f"下载失败: {e}")
            return False
    
    def start(self, log_callback=None):
        """启动 EasyTier"""
        try:
            if not self.is_installed():
                return False, "EasyTier 未安装"
            
            # 构建命令行参数
            cmd = [
                str(self.easytier_path),
                "-p", NETWORK_CONFIG["protocol"] + "://" + NETWORK_CONFIG["server"],
                "--network-name", NETWORK_CONFIG["network_name"],
                "--network-secret", NETWORK_CONFIG["network_secret"],
                "--hostname", f"Player-{int(time.time())}",
                "--no-listener"  # 客户端不需要监听
            ]
            
            # 启动进程
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
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
            self.process = None
            return True, "EasyTier 已停止"
        return False, "EasyTier 未运行"
    
    def is_running(self):
        """检查是否在运行"""
        return self.process is not None and self.process.poll() is None

class MainWindow:
    """主窗口"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} v{VERSION}")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        self.license_mgr = LicenseManager()
        self.easytier_mgr = EasyTierManager()
        
        self.setup_ui()
        self.check_license_on_startup()
    
    def setup_ui(self):
        """设置界面"""
        # 授权状态栏
        self.license_frame = ttk.LabelFrame(self.root, text="授权状态", padding=10)
        self.license_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.license_label = ttk.Label(self.license_frame, text="检查中...")
        self.license_label.pack(side=tk.LEFT)
        
        self.license_btn = ttk.Button(self.license_frame, text="输入授权码", command=self.show_license_dialog)
        self.license_btn.pack(side=tk.RIGHT)
        
        # 连接信息
        info_frame = ttk.LabelFrame(self.root, text="连接信息", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        info_text = f"""服务器: {NETWORK_CONFIG['server']}
协议: {NETWORK_CONFIG['protocol'].upper()}
房间名: {NETWORK_CONFIG['network_name']}
房间密码: {NETWORK_CONFIG['network_secret']}
游戏服务器: {NETWORK_CONFIG['game_server']}"""
        
        ttk.Label(info_frame, text=info_text, justify=tk.LEFT).pack(anchor=tk.W)
        
        # 控制按钮
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.start_btn = ttk.Button(btn_frame, text="启动组网", command=self.start_network, state=tk.DISABLED)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="停止组网", command=self.stop_network, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="复制游戏地址", command=self.copy_game_address).pack(side=tk.RIGHT, padx=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(self.root, text="运行日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 状态栏
        self.status_label = ttk.Label(self.root, text="就绪", relief=tk.SUNKEN)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM)
    
    def check_license_on_startup(self):
        """启动时检查授权"""
        valid, msg, expiry = self.license_mgr.check_license()
        self.update_license_ui(valid, msg)
    
    def update_license_ui(self, valid, msg):
        """更新授权界面"""
        if valid:
            self.license_label.config(text=msg, foreground="green")
            self.license_btn.config(text="查看授权", command=self.show_license_info)
            self.start_btn.config(state=tk.NORMAL)
        else:
            self.license_label.config(text=msg, foreground="red")
            self.license_btn.config(text="输入授权码", command=self.show_license_dialog)
            self.start_btn.config(state=tk.DISABLED)
    
    def show_license_dialog(self):
        """显示授权对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("输入授权码")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="机器码:").pack(pady=5)
        machine_id = self.license_mgr.machine_id
        ttk.Entry(dialog, value=machine_id, state="readonly").pack(fill=tk.X, padx=10)
        
        ttk.Button(dialog, text="复制机器码", 
                  command=lambda: self.copy_to_clipboard(machine_id)).pack(pady=5)
        
        ttk.Label(dialog, text="授权码:").pack(pady=5)
        license_entry = ttk.Entry(dialog, width=40)
        license_entry.pack(pady=5)
        
        def do_validate():
            key = license_entry.get().strip()
            if not key:
                messagebox.showerror("错误", "请输入授权码")
                return
            
            valid, expiry = self.license_mgr.validate_license(key)
            if valid:
                messagebox.showinfo("成功", f"授权成功！有效期至: {expiry.strftime('%Y-%m-%d')}")
                self.update_license_ui(True, f"授权有效 (剩余 30 天)")
                dialog.destroy()
            else:
                messagebox.showerror("错误", "授权码无效")
        
        ttk.Button(dialog, text="验证", command=do_validate).pack(pady=10)
    
    def show_license_info(self):
        """显示授权信息"""
        valid, msg, expiry = self.license_mgr.check_license()
        if valid:
            messagebox.showinfo("授权信息", 
                f"授权状态: 有效\n"
                f"有效期至: {expiry.strftime('%Y-%m-%d %H:%M')}\n"
                f"机器码: {self.license_mgr.machine_id}")
    
    def copy_to_clipboard(self, text):
        """复制到剪贴板"""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("提示", "已复制到剪贴板")
    
    def copy_game_address(self):
        """复制游戏地址"""
        self.copy_to_clipboard(NETWORK_CONFIG['game_server'])
    
    def log(self, message):
        """添加日志"""
        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def start_network(self):
        """启动组网"""
        # 检查 EasyTier 是否安装
        if not self.easytier_mgr.is_installed():
            if messagebox.askyesno("安装", "EasyTier 未安装，是否自动下载？"):
                self.log("正在下载 EasyTier...")
                if not self.easytier_mgr.download_easytier(lambda m: self.log(m)):
                    messagebox.showerror("错误", "下载失败，请检查网络")
                    return
            else:
                return
        
        # 启动
        success, msg = self.easytier_mgr.start(lambda m: self.log(m))
        if success:
            self.status_label.config(text="组网运行中")
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.log("组网已启动，等待连接...")
            self.log(f"游戏服务器: {NETWORK_CONFIG['game_server']}")
        else:
            messagebox.showerror("错误", msg)
    
    def stop_network(self):
        """停止组网"""
        success, msg = self.easytier_mgr.stop()
        if success:
            self.status_label.config(text="就绪")
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.log("组网已停止")
    
    def run(self):
        """运行应用"""
        self.root.mainloop()

if __name__ == "__main__":
    app = MainWindow()
    app.run()
