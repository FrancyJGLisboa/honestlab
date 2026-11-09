"""Approve the lab from inside the chat (Claude Code UserPromptSubmit hook).

Two messages from the person, never from the agent:

1. The person types ``aprovar`` / ``approve``. If the lab is ready, the hook blocks that
   message (so the agent never sees it) and shows the person the real APPROVAL.md
   together with a one-time code. Claude Code shows a block reason to the person
   only; it is not added to the model's context.
2. The person types ``sim 4821`` / ``yes 4821``. The hook checks the code, that it has
   not expired and that nothing measured changed in between, then freezes exactly as
   ``honestlab freeze`` does in a terminal, records ``approved_via: chat`` in the ledger
   and lets the message through with a note telling the agent to continue.

Unlocking works the same way: ``destrancar`` / ``unlock``, then ``sim 4821`` / ``yes 4821``.
It runs exactly what ``honestlab unfreeze`` runs in a terminal and records ``via: chat``.

The agent cannot type a user message. The guard also blocks the agent from running
``honestlab guard prompt`` itself. As with every rule that depends on the agent's
environment, a determined agent running as the same OS user could still work around
it (for example by reading the session transcript); the attempt would be visible in its
tool calls, and the hashes still catch any change to protected files.
"""
import contextlib
import hashlib
import io
import json
import re
import secrets
import time

from . import core
from .core import LabError

APPROVE_RE = re.compile(r"^\s*(?:honestlab\s+)?(aprovar|aprovo|aprova|approve|i approve)\s*[.!]?\s*$", re.I)
UNLOCK_RE = re.compile(r"^\s*(?:honestlab\s+)?(destrancar|destranca|destranque|destrancar o laborat[óo]rio|"
                       r"unlock|unfreeze|unlock the lab)\s*[.!]?\s*$", re.I)
STOP_RE = re.compile(r"^\s*(parar|pare|chega|parar o modo noite|para tudo|stop|stop overnight|halt)\s*[.!]?\s*$", re.I)
CONFIRM_RE = re.compile(r"^\s*(sim|s|yes|y)[\s,:-]+(\d{4})\s*[.!]?\s*$", re.I)
PENDING = "pending_approval.json"
TTL_SECONDS = 15 * 60


def _pending_path(root):
    return root / core.STATE_DIR / PENDING


def _digest(code: str, salt: str, expires: float) -> str:
    # Deliberately slow, so trying all 10,000 codes against a copied file outlasts the code's 15 minutes.
    # The expiry is part of the input, so editing it in the file voids the code.
    return hashlib.pbkdf2_hmac("sha256", code.encode(), f"{salt}:{expires:.0f}".encode(), 400_000).hex()


def _snapshot(root, cfg) -> str:
    ap = root / core.approval_rel(cfg)
    text = ap.read_text(encoding="utf-8") if ap.is_file() else ""
    spec = root / core.spec_rel(cfg)
    stext = spec.read_text(encoding="utf-8") if spec.is_file() else ""
    blob = json.dumps([text, stext, core.measurement_fingerprint(root, cfg)], sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


def _context(msg: str) -> int:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": msg}}))
    return 0


def _show_person(msg: str, extra: dict = None) -> int:
    out = {"decision": "block", "reason": msg,
           "hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "suppressOriginalPrompt": True}}
    if extra:
        out.update(extra)
    print(json.dumps(out))
    return 0


def _ledger_tip(root) -> str:
    led = core.read_ledger(root)
    return led[-1]["hash"] if led else ""


def _new_code(root, kind: str, snapshot: str) -> str:
    code = f"{secrets.randbelow(10000):04d}"
    salt = secrets.token_hex(8)
    p = _pending_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    core.exclude_local(root)
    expires = round(time.time() + TTL_SECONDS)
    core.write_file(p, json.dumps({"kind": kind, "salt": salt, "digest": _digest(code, salt, expires),
                                   "expires": expires, "snapshot": snapshot}))
    return code


def _ask_unlock(root, cfg, pt) -> int:
    code = _new_code(root, "unfreeze", _ledger_tip(root))
    if pt:
        msg = (f"honestlab: PARA DESTRANCAR, ENVIE  sim {code}   (leia antes)\n\n"
               "Destrancar deixa o agente mudar de novo a pergunta, a medida, os dados ou a regra de sucesso.\n"
               "- As tentativas feitas até agora continuam no histórico. Nada é apagado.\n"
               "- A medição inicial é refeita, e você vai precisar aprovar a página de novo.\n"
               "- Só destranque se o agente explicou o motivo e você concorda com ele.\n\n"
               f"Para destrancar, envie exatamente:  sim {code}\n"
               "(O código vale 15 minutos e o agente não o vê.) Para não destrancar, só continue a conversa.")
    else:
        msg = (f"honestlab: TO UNLOCK, SEND  yes {code}   (read this first)\n\n"
               "Unlocking lets the agent change the question, the measure, the data or the success rule again.\n"
               "- The attempts made so far stay in the history. Nothing is deleted.\n"
               "- The starting measurement is redone, and you will need to approve the page again.\n"
               "- Only unlock if the agent explained why and you agree.\n\n"
               f"To unlock, send exactly:  yes {code}\n"
               "(The code is valid for 15 minutes and the agent cannot see it.) To not unlock, just keep talking.")
    return _show_person(msg)


def _confirm_unlock(root, cfg, st, pt, payload, prompt) -> int:
    from .cli import unfreeze_unlock
    if not st.get("frozen"):
        return _show_person("O laboratório já está destrancado." if pt else "The lab is already unlocked.")
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf), core.lab_lock(root):
            unfreeze_unlock(root, cfg, st, "chat", evidence={
                "transcript_path": payload.get("transcript_path"),
                "session_id": payload.get("session_id"),
                "prompt_sha256": hashlib.sha256(prompt.strip().encode()).hexdigest()})
    except LabError as e:
        return _show_person(("Não foi possível destrancar: " if pt else "Could not unlock: ") + str(e))
    note = ("honestlab: the person unlocked the lab in the chat. Past experiments stay in the ledger. Make only the "
            "change you explained to the person, run `honestlab baseline` again, update the approval page, show it, "
            "and ask the person to type " + ("'aprovar'. Reply in Portuguese." if pt else "'approve'."))
    print(json.dumps({"systemMessage": "Destrancado pelo honestlab." if pt else "Unlocked by honestlab.",
                      "hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": note}}))
    return 0


def _stop_overnight(payload: dict) -> int:
    """The person typed 'parar'/'stop': end overnight mode, so the stop hook lets the agent stop."""
    root = core.find_root(payload.get("cwd")) or core.find_root()
    if root is None:
        return 0
    try:
        local = core.load_local(root)
    except (OSError, ValueError):
        return 0
    if not isinstance(local.get("overnight"), dict):
        return 0
    local.pop("overnight")
    core.save_local(root, local)
    return _context("honestlab: the person ended overnight mode. Finish or revert the current change (measure it "
                    "with `honestlab run` or undo it), then stop the loop and give the person a short summary "
                    "in plain words: best result, compared with the known methods, and what comes next.")


def handle(payload: dict) -> int:
    prompt = payload.get("prompt") or ""
    asks = APPROVE_RE.match(prompt)
    unlock = UNLOCK_RE.match(prompt)
    confirms = CONFIRM_RE.match(prompt)
    if STOP_RE.match(prompt):
        return _stop_overnight(payload)
    if not (asks or unlock or confirms):
        return 0
    root = core.find_root(payload.get("cwd")) or core.find_root()
    if root is None:
        return 0
    cfg, st = core.load_config(root), core.load_state(root)
    pt = core.is_pt(cfg)
    if unlock:
        return _ask_unlock(root, cfg, pt) if st.get("frozen") else 0
    if asks and st.get("frozen"):
        return 0
    from .cli import freeze_preflight, freeze_lock  # late import: cli imports this module lazily too

    if asks:
        try:
            freeze_preflight(root, cfg, st)
        except LabError as e:
            return _context(
                "honestlab: the person typed 'approve', but the lab cannot be approved yet: "
                f"{e}. Fix this, show the person the approval page again, and ask them to type "
                + ("'aprovar'." if pt else "'approve'."))
        code = _new_code(root, "approve", _snapshot(root, cfg))
        page = (root / core.approval_rel(cfg)).read_text(encoding="utf-8").strip()
        if pt:
            msg = (f"honestlab: PARA APROVAR, ENVIE  sim {code}   (leia a página abaixo antes)\n\n"
                   f"{page}\n\n---\nEsta é a página real, lida do arquivo pelo honestlab (não pelo agente).\n"
                   "Ao aprovar, a pergunta, a medida, os dados e a regra de sucesso ficam trancados; "
                   "o agente não poderá mudá-los depois.\n\n"
                   f"Para aprovar, envie exatamente:  sim {code}\n"
                   "(O código vale 15 minutos e o agente não o vê.) Para não aprovar, só continue a conversa.")
        else:
            msg = (f"honestlab: TO APPROVE, SEND  yes {code}   (read the page below first)\n\n"
                   f"{page}\n\n---\nThis is the real page, read from the file by honestlab (not by the agent).\n"
                   "Approving locks the question, the measure, the data and the success rule; "
                   "the agent cannot change them afterwards.\n\n"
                   f"To approve, send exactly:  yes {code}\n"
                   "(The code is valid for 15 minutes and the agent cannot see it.) To not approve, just keep talking.")
        return _show_person(msg)

    # confirmation
    p = _pending_path(root)
    try:
        pend = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return 0  # "sim 1234" with nothing pending is an ordinary message
    code = confirms.group(2)
    if time.time() > pend.get("expires", 0):
        p.unlink(missing_ok=True)
        return _show_person("O código expirou. Envie 'aprovar' de novo." if pt
                            else "The code expired. Send 'approve' again.")
    if _digest(code, pend.get("salt", ""), float(pend.get("expires", 0))) != pend.get("digest"):
        return _show_person("Código errado. Confira o código na mensagem de aprovação." if pt
                            else "Wrong code. Check the code in the approval message.")
    if pend.get("kind") == "unfreeze":
        if _ledger_tip(root) != pend.get("snapshot"):
            p.unlink()
            return _show_person("O laboratório mudou depois do pedido. Envie 'destrancar' de novo." if pt else
                                "The lab changed after the request. Send 'unlock' again.")
        p.unlink()
        return _confirm_unlock(root, cfg, st, pt, payload, prompt)
    if st.get("frozen"):
        p.unlink()
        return 0
    if _snapshot(root, cfg) != pend.get("snapshot"):
        p.unlink()
        return _show_person("A página ou o que é medido mudou depois que você a viu. Envie 'aprovar' de novo "
                            "para ver a versão atual." if pt else
                            "The page or what is measured changed after you saw it. Send 'approve' again "
                            "to see the current version.")
    p.unlink()
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf), core.lab_lock(root):
            freeze_preflight(root, cfg, st)
            n = freeze_lock(root, cfg, st, "chat", evidence={
                "transcript_path": payload.get("transcript_path"),
                "session_id": payload.get("session_id"),
                "prompt_sha256": hashlib.sha256(prompt.strip().encode()).hexdigest()})
    except LabError as e:
        return _show_person(("Não foi possível trancar: " if pt else "Could not lock: ") + str(e))
    note = (f"honestlab: the person approved in the chat. The lab is frozen ({n} protected files are "
            "hash-locked and read-only). Tell the person in one sentence that it is approved and locked, "
            "then continue with the experiments (phase 4 of the honestlab skill). "
            + ("The person speaks Portuguese: reply in Portuguese." if pt else "Reply in the person's language."))
    print(json.dumps({"systemMessage": ("Aprovado e trancado pelo honestlab." if pt else
                                        "Approved and locked by honestlab."),
                      "hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": note}}))
    return 0
