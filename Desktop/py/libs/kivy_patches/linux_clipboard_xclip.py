from kivy.utils import platform


def apply_patch():
    if platform != "linux":
        return

    from kivy.core.clipboard.clipboard_xclip import ClipboardXclip
    import subprocess
    def patch_xclip(inout, selection):
        pipe = {'std' + inout: subprocess.PIPE}
        if inout == 'in':
            pipe['stdout'] = subprocess.DEVNULL
            pipe['stderr'] = subprocess.DEVNULL
        else:
            pipe['stderr'] = subprocess.DEVNULL

        return subprocess.Popen(
            ['xclip', '-' + inout, '-selection', selection],
            **pipe)

    ClipboardXclip._clip = staticmethod(patch_xclip)
