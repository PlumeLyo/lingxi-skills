---
name: xzsk-publisher
description: |
  【彳亍时刻公众号排版】将润色版 Markdown 文章一键转为公众号 HTML。
  支持四模板差异化排版：光迹(暖橙)/星光(冰蓝)/光境(金白)/余温(文艺散文)。
  触发词："彳亍排版""公众号排版""排个版""排版发布"。
  核心能力：读取润色版.md → 按板块品牌规范排版 → 输出可直接粘贴的 HTML。
metadata:
  version: "2.3.0"
  category: publishing
  tags: [wechat, xzsk, html-export, publishing, four-sections]
---

# 彳亍时刻公众号排版技能（v2.3 四模板版）

将润色版 Markdown 文章按彳亍时刻品牌规范转为公众号 HTML。
基于品牌完整方案的颜色系统，四个模板使用完全不同的配色、字体和排版参数。

## 四模板对比

| 维度 | 光迹 Glow | 星光 Starlight | 光境 Lumin | 余温 Warmth |
|------|-----------|----------------|------------|-------------|
| 标识 | `section="glow"` | `section="starlight"` | `section="lumin"` | `section="warmth"` |
| 标签 | Stray Moments · 光迹 | Stray Moments · 星光 | Stray Moments · 光境 | · 彳亍时刻 · |
| 定位 | 影像/过程记录 | 诗歌/思考沉淀 | 设计/长篇叙事 | 文艺散文/随笔 |
| 字体 | PingFang SC黑体 | PingFang SC黑体 | PingFang SC黑体 | Noto Serif SC宋体 |
| 正文字号 | 15px | 15px | 16px | 15px |
| 行高 | 1.8 | 2.0 | 2.2 | 2.2 |
| 标题色 | 深色 rgb(50,50,50) | 深色 rgb(33,33,33) | 深色 rgb(40,40,40) | 深墨 #3D3832 |
| 章节标题色 | 暖橙 rgb(245,124,0) | 靛蓝 rgb(121,134,203) | 深金 rgb(184,122,0) | 深墨 #3D3832 |
| 加粗色 | 暖橙 rgb(245,124,0) | 靛蓝 rgb(121,134,203) | 深金 rgb(184,122,0) | 深墨 #3D3832 |
| 正文色 | rgb(50,50,50) | rgb(50,50,50) | rgb(50,50,50) | #4A453E |
| 引用底色 | 浅橙 rgb(255,240,224) | 浅蓝 rgb(227,242,253) | 暖白 rgb(255,253,245) | #FAF9F6 |
| 引用边框 | 暖橙 | 靛蓝 | 金色 rgb(255,224,130) | #BFB5A4 |
| 页面底色 | 暖白 rgb(255,252,245) | 蓝灰 rgb(247,249,252) | 极浅暖 rgb(255,253,245) | #FAF9F6 |
| 首行缩进 | 无 | 无 | 2em | 2em |
| Logo | 有 | 有 | 有 | 无 |
| 在看按钮 | 有 | 有 | 有 | 无 |
| 复制按钮 | 有 | 有 | 有 | 无 |
| 底部品牌 | logo+板块名 | logo+板块名 | logo+板块名 | 纯文字细线 |
| 背景方案 | body background-color | body background-color | body background-color | table bgcolor（公众号兼容） |
| 颜色格式 | rgb() | rgb() | rgb() | #HEX十六进制 |
| 颜色情绪 | 暖橙余晖 | 冰蓝坐标 | 金白充盈 | 米色纸页 |

## 余温模板说明

余温（Stray Warmth）是独立的文艺散文排版模板，源自五一归途手写排版风格。

核心特征：
- 宋体+Noto Serif SC，letter-spacing:6px 标题字间距
- 米色纸张底 #FAF9F6，用 `<table bgcolor>` 实现公众号编辑器兼容
- 极简装饰：细线分隔、无logo、无按钮、无复制栏
- 标题汉字间加空格模拟书法散字效果（"五 一 归 途"）
- 副标题自动取标题下一行短句

## 使用方法

### Python 脚本调用（推荐）

```python
import sys, os
sys.path.insert(0, os.path.join(os.getenv('SKILL_PATH'), 'xzsk-publisher'))
from xzsk_publish import xzsk_publish

# 星光板块（诗歌/心理/思考，默认）
result = xzsk_publish(md_path="文章_润色版.md", section="starlight")

# 光迹板块（影像/记录/街拍）
result = xzsk_publish(md_path="文章_润色版.md", section="glow")

# 光境板块（长文/设计/年度复盘）
result = xzsk_publish(md_path="文章_润色版.md", section="lumin")

# 余温模板（文艺散文/随笔）
result = xzsk_publish(md_path="文章_润色版.md", section="warmth")

# 指定输出路径和日期
result = xzsk_publish(
    md_path="文章_润色版.md",
    output_path="输出路径.html",
    date_str="2026年6月1日",
    section="starlight"
)
```

### 板块选择指南

```
这篇文章属于哪个板块？
    │
    ├── 影像/街拍/迁徙记录/日常碎片 → section="glow"（光迹）
    ├── 诗歌/心理/读书/认知短思   → section="starlight"（星光）
    ├── 长篇叙事/设计/品牌宣言/复盘 → section="lumin"（光境）
    └── 文艺散文/随笔/生活感悟      → section="warmth"（余温）
```

跨板块内容默认使用 `starlight`。

## Markdown 转换规则

| Markdown | HTML |
|----------|------|
| `# 标题` | Header中h2深色居中 |
| `## 章节` | h2 板块色标题 + 上方hr |
| `**加粗**` | span 板块色加粗 |
| `> 引用` | blockquote 板块专属底色+边框 |
| `---` / `···` | hr 分隔线 |
| `—— 朴丰` | 跳过 |
| 互动问题（文末？短句） | Footer 互动区 |

## 踩坑记录

1. **公众号编辑器不支持 `background-color`**：section的 `background-color` / `background:#hex` 会被编辑器剥离。余温模板改用 `<table bgcolor="#FAF9F6">` 作为背景容器，HTML属性级别的底色编辑器不敢动。
2. **颜色格式与编辑器兼容性**：余温模板使用 #HEX 十六进制格式，与原版五一归途保持一致。brand三模板使用 rgb() 格式无影响（它们的背景在body上，section内是白底）。
3. **大字符串拼接风险**：不要在 Python 脚本中内嵌 base64 大字符串（如纸张纹理），会导致文件损坏。外部资源用文件读取。
4. **金色 #ffc107 对比度不足**：不能直接当白底文字色，已用对应板块深色替代。

## 资源依赖

1. logo 路径：`C:\Users\羽涅\Desktop\内容创作\素材库\logo\logo无背景1.png`
2. 颜色来源：品牌完整方案颜色系统（v1.0 / 2026-05-27）
3. 排版规范来源：品牌完整方案 6.2 公众号排版速查
4. 所有样式内联，不使用 class/flex/grid/rgba/CSS变量
