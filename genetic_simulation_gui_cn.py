import tkinter as tk
from tkinter import messagebox, filedialog, ttk, Toplevel, Label, Entry, Button, Text, Scrollbar, Frame, Listbox, LabelFrame
from genetic_simulation_cn import GeneticSimulationSystem
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

class GeneticSimulationGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("遗传学模拟系统")
        self.system = GeneticSimulationSystem()
        self.current_group = None
        self.figure = None
        self.canvas = None
        self.font = None
        self.create_widgets()
        self.populate_groups_list()
        self.log_output("=== 系统已启动 ===")
        self.set_default_command()

    def set_default_command(self):
        # 设置输入框默认内容
        self.command_entry.insert(0, "/help")

    def create_widgets(self):
        main_frame = Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.menu_frame = Frame(main_frame, width=250)
        self.menu_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.group_var = tk.StringVar()
        self.group_dropdown = ttk.Combobox(self.menu_frame, textvariable=self.group_var, values=[], state="readonly", width=25)
        self.group_dropdown.pack(pady=10)
        self.group_dropdown.bind("<<ComboboxSelected>>", self.on_group_select)

        buttons = [
            ("添加基因", self.add_gene),
            ("创建组别", self.create_group),
            ("运行模拟", self.run_simulation),
            ("切换交配模式", self.change_mode),
            ("显示详细信息", self.show_details),
            ("加载指令", self.load_commands),
            ("删除所选个体", self.delete_selected),
            ("添加基因组合", self.add_genotype)
        ]

        for text, command in buttons:
            Button(self.menu_frame, text=text, command=command).pack(fill=tk.X, pady=5, padx=10)

        help_button = Button(self.menu_frame, text="帮助", command=self.show_help)
        help_button.place(x=170, y=10)  # 放置在右上角

        self.content_frame = Frame(main_frame)
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.genes_frame = LabelFrame(self.content_frame, text="已定义基因")
        self.genes_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=10, pady=10)

        self.genes_listbox = Listbox(self.genes_frame, width=30, height=20)
        self.genes_listbox.pack(fill=tk.BOTH, expand=True)
        self.genes_scrollbar = Scrollbar(self.genes_frame, command=self.genes_listbox.yview)
        self.genes_listbox.config(yscrollcommand=self.genes_scrollbar.set)
        self.genes_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.members_frame = LabelFrame(self.content_frame, text="当前组别成员")
        self.members_frame.pack(fill=tk.BOTH, expand=True, side=tk.RIGHT, padx=10, pady=10)

        self.members_listbox = Listbox(self.members_frame, width=30, height=20)
        self.members_listbox.pack(fill=tk.BOTH, expand=True)
        self.members_scrollbar = Scrollbar(self.members_frame, command=self.members_listbox.yview)
        self.members_listbox.config(yscrollcommand=self.members_scrollbar.set)
        self.members_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.log_frame = LabelFrame(self.content_frame, text="运行日志")
        self.log_frame.pack(fill=tk.BOTH, expand=True, side=tk.BOTTOM, padx=10, pady=10)

        self.log_text = Text(self.log_frame, wrap=tk.WORD, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.scrollbar = Scrollbar(self.log_frame, command=self.log_text.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=self.scrollbar.set)

        self.command_frame = Frame(self.master)
        self.command_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=10)

        Label(self.command_frame, text="输入指令:").pack(side=tk.LEFT)
        self.command_entry = Entry(self.command_frame, width=50)
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.command_entry.bind("<Return>", self.execute_command)
        Button(self.command_frame, text="执行", command=self.execute_command).pack(side=tk.LEFT)

        self.chart_frame = LabelFrame(self.master, text="基因统计图表")
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.chart_canvas = None
        self.draw_initial_chart()

        # 设置中文字体
        self.font = FontProperties(fname=r"c:\windows\fonts\simsun.ttc", size=10)  # 宋体

    def on_group_select(self, event):
        group_name = self.group_var.get()
        if group_name != self.current_group:
            self.current_group = group_name
            self.display_group_members()
            self.populate_genes_list()
            self.update_chart()

    def populate_groups_list(self):
        groups = list(self.system.groups.keys())
        self.group_dropdown["values"] = groups
        if groups:
            self.group_dropdown.current(0)
            self.current_group = groups[0]
            self.populate_genes_list()
            self.display_group_members()
            self.log_output("已加载组别: " + groups[0])

    def populate_genes_list(self):
        self.genes_listbox.delete(0, tk.END)
        for gene_symbol, gene in self.system.genes.items():
            self.genes_listbox.insert(tk.END, f"基因 {gene_symbol}: 显性 {gene.dom_trait}, 隐性 {gene.rec_trait}")

    def display_group_members(self):
        self.members_listbox.delete(0, tk.END)
        if self.current_group:
            group = self.system.groups[self.current_group]
            members = group.current_generation
            member_counts = {}
            for member in members:
                member_counts[member] = member_counts.get(member, 0) + 1
            for member, count in member_counts.items():
                self.members_listbox.insert(tk.END, f"{member} × {count}")

    def add_gene(self):
        dialog = Toplevel(self.master)
        dialog.title("添加基因")
        entries = {}
        fields = ["显性基因", "隐性基因", "显性性状", "隐性性状"]

        for i, field in enumerate(fields):
            Label(dialog, text=field).grid(row=i, column=0)
            entries[field] = Entry(dialog)
            entries[field].grid(row=i, column=1)

        Button(dialog, text="提交", command=lambda: self.process_add_gene(
            entries["显性基因"].get(),
            entries["隐性基因"].get(),
            entries["显性性状"].get(),
            entries["隐性性状"].get(),
            dialog
        )).grid(row=len(fields), column=0, columnspan=2)

    def process_add_gene(self, dom, rec, dom_trait, rec_trait, dialog):
        try:
            self.system.process_command(f"/add {dom} {rec} {dom_trait} {rec_trait}")
            self.populate_genes_list()
            self.log_output(f"基因添加成功: {dom}/{rec}")
            dialog.destroy()
        except Exception as e:
            self.log_output(f"基因添加失败: {str(e)}")
            dialog.destroy()

    def create_group(self):
        dialog = Toplevel(self.master)
        dialog.title("创建组别")
        entry = Entry(dialog)
        entry.pack()
        Button(dialog, text="创建", command=lambda: self.process_create_group(entry.get(), dialog)).pack()

    def process_create_group(self, group_name, dialog):
        if not group_name:
            self.log_output("错误: 组别名称不能为空")
            dialog.destroy()
            return
        try:
            self.system.process_command(f"/create {group_name}")
            self.current_group = group_name
            self.populate_groups_list()
            self.log_output(f"组别创建成功: {group_name}")
            dialog.destroy()
        except Exception as e:
            self.log_output(f"组别创建失败: {str(e)}")
            dialog.destroy()

    def run_simulation(self):
        if not self.current_group:
            self.log_output("错误: 未选择组别")
            return
        try:
            response = self.system.process_command(f"/run {self.current_group}")
            self.log_output("模拟运行完成")
            self.display_group_members()
            self.update_chart()
        except Exception as e:
            self.log_output(f"模拟运行失败: {str(e)}")

    def change_mode(self):
        if not self.current_group:
            self.log_output("错误: 未选择组别")
            return

        def choose_mode(mode):
            try:
                self.system.process_command(f"/mode {self.current_group} {mode}")
                self.log_output(f"交配模式已切换为: {mode}")
            except Exception as e:
                self.log_output(f"交配模式切换失败: {str(e)}")
            dialog.destroy()

        dialog = Toplevel(self.master)
        dialog.title("切换交配模式")
        dialog.geometry("300x150")

        Label(dialog, text="请选择交配模式：").pack(pady=10)

        Button(dialog, text="随机交配 (random)", command=lambda: choose_mode("random")).pack(pady=5)
        Button(dialog, text="人工杂交 (cross)", command=lambda: choose_mode("cross")).pack(pady=5)

    def show_details(self):
        if not self.current_group:
            self.log_output("错误: 未选择组别")
            return
        try:
            stats = self.system.groups[self.current_group].get_statistics(self.system.genes, details=True)
            details = f"=== {self.current_group} 统计详情 ===\n\n"
            details += "基因型分布：\n"
            for geno, info in stats['genotypes'].items():
                details += f"  {geno}: {info['count']} ({info['ratio'] * 100:.2f}%)\n"

            details += "\n表型分布：\n"
            for pheno, info in stats['phenotypes'].items():
                details += f"  {pheno}: {info['count']} ({info['ratio'] * 100:.2f}%)\n"

            self.display_details_window(details)
        except Exception as e:
            self.log_output(f"获取详细信息失败: {str(e)}")

    def show_group_details(self):
        if not self.current_group:
            self.log_output("错误: 未选择组别")
            return
        try:
            stats = self.system.groups[self.current_group].get_statistics(self.system.genes, details=True)
            details = f"=== {self.current_group} 统计详情 ===\n\n"
            details += "基因型分布：\n"
            for geno, info in stats['genotypes'].items():
                details += f"  {geno}: {info['count']} ({info['ratio'] * 100:.2f}%)\n"

            details += "\n表型分布：\n"
            for pheno, info in stats['phenotypes'].items():
                details += f"  {pheno}: {info['count']} ({info['ratio'] * 100:.2f}%)\n"

            self.display_details_window(details)
        except Exception as e:
            self.log_output(f"获取详细信息失败: {str(e)}")

    def display_details_window(self, details):
        dialog = Toplevel(self.master)
        dialog.title("详细信息")
        text = Text(dialog, wrap=tk.WORD)
        text.insert(tk.END, details)
        text.pack(fill=tk.BOTH, expand=True)
        Button(dialog, text="关闭", command=dialog.destroy).pack()

    def load_commands(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            try:
                response = self.system.process_command(f"/load {file_path}")
                if response:
                    self.log_output(response)
                else:
                    self.log_output("指令加载成功")
            except Exception as e:
                self.log_output(f"指令加载失败: {str(e)}")

    def delete_selected(self):
        selected = self.members_listbox.curselection()
        if not selected:
            self.log_output("错误: 未选择要删除的个体")
            return
        member = self.members_listbox.get(selected[0]).split(" × ")[0]
        try:
            response = self.system.process_command(f"/change {self.current_group} {member} del 1")
            if response:
                self.log_output(response)
            else:
                self.log_output(f"成功删除个体: {member}")
            self.display_group_members()
        except Exception as e:
            self.log_output(f"删除个体失败: {str(e)}")

    def add_genotype(self):
        dialog = Toplevel(self.master)
        dialog.title("添加基因组合")
        entries = {}
        fields = ["基因型", "数量"]

        for i, field in enumerate(fields):
            Label(dialog, text=field).grid(row=i, column=0)
            entries[field] = Entry(dialog)
            entries[field].grid(row=i, column=1)

        Button(dialog, text="提交", command=lambda: self.process_add_genotype(
            entries["基因型"].get(),
            entries["数量"].get(),
            dialog
        )).grid(row=len(fields), column=0, columnspan=2)

    def process_add_genotype(self, genotype, amount, dialog):
        if not genotype or not amount:
            self.log_output("错误: 请输入完整的基因型和数量")
            dialog.destroy()
            return
        try:
            amount = int(amount)
            if amount <= 0:
                raise ValueError("数量必须大于0")
            response = self.system.process_command(f"/change {self.current_group} {genotype} add {amount}")
            if response:
                self.log_output(response)
            else:
                self.log_output(f"成功添加 {amount} 个个体到组别 {self.current_group}: {genotype}")
            self.display_group_members()
            dialog.destroy()
        except Exception as e:
            self.log_output(f"添加个体失败: {str(e)}")
            dialog.destroy()

    def draw_initial_chart(self):
        self.figure = Figure(figsize=(6, 4), dpi=100)
        self.subplot1 = self.figure.add_subplot(211)
        self.subplot2 = self.figure.add_subplot(212)
        self.subplot1.set_title("基因型分布", fontproperties=self.font)
        self.subplot2.set_title("表型分布", fontproperties=self.font)
        self.subplot1.set_ylabel("数量", fontproperties=self.font)
        self.subplot2.set_ylabel("数量", fontproperties=self.font)

        self.chart_canvas = FigureCanvasTkAgg(self.figure, master=self.chart_frame)
        self.chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.chart_canvas.draw()

    def update_chart(self):
        if not self.current_group:
            return

        stats = self.system.groups[self.current_group].get_statistics(self.system.genes, details=True)

        self.subplot1.clear()
        self.subplot2.clear()

        genotypes = list(stats['genotypes'].keys())
        genotype_counts = [info['count'] for info in stats['genotypes'].values()]
        self.subplot1.bar(genotypes, genotype_counts)
        self.subplot1.set_title("基因型分布", fontproperties=self.font)
        self.subplot1.set_ylabel("数量", fontproperties=self.font)

        phenotypes = [str(pheno) for pheno in stats['phenotypes'].keys()]
        phenotype_counts = [info['count'] for info in stats['phenotypes'].values()]
        self.subplot2.bar(phenotypes, phenotype_counts)
        self.subplot2.set_title("表型分布", fontproperties=self.font)
        self.subplot2.set_ylabel("数量", fontproperties=self.font)

        self.figure.tight_layout()
        self.chart_canvas.draw()

    def log_output(self, message):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        max_chars = 10000
        current_chars = len(self.log_text.get("1.0", tk.END))
        if current_chars > max_chars:
            self.log_text.delete("1.0", f"1.0+{current_chars - max_chars}c")

    def execute_command(self, event=None):
        command = self.command_entry.get().strip()
        if not command:
            return
        try:
            response = self.system.process_command(command)
            if response is not None:
                self.log_output(response)
            else:
                self.log_output(f">>> {command}")
            
            # 刷新 UI
            self.populate_groups_list()
            self.display_group_members()
            self.populate_genes_list()
        except Exception as e:
            self.log_output(f"!!! 执行指令失败: {str(e)}")
        self.command_entry.delete(0, tk.END)

    def show_help(self):
        help_text = """
       遗传学模拟系统是一款基于Python的软件，旨在帮助用户模拟孟德尔遗传规律。以下是具体使用方法：
1. 启动系统：打开软件后，您将看到一个图形用户界面（GUI），包含菜单选项、输入框和显示区域。
2. 添加基因：点击“添加基因”按钮，输入显性基因、隐性基因及其对应的显性和隐性性状，例如“A/a 高茎/矮茎”，然后提交。
3. 创建组别：点击“创建组别”按钮，输入组别名称，例如“豌豆实验组”，然后提交。
4. 添加个体：在创建的组别中，您可以添加基因组合。例如，添加20个“Aa”基因型的个体，输入基因型和数量后提交。
5. 运行模拟：选择要运行模拟的组别，点击“运行模拟”按钮，系统将根据设定的遗传规则进行模拟，并在运行日志中显示结果。
6. 查看结果：模拟完成后，您可以在“当前组别成员”列表中查看组内个体的基因型和数量。同时，系统会更新基因统计图表，直观展示基因型和表型的分布。
7. 切换交配模式：根据需要，您可以切换交配模式为“随机交配”或“人工杂交”，以观察不同模式下的遗传结果。
8. 加载指令：如果您有预先编写好的指令文件，可以使用“加载指令”功能，快速执行一系列操作。
9. 删除个体：如果需要删除特定个体，可以在成员列表中选择后点击“删除所选个体”按钮。
10. 查看帮助：如果您对操作有疑问，可以点击“帮助”按钮，查看可用指令列表和使用说明。
通过以上步骤，您可以轻松地进行遗传学模拟实验，观察不同基因组合和交配模式下的遗传结果
        """
        dialog = Toplevel(self.master)
        dialog.title("帮助")
        text = Text(dialog, wrap=tk.WORD)
        text.insert(tk.END, help_text)
        text.pack(fill=tk.BOTH, expand=True)
        Button(dialog, text="关闭", command=dialog.destroy).pack()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1200x800")
    app = GeneticSimulationGUI(root)
    root.mainloop()