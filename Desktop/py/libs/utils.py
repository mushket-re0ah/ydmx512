from typing import Any, Callable, Dict, Sequence, Tuple


def merge_kwargs(default_kwargs: Dict[Any, Any], kwargs: Dict[Any, Any]) -> Dict[Any, Any]:
    for k, v in default_kwargs.items():
        if k not in kwargs:
            kwargs[k] = v
    if "other_attributes" in kwargs and "other_attributes" in default_kwargs:
        kwargs_other_attrs = kwargs["other_attributes"]
        for k, v in default_kwargs["other_attributes"].items():
            if k not in kwargs_other_attrs:
                kwargs_other_attrs[k] = v
    return kwargs


class ThrottledCall:
    def __init__(self, func: Callable[..., None], initial_interval: float):
        self.func: Callable[..., None] = func
        self.interval: float = initial_interval
        self._accumulator: float = 0.0

    def __call__(self, delta_time: float, *args: Any, **kwargs: Any) -> Any:
        self._accumulator += delta_time
        if self._accumulator >= self.interval:
            self._accumulator -= self.interval
            return self.func(*args, **kwargs)
        return None


def with_item(
    items: Sequence[Any],
    item: Any,
    unique: bool = False,
    identity: bool = True,
) -> Tuple[Any, ...]:
    if unique:
        exists = any(x is item for x in items) if identity else item in items
        if exists:
            return tuple(items)
    return tuple((*items, item))


def without_item(items: Sequence[Any], item: Any, identity:bool=True) -> Tuple[Any, ...]:
    if identity:
        return tuple(x for x in items if x is not item)
    return tuple(x for x in items if x != item)


def format_file_size(size: int) -> str:
    value = float(size)

    for unit in ("Б", "КБ", "МБ", "ГБ", "ТБ"):
        if value < 1024 or unit == "ТБ":
            if unit == "Б":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"

        value /= 1024

    raise AssertionError("unreachable")
