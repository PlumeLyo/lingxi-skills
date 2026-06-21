"""
科研可视化 — 公式渲染、化学结构、学术图表、流程图/架构图
中英文论文共享。图表标签语言应与论文语言一致。
"""

import io
import numpy as np
import platform
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch


# ─── 1. 化学结构式（RDKit，可选依赖） ──────────────────────────

def render_molecule(smiles: str, size=(400, 300)):
    """SMILES → PNG 图片。RDKit 不可用时返回 None。"""
    try:
        from rdkit import Chem
        from rdkit.Chem import Draw
    except ImportError:
        return None
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    img = Draw.MolToImage(mol, size=size)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


# ─── 2. 字体初始化（中英文通用，必须在所有绑图代码之前调用）───

def _ensure_cjk_font():
    """确保系统有可用的 CJK 字体，没有则自动下载。返回字体名或 None。"""
    available = {f.name for f in fm.fontManager.ttflist}
    system = platform.system()
    cjk_candidates = {
        'Windows': ['Microsoft YaHei', 'SimHei', 'SimSun', 'KaiTi'],
        'Darwin': ['PingFang SC', 'Heiti SC', 'STHeiti', 'Arial Unicode MS'],
        'Linux': ['WenQuanYi Micro Hei', 'Noto Sans CJK SC', 'Noto Sans SC',
                  'Droid Sans Fallback', 'AR PL UMing CN'],
    }.get(system, [])
    found = next((f for f in cjk_candidates if f in available), None)
    if found:
        return found

    import subprocess, os, glob
    font_dir = os.path.join(os.path.expanduser('~'), '.local', 'share', 'fonts')
    os.makedirs(font_dir, exist_ok=True)

    for ttf in glob.glob(os.path.join(font_dir, '*.ttf')) + glob.glob(os.path.join(font_dir, '*.otf')):
        try:
            fm.fontManager.addfont(ttf)
        except Exception:
            pass
    available = {f.name for f in fm.fontManager.ttflist}
    found = next((f for f in cjk_candidates if f in available), None)
    if found:
        return found

    if system == 'Linux':
        try:
            subprocess.run(['apt-get', 'install', '-y', 'fonts-wqy-microhei'],
                           capture_output=True, timeout=120)
            subprocess.run(['fc-cache', '-f'], capture_output=True)
        except Exception:
            pass

        font_url = 'https://github.com/google/fonts/raw/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf'
        dest = os.path.join(font_dir, 'NotoSansSC.ttf')
        if not os.path.exists(dest):
            try:
                import urllib.request
                print(f"[matplotlib] Downloading CJK font to {dest} ...")
                urllib.request.urlretrieve(font_url, dest)
            except Exception as e:
                print(f"[matplotlib] Font download failed: {e}")

        for ttf in glob.glob(os.path.join(font_dir, '*.ttf')) + glob.glob(os.path.join(font_dir, '*.otf')):
            try:
                fm.fontManager.addfont(ttf)
            except Exception:
                pass

        for d in ['/usr/share/fonts', '/usr/local/share/fonts']:
            for root, _, files in os.walk(d):
                for f in files:
                    if f.endswith(('.ttf', '.otf')) and any(k in f.lower() for k in ['cjk', 'wqy', 'noto', 'hei', 'song', 'kai']):
                        try:
                            fm.fontManager.addfont(os.path.join(root, f))
                        except Exception:
                            pass

    available = {f.name for f in fm.fontManager.ttflist}
    all_cjk = cjk_candidates + ['Noto Sans SC', 'Noto Sans CJK SC']
    return next((f for f in all_cjk if f in available), None)


_font_initialized = False
_font_primary = None


def setup_chart_font(paper_lang='auto'):
    """配置 matplotlib 字体，防止□□□。
    paper_lang: 'zh' 中文论文, 'en' 英文论文, 'auto' 自动检测。
    MUST be called before any plotting code.
    """
    global _font_initialized, _font_primary
    if _font_initialized:
        return _font_primary
    system = platform.system()
    sans_map = {
        'Windows': ['Arial', 'Calibri'],
        'Darwin': ['Helvetica Neue', 'Arial'],
        'Linux': ['DejaVu Sans', 'Liberation Sans'],
    }
    serif_candidates = ['Times New Roman', 'DejaVu Serif', 'Liberation Serif']

    chosen_cjk = _ensure_cjk_font()
    available = {f.name for f in fm.fontManager.ttflist}
    sans_list = sans_map.get(system, sans_map['Linux'])
    chosen_sans = next((f for f in sans_list if f in available), 'DejaVu Sans')
    chosen_serif = next((f for f in serif_candidates if f in available), 'DejaVu Serif')

    cjk_list = [chosen_cjk] if chosen_cjk else []
    if paper_lang == 'zh' or (paper_lang == 'auto' and chosen_cjk):
        primary = chosen_cjk or chosen_sans
        fallback = cjk_list + [chosen_sans, 'DejaVu Sans']
    else:
        primary = chosen_sans
        fallback = [chosen_sans] + cjk_list + ['DejaVu Sans']

    matplotlib.rcParams['font.sans-serif'] = [primary] + fallback
    matplotlib.rcParams['font.family'] = 'sans-serif'
    matplotlib.rcParams['font.serif'] = [chosen_serif] + serif_candidates
    matplotlib.rcParams['axes.unicode_minus'] = False
    matplotlib.rcParams['mathtext.fontset'] = 'cm'
    matplotlib.rcParams['mathtext.rm'] = 'serif'

    if chosen_cjk is None and paper_lang in ('zh', 'auto'):
        print("[WARNING] No CJK font found. Chinese text may show as □□□.")
        print("  Fix: pip install matplotlib && apt-get install -y fonts-wqy-microhei")
    print(f"[matplotlib] primary={primary}, serif={chosen_serif}, CJK={chosen_cjk or 'N/A'}")
    _font_initialized = True
    _font_primary = primary
    return primary


# ─── Unicode 上下标 → mathtext 转换 ─────────────────────────────

_SUPER_MAP = {
    '\u207A': '+', '\u207B': '-', '\u2070': '0', '\u00B9': '1',
    '\u00B2': '2', '\u00B3': '3', '\u2074': '4', '\u2075': '5',
    '\u2076': '6', '\u2077': '7', '\u2078': '8', '\u2079': '9',
    '\u207F': 'n', '\u2071': 'i',
}
_SUB_MAP = {
    '\u2080': '0', '\u2081': '1', '\u2082': '2', '\u2083': '3',
    '\u2084': '4', '\u2085': '5', '\u2086': '6', '\u2087': '7',
    '\u2088': '8', '\u2089': '9', '\u2090': 'a', '\u2091': 'e',
    '\u2092': 'o', '\u2093': 'x', '\u2095': 'h', '\u2096': 'k',
    '\u2097': 'l', '\u2098': 'm', '\u2099': 'n', '\u209A': 'p',
    '\u209B': 's', '\u209C': 't',
}
_SUPER_CHARS = set(_SUPER_MAP.keys())
_SUB_CHARS = set(_SUB_MAP.keys())

def _to_mathtext(text):
    """将含 Unicode 上下标的文本转为 matplotlib mathtext 混排格式。
    纯 ASCII 文本原样返回，避免不必要的 mathtext 开销。"""
    if not any(c in _SUPER_CHARS | _SUB_CHARS for c in text):
        return text

    parts = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch in _SUPER_CHARS:
            run = []
            while i < len(text) and text[i] in _SUPER_CHARS:
                run.append(_SUPER_MAP[text[i]])
                i += 1
            parts.append('$^{' + ''.join(run) + '}$')
        elif ch in _SUB_CHARS:
            run = []
            while i < len(text) and text[i] in _SUB_CHARS:
                run.append(_SUB_MAP[text[i]])
                i += 1
            parts.append('$_{' + ''.join(run) + '}$')
        else:
            parts.append(ch)
            i += 1
    return ''.join(parts)


# ─── 3. 学术配色方案 ────────────────────────────────────────────

SCIENCE_COLORS = {
    'nature': ['#E64B35', '#4DBBD5', '#00A087', '#3C5488', '#F39B7F',
               '#8491B4', '#91D1C2', '#DC0000', '#7E6148', '#B09C85'],
    'science': ['#3B4992', '#EE0000', '#008B45', '#631879', '#008280',
                '#BB0021', '#5F559B', '#A20056', '#808180', '#1B1919'],
    'lancet':  ['#00468B', '#ED0000', '#42B540', '#0099B4', '#925E9F',
                '#FDAF91', '#AD002A', '#ADB6B6'],
    'nejm':    ['#BC3C29', '#0072B5', '#E18727', '#20854E', '#7876B1',
                '#6F99AD', '#FFDC91', '#EE4C97'],
}


def science_style():
    return {
        'figure.dpi': 300, 'figure.figsize': (8, 5),
        'font.size': 12, 'axes.labelsize': 14, 'axes.titlesize': 16,
        'axes.linewidth': 1.2, 'lines.linewidth': 2, 'lines.markersize': 8,
        'xtick.labelsize': 11, 'ytick.labelsize': 11,
        'legend.fontsize': 11, 'legend.framealpha': 0.8, 'grid.alpha': 0.3,
        'savefig.bbox': 'tight', 'savefig.pad_inches': 0.1,
    }


# ─── 4. 图表模板 ────────────────────────────────────────────────

def create_bar_chart(categories, values_dict, title='', xlabel='', ylabel='', palette='nature'):
    plt.rcParams.update(science_style())
    colors = SCIENCE_COLORS[palette]
    fig, ax = plt.subplots()
    x = np.arange(len(categories))
    n = len(values_dict)
    width = 0.8 / n
    for i, (label, vals) in enumerate(values_dict.items()):
        ax.bar(x + i * width - 0.4 + width/2, vals, width,
               label=label, color=colors[i], edgecolor='white', linewidth=0.5)
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    ax.set_xticks(x); ax.set_xticklabels(categories)
    ax.legend(frameon=True, fancybox=True, shadow=True)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    fig.tight_layout()
    return fig


def create_line_chart(x_data, lines_dict, title='', xlabel='', ylabel='',
                      palette='nature', markers=True):
    """折线图。

    Args:
        x_data: x 轴数据（列表）
        lines_dict: {'系列名': [y 值], ...}
        markers: 是否显示数据点标记
    """
    plt.rcParams.update(science_style())
    colors = SCIENCE_COLORS[palette]
    marker_list = ['o', 's', '^', 'D', 'v', 'P', 'X', 'h']
    fig, ax = plt.subplots()
    for i, (label, vals) in enumerate(lines_dict.items()):
        mk = marker_list[i % len(marker_list)] if markers else None
        ax.plot(x_data, vals, label=label, color=colors[i % len(colors)],
                marker=mk, markerfacecolor='white', markeredgewidth=1.5)
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    ax.legend(frameon=True, fancybox=True, shadow=True)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    ax.grid(True, alpha=0.3, linestyle='--')
    fig.tight_layout()
    return fig


def create_scatter_chart(datasets, title='', xlabel='', ylabel='',
                         palette='nature', trendline=False):
    """散点图。

    Args:
        datasets: {'系列名': {'x': [...], 'y': [...]}, ...}
        trendline: 是否绘制线性趋势线
    """
    plt.rcParams.update(science_style())
    colors = SCIENCE_COLORS[palette]
    marker_list = ['o', 's', '^', 'D', 'v', 'P']
    fig, ax = plt.subplots()
    for i, (label, data) in enumerate(datasets.items()):
        c = colors[i % len(colors)]
        mk = marker_list[i % len(marker_list)]
        ax.scatter(data['x'], data['y'], label=label, color=c, marker=mk,
                   edgecolors='white', linewidths=0.5, s=60, alpha=0.8)
        if trendline:
            x_arr = np.array(data['x'], dtype=float)
            y_arr = np.array(data['y'], dtype=float)
            if len(x_arr) >= 2:
                z = np.polyfit(x_arr, y_arr, 1)
                p = np.poly1d(z)
                x_line = np.linspace(x_arr.min(), x_arr.max(), 100)
                ax.plot(x_line, p(x_line), color=c, linestyle='--', linewidth=1.2, alpha=0.6)
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    ax.legend(frameon=True, fancybox=True, shadow=True)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    fig.tight_layout()
    return fig


def create_pie_chart(labels, values, title='', palette='nature', donut=False):
    """饼图 / 环形图。

    Args:
        labels: 类别标签列表
        values: 对应数值列表
        donut: True 时绘制环形图
    """
    plt.rcParams.update(science_style())
    colors = SCIENCE_COLORS[palette]
    fig, ax = plt.subplots()
    wedgeprops = {'edgecolor': 'white', 'linewidth': 1.5}
    if donut:
        wedgeprops['width'] = 0.4
    wedges, texts, autotexts = ax.pie(
        values, labels=labels, colors=colors[:len(labels)],
        autopct='%1.1f%%', pctdistance=0.75 if donut else 0.6,
        wedgeprops=wedgeprops, startangle=90)
    for t in autotexts:
        t.set_fontsize(10)
        t.set_fontweight('bold')
    ax.set_aspect('equal')
    fig.tight_layout()
    return fig


def create_radar_chart(categories, series_dict, title='', palette='nature'):
    """雷达图。

    Args:
        categories: 维度名列表
        series_dict: {'系列名': [各维度值], ...}
    """
    plt.rcParams.update(science_style())
    colors = SCIENCE_COLORS[palette]
    n = len(categories)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(subplot_kw={'polar': True})
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_thetagrids(np.degrees(angles[:-1]), categories)

    for i, (label, vals) in enumerate(series_dict.items()):
        data = vals + vals[:1]
        c = colors[i % len(colors)]
        ax.plot(angles, data, 'o-', label=label, color=c, linewidth=2, markersize=6)
        ax.fill(angles, data, alpha=0.15, color=c)

    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1),
              frameon=True, fancybox=True, shadow=True)
    fig.tight_layout()
    return fig


def create_heatmap(data, row_labels, col_labels, title='', palette='nature',
                   annotate=True, cmap='YlOrRd'):
    """热力图。

    Args:
        data: 2D 列表或 numpy 数组
        row_labels: 行标签
        col_labels: 列标签
        annotate: 是否在格内显示数值
        cmap: matplotlib colormap 名称
    """
    plt.rcParams.update(science_style())
    data = np.array(data, dtype=float)
    fig, ax = plt.subplots()
    im = ax.imshow(data, cmap=cmap, aspect='auto')
    fig.colorbar(im, ax=ax, shrink=0.8)

    ax.set_xticks(np.arange(len(col_labels)))
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_xticklabels(col_labels)
    ax.set_yticklabels(row_labels)
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

    if annotate:
        for i in range(len(row_labels)):
            for j in range(len(col_labels)):
                val = data[i, j]
                threshold = (data.max() + data.min()) / 2
                color = 'white' if val > threshold else 'black'
                ax.text(j, i, f'{val:.2g}', ha='center', va='center',
                        color=color, fontsize=9)
    fig.tight_layout()
    return fig


# ─── 5. 流程图 / 架构图（纯 matplotlib，自动布局） ──────────────

ACADEMIC_COLORS = {
    'blue':    {'fill': '#DCEEFB', 'border': '#2B7BCE', 'text': '#1A4E8A'},
    'green':   {'fill': '#D6ECD8', 'border': '#2E8B57', 'text': '#1B5E20'},
    'orange':  {'fill': '#FDEBD0', 'border': '#E8890C', 'text': '#BF5B00'},
    'purple':  {'fill': '#E8D5F5', 'border': '#7E3FA8', 'text': '#4A148C'},
    'red':     {'fill': '#FAD4D4', 'border': '#C62828', 'text': '#8B1A1A'},
    'gray':    {'fill': '#EDEDED', 'border': '#6B6B6B', 'text': '#2D2D2D'},
    'teal':    {'fill': '#D0ECEB', 'border': '#008B8B', 'text': '#004D4D'},
    'yellow':  {'fill': '#FFF8D6', 'border': '#D4A017', 'text': '#8B6914'},
}

_SHAPE_DEFAULTS = {
    'rounded': (2.8, 0.9),
    'rect': (2.8, 0.9),
    'diamond': (3.2, 1.1),
    'ellipse': (2.8, 0.9),
}


def _auto_layout(nodes, edges, col_gap=3.6, row_gap=1.6):
    """分层布局 (Sugiyama-style): 回边检测 → 最长路径分层 → 重心法 x 优化。
    返回 {node_id: (cx, cy)} 坐标映射。"""
    from collections import defaultdict, deque

    ids = [n['id'] for n in nodes]
    id_set = set(ids)

    adj = defaultdict(list)
    all_edges = []
    for e in edges:
        src, dst = e['from'], e['to']
        if src in id_set and dst in id_set:
            adj[src].append(dst)
            all_edges.append((src, dst))

    WHITE, GRAY, BLACK = 0, 1, 2
    color = {nid: WHITE for nid in ids}
    back_edges = set()

    for start in ids:
        if color[start] != WHITE:
            continue
        stack = [(start, 0)]
        color[start] = GRAY
        while stack:
            u, idx = stack[-1]
            neighbors = adj[u]
            if idx < len(neighbors):
                stack[-1] = (u, idx + 1)
                v = neighbors[idx]
                if color[v] == GRAY:
                    back_edges.add((u, v))
                elif color[v] == WHITE:
                    color[v] = GRAY
                    stack.append((v, 0))
            else:
                color[u] = BLACK
                stack.pop()

    children = defaultdict(list)
    parents = defaultdict(list)
    in_deg = defaultdict(int)
    for src, dst in all_edges:
        if (src, dst) in back_edges:
            continue
        children[src].append(dst)
        parents[dst].append(src)
        in_deg[dst] += 1

    depth = {}
    queue = deque()
    for nid in ids:
        if in_deg.get(nid, 0) == 0:
            depth[nid] = 0
            queue.append(nid)
    if not queue:
        depth[ids[0]] = 0
        queue.append(ids[0])

    remaining = dict(in_deg)
    visited = set(queue)
    while queue:
        nid = queue.popleft()
        for ch in children[nid]:
            new_d = depth[nid] + 1
            if ch not in depth or new_d > depth[ch]:
                depth[ch] = new_d
            remaining[ch] = remaining.get(ch, 0) - 1
            if remaining[ch] <= 0 and ch not in visited:
                visited.add(ch)
                queue.append(ch)

    for nid in ids:
        if nid not in depth:
            depth[nid] = 0

    layer_map = defaultdict(list)
    for nid in ids:
        layer_map[depth[nid]].append(nid)
    max_layer = max(layer_map.keys()) if layer_map else 0
    layers = [layer_map.get(i, []) for i in range(max_layer + 1)]

    coords = {}
    for row_idx, layer in enumerate(layers):
        n = len(layer)
        total_w = (n - 1) * col_gap
        start_x = -total_w / 2
        for col_idx, nid in enumerate(layer):
            coords[nid] = (start_x + col_idx * col_gap, row_idx * row_gap)

    all_parents = defaultdict(list)
    all_children = defaultdict(list)
    for src, dst in all_edges:
        all_children[src].append(dst)
        all_parents[dst].append(src)

    layers_list = list(layers)
    for _iteration in range(10):
        sweep = layers_list if (_iteration % 2 == 0) else list(reversed(layers_list))
        for layer in sweep:
            for nid in layer:
                neighbors = [p for p in all_parents.get(nid, []) if p in coords] + \
                            [c for c in all_children.get(nid, []) if c in coords]
                if neighbors:
                    avg_x = sum(coords[nb][0] for nb in neighbors) / len(neighbors)
                    coords[nid] = (avg_x, coords[nid][1])

            ordered = sorted(layer, key=lambda nid: coords[nid][0])
            for i in range(1, len(ordered)):
                prev_x = coords[ordered[i - 1]][0]
                curr_x = coords[ordered[i]][0]
                if curr_x - prev_x < col_gap:
                    coords[ordered[i]] = (prev_x + col_gap, coords[ordered[i]][1])

    all_x = [coords[nid][0] for nid in ids]
    cx_mid = (min(all_x) + max(all_x)) / 2
    for nid in ids:
        x, y = coords[nid]
        coords[nid] = (x - cx_mid, y)

    return coords


def _get_anchor(src, dst, src_shape='rounded'):
    """计算从 src 到 dst 的最佳连接锚点对 (start, end)。"""
    sx, sy, sw, sh = src['cx'], src['cy'], src['w'], src['h']
    dx, dy, dw, dh = dst['cx'], dst['cy'], dst['w'], dst['h']

    delta_x = dx - sx
    delta_y = dy - sy

    is_diamond = src_shape == 'diamond'
    shw, shh = (sw / 2 + 0.25, sh / 2 + 0.2) if is_diamond else (sw / 2, sh / 2)
    dhw, dhh = dst['w'] / 2, dst['h'] / 2

    if abs(delta_y) > abs(delta_x) * 0.5:
        if delta_y > 0:
            return (sx, sy + shh), (dx, dy - dhh)
        else:
            return (sx, sy - shh), (dx, dy + dhh)
    else:
        if delta_x > 0:
            return (sx + shw, sy), (dx - dhw, dy)
        else:
            return (sx - shw, sy), (dx + dhw, dy)


def _draw_node(ax, cx, cy, w, h, shape, colors):
    """绘制单个节点形状，返回 patch。"""
    shadow_offset = 0.04
    if shape == 'diamond':
        verts = [(cx, cy - h / 2 - 0.2), (cx + w / 2 + 0.25, cy),
                 (cx, cy + h / 2 + 0.2), (cx - w / 2 - 0.25, cy)]
        shadow = plt.Polygon(
            [(x + shadow_offset, y + shadow_offset) for x, y in verts],
            facecolor='#00000010', edgecolor='none', zorder=1.5, closed=True)
        ax.add_patch(shadow)
        patch = plt.Polygon(verts, facecolor=colors['fill'], edgecolor=colors['border'],
                            linewidth=1.8, zorder=2, closed=True)
    elif shape == 'ellipse':
        shadow = mpatches.Ellipse((cx + shadow_offset, cy + shadow_offset), w, h,
                                   facecolor='#00000010', edgecolor='none', zorder=1.5)
        ax.add_patch(shadow)
        patch = mpatches.Ellipse((cx, cy), w, h, facecolor=colors['fill'],
                                  edgecolor=colors['border'], linewidth=1.8, zorder=2)
    elif shape == 'rect':
        shadow = plt.Rectangle((cx - w / 2 + shadow_offset, cy - h / 2 + shadow_offset), w, h,
                                facecolor='#00000010', edgecolor='none', zorder=1.5)
        ax.add_patch(shadow)
        patch = plt.Rectangle((cx - w / 2, cy - h / 2), w, h, facecolor=colors['fill'],
                               edgecolor=colors['border'], linewidth=1.8, zorder=2)
    else:
        shadow = FancyBboxPatch((cx - w / 2 + shadow_offset, cy - h / 2 + shadow_offset), w, h,
                                 boxstyle="round,pad=0.12", facecolor='#00000010',
                                 edgecolor='none', zorder=1.5)
        ax.add_patch(shadow)
        patch = FancyBboxPatch((cx - w / 2, cy - h / 2), w, h, boxstyle="round,pad=0.12",
                                facecolor=colors['fill'], edgecolor=colors['border'],
                                linewidth=1.8, zorder=2)
    ax.add_patch(patch)
    return patch


def _draw_edge(ax, src, dst, edge, src_shape='rounded'):
    """绘制一条连线及可选标签。回边从侧面绕弯回去。"""
    ls = '--' if edge.get('style') == 'dashed' else '-'
    is_back_edge = dst['cy'] < src['cy'] - 0.1

    if is_back_edge:
        is_diamond = src_shape == 'diamond'
        shw = (src['w'] / 2 + 0.25) if is_diamond else (src['w'] / 2)
        dhw = dst['w'] / 2

        go_left = src['cx'] <= dst['cx']
        if go_left:
            x0, x1 = src['cx'] - shw, dst['cx'] - dhw
        else:
            x0, x1 = src['cx'] + shw, dst['cx'] + dhw
        y0, y1 = src['cy'], dst['cy']
        detour_x = min(x0, x1) - 1.0 if go_left else max(x0, x1) + 1.0

        ax.plot([x0, detour_x, detour_x, x1], [y0, y0, y1, y1],
                color='#888888', linewidth=1.2, linestyle='--', zorder=0.8,
                solid_capstyle='round', clip_on=True)

        arrow_marker = '>' if go_left else '<'
        ax.plot(x1, y1, marker=arrow_marker, color='#888888',
                markersize=8, zorder=0.9, clip_on=True, linestyle='None')

        if edge.get('label'):
            lx = detour_x + (-0.15 if go_left else 0.15)
            ly = (y0 + y1) / 2
            ax.text(lx, ly, _to_mathtext(edge['label']), fontsize=8.5, color='#888888',
                    va='center', ha='right' if go_left else 'left',
                    bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                              edgecolor='#CCCCCC', alpha=0.9, linewidth=0.5))
    else:
        (x0, y0), (x1, y1) = _get_anchor(src, dst, src_shape)
        arrow = FancyArrowPatch(
            (x0, y0), (x1, y1),
            arrowstyle='->', mutation_scale=16,
            color='#4A4A4A', linewidth=1.4, linestyle=ls,
            connectionstyle='arc3,rad=0', zorder=1)
        ax.add_patch(arrow)

        if edge.get('label'):
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            ax.text(mx + 0.15, my, _to_mathtext(edge['label']), fontsize=8.5, color='#555555',
                    va='center', ha='center',
                    bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                              edgecolor='#CCCCCC', alpha=0.9, linewidth=0.5))


def create_flowchart(nodes, edges, title='', figsize=None):
    """绘制流程图。支持自动布局或手动坐标。

    nodes: list[dict]
        必填: id, text
        可选: color(ACADEMIC_COLORS key), shape('rounded'|'rect'|'diamond'|'ellipse')
        手动模式额外需要: x, y (若所有节点都有 x,y 则走手动布局)
        自动模式: 不需要 x,y，算法根据边的拓扑自动排列
    edges: list[dict] — from, to, label(optional), style('solid'|'dashed')
    """
    setup_chart_font()

    has_coords = all('x' in n and 'y' in n for n in nodes)
    if not has_coords:
        auto_pos = _auto_layout(nodes, edges)
    else:
        auto_pos = None

    node_map = {}
    for node in nodes:
        nid = node['id']
        shape = node.get('shape', 'rounded')
        dw, dh = _SHAPE_DEFAULTS.get(shape, (2.8, 0.9))
        w, h = node.get('width', dw), node.get('height', dh)

        if auto_pos:
            cx, cy = auto_pos.get(nid, (0, 0))
        else:
            cx, cy = node['x'], node['y']

        node_map[nid] = {'cx': cx, 'cy': cy, 'w': w, 'h': h, 'shape': shape}

    xs = [v['cx'] for v in node_map.values()]
    ys = [v['cy'] for v in node_map.values()]
    ws = [v['w'] for v in node_map.values()]
    hs = [v['h'] for v in node_map.values()]

    back_edge_pad = 0.0
    for edge in edges:
        s, d = node_map.get(edge['from']), node_map.get(edge['to'])
        if s and d and d['cy'] < s['cy'] - 0.1:
            back_edge_pad = max(back_edge_pad, 2.5)

    pad = 1.5
    x_min = min(xs) - max(ws) / 2 - pad - back_edge_pad
    x_max = max(xs) + max(ws) / 2 + pad
    y_min = min(ys) - max(hs) / 2 - pad
    y_max = max(ys) + max(hs) / 2 + pad
    if title:
        y_max += 0.8

    if figsize is None:
        fw = max(8, x_max - x_min + 1)
        fh = max(6, y_max - y_min + 1)
        figsize = (fw, fh)

    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_max, y_min)
    ax.set_aspect('equal')
    ax.axis('off')

    for node in nodes:
        nid = node['id']
        info = node_map[nid]
        cx, cy, w, h, shape = info['cx'], info['cy'], info['w'], info['h'], info['shape']
        colors = ACADEMIC_COLORS.get(node.get('color', 'blue'), ACADEMIC_COLORS['blue'])
        _draw_node(ax, cx, cy, w, h, shape, colors)
        ax.text(cx, cy, _to_mathtext(node['text']), ha='center', va='center', fontsize=10,
                fontweight='bold', color=colors['text'], zorder=3)

    for edge in edges:
        src, dst = node_map.get(edge['from']), node_map.get(edge['to'])
        if not src or not dst:
            continue
        _draw_edge(ax, src, dst, edge, src.get('shape', 'rounded'))

    if title:
        cx_mid = (x_min + x_max) / 2
        ax.text(cx_mid, y_min + 0.3, _to_mathtext(title), ha='center', va='center',
                fontsize=13, fontweight='bold', color='#333333')

    fig.tight_layout()
    return fig


def create_architecture_diagram(groups, nodes, connections, title='', figsize=None):
    """绘制架构图（含分组容器）。支持自动布局或手动坐标。

    groups: list[dict]
        必填: id, label
        可选: color, style('solid'|'dashed')
        手动模式额外需要: x, y, width, height
        自动模式: nodes 可选 group 字段指定所属分组
    nodes: list[dict] — 同 create_flowchart，额外可选 group 字段
    connections: list[dict] — 同 edges
    """
    setup_chart_font()

    has_coords = all('x' in n and 'y' in n for n in nodes)
    if not has_coords:
        auto_pos = _auto_layout(nodes, connections, col_gap=3.2, row_gap=1.5)
    else:
        auto_pos = None

    node_map = {}
    for node in nodes:
        nid = node['id']
        shape = node.get('shape', 'rounded')
        dw, dh = _SHAPE_DEFAULTS.get(shape, (2.4, 0.8))
        w = node.get('width', dw)
        h = node.get('height', dh)
        if auto_pos:
            cx, cy = auto_pos.get(nid, (0, 0))
        else:
            cx, cy = node['x'], node['y']
        node_map[nid] = {'cx': cx, 'cy': cy, 'w': w, 'h': h, 'shape': shape}

    xs = [v['cx'] for v in node_map.values()]
    ys = [v['cy'] for v in node_map.values()]
    ws = [v['w'] for v in node_map.values()]
    hs = [v['h'] for v in node_map.values()]

    has_group_coords = groups and all('x' in g and 'y' in g for g in groups)
    if has_group_coords:
        gxs = [g['x'] for g in groups] + [g['x'] + g['width'] for g in groups]
        gys = [g['y'] for g in groups] + [g['y'] + g['height'] for g in groups]
        xs = xs + gxs
        ys = ys + gys

    pad = 1.8
    x_min = min(xs) - max(ws) / 2 - pad
    x_max = max(xs) + max(ws) / 2 + pad
    y_min = min(ys) - max(hs) / 2 - pad
    y_max = max(ys) + max(hs) / 2 + pad
    if title:
        y_max += 0.8

    if not has_group_coords and groups:
        from collections import defaultdict
        group_members = defaultdict(list)
        for node in nodes:
            gid = node.get('group')
            if gid:
                nid = node['id']
                group_members[gid].append(node_map[nid])

        group_rects = {}
        gpad = 0.6
        for g in groups:
            members = group_members.get(g['id'], [])
            if not members:
                continue
            gx_min = min(m['cx'] - m['w'] / 2 for m in members) - gpad
            gx_max = max(m['cx'] + m['w'] / 2 for m in members) + gpad
            gy_min = min(m['cy'] - m['h'] / 2 for m in members) - gpad - 0.35
            gy_max = max(m['cy'] + m['h'] / 2 for m in members) + gpad
            group_rects[g['id']] = {
                'x': gx_min, 'y': gy_min,
                'width': gx_max - gx_min, 'height': gy_max - gy_min
            }
            x_min = min(x_min, gx_min - 0.5)
            x_max = max(x_max, gx_max + 0.5)
            y_min = min(y_min, gy_min - 0.5)
            y_max = max(y_max, gy_max + 0.5)
    else:
        group_rects = None

    if figsize is None:
        fw = max(10, x_max - x_min + 1)
        fh = max(7, y_max - y_min + 1)
        figsize = (fw, fh)

    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_max, y_min)
    ax.set_aspect('equal')
    ax.axis('off')

    for g in groups:
        colors = ACADEMIC_COLORS.get(g.get('color', 'gray'), ACADEMIC_COLORS['gray'])
        ls = '--' if g.get('style') == 'dashed' else '-'
        if group_rects and g['id'] in group_rects:
            r = group_rects[g['id']]
            gx, gy, gw, gh = r['x'], r['y'], r['width'], r['height']
        elif has_group_coords:
            gx, gy, gw, gh = g['x'], g['y'], g['width'], g['height']
        else:
            continue

        shadow = FancyBboxPatch(
            (gx + 0.05, gy + 0.05), gw, gh, boxstyle="round,pad=0.18",
            facecolor='#00000008', edgecolor='none', zorder=0)
        ax.add_patch(shadow)
        rect = FancyBboxPatch(
            (gx, gy), gw, gh, boxstyle="round,pad=0.18",
            facecolor=colors['fill'], edgecolor=colors['border'],
            linewidth=1.6, linestyle=ls, alpha=0.35, zorder=0.5)
        ax.add_patch(rect)
        ax.text(gx + gw / 2, gy + 0.3, _to_mathtext(g['label']), ha='center', va='center',
                fontsize=11, fontweight='bold', color=colors['text'], zorder=1)

    for node in nodes:
        nid = node['id']
        info = node_map[nid]
        cx, cy, w, h, shape = info['cx'], info['cy'], info['w'], info['h'], info['shape']
        colors = ACADEMIC_COLORS.get(node.get('color', 'blue'), ACADEMIC_COLORS['blue'])
        _draw_node(ax, cx, cy, w, h, shape, colors)
        ax.text(cx, cy, _to_mathtext(node['text']), ha='center', va='center', fontsize=9.5,
                fontweight='bold', color=colors['text'], zorder=3)

    for conn in connections:
        src, dst = node_map.get(conn['from']), node_map.get(conn['to'])
        if not src or not dst:
            continue
        _draw_edge(ax, src, dst, conn, src.get('shape', 'rounded'))

    if title:
        cx_mid = (x_min + x_max) / 2
        ax.text(cx_mid, y_min + 0.3, title, ha='center', va='center',
                fontsize=13, fontweight='bold', color='#333333')

    fig.tight_layout()
    return fig
