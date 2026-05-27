---
name: et
description: "WPS 云端在线表格（.xlsx）与在线智能表格（.ksheet）的创建与编辑能力。两者共用同一套 API。涵盖数据读写、公式、格式美化、图表、条件格式、数据透视表、图片插入等功能。当用户提供云文档链接或 file_id 要求操作 .xlsx / .ksheet 文件，或需要从零创建在线表格时使用。"
---

# 输出要求

## 所有在线表格操作

1. **公式优先**：所有计算逻辑必须用表格公式实现（如 `=SUM(A1:A10)`），禁止 Python 在内存中算出结果后直接填入数字。Python 计算结果不会被用户认可
   - **例外**：公式无法实现的复杂算法、一次性分析、大规模数据处理、固定文本标题，可用 Python 计算后写入结果值
2. **交付到表格**：所有计算结果必须体现为单元格中的数值或公式，严禁在对话中直接输出计算结果
3. **指令优先于示例**：用户文字描述与其提供的公式/代码冲突时，以文字描述为准
4. **性能优先**：禁止逐个单元格写入，应按逐行或逐列批量写入，或使用 `auto_fill` 填充连续公式

## 关键：使用公式，不要硬编码值

**始终使用表格公式，而非在 Python 中计算后将结果硬编码写入。** 这样表格才能在源数据变化时自动重算。

```python
# ❌ 错误：Python 计算后硬编码
total = sum(values)
sheet.range("B10").value = total

# ✅ 正确：使用表格公式
sheet.range("B10").formula = "=SUM(B2:B9)"
sheet.range("C5").formula = "=(C4-C2)/C2"
```

## 格式美化标准

- 表头行使用深色背景（#4472C4）+ 白色加粗字体 + 居中对齐
- 配色一致：整个表格最多使用 2-3 种颜色
- 字号层次：标题 14（加粗）、表头 12（加粗）、合计行 12（加粗）、数据区 11（常规）
- 列宽自适应：使用 `auto_fit()` 根据内容自动调整
- 数据区添加细线边框
- 数字格式统一：金额加千分位、百分比带%、日期格式一致
- 不要使用多种颜色混搭、粗边框、彩色边框、复杂的合并单元格布局

---

# 在线表格创建与编辑

## 概述

在 WPS 云文档上创建、编辑在线表格（.xlsx）或智能表格（.ksheet）。两种文件类型共用同一套 API，操作方式完全一致。不涉及本地文件的上传/下载——云文档必须在云端直接操作。

> 本文档由 `wps_docs/SKILL.md` 路由加载。前置条件：已通过 SKILL.md 确认文件类型为 .xlsx 或 .ksheet。

所有 Python 代码通过 `python_cell_exec` 工具执行。首次操作前，**必须先单独执行一次初始化**（仅含 `edit` 或 `create` 调用，不要在同一代码块中写入数据操作代码）。

- 用户提供了云文档 file_id 或链接 → 使用 `edit`（编辑已有文档）
- 用户要求创建新的在线表格 → 使用 `create`（从零创建）

**编辑已有云文档**：

```python
import sys, os
sys.path.insert(0, os.path.join(os.getenv('SKILL_PATH'), 'wps_docs', 'et', 'scripts')) #这两步不可以省略
from et import edit
wb, file_id = edit(file_id="<云文档 file_id>")
```

**从零创建新文件**（创建到根目录）：

```python
import sys, os
sys.path.insert(0, os.path.join(os.getenv('SKILL_PATH'), 'wps_docs', 'et', 'scripts'))
from et import create
wb, file_id = create("<文件名>.xlsx")   # 在线表格
wb, file_id = create("<文件名>.ksheet") # 智能表格
```

> 用户要求创建"智能表格"或文件名以 `.ksheet` 结尾时，使用 `.ksheet` 后缀；其他情况默认 `.xlsx`。

**创建到指定文件夹**（仅支持 `.xlsx`，不支持 `.ksheet`）：

```python
import sys, os
sys.path.insert(0, os.path.join(os.getenv('SKILL_PATH'), 'wps_docs', 'scripts'))
sys.path.insert(0, os.path.join(os.getenv('SKILL_PATH'), 'wps_docs', 'et', 'scripts'))
import kdocs
from et import create

folder_id = kdocs.find_folder_by_path("工作/项目A")
wb, file_id = create("<文件名>.xlsx", folder_id=folder_id)
```

> 若用户同时指定了文件夹和智能表格（`.ksheet`），**必须终止流程**，告知用户「指定文件夹暂不支持创建智能表格，只能使用 .xlsx 格式」，等待用户确认。严禁擅自用 `.xlsx` 替代 `.ksheet`、先在根目录创建再移动等变通方式。
>
> `find_folder_by_path` 仅支持「我的云文档」。若抛出 ValueError（未找到文件夹），**立即停止**，告知用户并询问是否需要通过 `kdocs.create_folder()` 创建。**禁止**未经用户确认自行创建文件夹。

**多文件操作**（同一轮对话操作多个云文档）：

支持在一次对话中依次操作多个文件。每次调用 `edit` / `create` 时，系统会自动保存并关闭上一个文件，然后打开新文件。

```python
import sys, os
sys.path.insert(0, os.path.join(os.getenv('SKILL_PATH'), 'wps_docs', 'et', 'scripts'))
from et import edit, create

# 步骤 1：读取源文件
wb, fid_a = edit(file_id="<源文件 file_id>")
data = wb.sheet("Sheet1").range("A1:D100").value

# 步骤 2：切换到目标文件（源文件自动保存）
wb, fid_b = create("分析报告.xlsx")
wb.sheet("Sheet1").range("A1:D1").value = [["姓名", "部门", "金额", "占比"]]

# 步骤 3：需要时可以切回源文件
wb, _ = edit(file_id=fid_a)
# ...继续操作源文件...
```

**多文件操作规则**：
- 每次只能有一个活动文件，切换时旧文件自动保存并关闭
- 切换后必须使用新返回的 `wb` 对象，旧的 `wb` 不再可用
- 保存好每个文件的 `file_id`（如 `fid_a`、`fid_b`），用于后续切回
- 同一文件不要重复调用 `edit`/`create`，只需调用一次

> **重要**：每个文件只需调用一次 `edit` / `create`，同一文件不要重复调用。执行后返回的 `wb`（Workbook 实例）和 `file_id` 可直接使用。

初始化执行后会自动输出**表格摘要**（仅 `edit` 时）：各工作表的使用范围、行列数、数据预览。根据摘要了解表格结构和内容，后续分析基于此展开。

**初始化后的基本操作链路**：

```python
sheet = wb.sheet("Sheet1") #这一步不能遗漏，sheet需要初始化
sheet.range("A1:C1").value = [["姓名", "年龄", "部门"]]
rng = sheet.range("A1:C1")
rng.format.font.bold = True
rng.format.font.color = '#FFFFFF'
rng.format.fill.color = '#4472C4'
```

> 缓冲操作（value 赋值、format 设置等）会在读取数据、执行脚本时自动提交，代码块执行结束时系统也会自动提交，无需手动处理。

## 工作流

### 编辑已有文档

1. **需求分析**：理解用户意图，设计处理方案（只输出分析，不写代码）
2. **任务规划**：分解为可验证的小步骤，复杂任务添加中间列放置中间结果
3. **执行任务**：按照规划生成代码并执行
4. **验证结果**：写入后读取结果进行检查（必须在单独的代码块中执行，推荐使用`print(sheet.range(addr)`验证数据和格式）
5. **格式美化**：调整行高列宽、添加边框、设置表头样式

#### 需求分析要点

- 根据初始化时自动输出的表格摘要了解工作表结构、表头含义和数据类型
- 需要更详细的数据时，使用 `print(sheet.range("A1:D10"))` 预览特定区域
- 注意摘要中是否存在省略行提示，如有则先读取省略范围的完整数据
- **完整读取指令**：逐句检查用户描述，列出所有条件分支和目标，避免只实现部分条件而遗漏其余。当用户给出条件→结果的映射规则时，还需读取数据确认是否存在其他同类映射未在指令中列出——如果数据中有多种组合但用户只提了一部分，应主动问清或基于数据推断补全
- **确认输出位置和语义**：明确输出从哪行哪列开始（用户说"从 I3 开始"就是 I3，不是 I2）；明确每列应放什么内容
- **理解业务方向**：涉及增减、扣除、正负值时，先确认语义方向再动手（如"调整金额"是上调还是下调、"结余"是收入减支出还是相反）
- 需求有歧义时先确认，避免理解偏差导致任务失败

#### 任务规划要点

- 分解为可验证的小步骤
- 复杂任务添加中间列放置中间结果，任务完成后清理中间列
- **位置变更检查**：如果操作会改变单元格位置（排序、移动、插入、删除），必须先检查操作涉及的数据是否被公式引用

### 创建新文档

1. **需求分析**：理解用户意图，设计表格结构（只输出分析，不写代码）
2. **工作表管理**：建立符合需求的工作表结构
3. **数据写入**：按逐行或逐列方式写入数据
4. **添加公式**：实现数据间的计算关系
5. **格式美化**（不可跳过）：设置表头样式、边框、列宽
6. **添加图表**：用户要求时必须执行，否则根据数据特征判断

#### 创建模式约束

- **默认工作表**：`.xlsx` 文件默认含 `Sheet1`；`.ksheet` 文件默认含 `工作表1`。可根据需求重命名或新建工作表
- **必须执行代码**：必须通过代码实际写入数据，不能只回复"已完成"而不执行
- **必须格式美化**：没有样式的表格不专业，数据写入后必须设置样式
- **默认预填充示例数据**：空表格对用户没有参考价值，应填入足够多的完整示例数据让用户理解表格用法。每行所有列都要有内容。只有用户明确说"空白模板"时才留空

#### 创建模式需求分析

在动手之前，先回答以下问题以确保正确理解需求：

1. 核心实体与行的关系：每一行代表什么？同一对象是否会出现多行？
2. 实体之间的归属关系：一对一还是一对多？
3. 计算与汇总的层级：个体、分组还是整体？
4. 验证表结构的现实合理性：同一行中的所有数据在现实场景中能否同时存在？
5. 用户使用场景：日常记录、数据分析、还是报告展示？

#### 工作表管理

- **分表规则**：数据量 30 行以上或有明确分类维度时分表（按时间、类别、功能维度）
- **单表场景**：数据量少于 30 行、结构简单、列数 10 列以内、无明显分类维度
- **命名规则**：默认的工作表（"Sheet1"或"工作表1"）应重命名为体现内容主题的名称。用 `wb.rename_sheet("Sheet1", "成绩表")` 重命名，`sheet.name` 是只读属性，不可赋值

### 多文件操作

当用户需求涉及多个云文档（如"从 A 表提取数据写入 B 表"、"汇总多个文件"）时：

1. **规划文件操作顺序**：先确定需要读取哪些源文件、写入哪些目标文件，合理安排切换顺序以减少来回切换
2. **读取源数据**：`edit` 打开源文件 → 读取所需数据到 Python 变量 → 数据暂存在内存中
3. **写入目标文件**：`edit`/`create` 切换到目标文件（源文件自动保存）→ 用内存中的数据写入
4. **验证结果**：在目标文件中验证写入结果

**注意事项**：
- 切换文件后，旧的 `wb` 对象失效，必须使用新返回的 `wb`
- 从源文件读取的数据（Python 变量）在切换后仍然有效，可以直接写入新文件
- 文件切换有网络开销，应尽量减少不必要的来回切换——先一次性读完源文件所需数据，再切换到目标文件写入

## 验证清单

验证操作不要和写入操作放在同一代码块内，必须在**单独的代码块**中执行，推荐使用`print(sheet.range(addr))`,能够验证数据，格式。
```python
print(sheet.range("A1:C10"))
```

### 必检项

- [ ] 删除/插入行后，读取目标区域确认关键数据是否在预期位置
- [ ] 合并/复制大量数据后，打印最后几行确认数据完整，检查总行数是否与源数据一致
- [ ] 排序/筛选后，打印首行、末行和总行数，与操作前对比确认无遗漏
- [ ] **语义对应检查**：写入后抽查首行数据，确认每列的值与对应表头含义匹配
- [ ] 用 print 输出每个结果区域的实际范围地址，供最终总结引用
- [ ] 图表位置必须通过 `chart_information()` 获取，不能用 `add_chart` 的参数

### 常见陷阱

| 场景         | 要点                                                               |
| ------------ | ------------------------------------------------------------------ |
| 数据清洗     | 优先使用公式：`=VALUE()` `=DATEVALUE()` `=TRIM()` `=CLEAN()`       |
| 合并单元格   | 合并区域只有左上角单元格有值，写入前必要时先取消合并               |
| 破坏性操作   | 删除行/列、清空数据前，先告知用户影响范围，确认后再执行            |
| 关联行删除   | 先遍历标记所有待删除行号，再统一倒序删除                           |
| 排序         | 使用 `range.sort()` 原地排序，保留格式和公式                       |
| 空值与默认值 | 数值列用 0，文本列用空字符串；混用会导致公式出错                   |
| 百分比精度   | 公式中保留完整精度（如 `=B2/C2`），显示精度由 `number_format` 控制 |

## 最佳实践

### 数据读写

```python
data = sheet.range("A1:C10").value            # 读取值（二维数组）
typed = sheet.range("A1:C10").typed_value     # 读取带类型 {type, value}
formulas = sheet.range("D2:D10").formula      # 读取公式

sheet.range("A1:C1").value = [["姓名", "年龄", "部门"]]  # 写入值
sheet.range("D2").formula = "=B2+C2"                       # 写入公式
```

#### 写入规范

- **逐行逐列写入**：批量写入时按逐行或逐列赋值，矩形区域一次性写入会导致数据错位

```python
# ✅ 正确：逐行赋值
sheet.range("A1:C1").value = [["姓名", "年龄", "部门"]]
sheet.range("A2:C2").value = [["张三", 25, "技术部"]]

# ❌ 错误：矩形区域一次性写入
sheet.range("A1:C3").value = [["a","b","c"], ["d","e","f"], ["g","h","i"]]
```

- **公式保护**：`.value` 读写会丢失公式！有公式的列要单独处理：

```python
formulas = sheet.range("D2:D100").formula  # 用 .formula 读公式
data = sheet.range("A2:C100").value        # 只对数据列用 .value
sheet.range("D2").formula = "=B2+C2"       # 用 .formula 写公式
```

- **长数字精度保护**：身份证号、银行账号等超过 15 位的纯数字，写入时加单引号前缀强制文本存储：

```python
sheet.range("B2").value = [["'" + invoice_no]]
```

- **百分比用字符串**：写入百分比永远用 `"X%"` 字符串，不写浮点数：

```python
sheet.range("A1").value = [["35%"]]
```

- **引号转义**：代码中字符串包含双引号时必须转义为 `\"`

#### 数据处理原则

- **数据只从表格读取**：禁止在代码中硬编码原始数据
- **先观察后处理**：处理数据前先打印样本，确认数据结构和类型
- **保持原始数据**：从表格读取的文本原样使用，避免 `.upper()` / `.lower()` / `.strip()` 等转换
- **区分类型处理**：日期和数值不做文本处理，只对字符串执行正则替换等操作。批量做日期/数字格式转换时，先用 `.typed_value` 检查每个单元格的 `type` 字段
- **删除操作倒序**：删除多行时从大行号往小行号删除，避免行号偏移

```python
for row in sorted(rows_to_delete, reverse=True):
    sheet.range(f"{row}:{row}").delete(shift='up')
```

- **保持工作表结构**：不要重命名或删除已有工作表，除非用户明确要求

### 格式设置

```python
rng = sheet.range("A1:C1")

# 字体
rng.format.font.bold = True
rng.format.font.color = '#FFFFFF'
rng.format.font.size = 12
rng.format.font.name = '微软雅黑'
rng.format.font.italic = True
rng.format.font.strikeout = True

# 填充
rng.format.fill.color = '#4472C4'

# 对齐
rng.format.h_align = 'center'       # left / center / right
rng.format.v_align = 'center'       # top / center / bottom

# 边框
rng.format.border.style = 'thin'    # thin / dashed / dotted / double / none
rng.format.border.type = 'all'      # all / outer / inner
rng.format.border.color = '#000000'

# 数字格式
rng.format.number_format = '#,##0.00'

# 自动换行
rng.format.wrap_text = True

# 列宽 / 行高
sheet.range("A:C").format.column_width = 15
sheet.range("1:1").format.row_height = 20

# 自适应列宽
sheet.range("A:C").auto_fit()

# 合并单元格
sheet.range("A1:C1").merge()
```

### 排序与填充

```python
# 原地排序（保留格式和公式）
sheet.range("A1:D10").sort(key="B", order="desc", header=True)
# 多字段排序
sheet.range("A1:D10").sort(key="A", order="asc", key2="C", order2="desc")

# 自动填充
sheet.range("A2").auto_fill("A2:A10")
```

### 图表

```python
sheet.add_chart("column_clustered", "A1:D10", "F1:L15", "销售趋势")
info = sheet.chart_information()                    # 查看已有图表
sheet.update_chart_title(1, "新标题")               # 修改图表标题
sheet.update_chart_type(1, "line")                  # 修改图表类型
sheet.update_chart_data_source(1, "A1:D10")         # 修改数据源
sheet.update_chart_position(1, "F1:L15")            # 修改位置
sheet.update_chart_legend(1, True, "bottom")        # 修改图例
sheet.update_chart_axis_title(1, "category", "月份") # 修改轴标题
sheet.delete_chart(1)                               # 删除图表
```

- 数据源应为连续区域
- 创建前先通过 `chart_information()` 了解已有图表，避免覆盖
- **先创建图表再调整行高/列宽**，顺序反了会导致图表位置偏移

### 条件格式

```python
# 数值条件：大于 100 时标红
sheet.range("B2:B20").add_format_condition("cell_value", operator="greater", formula1="100",
    format_style={"interior": {"color": "#ffeef0"}, "font": {"color": "#d1242f", "bls": True}})

# 文本匹配：包含"减少"时高亮（文本判断用 text 类型，不要用 cell_value）
sheet.range("H2:H100").add_format_condition("text", operator="string_conclude", formula1="减少",
    format_style={"interior": {"color": "#FFF2CC"}, "font": {"color": "#d1242f"}})

# 查看 / 删除 / 清除
rules = sheet.range("A1:D20").get_format_conditions()
sheet.range("A1:D20").delete_format_condition(priority=1)
sheet.range("A1:D20").clear_format_conditions()
```

### 插入图片

```python
sheet.range("A1").insert_picture("url", "https://example.com/chart.png",
    target_row_from=0, target_row_to=2, target_col_from=0, target_col_to=1)
```

行列索引均从 0 开始。支持 `local`（uploadId）、`attachment`（附件ID）、`url`（网络URL）三种来源。

### 数据透视表

#### 创建

- **空表头检查**：创建前必须检查数据源表头行是否存在空单元格，空表头会导致创建失败
- **放置位置**：用户未指定时必须新建工作表放置透视表，禁止放在源数据所在的工作表
- **数据类型**：创建前先用 `.typed_value` 检查值字段的数据类型，文本字段不能用 `sum`
- **字段与样式**：创建后必须配置字段布局并设置样式（默认使用 `set_table_style("PivotStyleLight16")`）
- **"值"标签美化**：当添加了多个数据字段时，必须将"值"字段 Caption 改为更具描述性的名称

#### 字段调整

修改字段方向时，先将所有需要的字段设置到目标区域（row/column/data），然后只将确实多余的字段设为 hidden。严禁将用户要求展示的字段设为 hidden。"值"是自动生成的虚拟字段，不要将其设为 hidden。

## 异常处理

- **permissionDenied**：立即停止，告知用户无法编辑
- **连续调用工具失败三次**：终止任务，报告失败原因
- **缺少必要 API**：明确告知用户，尝试其他方式可能导致不可预期的结果

---

# API 速查

以下为所有可用的属性和方法，**严禁使用下方未列出的任何属性或方法**。
如需查看完整签名和参数说明，可调用 `generate_full_outline(["Sheet"])` 获取指定类的详细文档。

## Workbook

```
wb.sheets() -> list[Sheet]                     # 列出全部工作表
wb.sheet(name) -> Sheet                         # 按名取表
wb.add_sheet(name, exists='override') -> Sheet  # 新建表（同名策略：override/new_name/ignore/error）
wb.rename_sheet(old_name, new_name) -> Sheet    # 重命名
wb.delete_sheet(name)                           # 删除工作表
```

## Sheet

```
sheet.range(addr) -> Range                      # 获取区域对象
sheet.used_range -> Range                       # (只读) 已使用区域
sheet.name -> str                               # (只读) 工作表名称
```

## Sheet — 图表

```
sheet.add_chart(chart_type, source_address, rect_address, title, plot_by='columns')
sheet.chart_information(verbose=True) -> dict
sheet.delete_chart(index)
sheet.update_chart_title(index, title)
sheet.update_chart_data_source(index, source_address, plot_by='columns')
sheet.update_chart_position(index, rect_address)
sheet.update_chart_type(index, chart_type)
sheet.update_chart_legend(index, has_legend, position='bottom')
sheet.update_chart_axis_title(index, axis_type, title, visible=True)
```

## Sheet — 数据透视表

```
sheet.pivot_table_wizard(source_address, table_destination='',
    table_name='', row_grand=True, column_grand=True) -> PivotTable
sheet.pivot_tables() -> list[PivotTable]
sheet.pivot_table(name_or_index) -> PivotTable
```

## Range — 数据读写

```
range.value                                     # (读写) 二维数组，空单元格返回''
range.typed_value                               # (只读) 带类型 [{type, value}]
range.formula                                   # (读写) 公式，须以'='开头
```

## Range — 格式

```
range.format.font.bold / .italic / .strikeout   # (读写) 字体样式
range.format.font.color / .name / .size         # (读写) 字体颜色/名称/大小
range.format.fill.color                         # (只写) 背景色
range.format.border.style / .type / .color      # (只写) 边框线型/类型/颜色
range.format.h_align / .v_align                 # (只写) 水平/垂直对齐
range.format.number_format                      # (只写) 数字格式
range.format.wrap_text                          # (只写) 自动换行
range.format.column_width                       # (读写) 列宽
range.format.row_height                         # (读写) 行高
```

## Range — 操作

```
range.merge()                                   # 合并单元格
range.clear(contents=True, formats=True, comments=True)
range.delete(shift='up')                        # 删除区域
range.insert_rows(count=1)                      # 插入行
range.insert_columns(count=1)                   # 插入列
range.auto_fit(fit_type='auto')                 # 自适应列宽/行高
range.sort(key, order='asc', key2=None, order2='asc',
           key3=None, order3='asc', header=True, match_case=False)
range.auto_fill(target_addr)                    # 自动填充
```

## Range — 条件格式

```
range.add_format_condition(condition_type, operator=None,
    formula1=None, formula2=None, format_style=None, rank=None, lastone=False)
range.get_format_conditions() -> list[dict]
range.delete_format_condition(priority)
range.clear_format_conditions()
```

## Range — 图片

```
range.insert_picture(tag, path, target_row_from, target_row_to,
                     target_col_from, target_col_to)
```

## Range — 属性

```
range.address -> str                            # (只读) 区域地址
range.row_from / .row_to -> int                 # (只读) 起止行号（1-based）
range.col_from / .col_to -> int                 # (只读) 起止列号（1-based）
range.col_from_letter / .col_to_letter -> str   # (只读) 起止列字母
range.rows_count / .columns_count -> int        # (只读) 行数/列数
```

## PivotTable

```
pvt.pivot_fields() -> list[PivotField]
pvt.pivot_field(name) -> PivotField
pvt.row_fields() / column_fields() / data_fields() / page_fields()
pvt.add_data_field(field_name, caption='', function='sum')
pvt.add_fields(row_fields, column_fields, page_fields)
pvt.refresh()
pvt.set_table_style(style_name)
pvt.row_axis_layout(layout)                     # compact/tabular/outline
pvt.add_calculated_field(name, formula)
pvt.clear_all_filters()
pvt.clear_table()                               # 清空透视表（重置为初建状态）
pvt.delete()
pvt.subtotal_location(location)                 # top/bottom
pvt.set_grand_total_name(name)                  # 设置总计标题文字
pvt.set_merge_labels(merge)                     # 合并标签（需 outline 版式）
pvt.set_row_grand(show)                         # 显示/隐藏行总计
pvt.set_column_grand(show)                      # 显示/隐藏列总计

pvt.source_data  # (读写) 数据源地址
pvt.name         # (只读) 透视表名
pvt.location     # (只读) 左上角地址
pvt.table_range  # (只读) 完整范围
```

## PivotField

```
field.orientation   # (读写) hidden/row/column/page/data
field.position      # (读写) 字段位置
field.function      # (读写) 汇总函数
field.caption       # (读写) 字段标题
field.number_format # (读写) 数字格式
field.auto_sort(order, field_name)
field.clear_all_filters()
field.pivot_items() -> list[PivotItem]
field.delete()
```

## PivotItem

```
item.name      # (只读) 数据项名称
item.position  # (只读) 位置序号
item.visible   # (读写) 是否可见
```
