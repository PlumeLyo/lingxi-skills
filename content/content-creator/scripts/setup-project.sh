#!/bin/bash
# Setup a new content writing project with standard structure
#
# Usage: ./setup-project.sh <project-name>
# Example: ./setup-project.sh "2024Q4-product-launch"

set -e

if [ $# -ne 1 ]; then
    echo "Usage: $0 <project-name>"
    echo "Example: $0 '2024Q4-product-launch'"
    exit 1
fi

PROJECT_NAME="$1"
PROJECT_DIR="./projects/${PROJECT_NAME}"

# Check if project already exists
if [ -d "$PROJECT_DIR" ]; then
    echo "❌ Error: Project '${PROJECT_NAME}' already exists at ${PROJECT_DIR}"
    exit 1
fi

# Create project directory structure
mkdir -p "$PROJECT_DIR"

# Create brief.md with template
cat > "${PROJECT_DIR}/brief.md" << 'EOF'
# 项目需求 (Client Brief)

## 基本信息
- **项目名称**: [填写项目名称]
- **截稿日期**: [填写日期]
- **目标平台**: [微信公众号/知乎/小红书/今日头条等]

## 需求描述
[在此描述核心需求：为什么要写这篇文章？]

## 目标受众
[描述目标读者群体：是谁？关心什么？]

## 核心信息点
- [关键点 1]
- [关键点 2]
- [关键点 3]

## 参考样张
[如有参考文章，列出路径或链接]

## 特殊要求
[任何特殊的格式、风格或内容要求]
EOF

# Create outline.md with template
cat > "${PROJECT_DIR}/outline.md" << 'EOF'
# 文章大纲 (Outline)

## 标题
[工作标题]

## 核心观点
[一句话概括文章的核心观点或价值]

## 结构框架

### 开篇
- [引子/痛点/场景]

### 主体
#### 第一部分
- [要点 1]
- [要点 2]

#### 第二部分
- [要点 1]
- [要点 2]

#### 第三部分（可选）
- [要点 1]
- [要点 2]

### 结尾
- [总结/升华/行动号召]

## 需要研究的问题
- [ ] [问题 1 - 需要论据支撑的观点]
- [ ] [问题 2 - 需要数据支撑的说法]
- [ ] [问题 3 - 需要案例说明的概念]

## 内部素材关键词
[用于搜索历史文章的关键词]

## 外部搜索主题
[用于网络搜索的主题]
EOF

# Create persona.md placeholder
cat > "${PROJECT_DIR}/persona.md" << 'EOF'
# 写作风格画像 (Persona)

## 整体基调
[描述整体语气和氛围]

## 句式特点
- [特点 1，如：长短句搭配，短句用于强调]
- [特点 2，如：多用设问引出话题]

## 词汇偏好
- [偏好 1，如：口语化表达，避免生僻词]
- [偏好 2，如：善用比喻和类比]

## 结构习惯
- [习惯 1，如：开篇常用个人经历引入]
- [习惯 2，如：段落较短，适合移动端阅读]

## 情感色彩
[理性/感性/幽默/严肃等]

## 典型表达
- [例句 1]
- [例句 2]
EOF

echo "✅ Project '${PROJECT_NAME}' created successfully at ${PROJECT_DIR}"
echo ""
echo "📁 Project structure:"
echo "   ${PROJECT_DIR}/"
echo "   ├── brief.md    (需求文档)"
echo "   ├── outline.md  (文章大纲)"
echo "   └── persona.md  (风格画像)"
echo ""
echo "📝 Next steps:"
echo "   1. Edit ${PROJECT_DIR}/brief.md - 填写项目需求"
echo "   2. Edit ${PROJECT_DIR}/outline.md - 设计文章结构"
echo "   3. Edit ${PROJECT_DIR}/persona.md - 定义写作风格"
echo "   4. Use search_notes MCP tool to find relevant notes"
echo "   5. Use web search for external research"
