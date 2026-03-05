import os
import sqlite3
import json
import threading
import requests
from datetime import datetime
from tkinter import filedialog, messagebox

import customtkinter as ctk
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from fpdf import FPDF

matplotlib.use("TkAgg")

# ====================== 配置信息 ======================
ZHIPU_API_KEY = "17d87e338dd2444fbf38812658e25718.iHNTNpYrGrS4taM6"
ZHIPU_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
ZHIPU_MODEL = "glm-4"

# ====================== 系统自适应配置 ======================
# 判断当前系统
IS_WINDOWS = os.name == 'nt'
IS_MACOS = not IS_WINDOWS

# 根据系统选择字体
FONT_FAMILY = "Microsoft YaHei" if IS_WINDOWS else "PingFang SC"

# 配色方案 (保持液态玻璃风格)
GLASS_BG_COLOR = "#f5f5f7"
GLASS_CARD_COLOR = "#ffffff"
GLASS_SIDEBAR_COLOR = "#ffffff"
GLASS_TEXT_COLOR = "#1d1d1f"
GLASS_SUBTEXT_COLOR = "#86868b"
GLASS_BORDER_COLOR = "#e5e5e7"

ACCENT_BLUE = "#007AFF"
ACCENT_GREEN = "#34c759"
ACCENT_RED = "#ff3b30"
ACCENT_PURPLE = "#af52de"

# ====================== 数据库路径 ======================
home_dir = os.path.expanduser("~")
db_dir = os.path.join(home_dir, "Documents")
os.makedirs(db_dir, exist_ok=True)
DB_PATH = os.path.join(db_dir, "pineapple_data.db")

# ====================== 外观设置 ======================
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("菠萝皮来源智能登记系统")
        self.geometry("1150x750")
        self.minsize(1000, 600)
        self.configure(fg_color=GLASS_BG_COLOR)

        # 字体设置 (自适应系统)
        self.font_cn = ctk.CTkFont(family=FONT_FAMILY, size=14)
        self.font_cn_bold = ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold")
        self.font_title = ctk.CTkFont(family=FONT_FAMILY, size=24, weight="bold")
        self.font_small = ctk.CTkFont(family=FONT_FAMILY, size=12)

        self.db_name = DB_PATH
        self.init_db()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- 侧边栏 ---
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color=GLASS_SIDEBAR_COLOR, border_width=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar, text="🍍 菠萝皮管理", font=self.font_title,
                                       text_color=GLASS_TEXT_COLOR)
        self.logo_label.grid(row=0, column=0, padx=25, pady=(40, 15), sticky="w")

        self.db_info_label = ctk.CTkLabel(self.sidebar, text="数据安全存储于本地 Documents", font=self.font_small,
                                          text_color=GLASS_SUBTEXT_COLOR)
        self.db_info_label.grid(row=1, column=0, padx=25, pady=(0, 40), sticky="w")

        self.btn_create = self.create_glass_button("📝 新增登记", self.show_create_frame, row=2)
        self.btn_view = self.create_glass_button("📊 数据总览", self.show_view_frame, row=3)
        self.btn_stats = self.create_glass_button("📈 统计图表", self.show_stats_frame, row=4)

        self.btn_ai = ctk.CTkButton(self.sidebar, text="🤖 AI 智能分析", command=self.show_ai_frame,
                                    font=self.font_cn_bold, height=50, corner_radius=14, fg_color=ACCENT_PURPLE,
                                    hover_color="#9038d0", text_color="white")
        self.btn_ai.grid(row=6, column=0, padx=25, pady=15, sticky="ew")

        self.btn_export = self.create_glass_button("📤 导出报表", self.export_menu, row=7, fg_color=ACCENT_GREEN,
                                                   hover_color="#30b350", text_color="white")

        # --- 主内容区域 ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=GLASS_BG_COLOR)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=25, pady=25)

        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.current_frame = None
        self.search_entry = None
        self.ai_is_working = False

        self.show_create_frame()

    def create_glass_button(self, text, command, row, fg_color="transparent", hover_color="#f0f0f5",
                            text_color=GLASS_TEXT_COLOR):
        btn = ctk.CTkButton(self.sidebar, text=text, command=command, font=self.font_cn, height=50, corner_radius=14,
                            fg_color=fg_color, hover_color=hover_color, text_color=text_color, anchor="w")
        btn.grid(row=row, column=0, padx=25, pady=5, sticky="ew")
        return btn

    # ====================== 数据库初始化 ======================
    def init_db(self):
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute(
                "CREATE TABLE IF NOT EXISTS records (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT NOT NULL, location TEXT NOT NULL, weight REAL NOT NULL, contact TEXT NOT NULL, phone TEXT NOT NULL, note TEXT)")
            conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("数据库错误", f"初始化数据库失败: {e}")
        finally:
            if "conn" in locals(): conn.close()

    def clear_main_frame(self):
        if self.current_frame:
            self.current_frame.destroy()
            self.current_frame = None

    # ====================== UI 页面：新增登记 ======================
    def show_create_frame(self):
        self.clear_main_frame()
        self.current_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        self.current_frame.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(self.current_frame, text="新增来源登记", font=self.font_title, text_color=GLASS_TEXT_COLOR,
                     anchor="w").pack(fill="x", pady=(0, 20))

        form_card = ctk.CTkFrame(self.current_frame, fg_color=GLASS_CARD_COLOR, corner_radius=20, border_width=1,
                                 border_color=GLASS_BORDER_COLOR)
        form_card.pack(fill="x", padx=5, pady=5)

        form_card.grid_columnconfigure(1, weight=1)
        form_card.grid_columnconfigure(3, weight=1)

        entry_style = {"height": 45, "border_width": 0, "corner_radius": 12, "fg_color": "#f7f7f7",
                       "text_color": GLASS_TEXT_COLOR}

        self._create_form_row(form_card, 0, "📅 日期", "YYYY-MM-DD", colspan=3, entry_style=entry_style)
        self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        self._create_form_row(form_card, 1, "📍 来源地点", "例如：广州天河市场", col=0, colspan=1,
                              entry_style=entry_style)
        self._create_form_row(form_card, 1, "⚖️ 重量", "单位：kg", col=2, colspan=1, entry_style=entry_style)

        self._create_form_row(form_card, 2, "👤 联系人", "姓名", col=0, colspan=1, entry_style=entry_style)
        self._create_form_row(form_card, 2, "📞 电话", "手机号码", col=2, colspan=1, entry_style=entry_style)

        self._create_form_row(form_card, 3, "📝 备注", "选填内容", is_textbox=True, colspan=3)

        action_frame = ctk.CTkFrame(self.current_frame, fg_color="transparent")
        action_frame.pack(fill="x", pady=(25, 10), padx=5)

        btn_container = ctk.CTkFrame(action_frame, fg_color="transparent")
        btn_container.pack(side="right")

        ctk.CTkButton(btn_container, text="重置", font=self.font_cn, width=110, height=45, fg_color="#e8e8ed",
                      text_color=GLASS_TEXT_COLOR, hover_color="#dcdce0", corner_radius=14,
                      command=self.show_create_frame).pack(side="left", padx=10)
        ctk.CTkButton(btn_container, text="💾 保存登记", font=self.font_cn_bold, width=150, height=45,
                      fg_color=ACCENT_BLUE, hover_color="#0062cc", corner_radius=14, command=self.submit_data).pack(
            side="left")

    def _create_form_row(self, parent, row, label_text, placeholder, col=0, colspan=2, is_textbox=False,
                         entry_style=None):
        if entry_style is None: entry_style = {}

        lbl = ctk.CTkLabel(parent, text=label_text, font=self.font_cn, text_color=GLASS_SUBTEXT_COLOR, anchor="e",
                           width=130)
        lbl.grid(row=row, column=col, padx=(25, 15), pady=15, sticky="ne")

        widget_col = col + 1

        if is_textbox:
            entry = ctk.CTkTextbox(parent, height=110, font=self.font_cn, corner_radius=12, border_width=0,
                                   fg_color="#f7f7f7", border_color=GLASS_BORDER_COLOR)
            entry.grid(row=row, column=widget_col, columnspan=colspan, padx=(0, 25), pady=15, sticky="ew")
            if placeholder: entry.insert("0.0", placeholder)
        else:
            entry = ctk.CTkEntry(parent, placeholder_text=placeholder, font=self.font_cn, **entry_style)
            entry.grid(row=row, column=widget_col, columnspan=colspan, padx=(0, 25), pady=15, sticky="ew")

        if "日期" in label_text:
            self.entry_date = entry
        elif "地点" in label_text:
            self.entry_location = entry
        elif "重量" in label_text:
            self.entry_weight = entry
        elif "联系人" in label_text:
            self.entry_contact = entry
        elif "电话" in label_text:
            self.entry_phone = entry
        elif "备注" in label_text:
            self.entry_note = entry

    # ====================== 保存数据 ======================
    def submit_data(self):
        try:
            date = self.entry_date.get().strip()
            location = self.entry_location.get().strip()
            contact = self.entry_contact.get().strip()
            phone = self.entry_phone.get().strip()
            note = self.entry_note.get("1.0", "end").strip()

            try:
                weight = float(self.entry_weight.get().strip())
                if weight <= 0: raise ValueError()
            except ValueError:
                messagebox.showerror("输入错误", "重量必须是大于0的数字")
                return

            if not all([date, location, contact, phone]):
                messagebox.showwarning("信息不完整", "请填写日期、地点、联系人和电话")
                return

            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute("INSERT INTO records (date, location, weight, contact, phone, note) VALUES (?, ?, ?, ?, ?, ?)",
                      (date, location, weight, contact, phone, note))
            conn.commit()
            messagebox.showinfo("成功", "✅ 数据已成功登记！")
            self.show_view_frame()
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}")
        finally:
            if "conn" in locals(): conn.close()

    # ====================== UI 页面：查看记录 ======================
    def show_view_frame(self):
        self.clear_main_frame()
        self.current_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        self.current_frame.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(self.current_frame, text="数据总览", font=self.font_title, text_color=GLASS_TEXT_COLOR,
                     anchor="w").pack(fill="x", pady=(0, 20))

        search_frame = ctk.CTkFrame(self.current_frame, fg_color=GLASS_CARD_COLOR, corner_radius=18, height=55,
                                    border_width=1, border_color=GLASS_BORDER_COLOR)
        search_frame.pack(fill="x", pady=(0, 15))
        search_frame.pack_propagate(False)

        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="🔍 搜索日期、地点、联系人...", font=self.font_cn,
                                         height=40, border_width=0, corner_radius=10, fg_color="#f0f0f2")
        self.search_entry.pack(side="left", padx=15, fill="x", expand=True, pady=7)

        ctk.CTkButton(search_frame, text="搜索", command=self.search_records, width=90, height=40, corner_radius=12,
                      fg_color=ACCENT_BLUE).pack(side="left", padx=(0, 15), pady=7)

        try:
            conn = sqlite3.connect(self.db_name)
            df = pd.read_sql_query("SELECT * FROM records ORDER BY id DESC", conn)
        except Exception as e:
            messagebox.showerror("错误", f"加载数据失败: {e}")
            df = pd.DataFrame()
        finally:
            if "conn" in locals(): conn.close()

        if df.empty:
            ctk.CTkLabel(self.current_frame, text="暂无记录\n点击左侧 '新增登记' 开始", font=self.font_cn,
                         text_color=GLASS_SUBTEXT_COLOR).pack(pady=50)
            return

        for _, row in df.iterrows():
            self._create_data_row_card(self.current_frame, row)

    def _create_data_row_card(self, parent, row):
        card = ctk.CTkFrame(parent, fg_color=GLASS_CARD_COLOR, corner_radius=15, border_width=1,
                            border_color=GLASS_BORDER_COLOR)
        card.pack(fill="x", pady=5)

        card.grid_columnconfigure(1, weight=1)

        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.grid(row=0, column=0, sticky="w", padx=20, pady=15)

        ctk.CTkLabel(info_frame, text=f"📍 {row['location']}", font=self.font_cn_bold, text_color=GLASS_TEXT_COLOR).grid(
            row=0, column=0, sticky="w")
        ctk.CTkLabel(info_frame, text=f"⚖️ {row['weight']} kg", font=self.font_cn, text_color=ACCENT_BLUE).grid(row=0,
                                                                                                                column=1,
                                                                                                                padx=(
                                                                                                                    25,
                                                                                                                    0))
        ctk.CTkLabel(info_frame, text=f"📅 {row['date']} | 👤 {row['contact']} ({row['phone']})", font=self.font_small,
                     text_color=GLASS_SUBTEXT_COLOR).grid(row=1, column=0, columnspan=2, sticky="w", pady=(5, 0))

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.grid(row=0, column=1, sticky="e", padx=20, pady=15)

        ctk.CTkButton(btn_frame, text="编辑", width=65, height=32, font=self.font_small, fg_color="#e8e8ed",
                      text_color=GLASS_TEXT_COLOR, hover_color="#dcdce0", corner_radius=10,
                      command=lambda rid=row["id"]: self.edit_record(rid)).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="删除", width=65, height=32, font=self.font_small, fg_color=ACCENT_RED,
                      text_color="white", hover_color="#d63029", corner_radius=10,
                      command=lambda rid=row["id"]: self.delete_record(rid)).pack(side="left", padx=5)

    # ====================== 搜索/删除/编辑逻辑 ======================
    def search_records(self):
        keyword = self.search_entry.get().strip()
        if not keyword:
            self.show_view_frame()
            return
        try:
            conn = sqlite3.connect(self.db_name)
            query = "SELECT * FROM records WHERE date LIKE ? OR location LIKE ? OR contact LIKE ? OR phone LIKE ? ORDER BY id DESC"
            like_kw = f"%{keyword}%"
            df = pd.read_sql_query(query, conn, params=(like_kw, like_kw, like_kw, like_kw))
        except Exception as e:
            return
        finally:
            if "conn" in locals(): conn.close()

        self.clear_main_frame()
        self.current_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        self.current_frame.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self.current_frame, text=f"搜索结果：{keyword}", font=self.font_title, text_color=GLASS_TEXT_COLOR,
                     anchor="w").pack(fill="x", pady=(0, 15))
        if df.empty:
            ctk.CTkLabel(self.current_frame, text="没有找到匹配记录", font=self.font_cn).pack(pady=20)
            return
        for _, row in df.iterrows():
            self._create_data_row_card(self.current_frame, row)

    def delete_record(self, record_id):
        if not messagebox.askyesno("确认删除", "确定要删除这条记录吗？"): return
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute("DELETE FROM records WHERE id=?", (record_id,))
            conn.commit()
            messagebox.showinfo("成功", "记录已删除")
            self.show_view_frame()
        except Exception as e:
            messagebox.showerror("错误", f"删除失败: {e}")
        finally:
            if "conn" in locals(): conn.close()

    def edit_record(self, record_id):
        try:
            conn = sqlite3.connect(self.db_name)
            df = pd.read_sql_query("SELECT * FROM records WHERE id=?", conn, params=(record_id,))
        except Exception as e:
            return
        finally:
            if "conn" in locals(): conn.close()
        if df.empty: return
        row = df.iloc[0]

        edit_win = ctk.CTkToplevel(self)
        edit_win.title(f"编辑记录 - ID {record_id}")
        edit_win.geometry("500x600")
        edit_win.configure(fg_color=GLASS_BG_COLOR)
        edit_win.transient(self)
        edit_win.grab_set()
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - 250
        y = self.winfo_y() + (self.winfo_height() // 2) - 300
        edit_win.geometry(f"+{x}+{y}")

        entries = {}
        labels = ["date", "location", "weight", "contact", "phone", "note"]
        label_texts = ["日期", "地点", "重量", "联系人", "电话", "备注"]

        card = ctk.CTkFrame(edit_win, fg_color=GLASS_CARD_COLOR, corner_radius=20, border_width=1,
                            border_color=GLASS_BORDER_COLOR)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        for i, (field, text) in enumerate(zip(labels, label_texts)):
            ctk.CTkLabel(card, text=text, font=self.font_cn, text_color=GLASS_TEXT_COLOR, anchor="w").pack(fill="x",
                                                                                                           padx=25,
                                                                                                           pady=(15, 0))
            if field == "note":
                entry = ctk.CTkTextbox(card, height=80, font=self.font_cn, border_width=0, corner_radius=10,
                                       fg_color="#f0f0f2")
                entry.pack(fill="x", padx=25, pady=(0, 10))
                entry.insert("0.0", str(row[field]))
            else:
                entry = ctk.CTkEntry(card, font=self.font_cn, height=40, border_width=0, corner_radius=10,
                                     fg_color="#f0f0f2")
                entry.pack(fill="x", padx=25, pady=(0, 10))
                entry.insert(0, str(row[field]))
            entries[field] = entry

        def save_edit():
            try:
                new_data = {
                    "date": entries["date"].get().strip(),
                    "location": entries["location"].get().strip(),
                    "weight": float(entries["weight"].get().strip()),
                    "contact": entries["contact"].get().strip(),
                    "phone": entries["phone"].get().strip(),
                    "note": entries["note"].get("1.0", "end").strip()
                }
                conn = sqlite3.connect(self.db_name)
                c = conn.cursor()
                c.execute("UPDATE records SET date=?, location=?, weight=?, contact=?, phone=?, note=? WHERE id=?",
                          (new_data["date"], new_data["location"], new_data["weight"], new_data["contact"],
                           new_data["phone"], new_data["note"], record_id))
                conn.commit()
                messagebox.showinfo("成功", "记录已更新")
                edit_win.destroy()
                self.show_view_frame()
            except Exception as e:
                messagebox.showerror("错误", f"更新失败: {e}")
            finally:
                if "conn" in locals(): conn.close()

        ctk.CTkButton(card, text="保存修改", command=save_edit, font=self.font_cn_bold, height=45, corner_radius=14,
                      fg_color=ACCENT_BLUE).pack(fill="x", padx=25, pady=20)

    # ====================== UI 页面：数据统计 (Windows 字体修复) ======================
    def show_stats_frame(self):
        self.clear_main_frame()
        self.current_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.current_frame.grid(row=0, column=0, sticky="nsew")
        self.current_frame.grid_rowconfigure(1, weight=1)
        self.current_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.current_frame, text="数据统计", font=self.font_title, text_color=GLASS_TEXT_COLOR,
                     anchor="w").grid(row=0, column=0, pady=(0, 15), sticky="w")

        try:
            conn = sqlite3.connect(self.db_name)
            df = pd.read_sql_query("SELECT * FROM records", conn)
        except Exception as e:
            messagebox.showerror("错误", f"加载数据失败: {e}")
            return
        finally:
            if "conn" in locals(): conn.close()

        if df.empty:
            ctk.CTkLabel(self.current_frame, text="暂无数据，无法生成统计图表", font=self.font_cn).grid(row=1, column=0,
                                                                                                       pady=20)
            return

        df["date"] = pd.to_datetime(df["date"]).dt.date
        total_weight = df["weight"].sum()
        total_records = len(df)
        unique_locations = df["location"].nunique()

        summary_frame = ctk.CTkFrame(self.current_frame, fg_color="transparent")
        summary_frame.grid(row=1, column=0, sticky="ew", pady=10)

        self._create_stat_card(summary_frame, "📦 总重量", f"{total_weight:.2f} kg", ACCENT_BLUE, 0)
        self._create_stat_card(summary_frame, "📝 记录数", f"{total_records} 条", ACCENT_GREEN, 1)
        self._create_stat_card(summary_frame, "🌍 地点数", f"{unique_locations} 个", "#ff9500", 2)

        chart_frame = ctk.CTkFrame(self.current_frame, fg_color=GLASS_CARD_COLOR, corner_radius=20, border_width=1,
                                   border_color=GLASS_BORDER_COLOR)
        chart_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=10)
        self.current_frame.grid_rowconfigure(2, weight=1)

        df_daily = df.groupby("date")["weight"].sum().reset_index()

        # --- 字体修复：根据系统自动选择字体路径 ---
        font_path = ''
        if IS_WINDOWS:
            # Windows 优先尝试微软雅黑，其次黑体
            font_path = 'C:/Windows/Fonts/msyh.ttc'
            if not os.path.exists(font_path):
                font_path = 'C:/Windows/Fonts/simhei.ttf'
        else:
            # macOS 字体路径
            font_path = '/System/Library/Fonts/PingFang.ttc'
            if not os.path.exists(font_path):
                font_path = '/System/Library/Fonts/STHeiti Light.ttc'

        try:
            font_prop = font_manager.FontProperties(fname=font_path)
        except:
            font_prop = font_manager.FontProperties()

        plt.style.use('seaborn-v0_8-whitegrid')
        fig, ax = plt.subplots(figsize=(8, 4), dpi=100)

        bars = ax.bar(df_daily["date"].astype(str), df_daily["weight"], color=ACCENT_BLUE, alpha=0.8, width=0.6)

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#d1d1d6')
        ax.spines['bottom'].set_color('#d1d1d6')

        ax.set_xlabel("日期", fontproperties=font_prop, fontsize=10, color=GLASS_SUBTEXT_COLOR)
        ax.set_ylabel("重量", fontproperties=font_prop, fontsize=10, color=GLASS_SUBTEXT_COLOR)
        ax.set_title("每日菠萝皮来源重量趋势", fontproperties=font_prop, fontsize=14, weight='bold',
                     color=GLASS_TEXT_COLOR, pad=15)

        plt.xticks(rotation=45, ha='right', fontsize=9, color=GLASS_SUBTEXT_COLOR)
        for label in ax.get_xticklabels():
            label.set_fontproperties(font_prop)

        plt.tight_layout()
        fig.patch.set_facecolor('white')

        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=15)

    def _create_stat_card(self, parent, title, value, color, col):
        card = ctk.CTkFrame(parent, fg_color=GLASS_CARD_COLOR, corner_radius=15, border_width=1,
                            border_color=GLASS_BORDER_COLOR, width=200, height=110)
        card.pack(side="left", padx=10, pady=5, expand=True, fill="x")
        card.pack_propagate(False)

        ctk.CTkLabel(card, text=title, font=self.font_small, text_color=GLASS_SUBTEXT_COLOR, anchor="w").pack(padx=20,
                                                                                                              pady=(25,
                                                                                                                    0),
                                                                                                              anchor="w")
        ctk.CTkLabel(card, text=value, font=self.font_title, text_color=color, anchor="w").pack(padx=20, pady=(5, 10),
                                                                                                anchor="w")

    # ====================== 导出功能 ======================
    def export_menu(self):
        win = ctk.CTkToplevel(self)
        win.title("导出数据")
        win.geometry("320x320")
        win.configure(fg_color=GLASS_BG_COLOR)
        win.transient(self)
        win.grab_set()
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - 160
        y = self.winfo_y() + (self.winfo_height() // 2) - 160
        win.geometry(f"+{x}+{y}")

        ctk.CTkLabel(win, text="选择导出格式", font=self.font_cn_bold, text_color=GLASS_TEXT_COLOR).pack(pady=25)

        formats = [("Excel (.xlsx)", "excel"), ("CSV (.csv)", "csv"), ("PDF (.pdf)", "pdf")]
        for text, fmt in formats:
            ctk.CTkButton(win, text=text, command=lambda f=fmt: self.export_data(f, win), font=self.font_cn, height=45,
                          corner_radius=12, fg_color=GLASS_CARD_COLOR, text_color=GLASS_TEXT_COLOR,
                          hover_color="#e8e8ed", border_width=1, border_color=GLASS_BORDER_COLOR).pack(fill="x",
                                                                                                       padx=35, pady=5)

    def export_data(self, file_type, window):
        try:
            conn = sqlite3.connect(self.db_name)
            df = pd.read_sql_query("SELECT * FROM records ORDER BY id", conn)
        except Exception as e:
            messagebox.showerror("错误", f"读取数据失败: {e}")
            return
        finally:
            if "conn" in locals(): conn.close()

        if df.empty:
            messagebox.showwarning("提示", "没有数据可导出")
            return

        ext_map = {"excel": "xlsx", "csv": "csv", "pdf": "pdf"}
        file_ext = ext_map[file_type]

        file_path = filedialog.asksaveasfilename(defaultextension=f".{file_ext}",
                                                 filetypes=[(f"{file_ext.upper()} files", f"*.{file_ext}")],
                                                 initialfile=f"菠萝皮数据_{datetime.now().strftime('%Y%m%d')}")

        if not file_path: return

        try:
            if file_type == "excel":
                df.to_excel(file_path, index=False)
            elif file_type == "csv":
                df.to_csv(file_path, index=False, encoding="utf-8-sig")
            elif file_type == "pdf":
                self.create_pdf(df, file_path)

            messagebox.showinfo("成功", f"已导出至:\n{file_path}")
            window.destroy()
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {e}")

    def create_pdf(self, df, filename):
        pdf = FPDF()
        pdf.add_page()

        # --- 字体修复：PDF 导出 ---
        font_path = ""
        if IS_WINDOWS:
            font_path = 'C:/Windows/Fonts/simhei.ttf'  # Windows 黑体
        else:
            font_path = "/System/Library/Fonts/PingFang.ttc"

        if os.path.exists(font_path):
            pdf.add_font("UserFont", "", font_path, uni=True)
            pdf.set_font("UserFont", size=12)
        else:
            pdf.set_font("Arial", size=12)

        pdf.cell(200, 10, txt="Pineapple Data Report", ln=1, align="C")
        pdf.ln(10)

        col_widths = [15, 30, 40, 20, 30, 30, 55]
        headers = ["ID", "Date", "Loc", "Wgt", "Name", "Phone", "Note"]
        for i, h in enumerate(headers):
            pdf.cell(col_widths[i], 10, h, border=1)
        pdf.ln()

        for _, row in df.iterrows():
            pdf.cell(col_widths[0], 10, str(row["id"]), border=1)
            pdf.cell(col_widths[1], 10, str(row["date"]), border=1)
            pdf.cell(col_widths[2], 10, str(row["location"])[:10], border=1)
            pdf.cell(col_widths[3], 10, str(row["weight"]), border=1)
            pdf.cell(col_widths[4], 10, str(row["contact"]), border=1)
            pdf.cell(col_widths[5], 10, str(row["phone"]), border=1)
            pdf.cell(col_widths[6], 10, str(row["note"])[:15] if row["note"] else "", border=1)
            pdf.ln()
        pdf.output(filename)

    # ====================== UI 页面：AI 助手 ======================
    def show_ai_frame(self):
        self.clear_main_frame()
        self.current_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.current_frame.grid(row=0, column=0, sticky="nsew")
        self.current_frame.grid_rowconfigure(0, weight=1)
        self.current_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.current_frame, text="🤖 AI 智能助手", font=self.font_title, text_color=GLASS_TEXT_COLOR,
                     anchor="w").grid(row=0, column=0, pady=(0, 5), sticky="nw", padx=5)

        chat_frame = ctk.CTkFrame(self.current_frame, fg_color=GLASS_CARD_COLOR, corner_radius=20, border_width=1,
                                  border_color=GLASS_BORDER_COLOR)
        chat_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        chat_frame.grid_rowconfigure(0, weight=1)
        chat_frame.grid_columnconfigure(0, weight=1)

        self.chat_display = ctk.CTkTextbox(chat_frame, font=self.font_cn, wrap="word", state="disabled", border_width=0,
                                           fg_color="transparent")
        self.chat_display.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        self._update_chat_display("AI 助手已就绪。您可以勾选数据库分析，然后提问。", "System")

        control_frame = ctk.CTkFrame(self.current_frame, fg_color=GLASS_CARD_COLOR, corner_radius=18, height=90,
                                     border_width=1, border_color=GLASS_BORDER_COLOR)
        control_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=(10, 0))
        control_frame.grid_propagate(False)

        self.db_checkbox = ctk.CTkCheckBox(control_frame, text="📂 包含数据库内容", font=self.font_cn, checkbox_width=22,
                                           checkbox_height=22, corner_radius=7, border_color=GLASS_BORDER_COLOR,
                                           fg_color=ACCENT_PURPLE)
        self.db_checkbox.pack(side="left", padx=25)

        self.ai_input_entry = ctk.CTkEntry(control_frame, placeholder_text="输入问题，例如：本周哪个地点供应量最大？",
                                           font=self.font_cn, height=50, border_width=0, corner_radius=15,
                                           fg_color="#f0f0f2")
        self.ai_input_entry.pack(side="left", fill="x", expand=True, padx=15, pady=20)
        self.ai_input_entry.bind("<Return>", lambda e: self._on_send_ai_request())

        self.send_btn = ctk.CTkButton(control_frame, text="发送", command=self._on_send_ai_request,
                                      font=self.font_cn_bold, width=90, height=50, corner_radius=15,
                                      fg_color=ACCENT_PURPLE)
        self.send_btn.pack(side="left", padx=25)

        self.ai_is_working = False

    # ====================== AI 逻辑 ======================
    def _update_chat_display(self, text, sender="System"):
        self.chat_display.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M")

        if sender == "User":
            prefix = f"[{timestamp}] 👤 You:\n"
        elif sender == "AI":
            prefix = f"[{timestamp}] 🤖 AI:\n"
        else:
            prefix = "------------------\n"

        self.chat_display.insert("end", prefix)
        self.chat_display.insert("end", f"{text}\n\n")
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")

    def _on_send_ai_request(self):
        if self.ai_is_working: return

        user_text = self.ai_input_entry.get().strip()
        if not user_text: return

        self.ai_is_working = True
        self.send_btn.configure(text="思考中...", state="disabled")

        self._update_chat_display(user_text, "User")
        self.ai_input_entry.delete(0, "end")

        include_db = self.db_checkbox.get()
        db_context = ""

        if include_db:
            try:
                conn = sqlite3.connect(self.db_name)
                df = pd.read_sql_query("SELECT * FROM records", conn)
                if not df.empty:
                    db_context = f"\n\n[数据库记录 CSV]:\n{df.tail(100).to_csv(index=False)}\n"
                else:
                    db_context = "\n[数据库为空]\n"
            except Exception as e:
                self._update_chat_display(f"读取数据库失败: {e}", "System")
                self.ai_is_working = False
                self.send_btn.configure(text="发送", state="normal")
                return
            finally:
                if "conn" in locals(): conn.close()

        system_prompt = "你是一个数据分析师，专注于菠萝皮回收业务。请根据数据回答。"
        full_prompt = db_context + "\n问题: " + user_text

        thread = threading.Thread(target=self._call_zhipu_api, args=(system_prompt, full_prompt))
        thread.start()

    def _call_zhipu_api(self, system_prompt, user_prompt):
        try:
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {ZHIPU_API_KEY}"}
            payload = {"model": ZHIPU_MODEL, "messages": [{"role": "system", "content": system_prompt},
                                                          {"role": "user", "content": user_prompt}]}
            response = requests.post(ZHIPU_API_URL, headers=headers, json=payload, timeout=60)

            if response.status_code == 200:
                result = response.json()
                answer = result.get("choices", [{}])[0].get("message", {}).get("content", "无回复")
                self.after(0, lambda: self._update_chat_display(answer, "AI"))
            else:
                self.after(0, lambda: self._update_chat_display(f"API错误: {response.text}", "System"))
        except Exception as e:
            self.after(0, lambda: self._update_chat_display(f"发生错误: {e}", "System"))
        finally:
            self.after(0, self._reset_ai_ui)

    def _reset_ai_ui(self):
        self.ai_is_working = False
        self.send_btn.configure(text="发送", state="normal")
        self.ai_input_entry.focus()


if __name__ == "__main__":
    app = App()
    app.mainloop()