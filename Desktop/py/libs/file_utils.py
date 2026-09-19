import json
from typing import Any, Dict, List, Optional
from pathlib import Path
import os
from libs import logger


def json_save(
    filepath: Path,
    data: Dict[str, Any],
    ensure_ascii: bool = False,
    indent: str = '\t'
) -> None:
    try:
        json_str = json.dumps(data, ensure_ascii=ensure_ascii, indent=indent)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(json_str)
    except Exception as e:
        logger.critical(f"Ошибка сохранения файла {filepath}", exc_info=e)
        raise e


def atomic_json_save(
    filepath: Path,
    data: Dict[str, Any],
    ensure_ascii: bool = False,
    indent: str = '\t'
) -> None:
    """
    Атомарно сохраняет данные в JSON-файл.
    Сначала пишет во временный файл, затем заменяет.
    """
    tmp_filepath = filepath.with_suffix(filepath.suffix + '.tmp')
    try:
        json_str = json.dumps(data, ensure_ascii=ensure_ascii, indent=indent)
        # minification
        # json_str = json.dumps(data_dict, ensure_ascii=False, separators=(',', ':'))
        with open(tmp_filepath, 'w', encoding='utf-8') as f:
            f.write(json_str)
        os.replace(tmp_filepath, filepath)
    except Exception as e:
        if tmp_filepath.exists():
            tmp_filepath.unlink()
        logger.critical(f"Ошибка сохранения файла {filepath}", exc_info=e)
        raise e


def json_load(filepath: Path) -> Optional[dict]:
    data = None
    try:
        with open(filepath, "r", encoding="utf8") as fptr:
            data = json.loads(fptr.read())
    except Exception as e:
        logger.debug(f"{filepath} not exist, about: {e}")
    return data
