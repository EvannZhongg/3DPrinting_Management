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
        self.geometry("1380x780")

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

        # 耗材列表
        self.filament_tree = ttk.Treeview(
            left_frame,
            columns=("category", "total_price", "price_per_g", "initial", "remaining"),
            show="tree headings",
            height=15
        )
        # 配置列
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

        # 操作按钮
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

        # 模型列表
        self.model_tree = ttk.Treeview(
            right_frame,
            columns=("filament_weight", "quantity", "total"),
            show="tree headings",
            height=15
        )
        # 配置列
        self.model_tree.heading("#0", text="模型名称", anchor=W)
        self.model_tree.heading("filament_weight", text="使用耗材及重量")  # 修改为“使用耗材及重量”
        self.model_tree.heading("quantity", text="单盘数量")
        self.model_tree.heading("total", text="总成本(元)")

        # 设置列宽
        self.model_tree.column("#0", width=250, anchor=W)
        self.model_tree.column("filament_weight", width=300, anchor=W)
        self.model_tree.column("quantity", width=100, anchor=CENTER)
        self.model_tree.column("total", width=120, anchor=CENTER)
        self.model_tree.pack(fill=BOTH, expand=True)

        # 操作按钮
        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(fill=X, pady=5)
        ttk.Button(btn_frame, text="添加模型", command=self.show_add_model,
                   bootstyle=SUCCESS).pack(side=LEFT, expand=True, padx=2)
        ttk.Button(btn_frame, text="删除模型", command=self.delete_model,
                   bootstyle=DANGER).pack(side=LEFT, expand=True, padx=2)
        ttk.Button(btn_frame, text="执行打印", command=self.use_model,
                   bootstyle=INFO).pack(side=LEFT, expand=True, padx=2)

    def refresh_models(self):
        """刷新模型列表（显示多耗材）"""
        self.model_tree.delete(*self.model_tree.get_children())
        print("当前模型数量:", len(self.model_manager.models))  # 调试输出

        for m in self.model_manager.models:
            # 构建耗材描述（添加异常处理）
            try:
                materials_desc = "\n".join([f"{mat['filament']} {mat['weight']}g"
                                            for mat in m.materials])

                # 计算成本（处理None值）
                total = 0
                for mat in m.materials:
                    filament = self.filament_manager.find_filament(mat["filament"])
                    if filament:
                        total += filament.price * mat["weight"]
                total *= m.quantity

                unit = total / m.quantity if m.quantity > 0 else 0

                # 插入数据（显式指定列）
                self.model_tree.insert(
                    "", END, text=m.name,
                    values=(
                        materials_desc,
                        m.quantity,
                        f"{total:.2f}",
                        f"{unit:.2f}"
                    )
                )
                print(f"插入模型: {m.name}")  # 调试输出
            except Exception as e:
                print(f"加载模型 {m.name} 出错: {str(e)}")

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
        dialog.geometry("600x400")

        # 耗材输入表格
        columns = [("filament", "耗材名称", 150), ("weight", "单件重量(g)", 100)]
        tree = ttk.Treeview(dialog, columns=[c[0] for c in columns], show="headings", height=4)
        for col_id, text, width in columns:
            tree.heading(col_id, text=text)
            tree.column(col_id, width=width, anchor=CENTER)
        tree.pack(pady=5, fill=X)

        # 添加耗材行
        def add_material():
            row_frame = ttk.Frame(dialog)
            row_frame.pack(fill=X, pady=2)

            filament_combo = ttk.Combobox(row_frame, values=[f.name for f in self.filament_manager.filaments])
            filament_combo.pack(side=LEFT, padx=2, fill=X, expand=True)

            weight_entry = ttk.Entry(row_frame)
            weight_entry.pack(side=LEFT, padx=2, fill=X, expand=True)

            ttk.Button(row_frame, text="×", command=lambda: row_frame.destroy(),
                       bootstyle=DANGER, width=2).pack(side=LEFT)

            materials.append((filament_combo, weight_entry))

        materials = []  # 存储所有输入行
        ttk.Button(dialog, text="+ 添加耗材", command=add_material,
                   bootstyle=SECONDARY).pack(anchor=W)

        # 其他字段
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
if __name__ == "__main__":
    app = App()
    app.mainloop()
