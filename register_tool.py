#!/usr/bin/env python3
"""迅鲨云联机助手 - 注册机（简洁版）"""
import os
import hashlib
import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timedelta

SECRET = "PALWORLD_2024_AUTH"

def get_local_machine_code():
    try:
        import platform
        data = f"{platform.machine()}_{platform.processor()}_{platform.node()}"
        return hashlib.md5(data.encode()).hexdigest()[:16].upper()
    except Exception:
        return hashlib.md5(os.environ.get("COMPUTERNAME", "UNKNOWN").encode()).hexdigest()[:16].upper()

def make_license(machine_id, days):
    data = f"{machine_id}_{days}_{SECRET}"
    return hashlib.sha256(data.encode()).hexdigest()[:24].upper()

class RegisterTool:
    def __init__(self, root):
        self.root = root
        root.title("授权码生成器")
        root.geometry("720x820")
        root.resizable(False, False)
        self.mode = "days"
        self.record_file = os.path.join(
            os.path.dirname(__file__) if "__file__" in dir() else os.getcwd(),
            "register_records.txt"
        )
        self.build_ui()
        self.load_records()

    def build_ui(self):
        tk.Label(self.root, text="授权码生成器", font=("Microsoft YaHei", 16, "bold")).pack(pady=(15, 10))

        # 机器码区
        mf = tk.LabelFrame(self.root, text="机器码", font=("Microsoft YaHei", 10), padx=10, pady=8)
        mf.pack(fill="x", padx=15, pady=5)
        mif = tk.Frame(mf)
        mif.pack(fill="x")
        self.machine_var = tk.StringVar()
        self.machine_entry = tk.Entry(mif, textvariable=self.machine_var, font=("Consolas", 12), width=50)
        self.machine_entry.pack(side="left", padx=(0, 10), ipady=3)
        self.machine_entry.focus()
        tk.Button(mif, text="粘贴", font=("Microsoft YaHei", 10), width=10, command=self.paste_machine).pack(side="left")

        # 授权设置区
        sf = tk.LabelFrame(self.root, text="授权设置", font=("Microsoft YaHei", 10), padx=10, pady=8)
        sf.pack(fill="x", padx=15, pady=5)

        # 模式切换
        mfb = tk.Frame(sf)
        mfb.pack(fill="x", pady=(0, 6))
        tk.Label(mfb, text="授权方式:", font=("Microsoft YaHei", 10)).pack(side="left")
        self.btn_days = tk.Button(mfb, text="按天数", font=("Microsoft YaHei", 10), width=10,
                                  command=lambda: self.switch_mode("days"))
        self.btn_days.pack(side="left", padx=(5, 5))
        self.btn_date = tk.Button(mfb, text="按到期日", font=("Microsoft YaHei", 10), width=10,
                                  command=lambda: self.switch_mode("date"))
        self.btn_date.pack(side="left")

        # 按天数
        self.days_row = tk.Frame(sf)
        self.days_row.pack(fill="x")
        tk.Label(self.days_row, text="授权天数:", font=("Microsoft YaHei", 10)).pack(side="left")
        self.days_var = tk.StringVar(value="30")
        self.days_entry = tk.Entry(self.days_row, textvariable=self.days_var, font=("Microsoft YaHei", 10), width=12)
        self.days_entry.pack(side="left", padx=(5, 5), ipady=2)
        for d in [7, 30, 90, 180, 365]:
            tk.Button(self.days_row, text=f"{d}天", font=("Microsoft YaHei", 9), width=5,
                      command=lambda v=d: self.set_days(v)).pack(side="left", padx=2)

        # 按到期日
        self.date_row = tk.Frame(sf)
        tk.Label(self.date_row, text="到期日期:", font=("Microsoft YaHei", 10)).pack(side="left")
        self.date_var = tk.StringVar()
        self.date_entry = tk.Entry(self.date_row, textvariable=self.date_var, font=("Microsoft YaHei", 10), width=14)
        self.date_entry.pack(side="left", padx=(5, 5), ipady=2)
        tk.Label(self.date_row, text="格式: YYYY-MM-DD", font=("Microsoft YaHei", 9), fg="gray").pack(side="left", padx=(5, 0))

        gen_btn = tk.Button(sf, text="生成授权码", font=("Microsoft YaHei", 10, "bold"), width=15, command=self.generate)
        gen_btn.pack(side="right", pady=(6, 0))
        self.switch_mode("days")

        # 授权码显示
        rf = tk.LabelFrame(self.root, text="生成的授权码", font=("Microsoft YaHei", 10), padx=10, pady=8)
        rf.pack(fill="x", padx=15, pady=5)
        self.result_text = tk.Text(rf, font=("Consolas", 12), height=2, wrap="word", state="disabled", bg="#f5f5f5")
        self.result_text.pack(fill="x", ipady=3)
        tk.Button(rf, text="复制授权码", font=("Microsoft YaHei", 10), width=15, command=self.copy_result).pack(pady=(5, 0))

        # 授权记录
        recf = tk.LabelFrame(self.root, text="授权记录", font=("Microsoft YaHei", 10), padx=10, pady=8)
        recf.pack(fill="both", expand=True, padx=15, pady=5)
        ri = tk.Frame(recf)
        ri.pack(fill="both", expand=True)
        sb = tk.Scrollbar(ri)
        sb.pack(side="right", fill="y")
        self.record_text = tk.Text(ri, font=("Consolas", 10), wrap="none", state="disabled", yscrollcommand=sb.set)
        self.record_text.pack(side="left", fill="both", expand=True)
        sb.config(command=self.record_text.yview)

        # 底部
        bf = tk.Frame(self.root)
        bf.pack(pady=10)
        tk.Button(bf, text="清空记录", font=("Microsoft YaHei", 10), width=12, command=self.clear_records).pack(side="left", padx=5)
        tk.Button(bf, text="刷新记录", font=("Microsoft YaHei", 10), width=12, command=self.load_records).pack(side="left", padx=5)

    def switch_mode(self, mode):
        self.mode = mode
        if mode == "days":
            self.btn_days.config(relief="sunken", bg="#d0d0d0")
            self.btn_date.config(relief="raised", bg="SystemButtonFace")
            self.days_row.pack(fill="x", pady=(6, 0))
            self.date_row.pack_forget()
        else:
            self.btn_days.config(relief="raised", bg="SystemButtonFace")
            self.btn_date.config(relief="sunken", bg="#d0d0d0")
            self.days_row.pack_forget()
            self.date_row.pack(fill="x", pady=(6, 0))
            self.date_entry.focus()

    def set_days(self, d):
        self.days_var.set(str(d))

    def paste_machine(self):
        try:
            content = self.root.clipboard_get().strip().upper()
            self.machine_var.set(content)
        except tk.TclError:
            messagebox.showwarning("提示", "剪贴板为空")

    def generate(self):
        mid = self.machine_var.get().strip().upper()
        if len(mid) != 16 or not all(c in "0123456789ABCDEF" for c in mid):
            messagebox.showwarning("机器码无效", "请输入 16 位 0-9 / A-F 字符的机器码")
            return
        if self.mode == "days":
            d_str = self.days_var.get().strip()
            if not d_str.isdigit() or int(d_str) <= 0:
                messagebox.showwarning("输入无效", "请输入正整数天数")
                return
            days = int(d_str)
            exp = datetime.now() + timedelta(days=days)
        else:
            ds = self.date_var.get().strip()
            try:
                exp = datetime.strptime(ds, "%Y-%m-%d")
            except ValueError:
                messagebox.showwarning("日期格式错误", "请使用 YYYY-MM-DD 格式，例如：2026-12-31")
                return
            delta = exp - datetime.now()
            days = delta.days + 1
            if days <= 0:
                messagebox.showwarning("日期无效", "到期日不能早于今天")
                return
        code = make_license(mid, days)
        exp_str = exp.strftime("%Y-%m-%d")
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", code)
        self.result_text.config(state="disabled")
        mode_str = "按天数" if self.mode == "days" else "按到期日"
        record = (f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 机器码: {mid}  {mode_str}: {days}天  到期: {exp_str}\n  授权码: {code}\n")
        self.append_record(record)

    def copy_result(self):
        code = self.result_text.get("1.0", "end").strip()
        if not code:
            messagebox.showwarning("提示", "请先生成授权码")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(code)
        self.root.update()
        messagebox.showinfo("已复制", "授权码已复制到剪贴板")

    def append_record(self, record):
        with open(self.record_file, "a", encoding="utf-8") as f:
            f.write(record)
        self.load_records()

    def load_records(self):
        if not os.path.exists(self.record_file):
            return
        self.record_text.config(state="normal")
        self.record_text.delete("1.0", "end")
        try:
            with open(self.record_file, "r", encoding="utf-8") as f:
                self.record_text.insert("1.0", f.read())
        except Exception as e:
            self.record_text.insert("1.0", f"读取记录失败: {e}")
        self.record_text.config(state="disabled")

    def clear_records(self):
        if not os.path.exists(self.record_file):
            messagebox.showinfo("提示", "没有记录")
            return
        if messagebox.askyesno("确认", "确定要清空所有授权记录吗？"):
            os.remove(self.record_file)
            self.record_text.config(state="normal")
            self.record_text.delete("1.0", "end")
            self.record_text.config(state="disabled")
            messagebox.showinfo("完成", "记录已清空")

def main():
    root = tk.Tk()
    RegisterTool(root)
    root.mainloop()

if __name__ == "__main__":
    main()
