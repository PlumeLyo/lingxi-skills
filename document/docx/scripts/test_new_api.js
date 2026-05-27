'use strict';

const path = require('path');
const createHelpers = require(path.join(__dirname, 'docx-helper'));

let passed = 0;
let failed = 0;

function assert(condition, msg) {
    if (condition) {
        passed++;
        console.log(`  \u2714 ${msg}`);
    } else {
        failed++;
        console.error(`  \u2718 ${msg}`);
    }
}

function section(name) {
    console.log(`\n--- ${name} ---`);
}

const h = createHelpers({
    fonts: { heading: 'SimHei', body: 'SimSun' },
    colors: { primary: '1A5276', text: '2C3E50', light: 'EBF5FB' },
});
const { Header, Footer, Bookmark } = h.raw;

// ── h.header() ──────────────────────────────────────────────

section('h.header()');

const hdr = h.header('测试页眉');
assert(hdr instanceof Header, '返回 Header 实例');

const hdr2 = h.header('自定义', { size: 24, color: 'FF0000' });
assert(hdr2 instanceof Header, '自定义 opts 返回 Header');

// ── h.footer() ──────────────────────────────────────────────

section('h.footer()');

const ftr = h.footer();
assert(ftr instanceof Footer, '无参返回 Footer（自动页码）');

const ftr2 = h.footer('底部文字');
assert(ftr2 instanceof Footer, '传内容返回 Footer');

const ftr3 = h.footer([h.text('第 '), h.text(h.pageNum(), { bold: true }), h.text(' 页')]);
assert(ftr3 instanceof Footer, '混排内容返回 Footer');

// ── h.pageNum() ─────────────────────────────────────────────

section('h.pageNum()');

const pn = h.pageNum();
assert(Array.isArray(pn), '返回数组');
assert(pn.length === 1, '数组长度为 1');

// ── h.headerFooter() ────────────────────────────────────────

section('h.headerFooter()');

const hf = h.headerFooter('报告标题');
assert(hf.headers && hf.headers.default, '包含 headers.default');
assert(hf.footers && hf.footers.default, '包含 footers.default');
assert(hf.headers.default instanceof Header, 'headers.default 是 Header');
assert(hf.footers.default instanceof Footer, 'footers.default 是 Footer');

const hf2 = h.headerFooter('标题', '自定义页脚');
assert(hf2.footers.default instanceof Footer, '自定义页脚 Footer');

const hf3 = h.headerFooter('标题', null);
assert(hf3.footers.default instanceof Footer, '传 null 走自定义分支');

// ── h.coverBg() ─────────────────────────────────────────────

section('h.coverBg()');

const fs = require('fs');
const os = require('os');
const tmpImg = path.join(__dirname, '_test_cover.png');
// 创建一个最小的 1x1 PNG
const PNG_1x1 = Buffer.from(
    '89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489' +
    '0000000a49444154789c626000000002000198e195280000000049454e44ae426082',
    'hex'
);
fs.writeFileSync(tmpImg, PNG_1x1);

try {
    const bg = h.coverBg(tmpImg);
    assert(bg.constructor.name === 'Paragraph', '返回 Paragraph');

    const bg2 = h.coverBg(tmpImg, { width: 100, height: 200 });
    assert(bg2.constructor.name === 'Paragraph', '自定义尺寸返回 Paragraph');
} finally {
    fs.unlinkSync(tmpImg);
}

// ── h.toc() ─────────────────────────────────────────────────

section('h.toc()');

const tocDefault = h.toc();
assert(tocDefault.constructor.name === 'Paragraph', '默认返回 Paragraph');

const tocCached = h.toc({
    cachedEntries: [
        { title: '第一章', level: 1, page: 2, href: '_ch1' },
        { title: '1.1 节', level: 2, page: 3, href: '_s1' },
    ],
});
assert(tocCached.constructor.name === 'Paragraph', '带 cachedEntries 返回 Paragraph');

const tocCustom = h.toc({ title: '自定义目录', headingStyleRange: '1-2' });
assert(tocCustom.constructor.name === 'Paragraph', '自定义参数返回 Paragraph');

// ── h.bookmark() ────────────────────────────────────────────

section('h.bookmark()');

const bm = h.bookmark('_test', '书签文字');
assert(bm instanceof Bookmark, '返回 Bookmark');

const bm2 = h.bookmark('_test2', [h.bold('粗体书签')]);
assert(bm2 instanceof Bookmark, '混排内容返回 Bookmark');

// ── h.MERGE ─────────────────────────────────────────────────

section('h.MERGE');

assert(h.MERGE.START !== undefined, 'MERGE.START 已定义');
assert(h.MERGE.CONTINUE !== undefined, 'MERGE.CONTINUE 已定义');
assert(h.MERGE.START !== h.MERGE.CONTINUE, 'START !== CONTINUE');

// ── h.table() + MERGE 集成 ──────────────────────────────────

section('h.table() + MERGE 集成');

const tbl = h.table({
    widths: [3000, 3000],
    rows: [
        [{ text: '跨行', verticalMerge: h.MERGE.START }, 'A'],
        [{ text: '', verticalMerge: h.MERGE.CONTINUE }, 'B'],
    ],
});
assert(tbl.constructor.name === 'Table', '纵向合并表格创建成功');

// ── h.table() 溢出保护 ──────────────────────────────────────

section('h.table() 溢出保护');

const overflowTable = h.table({
    widths: [1800, 4500, 1800, 4500],
    rows: [
        ['A', 'B', 'C', 'D'],
    ],
});
assert(overflowTable.constructor.name === 'Table', '溢出表格创建成功（自动缩放）');

const fitTable = h.table({
    widths: [3120, 3120, 3120],
    rows: [
        ['A', 'B', 'C'],
    ],
});
assert(fitTable.constructor.name === 'Table', '正常宽度表格不受影响');

const cw = h.contentWidth;
console.log(`  contentWidth = ${cw} DXA`);
assert(cw > 0, 'contentWidth 有效');

// ── keepNext / keepLines / widowControl ──────────────────────

section('keepNext / keepLines / widowControl');

const { Paragraph } = h.raw;

const heading1 = h.h1('标题一');
assert(heading1 instanceof Paragraph, 'h1 返回 Paragraph');

const heading2 = h.h2('标题二');
const heading3 = h.h3('标题三');

const pKeep = h.p('保持段', { keepNext: true, keepLines: true });
assert(pKeep instanceof Paragraph, 'p 支持 keepNext/keepLines');

const pWidow = h.p('孤行控制', { widowControl: true });
assert(pWidow instanceof Paragraph, 'p 支持 widowControl');

const headingBm = h.h2('书签标题', { bookmark: '_bm_heading' });
assert(headingBm instanceof Paragraph, '带 bookmark 的标题返回 Paragraph');

// ── children 嵌套数组自动展平 ────────────────────────────────

section('children 嵌套数组自动展平');

function fakeSection() {
    return [h.p('段落A'), h.p('段落B')];
}

const nestedOutPath = path.join(__dirname, '_test_nested.docx');
h.build({
    sections: [{
        children: [
            h.h1('标题'),
            fakeSection(),
            [h.p('深层嵌套1'), [h.p('深层嵌套2')]],
        ],
    }],
}, nestedOutPath).then(() => {
    const stat = fs.statSync(nestedOutPath);
    assert(stat.size > 0, '嵌套数组自动展平，文档生成成功');
    fs.unlinkSync(nestedOutPath);
}).catch(err => {
    console.error(`  ✘ 嵌套数组展平失败: ${err.message}`);
    failed++;
});

// ── h.build() 省略路径（argv 模式）────────────────────────────

section('h.build() 省略路径');

const argvOutPath = path.join(__dirname, '_test_argv_output.docx');
const origArgv2 = process.argv[2];
process.argv[2] = argvOutPath;

h.build({
    sections: [{ children: [h.p('argv 模式测试')] }],
}).then(() => {
    assert(fs.existsSync(argvOutPath), '省略路径时从 process.argv[2] 写入成功');
    fs.unlinkSync(argvOutPath);
    process.argv[2] = origArgv2;
}).catch(err => {
    console.error(`  ✘ argv 模式失败: ${err.message}`);
    failed++;
    process.argv[2] = origArgv2;
});

// ── h.build() patches 作为第二参数 ───────────────────────────

section('h.build() patches 作为第二参数');

const patchOutPath = path.join(__dirname, '_test_patch_output.docx');
process.argv[2] = patchOutPath;

h.build({
    sections: [{ children: [h.p('补丁模式测试')] }],
}, []).then(() => {
    assert(fs.existsSync(patchOutPath), 'patches 作为第二参数时正常工作');
    fs.unlinkSync(patchOutPath);
    process.argv[2] = origArgv2;
}).catch(err => {
    console.error(`  ✘ patches 模式失败: ${err.message}`);
    failed++;
    process.argv[2] = origArgv2;
});

// ── h.build() 集成（完整文档，向后兼容传路径）──────────────────

section('h.build() 集成（向后兼容）');

const outPath = path.join(__dirname, '_test_output.docx');

h.build({
    sections: [
        {
            children: [
                h.h1('封面标题', { align: 'center' }),
                h.spacer(400),
                h.p('副标题', { align: 'center', color: '999999' }),
            ],
        },
        {
            ...h.headerFooter('测试文档'),
            children: [
                h.h1('目  录', { align: 'center' }),
                h.toc(),
            ],
        },
        {
            ...h.headerFooter('测试文档'),
            children: [
                h.h1('第一章 测试', { bookmark: '_ch1' }),
                h.p('这是正文内容。'),
                h.bullet('列表项一'),
                h.bullet('列表项二'),
                h.h2('1.1 表格测试', { bookmark: '_s1' }),
                h.table({
                    widths: [3120, 3120, 3120],
                    header: ['列A', '列B', '列C'],
                    rows: [
                        ['数据1', '数据2', '数据3'],
                        [{ text: '合并', columnSpan: 2, bold: true, align: 'center' }, '单独'],
                    ],
                    headerColor: h.colors.primary,
                    altColor: h.colors.light,
                }),
            ],
        },
    ],
}, outPath).then(() => {
    const stat = fs.statSync(outPath);
    assert(stat.size > 0, `文档已生成，大小 ${stat.size} 字节`);
    fs.unlinkSync(outPath);

    return testCoverColorPatch();
}).then(() => {
    console.log(`\n=============================`);
    console.log(`总计: ${passed + failed} | 通过: ${passed} | 失败: ${failed}`);
    if (failed > 0) process.exit(1);
}).catch(err => {
    console.error(`\n  \u2718 build 失败: ${err.message}`);
    failed++;
    try { fs.unlinkSync(outPath); } catch (_) {}
    console.log(`\n=============================`);
    console.log(`总计: ${passed + failed} | 通过: ${passed} | 失败: ${failed}`);
    process.exit(1);
});

// ── h.refTracker() 编号压缩 ─────────────────────────────────

section('h.refTracker() 编号压缩');

const refs = h.refTracker();
const { TextRun } = h.raw;

function citeText(tr) {
    const wt = tr.root.find(n => n.rootKey === 'w:t');
    return wt ? wt.root.find(v => typeof v === 'string') : undefined;
}

const c1 = refs.cite('a');
assert(c1 instanceof TextRun, 'cite 返回 TextRun');

refs.cite('b');
refs.cite('c');
refs.cite('d');
refs.cite('e');

const cSingle = citeText(refs.cite('a'));
assert(cSingle === '[1]', `单引用: ${cSingle} === [1]`);

const cPair = citeText(refs.cite('a', 'c'));
assert(cPair === '[1,3]', `非连续双引用: ${cPair} === [1,3]`);

const cRange = citeText(refs.cite('a', 'b', 'c'));
assert(cRange === '[1-3]', `连续三引用压缩: ${cRange} === [1-3]`);

const cAll = citeText(refs.cite('a', 'b', 'c', 'd', 'e'));
assert(cAll === '[1-5]', `全连续压缩: ${cAll} === [1-5]`);

const cMixed = citeText(refs.cite('a', 'b', 'c', 'e'));
assert(cMixed === '[1-3,5]', `混合压缩: ${cMixed} === [1-3,5]`);

const cGaps = citeText(refs.cite('a', 'c', 'e'));
assert(cGaps === '[1,3,5]', `全不连续: ${cGaps} === [1,3,5]`);

const cComplex = citeText(refs.cite('a', 'b', 'd', 'e'));
assert(cComplex === '[1-2,4-5]', `两段连续: ${cComplex} === [1-2,4-5]`);

// ── coverColor patch ─────────────────────────────────────────
async function testCoverColorPatch() {
    section('coverColor patch');
    const JSZip = require('jszip');
    const coverOut = path.join(os.tmpdir(), 'test_cover_color.docx');

    await h.build({
        sections: [
            {
                children: [
                    h.spacer(3000),
                    h.p('封面标题', { size: 52, bold: true, color: 'FFFFFF', align: 'center' }),
                ],
            },
            {
                children: [h.p('正文内容')],
            },
        ],
    }, coverOut, [
        { type: 'coverColor', colors: ['1A1A2E', '3D1F0B'] },
    ]);

    const stat = fs.statSync(coverOut);
    assert(stat.size > 0, `coverColor 文档已生成，大小 ${stat.size} 字节`);

    const buf = fs.readFileSync(coverOut);
    const zip = await JSZip.loadAsync(buf);
    const docXml = await zip.file('word/document.xml').async('string');

    assert(docXml.includes('CoverColorBg'), 'document.xml 包含 CoverColorBg docPr');
    assert(docXml.includes('gradFill'), 'document.xml 包含渐变填充 gradFill');
    assert(docXml.includes('1A1A2E'), 'document.xml 包含起始色 1A1A2E');
    assert(docXml.includes('3D1F0B'), 'document.xml 包含结束色 3D1F0B');

    const solidOut = path.join(os.tmpdir(), 'test_cover_solid.docx');
    await h.build({
        sections: [{ children: [h.p('纯色封面')] }],
    }, solidOut, [
        { type: 'coverColor', colors: ['2B579A'] },
    ]);

    const solidBuf = fs.readFileSync(solidOut);
    const solidZip = await JSZip.loadAsync(solidBuf);
    const solidXml = await solidZip.file('word/document.xml').async('string');

    assert(solidXml.includes('solidFill'), '纯色模式使用 solidFill');
    assert(solidXml.includes('2B579A'), '纯色模式包含色值 2B579A');

    fs.unlinkSync(coverOut);
    fs.unlinkSync(solidOut);
}
