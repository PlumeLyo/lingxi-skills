"""
WPS Skill - WPS 365 V7 API 封装

使用方式：
    import sys
    sys.path.insert(0, "cooffice/skills/wps_docs/scripts")
    from kdocs import WpsClient

    client = WpsClient()
    result = client.download_file(file_id="xxx", save_dir="/tmp")
"""

from .kdocs import WpsClient, WpsSession

__all__ = [
    "WpsClient",
    "WpsSession",
]
