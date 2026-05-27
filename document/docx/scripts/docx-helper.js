'use strict';

const {
    Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
    Header, Footer, HeadingLevel, BorderStyle, WidthType, ShadingType,
    AlignmentType, PageNumber, PageBreak, ImageRun, LevelFormat,
    ExternalHyperlink, InternalHyperlink, Bookmark, FootnoteReferenceRun,
    PageOrientation, TableOfContents, VerticalMergeType, VerticalAlign,
    PositionalTab, PositionalTabAlignment, PositionalTabRelativeTo, PositionalTabLeader,
    TabStopType, TabStopPosition, Column, SectionType, LineRuleType,
    HorizontalPositionRelativeFrom, VerticalPositionRelativeFrom,
    TableAnchorType, OverlapType, RelativeHorizontalPosition,
} = require('docx');
const fs = require('fs');
const path = require('path');

// ── Defaults ────────────────────────────────────────────────────

const DEFAULTS = {
    fonts: { heading: 'Microsoft YaHei', body: 'Microsoft YaHei' },
    sizes: { h1: 36, h2: 30, h3: 26, body: 22, small: 18 },
    colors: {
        primary: '2B579A', text: '333333', light: 'F2F6FC',
        white: 'FFFFFF', border: 'D0D0D0',
    },
    spacing: {
        heading: { before: 360, after: 200 },
        body: { after: 160, line: 380 },
    },
    page: {
        width: 12240, height: 15840,
        margins: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
    },
};

const PRESETS = {};

function deepMerge(target, source) {
    const result = { ...target };
    for (const key of Object.keys(source)) {
        if (
            source[key] && typeof source[key] === 'object' && !Array.isArray(source[key]) &&
            target[key] && typeof target[key] === 'object' && !Array.isArray(target[key])
        ) {
            result[key] = deepMerge(target[key], source[key]);
        } else if (source[key] !== undefined) {
            result[key] = source[key];
        }
    }
    return result;
}

function _int(v) {
    if (v == null) return v;
    const n = Number(v);
    return Number.isFinite(n) ? Math.round(n) : v;
}

function _intArr(arr) {
    return Array.isArray(arr) ? arr.map(v => _int(v)) : arr;
}

function _intObj(obj) {
    if (!obj || typeof obj !== 'object') return obj;
    const out = {};
    for (const k of Object.keys(obj)) {
        out[k] = typeof obj[k] === 'object' && obj[k] !== null ? _intObj(obj[k]) : _int(obj[k]);
    }
    return out;
}

const ALIGN = {
    left: AlignmentType.LEFT,
    center: AlignmentType.CENTER,
    right: AlignmentType.RIGHT,
    justify: AlignmentType.JUSTIFIED,
};

// ── Factory ─────────────────────────────────────────────────────

module.exports = function createHelpers(userConfig) {
    const uc = userConfig || {};
    const presetName = uc.preset;
    const base = presetName && PRESETS[presetName] ? deepMerge(DEFAULTS, PRESETS[presetName]) : DEFAULTS;
    const cfg = deepMerge(base, uc);
    cfg.sizes = _intObj(cfg.sizes);
    cfg.spacing = _intObj(cfg.spacing);
    cfg.page = _intObj(cfg.page);
    if (cfg.fonts.english) {
        const en = cfg.fonts.english;
        if (typeof cfg.fonts.body === 'string') {
            cfg.fonts.body = { ascii: en, eastAsia: cfg.fonts.body, hAnsi: en, cs: en };
        }
        if (typeof cfg.fonts.heading === 'string') {
            cfg.fonts.heading = { ascii: en, eastAsia: cfg.fonts.heading, hAnsi: en, cs: en };
        }
    }

    if (cfg.indent && typeof cfg.indent === 'object') {
        cfg.indent = _int(cfg.indent.firstLine) || _int(cfg.indent.left) || 0;
    }

    const _fullContentWidth = _int(cfg.page.width - cfg.page.margins.left - cfg.page.margins.right);
    const _columnCount = (cfg.columns && cfg.columns.count) || 1;
    const _columnSpace = (cfg.columns && cfg.columns.space) || 708;
    const _columnContentWidth = _columnCount > 1
        ? Math.floor((_fullContentWidth - _columnSpace * (_columnCount - 1)) / _columnCount)
        : _fullContentWidth;
    let contentWidth = _columnContentWidth;
    const _EMOJI_RE = /\p{Extended_Pictographic}(?:\uFE0E|\uFE0F)?(?:\u200D\p{Extended_Pictographic}(?:\uFE0E|\uFE0F)?)*/gu;
    const _EMOJI_FONT = cfg.fonts.emoji || 'Segoe UI Emoji';

    // ── Numbering presets ─────────────────────────────────────────

    const BULLET_REF = '__hlp_bullet';
    const NUMBER_REF = '__hlp_number';
    const _usedNumberingRefs = new Set();
    const _builtinNumbering = [
        {
            reference: BULLET_REF,
            levels: [
                {
                    level: 0, format: LevelFormat.BULLET, text: '\u2022', alignment: AlignmentType.LEFT,
                    style: { paragraph: { indent: { left: 720, hanging: 360 } } }
                },
                {
                    level: 1, format: LevelFormat.BULLET, text: '\u25E6', alignment: AlignmentType.LEFT,
                    style: { paragraph: { indent: { left: 1440, hanging: 360 } } }
                },
            ],
        },
        {
            reference: NUMBER_REF,
            levels: [
                {
                    level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT,
                    style: { paragraph: { indent: { left: 720, hanging: 360 } } }
                },
                {
                    level: 1, format: LevelFormat.LOWER_LETTER, text: '%2)', alignment: AlignmentType.LEFT,
                    style: { paragraph: { indent: { left: 1440, hanging: 360 } } }
                },
            ],
        },
    ];

    // ── TextRun helpers ───────────────────────────────────────────

    function _runProps(props) {
        const rp = {};
        if (props.font || !props._noDefaultFont) rp.font = props.font || cfg.fonts.body;
        if (props.size || !props._noDefaultSize) rp.size = _int(props.size) || cfg.sizes.body;
        if (props.color || !props._noDefaultColor) rp.color = props.color || cfg.colors.text;
        if (props.bold) rp.bold = true;
        if (props.italics || props.italic) rp.italics = true;
        if (props.underline) rp.underline = typeof props.underline === 'object' ? props.underline : { type: 'single' };
        if (props.strike) rp.strike = true;
        if (props.highlight) rp.highlight = props.highlight;
        if (props.superScript) rp.superScript = true;
        if (props.subScript) rp.subScript = true;
        if (props.characterSpacing) rp.characterSpacing = props.characterSpacing;
        if (props.allCaps) rp.allCaps = true;
        if (props.smallCaps) rp.smallCaps = true;
        if (props.style) rp.style = props.style;
        return rp;
    }

    function _makeRun(content, props) {
        const rp = _runProps(props || {});
        if (typeof content === 'string') {
            rp.text = content;
        } else if (Array.isArray(content)) {
            rp.children = content;
        }
        return new TextRun(rp);
    }

    function _splitEmojiRuns(str, props) {
        _EMOJI_RE.lastIndex = 0;
        if (!_EMOJI_RE.test(str)) return [_makeRun(str, props)];
        _EMOJI_RE.lastIndex = 0;
        const runs = [];
        let last = 0;
        let m;
        while ((m = _EMOJI_RE.exec(str)) !== null) {
            if (m.index > last) runs.push(_makeRun(str.slice(last, m.index), props));
            runs.push(_makeRun(m[0], { ...props, font: _EMOJI_FONT }));
            last = _EMOJI_RE.lastIndex;
        }
        if (last < str.length) runs.push(_makeRun(str.slice(last), props));
        return runs;
    }

    function text(content, props) {
        if (typeof content === 'string') {
            if (content.includes('$')) {
                const parts = _splitInlineMath(content, props || {});
                return parts.length === 1 ? parts[0] : parts;
            }
            const runs = _splitEmojiRuns(content, props || {});
            return runs.length === 1 ? runs[0] : runs;
        }
        return _makeRun(content, props || {});
    }
    function bold(content, extra) { return text(content, { bold: true, ...extra }); }
    function italic(content, extra) { return text(content, { italic: true, ...extra }); }

    // ── Content coercion ──────────────────────────────────────────

    const RUN_KEYS = new Set([
        'bold', 'italic', 'italics', 'underline', 'strike', 'color',
        'size', 'font', 'highlight', 'superScript', 'subScript',
        'characterSpacing', 'allCaps', 'smallCaps',
    ]);

    function _extractRunProps(opts) {
        const rp = {};
        for (const k of RUN_KEYS) {
            if (opts[k] !== undefined) rp[k] = opts[k];
        }
        return rp;
    }

    const _INLINE_MATH_RE = /\$([^$]+?)\$/g;
    const _INLINE_CITE_RE = /\[@([^\]]+?)\]/g;
    const _formula = require(path.join(__dirname, 'formula'));
    let _activeRefTracker = null;

    function _splitInlineMath(str, runProps) {
        if (!str || !str.includes('$')) return _splitEmojiRuns(str, runProps);
        const parts = [];
        let last = 0;
        let m;
        _INLINE_MATH_RE.lastIndex = 0;
        while ((m = _INLINE_MATH_RE.exec(str)) !== null) {
            if (m.index > last) {
                parts.push(..._splitEmojiRuns(str.slice(last, m.index), runProps));
            }
            parts.push(_formula.createMath(m[1]));
            last = _INLINE_MATH_RE.lastIndex;
        }
        if (last < str.length) parts.push(..._splitEmojiRuns(str.slice(last), runProps));
        return parts;
    }

    const _BARE_CITE_RE = /\[([a-zA-Z][a-zA-Z0-9_]*(?:\d{4}[a-z]?)?(?:,[a-zA-Z][a-zA-Z0-9_]*(?:\d{4}[a-z]?)?)*)\]/g;
    const _NUMERIC_CITE_RE = /\[(\d+(?:\s*[-,，]\s*\d+)*)\]/g;

    function _numericCiteToSuperscript(str, runProps) {
        if (!_activeRefTracker || !str) return _splitInlineMath(str, runProps);
        _NUMERIC_CITE_RE.lastIndex = 0;
        if (!_NUMERIC_CITE_RE.test(str)) return _splitInlineMath(str, runProps);
        _NUMERIC_CITE_RE.lastIndex = 0;
        const supSize = _int(_activeRefTracker._supSize) || _int(cfg.sizes.ref) || _int(cfg.sizes.small) || 18;
        const refFont = _activeRefTracker._refFont || cfg.fonts.english || cfg.fonts.body;
        const parts = [];
        let last = 0;
        let m;
        while ((m = _NUMERIC_CITE_RE.exec(str)) !== null) {
            if (/^\s*$/.test(str.slice(0, m.index))) {
                parts.push(..._splitInlineMath(m[0], runProps));
                last = _NUMERIC_CITE_RE.lastIndex;
                continue;
            }
            if (m.index > last) {
                parts.push(..._splitInlineMath(str.slice(last, m.index), runProps));
            }
            parts.push(new TextRun({
                text: m[0],
                superScript: true,
                font: refFont,
                size: supSize,
            }));
            last = _NUMERIC_CITE_RE.lastIndex;
        }
        if (last < str.length) {
            parts.push(..._splitInlineMath(str.slice(last), runProps));
        }
        return parts;
    }

    function _splitInlineCite(str, runProps) {
        if (!_activeRefTracker || !str || !str.includes('[@')) {
            if (_activeRefTracker && str && _BARE_CITE_RE.test(str)) {
                _BARE_CITE_RE.lastIndex = 0;
                let bm;
                while ((bm = _BARE_CITE_RE.exec(str)) !== null) {
                    if (!/^\[\d+\]$/.test(bm[0]) && !/^\[[A-Z]\]$/.test(bm[0])) {
                        console.warn(
                            `[docx-helpers] 警告: 疑似引用缺少 @ 前缀: "${bm[0]}" → 应为 "[@${bm[1]}]"`
                        );
                    }
                }
            }
            return _numericCiteToSuperscript(str, runProps);
        }
        const parts = [];
        let last = 0;
        let m;
        _INLINE_CITE_RE.lastIndex = 0;
        while ((m = _INLINE_CITE_RE.exec(str)) !== null) {
            if (m.index > last) {
                parts.push(..._splitInlineMath(str.slice(last, m.index), runProps));
            }
            const keys = m[1].split(/[,;，；]/).map(k => k.trim().replace(/^@/, '')).filter(Boolean);
            parts.push(_activeRefTracker.cite(...keys));
            last = _INLINE_CITE_RE.lastIndex;
        }
        if (last < str.length) {
            parts.push(..._splitInlineMath(str.slice(last), runProps));
        }
        return parts;
    }

    function _toChildren(content, defaultRunProps) {
        if (content == null) return [];
        if (typeof content === 'string') return _splitInlineCite(content, defaultRunProps || {});
        if (content instanceof TextRun || content instanceof ImageRun) return [content];
        if (content instanceof Paragraph) {
            return content.root && content.root.length ? content.root.filter(c => c instanceof ImageRun || c instanceof TextRun) : [];
        }
        if (Array.isArray(content)) {
            return content.flatMap(item => {
                if (typeof item === 'string') return _splitInlineCite(item, defaultRunProps || {});
                if (item instanceof Paragraph) {
                    return item.root && item.root.length ? item.root.filter(c => c instanceof ImageRun || c instanceof TextRun) : [];
                }
                if (Array.isArray(item)) return item;
                return [item];
            });
        }
        return [content];
    }

    // ── Paragraph helpers ─────────────────────────────────────────

    function p(content, opts) {
        opts = opts || {};
        if (content instanceof Paragraph) {
            console.warn('[docx-helpers] 警告: h.p() 收到 Paragraph 对象，应直接放入 children 而非嵌套在 h.p() 内');
            return content;
        }
        if (content instanceof Table) {
            console.warn('[docx-helpers] 警告: h.p() 收到 Table 对象，Table 不能嵌套在段落中，已原样返回');
            return content;
        }
        const pp = {};
        if (opts.align) pp.alignment = ALIGN[opts.align] || opts.align;
        if (opts.spacing) pp.spacing = _intObj(opts.spacing);
        if (opts.indent) pp.indent = _intObj(opts.indent);
        if (opts.heading) pp.heading = opts.heading;
        if (opts.numbering) pp.numbering = opts.numbering;
        if (opts.pageBreakBefore) pp.pageBreakBefore = true;
        if (opts.shading) pp.shading = opts.shading;
        if (opts.border) pp.border = opts.border;
        if (opts.tabStops) pp.tabStops = opts.tabStops;
        if (opts.contextualSpacing !== undefined) pp.contextualSpacing = opts.contextualSpacing;
        if (opts.keepNext) pp.keepNext = true;
        if (opts.keepLines) pp.keepLines = true;
        if (opts.widowControl !== undefined) pp.widowControl = opts.widowControl;
        if (!pp.spacing && !opts.heading && !opts.numbering) {
            pp.spacing = { ...cfg.spacing.body };
        }
        const _align = opts.align && (ALIGN[opts.align] || opts.align);
        if (!pp.indent && !opts.heading && !opts.numbering && cfg.indent
            && _align !== AlignmentType.CENTER && _align !== AlignmentType.RIGHT) {
            pp.indent = { firstLine: _int(cfg.indent) };
        }

        pp.children = _toChildren(content, _extractRunProps(opts));
        return new Paragraph(pp);
    }

    const _headingRegistry = [];

    function _heading(level, content, opts) {
        opts = opts || {};
        const headings = [null, HeadingLevel.HEADING_1, HeadingLevel.HEADING_2, HeadingLevel.HEADING_3];
        const sizes = [null, cfg.sizes.h1, cfg.sizes.h2, cfg.sizes.h3];

        const textStr = typeof content === 'string' ? content : String(content);
        _headingRegistry.push({
            text: textStr,
            level,
            bookmark: opts.bookmark || null,
        });

        if (opts.bookmark) {
            const runProps = {
                bold: true,
                font: opts.font || cfg.fonts.heading,
                size: _int(opts.size) || sizes[level],
                color: opts.color || cfg.colors.primary,
            };
            const children = _toChildren(content, runProps);
            const bm = new Bookmark({ id: opts.bookmark, children });
            return new Paragraph({
                heading: headings[level],
                spacing: _intObj(opts.spacing) || { ...cfg.spacing.heading },
                keepNext: true,
                keepLines: true,
                children: [bm],
            });
        }

        return p(content, {
            heading: headings[level],
            spacing: { ...cfg.spacing.heading },
            bold: true,
            font: cfg.fonts.heading,
            size: sizes[level],
            color: cfg.colors.primary,
            keepNext: true,
            keepLines: true,
            ...opts,
        });
    }

    function h1(content, opts) { return _heading(1, content, opts); }
    function h2(content, opts) { return _heading(2, content, opts); }
    function h3(content, opts) { return _heading(3, content, opts); }

    function bullet(content, opts) {
        opts = opts || {};
        const level = opts.level || 0;
        return p(content, {
            numbering: { reference: BULLET_REF, level },
            spacing: { after: 80 },
            ...opts,
        });
    }

    function numbered(content, opts) {
        opts = opts || {};
        const level = opts.level || 0;
        const ref = opts.ref || NUMBER_REF;
        _usedNumberingRefs.add(ref);
        return p(content, {
            numbering: { reference: ref, level },
            spacing: { after: 80 },
            ...opts,
        });
    }

    // ── Layout helpers ────────────────────────────────────────────

    function pageBreak_() {
        return new Paragraph({ children: [new PageBreak()] });
    }

    function spacer(height) {
        const p = new Paragraph({
            spacing: { before: _int(height) || 400, line: 20, lineRule: LineRuleType.EXACT },
        });
        p._isSpacer = true;
        p._spacerHeight = _int(height) || 400;
        return p;
    }

    function divider(color, size) {
        return new Paragraph({
            border: { bottom: { style: BorderStyle.SINGLE, size: _int(size) || 6, color: color || cfg.colors.border } },
            spacing: { after: 200 },
        });
    }

    const _floatTblpPrCache = _columnCount > 1 ? _buildFloatTblpPr() : null;

    function _buildFloatTblpPr() {
        const ref = new Table({
            float: {
                horizontalAnchor: TableAnchorType.MARGIN,
                verticalAnchor: TableAnchorType.TEXT,
                relativeHorizontalPosition: RelativeHorizontalPosition.CENTER,
                overlap: OverlapType.NEVER,
                topFromText: 120,
                bottomFromText: 120,
            },
            width: { size: 1, type: WidthType.DXA },
            rows: [new TableRow({ children: [new TableCell({ children: [new Paragraph('')] })] })],
        });
        for (const child of ref.root) {
            if (child && child.rootKey === 'w:tblPr') {
                for (const sub of child.root) {
                    if (sub && sub.rootKey === 'w:tblpPr') return sub;
                }
            }
        }
        return null;
    }

    function _injectFloat(tbl) {
        if (!_floatTblpPrCache) return;
        for (const child of tbl.root) {
            if (child && child.rootKey === 'w:tblPr') {
                const hasPr = child.root.some(s => s && s.rootKey === 'w:tblpPr');
                if (!hasPr) child.root.unshift(_floatTblpPrCache);
                return;
            }
        }
    }

    function _scaleTableToFullWidth(tbl) {
        for (const child of tbl.root) {
            if (child && child.rootKey === 'w:tblPr') {
                for (const sub of child.root) {
                    if (sub && sub.rootKey === 'w:tblW') {
                        for (const attr of sub.root) {
                            if (attr && attr.rootKey === '_attr' && attr.root && attr.root.size) {
                                attr.root.size.value = _fullContentWidth;
                            }
                        }
                    }
                }
            }
        }
    }

    function _getTableColumnCount(tbl) {
        for (const child of tbl.root) {
            if (child instanceof TableRow) {
                let count = 0;
                for (const cell of child.root) {
                    if (cell instanceof TableCell) count++;
                }
                return count;
            }
        }
        return 0;
    }

    function _mergeCaptionIntoTable(captionPara, tbl, position) {
        const colCount = _getTableColumnCount(tbl);
        if (colCount < 1) return;
        const NONE = { style: BorderStyle.NIL, size: 0 };
        const captionCell = new TableCell({
            children: [captionPara],
            columnSpan: colCount,
            width: { size: _fullContentWidth, type: WidthType.DXA },
            borders: { top: NONE, bottom: NONE, left: NONE, right: NONE },
            margins: { top: 60, bottom: 60, left: 0, right: 0 },
        });
        const captionRow = new TableRow({ children: [captionCell] });
        if (position === 'before') {
            const insertIdx = tbl.root.findIndex(c => c instanceof TableRow);
            if (insertIdx >= 0) tbl.root.splice(insertIdx, 0, captionRow);
            else tbl.root.push(captionRow);
        } else {
            tbl.root.push(captionRow);
        }
    }

    function _scaleImageToFullWidth(para) {
        const scale = _fullContentWidth / _columnContentWidth;
        const pageContentHeight = cfg.page.height - cfg.page.margins.top - cfg.page.margins.bottom;
        const maxHeightEMU = Math.round(pageContentHeight * 0.3 * 635);
        function walk(node) {
            if (!node || !node.root) return;
            if (node.rootKey === 'wp:extent') {
                for (const attr of node.root) {
                    if (attr && attr.rootKey === '_attr' && attr.root) {
                        let newCx = Math.round((attr.root.x ? attr.root.x.value : 0) * scale);
                        let newCy = Math.round((attr.root.y ? attr.root.y.value : 0) * scale);
                        if (newCy > maxHeightEMU && newCy > 0) {
                            const hScale = maxHeightEMU / newCy;
                            newCx = Math.round(newCx * hScale);
                            newCy = maxHeightEMU;
                        }
                        if (attr.root.x) attr.root.x.value = newCx;
                        if (attr.root.y) attr.root.y.value = newCy;
                    }
                }
                return;
            }
            if (Array.isArray(node.root)) {
                for (const child of node.root) walk(child);
            }
        }
        walk(para);
    }

    function _wrapInFloatTable(paragraphs) {
        for (const p_ of paragraphs) _scaleImageToFullWidth(p_);
        const NONE = { style: BorderStyle.NIL, size: 0 };
        const noBorders = { top: NONE, bottom: NONE, left: NONE, right: NONE };
        const row = new TableRow({
            children: [new TableCell({
                children: paragraphs,
                width: { size: _fullContentWidth, type: WidthType.DXA },
                borders: noBorders,
                margins: { top: 0, bottom: 0, left: 0, right: 0 },
            })],
        });
        const tbl = new Table({
            float: {
                horizontalAnchor: TableAnchorType.MARGIN,
                verticalAnchor: TableAnchorType.TEXT,
                relativeHorizontalPosition: RelativeHorizontalPosition.CENTER,
                overlap: OverlapType.NEVER,
                topFromText: 120,
                bottomFromText: 120,
            },
            width: { size: _fullContentWidth, type: WidthType.DXA },
            columnWidths: [_fullContentWidth],
            rows: [row],
            borders: noBorders,
        });
        return tbl;
    }

    function fullWidth(...args) {
        const savedWidth = contentWidth;
        contentWidth = _fullContentWidth;
        let items;
        try {
            items = [];
            for (const a of args) {
                if (typeof a === 'function') {
                    const result = a(_fullContentWidth);
                    if (Array.isArray(result)) items.push(...result.flat(Infinity));
                    else if (result != null) items.push(result);
                } else if (Array.isArray(a)) {
                    items.push(...a.flat(Infinity));
                } else if (a != null) {
                    items.push(a);
                }
            }
        } finally {
            contentWidth = savedWidth;
        }

        if (_columnCount <= 1) return items;

        let result;
        const hasTable = items.some(it => it instanceof Table);
        if (!hasTable) {
            result = [_wrapInFloatTable(items)];
        } else {
            const toRemove = new Set();
            for (let i = 0; i < items.length; i++) {
                if (!(items[i] instanceof Table)) continue;
                const tbl = items[i];
                _injectFloat(tbl);
                _scaleTableToFullWidth(tbl);

                if (i > 0 && items[i - 1] instanceof Paragraph) {
                    _mergeCaptionIntoTable(items[i - 1], tbl, 'before');
                    toRemove.add(i - 1);
                }
                if (i + 1 < items.length && items[i + 1] instanceof Paragraph) {
                    _mergeCaptionIntoTable(items[i + 1], tbl, 'after');
                    toRemove.add(i + 1);
                }
            }
            result = toRemove.size > 0 ? items.filter((_, idx) => !toRemove.has(idx)) : items;
        }

        result.push(new Paragraph({ spacing: { before: 0, after: 0, line: 20 } }));
        return result;
    }

    // ── Image helper ──────────────────────────────────────────────

    function _readImageSize(buf) {
        // PNG: bytes 16-23 contain width(4) + height(4) in IHDR chunk
        if (buf.length >= 24 && buf[0] === 0x89 && buf[1] === 0x50) {
            return { w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) };
        }
        // JPEG: scan for SOFn marker (0xFF 0xC0..0xCF, excluding 0xC4/0xC8/0xCC)
        if (buf.length >= 2 && buf[0] === 0xFF && buf[1] === 0xD8) {
            let off = 2;
            while (off + 9 < buf.length) {
                if (buf[off] !== 0xFF) { off++; continue; }
                const marker = buf[off + 1];
                if (marker >= 0xC0 && marker <= 0xCF && marker !== 0xC4 && marker !== 0xC8 && marker !== 0xCC) {
                    return { w: buf.readUInt16BE(off + 7), h: buf.readUInt16BE(off + 5) };
                }
                off += 2 + buf.readUInt16BE(off + 2);
            }
        }
        return null;
    }

    function img(filePath, opts) {
        opts = opts || {};
        if (!filePath || typeof filePath !== 'string') {
            throw new Error('h.img() 第一个参数必须是图片文件路径（字符串）');
        }
        if (!fs.existsSync(filePath)) {
            throw new Error(`h.img() 图片文件不存在: ${filePath}`);
        }
        const ext = (filePath.split('.').pop() || 'png').toLowerCase();
        const data = fs.readFileSync(filePath);
        const realSize = _readImageSize(data);
        let w, h_;
        const hasW = opts.width != null;
        const hasH = opts.height != null;
        if (hasW && hasH) {
            w = _int(opts.width);
            h_ = _int(opts.height);
        } else if (hasW && realSize) {
            w = _int(opts.width);
            h_ = Math.round(w * realSize.h / realSize.w);
        } else if (hasH && realSize) {
            h_ = _int(opts.height);
            w = Math.round(h_ * realSize.w / realSize.h);
        } else if (realSize) {
            const ratio = realSize.h / realSize.w;
            w = Math.round(contentWidth / 15);
            h_ = Math.round(w * ratio);
        } else {
            w = _int(opts.width) || 400;
            h_ = _int(opts.height) || 300;
        }
        const maxPx = Math.round(contentWidth / 15);
        if (w > maxPx) {
            const scale = maxPx / w;
            h_ = Math.round(h_ * scale);
            w = maxPx;
        }
        const maxHPx = Math.round((cfg.page.height - cfg.page.margins.top - cfg.page.margins.bottom) / 15 * 0.85);
        if (h_ > maxHPx && maxHPx > 0) {
            const hScale = maxHPx / h_;
            w = Math.round(w * hScale);
            h_ = maxHPx;
        }
        const imgProps = {
            type: ext === 'jpg' ? 'jpeg' : ext,
            data,
            transformation: { width: w, height: h_ },
        };
        if (opts.altText) imgProps.altText = opts.altText;
        if (opts.floating) imgProps.floating = opts.floating;
        const run = new ImageRun(imgProps);
        if (opts._raw) return run;
        return new Paragraph({
            alignment: ALIGN[opts.align] || opts.align || AlignmentType.CENTER,
            children: [run],
            spacing: _intObj(opts.spacing) || {},
        });
    }

    // ── Link helpers ──────────────────────────────────────────────

    function link(displayText, url) {
        return new ExternalHyperlink({
            children: [new TextRun({ text: displayText, style: 'Hyperlink', color: cfg.colors.primary })],
            link: url,
        });
    }

    // ── Header / Footer / PageNumber ─────────────────────────────

    function header(content, opts) {
        opts = opts || {};
        const defaultProps = { size: 18, color: '999999', align: 'center' };
        const children = [p(content, { ...defaultProps, ...opts })];
        return new Header({ children });
    }

    function footer(content, opts) {
        opts = opts || {};
        if (content == null) {
            return new Footer({ children: [p([
                text('\u2014 ', { size: 18, color: '999999', _noDefaultFont: true }),
                text([PageNumber.CURRENT], { size: 18, color: '999999', _noDefaultFont: true }),
                text(' \u2014', { size: 18, color: '999999', _noDefaultFont: true }),
            ], { align: 'center' })] });
        }
        const defaultProps = { size: 18, color: '999999', align: 'center' };
        return new Footer({ children: [p(content, { ...defaultProps, ...opts })] });
    }

    function pageNum() {
        return [PageNumber.CURRENT];
    }

    function headerFooter(headerContent, footerContent, opts) {
        opts = opts || {};
        return {
            headers: { default: header(headerContent, opts.header || {}) },
            footers: { default: typeof footerContent === 'undefined'
                ? footer()
                : footer(footerContent, opts.footer || {}) },
        };
    }

    // ── Cover background ──────────────────────────────────────────

    function coverBg(imgPath, opts) {
        opts = opts || {};
        const pxW = Math.round(cfg.page.width / 15);
        const pxH = Math.round(cfg.page.height / 15);
        return img(imgPath, {
            width: opts.width || pxW,
            height: opts.height || pxH,
            floating: {
                horizontalPosition: { relative: HorizontalPositionRelativeFrom.PAGE, offset: 0 },
                verticalPosition: { relative: VerticalPositionRelativeFrom.PAGE, offset: 0 },
                behindDocument: true,
            },
        });
    }

    // ── Table of Contents ─────────────────────────────────────────

    let _tocRef = null;
    let _tocOpts = null;

    function toc(opts) {
        opts = opts || {};
        _tocOpts = opts;
        const noIndent = { indent: { firstLine: 0 } };
        if (opts.cachedEntries) {
            const tocObj = new TableOfContents(opts.title || '\u76EE\u5F55', {
                hyperlink: opts.hyperlink !== false,
                headingStyleRange: opts.headingStyleRange || '1-3',
                cachedEntries: opts.cachedEntries,
            });
            return p([tocObj], noIndent);
        }
        const tocObj = new TableOfContents(opts.title || '\u76EE\u5F55', {
            hyperlink: opts.hyperlink !== false,
            headingStyleRange: opts.headingStyleRange || '1-3',
        });
        const tocPara = p([tocObj], noIndent);
        _tocRef = tocPara;
        return tocPara;
    }

    // ── Bookmark helper ───────────────────────────────────────────

    function bookmark(id, content) {
        const children = _toChildren(content, { bold: true });
        return new Bookmark({ id, children });
    }

    // ── Vertical merge constant ───────────────────────────────────

    const MERGE = {
        START: VerticalMergeType.RESTART,
        CONTINUE: VerticalMergeType.CONTINUE,
    };

    // ── Table helpers ─────────────────────────────────────────────

    const _cellSpacing = { after: 0, line: 320 };

    function _cellChildren(content) {
        if (content instanceof Paragraph) return [content];
        if (content instanceof Table) return [content];
        if (content instanceof TextRun) {
            return [new Paragraph({ spacing: _cellSpacing, children: [content] })];
        }
        if (Array.isArray(content)) {
            if (content.length > 0 && (content[0] instanceof Paragraph || content[0] instanceof Table)) {
                return content;
            }
            return [new Paragraph({ spacing: _cellSpacing, children: _toChildren(content) })];
        }
        if (typeof content === 'string') {
            return [new Paragraph({ spacing: _cellSpacing, children: _toChildren(content) })];
        }
        return [new Paragraph({ spacing: _cellSpacing, children: [new TextRun(String(content != null ? content : ''))] })];
    }

    function _isCellObject(content) {
        return typeof content === 'object' && content !== null &&
            !(content instanceof Paragraph) && !(content instanceof Table) &&
            !(content instanceof TextRun) && !Array.isArray(content);
    }

    function table(spec) {
        const {
            widths: _widths,
            columnWidths: _columnWidths,
            header,
            rows = [],
            headerColor,
            headerTextColor,
            altColor,
            borders = true,
            margins,
            noBorders,
            align,
        } = spec;

        let widths = _intArr(_widths || _columnWidths);
        if (!widths || !Array.isArray(widths)) {
            throw new Error(
                'h.table() 需要 widths 数组（列宽 DXA）。'
                + (spec.width ? ' 注意：不要传 width/columnWidths，请用 widths: [...]' : '')
            );
        }
        let totalWidth = widths.reduce((a, b) => a + b, 0);
        if (totalWidth > contentWidth && _columnCount > 1) {
            const testWidths = widths.map(w => Math.round(w * contentWidth / totalWidth));
            const minCol = Math.min(...testWidths);
            if (minCol < 700) {
                console.warn(
                    `[docx-helpers] table: 双栏下列宽过窄（最小 ${minCol} DXA ≈ ${(minCol/567).toFixed(1)}cm），自动跨栏全宽显示`
                );
                return fullWidth(() => table(spec));
            }
        }
        if (totalWidth > contentWidth) {
            const scale = contentWidth / totalWidth;
            widths = widths.map(w => Math.round(w * scale));
            totalWidth = widths.reduce((a, b) => a + b, 0);
            const diff = contentWidth - totalWidth;
            if (diff !== 0) widths[widths.length - 1] += diff;
            totalWidth = contentWidth;
        }

        const stdBorder = noBorders
            ? { style: BorderStyle.NIL }
            : borders === true
                ? { style: BorderStyle.SINGLE, size: 1, color: cfg.colors.border }
                : borders || { style: BorderStyle.NIL };
        const defaultBorders = { top: stdBorder, bottom: stdBorder, left: stdBorder, right: stdBorder };
        const defaultMargins = _intObj(margins) || { top: 100, bottom: 100, left: 120, right: 120 };

        function _coerceSpan(value, context) {
            if (value == null) return 1;
            const span = _int(value);
            if (!Number.isInteger(span) || span < 1) {
                throw new Error(`h.table() ${context} 的 columnSpan 必须是 >= 1 的整数`);
            }
            return span;
        }

        function _spanWidth(startCol, span, context) {
            if (startCol + span > widths.length) {
                throw new Error(
                    `h.table() ${context} 覆盖到第 ${startCol + span} 列，但表格只声明了 ${widths.length} 列`
                );
            }
            return widths.slice(startCol, startCol + span).reduce((a, b) => a + b, 0);
        }

        function _cellSpan(content) {
            if (_isCellObject(content)) {
                return _coerceSpan(content.columnSpan, '单元格');
            }
            return 1;
        }

        function makeCell(content, colIdx, cellOpts) {
            cellOpts = cellOpts || {};
            const isCellObject = _isCellObject(content);
            const columnSpan = isCellObject ? _cellSpan(content) : _coerceSpan(cellOpts.columnSpan, '单元格');
            const cp = {
                width: { size: _spanWidth(colIdx, columnSpan, '单元格'), type: WidthType.DXA },
                borders: cellOpts.borders || defaultBorders,
                margins: cellOpts.margins || defaultMargins,
            };
            if (cellOpts.fill) cp.shading = { fill: cellOpts.fill, type: ShadingType.CLEAR };
            if (columnSpan > 1) cp.columnSpan = columnSpan;
            if (cellOpts.verticalMerge) cp.verticalMerge = cellOpts.verticalMerge;
            if (cellOpts.verticalAlign) cp.verticalAlign = cellOpts.verticalAlign;

            if (isCellObject) {
                const {
                    text: t,
                    children: ch,
                    fill,
                    columnSpan: _ignoredColumnSpan,
                    verticalMerge,
                    verticalAlign: va,
                    align,
                    borders: contentBorders,
                    margins: contentMargins,
                    ...runProps
                } = content;
                if (contentBorders) cp.borders = contentBorders;
                if (contentMargins) cp.margins = _intObj(contentMargins);
                if (fill) cp.shading = { fill, type: ShadingType.CLEAR };
                if (verticalMerge) cp.verticalMerge = verticalMerge;
                if (va) cp.verticalAlign = va;
                const cellText = ch ?? t ?? '';
                const innerChildren = _cellChildren(cellText);
                if (align && innerChildren[0] instanceof Paragraph) {
                    innerChildren[0] = new Paragraph({
                        ...innerChildren[0],
                        alignment: ALIGN[align] || align,
                        children: innerChildren[0].root ? undefined : _toChildren(cellText, runProps),
                    });
                }
                if (Object.keys(runProps).length > 0 && typeof cellText === 'string') {
                    cp.children = [new Paragraph({
                        spacing: { after: 0 },
                        alignment: align ? (ALIGN[align] || align) : undefined,
                        children: [_makeRun(cellText, runProps)],
                    })];
                } else {
                    cp.children = _cellChildren(cellText);
                }
            } else {
                cp.children = _cellChildren(content);
            }
            return new TableCell(cp);
        }

        function makeRow(cells, rowOpts) {
            rowOpts = rowOpts || {};
            let colIdx = 0;
            const children = cells.map(c => {
                const cell = makeCell(c, colIdx, { fill: rowOpts.fill });
                colIdx += _cellSpan(c);
                return cell;
            });
            if (colIdx !== widths.length) {
                throw new Error(
                    `h.table() ${rowOpts.label || '某一行'} 实际覆盖 ${colIdx} 列，但表格声明了 ${widths.length} 列；请检查 cells 数量或 columnSpan`
                );
            }
            return new TableRow({
                children,
            });
        }

        const allRows = [];

        if (header) {
            const hColor = headerTextColor || (headerColor ? cfg.colors.white : cfg.colors.text);
            const hCells = header.map(h =>
                typeof h === 'string'
                    ? { text: h, bold: true, color: hColor, align: 'center' }
                    : { bold: true, color: hColor, align: 'center', ...h }
            );
            allRows.push(makeRow(hCells, { fill: headerColor, label: '表头行' }));
        }

        rows.forEach((row, ri) => {
            const fill = altColor && ri % 2 === 1 ? altColor : undefined;
            allRows.push(makeRow(row, { fill, label: `数据行 ${ri + 1}` }));
        });

        return new Table({
            width: { size: totalWidth, type: WidthType.DXA },
            columnWidths: widths,
            rows: allRows,
            alignment: ALIGN[align] || align || AlignmentType.CENTER,
        });
    }

    // ── Cover page spacer auto-shrink ────────────────────────────

    function _shrinkCoverSpacers(children, availableTwips) {
        let spacerTotal = 0;
        const spacerIndices = [];
        let contentHeight = 0;
        for (let i = 0; i < children.length; i++) {
            const child = children[i];
            if (child._isSpacer) {
                spacerTotal += child._spacerHeight;
                spacerIndices.push(i);
            } else if (child instanceof Table) {
                let rowCount = 0;
                for (const c of child.root) { if (c instanceof TableRow) rowCount++; }
                contentHeight += Math.max(rowCount, 1) * 600;
            } else {
                contentHeight += 700;
            }
        }
        if (spacerIndices.length === 0) return;
        const budget = Math.round(availableTwips * 0.85) - contentHeight;
        if (budget >= spacerTotal) return;
        const scale = budget > 0 ? budget / spacerTotal : 0;
        console.warn(
            `[docx-helpers] 封面 spacer 总量 ${spacerTotal} 超出预算 ${Math.round(budget)}（` +
            `页面可用 ${availableTwips}，内容估算 ${contentHeight}），按 ${(scale * 100).toFixed(0)}% 等比压缩`
        );
        for (const idx of spacerIndices) {
            const oldH = children[idx]._spacerHeight;
            const newH = Math.max(Math.round(oldH * scale), 20);
            children[idx] = spacer(newH);
        }
    }

    // ── Document assembly ─────────────────────────────────────────

    function createDoc(spec) {
        const allNumbering = [..._builtinNumbering, ...(spec.numbering || [])];
        const registeredRefs = new Set(allNumbering.map(n => n.reference));
        for (const ref of _usedNumberingRefs) {
            if (!registeredRefs.has(ref)) {
                console.warn(`[docx-helpers] numbering ref "${ref}" 未注册，已自动 fallback 到默认编号格式`);
                allNumbering.push({
                    reference: ref,
                    levels: _builtinNumbering.find(n => n.reference === NUMBER_REF).levels,
                });
            }
        }

        const _defaultPage = {
            size: { width: cfg.page.width, height: cfg.page.height },
            margin: cfg.page.margins,
        };

        if (!spec.sections || spec.sections.length === 0) {
            throw new Error('[docx-helpers] build() 的 sections 不能为空，至少需要一个 section');
        }
        const flatSections = [];
        for (const sec of spec.sections) {
            const flat = { ...sec };
            if (flat.children) {
                flat.children = Array.isArray(flat.children)
                    ? flat.children.flat(Infinity)
                    : [flat.children];
                flat.children = flat.children.filter(c => c != null).map(c => {
                    if (typeof c === 'string' || typeof c === 'number') {
                        console.warn(`[docx-helpers] 警告: section children 中出现原始值 "${String(c).slice(0, 50)}"，已自动包装为 h.p()`);
                        return p(String(c));
                    }
                    return c;
                });
            }
            if (!flat.properties) {
                flat.properties = { page: _defaultPage, column: { count: 1 } };
            } else if (!flat.properties.page) {
                flat.properties.page = _defaultPage;
            }
            if (flat.cover && flat.children) {
                _shrinkCoverSpacers(flat.children, cfg.page.height - cfg.page.margins.top - cfg.page.margins.bottom);
            }
            flatSections.push(flat);
        }

        const lastSec = flatSections[flatSections.length - 1];
        const lastCol = lastSec && lastSec.properties && lastSec.properties.column;
        if (lastCol && lastCol.count > 1) {
            flatSections.push({
                properties: {
                    type: SectionType.CONTINUOUS,
                    page: _defaultPage,
                    column: { count: 1 },
                },
                children: [],
            });
        }

        if (_tocRef && _headingRegistry.length > 0) {
            const _tocTitleExcludes = new Set(['目录', 'tableofcontents']);
            const cachedEntries = _headingRegistry
                .filter(h => !_tocTitleExcludes.has(h.text.replace(/\s+/g, '').replace(/\u3000/g, '').toLowerCase()))
                .map(h => ({
                    title: h.text,
                    level: h.level - 1,
                    page: '',
                    ...(h.bookmark ? { href: h.bookmark } : {}),
                }));
            const newToc = new TableOfContents((_tocOpts && _tocOpts.title) || '\u76EE\u5F55', {
                hyperlink: !_tocOpts || _tocOpts.hyperlink !== false,
                headingStyleRange: (_tocOpts && _tocOpts.headingStyleRange) || '1-3',
                cachedEntries,
            });
            const newTocPara = p([newToc]);
            for (const sec of flatSections) {
                if (!sec.children) continue;
                const idx = sec.children.indexOf(_tocRef);
                if (idx !== -1) {
                    sec.children[idx] = newTocPara;
                    break;
                }
            }
        }

        const docSpec = {
            numbering: { config: allNumbering },
            sections: flatSections,
        };

        if (spec.compatibility) {
            docSpec.compatibility = spec.compatibility;
        }

        if (spec.styles) {
            docSpec.styles = spec.styles;
        } else {
            docSpec.styles = _defaultStyles();
        }

        if (spec.footnotes) docSpec.footnotes = spec.footnotes;

        return new Document(docSpec);
    }

    function _defaultStyles() {
        return {
            default: {
                document: {
                    run: { font: cfg.fonts.body, size: cfg.sizes.body, color: cfg.colors.text },
                    paragraph: { widowControl: true },
                },
            },
            paragraphStyles: [
                {
                    id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
                    run: { size: cfg.sizes.h1, bold: true, font: cfg.fonts.heading, color: cfg.colors.primary },
                    paragraph: { spacing: cfg.spacing.heading, outlineLevel: 0, keepNext: true, keepLines: true },
                },
                {
                    id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
                    run: { size: cfg.sizes.h2, bold: true, font: cfg.fonts.heading, color: cfg.colors.primary },
                    paragraph: { spacing: cfg.spacing.heading, outlineLevel: 1, keepNext: true, keepLines: true },
                },
                {
                    id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
                    run: { size: cfg.sizes.h3, bold: true, font: cfg.fonts.heading, color: cfg.colors.primary },
                    paragraph: { spacing: cfg.spacing.heading, outlineLevel: 2, keepNext: true, keepLines: true },
                },
            ],
        };
    }

    function build(spec, outputPath, patches) {
        if (Array.isArray(outputPath)) {
            patches = outputPath;
            outputPath = null;
        }
        outputPath = outputPath || process.argv[2];
        if (!outputPath) {
            throw new Error(
                '[docx-helpers] 未指定输出路径：请通过 run_node_docx(output=...) 传入，' +
                '或在 h.build() 第二个参数指定'
            );
        }
        const doc = createDoc(spec);
        return Packer.toBuffer(doc).then(async (buffer) => {
            let final = buffer;
            if (patches && patches.length > 0) {
                try {
                    const { applyPatches } = require(path.join(__dirname, 'docx_patches'));
                    final = await applyPatches(buffer, patches);
                } catch (err) {
                    throw new Error('[docx-helpers] applyPatches 失败: ' + err.message);
                }
            }
            fs.writeFileSync(outputPath, final);
            console.log('[docx-helpers] 文档已生成: ' + outputPath);
        });
    }

    // ── Math / Formula helpers ───────────────────────────────────

    function math(latex) {
        return _formula.createMath(latex);
    }

    function formula(latex, opts) {
        opts = opts || {};
        if (!opts._pageWidth) opts._pageWidth = contentWidth;
        if (!opts.spacing) {
            opts.spacing = {
                before: cfg.spacing.body.after != null ? Math.max(cfg.spacing.body.after, 120) : 160,
                after: cfg.spacing.body.after != null ? Math.max(cfg.spacing.body.after, 120) : 160,
                line: cfg.spacing.body.line,
                lineRule: cfg.spacing.body.lineRule,
            };
        }
        return _formula.createFormula(latex, opts);
    }

    // ── Three-line table (学术三线表) ─────────────────────────────

    function threeLineTable(spec) {
        const {
            widths: _widths,
            header: hdr,
            rows = [],
            caption,
            captionPosition = 'top',
            cellFont,
            cellEastAsia,
            cellSize,
            margins,
        } = spec;

        let widths = _intArr(_widths);
        if (!widths || !Array.isArray(widths)) {
            throw new Error('h.threeLineTable() 需要 widths 数组');
        }
        let totalWidth = widths.reduce((a, b) => a + b, 0);
        if (totalWidth > contentWidth && _columnCount > 1) {
            const testWidths = widths.map(w => Math.round(w * contentWidth / totalWidth));
            const minCol = Math.min(...testWidths);
            if (minCol < 700) {
                console.warn(
                    `[docx-helpers] threeLineTable: 双栏下列宽过窄（最小 ${minCol} DXA ≈ ${(minCol/567).toFixed(1)}cm），自动跨栏全宽显示`
                );
                return fullWidth(() => threeLineTable(spec));
            }
        }
        if (totalWidth > contentWidth) {
            const scale = contentWidth / totalWidth;
            widths = widths.map(w => Math.round(w * scale));
            totalWidth = widths.reduce((a, b) => a + b, 0);
            const diff = contentWidth - totalWidth;
            if (diff !== 0) widths[widths.length - 1] += diff;
            totalWidth = contentWidth;
        }

        const THICK = { style: BorderStyle.SINGLE, size: 12, color: '000000' };
        const THIN = { style: BorderStyle.SINGLE, size: 6, color: '000000' };
        const NONE = { style: BorderStyle.NIL, size: 0 };
        const defaultMargins = _intObj(margins) || { top: 60, bottom: 60, left: 100, right: 100 };
        const numRows = (hdr ? 1 : 0) + rows.length;

        function makeBorders(rowIdx) {
            const isFirst = rowIdx === 0;
            const isHeaderBottom = hdr && rowIdx === 0;
            const isSecondRow = hdr && rowIdx === 1;
            const isLast = rowIdx === numRows - 1;
            return {
                top: isFirst ? THICK : isSecondRow ? THIN : NONE,
                bottom: isHeaderBottom ? THIN : isLast ? THICK : NONE,
                left: NONE, right: NONE,
            };
        }

        function makeCell(content, rowIdx, colIdx) {
            const cellProps = {
                width: { size: widths[colIdx], type: WidthType.DXA },
                borders: makeBorders(rowIdx),
                margins: defaultMargins,
            };
            const isHeader = hdr && rowIdx === 0;
            const cellContent = typeof content === 'string' ? content : String(content != null ? content : '');
            const runProps = { font: cellFont || cfg.fonts.body, size: _int(cellSize) || cfg.sizes.body };
            if (isHeader) runProps.bold = true;
            cellProps.children = [new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { after: 0, line: 320 },
                children: _toChildren(cellContent, runProps),
            })];
            return new TableCell(cellProps);
        }

        function makeRow(cells, rowIdx) {
            return new TableRow({
                children: cells.map((c, ci) => makeCell(c, rowIdx, ci)),
            });
        }

        const allRows = [];
        let ri = 0;
        if (hdr) {
            if (hdr.length !== widths.length) {
                throw new Error(
                    `h.threeLineTable() header 有 ${hdr.length} 个单元格，但 widths 声明了 ${widths.length} 列`
                );
            }
            allRows.push(makeRow(hdr, ri)); ri++;
        }
        for (const row of rows) {
            if (row.length !== widths.length) {
                throw new Error(
                    `h.threeLineTable() 第 ${ri + 1} 行有 ${row.length} 个单元格，但 widths 声明了 ${widths.length} 列`
                );
            }
            allRows.push(makeRow(row, ri)); ri++;
        }

        const tbl = new Table({
            width: { size: totalWidth, type: WidthType.DXA },
            columnWidths: widths,
            rows: allRows,
        });

        const afterSpacer = new Paragraph({ spacing: { before: 200, after: 0, line: 20, lineRule: LineRuleType.EXACT } });

        if (!caption) return [tbl, afterSpacer];

        const captionPara = p(caption, {
            align: 'center',
            size: _int(cellSize) || 18,
            spacing: { before: captionPosition === 'top' ? 200 : 60, after: captionPosition === 'top' ? 60 : 200 },
        });
        return captionPosition === 'top' ? [captionPara, tbl, afterSpacer] : [tbl, captionPara];
    }

    // ── Reference tracker (引用追踪器) ──────────────────────────

    function refTracker(opts) {
        opts = opts || {};
        const _map = new Map();
        let _counter = 0;
        const supSize = _int(opts.size) || _int(cfg.sizes.ref) || _int(cfg.sizes.small) || 18;
        const refFont = opts.font || cfg.fonts.english || cfg.fonts.body;
        const bodyFont = opts.bodyFont || cfg.fonts.body;
        const bodySize = _int(opts.bodySize) || _int(cfg.sizes.body) || 24;

        function _getNum(key) {
            if (_map.has(key)) return _map.get(key);
            _counter++;
            _map.set(key, _counter);
            return _counter;
        }

        function _compressNums(nums) {
            if (nums.length <= 1) return nums.join('');
            const ranges = [];
            let start = nums[0], end = nums[0];
            for (let i = 1; i < nums.length; i++) {
                if (nums[i] === end + 1) { end = nums[i]; }
                else { ranges.push(start === end ? `${start}` : `${start}-${end}`); start = end = nums[i]; }
            }
            ranges.push(start === end ? `${start}` : `${start}-${end}`);
            return ranges.join(',');
        }

        function cite(...keys) {
            const nums = keys.map(k => _getNum(k));
            nums.sort((a, b) => a - b);
            const label = '[' + _compressNums(nums) + ']';
            return new TextRun({
                text: label,
                superScript: true,
                font: refFont,
                size: supSize,
            });
        }

        function bibliography(entries, bibOpts) {
            bibOpts = bibOpts || {};
            const _LEADING_MANUAL_REF_RE = /^(?:\s*\[(?:\d+(?:\s*[-,，]\s*\d+)*|[Nn])\]\s*)+/;

            const valid = entries.filter(e => e && typeof e === 'object' && e.key && e.text);
            if (valid.length < entries.length) {
                const skipped = entries.length - valid.length;
                console.warn(`[docx-helpers] bibliography: 跳过 ${skipped} 条无效条目（缺少 key 或 text）`);
            }

            const entryKeys = new Set(valid.map(e => e.key));
            const missing = [];
            for (const [key] of _map) {
                if (!entryKeys.has(key)) missing.push(key);
            }
            if (missing.length > 0) {
                console.warn(
                    `[docx-helpers] 警告: ${missing.length} 个正文 [@key] 在 bibliography 中缺少对应条目:\n` +
                    `  ${missing.join(', ')}\n` +
                    `  请确保每个 [@key] 都有对应的 { key, text } 条目。`
                );
            }

            const uncited = valid.filter(e => !_map.has(e.key)).map(e => e.key);
            if (uncited.length > 0) {
                console.warn(
                    `[docx-helpers] 警告: ${uncited.length} 个 bibliography 条目在正文中未被 [@key] 引用:\n` +
                    `  ${uncited.join(', ')}\n` +
                    `  未引用的条目仍会输出，但编号排在末尾。如非必要请移除，或在正文中添加 [@key] 引用。`
                );
            }

            const sorted = [...valid].sort((a, b) => {
                const na = _map.has(a.key) ? _map.get(a.key) : Infinity;
                const nb = _map.has(b.key) ? _map.get(b.key) : Infinity;
                return na - nb;
            });
            const paragraphs = [];
            let strippedManualCount = 0;
            for (const entry of sorted) {
                const num = _map.has(entry.key) ? _map.get(entry.key) : (_counter++, _map.set(entry.key, _counter), _counter);
                const bodyRunProps = { font: bodyFont, size: bodySize };
                const rawText = typeof entry.text === 'string' ? entry.text : String(entry.text ?? '');
                const cleanText = rawText.replace(_LEADING_MANUAL_REF_RE, '').trimStart();
                if (cleanText !== rawText) strippedManualCount++;
                paragraphs.push(new Paragraph({
                    spacing: { after: bibOpts.spacing || 60, line: bibOpts.line || 320 },
                    indent: { left: 420, hanging: 420 },
                    children: [
                        new TextRun({
                            text: `[${num}] `,
                            font: refFont,
                            size: bodySize,
                        }),
                        ..._toChildren(cleanText, bodyRunProps),
                    ],
                }));
            }
            if (strippedManualCount > 0) {
                console.warn(
                    `[docx-helpers] bibliography: 已自动移除 ${strippedManualCount} 条条目前缀手写编号（如 [1] / [2][3]），统一使用自动编号。`
                );
            }
            return paragraphs;
        }

        function _parsePool(poolPath) {
            const raw = fs.readFileSync(poolPath, 'utf-8');
            const entries = [];
            let current = null;
            for (const line of raw.split('\n')) {
                if (line.startsWith('### ')) {
                    if (current) entries.push(current);
                    current = { key: line.slice(4).trim(), text: '', authors: '', title: '', year: '', journal: '', doi: '' };
                } else if (current) {
                    const m = line.match(/^- (.+?)：(.*)$/);
                    if (m) {
                        const [, field, val] = m;
                        const v = val.trim();
                        if (field === '引用文本') current.text = v;
                        else if (field === '作者') current.authors = v;
                        else if (field === '标题') current.title = v;
                        else if (field === '年份') current.year = v;
                        else if (field === '期刊/来源') current.journal = v;
                        else if (field === 'DOI') current.doi = v;
                    }
                }
            }
            if (current) entries.push(current);
            for (const e of entries) {
                if (!e.text) {
                    const parts = [e.authors, e.title].filter(Boolean).join('. ');
                    e.text = parts + (e.journal ? `[J]. ${e.journal}` : '') + (e.year ? `, ${e.year}` : '') + '.';
                }
            }
            return entries;
        }

        function bibliographyFromPool(poolPath, bibOpts) {
            const allEntries = _parsePool(poolPath);
            const cited = allEntries.filter(e => _map.has(e.key));
            if (cited.length === 0 && _map.size > 0) {
                console.warn(
                    `[docx-helpers] 文献池中未找到任何被引用的 key。\n` +
                    `  正文中引用了: ${[..._map.keys()].join(', ')}\n` +
                    `  文献池中有: ${allEntries.map(e => e.key).join(', ')}`
                );
            }
            return bibliography(cited.length > 0 ? cited : allEntries.filter(e => e.text), bibOpts);
        }

        function autoBibliography(jsonPath, bibOpts) {
            const raw = fs.readFileSync(jsonPath, 'utf-8');
            let entries;
            try {
                entries = JSON.parse(raw);
            } catch (e) {
                console.warn(`[docx-helpers] autoBibliography: JSON 解析失败: ${jsonPath}\n  ${e.message}`);
                return [];
            }
            if (!Array.isArray(entries) || entries.length === 0) {
                console.warn(`[docx-helpers] autoBibliography: JSON 为空或格式错误: ${jsonPath}`);
                return [];
            }
            const valid = entries.filter(e => e && typeof e === 'object' && e.key && e.text);
            const cited = valid.filter(e => _map.has(e.key));

            const jsonKeys = new Set(valid.map(e => e.key));
            const missing = [..._map.keys()].filter(k => !jsonKeys.has(k));
            if (missing.length > 0) {
                console.warn(
                    `[docx-helpers] autoBibliography: ${missing.length} 个正文 [@key] 在 JSON 中无对应条目:\n` +
                    `  ${missing.join(', ')}\n` +
                    `  强制规则: 严禁手动补写 references.json 或手写参考文献条目；缺失引用直接忽略，不补检索、不补条目。`
                );
            }

            return bibliography(cited, bibOpts);
        }

        const tracker = { cite, bibliography, bibliographyFromPool, autoBibliography, getNum: _getNum, get count() { return _counter; }, _supSize: supSize, _refFont: refFont };
        _activeRefTracker = tracker;
        return tracker;
    }

    // ── Public API ────────────────────────────────────────────────

    return {
        text, bold, italic,
        p, h1, h2, h3, bullet, numbered,
        table, threeLineTable,
        math, formula,
        refTracker,
        pageBreak: pageBreak_, spacer, divider, fullWidth,
        img, link,
        header, footer, pageNum, headerFooter,
        coverBg, toc, bookmark, MERGE,
        createDoc, build,
        colors: cfg.colors,
        fonts: cfg.fonts,
        sizes: cfg.sizes,
        contentWidth,
        fullContentWidth: _fullContentWidth,
        cfg,
        raw: {
            Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
            Header, Footer, HeadingLevel, BorderStyle, WidthType, ShadingType,
            AlignmentType, PageNumber, PageBreak, ImageRun, LevelFormat,
            ExternalHyperlink, InternalHyperlink, Bookmark, FootnoteReferenceRun,
            PageOrientation, TableOfContents, VerticalMergeType, VerticalAlign,
            PositionalTab, PositionalTabAlignment, PositionalTabRelativeTo, PositionalTabLeader,
            TabStopType, TabStopPosition, Column, SectionType,
            HorizontalPositionRelativeFrom, VerticalPositionRelativeFrom,
        },
    };
};
