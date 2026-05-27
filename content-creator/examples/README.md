# Content Creator 使用示例

本文档演示 content-creator Skill 的完整使用流程。

## 示例 1: 提取写作模板

### 用户输入

```
分析我上传的这篇文章，提取我的写作模板。
```

### Skill 执行流程

1. **接收样张**: `examples/sample-workflow/样张文章.md`
2. **运行分析**:
   ```bash
   python scripts/extract-template.py examples/sample-workflow/样张文章.md \
     --output examples/sample-workflow/template.json
   ```
3. **生成模板**: `template.json`

### 提取结果示例

```json
{
  "meta": {
    "extracted_from": "样张文章.md",
    "word_count": 1250,
    "style_type": "多层推演"
  },
  "structure": {
    "type": "多层推演",
    "paragraph_distribution": {
      "short": 0.45,
      "medium": 0.40,
      "long": 0.15
    },
    "avg_paragraph_length": 85
  },
  "language": {
    "sentence_avg_length": 18,
    "sentence_preference": "short",
    "punctuation_style": {
      "ellipsis": 8,
      "brackets": 5,
      "guillemets": 3
    },
    "common_transitions": ["坦白讲", "说实话", "后来", "所以"],
    "unique_patterns": [
      "自我质疑: 但，这真的对吗？",
      "转折: 后来我开始怀疑",
      "强调: 真正的问题"
    ]
  },
  "thinking": {
    "patterns": ["multi_layer_deduction", "emotional_arc"],
    "structure_pattern": "多层推演"
  },
  "bookends": {
    "opening": "自我介绍开场",
    "closing": "开放问题结尾"
  }
}
```

---

## 示例 2: 基于模板创作

### 用户输入

```
按照我刚上传的风格，写一篇关于 "远程工作效率" 的文章。
```

### Skill 执行流程

1. **读取模板**: `template.json`
2. **生成大纲**:
   ```bash
   python scripts/create-content.py \
     --template examples/sample-workflow/template.json \
     --topic "远程工作效率" \
     --output examples/sample-workflow/output
   ```
3. **输出文件**:
   - `outline.md` - 文章大纲
   - `writing-guide.md` - 风格指导
   - `draft.md` - 初稿占位

### 生成的大纲示例

```markdown
# 远程工作效率

## 文章大纲

**结构类型**: 多层推演
**创作时间**: 2026-03-12

### 开头（Hook）
- 【套路】自我介绍开场
- 引入话题，制造共鸣或好奇心

### 第一层：现象/案例
- 描述具体案例或现象
- 建立共识基础

### 第二层：初步洞察
- 从现象中提炼观点
- 提出初步结论

### 第三层：自我质疑
- 【使用模板中的质疑句式】
- 转折，提出问题

### 第四层：深层推演
- 深入分析
- 揭示本质

### 结尾
- 【套路】开放问题结尾
- 收束观点或开放思考

### 风格提示
- 复用表达: 自我质疑: 但，这真的对吗？
- 复用表达: 转折: 后来我开始怀疑
- 复用表达: 强调: 真正的问题
```

---

## 示例 3: 风格迁移

### 场景

用户想学习"刘润风格"，然后用该风格写自己的产品案例分析。

### 执行步骤

1. 上传刘润文章作为样张
2. 提取模板：`template-liurun.json`
3. 基于模板创作：
   ```bash
   python scripts/create-content.py \
     --template template-liurun.json \
     --topic "我们公司的产品案例分析" \
     --materials "产品资料.pdf" \
     --output output/
   ```

---

## 快速开始

### 1. 提取你的写作模板

```bash
# 准备一篇你最满意的文章，保存为 sample.md

python scripts/extract-template.py sample.md --output my-style.json
```

### 2. 查看提取的模板

```bash
cat my-style.json
```

### 3. 基于模板创作

```bash
python scripts/create-content.py \
  --template my-style.json \
  --topic "你想写的主题" \
  --output ./new-article
```

### 4. 查看生成的文件

```bash
ls ./new-article/
# outline.md  writing-guide.md  draft.md
```

---

## 进阶用法

### 保存多个模板

```bash
# 技术分析风格
python scripts/extract-template.py tech-article.md --output templates/tech.json

# 个人随笔风格
python scripts/extract-template.py essay.md --output templates/personal.json

# 产品分析风格
python scripts/extract-template.py product-review.md --output templates/product.json
```

### 按场景选择模板

```bash
# 技术话题用 tech 模板
python scripts/create-content.py -t templates/tech.json --topic "AI 原生存储"

# 个人成长话题用 personal 模板
python scripts/create-content.py -t templates/personal.json --topic "我的 2025"
```

---

## 注意事项

1. **样张质量决定模板质量**
   - 提供你最满意、最完整的文章
   - 建议篇幅 1000-5000 字
   - 避免提供片段或不完整的内容

2. **模板不是复制**
   - 提取的是"风格"不是"内容"
   - AI 会基于模板创作原创内容
   - 不会抄袭样张的具体表述

3. **可以迭代优化**
   - 先用模板创作一版
   - 根据结果调整模板参数
   - 或提供新的样张重新提取
