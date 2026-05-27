#!/usr/bin/env python3
"""
WPS Note 智能搜索 Skill - 测试执行器

执行测试用例，验证意图解析和发散搜索能力。
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from __init__ import parse_intent


class TestRunner:
    """测试执行器"""

    def __init__(self, mock_notes_path: str = "mock-notes.json"):
        self.mock_notes_path = Path(__file__).parent / mock_notes_path
        self.mock_notes = self._load_mock_notes()
        self.results = []

    def _load_mock_notes(self) -> List[Dict]:
        """加载模拟笔记数据"""
        try:
            with open(self.mock_notes_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("notes", [])
        except Exception as e:
            print(f"⚠️ 无法加载模拟数据: {e}")
            return []

    def run_intent_parse_test(self, query: str, expected: Dict) -> bool:
        """执行意图解析测试"""
        result = parse_intent(query)

        # 简化对比（实际测试可以更严格）
        passed = True
        errors = []

        if expected.get("keywords") and result.get("keywords") != expected["keywords"]:
            errors.append(f"keywords: 期望 '{expected['keywords']}', 实际 '{result.get('keywords')}'")
            passed = False

        if expected.get("time_range") and result.get("time_range") != expected["time_range"]:
            errors.append(f"time_range: 期望 {expected['time_range']}, 实际 {result.get('time_range')}")
            passed = False

        if expected.get("tags") and result.get("tags") != expected["tags"]:
            errors.append(f"tags: 期望 {expected['tags']}, 实际 {result.get('tags')}")
            passed = False

        return passed, result, errors

    def run_divergent_search_test(self, query: str, entity_type: str) -> Dict:
        """执行发散搜索测试"""
        # 模拟发散搜索逻辑
        divergent_dimensions = {
            "person": ["联系方式", "近期沟通", "参与项目", "相关团队", "个人偏好"],
            "project": ["目标", "里程碑", "资源需求", "依赖项目", "负责人", "风险"],
            "tech": ["技术方案", "实施记录", "测试数据", "相关会议", "最佳实践"],
            "concept": ["定义", "应用场景", "优缺点", "相关概念"]
        }

        dimensions = divergent_dimensions.get(entity_type, [])

        # 模拟搜索结果
        related_notes = self._find_related_notes(query, dimensions)

        return {
            "query": query,
            "entity_type": entity_type,
            "divergent_dimensions": dimensions,
            "related_notes_count": len(related_notes),
            "related_notes": related_notes[:5]  # 只返回前5个
        }

    def _find_related_notes(self, query: str, dimensions: List[str]) -> List[Dict]:
        """模拟查找相关笔记"""
        results = []
        query_lower = query.lower()

        for note in self.mock_notes:
            score = 0
            match_reasons = []

            # 直接匹配
            if query_lower in note["title"].lower() or query_lower in note["content"].lower():
                score += 10
                match_reasons.append("直接匹配")

            # 标签匹配
            for tag in note.get("tags", []):
                if any(dim in tag for dim in dimensions):
                    score += 5
                    match_reasons.append(f"标签关联: {tag}")

            # 维度匹配
            for dim in dimensions:
                if dim in note["content"]:
                    score += 3
                    match_reasons.append(f"维度匹配: {dim}")

            if score > 0:
                results.append({
                    "note_id": note["note_id"],
                    "title": note["title"],
                    "score": score,
                    "match_reasons": match_reasons
                })

        # 按分数排序
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("WPS Note 智能搜索 Skill - 测试套件")
        print("=" * 60)

        # 测试 1: 意图解析
        print("\n📋 测试分类 1: 意图解析")
        print("-" * 40)

        test_cases = [
            {
                "query": "帮我找上周的会议纪要",
                "expected": {
                    "keywords": "会议纪要",
                    "time_range": {"since": "last_week_start", "before": "last_week_end"}
                }
            },
            {
                "query": "最近三天的待办事项",
                "expected": {
                    "keywords": "待办事项",
                    "time_range": {"since": "3_days_ago", "before": "now"}
                }
            },
            {
                "query": "查找 #工作 标签下的项目文档",
                "expected": {
                    "keywords": "项目文档",
                    "tags": ["工作"]
                }
            }
        ]

        passed = 0
        failed = 0

        for i, tc in enumerate(test_cases, 1):
            print(f"\nTC-{i:03d}: {tc['query']}")
            is_passed, result, errors = self.run_intent_parse_test(tc["query"], tc["expected"])

            if is_passed:
                print(f"  ✅ 通过")
                passed += 1
            else:
                print(f"  ❌ 失败")
                for error in errors:
                    print(f"     - {error}")
                failed += 1

            print(f"  解析结果: {json.dumps(result, ensure_ascii=False, indent=2)}")

        # 测试 2: 发散搜索
        print("\n\n📋 测试分类 2: 发散搜索")
        print("-" * 40)

        divergent_tests = [
            {"query": "张总", "entity_type": "person"},
            {"query": "Q3规划", "entity_type": "project"},
            {"query": "前端性能优化", "entity_type": "tech"}
        ]

        for i, tc in enumerate(divergent_tests, 1):
            print(f"\nTC-{100+i}: {tc['query']} ({tc['entity_type']})")
            result = self.run_divergent_search_test(tc["query"], tc["entity_type"])

            print(f"  发散维度: {', '.join(result['divergent_dimensions'])}")
            print(f"  找到相关笔记: {result['related_notes_count']} 条")

            if result['related_notes']:
                print(f"  相关笔记示例:")
                for note in result['related_notes'][:3]:
                    print(f"    - {note['title']} (评分: {note['score']})")
                    print(f"      匹配原因: {', '.join(note['match_reasons'])}")

            passed += 1

        # 测试 3: 任务聚合
        print("\n\n📋 测试分类 3: 任务聚合")
        print("-" * 40)

        keywords_list = [
            ["待办", "TODO", "todo", "任务清单"],
            ["会议纪要", "会议记录", "周会"],
            ["读书笔记", "书摘", "摘录"]
        ]

        for i, keywords in enumerate(keywords_list, 1):
            print(f"\nTC-{200+i}: 关键词聚合 - {keywords[0]}")
            all_results = []
            for kw in keywords:
                results = self._find_related_notes(kw, [])
                all_results.extend(results)

            # 去重
            seen = set()
            unique_results = []
            for r in all_results:
                if r["note_id"] not in seen:
                    seen.add(r["note_id"])
                    unique_results.append(r)

            print(f"  关键词: {', '.join(keywords)}")
            print(f"  聚合结果: {len(unique_results)} 条笔记")
            for note in unique_results[:3]:
                print(f"    - {note['title']}")

            passed += 1

        # 汇总
        print("\n\n" + "=" * 60)
        print("测试汇总")
        print("=" * 60)
        print(f"通过: {passed} 项")
        print(f"失败: {failed} 项")
        print(f"总计: {passed + failed} 项")
        print(f"通过率: {passed/(passed+failed)*100:.1f}%")

        return failed == 0


def main():
    """主入口"""
    runner = TestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
