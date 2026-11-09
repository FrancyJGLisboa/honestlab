"""honestlab data-read watch, loaded only when honestlab runs a Python evaluator.

It records when code under the editable paths (the candidate) opens a file under the watched
paths (the data and the evaluator). The evaluator itself may read its data; the candidate may
not. This is a tripwire, not a sandbox: code running in the same process can get around it
with enough effort, and that effort shows up in the patch.

Native libraries: loading one with ctypes counts as launching a program, because native code
can start programs without Python seeing it. Libraries inside the Python installation or a
site-packages folder (numpy, PyTorch and the like, including the lab's own .venv) are allowed.

This file replaces any sitecustomize the Python installation has (Homebrew, Debian), so it
loads that file afterwards. Without that, Homebrew Python loses its site-packages.
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
    os_realpath, getframe = os.path.realpath, sys._getframe
    seen = set()
    cache = {}

    def realpath(p):
        r = cache.get(p)
        if r is None:
            r = cache[p] = os_realpath(p)
        return r

    def under(path, roots):
        return any(path == r or path.startswith(r + os.sep) for r in roots)

    launch_events = ("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.spawn", "os.startfile",
                     "pty.spawn", "ctypes.dlopen")

    def installed_library(name):
        """True when a ctypes.dlopen target is a file inside Python's install or site-packages."""
        if not isinstance(name, (str, bytes, os.PathLike)):
            return False
        try:
            path = os_realpath(os.fsdecode(name))
        except (TypeError, ValueError, OSError):
            return False
        if not os.path.isabs(os.fsdecode(name)) or not os.path.isfile(path):
            return False
        roots = {realpath(p) for p in (sys.prefix, sys.base_prefix, sys.exec_prefix) if p}
        roots |= {realpath(p) for p in sys.path if p and ("site-packages" in p or "dist-packages" in p)}
        return under(path, roots) and not under(path, editable) and not under(path, watch)

    def ctypes_own_handle():
        """True when the stdlib ctypes module opens the running process for ctypes.pythonapi."""
        f = getframe(0)
        while f is not None and not f.f_code.co_filename.endswith(os.path.join("ctypes", "__init__.py")):
            f = f.f_back
        while f is not None and f.f_code.co_filename.endswith(os.path.join("ctypes", "__init__.py")):
            if f.f_code.co_name == "<module>":
                return True
            f = f.f_back
        return False

    # Calling these through ctypes starts a program or opens a file without Python's audit events.
    native_launch = {"system", "popen", "fork", "vfork", "forkpty", "execv", "execve", "execvp", "execvpe",
                     "execl", "execle", "execlp", "fexecve", "posix_spawn", "posix_spawnp", "open", "openat",
                     "fopen", "freopen", "creat", "dlopen", "CreateProcessA", "CreateProcessW", "WinExec",
                     "ShellExecuteA", "ShellExecuteW", "CreateFileA", "CreateFileW", "LoadLibraryA",
                     "LoadLibraryW", "LoadLibraryExA", "LoadLibraryExW"}

    # Ways to reach the evaluator's own variables (where the answers are) from candidate code.
    memory_events = ("sys._getframe", "sys._current_frames", "sys._current_exceptions", "gc.get_objects",
                     "gc.get_referrers", "gc.get_referents")
    memory_attrs = {"tb_frame", "gi_frame", "cr_frame", "ag_frame", "f_back", "f_locals", "f_globals"}
    this_file = realpath(__file__)
    busy = []

    def direct_caller():
        """The frame that triggered the event, seen through inspect.py helpers."""
        f = getframe(0)
        while f is not None:
            fn = f.f_code.co_filename
            if fn and not fn.startswith("<") and realpath(fn) != this_file and \
                    not fn.endswith(os.sep + "inspect.py"):
                return fn
            f = f.f_back
        return None

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
        if busy:  # the checks below call sys._getframe, which raises an event of its own
            return
        busy.append(1)
        try:
            if event in memory_events or (event == "object.__getattr__" and len(args) >= 2
                                          and args[1] in memory_attrs):
                fn = direct_caller()
                if fn and under(realpath(fn), editable):
                    shown = event if event != "object.__getattr__" else args[1]
                    record(fn, f"read the evaluator's memory ({shown})")
            elif event == "open" and args:
                _check(args)
            elif event in launch_events:
                if event == "ctypes.dlopen" and args and (installed_library(args[0]) or
                                                          (args[0] is None and ctypes_own_handle())):
                    return
                fn = from_editable()
                if fn:
                    shown = args[0] if args else event
                    if isinstance(shown, (list, tuple)):
                        shown = " ".join(map(str, shown))
                    record(fn, f"launched a program ({event}: {str(shown)[:120]})")
            elif event.startswith("ctypes.dlsym") and len(args) >= 2:
                name = args[1]
                name = name.decode("ascii", "replace") if isinstance(name, bytes) else name
                if isinstance(name, str) and name.lstrip("_") in native_launch:
                    fn = from_editable()
                    if fn:
                        record(fn, f"launched a program (ctypes native function {name})")
        except Exception:  # a tripwire must never break the program it watches
            pass
        finally:
            busy.clear()

    def _check(args):
        target = args[0]
        if isinstance(target, int):
            return
        try:
            path = os_realpath(os.fsdecode(target))
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


def _chain():
    """Run the sitecustomize this file hides, if the Python installation has one."""
    import importlib.machinery
    import importlib.util
    here = os.path.dirname(os.path.realpath(__file__))
    rest = [p for p in sys.path if p and os.path.realpath(p) != here]
    spec = importlib.machinery.PathFinder.find_spec("sitecustomize", rest)
    if spec is None or spec.loader is None or not spec.origin:
        return
    if os.path.realpath(spec.origin) == os.path.realpath(__file__):
        return
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)


_install()
_chain()
