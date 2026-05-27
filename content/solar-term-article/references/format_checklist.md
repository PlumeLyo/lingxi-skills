# 节气文案格式备忘录（最终版）

## 必须遵守的格式要求（已测试可复制）

### 1. 装饰元素（最重要）
```html
<p style="border-top:1px solid #9B8AA5;width:32px;margin:0 auto 24px;"></p>
```
- 必须使用`border-top`，不能用`background`
- 必须使用`<p>`标签，不能用`<div>`
- 必须内联样式

### 2. 字号规范
- 正文：15px
- 板块主标题：20px，居中
- 固定关注引导：12px，居中
- 彳亍时刻标题：20px，颜色淡紫#9B8AA5

### 3. 固定模板（文末必须）
```html
<section style="padding:28px 28px 40px;background:#FDFBF7;text-align:center;">
  <p style="border-top:1px solid #9B8AA5;width:32px;margin:0 auto 24px;"></p>
  <p style="font-size:12px;color:#9B8AA5;margin:0;line-height:1.8;">关注「彳亍时刻」，跟着节气，走过四季，也走过内心。</p>
</section>
```

### 4. 颜色规范
- 主文字：深灰#373737
- 辅助文字：淡紫#9B8AA5
- 背景：米白#FDFBF7（所有板块统一）

### 5. 布局原则
- 所有样式必须内联
- 板块主标题居中，有主标题的板块不要副标题
- 结语板块不显示标题
- 充足留白，板块间距大于行间距

## 检查清单（生成文案后核对）
- [ ] 装饰元素使用边框方案
- [ ] 所有样式内联
- [ ] 正文字号15px
- [ ] 主标题字号20px
- [ ] 彳亍时刻标题淡紫色
- [ ] 固定关注引导在文末
- [ ] 结语板块无标题
- [ ] 所有板块背景统一

## 重要提醒
此格式已通过用户测试，确保公众号编辑器可正常复制粘贴。后续所有节气文案必须严格遵循此格式。