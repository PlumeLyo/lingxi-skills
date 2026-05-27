from __future__ import annotations

import argparse
import json
from pathlib import Path

from docx_template_adapters import get_adapter, list_adapters


def _resolve_template_path(adapter_id: str, template_path: str | None) -> str:
    adapter = get_adapter(adapter_id)
    resolved = template_path or adapter.default_template_path
    if not resolved:
        raise ValueError(
            f"Adapter '{adapter_id}' does not define a default template. Pass --template explicitly."
        )
    return resolved


def main() -> None:
    parser = argparse.ArgumentParser(description="Run DOCX template adapters through a shared interface.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List available DOCX template adapters.")
    list_parser.add_argument("--out", help="Optional JSON output path.")

    inspect_parser = subparsers.add_parser("inspect", help="Inspect a template through an adapter.")
    inspect_parser.add_argument("--adapter", required=True, help="Adapter ID, for example: cjc")
    inspect_parser.add_argument("--template", help="Optional template path. Uses the adapter default when omitted.")
    inspect_parser.add_argument("--sample-limit", type=int, default=40, help="Max sample paragraphs to collect.")
    inspect_parser.add_argument("--out", help="Optional JSON output path.")

    generate_parser = subparsers.add_parser("generate", help="Generate a DOCX through an adapter.")
    generate_parser.add_argument("--adapter", required=True, help="Adapter ID, for example: cjc")
    generate_parser.add_argument("--template", help="Optional template path. Uses the adapter default when omitted.")
    generate_parser.add_argument("--spec", required=True, help="Path to the JSON spec.")
    generate_parser.add_argument("--output", required=True, help="Path to the output DOCX.")

    args = parser.parse_args()

    if args.command == "list":
        result = {
            "adapters": [
                {
                    "adapter_id": adapter.adapter_id,
                    "description": adapter.description,
                    "spec_family": adapter.spec_family,
                    "default_template_path": adapter.default_template_path,
                    "default_profile_path": adapter.default_profile_path,
                }
                for adapter in list_adapters()
            ]
        }
        _emit_json(result, args.out)
        return

    adapter = get_adapter(args.adapter)
    template_path = _resolve_template_path(args.adapter, getattr(args, "template", None))

    if args.command == "inspect":
        result = adapter.inspect_template(template_path, args.sample_limit)
        result["adapter_id"] = adapter.adapter_id
        result["spec_family"] = adapter.spec_family
        if adapter.default_profile_path:
            result["default_profile_path"] = adapter.default_profile_path
        _emit_json(result, args.out)
        return

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    result = adapter.generate_document(template_path, spec, args.output)
    result["adapter_id"] = adapter.adapter_id
    result["spec_family"] = adapter.spec_family
    _emit_json(result)


def _emit_json(payload: dict, output_path: str | None = None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if output_path:
        Path(output_path).write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
