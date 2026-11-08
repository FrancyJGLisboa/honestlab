"""honestlab data-read watch, loaded only when honestlab runs a Python evaluator.

It records when code under the editable paths (the candidate) opens a file under the watched
paths (the data and the evaluator). The evaluator itself may read its data; the candidate may
not. This is a tripwire, not a sandbox: code running in the same process can get around it
with enough effort, and that effort shows up in the patch.
"""
import os
import sys


def _install():
    log = os.environ.get("HONESTLAB_AUDIT_LOG")
    if not log:
        return
    sep = os.pathsep
    editable = [os.path.realpath(p) for p in os.environ.get("HONESTLAB_AUDIT_EDITABLE", "").split(sep) if p]
    watch = [os.path.realpath(p) for p in os.environ.get("HONESTLAB_AUDIT_WATCH", "").split(sep) if p]
    if not editable or not watch:
        return
    realpath, getframe = os.path.realpath, sys._getframe
    seen = set()

    def under(path, roots):
        return any(path == r or path.startswith(r + os.sep) for r in roots)

    launch_events = ("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.spawn", "os.startfile",
                     "pty.spawn", "ctypes.dlopen")

    def from_editable():
        f = getframe(0)
        while f is not None:
            fn = f.f_code.co_filename
            if fn and not fn.startswith("<") and under(realpath(fn), editable):
                return fn
            f = f.f_back
        return None

    def record(fn, what):
        key = (what, fn)
        if key in seen:
            return
        seen.add(key)
        try:
            with open(log, "a", encoding="utf-8") as fh:
                fh.write(f"{fn}\t{what}\n")
        except OSError:
            pass

    def hook(event, args):
        try:
            if event == "open" and args:
                _check(args)
            elif event in launch_events:
                fn = from_editable()
                if fn:
                    shown = args[0] if args else event
                    if isinstance(shown, (list, tuple)):
                        shown = " ".join(map(str, shown))
                    record(fn, f"launched a program ({event}: {str(shown)[:120]})")
        except Exception:  # a tripwire must never break the program it watches
            pass

    def _check(args):
        target = args[0]
        if isinstance(target, int):
            return
        try:
            path = realpath(os.fsdecode(target))
        except (TypeError, ValueError, OSError):
            return
        if not under(path, watch) or path == log:
            return
        f = getframe(0)
        while f is not None:
            fn = f.f_code.co_filename
            if fn and not fn.startswith("<"):
                if under(realpath(fn), editable):
                    key = (path, fn)
                    if key not in seen:
                        seen.add(key)
                        try:
                            with open(log, "a", encoding="utf-8") as fh:
                                fh.write(f"{fn}\t{path}\n")
                        except OSError:
                            pass
                    return
            f = f.f_back

    sys.addaudithook(hook)


_install()
