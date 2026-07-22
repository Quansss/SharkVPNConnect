#!/usr/bin/env python3
"""
Palworld 联机客户端 - 授权码生成器（简化版，纯 tkinter）
"""
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

class LicenseGenerator:
    """授权码生成器"""
    SECRET = "PALWORLD_2024_AUTH"
    
    @classmethod
    def generate(cls, machine_id, days=30):
        """生成授权码"""
        data = f"{machine_id}_{days}_{cls.SECRET}"
        return hashlib.sha256(data.encode()).hexdigest()[:24].upper()

class GeneratorApp:
    """授权码生成器界面"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Palworld 联机客户端 - 授权码生成器")
        self.root.geometry("550x500")
        self.root.resizable(False, False)
        
        self.history = []
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        # 标题
        ttk.Label(self.root, text="授权码生成器", font=("Arial", 16, "bold")).pack(pady=10)
        
        # 机器码输入
        frame1 = ttk.LabelFrame(self.root, text="机器码", padding=10)
        frame1.pack(fill=tk.X, padx=10, pady=5)
        
        self.machine_entry = ttk.Entry(frame1, width=45)
        self.machine_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(frame1, text="粘贴", command=self.paste).pack(side=tk.LEFT, padx=5)
        
        # 授权设置
        frame2 = ttk.LabelFrame(self.root, text="授权设置", padding=10)
        frame2.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(frame2, text="授权天数:").pack(side=tk.LEFT, padx=5)
        
        self.days = ttk.Combobox(frame2, values=[7, 30, 90, 365], width=10)
        self.days.set(30)
        self.days.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(frame2, text="生成授权码", command=self.generate).pack(side=tk.RIGHT, padx=5)
        
        # 结果
        frame3 = ttk.LabelFrame(self.root, text="生成的授权码", padding=10)
        frame3.pack(fill=tk.X, padx=10, pady=5)
        
        self.result = tk.Text(frame3, height=2, wrap=tk.WORD, font=("Consolas", 12))
        self.result.pack(fill=tk.X)
        
        ttk.Button(frame3, text="复制授权码", command=self.copy_result).pack(pady=5)
        
        # 历史记录
        frame4 = ttk.LabelFrame(self.root, text="授权记录", padding=10)
        frame4.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.history_text = scrolledtext.ScrolledText(frame4, height=10)
        self.history_text.pack(fill=tk.BOTH, expand=True)
        
        # 按钮
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(btn_frame, text="导出记录", command=self.export).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="清空记录", command=self.clear).pack(side=tk.LEFT, padx=5)
    
    def paste(self):
        """粘贴"""
        try:
            text = self.root.clipboard_get().strip()
            self.machine_entry.delete(0, tk.END)
            self.machine_entry.insert(0, text)
        except:
            pass
    
    def generate(self):
        """生成"""
        machine_id = self.machine_entry.get().strip()
        
        if not machine_id:
            messagebox.showerror("错误", "请输入机器码")
            return
        
        try:
            days = int(self.days.get())
        except:
            days = 30
        
        # 生成
        license_key = LicenseGenerator.generate(machine_id, days)
        
        # 显示
        self.result.delete(1.0, tk.END)
        self.result.insert(1.0, license_key)
        
        # 添加到历史
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        expiry = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        
        record = f"[{timestamp}] 机器:{machine_id[:12]}... 天数:{days} 到期:{expiry}\n码: {license_key}\n\n"
        self.history_text.insert(tk.END, record)
        self.history_text.see(tk.END)
        
        self.history.append({
            "time": timestamp,
            "machine": machine_id,
            "days": days,
            "expiry": expiry,
            "key": license_key
        })
        
        messagebox.showinfo("成功", f"授权码已生成！\n有效期: {days} 天\n到期: {expiry}")
    
    def copy_result(self):
        """复制结果"""
        text = self.result.get(1.0, tk.END).strip()
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            messagebox.showinfo("提示", "已复制到剪贴板")
    
    def export(self):
        """导出"""
        if not self.history:
            messagebox.showwarning("警告", "没有记录可导出")
            return
        
        filename = f"licenses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = Path.home() / "Desktop" / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)
        
        messagebox.showinfo("成功", f"已导出到桌面:\n{filename}")
    
    def clear(self):
        """清空"""
        if messagebox.askyesno("确认", "确定清空所有记录？"):
            self.history.clear()
            self.history_text.delete(1.0, tk.END)
    
    def run(self):
        """运行"""
        self.root.mainloop()

if __name__ == "__main__":
    app = GeneratorApp()
    app.run()
