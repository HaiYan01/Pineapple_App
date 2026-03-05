import os
import sqlite3
from datetime import datetime
from tkinter import filedialog, messagebox

import customtkinter as ctk
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from fpdf import FPDF
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

matplotlib.use("TkAgg")

# ====================== 数据库路径（固定在 Documents） ======================
home_dir = os.path.expanduser("~")
db_dir = os.path.join(home_dir, "Documents")
os.makedirs(db_dir, exist_ok=True)
DB_PATH = os.path.join(db_dir, "pineapple_data.db")

# ====================== 外观设置 ======================
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 窗口标题
        self.title("菠萝皮来源智能登记系统 For Mac")
        self.geometry("1000x650")
        self.minsize(900, 550)

        # 字体（Mac 用苹方）
        self.font_cn = ctk.CTkFont(family="PingFang SC", size=14)
        self.font_cn_title = ctk.CTkFont(family="PingFang SC", size=20, weight="bold")

        # 数据库路径
        self.db_name = DB_PATH
        self.init_db()

        # 布局
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # 侧边栏
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(7, weight=1)

        self.logo_label = ctk.CTkLabel(
            self.sidebar, text="菠萝皮管理", font=self.font_cn_title
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # 提示用户数据库位置
        self.db_info_label = ctk.CTkLabel(
            self.sidebar,
            text=f"数据库存放位置:\n{self.db_name}",
            font=self.font_cn,
            wraplength=180,
        )
        self.db_info_label.grid(row=1, column=0, padx=20, pady=10)

        # 按钮
        self.btn_create = ctk.CTkButton(
            self.sidebar, text="📝 新增登记", command=self.show_create_frame, font=self.font_cn
        )
        self.btn_create.grid(row=2, column=0, padx=20, pady=10)

        self.btn_view = ctk.CTkButton(
            self.sidebar, text="📊 查看数据", command=self.show_view_frame, font=self.font_cn
        )
        self.btn_view.grid(row=3, column=0, padx=20, pady=10)

        self.btn_stats = ctk.CTkButton(
            self.sidebar, text="📈 数据统计", command=self.show_stats_frame, font=self.font_cn
        )
        self.btn_stats.grid(row=4, column=0, padx=20, pady=10)

        self.btn_export = ctk.CTkButton(
            self.sidebar, text="📤 导出报表", command=self.export_menu, font=self.font_cn
        )
        self.btn_export.grid(row=5, column=0, padx=20, pady=10)

        # 主内容区域
        self.main_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.current_frame = None
        self.search_entry = None

        # 默认显示列表
        self.show_view_frame()

    # ====================== 数据库初始化 ======================
    def init_db(self):
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS records
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    location TEXT NOT NULL,
                    weight REAL NOT NULL,
                    contact TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    note TEXT
                )
                """
            )
            conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("数据库错误", f"初始化数据库失败: {e}")
        finally:
            if "conn" in locals():
                conn.close()

    def clear_main_frame(self):
        if self.current_frame:
            self.current_frame.destroy()
            self.current_frame = None

    # ====================== 新增登记 ======================
    def show_create_frame(self):
        self.clear_main_frame()
        self.current_frame = ctk.CTkFrame(self.main_frame)
        self.current_frame.grid(row=0, column=0, sticky="nsew")

        scroll_frame = ctk.CTkScrollableFrame(self.current_frame, label_text="新增来源登记")
        scroll_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 0))

        form_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        form_frame.pack(pady=10, padx=50, fill="x")

        self.entry_date = ctk.CTkEntry(form_frame, placeholder_text="日期 (YYYY-MM-DD)", font=self.font_cn)
        self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.entry_date.pack(pady=10, fill="x")

        self.entry_location = ctk.CTkEntry(form_frame, placeholder_text="来源地点", font=self.font_cn)
        self.entry_location.pack(pady=10, fill="x")

        self.entry_weight = ctk.CTkEntry(form_frame, placeholder_text="重量（kg）", font=self.font_cn)
        self.entry_weight.pack(pady=10, fill="x")

        self.entry_contact = ctk.CTkEntry(form_frame, placeholder_text="联系人姓名", font=self.font_cn)
        self.entry_contact.pack(pady=10, fill="x")

        self.entry_phone = ctk.CTkEntry(form_frame, placeholder_text="联系电话", font=self.font_cn)
        self.entry_phone.pack(pady=10, fill="x")

        self.entry_note = ctk.CTkTextbox(form_frame, height=100, font=("PingFang SC", 12))
        self.entry_note.pack(pady=10, fill="x")

        bottom_frame = ctk.CTkFrame(self.current_frame, height=80)
        bottom_frame.grid(row=1, column=0, sticky="ew")

        save_btn = ctk.CTkButton(bottom_frame, text="💾 保存", command=self.submit_data, height=40, font=self.font_cn)
        save_btn.pack(side="left", padx=20, pady=20, fill="x", expand=True)

        submit_btn = ctk.CTkButton(bottom_frame, text="✅ 提交", command=self.submit_data, height=40, font=self.font_cn)
        submit_btn.pack(side="left", padx=20, pady=20, fill="x", expand=True)

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
                if weight <= 0:
                    raise ValueError("重量必须大于0")
            except ValueError:
                messagebox.showerror("错误", "重量必须是正数")
                return

            if not all([date, location, contact, phone]):
                messagebox.showwarning("提示", "请填写完整必要信息（日期、地点、联系人、电话）")
                return

            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute(
                "INSERT INTO records (date, location, weight, contact, phone, note) VALUES (?, ?, ?, ?, ?, ?)",
                (date, location, weight, contact, phone, note),
            )
            conn.commit()
            messagebox.showinfo("成功", "✅ 数据已保存！")
            self.show_view_frame()
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}")
        finally:
            if "conn" in locals():
                conn.close()

    # ====================== 查看记录 ======================

    def show_view_frame(self):
        self.clear_main_frame()
        self.current_frame = ctk.CTkScrollableFrame(self.main_frame, label_text="所有登记记录")
        self.current_frame.grid(row=0, column=0, sticky="nsew")

        # 搜索栏
        search_frame = ctk.CTkFrame(self.current_frame, fg_color="transparent")
        search_frame.pack(fill="x", pady=10)

        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="输入关键词搜索（日期/地点/联系人/电话）",
            font=self.font_cn
        )
        self.search_entry.pack(side="left", padx=10, fill="x", expand=True)

        ctk.CTkButton(
            search_frame,
            text="🔍 搜索",
            command=self.search_records,
            font=self.font_cn
        ).pack(side="left", padx=10)

        # 表头
        header_frame = ctk.CTkFrame(self.current_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=5)

        headers = ["编号", "日期", "地点", "重量", "联系人", "电话", "操作"]
        widths = [50, 100, 200, 80, 100, 120, 160]

        for h, w in zip(headers, widths):
            ctk.CTkLabel(
                header_frame,
                text=h,
                font=self.font_cn,
                width=w,
                anchor="w"
            ).pack(side="left", padx=5)

        # 加载数据
        try:
            conn = sqlite3.connect(self.db_name)
            df = pd.read_sql_query("SELECT * FROM records ORDER BY id DESC", conn)
        except Exception as e:
            messagebox.showerror("错误", f"加载数据失败: {e}")
            df = pd.DataFrame()
        finally:
            if "conn" in locals():
                conn.close()

        if df.empty:
            ctk.CTkLabel(self.current_frame, text="暂无记录", font=self.font_cn).pack(pady=20)
            return

        # 显示每条记录
        for _, row in df.iterrows():
            item_frame = ctk.CTkFrame(self.current_frame, fg_color=("gray90", "gray25"))
            item_frame.pack(fill="x", pady=2, padx=5)

            for val, w in zip(
                [row["id"], row["date"], row["location"], row["weight"], row["contact"], row["phone"]],
                widths[:-1]
            ):
                ctk.CTkLabel(item_frame, text=str(val), width=w, anchor="w", font=self.font_cn).pack(
                    side="left", padx=5
                )

            # 编辑按钮
            ctk.CTkButton(
                item_frame,
                text="✏ 编辑",
                width=70,
                command=lambda rid=row["id"]: self.edit_record(rid),
                font=self.font_cn
            ).pack(side="left", padx=5)

            # 删除按钮
            ctk.CTkButton(
                item_frame,
                text="❌ 删除",
                width=70,
                fg_color="red",
                hover_color="#aa0000",
                command=lambda rid=row["id"]: self.delete_record(rid),
                font=self.font_cn
            ).pack(side="left", padx=5)

    # ====================== 搜索功能 ======================
    def search_records(self):
        keyword = self.search_entry.get().strip()
        if not keyword:
            self.show_view_frame()
            return

        try:
            conn = sqlite3.connect(self.db_name)
            query = """
                SELECT * FROM records
                WHERE date LIKE ? OR location LIKE ? OR contact LIKE ? OR phone LIKE ?
                ORDER BY id DESC
            """
            like_kw = f"%{keyword}%"
            df = pd.read_sql_query(query, conn, params=(like_kw, like_kw, like_kw, like_kw))
        except Exception as e:
            messagebox.showerror("错误", f"搜索失败: {e}")
            return
        finally:
            if "conn" in locals():
                conn.close()

        self.clear_main_frame()
        self.current_frame = ctk.CTkScrollableFrame(
            self.main_frame, label_text=f"搜索结果：{keyword}"
        )
        self.current_frame.grid(row=0, column=0, sticky="nsew")

        if df.empty:
            ctk.CTkLabel(self.current_frame, text="没有找到匹配记录", font=self.font_cn).pack(pady=20)
            return

        for _, row in df.iterrows():
            item_frame = ctk.CTkFrame(self.current_frame, fg_color=("gray90", "gray25"))
            item_frame.pack(fill="x", pady=2, padx=5)

            for val in [
                row["id"], row["date"], row["location"], row["weight"], row["contact"], row["phone"]
            ]:
                ctk.CTkLabel(item_frame, text=str(val), width=120, anchor="w", font=self.font_cn).pack(
                    side="left", padx=5
                )

            ctk.CTkButton(
                item_frame,
                text="✏ 编辑",
                width=70,
                command=lambda rid=row["id"]: self.edit_record(rid),
                font=self.font_cn
            ).pack(side="left", padx=5)

            ctk.CTkButton(
                item_frame,
                text="❌ 删除",
                width=70,
                fg_color="red",
                hover_color="#aa0000",
                command=lambda rid=row["id"]: self.delete_record(rid),
                font=self.font_cn
            ).pack(side="left", padx=5)

    # ====================== 删除记录 ======================
    def delete_record(self, record_id):
        if not messagebox.askyesno("确认删除", "确定要删除这条记录吗？"):
            return

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
            if "conn" in locals():
                conn.close()

    # ====================== 编辑记录 ======================
    def edit_record(self, record_id):
        try:
            conn = sqlite3.connect(self.db_name)
            df = pd.read_sql_query("SELECT * FROM records WHERE id=?", conn, params=(record_id,))
        except Exception as e:
            messagebox.showerror("错误", f"读取记录失败: {e}")
            return
        finally:
            if "conn" in locals():
                conn.close()

        if df.empty:
            messagebox.showerror("错误", "未找到记录")
            return

        row = df.iloc[0]

        edit_win = ctk.CTkToplevel(self)
        edit_win.title(f"编辑记录 - ID {record_id}")
        edit_win.geometry("400x550")

        entries = {}
        labels = {
            "date": "日期 (YYYY-MM-DD)",
            "location": "来源地点",
            "weight": "重量（kg）",
            "contact": "联系人",
            "phone": "联系电话",
            "note": "备注",
        }

        for field in ["date", "location", "weight", "contact", "phone", "note"]:
            ctk.CTkLabel(edit_win, text=labels[field], font=self.font_cn).pack(pady=(10, 0))
            entry = ctk.CTkEntry(edit_win, font=self.font_cn)
            entry.insert(0, str(row[field]))
            entry.pack(pady=5, fill="x", padx=20)
            entries[field] = entry

        def save_edit():
            try:
                new_date = entries["date"].get().strip()
                new_location = entries["location"].get().strip()
                new_weight = float(entries["weight"].get().strip())
                new_contact = entries["contact"].get().strip()
                new_phone = entries["phone"].get().strip()
                new_note = entries["note"].get().strip()

                if new_weight <= 0:
                    raise ValueError("重量必须大于0")

                conn = sqlite3.connect(self.db_name)
                c = conn.cursor()
                c.execute(
                    """
                    UPDATE records
                    SET date=?, location=?, weight=?, contact=?, phone=?, note=?
                    WHERE id=?
                    """,
                    (
                        new_date,
                        new_location,
                        new_weight,
                        new_contact,
                        new_phone,
                        new_note,
                        record_id,
                    ),
                )
                conn.commit()
                messagebox.showinfo("成功", "记录已更新")
                edit_win.destroy()
                self.show_view_frame()
            except Exception as e:
                messagebox.showerror("错误", f"更新失败: {e}")
            finally:
                if "conn" in locals():
                    conn.close()

        ctk.CTkButton(edit_win, text="保存修改", command=save_edit, font=self.font_cn).pack(pady=20)

    # ====================== 数据统计 ======================
    def show_stats_frame(self):
        self.clear_main_frame()
        self.current_frame = ctk.CTkFrame(self.main_frame)
        self.current_frame.grid(row=0, column=0, sticky="nsew")
        self.current_frame.grid_rowconfigure(1, weight=1)
        self.current_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            self.current_frame,
            text="数据统计与图表",
            font=self.font_cn_title,
        )
        title_label.grid(row=0, column=0, pady=10)

        try:
            conn = sqlite3.connect(self.db_name)
            df = pd.read_sql_query("SELECT * FROM records", conn)
        except Exception as e:
            messagebox.showerror("错误", f"加载数据失败: {e}")
            return
        finally:
            if "conn" in locals():
                conn.close()

        if df.empty:
            ctk.CTkLabel(self.current_frame, text="暂无数据，无法生成统计图表", font=self.font_cn).grid(
                row=1, column=0, pady=20
            )
            return

        df["date"] = pd.to_datetime(df["date"]).dt.date

        total_weight = df["weight"].sum()
        total_records = len(df)
        unique_locations = df["location"].nunique()

        summary_frame = ctk.CTkFrame(self.current_frame)
        summary_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 5))

        ctk.CTkLabel(summary_frame, text=f"总记录数：{total_records}", font=self.font_cn).pack(
            side="left", padx=20, pady=10
        )
        ctk.CTkLabel(summary_frame, text=f"总重量：{total_weight:.2f} kg", font=self.font_cn).pack(
            side="left", padx=20, pady=10
        )
        ctk.CTkLabel(summary_frame, text=f"来源地点数：{unique_locations}", font=self.font_cn).pack(
            side="left", padx=20, pady=10
        )

        chart_frame = ctk.CTkFrame(self.current_frame)
        chart_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        self.current_frame.grid_rowconfigure(2, weight=1)

        df_daily = df.groupby("date")["weight"].sum().reset_index()
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        ax.bar(df_daily["date"].astype(str), df_daily["weight"], color="#4e79a7")
        ax.set_xlabel("日期")
        ax.set_ylabel("总重量 (kg)")
        ax.set_title("每日菠萝皮来源重量统计")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # ====================== 导出菜单 ======================
    def export_menu(self):
        export_win = ctk.CTkToplevel(self)
        export_win.title("导出数据")
        export_win.geometry("300x250")

        ctk.CTkLabel(
            export_win,
            text="请选择导出格式",
            font=self.font_cn_title,
        ).pack(pady=20)

        ctk.CTkButton(
            export_win,
            text="导出为 Excel (.xlsx)",
            command=lambda: self.export_data("excel", export_win),
            font=self.font_cn,
        ).pack(pady=10, padx=20, fill="x")

        ctk.CTkButton(
            export_win,
            text="导出为 CSV (.csv)",
            command=lambda: self.export_data("csv", export_win),
            font=self.font_cn,
        ).pack(pady=10, padx=20, fill="x")

        ctk.CTkButton(
            export_win,
            text="导出为 PDF (.pdf)",
            command=lambda: self.export_data("pdf", export_win),
            font=self.font_cn,
        ).pack(pady=10, padx=20, fill="x")

    # ====================== 导出实现 ======================
    def export_data(self, file_type, window):
        try:
            conn = sqlite3.connect(self.db_name)
            df = pd.read_sql_query("SELECT * FROM records ORDER BY id", conn)
        except Exception as e:
            messagebox.showerror("错误", f"读取数据失败: {e}")
            return
        finally:
            if "conn" in locals():
                conn.close()

        if df.empty:
            messagebox.showwarning("提示", "没有数据可导出")
            return

        ext_map = {"excel": "xlsx", "csv": "csv", "pdf": "pdf"}
        file_ext = ext_map[file_type]

        file_path = filedialog.asksaveasfilename(
            defaultextension=f".{file_ext}",
            filetypes=[
                (f"{file_ext.upper()} files", f"*.{file_ext}"),
                ("All files", "*.*"),
            ],
            initialfile=f"菠萝皮数据导出_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        )

        if not file_path:
            return

        try:
            if file_type == "excel":
                df.to_excel(file_path, index=False)
            elif file_type == "csv":
                df.to_csv(file_path, index=False, encoding="utf-8-sig")
            elif file_type == "pdf":
                self.create_pdf(df, file_path)

            messagebox.showinfo("成功", f"已成功导出至: {file_path}")
            window.destroy()
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {e}")

    # ====================== PDF 生成 ======================
    def create_pdf(self, df, filename):
        pdf = FPDF()
        pdf.add_page()

        font_name = "Arial"

        # 尝试加载中文字体
        common_fonts = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
        ]
        for f in common_fonts:
            if os.path.exists(f):
                try:
                    pdf.add_font("PingFang", "", f, uni=True)
                    pdf.add_font("PingFang", "B", f, uni=True)
                    font_name = "PingFang"
                except:
                    pass
                break

        pdf.set_font(font_name, size=12)

        pdf.set_font(font_name, "B", 16)
        pdf.cell(200, 10, txt="Pineapple Sources Report", ln=1, align="C")
        pdf.ln(10)

        headers = ["ID", "Date", "Location", "Weight", "Contact", "Phone", "Note"]
        col_widths = [15, 30, 40, 20, 30, 30, 55]

        pdf.set_font(font_name, size=12)
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, txt=header, border=1)
        pdf.ln()

        pdf.set_font(font_name, size=9)
        for _, row in df.iterrows():
            row_data = [
                str(row["id"]),
                str(row["date"]),
                str(row["location"]),
                str(row["weight"]),
                str(row["contact"]),
                str(row["phone"]),
                str(row["note"]) if row["note"] else "",
            ]

            row_data = [x if len(x) < 30 else x[:27] + "..." for x in row_data]

            for i, item in enumerate(row_data):
                pdf.cell(col_widths[i], 10, txt=item, border=1)
            pdf.ln()

        pdf.output(filename)


if __name__ == "__main__":
    app = App()
    app.mainloop()
