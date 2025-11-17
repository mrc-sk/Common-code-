#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
银行管理系统 - 图形化完整版
支持搜索用户、图形化界面、密码验证等功能
"""

import os
import json
import uuid
import qrcode
import zlib
import pickle
import sqlite3
import psutil
import hashlib
import getpass
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from PIL import Image, ImageTk
import requests


class BankManagementGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("银行管理系统")
        self.root.geometry("1000x700")

        # 初始化银行系统
        self.bank_system = SecureBankManagementSystem()
        self.current_user = None

        self.setup_gui()

    def setup_gui(self):
        """设置图形界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 标题
        title_label = ttk.Label(main_frame, text="银行管理系统",
                                font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)

        # 创建选项卡
        tab_control = ttk.Notebook(main_frame)

        # 添加用户选项卡
        self.add_user_tab = ttk.Frame(tab_control)
        tab_control.add(self.add_user_tab, text="添加用户")

        # 搜索用户选项卡
        self.search_tab = ttk.Frame(tab_control)
        tab_control.add(self.search_tab, text="搜索用户")

        # 用户操作选项卡
        self.user_ops_tab = ttk.Frame(tab_control)
        tab_control.add(self.user_ops_tab, text="用户操作")

        tab_control.grid(row=1, column=0, columnspan=3,
                         sticky=(tk.W, tk.E, tk.N, tk.S))

        # 设置各选项卡内容
        self.setup_add_user_tab()
        self.setup_search_tab()
        self.setup_user_ops_tab()

        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(
            main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E))

    def setup_add_user_tab(self):
        """设置添加用户选项卡"""
        frame = ttk.Frame(self.add_user_tab, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 用户信息输入字段
        fields = [
            ("姓名", "name"),
            ("身份证号", "id_card"),
            ("手机号", "phone"),
            ("邮箱", "email"),
            ("地址", "address"),
            ("账户类型", "account_type"),
            ("初始余额", "balance")
        ]

        self.entry_vars = {}
        for i, (label, field) in enumerate(fields):
            ttk.Label(frame, text=label + ":").grid(row=i,
                                                    column=0, sticky=tk.W, pady=5)

            if field == "account_type":
                var = tk.StringVar(value="储蓄账户")
                combobox = ttk.Combobox(frame, textvariable=var,
                                        values=["储蓄账户", "支票账户", "信用卡账户", "贷款账户"])
                combobox.grid(row=i, column=1, sticky=(
                    tk.W, tk.E), pady=5, padx=5)
            else:
                var = tk.StringVar()
                entry = ttk.Entry(frame, textvariable=var, width=30)
                entry.grid(row=i, column=1, sticky=(
                    tk.W, tk.E), pady=5, padx=5)

            self.entry_vars[field] = var

        # 按钮框架
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="添加用户",
                   command=self.add_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清空表单",
                   command=self.clear_form).pack(side=tk.LEFT, padx=5)

        # 结果显示
        self.result_text = tk.Text(frame, height=8, width=60)
        self.result_text.grid(row=len(fields)+1, column=0,
                              columnspan=2, pady=10)

        # 二维码显示区域
        self.qr_label = ttk.Label(frame, text="二维码将在这里显示")
        self.qr_label.grid(row=len(fields)+2, column=0, columnspan=2, pady=10)

    def setup_search_tab(self):
        """设置搜索用户选项卡"""
        frame = ttk.Frame(self.search_tab, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 搜索条件
        search_frame = ttk.Frame(frame)
        search_frame.grid(row=0, column=0, columnspan=2,
                          sticky=(tk.W, tk.E), pady=10)

        ttk.Label(search_frame, text="搜索条件:").grid(
            row=0, column=0, sticky=tk.W)

        self.search_type = tk.StringVar(value="user_id")
        ttk.Radiobutton(search_frame, text="用户ID", variable=self.search_type,
                        value="user_id").grid(row=0, column=1, sticky=tk.W)
        ttk.Radiobutton(search_frame, text="姓名", variable=self.search_type,
                        value="name").grid(row=0, column=2, sticky=tk.W)
        ttk.Radiobutton(search_frame, text="身份证", variable=self.search_type,
                        value="id_card").grid(row=0, column=3, sticky=tk.W)

        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.grid(
            row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)

        ttk.Button(search_frame, text="搜索",
                   command=self.search_users).grid(row=1, column=4, padx=5)

        # 搜索结果表格
        columns = ("用户ID", "姓名", "身份证", "手机号", "账户类型", "余额", "状态")
        self.search_tree = ttk.Treeview(
            frame, columns=columns, show="headings", height=15)

        # 设置列标题
        for col in columns:
            self.search_tree.heading(col, text=col)
            self.search_tree.column(col, width=100)

        self.search_tree.grid(row=1, column=0, columnspan=2,
                              sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)

        # 滚动条
        scrollbar = ttk.Scrollbar(
            frame, orient=tk.VERTICAL, command=self.search_tree.yview)
        scrollbar.grid(row=1, column=2, sticky=(tk.N, tk.S))
        self.search_tree.configure(yscrollcommand=scrollbar.set)

        # 双击查看详情
        self.search_tree.bind("<Double-1>", self.on_user_double_click)

    def setup_user_ops_tab(self):
        """设置用户操作选项卡"""
        frame = ttk.Frame(self.user_ops_tab, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 用户认证区域
        auth_frame = ttk.LabelFrame(frame, text="用户认证", padding="10")
        auth_frame.grid(row=0, column=0, columnspan=2,
                        sticky=(tk.W, tk.E), pady=10)

        ttk.Label(auth_frame, text="用户ID:").grid(row=0, column=0, sticky=tk.W)
        self.auth_user_id = tk.StringVar()
        ttk.Entry(auth_frame, textvariable=self.auth_user_id,
                  width=20).grid(row=0, column=1, padx=5)

        ttk.Button(auth_frame, text="登录",
                   command=self.user_login).grid(row=0, column=2, padx=5)
        ttk.Button(auth_frame, text="设置密码",
                   command=self.set_password).grid(row=0, column=3, padx=5)
        ttk.Button(auth_frame, text="退出登录",
                   command=self.user_logout).grid(row=0, column=4, padx=5)

        # 用户信息显示
        self.user_info_text = tk.Text(
            frame, height=10, width=60, state=tk.DISABLED)
        self.user_info_text.grid(
            row=1, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))

        # 操作按钮
        ops_frame = ttk.Frame(frame)
        ops_frame.grid(row=2, column=0, columnspan=2, pady=10)

        ttk.Button(ops_frame, text="查看余额",
                   command=self.show_balance, state=tk.DISABLED).pack(side=tk.LEFT, padx=5)
        ttk.Button(ops_frame, text="存款",
                   command=self.deposit, state=tk.DISABLED).pack(side=tk.LEFT, padx=5)
        ttk.Button(ops_frame, text="取款",
                   command=self.withdraw, state=tk.DISABLED).pack(side=tk.LEFT, padx=5)
        ttk.Button(ops_frame, text="转账",
                   command=self.transfer, state=tk.DISABLED).pack(side=tk.LEFT, padx=5)
        ttk.Button(ops_frame, text="交易记录",
                   command=self.show_transactions, state=tk.DISABLED).pack(side=tk.LEFT, padx=5)

        self.ops_buttons = ops_frame.winfo_children()

    def add_user(self):
        """添加用户"""
        user_data = {}
        for field, var in self.entry_vars.items():
            user_data[field] = var.get().strip()

        # 验证必要字段
        if not user_data['name'] or not user_data['id_card']:
            messagebox.showerror("错误", "姓名和身份证号为必填项")
            return

        try:
            result = self.bank_system.add_user(user_data)

            if result['success']:
                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(tk.END, f"用户添加成功！\n")
                self.result_text.insert(tk.END, f"用户ID: {result['user_id']}\n")
                self.result_text.insert(
                    tk.END, f"二维码路径: {result['qr_code_path']}\n")

                # 显示二维码
                self.display_qr_code(result['qr_code_path'])

                self.status_var.set("用户添加成功")
                messagebox.showinfo("成功", "用户添加成功！")
            else:
                messagebox.showerror("错误", result['message'])
                self.status_var.set(f"添加失败: {result['message']}")

        except Exception as e:
            messagebox.showerror("错误", f"添加用户时发生异常: {str(e)}")
            self.status_var.set(f"添加异常: {str(e)}")

    def display_qr_code(self, qr_path):
        """显示二维码"""
        try:
            image = Image.open(qr_path)
            image = image.resize((200, 200), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            self.qr_label.configure(image=photo)
            self.qr_label.image = photo  # 保持引用
        except Exception as e:
            self.qr_label.configure(text=f"无法显示二维码: {str(e)}")

    def clear_form(self):
        """清空表单"""
        for var in self.entry_vars.values():
            var.set("")
        self.entry_vars['account_type'].set("储蓄账户")
        self.result_text.delete(1.0, tk.END)
        self.qr_label.configure(image='', text="二维码将在这里显示")
        self.status_var.set("表单已清空")

    def search_users(self):
        """搜索用户"""
        search_type = self.search_type.get()
        search_value = self.search_entry.get().strip()

        if not search_value:
            messagebox.showwarning("警告", "请输入搜索条件")
            return

        try:
            results = self.bank_system.search_users(search_type, search_value)

            # 清空现有结果
            for item in self.search_tree.get_children():
                self.search_tree.delete(item)

            # 添加新结果
            for user in results:
                self.search_tree.insert("", tk.END, values=(
                    user['user_id'],
                    user['name'],
                    user['id_card'],
                    user.get('phone', ''),
                    self.bank_system._expand_account_type(
                        user.get('account_type', 'SAV')),
                    f"{user.get('balance', 0)/100:.2f}",
                    "活跃" if user.get('status') == 'A' else "冻结"
                ))

            self.status_var.set(f"找到 {len(results)} 个用户")

        except Exception as e:
            messagebox.showerror("错误", f"搜索用户时发生异常: {str(e)}")
            self.status_var.set(f"搜索异常: {str(e)}")

    def on_user_double_click(self, event):
        """双击用户行查看详情"""
        selection = self.search_tree.selection()
        if selection:
            item = selection[0]
            user_id = self.search_tree.item(item, 'values')[0]
            self.auth_user_id.set(user_id)
            self.status_var.set(f"已选择用户: {user_id}")

    def user_login(self):
        """用户登录"""
        user_id = self.auth_user_id.get().strip()
        if not user_id:
            messagebox.showwarning("警告", "请输入用户ID")
            return

        try:
            if self.bank_system.authenticate_user(user_id):
                self.current_user = user_id
                self.update_user_info()
                self.set_ops_buttons_state(tk.NORMAL)
                self.status_var.set(f"用户 {user_id} 登录成功")
                messagebox.showinfo("成功", "登录成功！")
            else:
                self.status_var.set("登录失败")
        except Exception as e:
            messagebox.showerror("错误", f"登录时发生异常: {str(e)}")
            self.status_var.set(f"登录异常: {str(e)}")

    def set_password(self):
        """设置密码"""
        user_id = self.auth_user_id.get().strip()
        if not user_id:
            messagebox.showwarning("警告", "请输入用户ID")
            return

        try:
            if self.bank_system.set_user_password(user_id):
                self.status_var.set("密码设置成功")
                messagebox.showinfo("成功", "密码设置成功！")
            else:
                self.status_var.set("密码设置失败")
        except Exception as e:
            messagebox.showerror("错误", f"设置密码时发生异常: {str(e)}")
            self.status_var.set(f"设置密码异常: {str(e)}")

    def user_logout(self):
        """用户退出登录"""
        self.current_user = None
        self.user_info_text.config(state=tk.NORMAL)
        self.user_info_text.delete(1.0, tk.END)
        self.user_info_text.config(state=tk.DISABLED)
        self.set_ops_buttons_state(tk.DISABLED)
        self.status_var.set("已退出登录")

    def set_ops_buttons_state(self, state):
        """设置操作按钮状态"""
        for button in self.ops_buttons:
            button.configure(state=state)

    def update_user_info(self):
        """更新用户信息显示"""
        if not self.current_user:
            return

        try:
            user_info = self.bank_system.get_user_info(self.current_user)
            if user_info:
                self.user_info_text.config(state=tk.NORMAL)
                self.user_info_text.delete(1.0, tk.END)

                info_str = f"用户ID: {user_info['user_id']}\n"
                info_str += f"姓名: {user_info['name']}\n"
                info_str += f"身份证: {user_info['id_card']}\n"
                info_str += f"手机: {user_info.get('phone', '')}\n"
                info_str += f"邮箱: {user_info.get('email', '')}\n"
                info_str += f"地址: {user_info.get('address', '')}\n"
                info_str += f"账户类型: {self.bank_system._expand_account_type(user_info.get('account_type', 'SAV'))}\n"
                info_str += f"余额: {user_info.get('balance', 0)/100:.2f} 元\n"
                info_str += f"状态: {'活跃' if user_info.get('status') == 'A' else '冻结'}\n"
                info_str += f"开户时间: {datetime.fromtimestamp(user_info.get('created_time', 0)).strftime('%Y-%m-%d %H:%M:%S')}"

                self.user_info_text.insert(tk.END, info_str)
                self.user_info_text.config(state=tk.DISABLED)

        except Exception as e:
            messagebox.showerror("错误", f"获取用户信息时发生异常: {str(e)}")

    def show_balance(self):
        """显示余额"""
        if not self.current_user:
            return

        try:
            balance = self.bank_system.get_balance(self.current_user)
            messagebox.showinfo("余额", f"当前余额: {balance/100:.2f} 元")
        except Exception as e:
            messagebox.showerror("错误", f"获取余额时发生异常: {str(e)}")

    def deposit(self):
        """存款"""
        if not self.current_user:
            return

        amount = simpledialog.askfloat("存款", "请输入存款金额:")
        if amount and amount > 0:
            try:
                if self.bank_system.deposit(self.current_user, amount):
                    messagebox.showinfo("成功", f"存款 {amount:.2f} 元成功")
                    self.update_user_info()
                else:
                    messagebox.showerror("错误", "存款失败")
            except Exception as e:
                messagebox.showerror("错误", f"存款时发生异常: {str(e)}")

    def withdraw(self):
        """取款"""
        if not self.current_user:
            return

        amount = simpledialog.askfloat("取款", "请输入取款金额:")
        if amount and amount > 0:
            try:
                if self.bank_system.withdraw(self.current_user, amount):
                    messagebox.showinfo("成功", f"取款 {amount:.2f} 元成功")
                    self.update_user_info()
                else:
                    messagebox.showerror("错误", "取款失败，余额不足或其他错误")
            except Exception as e:
                messagebox.showerror("错误", f"取款时发生异常: {str(e)}")

    def transfer(self):
        """转账"""
        if not self.current_user:
            return

        target_user = simpledialog.askstring("转账", "请输入目标用户ID:")
        if not target_user:
            return

        amount = simpledialog.askfloat("转账", "请输入转账金额:")
        if amount and amount > 0:
            try:
                if self.bank_system.transfer(self.current_user, target_user, amount):
                    messagebox.showinfo(
                        "成功", f"向 {target_user} 转账 {amount:.2f} 元成功")
                    self.update_user_info()
                else:
                    messagebox.showerror("错误", "转账失败，余额不足或目标用户不存在")
            except Exception as e:
                messagebox.showerror("错误", f"转账时发生异常: {str(e)}")

    def show_transactions(self):
        """显示交易记录"""
        if not self.current_user:
            return

        try:
            transactions = self.bank_system.get_transactions(self.current_user)

            # 创建交易记录窗口
            trans_window = tk.Toplevel(self.root)
            trans_window.title(f"用户 {self.current_user} 的交易记录")
            trans_window.geometry("800x400")

            # 创建表格
            columns = ("时间", "类型", "金额", "目标用户", "描述")
            tree = ttk.Treeview(trans_window, columns=columns,
                                show="headings", height=20)

            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=150)

            # 添加数据
            for trans in transactions:
                tree.insert("", tk.END, values=(
                    datetime.fromtimestamp(trans['transaction_time']).strftime(
                        '%Y-%m-%d %H:%M:%S'),
                    trans['transaction_type'],
                    f"{trans['amount']/100:.2f}",
                    trans.get('target_user_id', ''),
                    trans.get('description', '')
                ))

            tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        except Exception as e:
            messagebox.showerror("错误", f"获取交易记录时发生异常: {str(e)}")


class SecureBankManagementSystem:
    def __init__(self, db_path: str = "bank_system.db", config_path: str = "config.json"):
        """初始化银行管理系统"""
        self.db_path = db_path
        self.config_path = config_path
        self.config = self.load_config()
        self.init_database()

        # 设置存储阈值（默认为100MB）
        self.storage_threshold = self.config.get(
            'storage_threshold', 100 * 1024 * 1024)
        self.backup_server_url = self.config.get('backup_server_url')

    def load_config(self) -> Dict:
        """加载配置文件"""
        default_config = {
            'storage_threshold': 100 * 1024 * 1024,  # 100MB
            'backup_server_url': 'http://your-backup-server.com/api/backup',
            'compression_enabled': True,
            'auto_upload_enabled': True,
            'max_password_attempts': 3,
            'password_min_length': 6
        }

        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return {**default_config, **json.load(f)}
        except Exception as e:
            print(f"加载配置文件失败，使用默认配置: {e}")

        return default_config

    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败: {e}")

    def init_database(self):
        """初始化数据库 - 包含密码表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建用户表 - 优化字段设计减少存储
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                id_card TEXT UNIQUE NOT NULL,
                phone TEXT,
                email TEXT,
                address TEXT,
                account_type TEXT DEFAULT 'SAV',
                balance INTEGER DEFAULT 0,  -- 使用整数存储分单位
                created_time INTEGER NOT NULL,  -- 使用时间戳
                status TEXT DEFAULT 'A',
                compressed_data BLOB  -- 存储压缩的额外数据
            )
        ''')

        # 创建密码表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_passwords (
                user_id TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                failed_attempts INTEGER DEFAULT 0,
                last_attempt_time INTEGER,
                created_time INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        # 创建交易记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                transaction_type TEXT NOT NULL,  -- DEPOSIT, WITHDRAW, TRANSFER
                amount INTEGER NOT NULL,
                target_user_id TEXT,  -- 对于转账操作
                description TEXT,
                transaction_time INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        # 创建索引优化查询
        cursor.execute(
            'CREATE INDEX IF NOT EXISTS idx_user_id ON users(user_id)')
        cursor.execute(
            'CREATE INDEX IF NOT EXISTS idx_id_card ON users(id_card)')
        cursor.execute(
            'CREATE INDEX IF NOT EXISTS idx_created_time ON users(created_time)')
        cursor.execute(
            'CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id)')
        cursor.execute(
            'CREATE INDEX IF NOT EXISTS idx_transactions_time ON transactions(transaction_time)')

        conn.commit()
        conn.close()

    def hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """哈希密码"""
        if salt is None:
            salt = os.urandom(32).hex()

        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # 迭代次数
        ).hex()

        return password_hash, salt

    def verify_password(self, password: str, stored_hash: str, salt: str) -> bool:
        """验证密码"""
        password_hash, _ = self.hash_password(password, salt)
        return password_hash == stored_hash

    def set_user_password(self, user_id: str) -> bool:
        """设置用户密码（只能用户输入）"""
        if not self.user_exists(user_id):
            print("用户不存在")
            return False

        # 检查是否已设置密码
        if self.is_password_set(user_id):
            print("该用户已设置密码，如需修改请联系管理员")
            return False

        print(f"为用户 {user_id} 设置密码")

        # 获取密码（隐藏输入）
        while True:
            password = getpass.getpass("请输入密码: ")
            confirm_password = getpass.getpass("请确认密码: ")

            if password != confirm_password:
                print("两次输入的密码不一致，请重新输入")
                continue

            if len(password) < self.config.get('password_min_length', 6):
                print(f"密码长度至少为 {self.config['password_min_length']} 位")
                continue

            if not password.strip():
                print("密码不能为空")
                continue

            break

        # 哈希并存储密码
        password_hash, salt = self.hash_password(password)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO user_passwords 
                (user_id, password_hash, salt, created_time)
                VALUES (?, ?, ?, ?)
            ''', (user_id, password_hash, salt, int(datetime.now().timestamp())))

            conn.commit()
            print("密码设置成功")
            return True

        except Exception as e:
            conn.rollback()
            print(f"设置密码失败: {e}")
            return False
        finally:
            conn.close()

    def authenticate_user(self, user_id: str) -> bool:
        """用户身份验证"""
        if not self.user_exists(user_id):
            print("用户不存在")
            return False

        if not self.is_password_set(user_id):
            print("该用户尚未设置密码，请先设置密码")
            return self.set_user_password(user_id)

        max_attempts = self.config.get('max_password_attempts', 3)
        attempts = 0

        while attempts < max_attempts:
            password = getpass.getpass(f"请输入用户 {user_id} 的密码: ")

            if self.verify_user_password(user_id, password):
                print("密码验证成功")
                return True
            else:
                attempts += 1
                remaining = max_attempts - attempts
                if remaining > 0:
                    print(f"密码错误，还剩 {remaining} 次尝试机会")
                else:
                    print("密码错误次数过多，请稍后再试")
                    return False

        return False

    def verify_user_password(self, user_id: str, password: str) -> bool:
        """验证用户密码"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT password_hash, salt, failed_attempts FROM user_passwords WHERE user_id = ?",
                (user_id,)
            )
            result = cursor.fetchone()

            if not result:
                return False

            stored_hash, salt, failed_attempts = result

            if self.verify_password(password, stored_hash, salt):
                # 密码正确，重置失败次数
                if failed_attempts > 0:
                    cursor.execute(
                        "UPDATE user_passwords SET failed_attempts = 0 WHERE user_id = ?",
                        (user_id,)
                    )
                    conn.commit()
                return True
            else:
                # 密码错误，增加失败次数
                cursor.execute(
                    "UPDATE user_passwords SET failed_attempts = failed_attempts + 1, last_attempt_time = ? WHERE user_id = ?",
                    (int(datetime.now().timestamp()), user_id)
                )
                conn.commit()
                return False

        finally:
            conn.close()

    def user_exists(self, user_id: str) -> bool:
        """检查用户是否存在"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM users WHERE user_id = ?", (user_id,))
        count = cursor.fetchone()[0]

        conn.close()
        return count > 0

    def is_password_set(self, user_id: str) -> bool:
        """检查是否已设置密码"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM user_passwords WHERE user_id = ?", (user_id,))
        count = cursor.fetchone()[0]

        conn.close()
        return count > 0

    def check_storage_space(self) -> Tuple[bool, float]:
        """检查存储空间"""
        try:
            disk_usage = psutil.disk_usage('.')
            free_space = disk_usage.free
            return free_space < self.storage_threshold, free_space
        except Exception as e:
            print(f"检查存储空间失败: {e}")
            return False, 0

    def compress_data(self, data: Dict) -> bytes:
        """压缩数据"""
        try:
            json_str = json.dumps(
                data, ensure_ascii=False, separators=(',', ':'))
            compressed = zlib.compress(json_str.encode('utf-8'), level=9)
            return compressed
        except Exception as e:
            print(f"数据压缩失败: {e}")
            return pickle.dumps(data)

    def decompress_data(self, compressed_data: bytes) -> Dict:
        """解压数据"""
        try:
            decompressed = zlib.decompress(compressed_data)
            return json.loads(decompressed.decode('utf-8'))
        except:
            return pickle.loads(compressed_data)

    def generate_user_id(self) -> str:
        """生成固定用户ID - 更紧凑的格式"""
        timestamp = int(datetime.now().timestamp())
        unique_part = str(uuid.uuid4().int)[:6]
        return f"B{timestamp}{unique_part}"

    def add_user(self, user_data: Dict) -> Dict:
        """添加新用户 - 带存储检查"""
        # 检查存储空间
        storage_low, free_space = self.check_storage_space()
        if storage_low and self.config.get('auto_upload_enabled', True):
            print(f"存储空间不足，剩余: {free_space/1024/1024:.2f}MB")
            upload_result = self.upload_to_server()
            if not upload_result.get('success'):
                return {"success": False, "message": "存储空间不足且上传失败"}

        # 验证必要字段
        required_fields = ['name', 'id_card']
        for field in required_fields:
            if field not in user_data:
                return {"success": False, "message": f"缺少必要字段: {field}"}

        # 检查身份证是否已存在
        if self.check_id_card_exists(user_data['id_card']):
            return {"success": False, "message": "该身份证号已注册"}

        # 生成用户ID
        user_id = self.generate_user_id()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 准备压缩的额外数据
            extra_data = {
                'original_data': {k: v for k, v in user_data.items() if k not in ['name', 'id_card', 'phone', 'email', 'address']},
                'system_info': {
                    'version': '1.0',
                    'created_by': 'bank_system'
                }
            }
            compressed_extra = self.compress_data(extra_data) if self.config.get(
                'compression_enabled', True) else None

            # 转换余额到分
            balance = int(float(user_data.get('balance', 0)) * 100)

            # 插入用户数据
            cursor.execute('''
                INSERT INTO users 
                (user_id, name, id_card, phone, email, address, account_type, balance, created_time, compressed_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                user_data['name'],
                user_data['id_card'],
                user_data.get('phone', ''),
                user_data.get('email', ''),
                user_data.get('address', ''),
                self._shorten_account_type(
                    user_data.get('account_type', '储蓄账户')),
                balance,
                int(datetime.now().timestamp()),
                compressed_extra
            ))

            conn.commit()

            # 生成二维码
            qr_code_path = self.generate_qr_code(user_id, user_data['name'])

            return {
                "success": True,
                "message": "用户添加成功",
                "user_id": user_id,
                "qr_code_path": qr_code_path,
                "storage_status": {
                    "low_space": storage_low,
                    "free_space_mb": free_space/1024/1024
                }
            }

        except Exception as e:
            conn.rollback()
            return {"success": False, "message": f"添加用户失败: {str(e)}"}
        finally:
            conn.close()

    def _shorten_account_type(self, account_type: str) -> str:
        """缩短账户类型字符串"""
        mapping = {
            '储蓄账户': 'SAV',
            '支票账户': 'CHK',
            '信用卡账户': 'CRD',
            '贷款账户': 'LN'
        }
        return mapping.get(account_type, 'SAV')

    def _expand_account_type(self, short_type: str) -> str:
        """扩展账户类型字符串"""
        mapping = {
            'SAV': '储蓄账户',
            'CHK': '支票账户',
            'CRD': '信用卡账户',
            'LN': '贷款账户'
        }
        return mapping.get(short_type, '储蓄账户')

    def check_id_card_exists(self, id_card: str) -> bool:
        """检查身份证号是否存在"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM users WHERE id_card = ?", (id_card,))
        count = cursor.fetchone()[0]

        conn.close()
        return count > 0

    def generate_qr_code(self, user_id: str, user_name: str) -> str:
        """生成用户二维码 - 优化大小"""
        # 创建二维码目录
        qr_dir = "user_qrcodes"
        if not os.path.exists(qr_dir):
            os.makedirs(qr_dir)

        # 最小化二维码数据
        qr_data = {
            "uid": user_id,
            "n": user_name,
            "t": int(datetime.now().timestamp())
        }

        # 生成优化大小的二维码
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=8,  # 更小的盒子尺寸
            border=2,    # 更细的边框
        )
        qr.add_data(json.dumps(qr_data, separators=(',', ':')))
        qr.make(fit=True)

        # 创建二维码图片
        img = qr.make_image(fill_color="black", back_color="white")

        # 保存二维码
        qr_filename = f"{user_id}_qrcode.png"
        qr_path = os.path.join(qr_dir, qr_filename)
        img.save(qr_path)

        return qr_path

    def search_users(self, search_type: str, search_value: str) -> List[Dict]:
        """搜索用户"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            if search_type == "user_id":
                cursor.execute('''
                    SELECT user_id, name, id_card, phone, account_type, balance, status
                    FROM users WHERE user_id LIKE ? AND status = 'A'
                ''', (f"%{search_value}%",))
            elif search_type == "name":
                cursor.execute('''
                    SELECT user_id, name, id_card, phone, account_type, balance, status
                    FROM users WHERE name LIKE ? AND status = 'A'
                ''', (f"%{search_value}%",))
            elif search_type == "id_card":
                cursor.execute('''
                    SELECT user_id, name, id_card, phone, account_type, balance, status
                    FROM users WHERE id_card LIKE ? AND status = 'A'
                ''', (f"%{search_value}%",))
            else:
                return []

            results = []
            for row in cursor.fetchall():
                user = {
                    'user_id': row[0],
                    'name': row[1],
                    'id_card': row[2],
                    'phone': row[3],
                    'account_type': row[4],
                    'balance': row[5],
                    'status': row[6]
                }
                results.append(user)

            return results

        finally:
            conn.close()

    def get_user_info(self, user_id: str) -> Optional[Dict]:
        """获取用户信息（需要密码验证）"""
        if not self.authenticate_user(user_id):
            return None

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT user_id, name, id_card, phone, email, address, account_type, balance, created_time, status, compressed_data
                FROM users WHERE user_id = ?
            ''', (user_id,))

            row = cursor.fetchone()
            if not row:
                return None

            user_info = {
                'user_id': row[0],
                'name': row[1],
                'id_card': row[2],
                'phone': row[3],
                'email': row[4],
                'address': row[5],
                'account_type': row[6],
                'balance': row[7],
                'created_time': row[8],
                'status': row[9]
            }

            # 解压额外数据
            if row[10]:
                try:
                    extra_data = self.decompress_data(row[10])
                    user_info.update(extra_data.get('original_data', {}))
                except:
                    pass

            return user_info

        finally:
            conn.close()

    def get_balance(self, user_id: str) -> Optional[int]:
        """获取用户余额（需要密码验证）"""
        if not self.authenticate_user(user_id):
            return None

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT balance FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    def deposit(self, user_id: str, amount: float) -> bool:
        """存款（需要密码验证）"""
        if not self.authenticate_user(user_id):
            return False

        amount_cents = int(amount * 100)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 更新余额
            cursor.execute(
                "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                (amount_cents, user_id)
            )

            # 记录交易
            cursor.execute('''
                INSERT INTO transactions 
                (user_id, transaction_type, amount, description, transaction_time)
                VALUES (?, 'DEPOSIT', ?, ?, ?)
            ''', (user_id, amount_cents, f"存款 {amount:.2f} 元", int(datetime.now().timestamp())))

            conn.commit()
            return cursor.rowcount > 0

        except Exception as e:
            conn.rollback()
            print(f"存款失败: {e}")
            return False
        finally:
            conn.close()

    def withdraw(self, user_id: str, amount: float) -> bool:
        """取款（需要密码验证）"""
        if not self.authenticate_user(user_id):
            return False

        amount_cents = int(amount * 100)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 检查余额是否足够
            cursor.execute(
                "SELECT balance FROM users WHERE user_id = ?", (user_id,))
            current_balance = cursor.fetchone()[0]

            if current_balance < amount_cents:
                return False

            # 更新余额
            cursor.execute(
                "UPDATE users SET balance = balance - ? WHERE user_id = ?",
                (amount_cents, user_id)
            )

            # 记录交易
            cursor.execute('''
                INSERT INTO transactions 
                (user_id, transaction_type, amount, description, transaction_time)
                VALUES (?, 'WITHDRAW', ?, ?, ?)
            ''', (user_id, amount_cents, f"取款 {amount:.2f} 元", int(datetime.now().timestamp())))

            conn.commit()
            return cursor.rowcount > 0

        except Exception as e:
            conn.rollback()
            print(f"取款失败: {e}")
            return False
        finally:
            conn.close()

    def transfer(self, from_user_id: str, to_user_id: str, amount: float) -> bool:
        """转账（需要密码验证）"""
        if not self.authenticate_user(from_user_id):
            return False

        # 检查目标用户是否存在
        if not self.user_exists(to_user_id):
            return False

        amount_cents = int(amount * 100)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 检查余额是否足够
            cursor.execute(
                "SELECT balance FROM users WHERE user_id = ?", (from_user_id,))
            current_balance = cursor.fetchone()[0]

            if current_balance < amount_cents:
                return False

            # 执行转账
            # 减少转出用户余额
            cursor.execute(
                "UPDATE users SET balance = balance - ? WHERE user_id = ?",
                (amount_cents, from_user_id)
            )

            # 增加转入用户余额
            cursor.execute(
                "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                (amount_cents, to_user_id)
            )

            # 记录转出交易
            cursor.execute('''
                INSERT INTO transactions 
                (user_id, transaction_type, amount, target_user_id, description, transaction_time)
                VALUES (?, 'TRANSFER_OUT', ?, ?, ?, ?)
            ''', (from_user_id, amount_cents, to_user_id, f"向 {to_user_id} 转账 {amount:.2f} 元", int(datetime.now().timestamp())))

            # 记录转入交易
            cursor.execute('''
                INSERT INTO transactions 
                (user_id, transaction_type, amount, target_user_id, description, transaction_time)
                VALUES (?, 'TRANSFER_IN', ?, ?, ?, ?)
            ''', (to_user_id, amount_cents, from_user_id, f"收到 {from_user_id} 转账 {amount:.2f} 元", int(datetime.now().timestamp())))

            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            print(f"转账失败: {e}")
            return False
        finally:
            conn.close()

    def get_transactions(self, user_id: str) -> List[Dict]:
        """获取交易记录（需要密码验证）"""
        if not self.authenticate_user(user_id):
            return []

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT transaction_type, amount, target_user_id, description, transaction_time
                FROM transactions 
                WHERE user_id = ? 
                ORDER BY transaction_time DESC
                LIMIT 100
            ''', (user_id,))

            transactions = []
            for row in cursor.fetchall():
                trans = {
                    'transaction_type': row[0],
                    'amount': row[1],
                    'target_user_id': row[2],
                    'description': row[3],
                    'transaction_time': row[4]
                }
                transactions.append(trans)

            return transactions

        finally:
            conn.close()

    def upload_to_server(self) -> Dict:
        """上传数据到服务器"""
        # 这里实现上传逻辑
        return {"success": False, "message": "服务器上传功能待实现"}


def main():
    """主函数"""
    root = tk.Tk()
    app = BankManagementGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
