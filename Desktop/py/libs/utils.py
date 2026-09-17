from typing import Callable


def merge_kwargs(default_kwargs: dict, kwargs: dict) -> dict:
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
    def __init__(self, func: Callable, initial_interval: float):
        self.func = func
        self.interval = initial_interval
        self._accumulator = 0.0

    def __call__(self, delta_time: float, *args, **kwargs) -> any:
        self._accumulator += delta_time
        if self._accumulator >= self.interval:
            self._accumulator -= self.interval
            return self.func(*args, **kwargs)
        return None
