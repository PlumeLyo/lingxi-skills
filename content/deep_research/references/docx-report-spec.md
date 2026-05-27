# DOCX Report Spec

`report-spec.json` 是学术 DOCX 路径的通用内容协议，不属于某个单独模板实现。推荐结构是：

`通用 JSON spec -> 通用模板适配器 -> 具体模板实现`

## 一、版本字段

新建 spec 时，顶层显式写：

```json
{
  "spec_family": "docx-report-spec-v1"
}
```

当前 `cjc` 适配器消费的也是这份通用协议，而不是一份 CJC 私有 JSON。

## 二、核心字段

- `spec_family`：协议版本标识
- `title_cn` / `title_en`
- `authors_cn` / `authors_en`
- `affiliations_cn` / `affiliations_en`
- `abstract_cn` / `abstract_en`
- `keywords_cn` / `keywords_en`
- `classification_cn`
- `received_date` / `revised_date`
- `corresponding_author`
- `funding_cn` / `funding_en`
- `sections`
- `acknowledgements`
- `references`
- `appendices`
- `back_matter`

## 三、正文结构

正文固定使用：

- `sections[].level`
- `sections[].title`
- `sections[].paragraphs`
- `sections[].blocks[]`
- `sections[].subsections[]`

`paragraphs` 适合纯文本段落；`blocks[]` 适合需要混排表格、图片、子标题等内容的 section。二者可二选一；如果都提供，适配器优先读取 `blocks[]`。

### `blocks[]` 支持的类型

#### 1. 段落

```json
{
  "type": "paragraph",
  "text": "这是正文段落。"
}
```

#### 2. 子标题

```json
{
  "type": "subheading",
  "text": "研究设计"
}
```

#### 3. 表格

```json
{
  "type": "table",
  "rows": [
    ["模型", "准确率"],
    ["A", "91.2%"],
    ["B", "93.4%"]
  ]
}
```

当前表格能力只覆盖基础二维表；暂不支持合并单元格、列宽控制、复杂样式和表格脚注。

#### 4. 图片

```json
{
  "type": "image",
  "path": "/abs/path/figure-1.png",
  "width_inches": 4.8,
  "alignment": "center",
  "caption": "图1 模型总体架构"
}
```

图片 block 当前支持：

- `path` 或 `src`：本地图片路径；推荐绝对路径
- `width_inches` / `width_cm` / `width_mm` / `width_pt`
- `height_inches` / `height_cm` / `height_mm` / `height_pt`
- `alignment`：`left` / `center` / `right` / `justify`
- `caption`

当前图片能力只覆盖基础插图；暂不支持浮动环绕、题注自动编号、交叉引用和图注专用样式。

新写 spec 时，不要再发明这些旧字段：

- `body`
- `heading_1`
- `sub_sections`

当前 `cjc` 实现为了兼容历史输入，仍能容忍部分旧别名，但新流程不要继续产出这些结构。

## 四、适配器边界

- 通用 spec 负责表达内容，不负责表达某个模板的具体样式名
- 模板样式映射、分页、分栏、标题样式等细节，交给适配器实现
- 模板画像文件只描述某个模板实现的样式能力，不改变通用 spec 结构

## 五、可选稿件元信息

对期刊模板或正式投稿稿，允许补充以下可选稿件元信息：

- `received_date`
- `revised_date`
- `corresponding_author`
- `funding_cn`
- `funding_en`

示例：

```json
{
  "received_date": "2026-03-19",
  "revised_date": "2026-04-02",
  "corresponding_author": "张三，zhangsan@example.com",
  "funding_cn": "国家自然科学基金资助项目（No.12345678）；陕西省重点研发计划基金资助项目（No.2025XYZ001）",
  "funding_en": "The National Natural Science Foundation of China (No.12345678), The Key Research and Development Program of Shaanxi Province (No.2025XYZ001)"
}
```

约束：

- `received_date` 与 `revised_date` 是原始字段；适配器可按模板要求组合成 `收稿日期：...；修回日期：...`
- `corresponding_author` 默认是完整展示字符串，例如 `姓名，邮箱`
- `funding_cn` 与 `funding_en` 默认是完整展示字符串；如需多个项目，可直接在同一字符串里组织分号分隔
- 当前 `generic` 适配器已支持这些字段；其他适配器如未显式处理，可忽略它们

## 六、可选尾部结构

当模板存在“附中文参考文献”“作者简介”这类尾部专有块时，允许通过可选字段 `back_matter` 描述：

```json
{
  "back_matter": [
    {
      "kind": "references_cn",
      "title": "附中文参考文献",
      "items": [
        "[1] 中文补充参考文献。"
      ]
    },
    {
      "kind": "author_bios",
      "title": "作者简介",
      "items": [
        "张三，博士，主要研究领域为软件工程。"
      ]
    }
  ]
}
```

约束：

- `back_matter` 是通用扩展区，具体 `kind` 由适配器决定是否支持
- 当前 `jos` 适配器支持 `references_cn` 和 `author_bios`
- 不支持的 `kind` 会被适配器忽略
- `title` 可选；缺省时由适配器填默认标题

## 七、模板文件

优先从以下模板复制：

- `assets/docx-report-spec-template.json`
