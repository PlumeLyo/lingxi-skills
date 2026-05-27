from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from docx.enum.text import WD_ALIGN_PARAGRAPH

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from docx_writer_core import (  # noqa: E402
    FrontMatterField,
    WriterConfig,
    generate_document as generate_document_from_template,
    inspect_template as inspect_template_profile,
    load_json,
)

SKILL_DIR = SCRIPT_DIR.parent
ADAPTER_ID = "cjc"
ADAPTER_DESCRIPTION = "CJC academic DOCX template adapter for Chinese journal and academic manuscript layouts."
SPEC_FAMILY = "docx-report-spec-v1"
DEFAULT_TEMPLATE_PATH = SKILL_DIR / "assets/CJC-Templet_Word2003.docx"
DEFAULT_PROFILE_PATH = SKILL_DIR / "references/cjc-template-profile.json"


STYLE_CANDIDATES: dict[str, list[str]] = {
    "title_cn": ["Subtitle", "Title", "Normal"],
    "authors_cn": ["作者", "Normal"],
    "affiliations_cn": ["单位", "Normal"],
    "abstract_cn": ["摘要", "Body Text", "Normal"],
    "keywords_cn": ["关键词", "Body Text", "Normal"],
    "classification_cn": ["分类号", "Body Text", "Normal"],
    "title_en": ["Title1", "Title", "Normal"],
    "authors_en": ["Name", "Normal"],
    "affiliations_en": ["Depart.Correspond", "Normal"],
    "abstract_en": ["Abstract", "Body Text", "Normal"],
    "keywords_en": ["Key words", "Body Text", "Normal"],
    "heading_1": ["Heading 1", "标题1", "Normal"],
    "heading_2": ["Heading 2", "标题11", "Normal"],
    "heading_3": ["Heading 3", "Normal"],
    "body": ["Body Text", "Normal"],
    "ack_heading": ["致谢", "Heading 1", "Normal"],
    "reference_heading": ["Normal", "Reference"],
    "reference_cn_text": ["Text of 中文参考文献", "中文参考文献", "Normal"],
    "reference_en_text": ["Text of Reference", "Reference", "Normal"],
    "appendix_heading": ["Heading 1", "Normal"],
}

FRONT_MATTER_FIELDS = (
    FrontMatterField(
        spec_key="title_cn",
        style_key="title_cn",
        alignment=WD_ALIGN_PARAGRAPH.CENTER,
    ),
    FrontMatterField(
        spec_key="authors_cn",
        style_key="authors_cn",
        mode="join_list",
        alignment=WD_ALIGN_PARAGRAPH.CENTER,
    ),
    FrontMatterField(
        spec_key="affiliations_cn",
        style_key="affiliations_cn",
        mode="list",
        alignment=WD_ALIGN_PARAGRAPH.CENTER,
    ),
    FrontMatterField(
        spec_key="abstract_cn",
        style_key="abstract_cn",
        label="摘  要",
    ),
    FrontMatterField(
        spec_key="keywords_cn",
        style_key="keywords_cn",
        mode="keywords",
        label="关键词",
        separator="；",
    ),
    FrontMatterField(
        spec_key="classification_cn",
        style_key="classification_cn",
        label="中图法分类号",
    ),
    FrontMatterField(
        spec_key="title_en",
        style_key="title_en",
        alignment=WD_ALIGN_PARAGRAPH.CENTER,
    ),
    FrontMatterField(
        spec_key="authors_en",
        style_key="authors_en",
        mode="join_list",
        alignment=WD_ALIGN_PARAGRAPH.CENTER,
    ),
    FrontMatterField(
        spec_key="affiliations_en",
        style_key="affiliations_en",
        mode="list",
        alignment=WD_ALIGN_PARAGRAPH.CENTER,
    ),
    FrontMatterField(
        spec_key="abstract_en",
        style_key="abstract_en",
        label="Abstract",
    ),
    FrontMatterField(
        spec_key="keywords_en",
        style_key="keywords_en",
        mode="keywords",
        label="Key words",
        separator="; ",
    ),
)

CJC_WRITER_CONFIG = WriterConfig(
    style_candidates=STYLE_CANDIDATES,
    front_matter_fields=FRONT_MATTER_FIELDS,
    body_columns=2,
    acknowledgement_heading="致  谢",
    reference_heading="参 考 文 献",
    appendix_default_title="附录",
)


def inspect_template(template_path: str | Path, sample_limit: int = 40) -> dict[str, Any]:
    return inspect_template_profile(
        template_path=template_path,
        style_candidates=STYLE_CANDIDATES,
        sample_limit=sample_limit,
    )


def generate_document(
    template_path: str | Path,
    spec: dict[str, Any],
    output_path: str | Path,
) -> dict[str, Any]:
    return generate_document_from_template(
        template_path=template_path,
        spec=spec,
        output_path=output_path,
        config=CJC_WRITER_CONFIG,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect and write CJC template DOCX files.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Inspect template styles and structure.")
    inspect_parser.add_argument("--template", required=True, help="Path to the .docx template.")
    inspect_parser.add_argument("--out", help="Optional JSON output path.")

    generate_parser = subparsers.add_parser("generate", help="Generate a .docx from a JSON spec.")
    generate_parser.add_argument("--template", required=True, help="Path to the .docx template.")
    generate_parser.add_argument("--spec", required=True, help="Path to the JSON spec.")
    generate_parser.add_argument("--output", required=True, help="Path to the output .docx.")

    args = parser.parse_args()

    if args.command == "inspect":
        result = inspect_template(args.template)
        text = json.dumps(result, ensure_ascii=False, indent=2)
        if args.out:
            Path(args.out).write_text(text, encoding="utf-8")
        print(text)
        return

    result = generate_document(
        template_path=args.template,
        spec=load_json(args.spec),
        output_path=args.output,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
