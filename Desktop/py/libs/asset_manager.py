from pathlib import Path
from typing import List, Any
from libs.serialize import SerializableMixin
from libs.file_utils import atomic_json_save, json_load
from libs import logger


class FileAssetManager:
    def __init__(self, root_dir: Path, subdir_name: str, data_class: SerializableMixin, extension: str=".json"):
        self.root_dir = Path(root_dir)
        self.subdir_name = subdir_name
        self.data_class = data_class
        self.dirname = self.root_dir / self.subdir_name
        self.extension = extension
        if not self.dirname.is_dir():
            self.dirname.mkdir(parents=True, exist_ok=True)
            self._create_default()
        self._on_init()

    def get_asset_by_path(self, filepath: Path) -> Any:
        return self._get_asset_by_path(filepath)

    def _get_asset_by_path(self, filepath: Path) -> Any:
        try:
            return self._deserialize(self._load_asset(filepath))
        except Exception as e:
            logger.warning(f"Failed to load asset from {filepath}: {e}")
        return None

    def add_asset(self, key, asset: SerializableMixin) -> bool:
        asset_dir = self._get_asset_dirname(key)
        asset_dir.mkdir(exist_ok=True)
        filepath = asset_dir / self._get_asset_filename(asset)
        return self._save_asset(filepath, asset)

    def get_asset_list(self, key) -> List[Any]:
        asset_dir = self._get_asset_dirname(key)
        if not asset_dir.is_dir():
            return []
        return [
            self.get_asset_by_path(fp)
            for fp in asset_dir.iterdir()
            if fp.is_file() and fp.suffix == self.extension
        ]

    def _serialize(self, asset: Any) -> Any:
        return asset.serialize()

    def _deserialize(self, data) -> Any:
        return self.data_class.from_data(data)

    def _get_asset_filename(self, asset: SerializableMixin) -> str:
        return f"{self._get_asset_stem(asset)}{self.extension}"

    def _get_asset_stem(self, asset: SerializableMixin) -> str:
        return asset.title

    def _save_asset(self, filepath: Path, asset: SerializableMixin) -> bool:
        try:
            atomic_json_save(filepath, self._serialize(asset))
            return True
        except Exception as e:
            logger.critical(f"Ошибка сохранения ассета {asset}, filepath={filepath}", exc_info=e)
            return False

    def _load_asset(self, filepath: Path) -> Any:
        return json_load(filepath)

    def _get_asset_dirname(self, key) -> Path:
        return self.dirname / self._key_to_string(key)

    def _key_to_string(self, key) -> str:
        return str(key)

    def _create_default(self):
        pass

    def _on_init(self):
        pass
