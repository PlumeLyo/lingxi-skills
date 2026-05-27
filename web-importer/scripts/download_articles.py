# -*- coding=utf-8
"""
微信公众号文章下载工具
下载文章内容和图片到本地

使用方式：
1. 单链接下载：python3.11 download_articles.py "https://mp.weixin.qq.com/s/xxxxx"
2. 批量下载：python3.11 download_articles.py（使用内置列表）
3. 最新推文下载到历史推文：python3.11 download_articles.py --latest
"""
import requests
from bs4 import BeautifulSoup
import os
import re
import time
from urllib.parse import urlparse, parse_qs
import json
import sys
import datetime

# 文章列表
# 优先从外部文件加载：在脚本同目录下创建 articles.json（不提交到 git）
# 格式：[{"title": "文章标题", "url": "https://mp.weixin.qq.com/s/xxx"}, ...]
_ARTICLES_FILE = os.path.join(os.path.dirname(__file__), 'articles.json')
if os.path.exists(_ARTICLES_FILE):
    with open(_ARTICLES_FILE, 'r', encoding='utf-8') as _f:
        ARTICLES = json.load(_f)
else:
    ARTICLES = [
        # 示例，替换为你自己的文章链接，或创建 articles.json 文件
        {"title": "示例文章标题", "url": "https://mp.weixin.qq.com/s/xxxxxxxxxxxxxxxx"},
    ]

# 最新推文列表（下载到历史推文目录）
# 同样支持外部文件：latest_articles.json
_LATEST_FILE = os.path.join(os.path.dirname(__file__), 'latest_articles.json')
if os.path.exists(_LATEST_FILE):
    with open(_LATEST_FILE, 'r', encoding='utf-8') as _f:
        LATEST_ARTICLES = json.load(_f)
else:
    LATEST_ARTICLES = [
        # 示例，替换为你自己的最新文章链接，或创建 latest_articles.json 文件
        {"title": "示例最新文章标题", "url": "https://mp.weixin.qq.com/s/xxxxxxxxxxxxxxxx"},
    ]
# 请求头，模拟浏览器
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Connection': 'keep-alive',
}

def sanitize_filename(filename):
    """清理文件名，移除不合法字符"""
    # 移除或替换不合法字符
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # 移除前后空格
    filename = filename.strip()
    # 限制长度
    if len(filename) > 100:
        filename = filename[:100]
    return filename

def validate_wechat_url(url):
    """验证是否为有效的微信公众号文章链接"""
    if not url:
        return False
    return 'mp.weixin.qq.com' in url and ('/s/' in url or '/s?' in url)

def extract_mmdd_from_time(publish_time_str):
    """从发布时间字符串提取 MMDD 格式"""
    if not publish_time_str:
        return ''
    try:
        # 尝试解析时间格式，微信公众号通常是 "2024-01-25 08:30" 这样的格式
        time_obj = datetime.datetime.strptime(publish_time_str, '%Y-%m-%d %H:%M')
        return time_obj.strftime('%m%d')
    except:
        # 如果解析失败，尝试其他格式
        try:
            # 尝试只有日期的格式
            time_obj = datetime.datetime.strptime(publish_time_str.split()[0], '%Y-%m-%d')
            return time_obj.strftime('%m%d')
        except:
            return ''

def extract_yyyymmddhhmm_from_time(publish_time_str):
    """从发布时间字符串提取 yyyymmddhhmm 格式"""
    if not publish_time_str:
        return ''
    try:
        time_obj = datetime.datetime.strptime(publish_time_str, '%Y-%m-%d %H:%M')
        return time_obj.strftime('%Y%m%d%H%M')
    except:
        try:
            time_obj = datetime.datetime.strptime(publish_time_str.split()[0], '%Y-%m-%d')
            return time_obj.strftime('%Y%m%d') + '0000'
        except:
            return ''

def create_folder_name(publish_time, title, use_history_format=False):
    """生成文件夹名称
    use_history_format=False: MMDD 标题关键词（推文/已下载的推文）
    use_history_format=True:  yyyymmddhhmm_标题（历史推文）
    """
    if use_history_format:
        yyyymmddhhmm = extract_yyyymmddhhmm_from_time(publish_time)
        safe_title = sanitize_filename(title)
        if yyyymmddhhmm:
            return f"{yyyymmddhhmm}_{safe_title}"
        else:
            current_ts = datetime.datetime.now().strftime('%Y%m%d%H%M')
            return f"{current_ts}_{safe_title}"
    else:
        mmdd = extract_mmdd_from_time(publish_time)
        title_keywords = title[:15] if len(title) > 15 else title
        safe_keywords = sanitize_filename(title_keywords)
        if mmdd:
            return f"{mmdd} {safe_keywords}"
        else:
            current_mmdd = datetime.datetime.now().strftime('%m%d')
            return f"{current_mmdd} {safe_keywords}"

def download_image(img_url, save_path, max_retries=3):
    """下载单张图片，支持重试"""
    for retry in range(max_retries):
        try:
            response = requests.get(img_url, headers=HEADERS, timeout=30)
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True
            else:
                if retry < max_retries - 1:
                    print(f"      ⚠️  图片下载失败 (状态码: {response.status_code})，重试 {retry + 1}/{max_retries - 1}")
                    time.sleep(2)
                else:
                    print(f"      ❌ 图片下载失败 (状态码: {response.status_code})")
                    return False
        except Exception as e:
            if retry < max_retries - 1:
                print(f"      ⚠️  图片下载异常: {str(e)}，重试 {retry + 1}/{max_retries - 1}")
                time.sleep(2)
            else:
                print(f"      ❌ 图片下载异常: {str(e)}")
                return False
    return False

def _import_to_wps(article_dir: str, article_info: dict, img_dir: str):
    """
    将已下载的文章直接导入到 WPS 笔记（高质量模式：保留颜色/粗体/标题格式）。
    """
    import sys, os, importlib.util
    this_dir = os.path.dirname(os.path.abspath(__file__))
    wps_script = os.path.join(this_dir, 'wps_writer.py')
    if not os.path.exists(wps_script):
        print(f"   ⚠️  找不到 wps_writer.py，跳过 WPS 导入")
        return False

    spec = importlib.util.spec_from_file_location('wps_writer', wps_script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    if not mod.cli_check():
        print(f"   ⚠️  wpsnote-cli 未连接，跳过 WPS 导入")
        return False

    from pathlib import Path

    html_path = Path(article_dir) / '原文.html'
    img_path  = Path(img_dir)
    title     = article_info['title']
    publish_time = article_info.get('publish_time', '')

    # 解析 HTML → segments
    segments = mod.html_to_segments(html_path, img_path)
    if not segments:
        print(f"   ⚠️  html_to_segments 返回空，跳过 WPS 导入")
        return False

    xml_count = sum(1 for t, _ in segments if t == 'xml')
    img_count  = sum(1 for t, _ in segments if t == 'img')
    print(f"   [WPS] 解析完成: {xml_count} 段文字, {img_count} 张图片")

    # 创建笔记
    note_id = mod.cli_create_note(title)
    if not note_id:
        print(f"   ❌ WPS 创建笔记失败")
        return False
    mod.cli_sync(note_id)
    print(f"   [WPS] 创建笔记: {note_id}")

    # 写标题 + 时间行
    outline_data = mod.cli_get_outline(note_id)
    blocks = outline_data.get('blocks', [])
    if not blocks:
        print(f"   ❌ WPS 无法获取初始 blocks")
        return False
    first_id = blocks[0]['id']
    res = mod.cli_batch_edit(note_id, [
        {'op': 'replace', 'block_id': first_id, 'content': f'<h1>{title}</h1>'},
        {'op': 'insert', 'anchor_id': first_id, 'position': 'after',
         'content': f'<p>{publish_time}</p>' if publish_time else '<p></p>'},
    ])
    if res.get('ok') is False:
        print(f"   ❌ WPS 写标题失败: {res.get('message')}")
        return False

    # 写正文 + 占位符
    img_list = mod.write_content_with_placeholders(note_id, segments)
    print(f"   [WPS] 文字写入完成，{len(img_list)} 个图片占位符")

    # 插图
    if img_list:
        ok, fail = mod.find_and_insert_images(note_id, img_list)
        print(f"   [WPS] 图片插入: {ok}/{len(img_list)}")

    print(f"   ✅ WPS 导入完成：《{title}》")
    return True


def download_article(title, url, base_dir, max_retries=3, use_history_format=False,
                     import_wps=False):
    """下载单篇文章，支持重试"""
    print(f"\n📄 正在下载: {title}")
    
    # 文章下载重试逻辑
    for retry in range(max_retries):
        try:
            # 先下载文章内容获取发布时间
            print(f"   🌐 请求文章页面...")
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                if retry < max_retries - 1:
                    print(f"   ⚠️  请求失败 (状态码: {response.status_code})，重试 {retry + 1}/{max_retries - 1}")
                    time.sleep(2)
                    continue
                else:
                    print(f"   ❌ 请求失败 (状态码: {response.status_code})")
                    return False
            
            # 解析 HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取文章信息
            article_info = {
                'title': title,
                'url': url,
                'author': '',
                'publish_time': '',
                'content': '',
            }
            
            # 提取作者
            author_tag = soup.find('a', {'id': 'js_name'})
            if author_tag:
                article_info['author'] = author_tag.text.strip()
            
            # 提取发布时间
            time_tag = soup.find('em', {'id': 'publish_time'})
            publish_time_str = ''
            if time_tag and time_tag.text.strip():
                article_info['publish_time'] = time_tag.text.strip()
                publish_time_str = time_tag.text.strip()
            else:
                # 如果页面上没有显示时间，尝试从JavaScript变量中提取
                create_time_match = re.search(r'var createTime = [\'"]([^\'"]+)[\'"]', response.text)
                if create_time_match:
                    publish_time_str = create_time_match.group(1)
                    article_info['publish_time'] = publish_time_str
            
            # 创建文章目录（使用新的命名格式：MMDD 标题关键词）
            folder_name = create_folder_name(publish_time_str, title, use_history_format)
            article_dir = os.path.join(base_dir, folder_name)
            os.makedirs(article_dir, exist_ok=True)
            
            # 创建图片目录（改为"图片素材"）
            images_dir = os.path.join(article_dir, '图片素材')
            os.makedirs(images_dir, exist_ok=True)
        
            # 提取正文内容
            content_div = soup.find('div', {'id': 'js_content'})
            if not content_div:
                print(f"   ❌ 未找到文章内容")
                return False
            
            # 保存原始 HTML
            html_path = os.path.join(article_dir, '原文.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"   ✅ HTML 已保存")
            
            # 下载图片
            images = content_div.find_all('img')
            print(f"   🖼️  发现 {len(images)} 张图片")
            
            image_mapping = {}
            img_counter = 1
            failed_images = []
            
            for img in images:
                img_url = img.get('data-src') or img.get('src')
                if not img_url:
                    continue
                
                # 跳过表情图片和占位图
                if 'emotion' in img_url or 'mmbiz_png/0' in img_url:
                    continue
                
                # 确定图片扩展名
                ext = '.jpg'
                if '.png' in img_url:
                    ext = '.png'
                elif '.gif' in img_url:
                    ext = '.gif'
                elif '.webp' in img_url:
                    ext = '.webp'
                
                # 保存图片
                img_filename = f"image_{img_counter:03d}{ext}"
                img_path = os.path.join(images_dir, img_filename)
                
                print(f"      📥 下载图片 {img_counter}: {img_filename}")
                if download_image(img_url, img_path, max_retries=3):
                    local_path = f"./图片素材/{img_filename}"
                    image_mapping[img_url] = local_path
                    
                    # 替换 HTML 中的图片链接
                    img['src'] = local_path
                    if img.get('data-src'):
                        img['data-src'] = local_path
                    
                    # 在图片标签后添加一个特殊标记，用于 Markdown 转换
                    img['data-md-path'] = local_path
                    img_counter += 1
                else:
                    failed_images.append(img_filename)
                
                # 延迟避免请求过快
                time.sleep(1.5)
        
            # ── 转换并保存 ──────────────────────────────────────────────
            if import_wps:
                # 高质量模式：直接导入 WPS，保留颜色/粗体/标题格式
                wps_ok = _import_to_wps(article_dir, article_info, images_dir)
                if not wps_ok:
                    print(f"   ⚠️  WPS 导入失败，fallback 保存 Markdown")
                    import_wps = False  # 降级走 Markdown 路径

            if not import_wps:
                def is_bold_style(style_str):
                    """判断 style 属性是否包含加粗"""
                    if not style_str:
                        return False
                    s = style_str.lower().replace(' ', '')
                    return 'font-weight:bold' in s or 'font-weight:700' in s or 'font-weight:600' in s

                def is_italic_style(style_str):
                    """判断 style 属性是否包含斜体"""
                    if not style_str:
                        return False
                    s = style_str.lower().replace(' ', '')
                    return 'font-style:italic' in s

                def convert_to_markdown(element):
                    """递归转换 HTML 元素为 Markdown"""
                    if element.name is None:
                        return element.string if element.string else ''

                    if element.name == 'img':
                        md_path = element.get('data-md-path')
                        if md_path:
                            alt_text = element.get('alt', '图片')
                            return f"\n\n![{alt_text}]({md_path})\n\n"
                        return ''

                    result = []
                    for child in element.children:
                        result.append(convert_to_markdown(child))

                    text = ''.join(result)

                    if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        level = int(element.name[1])
                        return f"\n\n{'#' * level} {text.strip()}\n\n"
                    elif element.name == 'p':
                        stripped = text.strip()
                        if not stripped:
                            return ''
                        return f"\n\n{stripped}\n\n"
                    elif element.name in ['strong', 'b']:
                        inner = text.strip()
                        return f"**{inner}**" if inner else ''
                    elif element.name in ['em', 'i']:
                        inner = text.strip()
                        return f"*{inner}*" if inner else ''
                    elif element.name == 'span':
                        style = element.get('style', '')
                        inner = text
                        if is_bold_style(style) and is_italic_style(style):
                            stripped = inner.strip()
                            return f"***{stripped}***" if stripped else ''
                        elif is_bold_style(style):
                            stripped = inner.strip()
                            return f"**{stripped}**" if stripped else inner
                        elif is_italic_style(style):
                            stripped = inner.strip()
                            return f"*{stripped}*" if stripped else inner
                        return inner
                    elif element.name == 'a':
                        href = element.get('href', '')
                        inner = text.strip()
                        if href and inner:
                            return f"[{inner}]({href})"
                        return inner
                    elif element.name == 'blockquote':
                        lines = text.strip().splitlines()
                        quoted = '\n'.join(f"> {l}" for l in lines if l.strip())
                        return f"\n\n{quoted}\n\n" if quoted else ''
                    elif element.name == 'ul':
                        return f"\n{text}\n"
                    elif element.name == 'ol':
                        return f"\n{text}\n"
                    elif element.name == 'li':
                        stripped = text.strip()
                        parent = element.parent
                        if parent and parent.name == 'ol':
                            siblings = [s for s in parent.children if getattr(s, 'name', None) == 'li']
                            idx = siblings.index(element) + 1 if element in siblings else 1
                            return f"\n{idx}. {stripped}"
                        else:
                            return f"\n- {stripped}"
                    elif element.name == 'br':
                        return '\n'
                    elif element.name == 'section':
                        return text
                    else:
                        return text

                # 生成 Markdown 内容
                md_content = convert_to_markdown(content_div)
                md_content = re.sub(r'\n{3,}', '\n\n', md_content)
                article_info['content'] = md_content.strip()

                md_path = os.path.join(article_dir, '终稿.md')
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(f"{article_info['title']}\n")
                    f.write(md_content)
                print(f"   ✅ Markdown 已保存（终稿.md）")
            
            # 保存元数据
            meta_path = os.path.join(article_dir, 'meta.json')
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'title': article_info['title'],
                    'author': article_info['author'],
                    'publish_time': article_info['publish_time'],
                    'url': article_info['url'],
                    'images_count': len(image_mapping),
                    'failed_images_count': len(failed_images),
                    'download_time': time.strftime('%Y-%m-%d %H:%M:%S')
                }, f, ensure_ascii=False, indent=2)
            
            # 显示下载摘要
            print(f"\n   📊 下载摘要:")
            print(f"      📁 保存路径: {article_dir}")
            print(f"      🖼️  图片总数: {len(images)}")
            print(f"      ✅ 成功: {len(image_mapping)} 张")
            print(f"      ❌ 失败: {len(failed_images)} 张")
            if failed_images:
                print(f"      失败列表: {', '.join(failed_images)}")
            
            print(f"\n   ✅ 文章下载完成!")
            return True
            
        except Exception as e:
            if retry < max_retries - 1:
                print(f"   ⚠️  下载失败: {str(e)}，重试 {retry + 1}/{max_retries - 1}")
                time.sleep(2)
                continue
            else:
                print(f"   ❌ 下载失败: {str(e)}")
                import traceback
                traceback.print_exc()
                return False
    
    return False

def download_single_article_from_url(url):
    """从URL下载单篇文章"""
    print("=" * 80)
    print("微信公众号文章下载工具 - 单链接模式")
    print("=" * 80)
    
    # 验证链接
    if not validate_wechat_url(url):
        print("❌ 错误: 无效的微信公众号文章链接")
        print("\n使用说明:")
        print('  python3.11 download_articles.py "https://mp.weixin.qq.com/s/xxxxx"')
        return False
    
    print(f"📎 文章链接: {url}")
    
    # 创建保存目录（保存到"推文"目录）
    base_dir = os.path.join(os.path.dirname(__file__), '..', '推文')
    os.makedirs(base_dir, exist_ok=True)
    print(f"📁 保存目录: {os.path.abspath(base_dir)}\n")
    
    # 下载文章（不需要提供标题，会自动从页面提取）
    success = download_article_from_url(url, base_dir)
    
    if success:
        print("\n" + "=" * 80)
        print("✅ 下载成功!")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("❌ 下载失败")
        print("=" * 80)
    
    return success

def download_article_from_url(url, base_dir, max_retries=3, import_wps=False):
    """从URL下载文章（自动提取标题）"""
    print(f"\n📄 正在获取文章信息...")
    
    # 先请求一次获取标题
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            print(f"   ❌ 请求失败 (状态码: {response.status_code})")
            return False
        
        # 解析标题（多重兜底）
        soup = BeautifulSoup(response.text, 'html.parser')
        title = ""

        # 方案1: og:title meta 标签（最稳定）
        og_title = soup.find('meta', {'property': 'og:title'})
        if og_title and og_title.get('content', '').strip():
            title = og_title['content'].strip()

        # 方案2: js_title_inner span（微信标准结构）
        if not title:
            span = soup.find('span', {'class': 'js_title_inner'})
            if span and span.text.strip():
                title = span.text.strip()

        # 方案3: rich_media_title h1/h2
        if not title:
            title_tag = soup.find('h1', {'class': 'rich_media_title'}) or soup.find('h2', {'class': 'rich_media_title'})
            if title_tag and title_tag.text.strip():
                title = title_tag.text.strip()

        # 方案4: 正则从原始 HTML 中提取
        if not title:
            m = re.search(r'var\s+msg_title\s*=\s*["\']([^"\']+)["\']', response.text)
            if m:
                title = m.group(1).strip()

        if title:
            print(f"   📝 文章标题: {title}")
        else:
            print(f"   ⚠️  未找到标题，使用默认标题")
            title = "未命名文章"
        
        # 调用原有的下载函数
        return download_article(title, url, base_dir, max_retries, import_wps=import_wps)
        
    except Exception as e:
        print(f"   ❌ 获取文章信息失败: {str(e)}")
        return False

def batch_download():
    """批量下载模式"""
    print("=" * 80)
    print("微信公众号文章下载工具 - 批量下载模式")
    print("=" * 80)
    print(f"共 {len(ARTICLES)} 篇文章待下载")
    print("=" * 80)
    
    # 创建保存目录
    base_dir = os.path.join(os.path.dirname(__file__), '..', '已下载的推文')
    os.makedirs(base_dir, exist_ok=True)
    print(f"\n📁 保存目录: {os.path.abspath(base_dir)}\n")
    
    # 统计
    success_count = 0
    fail_count = 0
    
    # 下载所有文章
    for idx, article in enumerate(ARTICLES, 1):
        print(f"\n[{idx}/{len(ARTICLES)}]", end=" ")
        
        if download_article(article['title'], article['url'], base_dir):
            success_count += 1
        else:
            fail_count += 1
        
        # 延迟避免请求过快
        if idx < len(ARTICLES):
            print(f"\n   ⏳ 等待 5 秒...")
            time.sleep(5)
    
    # 输出统计
    print("\n" + "=" * 80)
    print("📊 下载完成统计")
    print("=" * 80)
    print(f"✅ 成功: {success_count} 篇")
    print(f"❌ 失败: {fail_count} 篇")
    print(f"📁 保存位置: {os.path.abspath(base_dir)}")
    print("=" * 80)

def download_latest_to_history(import_wps=False):
    """下载最新推文到历史推文目录"""
    print("=" * 80)
    print("微信公众号文章下载工具 - 最新推文 → 历史推文")
    print("=" * 80)
    print(f"共 {len(LATEST_ARTICLES)} 篇文章待下载")
    print("=" * 80)

    base_dir = os.path.join(os.path.dirname(__file__), '..', '历史推文')
    os.makedirs(base_dir, exist_ok=True)
    print(f"\n📁 保存目录: {os.path.abspath(base_dir)}\n")

    success_count = 0
    fail_count = 0

    for idx, article in enumerate(LATEST_ARTICLES, 1):
        print(f"\n[{idx}/{len(LATEST_ARTICLES)}]", end=" ")

        if download_article(article['title'], article['url'], base_dir, use_history_format=True,
                            import_wps=import_wps):
            success_count += 1
        else:
            fail_count += 1

        if idx < len(LATEST_ARTICLES):
            print(f"\n   ⏳ 等待 5 秒...")
            time.sleep(5)

    print("\n" + "=" * 80)
    print("📊 下载完成统计")
    print("=" * 80)
    print(f"✅ 成功: {success_count} 篇")
    print(f"❌ 失败: {fail_count} 篇")
    print(f"📁 保存位置: {os.path.abspath(base_dir)}")
    print("=" * 80)


def main():
    """主函数"""
    import_wps = '--wps' in sys.argv

    # 检查 --latest 参数
    if '--latest' in sys.argv:
        download_latest_to_history(import_wps=import_wps)
        return

    # 检查命令行参数
    if len(sys.argv) > 1:
        # 单链接下载模式（过滤掉 flag 参数）
        url = next((a for a in sys.argv[1:] if not a.startswith('--')), None)
        if url:
            base_dir = os.path.join(os.path.dirname(__file__), '..', '推文')
            os.makedirs(base_dir, exist_ok=True)
            download_article_from_url(url, base_dir, import_wps=import_wps)
        else:
            batch_download()
    else:
        # 批量下载模式
        batch_download()


if __name__ == '__main__':
    main()
