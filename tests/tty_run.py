"""Run a command in a pseudo-terminal, feeding one line of input (simulates a human)."""
import os, pty, sys, time

cwd, answer, *cmd = sys.argv[1:]
pid, fd = pty.fork()
if pid == 0:
    os.chdir(cwd)
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDECODE",)}
    os.execvpe(cmd[0], cmd, env)
buf = b""
sent = False
while True:
    try:
        data = os.read(fd, 4096)
    except OSError:
        break
    if not data:
        break
    buf += data
    low = buf.lower()
    if not sent and (b"confirm:" in low or b"confirmar:" in low):
        reply = "yes" if (b"yes to confirm" in low or b"sim para confirmar" in low) else answer
        os.write(fd, (reply + "\n").encode())
        sent = True
_, status = os.waitpid(pid, 0)
print(buf.decode(errors="replace"))
print("EXIT", os.waitstatus_to_exitcode(status))
