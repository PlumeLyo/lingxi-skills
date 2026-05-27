# 场景模板 XML 参考

各模板均遵循「严格基于转写、跳过空章节、默认富文本排版」原则。

## 通用转写模板

```xml
<h2>转写摘要</h2>
<p><strong>时间</strong>：[日期时间] &nbsp; <strong>主题</strong>：[主题]</p>
<h3>[主题一]</h3>
<columns>
  <column columnBackgroundColor="#EBF2FF">
    <h4>[发言人 / 子主题]</h4>
    <p listType="bullet" listLevel="0">[要点]</p>
    <blockquote>「[原话]」</blockquote>
  </column>
</columns>
<h3>后续行动</h3>
<p listType="todo" listLevel="0" checked="0">[行动项]</p>
```

## 会议纪要模板

```xml
<h2>会议纪要</h2>
<p><strong>主题</strong>：[主题] &nbsp; <strong>时间</strong>：[时间] &nbsp; <strong>参会</strong>：[人员]</p>
<h3>[议题一]</h3>
<columns>
  <column columnBackgroundColor="#EBF2FF">
    <h4>[发言人]</h4>
    <p listType="bullet" listLevel="0">[观点]</p>
    <blockquote>「[原话]」</blockquote>
  </column>
</columns>
<columns>
  <column columnBackgroundColor="#E8FCEF">
    <h4>结论 / 决策</h4>
    <p listType="bullet" listLevel="0">[决策]</p>
  </column>
</columns>
<h3>行动项</h3>
<p listType="todo" listLevel="0" checked="0">[任务]（负责人：XX，截止：XX）</p>
```

## 课堂笔记模板

```xml
<h2>课堂笔记</h2>
<p><strong>课程</strong>：[课程名] &nbsp; <strong>时间</strong>：[时间]</p>
<h3>核心知识点</h3>
<h4>[知识点一]</h4>
<p>[核心概念与讲解]</p>
<h3>重点强调</h3>
<p listType="bullet" listLevel="0">[重点1]</p>
<h3>作业与任务</h3>
<p listType="todo" listLevel="0" checked="0">[作业]（截止：XX）</p>
```

## 知识分享模板

```xml
<h2>知识分享记录</h2>
<p><strong>主题</strong>：[主题] &nbsp; <strong>分享人</strong>：[姓名]</p>
<h3>核心知识</h3>
<h4>[知识点一]</h4>
<p>[核心概念与实践经验]</p>
<h3>学习要点</h3>
<p listType="bullet" listLevel="0">[要点1]</p>
<h3>后续学习</h3>
<p listType="todo" listLevel="0" checked="0">[学习任务]</p>
```

## 直播/播客模板

```xml
<h2>内容纪要</h2>
<p><strong>标题</strong>：[标题] &nbsp; <strong>类型</strong>：[直播/播客]</p>
<h3>[主题一]</h3>
<columns>
  <column columnBackgroundColor="#FFF5EB">
    <h4>[嘉宾一] · [身份]</h4>
    <p listType="bullet" listLevel="0">[核心观点]</p>
    <blockquote>「[原话]」</blockquote>
  </column>
</columns>
<columns>
  <column columnBackgroundColor="#EBF2FF">
    <h4>[嘉宾二] · [身份]</h4>
    <p listType="bullet" listLevel="0">[核心观点]</p>
  </column>
</columns>
```

## 商务谈判模板

```xml
<h2>谈判记录</h2>
<p><strong>主题</strong>：[主题] &nbsp; <strong>各方</strong>：[甲方] vs [乙方]</p>
<h3>[议题一]</h3>
<columns>
  <column columnBackgroundColor="#EBF2FF">
    <h4>[甲方]</h4>
    <p listType="bullet" listLevel="0">[立场]</p>
  </column>
  <column columnBackgroundColor="#FFECEB">
    <h4>[乙方]</h4>
    <p listType="bullet" listLevel="0">[立场]</p>
  </column>
</columns>
<columns>
  <column columnBackgroundColor="#E8FCEF">
    <h4>达成协议</h4>
    <p listType="bullet" listLevel="0">[协议内容]</p>
  </column>
</columns>
<h3>待确认事项</h3>
<p listType="todo" listLevel="0" checked="0">[待确认]</p>
```

## 项目复盘模板

```xml
<h2>项目复盘</h2>
<p><strong>项目</strong>：[名称] &nbsp; <strong>时间</strong>：[时间]</p>
<h3>成果总结</h3>
<p>[量化与质化成果]</p>
<h3>问题与分析</h3>
<h4>[问题一]</h4>
<p>[原因分析与解决方案]</p>
<h3>经验教训</h3>
<p listType="bullet" listLevel="0">[成功经验/失败教训]</p>
<h3>改进行动</h3>
<p listType="todo" listLevel="0" checked="0">[改进项]（负责人：XX）</p>
```

## 专业场景（简略版）

- **庭审**：庭前准备→法庭调查→举证质证→法庭辩论→最后陈述
- **病例**：主诉→现病史→诊断→治疗方案→医嘱
- **新闻采访**：5W1H→精彩引用→后续跟进
- **电话录音**：通话目的→讨论内容→承诺事项→后续行动
- **采访记录**：话题→核心观点→精彩引用→后续跟进
- **培训课程**：课程大纲→知识点→实践练习→课后作业
- **口述转文章**：引言→章节→结论（口语转书面语）
