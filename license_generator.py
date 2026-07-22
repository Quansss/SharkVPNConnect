#!/usr/bin/env python3
"""
Palworld 联机客户端 - 授权码生成器
"""
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

class LicenseGenerator:
    """授权码生成器"""
    
    SECRET_KEY = "PALWORLD_2024_SECRET_KEY"
    
    @classmethod
    def generate_license(cls, machine_id, days=30):
        """生成授权码"""
        # 创建授权数据
        data = {
            "machine_id": machine_id,
            "days": days,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=days)).isoformat()
        }
        
        # 生成授权码
        license_str = f"{machine_id}_{days}_{cls.SECRET_KEY}"
        license_key = hashlib.sha256(license_str.encode()).hexdigest()[:24].upper()
        
        return {
            "key": license_key,
            "data": data
        }
    
    @classmethod
    def validate_license_format(cls, license_key):
        """验证授权码格式"""
        if not license_key or len(license_key) != 24:
            return False
        return all(c in '0123456789ABCDEF' for c in license_key.upper())

class GeneratorWindow:
    """授权码生成器界面"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Palworld 联机客户端 - 授权码生成器")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        self.generated_licenses = []
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        # 标题
        title = ttk.Label(self.root, text="授权码生成器", font=("Arial", 16, "bold"))
        title.pack(pady=10)
        
        # 机器码输入
        frame1 = ttk.LabelFrame(self.root, text="机器码", padding=10)
        frame1.pack(fill=tk.X, padx=10, pady=5)
        
        self.machine_entry = ttk.Entry(frame1, width=50)
        self.machine_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(frame1, text="粘贴", command=self.paste_machine_id).pack(side=tk.LEFT, padx=5)
        
        # 授权天数
        frame2 = ttk.LabelFrame(self.root, text="授权设置", padding=10)
        frame2.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(frame2, text="授权天数:").pack(side=tk.LEFT, padx=5)
        
        self.days_var = tk.IntVar(value=30)
        days_combo = ttk.Combobox(frame2, textvariable=self.days_var, values=[7, 30, 90, 365], width=10)
        days_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(frame2, text="生成授权码", command=self.generate).pack(side=tk.RIGHT, padx=5)
        
        # 结果显示
        frame3 = ttk.LabelFrame(self.root, text="生成的授权码", padding=10)
        frame3.pack(fill=tk.X, padx=10, pady=5)
        
        self.result_text = tk.Text(frame3, height=3, wrap=tk.WORD)
        self.result_text.pack(fill=tk.X)
        
        ttk.Button(frame3, text="复制授权码", command=self.copy_result).pack(pady=5)
        
        # 历史记录
        frame4 = ttk.LabelFrame(self.root, text="授权记录", padding=10)
        frame4.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.history_text = scrolledtext.ScrolledText(frame4, height=10)
        self.history_text.pack(fill=tk.BOTH, expand=True)
        
        # 按钮
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(btn_frame, text="导出记录", command=self.export_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="清空记录", command=self.clear_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="批量生成", command=self.batch_generate).pack(side=tk.RIGHT, padx=5)
    
    def paste_machine_id(self):
        """从剪贴板粘贴机器码"""
        try:
            machine_id = self.root.clipboard_get().strip()
            self.machine_entry.delete(0, tk.END)
            self.machine_entry.insert(0, machine_id)
        except:
            pass
    
    def generate(self):
        """生成授权码"""
        machine_id = self.machine_entry.get().strip()
        
        if not machine_id:
            messagebox.showerror("错误", "请输入机器码")
            return
        
        if len(machine_id) != 16:
            messagebox.showwarning("警告", "机器码长度应为16位，但将继续生成")
        
        days = self.days_var.get()
        
        # 生成授权码
        result = LicenseGenerator.generate_license(machine_id, days)
        license_key = result["key"]
        
        # 显示结果
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(1.0, license_key)
        
        # 添加到历史
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        expires = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        
        record = {
            "timestamp": timestamp,
            "machine_id": machine_id,
            "days": days,
            "expires": expires,
            "key": license_key
        }
        self.generated_licenses.append(record)
        
        # 更新历史显示
        history_line = f"[{timestamp}] 机器:{machine_id[:8]}... 天数:{days} 到期:{expires} 码:{license_key}\n"
        self.history_text.insert(tk.END, history_line)
        self.history_text.see(tk.END)
        
        messagebox.showinfo("成功", f"授权码已生成！\n有效期: {days} 天\n到期日: {expires}")
    
    def copy_result(self):
        """复制结果"""
        result = self.result_text.get(1.0, tk.END).strip()
        if result:
            self.root.clipboard_clear()
            self.root.clipboard_append(result)
            messagebox.showinfo("提示", "已复制到剪贴板")
    
    def export_history(self):
        """导出历史记录"""
        if not self.generated_licenses:
            messagebox.showwarning("警告", "没有记录可导出")
            return
        
        filename = f"licenses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = Path.home() / "Desktop" / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.generated_licenses, f, indent=2, ensure_ascii=False)
        
        messagebox.showinfo("成功", f"记录已导出到:\n{filepath}")
    
    def clear_history(self):
        """清空历史"""
        if messagebox.askyesno("确认", "确定要清空所有记录吗？"):
            self.generated_licenses.clear()
            self.history_text.delete(1.0, tk.END)
    
    def batch_generate(self):
        """批量生成"""
        dialog = tk.Toplevel(self.root)
        dialog.title("批量生成授权码")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        
        ttk.Label(dialog, text="输入机器码列表（每行一个）:").pack(pady=5)
        
        text = tk.Text(dialog, height=15)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        ttk.Label(dialog, text="授权天数:").pack()
        days_var = tk.IntVar(value=30)
        ttk.Combobox(dialog, textvariable=days_var, values=[7, 30, 90, 365], width=10).pack()
        
        def do_generate():
            machine_ids = [line.strip() for line in text.get(1.0, tk.END).strip().split('\n') if line.strip()]
            
            if not machine_ids:
                messagebox.showerror("错误", "请输入机器码")
                return
            
            days = days_var.get()
            results = []
            
            for machine_id in machine_ids:
                result = LicenseGenerator.generate_license(machine_id, days)
                results.append({
                    "machine_id": machine_id,
                    "key": result["key"],
                    "days": days
                })
            
            # 显示结果
            result_window = tk.Toplevel(dialog)
            result_window.title("批量生成结果")
            result_window.geometry("600x400")
            
            result_text = scrolledtext.ScrolledText(result_window)
            result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            for r in results:
                result_text.insert(tk.END, f"机器: {r['machine_id']}\n授权: {r['key']}\n\n")
            
            # 保存到文件
            filename = f"batch_licenses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = Path.home() / "Desktop" / filename
            with open(filepath, 'w') as f:
                for r in results:
                    f.write(f"{r['machine_id']}\t{r['key']}\n")
            
            ttk.Label(result_window, text=f"已保存到: {filename}").pack(pady=5)
        
        ttk.Button(dialog, text="生成", command=do_generate).pack(pady=10)
    
    def run(self):
        """运行"""
        self.root.mainloop()

if __name__ == "__main__":
    app = GeneratorWindow()
    app.run()
