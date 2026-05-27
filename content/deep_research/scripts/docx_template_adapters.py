from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


InspectFn = Callable[[str | Path, int], dict[str, Any]]
GenerateFn = Callable[[str | Path, dict[str, Any], str | Path], dict[str, Any]]


@dataclass(frozen=True)
class DocxTemplateAdapter:
    adapter_id: str
    description: str
    spec_family: str
    default_template_path: str | None
    default_profile_path: str | None
    inspect_template: InspectFn
    generate_document: GenerateFn


_SCRIPT_DIR = Path(__file__).resolve().parent
_REGISTRY: dict[str, DocxTemplateAdapter] = {}
_BUILTINS_LOADED = False


def register_adapter(adapter: DocxTemplateAdapter) -> None:
    _REGISTRY[adapter.adapter_id] = adapter


def get_adapter(adapter_id: str) -> DocxTemplateAdapter:
    _load_builtin_adapters()
    try:
        return _REGISTRY[adapter_id]
    except KeyError as exc:
        available = ", ".join(sorted(_REGISTRY))
        raise KeyError(f"Unknown adapter '{adapter_id}'. Available: {available}") from exc


def list_adapters() -> list[DocxTemplateAdapter]:
    _load_builtin_adapters()
    return [_REGISTRY[key] for key in sorted(_REGISTRY)]


def _load_builtin_adapters() -> None:
    global _BUILTINS_LOADED
    if _BUILTINS_LOADED:
        return

    _register_module_adapter(
        _load_module("cjc_docx_writer_builtin", "cjc_docx_writer.py"),
        default_adapter_id="cjc",
        default_description="CJC academic DOCX template adapter.",
    )
    _register_module_adapter(
        _load_module("jos_docx_writer_builtin", "jos_docx_writer.py"),
        default_adapter_id="jos",
        default_description="Journal of Software academic DOCX template adapter.",
    )
    _register_module_adapter(
        _load_module("generic_docx_writer_builtin", "generic_docx_writer.py"),
        default_adapter_id="generic",
        default_description="Best-effort generic academic DOCX template adapter.",
    )
    _BUILTINS_LOADED = True


def _register_module_adapter(module, *, default_adapter_id: str, default_description: str) -> None:
    register_adapter(
        DocxTemplateAdapter(
            adapter_id=str(getattr(module, "ADAPTER_ID", default_adapter_id)),
            description=str(getattr(module, "ADAPTER_DESCRIPTION", default_description)),
            spec_family=str(getattr(module, "SPEC_FAMILY", "docx-report-spec-v1")),
            default_template_path=_stringify_path(getattr(module, "DEFAULT_TEMPLATE_PATH", None)),
            default_profile_path=_stringify_path(getattr(module, "DEFAULT_PROFILE_PATH", None)),
            inspect_template=getattr(module, "inspect_template"),
            generate_document=getattr(module, "generate_document"),
        )
    )


def _load_module(module_name: str, filename: str):
    module_path = _SCRIPT_DIR / filename
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _stringify_path(value: Any) -> str | None:
    if value is None:
        return None
    return str(Path(value))
