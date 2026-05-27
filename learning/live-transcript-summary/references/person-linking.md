# 人名知识联动 — 详细实现

本文件供 `SKILL.md` 中 Step 4.5 参考。

## 人名提取

```python
import re

def extract_names(sentences, speaker_map):
    """从转写句子中提取人名：speaker_map 中的已知姓名 + 职位词前缀匹配"""
    names = set(v for v in speaker_map.values() if "❓" not in v)  # 已确认的发言人
    title_pattern = re.compile(
        r'([\u4e00-\u9fa5]{1,3})'
        r'(总|经理|主任|主管|老师|工程师|总裁|总监|教授|博士|先生|女士|副总)'
    )
    for s in sentences:
        for m in title_pattern.finditer(s["text"]):
            names.add(m.group(1))
    return names
```

## 拆字搜索策略

```python
import subprocess, json

def search_person_notes(name, current_note_id):
    """
    搜索策略（优先级从高到低）：
      1. 全名搜索（如「张三」）
      2. 后两字搜索（如「三」→ 适合三字名）
      3. 单字姓搜索（如「张」→ 慎用，噪音大，仅当前两步无结果时尝试）
    每人最多返回 2 篇笔记 × 3 段上下文。
    """
    def _find(keyword, limit=3):
        out = subprocess.check_output(
            ["wpsnote-cli", "find", "--keyword", keyword, "--limit", str(limit), "--json"]
        )
        return json.loads(out)["data"]["notes"]

    notes = _find(name)
    if not notes and len(name) >= 3:
        notes = _find(name[-2:])  # 后两字
    if not notes and len(name) == 2:
        notes = _find(name[1])    # 名字单字（姓名2字时取名）

    results = []
    for note in notes[:2]:
        if note["note_id"] == current_note_id:
            continue
        ctx_out = subprocess.check_output(
            ["wpsnote-cli", "search", "--note_id", note["note_id"],
             "--query", name, "--json"]
        )
        snippets = json.loads(ctx_out)["data"].get("results", [])
        if snippets:
            results.append({
                "name": name,
                "note_title": note["title"],
                "snippets": [s.get("text", "")[:150] for s in snippets[:3]]
            })
    return results
```

## 注入摘要 Prompt

```python
def build_person_context(extracted_names, current_note_id, person_cache):
    """
    person_cache: state["person_cache"]，已搜过的人名直接复用，避免重复搜索
    返回注入文本（若无结果则返回空字符串）
    """
    lines = []
    for name in extracted_names:
        if name in person_cache:
            refs = person_cache[name]
        else:
            refs = search_person_notes(name, current_note_id)
            person_cache[name] = refs  # 缓存，本次 session 不重复搜

        for ref in refs:
            snippet = ref["snippets"][0] if ref["snippets"] else ""
            lines.append(f"- {name}（来自《{ref['note_title']}》）：{snippet}")

    if not lines:
        return ""
    return "\n\n[人物背景（来自笔记库，供参考，不强行引用）]:\n" + "\n".join(lines)
```

## 联动使用原则

- 背景信息**只补充人物背景**（角色、历史决策、所负责模块等），不替换转写内容
- 与当前转写无关联时**不写入摘要**
- 引用时在该人物色块内以小字注明：`（背景来自《笔记标题》）`
- 每人仅首次出现时搜索，结果缓存在 `state["person_cache"]`，后续轮次直接复用
- 单字搜索（策略3）噪音大，慎用；若返回超过 5 篇，放弃该轮搜索
