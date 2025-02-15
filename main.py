import json
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from filament import Filament, FilamentManager
from model import Model, ModelManager


class App(ttk.Window):
    def __init__(self):
        super().__init__(themename="minty")
        self.title("3D打印耗材管理系统 v3.0")
        self.geometry("1780x780")

        # 初始化数据管理
        self.filament_manager = FilamentManager()
        self.model_manager = ModelManager()

        # 创建界面组件
        self.create_widgets()

        # 将刷新操作放在组件创建之后
        self.refresh_filaments()
        self.refresh_models()

    def refresh_filaments(self):
        """刷新耗材列表"""
        self.filament_tree.delete(*self.filament_tree.get_children())
        for f in self.filament_manager.filaments:
            self.filament_tree.insert("", END, text=f.name, values=(
                f.category,
                f"{f.total_price:.2f}",
                f"{f.price:.4f}",
                f.initial_amount,
                f.remaining
            ))

    def create_widgets(self):
        """创建主界面布局"""
        # ================= 左侧耗材管理面板 =================
        left_frame = ttk.Labelframe(self, text=" 耗材管理 ", bootstyle=INFO)
        left_frame.pack(side=LEFT, fill=Y, padx=10, pady=10)

        # 耗材列表（保持不变）
        self.filament_tree = ttk.Treeview(
            left_frame,
            columns=("category", "total_price", "price_per_g", "initial", "remaining"),
            show="tree headings",
            height=15
        )
        # 配置列（保持不变）
        columns = [
            ("#0", "耗材名称", 200, W),
            ("category", "种类", 120, W),
            ("total_price", "总价(元)", 100, CENTER),
            ("price_per_g", "单价(元/克)", 120, CENTER),
            ("initial", "总量(g)", 100, CENTER),
            ("remaining", "剩余(g)", 100, CENTER)
        ]
        for col_id, text, width, anchor in columns:
            self.filament_tree.heading(col_id, text=text, anchor=anchor)
            self.filament_tree.column(col_id, width=width, anchor=anchor)
        self.filament_tree.pack(fill=X)

        # 操作按钮（保持不变）
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=X, pady=5)
        ttk.Button(btn_frame, text="添加耗材", command=self.show_add_filament,
                   bootstyle=SUCCESS).pack(side=LEFT, expand=True, padx=2)
        ttk.Button(btn_frame, text="编辑耗材", command=self.show_edit_filament,
                   bootstyle=WARNING).pack(side=LEFT, expand=True, padx=2)
        ttk.Button(btn_frame, text="删除耗材", command=self.delete_filament,
                   bootstyle=DANGER).pack(side=LEFT, expand=True, padx=2)

        # ================= 右侧模型管理面板 =================
        right_frame = ttk.Labelframe(self, text=" 模型管理 ", bootstyle=WARNING)
        right_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=10, pady=10)

        # 模型列表（关键修改部分）
        self.model_tree = ttk.Treeview(
            right_frame,
            columns=("materials", "quantity", "total", "unit"),
            show="tree headings",
            height=15,
            style="Custom.Treeview"
        )

        # 配置自定义样式
        style = ttk.Style()
        style.configure("Custom.Treeview", font=('Microsoft YaHei', 10), rowheight=28)
        style.configure("Custom.Treeview.Heading", font=('Microsoft YaHei', 10, 'bold'))
        style.map("Custom.Treeview", background=[("selected", "#e0f0ff")])

        # +++ 新增编辑对话框控件的样式 +++
        style.configure("Edit.TEntry", padding=5)  # 输入框内边距
        style.configure("Edit.TCombobox", padding=3)  # 下拉框内边距
        # ++++++++++++++++++++++++++++++++

        # 配置列（新增unit列）
        columns = [
            ("#0", "模型名称", 280, W),
            ("materials", "使用耗材", 220, W),
            ("quantity", "数量", 100, CENTER),
            ("total", "总成本(元)", 120, CENTER),
            ("unit", "单价(元)", 120, CENTER)
        ]
        for col_id, text, width, anchor in columns:
            self.model_tree.heading(col_id, text=text, anchor=anchor)
            self.model_tree.column(col_id, width=width, anchor=anchor)

        # 配置层级样式
        self.model_tree.tag_configure("parent", font=('Microsoft YaHei', 10, 'bold'))
        self.model_tree.tag_configure("child",
                                      font=('Microsoft YaHei', 9),
                                      background="#f8f8f8",
                                      foreground="#666666")

        self.model_tree.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # 操作按钮（添加编辑按钮）
        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(fill=X, pady=5)
        ttk.Button(btn_frame, text="添加模型", command=self.show_add_model,
                   bootstyle=SUCCESS).pack(side=LEFT, expand=True, padx=2)
        ttk.Button(btn_frame, text="编辑模型", command=self.show_edit_model,  # 新增
                   bootstyle=WARNING).pack(side=LEFT, expand=True, padx=2)
        ttk.Button(btn_frame, text="删除模型", command=self.delete_model,
                   bootstyle=DANGER).pack(side=LEFT, expand=True, padx=2)
        ttk.Button(btn_frame, text="执行打印", command=self.use_model,
                   bootstyle=INFO).pack(side=LEFT, expand=True, padx=2)

    def refresh_models(self):
        """刷新模型列表（支持多耗材展开显示）"""
        self.model_tree.delete(*self.model_tree.get_children())

        for m in self.model_manager.models:
            try:
                total_weight = 0  # 初始化总重量
                total_unit_cost = 0  # 初始化总单价

                # 插入父项（模型基本信息）
                parent = self.model_tree.insert(
                    "", END,
                    text=m.name,
                    values=(
                        f"{len(m.materials)}种耗材",  # 显示耗材数量
                        m.quantity,
                        self._calculate_total_cost(m),  # 总成本（每个耗材的成本累加）
                        ""  # 单价列留空
                    ),
                    open=False  # 默认折叠状态
                )

                # 插入子项（耗材详情）
                for mat in m.materials:
                    filament = self.filament_manager.find_filament(mat["filament"])
                    if filament:
                        material_cost = filament.price * mat["weight"]  # 单个耗材的成本
                        total_weight += mat["weight"]  # 累加耗材重量
                        total_unit_cost += material_cost / m.quantity  # 累加每个模型单位的耗材成本

                        self.model_tree.insert(
                            parent, END,
                            text="→ " + mat["filament"],
                            values=(
                                f"{mat['weight']}g",  # 显示耗材重量
                                1,  # 单耗材数量固定为1
                                f"{material_cost:.2f}",  # 显示单个耗材成本
                                f"{filament.price:.2f}"  # 显示单价
                            ),
                            tags=("child",)  # 添加标签用于样式控制
                        )

                # 更新父项（模型）中的"使用耗材"和"单价"信息
                self.model_tree.item(parent, values=(
                    f"{total_weight:.2f}g",  # 显示所有耗材的总重量
                    m.quantity,
                    f"{total_unit_cost * m.quantity:.2f}",  # 更新总成本
                    f"{total_unit_cost:.2f}"  # 更新总单价（所有子项单价的总和）
                ))

            except Exception as e:
                print(f"加载模型 {m.name} 出错: {str(e)}")

    def _calculate_total_cost(self, model):
        """计算模型总成本"""
        total = 0
        for mat in model.materials:
            filament = self.filament_manager.find_filament(mat["filament"])
            if filament:
                total += filament.price * mat["weight"] * model.quantity
        return f"{total:.2f}"

    # ------------------ 功能弹窗 ------------------
    def show_add_filament(self):
        """显示添加耗材对话框"""
        dialog = ttk.Toplevel(title="添加耗材")
        dialog.geometry("320x280")

        # 输入字段
        fields = [
            ("名称:", ttk.Entry(dialog)),
            ("种类:", ttk.Combobox(dialog, values=["PLA", "ABS", "PETG", "TPU", "其他"])),
            ("总价(元):", ttk.Entry(dialog)),
            ("总量(g):", ttk.Entry(dialog))
        ]

        for label, widget in fields:
            ttk.Label(dialog, text=label).pack(pady=2)
            widget.pack(fill=X, padx=10)

        name_entry, category_combo, price_entry, amount_entry = [w for _, w in fields]

        def on_submit():
            try:
                filament = Filament(
                    name=name_entry.get(),
                    category=category_combo.get(),
                    total_price=float(price_entry.get()),
                    initial_amount=int(amount_entry.get())
                )
                self.filament_manager.add_filament(filament)
                self.refresh_filaments()
                dialog.destroy()
            except ValueError as e:
                messagebox.showerror("错误", f"输入无效: {str(e)}")

        ttk.Button(dialog, text="提交", command=on_submit, bootstyle=SUCCESS).pack(pady=10)

    def show_edit_filament(self):
        """显示编辑耗材对话框（带原始数据）"""
        if not (selected := self.filament_tree.selection()):
            messagebox.showwarning("提示", "请先选择要编辑的耗材！")
            return

        name = self.filament_tree.item(selected[0], "text")
        filament = self.filament_manager.find_filament(name)

        # 添加耗材存在性检查
        if not filament:
            messagebox.showerror("错误", "所选耗材不存在！")
            return

        dialog = ttk.Toplevel(title=f"编辑耗材 - {name}")
        dialog.geometry("360x360")

        # 创建带初始值的变量
        name_var = ttk.StringVar(value=filament.name)
        category_var = ttk.StringVar(value=filament.category)
        price_var = ttk.DoubleVar(value=filament.total_price)
        initial_var = ttk.DoubleVar(value=filament.initial_amount)
        remaining_var = ttk.DoubleVar(value=filament.remaining)

        # 输入字段配置
        fields = [
            ("名称:", ttk.Entry(dialog, textvariable=name_var)),
            ("种类:", ttk.Combobox(
                dialog,
                values=["PLA", "ABS", "PETG", "TPU", "其他"],
                textvariable=category_var
            )),
            ("总价(元):", ttk.Entry(dialog, textvariable=price_var)),
            ("总量(g):", ttk.Entry(dialog, textvariable=initial_var)),
            ("剩余(g):", ttk.Entry(dialog, textvariable=remaining_var))
        ]

        # 布局字段
        for label, widget in fields:
            ttk.Label(dialog, text=label).pack(pady=2)
            widget.pack(fill=X, padx=10, pady=2)

        def on_submit():
            try:
                # 获取并验证输入
                new_name = name_var.get().strip()
                new_category = category_var.get()
                new_price = float(price_var.get())
                new_initial = float(initial_var.get())
                new_remaining = float(remaining_var.get())

                # 数据验证
                if not new_name:
                    raise ValueError("名称不能为空")
                if new_price <= 0:
                    raise ValueError("总价必须大于0")
                if new_initial <= 0:
                    raise ValueError("总量必须大于0")
                if new_remaining < 0:
                    raise ValueError("剩余量不能为负数")

                # 转换为整数（支持小数输入）
                new_initial = int(round(new_initial))
                new_remaining = int(round(new_remaining))

                # 自动调整剩余量逻辑
                if filament.initial_amount > 0 and new_initial != filament.initial_amount:
                    ratio = filament.remaining / filament.initial_amount
                    adjusted_remaining = int(round(new_initial * ratio))
                    if new_remaining != adjusted_remaining:
                        if messagebox.askyesno("提示",
                                               f"总量变化将自动调整剩余量为{adjusted_remaining}g\n是否继续？"):
                            new_remaining = adjusted_remaining

                # 更新数据
                filament.name = new_name
                filament.category = new_category
                filament.total_price = new_price
                filament.initial_amount = new_initial
                filament.remaining = min(new_remaining, new_initial)  # 确保不超过总量

                self.filament_manager.save_data()
                self.refresh_filaments()
                dialog.destroy()
                messagebox.showinfo("成功", "耗材信息已更新！")

            except ValueError as e:
                messagebox.showerror("输入错误", f"无效输入：{str(e)}")
            except Exception as e:
                messagebox.showerror("错误", f"更新失败：{str(e)}")

        ttk.Button(dialog, text="保存修改", command=on_submit, bootstyle=SUCCESS).pack(pady=10)

    def show_add_model(self):
        """显示添加模型对话框（支持多耗材）"""
        dialog = ttk.Toplevel(title="添加模型")
        dialog.geometry("600x450")  # Adjusted size for better layout

        # 用于添加耗材行的区域 (将添加的耗材行放在这里)
        material_frame = ttk.Frame(dialog)
        material_frame.pack(fill=X, pady=10)

        # 初始的“添加耗材”行按钮
        def add_material_row():
            """添加耗材行（将输入框放在顶部）"""
            row_frame = ttk.Frame(material_frame)
            row_frame.pack(fill=X, pady=2)

            # 耗材选择框
            filament_combo = ttk.Combobox(row_frame, values=[f.name for f in self.filament_manager.filaments])
            filament_combo.pack(side=LEFT, padx=2, fill=X, expand=True)

            # 重量输入框
            weight_entry = ttk.Entry(row_frame)
            weight_entry.pack(side=LEFT, padx=2, fill=X, expand=True)

            # 删除按钮
            ttk.Button(row_frame, text="×", command=lambda: row_frame.destroy(),
                       bootstyle=DANGER, width=2).pack(side=LEFT)

        # 默认添加一个耗材行
        add_material_row()

        # 添加耗材按钮，点击时会增加新的输入框
        ttk.Button(dialog, text="+ 添加耗材", command=add_material_row,
                   bootstyle=SECONDARY).pack(anchor=W, pady=5)

        # 模型基本信息部分
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=X, pady=5)
        ttk.Label(main_frame, text="模型名称:").pack(side=LEFT)
        name_entry = ttk.Entry(main_frame)
        name_entry.pack(side=LEFT, fill=X, expand=True)

        ttk.Label(main_frame, text="单盘数量:").pack(side=LEFT, padx=10)
        quantity_entry = ttk.Entry(main_frame, width=8)
        quantity_entry.pack(side=LEFT)

        def on_submit():
            try:
                # 收集所有耗材数据
                material_list = []
                for row in material_frame.winfo_children():
                    # 获取每一行的耗材和重量
                    combo = row.winfo_children()[0]  # Combobox for filament
                    entry = row.winfo_children()[1]  # Entry for weight
                    filament_name = combo.get()
                    weight = float(entry.get())

                    if not filament_name or weight <= 0:
                        raise ValueError("耗材信息不完整")

                    material_list.append({
                        "filament": filament_name,
                        "weight": round(weight, 2)
                    })

                # 创建模型
                model = Model(
                    name=name_entry.get(),
                    materials=material_list,
                    quantity=int(quantity_entry.get())
                )
                self.model_manager.add_model(model)
                self.refresh_models()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("错误", f"输入无效: {str(e)}")

        ttk.Button(dialog, text="提交", command=on_submit, bootstyle=SUCCESS).pack(pady=10)

    def batch_calculate(self):
        """批量计算选中模型"""
        selected = self.model_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要计算的模型")
            return

        total_cost = 0
        details = []

        for item in selected:
            model_name = self.model_tree.item(item, "text")
            model = self.model_manager.find_model(model_name)

            for material in model.materials:
                filament = self.filament_manager.find_filament(material["filament"])
                if not filament:
                    continue

                cost = filament.price * material["weight"] * model.quantity
                total_cost += cost
                details.append(
                    f"{model.name}: {material['filament']} "
                    f"{material['weight']}g × {model.quantity}个 = {cost:.2f}元"
                )

        report = "\n".join(details) + f"\n\n总计成本: {total_cost:.2f}元"
        messagebox.showinfo("批量计算结果", report)
    # ------------------ 操作功能 ------------------
    def delete_filament(self):
        """删除选中耗材"""
        if selected := self.filament_tree.selection():
            name = self.filament_tree.item(selected[0], "text")
            if messagebox.askyesno("确认", f"确定删除耗材 {name} 吗？"):
                self.filament_manager.filaments = [
                    f for f in self.filament_manager.filaments if f.name != name
                ]
                self.filament_manager.save_data()
                self.refresh_filaments()
        else:
            messagebox.showwarning("提示", "请先选择要删除的耗材！")

    def delete_model(self):
        """删除选中模型"""
        if selected := self.model_tree.selection():
            name = self.model_tree.item(selected[0], "text")
            if messagebox.askyesno("确认", f"确定删除模型 {name} 吗？"):
                self.model_manager.models = [
                    m for m in self.model_manager.models if m.name != name
                ]
                self.model_manager.save_data()
                self.refresh_models()
        else:
            messagebox.showwarning("提示", "请先选择要删除的模型！")

    def use_model(self):
        """执行打印操作（支持多耗材）"""
        if not (selected := self.model_tree.selection()):
            messagebox.showwarning("提示", "请先选择要使用的模型！")
            return

        model_name = self.model_tree.item(selected[0], "text")
        model = self.model_manager.find_model(model_name)

        # 检查所有耗材是否足够
        required = {}
        for material in model.materials:
            filament = self.filament_manager.find_filament(material["filament"])
            if not filament:
                messagebox.showerror("错误", f"耗材 {material['filament']} 不存在！")
                return

            needed = material["weight"] * model.quantity
            if filament.remaining < needed:
                messagebox.showerror("错误",
                                     f"{material['filament']} 需要 {needed}g\n当前剩余: {filament.remaining}g")
                return

            required[filament] = needed  # 存储需要扣除的量

        # 执行扣除
        for filament, amount in required.items():
            filament.remaining -= amount

        self.filament_manager.save_data()
        self.refresh_filaments()

        # 生成报告
        report = "\n".join([f"{k.name}: 使用 {v}g" for k, v in required.items()])
        messagebox.showinfo("打印成功",
                            f"已成功打印 {model.quantity} 个 {model.name}\n{report}")

    def show_edit_model(self):
        """显示编辑模型对话框"""
        if not (selected := self.model_tree.selection()):
            messagebox.showwarning("提示", "请先选择要编辑的模型！")
            return

        model_name = self.model_tree.item(selected[0], "text")
        model = self.model_manager.find_model(model_name)

        dialog = ttk.Toplevel(title=f"编辑模型 - {model_name}")
        dialog.geometry("600x450")

        # 模型基本信息
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=X, pady=5)
        ttk.Label(main_frame, text="模型名称:").pack(side=LEFT)
        name_entry = ttk.Entry(main_frame)
        name_entry.insert(0, model.name)
        name_entry.pack(side=LEFT, fill=X, expand=True)

        ttk.Label(main_frame, text="单盘数量:").pack(side=LEFT, padx=10)
        quantity_entry = ttk.Entry(main_frame, width=8)
        quantity_entry.insert(0, str(model.quantity))
        quantity_entry.pack(side=LEFT)

        # 耗材编辑表格
        columns = [("filament", "耗材名称", 150), ("weight", "单件重量(g)", 100)]
        tree = ttk.Treeview(dialog, columns=[c[0] for c in columns], show="headings", height=4)
        for col_id, text, width in columns:
            tree.heading(col_id, text=text)
            tree.column(col_id, width=width, anchor=CENTER)
        tree.pack(pady=5, fill=X)

        materials = []  # 存储所有输入行

        def add_material_row(mat_data=None):
            """添加耗材行（带初始数据）"""
            row_frame = ttk.Frame(dialog)
            row_frame.pack(fill=X, pady=2)

            # 耗材选择
            filament_combo = ttk.Combobox(row_frame, values=[f.name for f in self.filament_manager.filaments])
            filament_combo.pack(side=LEFT, padx=2, fill=X, expand=True)
            if mat_data:
                filament_combo.set(mat_data["filament"])

            # 重量输入
            weight_entry = ttk.Entry(row_frame)
            weight_entry.pack(side=LEFT, padx=2, fill=X, expand=True)
            if mat_data:
                weight_entry.insert(0, str(mat_data["weight"]))

            # 删除按钮
            ttk.Button(row_frame, text="×", command=lambda: row_frame.destroy(),
                       bootstyle=DANGER, width=2).pack(side=LEFT)

            materials.append((filament_combo, weight_entry))

        # 加载现有耗材数据
        for mat in model.materials:
            add_material_row(mat)

        # 添加耗材按钮
        ttk.Button(dialog, text="+ 添加耗材", command=lambda: add_material_row(),
                   bootstyle=SECONDARY).pack(anchor=W)

        def on_submit():
            try:
                # 收集耗材数据
                material_list = []
                for combo, entry in materials:
                    filament_name = combo.get()
                    weight = float(entry.get())
                    if not filament_name or weight <= 0:
                        raise ValueError("耗材信息不完整")
                    material_list.append({
                        "filament": filament_name,
                        "weight": round(weight, 2)
                    })

                # 更新模型
                model.name = name_entry.get()
                model.quantity = int(quantity_entry.get())
                model.materials = material_list

                self.model_manager.save_data()
                self.refresh_models()
                dialog.destroy()
                messagebox.showinfo("成功", "模型信息已更新！")
            except Exception as e:
                messagebox.showerror("错误", f"输入无效: {str(e)}")

        ttk.Button(dialog, text="保存修改", command=on_submit, bootstyle=SUCCESS).pack(pady=10)

if __name__ == "__main__":
    app = App()
    app.mainloop()
