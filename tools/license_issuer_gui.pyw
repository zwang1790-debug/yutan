"""Small local Windows GUI for issuing seller licenses."""
from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

if getattr(sys, "frozen", False):
    # In a packaged seller tool, keep the private key beside the executable.
    ROOT = Path(sys.executable).resolve().parent
else:
    ROOT = Path(__file__).resolve().parent.parent
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

from tools.license_issuer_core import (
    SUPPORTED_PLANS,
    default_days_for_plan,
    format_timestamp,
    issue_license,
)

VERSION = "2.1.1"


class LicenseIssuerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("鱼探 Radar · 授权码签发工具")
        self.root.geometry("760x620")
        self.root.minsize(700, 560)
        self.root.configure(bg="#eef5f8")
        self.code_var = tk.StringVar()
        self.device_var = tk.StringVar()
        self.key_var = tk.StringVar(value=str(ROOT / "license-keys" / "private.key"))
        self.plan_var = tk.StringVar(value="personal_annual")
        self.days_var = tk.StringVar(value=str(default_days_for_plan(self.plan_var.get())))
        self.version_var = tk.StringVar(value=VERSION)
        self._build()

    def _build(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("vista")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("Microsoft YaHei UI", 18, "bold"), foreground="#123b57")
        style.configure("Hint.TLabel", foreground="#557084")
        frame = ttk.Frame(self.root, padding=24)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="鱼探 Radar 授权码签发", style="Title.TLabel").pack(anchor="w")
        ttk.Label(frame, text="仅供卖家本机使用。私钥不会写入客户安装包。", style="Hint.TLabel").pack(anchor="w", pady=(4, 18))

        form = ttk.LabelFrame(frame, text="授权信息", padding=14)
        form.pack(fill="x")
        self._row(form, 0, "客户设备指纹", ttk.Entry(form, textvariable=self.device_var, width=58))
        plan = ttk.Combobox(form, textvariable=self.plan_var, state="readonly", width=42, values=list(SUPPORTED_PLANS))
        plan.bind("<<ComboboxSelected>>", self._on_plan_changed)
        self._row(form, 1, "授权套餐", plan)
        self._row(form, 2, "有效期（天）", ttk.Entry(form, textvariable=self.days_var, width=18))
        self._row(form, 3, "软件版本", ttk.Entry(form, textvariable=self.version_var, width=18))
        key_entry = ttk.Entry(form, textvariable=self.key_var, width=58)
        self._row(form, 4, "卖家私钥文件", key_entry, browse=True)

        ttk.Label(frame, text="套餐 ID：personal_monthly / personal_launch / personal_annual；professional_annual 暂不建议销售。", style="Hint.TLabel", wraplength=700).pack(anchor="w", pady=(10, 10))
        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=(4, 12))
        ttk.Button(buttons, text="生成授权码", command=self.generate).pack(side="left")
        ttk.Button(buttons, text="复制授权码", command=self.copy_code).pack(side="left", padx=8)
        ttk.Button(buttons, text="保存授权码", command=self.save_code).pack(side="left")
        ttk.Button(buttons, text="清空", command=self.clear).pack(side="right")

        output = ttk.LabelFrame(frame, text="生成结果", padding=12)
        output.pack(fill="both", expand=True)
        self.output = tk.Text(output, height=10, wrap="word", font=("Consolas", 10), relief="solid", borderwidth=1)
        self.output.pack(fill="both", expand=True)
        self.output.configure(state="disabled")
        ttk.Label(frame, text="提示：授权码只发给对应客户；建议同时记录订单号、设备指纹、授权 ID 和到期时间。", style="Hint.TLabel", wraplength=700).pack(anchor="w", pady=(10, 0))

    def _on_plan_changed(self, _event: tk.Event | None = None) -> None:
        self.days_var.set(str(default_days_for_plan(self.plan_var.get())))

    def _row(self, parent: ttk.Frame, row: int, label: str, widget: tk.Widget, browse: bool = False) -> None:
        ttk.Label(parent, text=label, width=16).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=5)
        widget.grid(row=row, column=1, sticky="ew", pady=5)
        if browse:
            ttk.Button(parent, text="选择...", command=self.choose_key).grid(row=row, column=2, padx=(8, 0), pady=5)
        parent.columnconfigure(1, weight=1)

    def choose_key(self) -> None:
        path = filedialog.askopenfilename(title="选择卖家私钥", filetypes=[("Key files", "*.key"), ("All files", "*.*")])
        if path:
            self.key_var.set(path)

    def generate(self) -> None:
        key_path = self.key_var.get().strip()
        if not key_path or not Path(key_path).is_file():
            messagebox.showerror(
                "无法生成授权码",
                "找不到卖家私钥文件。请确认 license-keys\\private.key 存在，或点击“选择...”指定 private.key 文件。",
                parent=self.root,
            )
            return
        try:
            code, payload = issue_license(
                device_hash=self.device_var.get(),
                plan=self.plan_var.get(),
                days=int(self.days_var.get().strip()),
                version=self.version_var.get(),
                private_key_path=key_path,
            )
        except (ValueError, OSError) as exc:
            messagebox.showerror("无法生成授权码", str(exc), parent=self.root)
            return
        result = (
            f"授权 ID：{payload['license_id']}\n"
            f"套餐：{SUPPORTED_PLANS[payload['plan']]} ({payload['plan']})\n"
            f"设备指纹：{payload['device_hash']}\n"
            f"签发时间：{format_timestamp(payload['issued_at'])}\n"
            f"到期时间：{format_timestamp(payload['expires_at'])}\n\n"
            f"{code}"
        )
        self.code_var.set(code)
        self.output.configure(state="normal")
        self.output.delete("1.0", tk.END)
        self.output.insert("1.0", result)
        self.output.configure(state="disabled")
        self.root.clipboard_clear()
        self.root.clipboard_append(code)
        messagebox.showinfo("生成成功", "授权码已生成，并已复制到剪贴板。", parent=self.root)

    def copy_code(self) -> None:
        if not self.code_var.get():
            messagebox.showwarning("没有授权码", "请先生成授权码。", parent=self.root)
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(self.code_var.get())
        messagebox.showinfo("已复制", "授权码已复制到剪贴板。", parent=self.root)

    def save_code(self) -> None:
        if not self.code_var.get():
            messagebox.showwarning("没有授权码", "请先生成授权码。", parent=self.root)
            return
        path = filedialog.asksaveasfilename(title="保存授权码", defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if path:
            try:
                Path(path).write_text(self.code_var.get() + "\n", encoding="utf-8")
            except OSError as exc:
                messagebox.showerror("保存失败", f"无法保存授权码：\n{exc}", parent=self.root)
                return
            messagebox.showinfo("保存成功", f"授权码已保存到：\n{path}", parent=self.root)

    def clear(self) -> None:
        self.code_var.set("")
        self.output.configure(state="normal")
        self.output.delete("1.0", tk.END)
        self.output.configure(state="disabled")


if __name__ == "__main__":
    app_root = tk.Tk()
    LicenseIssuerApp(app_root)
    app_root.mainloop()
