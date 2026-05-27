
def analyze_pages_structure(outline_file: str) -> str:
	"""
	解析 _outline.xml 文件，获取页面数量和每个页面对应的页面类型

	参数:
		outline_file: _outline.xml 文件路径

	返回:
		Markdown 格式的文本，包含页面数量和每个页面对应的页面类型
	"""
	import re
	from pathlib import Path

	# 读取文件内容
	try:
		content = Path(outline_file).read_text(encoding='utf-8')
	except FileNotFoundError:
		return f"错误：文件 {outline_file} 不存在"
	except Exception as e:
		return f"错误：读取文件失败 - {str(e)}"

	# 使用正则表达式提取所有页面信息
	# 匹配 <page number="数字"> ... </page> 块
	page_pattern = r'<page\s+number="(\d+)">(.*?)</page>'
	pages = re.findall(page_pattern, content, re.DOTALL)

	if not pages:
		return "错误：未找到任何页面信息"

	# 构建结果
	result_lines = [
		f"# PPT 页面结构分析\n",
		f"**总页数**: {len(pages)}\n",
		f"## 页面详情\n"
	]

	for page_num, page_content in pages:
		# 提取角色（页面类型）
		role_match = re.search(r'<role>(.*?)</role>', page_content, re.DOTALL)
		role = role_match.group(1).strip() if role_match else "未指定"
		# 添加页面信息
		result_lines.append(f"### 第 {page_num} 页")
		result_lines.append(f"- **页面类型**: {role}")
		result_lines.append("")  # 空行分隔

	return "\n".join(result_lines)

def analyze_page(outline_file: str, page_number: int) -> str:
	"""
	解析 _outline.xml 文件，获取指定页面的详细信息

	参数:
		outline_file: _outline.xml 文件路径
		page_number: 要分析的页面编号

	返回:
		Markdown 格式的文本，包含指定页面的详细信息
	"""
	import re
	from pathlib import Path

	# 读取文件内容
	try:
		content = Path(outline_file).read_text(encoding='utf-8')
	except FileNotFoundError:
		return f"错误：文件 {outline_file} 不存在"
	except Exception as e:
		return f"错误：读取文件失败 - {str(e)}"

	# 使用正则表达式提取指定页面信息
	page_pattern = rf'<page\s+number="{page_number}">(.*?)</page>'
	page_match = re.search(page_pattern, content, re.DOTALL)

	if not page_match:
		return f"错误：未找到第 {page_number} 页的信息"

	page_content = page_match.group(1)

	# 提取角色（页面类型）
	role_match = re.search(r'<role>(.*?)</role>', page_content, re.DOTALL)
	role = role_match.group(1).strip() if role_match else "未指定"

	# 提取标题
	title_match = re.search(r'<title>(.*?)</title>', page_content, re.DOTALL)
	title = title_match.group(1).strip() if title_match else "无标题"

	# 提取内容
	content_match = re.search(r'<content>(.*?)</content>', page_content, re.DOTALL)
	content_text = content_match.group(1).strip() if content_match else "无内容"

	# 提取布局
	layout_match = re.search(r'<layout>(.*?)</layout>', page_content, re.DOTALL)
	layout = layout_match.group(1).strip() if layout_match else "未知布局"

	# 提取视觉元素
	visuals = []
	for visual_match in re.finditer(r'<visual_element\s+type="(.*?)">(.*?)</visual_element>', page_content, re.DOTALL):
		ve_type = visual_match.group(1).strip()
		ve_text = visual_match.group(2).strip()
		visuals.append(f"  - type={ve_type}: {ve_text}")
	result_lines = [
		f"# 第 {page_number} 页分析\n",
		"---",
		f"- **页面类型**: {role}",
		"---",
		f"- **标题**: {title}",
		"---",
		f"- **内容**:\n\n{content_text}",
		"---",
		f"- **布局**: {layout}",
		"---",
		f"- **视觉元素**:\n" + "\n".join(visuals),
		"---",
	]

	return "\n".join(result_lines)

