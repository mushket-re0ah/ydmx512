# https://github.com/kivy/kivy/issues/9373

def apply_patch():
    from types import MethodType
    from kivy.lang import builder
    def patch_sync(self):
        next_args = builder._delayed_start
        builder._delayed_start = None  # moved there from end of procedure
        if next_args is None:
            return

        while next_args is not StopIteration:
            try:
                builder.call_fn(next_args[:-1], None, None)
            except ReferenceError:
                pass
            args = next_args
            next_args = args[-1]
            args[-1] = None

    builder.Builder.sync = MethodType(patch_sync, builder.Builder)
