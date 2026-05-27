# pyright: reportUndefinedVariable=false
"""
开源文献库 — 学术搜索、去重、并发调度
中英文论文共享的核心数据源 + 英文/中文特有数据源。
API 文档见 references/shared/academic-sources.md。
"""

import asyncio
import json
import os
import re
from urllib.parse import quote

import aiohttp


# ─── 统一数据结构 ───────────────────────────────────────────────

PAPER_TEMPLATE = {
    "title": "",
    "authors": "",           # 逗号分隔
    "year": None,
    "doi": "",
    "cited_by_count": 0,
    "abstract": "",
    "source": "",            # "openalex" / "semantic_scholar" / ...
    "journal": "",
    "pdf_url": "",
    "open_access": False,
}


# ─── 核心数据源（中英文共享） ───────────────────────────────────

async def search_openalex(query: str, per_page=5):
    """OpenAlex — 完全免费，无需 Key，2.5 亿+文献"""
    url = "https://api.openalex.org/works"
    params = {
        "search": query, "per_page": per_page,
        "sort": "cited_by_count:desc",
        "select": "id,title,authorships,publication_year,doi,"
                  "cited_by_count,abstract_inverted_index,"
                  "primary_location,open_access,type"
    }
    # 可选: params["mailto"] = "your@email.com" 进入 Polite Pool
    # Abstract 为倒排索引，需还原为正常文本
    # 期刊名：primary_location.source.display_name
    # 中文文献过滤：filter=language:zh
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            data = await resp.json()
            return [_parse_openalex(w) for w in data.get("results", [])]


def _parse_openalex(work):
    authors = ", ".join(a["author"]["display_name"] for a in work.get("authorships", []) if a.get("author"))
    abstract = ""
    inv_idx = work.get("abstract_inverted_index")
    if inv_idx:
        words = sorted(((pos, word) for word, positions in inv_idx.items() for pos in positions))
        abstract = " ".join(w for _, w in words)
    loc = work.get("primary_location") or {}
    source = loc.get("source") or {}
    return {
        "title": work.get("title", ""),
        "authors": authors,
        "year": work.get("publication_year"),
        "doi": (work.get("doi") or "").replace("https://doi.org/", ""),
        "cited_by_count": work.get("cited_by_count", 0),
        "abstract": abstract,
        "source": "openalex",
        "journal": source.get("display_name", ""),
        "pdf_url": (loc.get("pdf_url") or ""),
        "open_access": work.get("open_access", {}).get("is_oa", False),
    }


async def search_semantic_scholar(query: str, limit=5):
    """Semantic Scholar — 2 亿+，影响力指标。免费 100 请求/5 分钟。"""
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query, "limit": limit,
        "fields": "title,authors,year,externalIds,citationCount,"
                  "abstract,openAccessPdf,journal,url"
    }
    # 可选: headers = {"x-api-key": "KEY"} 提高限额
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            data = await resp.json()
            return [_parse_s2(p) for p in data.get("data", [])]


def _parse_s2(paper):
    return {
        "title": paper.get("title", ""),
        "authors": ", ".join(a.get("name", "") for a in paper.get("authors", [])),
        "year": paper.get("year"),
        "doi": (paper.get("externalIds") or {}).get("DOI", ""),
        "cited_by_count": paper.get("citationCount", 0),
        "abstract": paper.get("abstract", "") or "",
        "source": "semantic_scholar",
        "journal": (paper.get("journal") or {}).get("name", ""),
        "pdf_url": (paper.get("openAccessPdf") or {}).get("url", ""),
        "open_access": paper.get("openAccessPdf") is not None,
    }


async def search_crossref(query: str, rows=5):
    """CrossRef — 1.5 亿+ DOI 文献，权威元数据。加 User-Agent 进 Polite Pool。"""
    url = "https://api.crossref.org/works"
    params = {"query": query, "rows": rows, "sort": "relevance",
              "select": "DOI,title,author,published-print,"
                        "is-referenced-by-count,abstract,container-title,type"}
    headers = {"User-Agent": "AcademicPaperWriter/1.0 (mailto:user@example.com)"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers,
                               timeout=aiohttp.ClientTimeout(total=15)) as resp:
            data = await resp.json()
            return [_parse_crossref(w) for w in data.get("message", {}).get("items", [])]


def _parse_crossref(work):
    authors = ", ".join(
        f"{a.get('family', '')} {a.get('given', '')}".strip()
        for a in work.get("author", [])
    )
    pub = work.get("published-print") or work.get("published-online") or {}
    date_parts = pub.get("date-parts") or [[]]
    year = date_parts[0][0] if date_parts and date_parts[0] else None
    return {
        "title": (work.get("title") or [""])[0],
        "authors": authors,
        "year": year,
        "doi": work.get("DOI", ""),
        "cited_by_count": work.get("is-referenced-by-count", 0),
        "abstract": work.get("abstract", "") or "",
        "source": "crossref",
        "journal": (work.get("container-title") or [""])[0],
        "pdf_url": "",
        "open_access": False,
    }


async def search_pubmed(query: str, retmax=5):
    """PubMed — 3600 万+生物医学。两步查询：esearch → esummary。"""
    esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {"db": "pubmed", "term": query, "retmax": retmax, "retmode": "json"}
    async with aiohttp.ClientSession() as session:
        async with session.get(esearch_url, params=params,
                               timeout=aiohttp.ClientTimeout(total=15)) as resp:
            data = await resp.json()
            ids = data.get("esearchresult", {}).get("idlist", [])
        if not ids:
            return []
        esummary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        params2 = {"db": "pubmed", "id": ",".join(ids), "retmode": "json"}
        async with session.get(esummary_url, params=params2,
                               timeout=aiohttp.ClientTimeout(total=15)) as resp:
            data = await resp.json()
            results = []
            for uid in ids:
                doc = data.get("result", {}).get(uid, {})
                if not doc or "error" in doc:
                    continue
                authors = ", ".join(a.get("name", "") for a in doc.get("authors", []))
                _pubdate = (doc.get("pubdate") or "")[:4]
                results.append({
                    "title": doc.get("title", ""),
                    "authors": authors,
                    "year": int(_pubdate) if _pubdate.isdigit() else None,
                    "doi": next((eid.get("value", "") for eid in doc.get("articleids", []) if eid.get("idtype") == "doi"), ""),
                    "cited_by_count": 0,
                    "abstract": "",
                    "source": "pubmed",
                    "journal": doc.get("fulljournalname", ""),
                    "pdf_url": "",
                    "open_access": False,
                })
            return results


async def search_core(query: str, limit=5, api_key=""):
    """CORE — 2 亿+开放获取。需注册获取免费 API Key。"""
    url = "https://api.core.ac.uk/v3/search/works"
    params = {"q": query, "limit": limit}
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers,
                               timeout=aiohttp.ClientTimeout(total=15)) as resp:
            data = await resp.json()
            return [_parse_core(r) for r in data.get("results", [])]


def _parse_core(result):
    return {
        "title": result.get("title", ""),
        "authors": ", ".join(a.get("name", "") for a in result.get("authors", [])),
        "year": result.get("yearPublished"),
        "doi": result.get("doi", "") or "",
        "cited_by_count": result.get("citationCount", 0),
        "abstract": result.get("abstract", "") or "",
        "source": "core",
        "journal": result.get("publisher", ""),
        "pdf_url": result.get("downloadUrl", "") or "",
        "open_access": True,
    }


async def search_google_scholar(query: str, hl='en'):
    """Google Scholar — 爬虫，反爬严格，低频使用，加随机延时 2-5s。"""
    import random
    await asyncio.sleep(random.uniform(2, 5))
    url = f"https://scholar.google.com/scholar?q={quote(query)}&hl={hl}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers,
                               timeout=aiohttp.ClientTimeout(total=15)) as resp:
            html = await resp.text()
            return _parse_google_scholar(html)


def _parse_google_scholar(html):
    papers = []
    for block in re.findall(r'<div class="gs_ri">(.*?)</div>\s*</div>', html, re.DOTALL):
        title_m = re.search(r'class="gs_rt"[^>]*>.*?>(.*?)</a>', block, re.DOTALL)
        author_m = re.search(r'class="gs_a">(.*?)</div>', block)
        abstract_m = re.search(r'class="gs_rs">(.*?)</div>', block, re.DOTALL)
        cited_m = re.search(r'Cited by (\d+)', block)
        if title_m:
            title = re.sub(r'<[^>]+>', '', title_m.group(1)).strip()
            author_line = re.sub(r'<[^>]+>', '', author_m.group(1)).strip() if author_m else ""
            papers.append({
                "title": title,
                "authors": author_line.split(" - ")[0].strip() if " - " in author_line else author_line,
                "year": int(m.group(1)) if (m := re.search(r'(\d{4})', author_line)) else None,
                "doi": "",
                "cited_by_count": int(cited_m.group(1)) if cited_m else 0,
                "abstract": re.sub(r'<[^>]+>', '', abstract_m.group(1)).strip() if abstract_m else "",
                "source": "google_scholar",
                "journal": "",
                "pdf_url": "",
                "open_access": False,
            })
    return papers


# ─── 英文特有数据源 ─────────────────────────────────────────────

async def search_arxiv(query: str, max_results=5):
    """arXiv — 240万+ 预印本（CS/Physics/Math/Econ）。无需 Key，间隔 3s。"""
    import xml.etree.ElementTree as ET
    url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{query}",
        "start": 0, "max_results": max_results,
        "sortBy": "relevance", "sortOrder": "descending"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params,
                               timeout=aiohttp.ClientTimeout(total=15)) as resp:
            text = await resp.text()
            root = ET.fromstring(text)
            ns = {"a": "http://www.w3.org/2005/Atom"}
            papers = []
            for entry in root.findall("a:entry", ns):
                title = (entry.findtext("a:title", "", ns) or "").strip().replace("\n", " ")
                authors = ", ".join(a.findtext("a:name", "", ns) for a in entry.findall("a:author", ns))
                pub = entry.findtext("a:published", "", ns)
                year = int(pub[:4]) if pub else None
                link = entry.findtext("a:id", "", ns) or ""
                papers.append({
                    "title": title, "authors": authors, "year": year,
                    "doi": "", "cited_by_count": 0,
                    "abstract": (entry.findtext("a:summary", "", ns) or "").strip(),
                    "source": "arxiv", "journal": "arXiv",
                    "pdf_url": link.replace("/abs/", "/pdf/") if link else "",
                    "open_access": True,
                })
            return papers


async def search_doaj(query: str, page_size=5):
    """DOAJ — 900万+ 经验证的 OA 期刊论文。无需 Key。"""
    url = "https://doaj.org/api/search/articles/" + quote(query)
    params = {"pageSize": page_size}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params,
                               timeout=aiohttp.ClientTimeout(total=15)) as resp:
            data = await resp.json()
            papers = []
            for r in data.get("results", []):
                bib = r.get("bibjson", {})
                authors = ", ".join(a.get("name", "") for a in bib.get("author", []))
                _doaj_year = str(bib.get("year") or "")
                papers.append({
                    "title": bib.get("title", ""),
                    "authors": authors,
                    "year": int(_doaj_year) if _doaj_year.isdigit() else None,
                    "doi": next((ident.get("id", "") for ident in bib.get("identifier", []) if ident.get("type") == "doi"), ""),
                    "cited_by_count": 0,
                    "abstract": bib.get("abstract", "") or "",
                    "source": "doaj",
                    "journal": bib.get("journal", {}).get("title", ""),
                    "pdf_url": next((l.get("url", "") for l in bib.get("link", []) if l.get("type") == "fulltext"), ""),
                    "open_access": True,
                })
            return papers


async def search_europe_pmc(query: str, page_size=5):
    """Europe PMC — 4200万+ 生命科学文献。覆盖 PubMed + PMC + 预印本。无需 Key。"""
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    params = {"query": query, "format": "json", "pageSize": page_size, "resultType": "core"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params,
                               timeout=aiohttp.ClientTimeout(total=15)) as resp:
            data = await resp.json()
            papers = []
            for r in data.get("resultList", {}).get("result", []):
                papers.append({
                    "title": r.get("title", ""),
                    "authors": r.get("authorString", ""),
                    "year": int(r["pubYear"]) if str(r.get("pubYear", "")).isdigit() else None,
                    "doi": r.get("doi", "") or "",
                    "cited_by_count": r.get("citedByCount", 0),
                    "abstract": r.get("abstractText", "") or "",
                    "source": "europe_pmc",
                    "journal": r.get("journalTitle", ""),
                    "pdf_url": "",
                    "open_access": r.get("isOpenAccess", "N") == "Y",
                })
            return papers


async def check_unpaywall(doi: str, email="user@example.com"):
    """Unpaywall — 基于 DOI 查询 OA 可用性。非搜索引擎。每日 10 万次。"""
    url = f"https://api.unpaywall.org/v2/{doi}"
    params = {"email": email}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params,
                               timeout=aiohttp.ClientTimeout(total=10)) as resp:
            data = await resp.json()
            best = data.get("best_oa_location") or {}
            return best.get("url_for_pdf", "")


# ─── 中文特有数据源 ─────────────────────────────────────────────

async def search_cnki(query: str):
    """CNKI 学术搜索 — 中文文献首选。优先 JSON API，失败回退 HTML 解析。"""
    # 方案A: JSON API
    url = "https://scholar.cnki.net/api/search"
    params = {"q": query, "page": 1, "size": 10}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params,
                                   timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                if data.get("data"):
                    return [_parse_cnki(r) for r in data["data"]]
    except Exception:
        pass
    # 方案B: HTML 爬虫 fallback
    html_url = f"https://scholar.cnki.net/search?q={quote(query)}"
    headers = {"User-Agent": "Mozilla/5.0"}
    async with aiohttp.ClientSession() as session:
        async with session.get(html_url, headers=headers,
                               timeout=aiohttp.ClientTimeout(total=10)) as resp:
            html = await resp.text()
            return _parse_cnki_html(html)


def _parse_cnki(item):
    return {
        "title": item.get("title", ""),
        "authors": item.get("authors", ""),
        "year": item.get("year"),
        "doi": item.get("doi", ""),
        "cited_by_count": item.get("citedCount", 0),
        "abstract": item.get("abstract", ""),
        "source": "cnki",
        "journal": item.get("journal", ""),
        "pdf_url": "",
        "open_access": False,
    }


def _parse_cnki_html(html):
    papers = []
    blocks = re.split(r'class="result-table-list"', html)
    if len(blocks) <= 1:
        blocks = re.split(r'class="s-single"', html)

    for block in blocks[1:]:
        title_m = re.search(r'class="title"[^>]*>.*?<a[^>]*>(.*?)</a>', block, re.DOTALL)
        if not title_m:
            continue
        title = re.sub(r'<[^>]+>', '', title_m.group(1)).strip()
        if not title:
            continue

        author_m = re.search(r'class="author"[^>]*>(.*?)</(?:span|div|td)', block, re.DOTALL)
        authors = re.sub(r'<[^>]+>', '', author_m.group(1)).strip().replace(';', ', ') if author_m else ""

        journal_m = re.search(r'class="source"[^>]*>.*?<a[^>]*>(.*?)</a>', block, re.DOTALL)
        journal = re.sub(r'<[^>]+>', '', journal_m.group(1)).strip() if journal_m else ""

        year_m = re.search(r'class="date"[^>]*>.*?(\d{4})', block, re.DOTALL)
        year = int(year_m.group(1)) if year_m else None

        papers.append({
            **PAPER_TEMPLATE,
            "title": title, "authors": authors, "journal": journal,
            "year": year, "source": "cnki",
        })
    return papers


async def search_juren(query: str):
    """巨人学术 — 中文学术聚合搜索引擎。"""
    url = f"https://jurenxueshu.qingmo.net/search?keyword={quote(query)}"
    headers = {"User-Agent": "Mozilla/5.0"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers,
                               timeout=aiohttp.ClientTimeout(total=10)) as resp:
            html = await resp.text()
            papers = []
            for block in re.findall(r'class="paper-card">(.*?)</(?:article|section|div\s*>\s*</div)', html, re.DOTALL):
                title_m = re.search(r'class="title"[^>]*>(.*?)<', block)
                if not title_m:
                    continue
                title = re.sub(r'<[^>]+>', '', title_m.group(1)).strip()
                if not title:
                    continue

                author_m = re.search(r'class="author[^"]*"[^>]*>(.*?)<', block)
                authors = author_m.group(1).strip() if author_m else ""

                journal_m = re.search(r'class="(?:journal|source)"[^>]*>(.*?)<', block)
                journal = journal_m.group(1).strip() if journal_m else ""

                year_m = re.search(r'(\d{4})', block)
                year = int(year_m.group(1)) if year_m and 1900 < int(year_m.group(1)) <= 2030 else None

                papers.append({
                    **PAPER_TEMPLATE,
                    "title": title, "authors": authors, "journal": journal,
                    "year": year, "source": "juren",
                })
            return papers


# ─── Metaso（秘塔学术搜索，通过 WPS AI Gateway） ─────────────────

_METASO_URL = "https://lingxi.wps.cn/api/aioffice/v1/web_search"


async def search_metaso(query: str, page_size=10):
    """秘塔学术搜索 — 通过 WPS AI Gateway 调用，支持中英文学术文献。"""
    sid = os.environ.get("TMP_LX_UUID") or os.environ.get("wps_sid") or os.environ.get("WPS_SID") or ""
    if not sid:
        print("[WARNING] search_metaso: 缺少 wps_sid，跳过")
        return []
    cookies = {"wps_sid": sid, "csrf": sid}
    body = {
        "engine": "metaso",
        "query": query,
        # 新版接口参数包在 data.metaso 下；保留该结构与官方文档一致
        "metaso": {
            "scope": "scholar",
            "page": 1,
            "include_summary": False,
            "concise_snippet": False,
        },
    }
    headers = {
        "Content-Type": "application/json",
        "Origin": "https://lingxi.wps.cn",
        "Referer": "https://lingxi.wps.cn/",
        # "x-cc-region": "ys1",
    }
    async with aiohttp.ClientSession(cookies=cookies) as session:
        async with session.post(
            _METASO_URL, json=body, headers=headers,
            timeout=aiohttp.ClientTimeout(total=20),
        ) as resp:
            data = await resp.json()
            if data.get("result") != "ok":
                print(f"[WARNING] search_metaso: {data.get('msg', data.get('result', '未知错误'))}")
                return []
            data_obj = data.get("data") or {}
            # 新版：data.metaso.scholars；旧版：data.scholars
            metaso_obj = data_obj.get("metaso") or data_obj
            items = (
                metaso_obj.get("scholars")
                or metaso_obj.get("organic")
                or []
            )
            papers = [_parse_metaso(item) for item in items[:page_size]]
            return [p for p in papers if p.get("title")]


def _parse_metaso(item):
    authors_raw = item.get("authors") or []
    authors = ", ".join(authors_raw) if isinstance(authors_raw, list) else str(authors_raw)
    year = None
    date_str = item.get("date") or ""
    year_m = re.search(r'(\d{4})', date_str)
    if year_m:
        y = int(year_m.group(1))
        if 1900 < y <= 2030:
            year = y
    return {
        **PAPER_TEMPLATE,
        "title": (item.get("title") or "").strip(),
        "authors": authors,
        "year": year,
        "abstract": (item.get("snippet") or "").strip(),
        "source": "metaso",
        "pdf_url": item.get("link") or "",
    }


# ─── 质量过滤 ───────────────────────────────────────────────────

_MIN_ABSTRACT_LEN = 30


def _is_quality_paper(paper: dict) -> bool:
    """判断文献是否具备引用价值。缺少关键信息的文献不落盘、不进上下文。

    必须同时满足:
    1. 有标题且长度 > 5
    2. 有作者且非匿名
    3. 有摘要且长度 >= 30 字符（过短的摘要无参考价值）
    4. 有年份
    """
    title = (paper.get("title") or "").strip()
    authors = (paper.get("authors") or "").strip()
    abstract = (paper.get("abstract") or "").strip()
    year = paper.get("year")

    if not title or len(title) <= 5:
        return False
    if not authors or authors.lower() in ("anonymous", "unknown", "佚名"):
        return False
    if not abstract or len(abstract) < _MIN_ABSTRACT_LEN:
        return False
    if not year:
        return False
    return True


_CJK_RE = re.compile(r'[\u4e00-\u9fff]')


def _is_chinese_paper(paper: dict) -> bool:
    title = paper.get("title") or ""
    return bool(_CJK_RE.search(title))


# ─── 去重策略 ───────────────────────────────────────────────────

def dedup_papers(papers: list[dict]) -> list[dict]:
    """质量过滤 + DOI/标题去重。

    1. 先过滤掉缺少关键信息的文献（无摘要、无作者、无年份等）
    2. DOI 相同 → 合并（保留 cited_by_count 更高的）
    3. 标题相同 → 合并
    """
    seen_doi, seen_title, result = {}, {}, []
    skipped = 0
    for p in papers:
        if not _is_quality_paper(p):
            skipped += 1
            continue
        doi = (p.get("doi") or "").strip().lower()
        if doi and doi in seen_doi:
            if p.get("cited_by_count", 0) > seen_doi[doi].get("cited_by_count", 0):
                seen_doi[doi].update(p)
            continue
        norm_title = p["title"].strip().lower()
        if norm_title in seen_title:
            continue
        if doi:
            seen_doi[doi] = p
        seen_title[norm_title] = True
        result.append(p)
    if skipped:
        print(f"[质量过滤] 跳过 {skipped} 篇低质量文献（缺少摘要/作者/年份）")
    return result


# ─── 并发调度 ───────────────────────────────────────────────────

SEARCH_FUNCS = {
    "openalex": search_openalex,
    "semantic_scholar": search_semantic_scholar,
    "crossref": search_crossref,
    "pubmed": search_pubmed,
    "core": search_core,
    "google_scholar": search_google_scholar,
    "arxiv": search_arxiv,
    "doaj": search_doaj,
    "europe_pmc": search_europe_pmc,
    "cnki": search_cnki,
    "juren": search_juren,
    "metaso": search_metaso,
}


_PAGE_SIZE_PARAM = {
    "openalex": "per_page",
    "semantic_scholar": "limit",
    "crossref": "rows",
    "pubmed": "retmax",
    "core": "limit",
    "arxiv": "max_results",
    "doaj": "page_size",
    "europe_pmc": "page_size",
    "metaso": "page_size",
}


def _ensure_list(val, name: str = "参数") -> list:
    if isinstance(val, str):
        return [val]
    if not isinstance(val, (list, tuple)):
        return list(val) if val else []
    return list(val)


async def search_all(keywords, sources, per_page=5):
    """并发搜索多源多关键词。per_page 控制每源每关键词返回数量。"""
    keywords = _ensure_list(keywords, "keywords")
    sources = _ensure_list(sources, "sources")
    per_page = max(1, int(per_page))
    if not keywords or not sources:
        print("[search_all] keywords 或 sources 为空，跳过")
        return []
    sem = asyncio.Semaphore(3)
    gs_sem = asyncio.Semaphore(1)

    async def _limited(coro, src_name=""):
        s = gs_sem if src_name == "google_scholar" else sem
        async with s:
            return await coro

    tasks = []
    task_labels = []
    for src in sources:
        if src not in SEARCH_FUNCS:
            print(f"[WARNING] 未知数据源 '{src}'，跳过")
            continue
        fn = SEARCH_FUNCS[src]
        size_param = _PAGE_SIZE_PARAM.get(src)
        for kw in keywords:
            if size_param:
                tasks.append(_limited(fn(kw, **{size_param: per_page}), src))
            else:
                tasks.append(_limited(fn(kw), src))
            task_labels.append(f"{src}:{kw}")
    results = await asyncio.gather(*tasks, return_exceptions=True)
    papers = []
    for i, batch in enumerate(results):
        if isinstance(batch, Exception):
            print(f"[WARNING] {task_labels[i]} 检索失败: {type(batch).__name__}: {batch}")
            continue
        if isinstance(batch, list):
            papers.extend(batch)
    return dedup_papers(papers)


# ─── 文献池：落盘 + 精简输出 ──────────────────────────────────────

_MAX_ABSTRACT_CHARS = 500


def _paper_key(paper: dict) -> str:
    """去重键：优先 DOI，否则归一化标题。"""
    doi = (paper.get("doi") or "").strip().lower()
    if doi:
        return f"doi:{doi}"
    return f"title:{paper.get('title', '').strip().lower()}"


def _truncate_abstract(abstract: str) -> str:
    if not abstract or len(abstract) <= _MAX_ABSTRACT_CHARS:
        return abstract
    cut = abstract[:_MAX_ABSTRACT_CHARS]
    for sep in ('. ', '。', '；', '; '):
        idx = cut.rfind(sep)
        if idx > _MAX_ABSTRACT_CHARS // 2:
            return cut[:idx + len(sep)].strip()
    return cut.strip() + "..."


def _infer_doc_type(paper: dict) -> str:
    """根据来源和元数据推断文献类型标签。"""
    source = paper.get("source", "").lower()
    journal = (paper.get("journal") or "").lower()
    title = (paper.get("title") or "").lower()

    if source == "arxiv":
        return "[EB/OL]"
    if any(k in journal for k in ("conference", "proceedings", "workshop", "symposium",
                                   "会议", "论坛")):
        return "[C]"
    if any(k in title for k in ("thesis", "dissertation", "学位论文", "硕士", "博士",
                                 "毕业论文")):
        return "[D]"
    if any(k in journal for k in ("press", "publisher", "出版", "publishing")):
        return "[M]"
    return "[J]"


def _format_authors_for_ref(authors_raw: str) -> str:
    """作者格式化：<=3 全列；>3 截断为前 3 位 + 等/et al."""
    s = (authors_raw or "").strip().rstrip(".")
    if not s:
        return ""

    # 已带等/et al. 时不重复处理
    if re.search(r"(?:\bet\s*al\.?$|等)$", s, re.IGNORECASE):
        return s

    authors = [a.strip() for a in re.split(r"\s*[;,，；]\s*", s) if a.strip()]
    if not authors:
        return s
    if len(authors) <= 3:
        return ", ".join(authors)

    head = ", ".join(authors[:3])
    if re.search(r"[\u4e00-\u9fff]", s):
        return f"{head}, 等"
    return f"{head}, et al."


def _format_ref_text(paper: dict) -> str:
    """生成模板化引用文本（偏 GB/T 风格），不补全缺失字段。"""
    authors = _format_authors_for_ref(str(paper.get("authors") or ""))
    title = (paper.get("title") or "").strip().rstrip(".")
    journal = (paper.get("journal") or "").strip().rstrip(".")
    year = str(paper.get("year") or "").strip()
    url = (paper.get("pdf_url") or "").strip()
    date = str(paper.get("date") or "").strip()
    tag = _infer_doc_type(paper)

    # 统一“作者. 题名[类型]”前缀，后续字段按类型追加，缺失字段不猜测补全。
    prefix_parts = []
    if authors:
        prefix_parts.append(authors)
    if title:
        prefix_parts.append(f"{title}{tag}")
    elif tag:
        prefix_parts.append(tag)
    text = ". ".join(prefix_parts).strip()

    if journal:
        text += f". {journal}"
    if year:
        text += f", {year}"

    # 在线文献补充 URL（若有），并尽量保留抓到的日期字段。
    if tag in ("[EB/OL]", "[A/OL]"):
        if date:
            text += f" ({date})"
        if url:
            text += f". {url}"

    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\.\.", ".", text)
    if text and not text.endswith("."):
        text += "."
    return text


def _make_ref_key(paper: dict, existing_keys: set[str] | None = None) -> str:
    """生成引用 key（第一作者姓 + 年份），遇冲突自动加后缀 a/b/c。"""
    _author_parts = paper.get("authors", "").split(",")[0].strip().split()
    first_author = _author_parts[-1] if _author_parts else "Unknown"
    first_author = re.sub(r'[^\w]', '', first_author)
    year = paper.get("year") or "XXXX"
    base = f"{first_author}{year}"
    if existing_keys is None:
        return base
    if base not in existing_keys:
        return base
    for suffix in "abcdefghijklmnopqrstuvwxyz":
        candidate = f"{base}{suffix}"
        if candidate not in existing_keys:
            return candidate
    return f"{base}_{len(existing_keys)}"


def _save_refs_json(papers: list[dict], json_path: str):
    """将文献列表追加保存为 JSON 文件，用于 autoBibliography 自动生成参考文献。

    JSON 格式: [{ key, text, authors, title, year, journal, doi, url, source }, ...]
    key 冲突时自动加后缀（Wang2024 → Wang2024a）。
    """
    existing = []
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            try:
                existing = json.load(f)
            except (json.JSONDecodeError, ValueError):
                existing = []
    existing_keys = {e["key"] for e in existing if isinstance(e, dict) and "key" in e}

    for p in papers:
        key = _make_ref_key(p, existing_keys)
        existing_keys.add(key)
        p["_ref_key"] = key
        existing.append({
            "key": key,
            "text": _format_ref_text(p),
            "authors": p.get("authors", ""),
            "title": p.get("title", ""),
            "year": str(p.get("year") or ""),
            "journal": p.get("journal", ""),
            "doi": p.get("doi", ""),
            "url": p.get("pdf_url", ""),
            "source": p.get("source", ""),
        })

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)


def _format_pool_entry(paper: dict) -> str:
    """按文献池模板格式化一条文献。"""
    key = paper.get("_ref_key") or _make_ref_key(paper)
    abstract_text = paper.get("abstract", "")
    ref_text = _format_ref_text(paper)
    lines = [
        f"### {key}",
        f"- 引用文本：{ref_text}",
        f"- 作者：{paper.get('authors', '')}",
        f"- 标题：{paper.get('title', '')}",
        f"- 年份：{paper.get('year', '')}",
        f"- 期刊/来源：{paper.get('journal', '')}",
        f"- DOI：{paper.get('doi', '')}",
        f"- 被引量：{paper.get('cited_by_count', 0)}",
        f"- 摘要：{abstract_text}",
        f"- 检索来源：{paper.get('source', '')}",
        "",
    ]
    return "\n".join(lines) + "\n"


def _load_pool_keys(pool_path: str) -> tuple[set[str], int]:
    """从已有文献池提取 DOI/标题键集合和文献篇数。

    Returns:
        (keys, count): 去重用键集合 + 实际篇数
    """
    keys: set[str] = set()
    count = 0
    if not os.path.exists(pool_path):
        return keys, 0

    def _flush(doi: str, title: str):
        nonlocal count
        if doi or title:
            count += 1
        if doi:
            keys.add(f"doi:{doi}")
        if title:
            keys.add(f"title:{title}")

    with open(pool_path, "r", encoding="utf-8") as f:
        current_doi = ""
        current_title = ""
        in_entry = False
        for line in f:
            line = line.strip()
            if line.startswith("### "):
                if in_entry:
                    _flush(current_doi, current_title)
                current_doi = ""
                current_title = ""
                in_entry = True
            elif line.startswith("- DOI：") or line.startswith("- DOI:"):
                current_doi = line.split("：", 1)[-1].split(":", 1)[-1].strip().lower()
            elif line.startswith("- 标题：") or line.startswith("- 标题:"):
                current_title = line.split("：", 1)[-1].split(":", 1)[-1].strip().lower()
        if in_entry:
            _flush(current_doi, current_title)
    return keys, count


def _print_paper_full(paper: dict):
    """打印单篇文献的完整信息供模型使用。

    检索阶段需要完整摘要来判断文献与各章节的相关性，
    因此只对超长摘要（>500字符）做尾部截断，保留核心内容。
    """
    key = paper.get("_ref_key") or _make_ref_key(paper)
    print(f"### {key}")
    print(f"  引用文本：{_format_ref_text(paper)}")
    print(f"  作者：{paper.get('authors', '')}")
    print(f"  标题：{paper.get('title', '')}")
    print(f"  年份：{paper.get('year', '')} | 期刊：{paper.get('journal', '')} | DOI：{paper.get('doi', '')}")
    print(f"  被引量：{paper.get('cited_by_count', 0)} | 来源：{paper.get('source', '')}")
    abstract = paper.get("abstract", "")
    if abstract:
        print(f"  摘要：{_truncate_abstract(abstract)}")
    print()


def print_refs_summary(refs_json: str):
    """从落盘的 refs_json 中打印精简文献列表，供写作阶段查阅。

    每篇只输出一行：key + 作者(截断) + 年份 + 标题(截断)，
    便于模型在写每章时快速浏览可用文献并做引用决策。
    """
    if not os.path.exists(refs_json):
        print(f"[refs] 文件不存在: {refs_json}")
        return
    with open(refs_json, "r", encoding="utf-8") as f:
        try:
            refs = json.load(f)
        except (json.JSONDecodeError, ValueError):
            print("[refs] JSON 解析失败")
            return
    if not refs:
        print("[refs] 无文献记录")
        return

    print(f"=== 文献池 ({len(refs)} 篇) ===\n")
    for r in refs:
        key = r.get("key", "?")
        authors = r.get("authors", "")
        if len(authors) > 30:
            authors = authors[:30] + "..."
        year = r.get("year", "")
        title = r.get("title", "")
        if len(title) > 60:
            title = title[:60] + "..."
        print(f"  [@{key}] {authors} ({year}) {title}")
    print()


async def search_and_save(keywords, sources, per_page=5, refs_json="",
                          pool_path="", topic=""):
    """检索 + 去重，完整结果直接打印到 stdout 供模型使用。

    refs_json: 传入路径时将文献元数据落盘为 JSON（供 autoBibliography 自动生成参考文献）。
    pool_path: 兼容旧流程，传入时同时落盘到文献池 .md 文件。

    Args:
        keywords: 检索关键词列表（也接受单个字符串）
        sources: 数据源列表（也接受单个字符串）
        per_page: 每源每关键词返回数量（默认 5）
        refs_json: 可选，引用 JSON 文件路径，传入则自动落盘
        pool_path: 可选，文献池 .md 文件路径，传入则同时落盘
        topic: 论文主题（首次创建时写入）
    """
    keywords = _ensure_list(keywords, "keywords")
    sources = _ensure_list(sources, "sources")
    papers = await search_all(keywords, sources, per_page=per_page)

    existing_keys = set()
    existing_count = 0
    if pool_path:
        existing_keys, existing_count = _load_pool_keys(pool_path)
    new_papers = [p for p in papers if _paper_key(p) not in existing_keys]

    if refs_json and new_papers:
        _save_refs_json(new_papers, refs_json)

    if pool_path and new_papers:
        if not os.path.exists(pool_path):
            with open(pool_path, "w", encoding="utf-8") as f:
                f.write(f"# 文献池\n\n- 主题：{topic or '(待填写)'}\n- 收录：{len(new_papers)} 篇\n\n---\n\n")
        with open(pool_path, "a", encoding="utf-8") as f:
            for p in new_papers:
                f.write(_format_pool_entry(p))

    total = existing_count + len(new_papers)
    print(f"检索: {len(papers)} 篇, 去重后新增 {len(new_papers)} 篇, 累计 {total} 篇")
    print(f"关键词: {keywords} | 数据源: {sources}")
    if new_papers:
        print()
        for p in new_papers:
            _print_paper_full(p)

    return new_papers


# ─── 多轮批量检索 ─────────────────────────────────────────────

async def multi_round_search(
    rounds: list[dict],
    topic: str = "",
    target: int = 0,
    per_page: int = 5,
    refs_json: str = "",
    pool_path: str = "",
    zh_ratio: float = 0,
):
    """多轮批量检索，完整结果直接打印到 stdout，达到目标篇数后提前停止。

    每轮是一次 search_all 调用（多关键词 x 多源并发），轮间串行。
    rounds 中每个 dict 包含:
        keywords: list[str]  — 该轮使用的关键词
        sources:  list[str]  — 该轮使用的数据源
        per_page: int        — 可选，覆盖全局 per_page

    Args:
        rounds:    检索轮次列表，按顺序执行
        topic:     论文主题
        target:    目标篇数，达到后跳过后续轮次（0=不限制）
        per_page:  每源每关键词返回数量（默认 5，轮次可覆盖）
        refs_json: 可选，引用 JSON 文件路径，传入则每轮自动落盘
        pool_path: 可选，文献池 .md 文件路径，传入则同时落盘
        zh_ratio:  中文文献最低占比（0-1），如 0.3 表示中文文献≥30%。
                   所有用户轮次跑完后，若中文占比不足，自动追加中文检索轮次
                   （用 topic 的中文关键词检索 cnki/juren/openalex-zh）。
                   默认 0 表示不做中文比例约束。

    Returns:
        本次所有轮次新增的文献列表

    Example::

        await ac.multi_round_search(
            rounds=[
                {"keywords": ["bismuth photocatalyst degradation",
                              "Bi2WO6 hydrothermal photocatalytic"],
                 "sources": ["openalex", "semantic_scholar", "crossref"]},
                {"keywords": ["photocatalytic degradation mechanism radical",
                              "Bi2WO6 XRD SEM characterization"],
                 "sources": ["openalex", "semantic_scholar", "crossref"]},
            ],
            topic="铋基光催化剂降解有机污染物",
            target=50,
            refs_json=r'/path/to/references.json',
            per_page=5,
            zh_ratio=0.3,
        )
    """
    target = max(0, int(target))
    per_page = max(1, int(per_page))
    zh_ratio = float(zh_ratio)
    if zh_ratio > 1:
        zh_ratio = zh_ratio / 100.0
    zh_ratio = max(0.0, min(1.0, zh_ratio))
    if not rounds:
        print("[multi_round_search] rounds 为空，无检索轮次")
        return []

    all_new = []
    existing_keys = set()
    pool_total = 0
    if pool_path:
        existing_keys, pool_total = _load_pool_keys(pool_path)
        if not os.path.exists(pool_path):
            with open(pool_path, "w", encoding="utf-8") as f:
                f.write(f"# 文献池\n\n- 主题：{topic or '(待填写)'}\n- 收录：0 篇\n\n---\n\n")
    if refs_json and os.path.exists(refs_json):
        try:
            with open(refs_json, "r", encoding="utf-8") as f:
                _existing_refs = json.load(f)
            pool_total = max(pool_total, len(_existing_refs))
        except (json.JSONDecodeError, ValueError):
            pass
    executed = 0

    for i, rd in enumerate(rounds, 1):
        if target > 0 and pool_total >= target:
            print(f"第 {i}/{len(rounds)} 轮跳过: 已有 {pool_total} 篇, 达到目标 {target}")
            break

        kw = _ensure_list(rd.get("keywords", []), "keywords")
        src = _ensure_list(rd.get("sources", []), "sources")
        pp = max(1, int(rd.get("per_page", per_page)))

        papers = await search_all(kw, src, per_page=pp)
        new_papers = [p for p in papers if _paper_key(p) not in existing_keys]

        if refs_json and new_papers:
            _save_refs_json(new_papers, refs_json)

        if pool_path and new_papers:
            with open(pool_path, "a", encoding="utf-8") as f:
                for p in new_papers:
                    f.write(_format_pool_entry(p))

        for p in new_papers:
            existing_keys.add(_paper_key(p))

        pool_total += len(new_papers)
        all_new.extend(new_papers)
        executed += 1

        remaining = f", 距目标还差 {target - pool_total} 篇" if target > 0 and pool_total < target else ""
        print(f"── 第 {i}/{len(rounds)} 轮 ──  检索 {len(papers)} 篇, 新增 {len(new_papers)} 篇, "
              f"累计 {pool_total} 篇{remaining}")
        print(f"  关键词: {kw} | 数据源: {src}")
        if new_papers:
            print()
            for p in new_papers:
                _print_paper_full(p)

    # ── 中文比例自动补检索 ──
    if zh_ratio > 0 and pool_total > 0 and topic:
        zh_count = sum(1 for p in all_new if _is_chinese_paper(p))
        current_ratio = zh_count / pool_total if pool_total else 0
        if current_ratio < zh_ratio:
            zh_need = max(1, int(pool_total * zh_ratio) - zh_count)
            zh_kws = [kw for kw in re.split(r'[,;，；\s]+', topic) if kw]
            if not zh_kws:
                zh_kws = [topic]
            zh_sources = ["metaso", "openalex", "crossref", "doaj"]
            print(f"\n── 中文补检索 ──  当前中文 {zh_count}/{pool_total} ({current_ratio:.0%}), "
                  f"目标 ≥{zh_ratio:.0%}, 需补 ~{zh_need} 篇")

            zh_papers = await search_all(zh_kws, zh_sources, per_page=max(5, zh_need))
            zh_new = [p for p in zh_papers if _paper_key(p) not in existing_keys]

            if zh_new:
                if refs_json:
                    _save_refs_json(zh_new, refs_json)
                if pool_path:
                    with open(pool_path, "a", encoding="utf-8") as f:
                        for p in zh_new:
                            f.write(_format_pool_entry(p))
                for p in zh_new:
                    existing_keys.add(_paper_key(p))
                pool_total += len(zh_new)
                all_new.extend(zh_new)
                executed += 1
                print(f"  中文补检索新增 {len(zh_new)} 篇, 累计 {pool_total} 篇")
                print(f"  关键词: {zh_kws} | 数据源: {zh_sources}")
                print()
                for p in zh_new:
                    _print_paper_full(p)
            else:
                print(f"  中文补检索未找到新文献")

    print(f"\n{'='*60}")
    zh_final = sum(1 for p in all_new if _is_chinese_paper(p))
    en_final = len(all_new) - zh_final
    print(f"检索完成: 共执行 {executed} 轮, 新增 {len(all_new)} 篇 (中文 {zh_final} / 英文 {en_final}), 累计 {pool_total} 篇")
    if refs_json:
        print(f"引用数据: {refs_json}")
    return all_new
