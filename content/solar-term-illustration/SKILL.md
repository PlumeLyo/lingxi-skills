---
name: solar-term-illustration
description: 生成中国古典二十四节气工笔重彩风格插画，纯插画无文字，21:9宽银幕比例。适用于创建节气主题海报、公众号封面、小红书配图、传统文化宣传素材等场景。当用户要求生成节气插画、节气海报、节气封面、传统文化插画时触发。
---

# 二十四节气插画生成技能

## 概述

本技能用于生成中国古典二十四节气工笔重彩风格插画，采用21:9宽银幕比例，纯插画无任何文字，适合海报、封面等视觉设计使用。

## 核心特性

- **风格**：工笔重彩，细腻笔触，传统国画意境
- **比例**：21:9（≈2.35:1）宽银幕比例
- **内容**：纯插画，无任何文字、印章
- **主题**：二十四节气及其三候物候现象
- **色调**：浅米黄宣纸纹理背景，柔和复古色彩

## 工作流程

### 1. 确定节气
根据用户需求确定要生成的节气，可以是：
- 单个节气（如"生成清明节气插画"）
- 多个节气（如"生成春季六个节气"）
- 全部二十四节气

### 2. 查阅参考资料
读取 `references/solar-terms-data.md` 获取节气三候信息，确保插画内容准确表现物候现象。

### 3. 构建提示词
使用 `references/prompt-templates.md` 中的模板，根据具体节气填充：
- 节气英文名和拼音
- 三候物候现象的英文描述
- 构图描述（前景、中景、背景）
- 色彩和氛围描述

### 4. 生成插画
使用 `generate_image` 工具，参数：
- `prompt`：构建好的提示词
- `aspect_ratio`：21:9
- `brief`：简要描述（如"生成立春节气插画"）

### 5. 整理输出
- 保存图片到工作目录
- 可创建HTML展示页面或文件列表
- 提供在线链接和本地路径

## 提示词构建示例

以立春节气为例：

```
Traditional Chinese painting illustration for "Start of Spring" (Lichun) solar term. Pure illustration without any text or characters. Gongbi (meticulous) heavy color style with fine brushwork. Color palette: soft warm beige, muted greens, subtle blues. Scene depicts spring phenomena: cracking ice on a river surface showing flowing water beneath, insects awakening near rocks, fish swimming under thin ice. Composition with foreground detailed rocks and ice cracks, midground riverbank with early spring plants, background misty mountains. Atmosphere: fresh, awakening, harmonious. Aspect ratio 21:9. No text, no characters, no seals.
```

## 资源说明

### references/
- `solar-terms-data.md`：二十四节气三候详细数据
- `prompt-templates.md`：提示词模板和英文翻译参考

### assets/
可存放生成的示例图片或模板文件。

## 使用示例

### 示例1：生成单个节气
用户请求："帮我生成谷雨节气的插画"
操作流程：
1. 读取 `references/solar-terms-data.md` 获取谷雨三候
2. 读取 `references/prompt-templates.md` 获取提示词模板
3. 构建谷雨专属提示词
4. 生成插画并保存

### 示例2：生成全部节气
用户请求："生成二十四节气全套插画"
操作流程：
1. 遍历24个节气
2. 为每个节气构建专属提示词
3. 依次生成所有插画
4. 创建HTML展示页面和文件列表

### 示例3：按季节生成
用户请求："生成夏季六个节气的插画"
操作流程：
1. 确定夏季节气：立夏、小满、芒种、夏至、小暑、大暑
2. 为每个节气构建提示词
3. 生成六张插画
4. 整理输出

## 注意事项

1. 确保插画中**不出现任何文字**，保持画面纯净
2. 严格遵循21:9宽银幕比例
3. 色调保持统一：浅米黄背景，柔和复古色彩
4. 每个节气的插画内容需准确表现其三候物候现象
5. 工笔重彩风格需保持一致，笔触细腻

## 扩展可能

- 可添加竖版3:4比例变体
- 可添加带节气名称文字的版本
- 可创建节气海报模板（插画+文字排版）
- 可生成节气主题系列封面图
