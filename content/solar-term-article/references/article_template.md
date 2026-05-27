# 融合模板与排版规范（最终版）

## 排版规范（基于用户确认的最终格式）

### 基础样式
- **字体**：Noto Serif SC（衬线字体），回退到宋体
- **背景色**：米白色 #FDFBF7（所有板块统一背景）
- **文字颜色**：深灰色 #373737（主文字），淡紫色 #9B8AA5（辅助文字）
- **行高**：1.8-2.2，确保阅读舒适
- **字间距**：1-5pt，标题字间距较大

### 字号规范
- **正文**：固定15px
- **板块主标题**：20px，居中，有主标题的板块不要副标题
- **节气名称**：26pt
- **栏目标题**：9pt
- **副标题/引导语**：12pt
- **固定关注引导**：12px，居中
- **彳亍时刻标题**：20px，颜色淡紫#9B8AA5（与其他板块标题区分，形成前后呼应）

### 装饰元素规范
- **淡紫色小矩形**：宽32px，高1px，淡紫色#9B8AA5，居中，板块标题上方
- **必须实现方式**（已测试可复制）：
  ```html
  <p style="border-top:1px solid #9B8AA5;width:32px;margin:0 auto 24px;"></p>
  ```
- **重要说明**：
  1. 必须使用`border-top`而不是`background`
  2. 必须使用`<p>`标签而不是`<div>`
  3. 必须使用内联样式
  4. 此格式已通过用户测试，确保公众号编辑器可复制

### 布局原则
1. **板块主标题居中**，有主标题的板块不要副标题
2. **充足留白**，板块间距大于行间距
3. **统一背景**，所有板块使用相同背景色
4. **层级分明**，通过字号和颜色区分信息层级
5. **所有样式必须内联**，确保复制粘贴时格式保留

### 固定模板规范
文章最后一句必须包含：
```
关注「彳亍时刻」，跟着节气，走过四季，也走过内心。
```
- 字号：12px
- 颜色：淡紫色 #9B8AA5
- 对齐：居中
- 位置：结语板块之后，作为固定收尾
- 上方必须有装饰元素（淡紫色小矩形）

### 结语板块规范
- 结语板块不显示标题，直接显示内容
- 上方必须有装饰元素
- 标签（如#小满 #二十四节气等）使用12px，淡紫色，居中

### 完整HTML结构示例

#### 开篇板块
```html
<section style="padding:36px 24px 28px;background:#FDFBF7;text-align:center;">
  <p style="font-size:9pt;font-weight:300;letter-spacing:5pt;color:#9B8AA5;margin:0 0 20px;">彳亍时刻 · 节气</p>
  <p style="font-size:26pt;font-weight:300;letter-spacing:4pt;color:#373737;margin:0 0 6px;">小满</p>
  <p style="font-size:12pt;font-weight:300;letter-spacing:1.5pt;color:#9B8AA5;margin:0;">刚刚好就是最好</p>
</section>
```

#### 有标题的板块
```html
<section style="padding:28px 28px 32px;background:#FDFBF7;">
  <p style="border-top:1px solid #9B8AA5;width:32px;margin:0 auto 24px;"></p>
  <p style="font-size:20px;font-weight:300;letter-spacing:2px;color:#373737;text-align:center;margin:0 0 24px;">板块标题</p>
  {内容段落}
</section>
```

#### 彳亍时刻板块（特殊颜色）
```html
<section style="padding:28px 28px 36px;background:#FDFBF7;">
  <p style="border-top:1px solid #9B8AA5;width:32px;margin:0 auto 24px;"></p>
  <p style="font-size:20px;font-weight:300;letter-spacing:2px;color:#9B8AA5;text-align:center;margin:0 0 24px;">🌿 彳亍时刻</p>
  {内容段落}
</section>
```

#### 固定关注引导板块
```html
<section style="padding:28px 28px 40px;background:#FDFBF7;text-align:center;">
  <p style="border-top:1px solid #9B8AA5;width:32px;margin:0 auto 24px;"></p>
  <p style="font-size:12px;color:#9B8AA5;margin:0;line-height:1.8;">关注「彳亍时刻」，跟着节气，走过四季，也走过内心。</p>
</section>
```

### 内容段落样式
- **普通段落**：`<p style="margin:12px 0;line-height:1.8;font-size:15px;color:#373737;">{文本}</p>`
- **加粗文本**：`<b>{文本}</b>`
- **列表**：`<ul style="margin:12px 0;padding-left:20px;"><li style="margin:8px 0;line-height:1.8;font-size:15px;color:#373737;">{项目}</li></ul>`


### 一键复制按钮规范
- HTML预览页右下角加"复制全文"按钮，颜色#9B8AA5匹配节气品牌调性
- 按钮放在最外层`</section>`之后、`</body>`之前（不在任何section内）
- 使用fixed定位：`position:fixed;bottom:28px;right:28px;z-index:9999;`
- 按钮样式：圆角8px，14px字号，白色文字，带阴影
- hover变为#8A7B96，点击后变"已复制"+绿色反馈#8B9A82
- JS复制逻辑：`range.selectNode`选中所有section，只复制文章内容不含按钮
- 选中文字颜色：`::selection{background:#D6CEC2;color:#3D3832;}`

**复制按钮HTML结构**（放在最后一个section之后）：
```html
<button id="copy-btn" onclick="copyContent()" style="position:fixed;bottom:28px;right:28px;z-index:9999;padding:10px 22px;border:none;border-radius:8px;background:#9B8AA5;color:#fff;font-size:14px;font-family:'PingFang SC','Microsoft YaHei',sans-serif;cursor:pointer;box-shadow:0 4px 14px rgba(155,138,165,0.4);transition:all 0.3s ease;letter-spacing:1px;">复制全文</button>
<script>
function copyContent(){var s=document.querySelectorAll('section'),c=document.getElementById('copy-btn'),r=document.createRange(),f=document.createDocumentFragment();s.forEach(function(e){f.appendChild(r.createContextualFragment(e.outerHTML))});r.selectNodeContents(f);var sel=window.getSelection();sel.removeAllRanges();sel.addRange(r);try{document.execCommand('copy');sel.removeAllRanges();c.textContent='已复制';c.style.background='#8B9A82';setTimeout(function(){c.textContent='复制全文';c.style.background='#9B8AA5'},2000)}catch(e){sel.removeAllRanges();c.textContent='请手动选择';c.style.background='#C28B7A';setTimeout(function(){c.textContent='复制全文';c.style.background='#9B8AA5'},2000)}}
</script>
```

## 重要提醒
1. **装饰元素必须使用边框方案**：`border-top:1px solid #9B8AA5;width:32px;margin:0 auto 24px;`
2. **所有样式必须内联**：不使用外部CSS或<style>标签
3. **测试可复制性**：此格式已通过用户测试，确保公众号编辑器可正常复制粘贴
4. **保持一致性**：后续所有节气文案必须遵循此格式规范

## 文件命名规范
- **文本版**：`{节气名}-节气文案.txt`
- **HTML版**：`{节气名}-节气文案-公众号版.html`

## 生成流程
1. 确定节气信息（日期、三候）
2. 确定心理主题
3. 选择标题策略
4. 构建文章框架（选择板块）
5. 生成内容（文本版）
6. 应用排版模板（HTML版）
7. 保存文件