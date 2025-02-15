import re
import random
from collections import defaultdict
from copy import deepcopy

# ====================
#   基因定义模块
# ====================
class Gene:
    def __init__(self, dominant, recessive, dom_trait, rec_trait):
        if len(dominant) != 1 or len(recessive) != 1:
            raise ValueError("基因符号必须为单个字符")
        if dominant == recessive:
            raise ValueError("显性和隐性基因不能相同")
        self.dominant = dominant.upper()
        self.recessive = recessive.lower()
        self.dom_trait = dom_trait
        self.rec_trait = rec_trait
    
    def get_phenotype(self, genotype):
        if self.dominant in genotype:
            return self.dom_trait
        return self.rec_trait

    def validate_allele(self, allele):
        return allele in {self.dominant, self.recessive}

# ====================
#   基因组成模块
# ====================
class GeneComposition:
    def __init__(self, genes_str, genes_dict):
        self.genes = genes_str
        self.validate(genes_dict)
        
    def validate(self, genes_dict):
        """强化验证逻辑"""
        if len(self.genes) % 2 != 0:
            raise ValueError("基因长度必须为偶数")
        
        for i in range(0, len(self.genes), 2):
            # 获取基因定义（符号需大写）
            gene_symbol = self.genes[i].upper()
            if gene_symbol not in genes_dict:
                raise ValueError(f"未定义基因: {gene_symbol}")
            gene = genes_dict[gene_symbol]
            
            # 获取实际输入的等位基因
            allele1 = self.genes[i]
            allele2 = self.genes[i+1]
            
            # 验证等位基因有效性
            valid_alleles = {gene.dominant, gene.recessive}
            if {allele1, allele2} - valid_alleles:
                raise ValueError(f"非法等位基因组合: {allele1}{allele2}")
            
            # 验证显性基因顺序（显性必须在前）
            if (allele2 == gene.dominant and 
                allele1 == gene.recessive):
                raise ValueError(f"显性基因必须在前，正确顺序应为{gene.dominant}{gene.recessive}")

# ====================
#   模拟组别模块
# ====================
class SimulationGroup:
    def __init__(self):
        self.current_generation = []
        self.gene_structure = []  # 存储基因定义顺序
        self.gene_length = 0      # 每个个体的基因长度
        self.experiment_mode = 'random'  # 实验模式：random/cross
        self.breed_history = []   # 繁殖历史记录

    def initialize_structure(self, genes_str, genes_dict):
        """初始化基因结构"""
        self.gene_structure = []
        seen_genes = set()
        
        # 验证并记录基因顺序
        for i in range(0, len(genes_str), 2):
            gene_symbol = genes_str[i].upper()
            if gene_symbol in seen_genes:
                raise ValueError(f"重复基因符号: {gene_symbol}")
            if gene_symbol not in genes_dict:
                raise ValueError(f"未定义基因: {gene_symbol}")
                
            self.gene_structure.append(genes_dict[gene_symbol])
            seen_genes.add(gene_symbol)
        
        self.gene_length = len(genes_str)

    def add_organism(self, genes_str, genes_dict):
        """添加个体到当前代"""
        # 首次添加时初始化结构
        if not self.current_generation:
            self.initialize_structure(genes_str, genes_dict)
        
        # 验证基因型
        GeneComposition(genes_str, genes_dict)
        
        if len(genes_str) != self.gene_length:
            raise ValueError(f"基因长度不符，要求长度：{self.gene_length}")
            
        self.current_generation.append(genes_str)



    def get_statistics(self, genes_dict, details=False):
        """获取统计信息"""
        stats = {
            'total': len(self.current_generation),
            'genotypes': defaultdict(int),
            'phenotypes': defaultdict(lambda: {'count':0, 'genotypes':set()}),
            'details': []
        }
        
        for geno in self.current_generation:
            # 基因型统计
            stats['genotypes'][geno] += 1
            
            # 表型分析
            phenotype = []
            for i in range(0, len(geno), 2):
                gene_symbol = geno[i].upper()
                gene = genes_dict[gene_symbol]
                phenotype.append(gene.get_phenotype(geno[i:i+2]))
            
            pheno_key = tuple(phenotype)
            stats['phenotypes'][pheno_key]['count'] += 1
            stats['phenotypes'][pheno_key]['genotypes'].add(geno)
        
        # 计算比率
        total = stats['total']
        for geno in stats['genotypes']:
            stats['genotypes'][geno] = {
                'count': stats['genotypes'][geno],
                'ratio': stats['genotypes'][geno] / total if total >0 else 0
            }
            
        for pheno in stats['phenotypes']:
            stats['phenotypes'][pheno]['ratio'] = stats['phenotypes'][pheno]['count'] / total if total >0 else 0
            stats['phenotypes'][pheno]['genotypes'] = list(stats['phenotypes'][pheno]['genotypes'])
        
        # 生成详细信息
        if details:
            for geno in stats['genotypes']:
                traits = []
                for i in range(0, len(geno), 2):
                    gene_symbol = geno[i].upper()
                    gene = genes_dict[gene_symbol]
                    traits.append(gene.get_phenotype(geno[i:i+2]))
                stats['details'].append({
                    'genotype': geno,
                    'traits': ', '.join(traits),
                    'count': stats['genotypes'][geno]['count'],
                    'ratio': stats['genotypes'][geno]['ratio']
                })
            # 按数量排序
            stats['details'].sort(key=lambda x: -x['count'])
        
        return stats

    def set_experiment_mode(self, mode):
        """设置实验模式"""
        valid_modes = ['random', 'cross']
        if mode not in valid_modes:
            raise ValueError(f"无效模式，可选：{valid_modes}")
        self.experiment_mode = mode

    
    def breed(self, genes_dict):
        """执行繁殖逻辑（允许相同基因型杂交）"""
        if len(self.current_generation) < 2:
            raise ValueError("至少需要两个亲本进行繁殖")
    
        next_gen = []
        parents = self.current_generation.copy()
    
        if self.experiment_mode == 'cross':
            # 改进的杂交模式：允许相同基因型配对
            parent_groups = defaultdict(list)
            for p in parents:
                parent_groups[p].append(p)
        
            pairs = []
            keys = list(parent_groups.keys())
        
            # 生成所有可能的配对组合（包括相同基因型）
            for i in range(len(keys)):
                # 不同基因型配对
                for j in range(i+1, len(keys)):
                    pairs.extend(zip(parent_groups[keys[i]], parent_groups[keys[j]]))
                # 相同基因型配对（至少需要2个个体）
                same_type = parent_groups[keys[i]]
                while len(same_type) >= 2:
                    pairs.append((same_type.pop(), same_type.pop()))
        
            random.shuffle(pairs)
            for p1, p2 in pairs[:len(parents)//2]:  # 保持种群规模稳定
                child = self._create_child(p1, p2, genes_dict)
                next_gen.append(child)
        else:
            # 原有自然随机交配模式保持不变
            random.shuffle(parents)
            for i in range(0, len(parents)//2*2, 2):
                p1 = parents[i]
                p2 = parents[i+1]
                child = self._create_child(p1, p2, genes_dict)
                next_gen.append(child)
    
        self.breed_history.append({
            'parent_count': len(parents),
            'child_count': len(next_gen)
        })
        self.current_generation = next_gen

    def _create_child(self, p1, p2, genes_dict):
        child_genes = []
        # 按基因座独立处理
        for locus in range(0, len(p1), 2):
            gene_symbol = p1[locus].upper()
            gene = genes_dict[gene_symbol]
        
            # 分别从父母获取当前基因座的等位基因
            p1_alleles = [p1[locus], p1[locus+1]]
            p2_alleles = [p2[locus], p2[locus+1]]
        
            # 独立选择配子（修复关键点）
            gamete1 = random.choice(p1_alleles)
            gamete2 = random.choice(p2_alleles)
        
            # 移除显性排序，保持随机顺序
            child_genes.extend([gamete1, gamete2])  # 不再排序
    
        # 按基因结构排序（保持基因顺序）
        sorted_genes = []
        for i in range(0, len(child_genes), 2):
            gene_symbol = child_genes[i].upper()
            gene = genes_dict[gene_symbol]
            # 仅在同一基因座内排序
            alleles = sorted([child_genes[i], child_genes[i+1]], 
                       key=lambda x: x == gene.recessive)
            sorted_genes.extend(alleles)
    
        return ''.join(sorted_genes)


# ====================
#   主系统模块
# ====================
class GeneticSimulationSystem:
    def __init__(self):
        self.genes = {}  # {symbol: Gene}
        self.groups = {}  # {group_name: SimulationGroup}
        self.current_group = None
    
    def process_command(self, cmd):
        cmd = cmd.strip()
        if not cmd:
            return
        
        parts = re.split(r'\s+', cmd)
        instruction = parts[0].lower()
        
        try:
            if instruction == '/help':
                self.show_help()
            elif instruction == '/add':
                self.add_gene(parts[1:])
            elif instruction == '/delete':
                self.delete_gene(parts[1:])
            elif instruction == '/create':
                self.create_group(parts[1:])
            elif instruction == '/read':
                self.read_group(parts[1:])
            elif instruction == '/save':
                self.save_group(parts[1:])
            elif instruction == '/list':
                self.list_groups(parts[1:])
            elif instruction == '/show':
                self.show_group(parts[1:])
            elif instruction == '/run':
                self.run_simulation(parts[1:])
            elif instruction == '/write':
                self.write_simulation(parts[1:])
            elif instruction == '/change':
                self.change_composition(parts[1:])
            elif instruction == '/random':
                self.random_generate(parts[1:])
                return;
            elif instruction == '/load':
                self.load_commands(parts[1:])
                return;
            elif instruction == '/mode':
                self.set_experiment_mode(parts[1:])
                return;
            elif instruction == '/runs':
                self.run_for_times(parts[1:])
                return;
            else:
                print("未知指令，输入/help查看帮助")
        except Exception as e:
            print(f"错误：{str(e)}")
    
    def show_help(self):
        help_text = """
=== 遗传模拟系统指令手册 ===
/help - 显示本帮助信息
/add <显性基因> <隐性基因> <显性性状> <隐性性状> - 添加新基因定义
/delete <基因符号> - 删除已定义基因
/create <组名> - 创建新模拟组
/read <组名> - 切换到指定组
/save <组名> - 保存当前状态到组
/list [组名] - 列出所有组或组内个体
/show <组名> [-details] - 显示统计信息
/run <组名> - 执行一代繁殖并显示结果
/write <组名> - 执行繁殖并覆盖当前组
/change <组名> <基因型> <add/del> <数量> - 修改组成
/random <组名> <数量> <基因长度> - 随机生成个体
/load <文件路径> - 逐行读取指定文件里的指令并执行
/mode <组名> <cross|random> - 设置当前组别的类型
/runs <轮数> - 执行繁殖指定轮数次
/exit - 退出当前程序

* 基因符号规则：
  - 显性基因使用大写字母（如A）
  - 隐性基因使用小写字母（如a）
  - 多基因按顺序排列（如AaBb）

* 遗传规则：
  - 严格遵守孟德尔遗传定律
  - 显性性状优先表达
  - 配子形成时等位基因随机分离
  - 繁殖需要至少两个个体
"""
        print(help_text)
    def run_for_times(self, args):
        try:
            count=int(args[0])
        except:
            print("不正确的参数")
            return;
        for i in range(count):
            system.process_command("/run")

    def set_experiment_mode(self, args):
        if len(args) < 2:
            raise ValueError("格式：/mode <组名> <cross|random>")
        group_name, mode = args[0], args[1]
        
        if group_name not in self.groups:
            raise ValueError("组别不存在")
        if mode not in ['cross', 'random']:
            raise ValueError("模式必须是cross或random")
            
        self.groups[group_name].set_experiment_mode(mode)
        print(f"已设置{group_name}组为{mode}模式")
    def show_group(self, args):
        """完善统计显示功能"""
        if not args:
            raise ValueError("需要指定组名")

        group_name = args[0]
        details = '-details' in args[1:]

        if group_name not in self.groups:
            raise ValueError("组别不存在")

        group = self.groups[group_name]
        stats = group.get_statistics(self.genes, details=details)

        print(f"\n=== {group_name} 统计 ===")
        print(f"总个体数：{stats['total']}")
        
        # 基因型分布
        print("\n基因型分布：")
        for geno, info in sorted(stats['genotypes'].items(), 
                               key=lambda x: -x[1]['count']):
            print(f"  {geno}: {info['count']} ({info['ratio']*100:.2f}%)")

        # 表型分布
        print("\n表型分布：")
        for pheno, info in sorted(stats['phenotypes'].items(),
                                key=lambda x: -x[1]['count']):
            print(f"  {pheno}:")
            print(f"    数量：{info['count']} 占比：{info['ratio']*100:.2f}%")
            if details:
                print(f"    基因型：{', '.join(info['genotypes'])}")

        # 详细模式
        if details:
            print("\n详细性状组合：")
            for detail in stats.get('details', []):
                print(f"  {detail['genotype']} → {detail['traits']}")

    def add_gene(self, args):
        if len(args) != 4:
            raise ValueError("参数数量错误，需要4个参数")
        dom, rec, dom_t, rec_t = args
        gene_symbol = dom.upper()
        
        if gene_symbol in self.genes:
            raise ValueError("该基因已存在")
        
        new_gene = Gene(dom, rec, dom_t, rec_t)
        self.genes[gene_symbol] = new_gene
        print(f"成功添加基因：{gene_symbol}（显性：{dom_t}，隐性：{rec_t}）")
    def load_commands(self, args):
        """处理/load指令：从文件读取命令批量执行"""
        if len(args) < 1:
            raise ValueError("需要指定文件路径，格式：/load <文件路径>")

        file_path = args[0]
        line_num = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                print(f"\n=== 开始执行指令文件：{file_path} ===")
                
                for line_num, line in enumerate(f, 1):
                    # 清理行内容并跳过空行/注释
                    clean_line = line.strip()
                    if not clean_line or clean_line.startswith('#'):
                        continue
                    
                    # 显示执行进度
                    print(f"\n[行{line_num}] 执行: {clean_line}")
                    
                    try:
                        self.process_command(clean_line)
                    except Exception as e:
                        print(f"!! 行{line_num}执行失败: {str(e)}")
                        # 可选：是否继续执行后续命令
                        # raise  # 如果要中断执行则取消注释
                
                print(f"\n=== 文件执行完成，共处理 {line_num} 行 ===")

        except FileNotFoundError:
            raise ValueError(f"文件不存在：{file_path}")
        except UnicodeDecodeError:
            raise ValueError("文件编码错误，请使用UTF-8编码")
        except Exception as e:
            raise ValueError(f"文件读取失败：{str(e)}")


    def create_group(self, args):
        if len(args) < 1:
            raise ValueError("缺少组名参数")
        group_name = args[0]
        
        if group_name in self.groups:
            raise ValueError("组别已存在")
            
        self.groups[group_name] = SimulationGroup()
        self.current_group = group_name
        print(f"成功创建组别：{group_name}")

    def read_group(self, args):
        if len(args) < 1:
            raise ValueError("缺少组名参数")
        group_name = args[0]
        
        if group_name not in self.groups:
            raise ValueError("组别不存在")
            
        self.current_group = group_name
        print(f"已切换到组别：{group_name}")

    def run_simulation(self, args):
        if len(args) < 1:
            if not self.current_group:
                raise ValueError("需要指定组别")
            group_name = self.current_group
        else:
            group_name = args[0]
        
        group = self.groups.get(group_name)
        if not group:
            raise ValueError("组别不存在")
        
        try:
            original = len(group.current_generation)
            group.breed(self.genes)
            new_count = len(group.current_generation)
            
            print(f"\n=== 第{group_name}组繁殖结果 ===")
            print(f"亲代数量：{original} → 子代数量：{new_count}")
            print("注意：繁殖后亲代将被替换为子代")
            
            stats = group.get_statistics(self.genes)
            self._display_stats(stats)
            
        except ValueError as e:
            print(f"繁殖失败：{str(e)}")

    def write_simulation(self, args):
        self.run_simulation(args)
        print("已更新当前组状态")

    def random_generate(self, args):
        if len(args) < 3:
            raise ValueError("参数不足，格式：/random <组名> <数量> <基因长度>")
        
        group_name, amount, length = args[0], int(args[1]), int(args[2])
        group = self.groups.get(group_name)
        if not group:
            raise ValueError("组别不存在")
        
        if length % 2 != 0:
            raise ValueError("基因长度必须为偶数")
        
        existing_genes = list(self.genes.keys())
        if not existing_genes:
            raise ValueError("请先定义基因")
        
        for _ in range(amount):
            genes = []
            for _ in range(length//2):
                gene = random.choice(existing_genes)
                alleles = [self.genes[gene].dominant, self.genes[gene].recessive]
                pair = random.choices(alleles, k=2)
                genes.extend(sorted(pair, key=lambda x: x.isupper(), reverse=True))
            group.add_organism(''.join(genes), self.genes)
        
        print(f"成功生成{amount}个随机个体")

    def _display_stats(self, stats):
        print("\n基因型分布：")
        for geno, info in stats['genotypes'].items():
            print(f"{geno}: {info['count']} ({info['ratio']*100:.2f}%)")
        
        print("\n表型分布：")
        for pheno, info in stats['phenotypes'].items():
            print(f"{pheno}: {info['count']} ({info['ratio']*100:.2f}%)")
    def list_groups(self, args):
        """完善列表显示功能"""
        try:
            if not args:
                print("\n当前组别列表:")
                for name in self.groups:
                    status = "(当前)" if name == self.current_group else ""
                    count = len(self.groups[name].current_generation)
                    print(f"  {name} {status} 个体数：{count}")
                return

            group_name = args[0]
            if group_name not in self.groups:
                raise ValueError("组别不存在")

            group = self.groups[group_name]
            print(f"\n组别 [{group_name}] 成员列表（共{len(group.current_generation)}个）:")
            counter = defaultdict(int)
            for geno in group.current_generation:
                counter[geno] += 1
            for i, (geno, count) in enumerate(counter.items(), 1):
                print(f"{i}. {geno} ×{count}")

        except IndexError:
            raise ValueError("缺少组名参数")
    def change_composition(self, args):
        """完善基因组成修改"""
        if len(args) < 4:
            raise ValueError("参数不足，格式：/change <组名> <基因型> <add/del> <数量>")

        group_name = args[0]
        genotype = args[1]
        operation = args[2]
        amount = int(args[3])

        # 获取目标组
        if group_name not in self.groups:
            raise ValueError(f"组别 {group_name} 不存在")
        group = self.groups[group_name]

        # 验证基因型
        try:
            GeneComposition(genotype, self.genes)
        except ValueError as e:
            raise ValueError(f"无效基因型: {str(e)}")

        # 检查基因长度
        if group.gene_length > 0 and len(genotype) != group.gene_length:
            raise ValueError(f"基因长度不匹配，要求长度：{group.gene_length}")

        # 执行操作
        if operation == 'add':
            for _ in range(amount):
                group.add_organism(genotype, self.genes)
            print(f"成功添加 {amount} 个个体")
        elif operation == 'del':
            current_count = group.current_generation.count(genotype)
            if current_count < amount:
                raise ValueError(f"数量不足，当前存在 {current_count} 个")
            group.current_generation = [g for g in group.current_generation if g != genotype][:len(group.current_generation)-amount]
            print(f"成功删除 {amount} 个个体")
        else:
            raise ValueError("操作类型必须是 add 或 del")


# ====================
#   主程序入口
# ====================
if __name__ == "__main__":
    system = GeneticSimulationSystem()
    print("=== 遗传模拟系统 ===")
    print("输入/help查看指令帮助")
    
    while True:
        try:
            cmd = input("\n>>> ").strip()
            if cmd.lower() == '/exit':
                print("系统已退出")
                break
            system.process_command(cmd)
        except KeyboardInterrupt:
            print("\n检测到中断操作，输入/exit退出系统")
        except Exception as e:
            print(f"运行时错误：{str(e)}")

