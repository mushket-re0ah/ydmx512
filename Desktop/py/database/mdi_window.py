from kivy.clock import Clock
from libs.kivy_json_orm.table_implementation import DatabaseTable, DatabaseRow
from libs.serialize import serializable_or_raw_serializer
from libs.kivy_json_orm.fields import StringField, BooleanField, ObjectField


class ViewContextSaverMixin:
    """Микшин для MDIWindow. Автоматически сохраняет состояние виджетов
    по плоскому списку путей, в том числе с динамическими ключами @var."""

    view_context_template = {}  # переопределить в наследнике

    def load_view_context(self):
        Clock.schedule_once(self._load_view_context, 0)

    def _load_view_context(self, _):
        self._saved_vc = self.mdi_db_row.view_context or {}
        self._bindings = {}
        for path, params in self.view_context_template.items():
            self._setup_path(path, params)

    def _get_params(self, params):
        """Если params — словарь с ключом 'default', это расширенный формат.
        Иначе это просто значение по умолчанию без сериализаторов.
        """
        if isinstance(params, dict) and 'default' in params:
            return params.get('default'), params.get('serialize'), params.get('deserialize')
        return params, None, None

    def _setup_path(self, path, params):
        # Разделяем путь на "объект" и "свойство@var"
        default, serialize, deserialize = self._get_params(params)
        obj_path, _, rest = path.rpartition('/')
        if not obj_path:
            obj_path, rest = '', path
        if rest:
            prop, _, dynamic_var = rest.partition('@')
        else:
            prop, dynamic_var = obj_path, None
            obj_path = ''

        # Поиск целевого объекта по цепочке obj_path (через точки)
        if obj_path:
            obj = self
            for attr in obj_path.split('.'):
                child = getattr(obj, attr, None)
                if child is None:
                    obj.bind(**{attr: lambda i, v, a=attr, p=path, pr=params: self._rebind_path(p, pr) if v else None})
                    return
                obj = child
        else:
            obj = self

        if dynamic_var:
            self._bind_dynamic(obj, prop, dynamic_var, path, default, serialize, deserialize)
        else:
            self._bind_static(obj, prop, path, default, serialize, deserialize)

    def _apply_value(self, obj, prop, key, default, serialize, deserialize):
        """Восстанавливает значение из _saved_vc или устанавливает default."""
        if key in self._saved_vc:
            val = self._saved_vc[key]
            if deserialize:
                val = deserialize(obj, val)
            setattr(obj, prop, val)
        else:
            setattr(obj, prop, default)

    def _add_change_tracker(self, path, obj, prop, key_func, serialize):
        """Добавляет бинд на изменение свойства и сохранение в _saved_vc.
        key_func вызывается без аргументов и возвращает актуальный ключ для сохранения.
        """
        def on_change(instance, value):
            key = key_func()
            stored = serialize(instance, value) if serialize else value
            self._saved_vc[key] = stored
            self._save()
        obj.bind(**{prop: on_change})
        self._bindings.setdefault(path, []).append((obj, prop, on_change))

    def _bind_static(self, obj, prop, path, default, serialize, deserialize):
        self._apply_value(obj, prop, path, default, serialize, deserialize)
        self._add_change_tracker(path, obj, prop, lambda: path, serialize)

    def _bind_dynamic(self, obj, prop, var, path, default, serialize, deserialize):
        current_var = getattr(self, var, None)
        if current_var is not None:
            actual_key = path.replace(f'@{var}', f'_{current_var}')
            self._apply_value(obj, prop, actual_key, default, serialize, deserialize)

        # Отслеживаем изменение свойства (с динамическим ключом)
        self._add_change_tracker(
            path, obj, prop,
            key_func=lambda: path.replace(f'@{var}', f'_{getattr(self, var, "")}'),
            serialize=serialize
        )

        # Отслеживаем изменение переменной (восстановление значения при переключении)
        def on_var_change(instance, new_var):
            new_key = path.replace(f'@{var}', f'_{new_var}')
            self._apply_value(obj, prop, new_key, default, serialize, deserialize)
        self.bind(**{var: on_var_change})
        self._bindings.setdefault(path, []).append((self, var, on_var_change))

    def _rebind_path(self, path, params):
        """Вызывается, когда нужный объект появляется в дереве."""
        self._unbind_path(path)
        self._setup_path(path, params)

    def _unbind_path(self, path):
        for obj, prop, func in self._bindings.get(path, []):
            obj.unbind(**{prop: func})
        self._bindings.pop(path, None)

    def _save(self):
        self.mdi_db_row.edit(view_context=self._saved_vc)

    def _unbind_all(self):
        for path in list(self._bindings):
            self._unbind_path(path)

    def on_close(self, *args):
        self._save()
        return super().on_close(*args)


class RowMDIWindow(DatabaseRow):
    title_id = StringField()
    locked = BooleanField(False)
    expanded = BooleanField(False)
    view_context = ObjectField(serialize=serializable_or_raw_serializer(), deserialize=lambda self, v: v, allownone=True)


class TableMDIWindow(DatabaseTable):
    cls_row = RowMDIWindow
    filename = "mdi_window.json"
