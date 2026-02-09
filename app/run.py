"""Main pipeline: ingress → redact → classify → draft (supported intents) → guardrails/eval."""

import argparse
import os
from pathlib import Path

from app.redact import load_patterns, redact
from app.classify import classify
from app.kb import load_kb
from app.draft import draft_from_policy
from app.guardrails import run_draft_checks
from app.mtl import DEFAULT_MODEL_DIR, MODEL_FILE

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Prompt
    from rich.table import Table
    from rich.theme import Theme

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Theme: OK green, FAIL red, dim for meta
CLI_THEME = Theme(
    {
        "ok": "green",
        "fail": "red",
        "dim": "dim",
        "info": "cyan",
    }
)
console = Console(theme=CLI_THEME) if RICH_AVAILABLE else None


def _status_style(ok: bool) -> str:
    if not RICH_AVAILABLE:
        return "OK" if ok else "FAIL"
    return "[ok]OK[/ok]" if ok else "[fail]FAIL[/fail]"


def run_pipeline(
    messages_path: Path,
    data_dir: Path,
    limit: int | None = 5,
) -> None:
    """
    Wire pipeline: redaction runs before any non-local model or external service.
    Ingress (messages.csv) → redact → classify → draft (for supported intents) → check.
    """
    import pandas as pd

    if not messages_path.exists():
        (console or __import__("builtins").print)(
            f"messages.csv not found at {messages_path}"
        )
        return
    df = pd.read_csv(messages_path)
    if limit:
        df = df.head(limit)
    pii_path = data_dir / "pii_patterns.yaml"
    kb = load_kb(data_dir / "kb")
    patterns = load_patterns(pii_path)
    model_path = Path(__file__).resolve().parent.parent / DEFAULT_MODEL_DIR / MODEL_FILE
    backend = "mtl" if model_path.exists() else "stub"
    use_llm = os.environ.get("USE_LLM", "").strip().lower() in ("1", "true", "yes")

    if RICH_AVAILABLE:
        console.print(
            Panel(
                f"[bold]Backend[/bold]: {backend}\n"
                f"[bold]Draft[/bold]: {'LLM (GPT-4o-mini)' if use_llm else 'template'}\n"
                f"[bold]Messages[/bold]: {len(df)} (redact → classify → draft → check)",
                title="[cyan]Intelligent message routing[/cyan]",
                border_style="cyan",
            )
        )
    else:
        print(
            f"Backend: {backend}. Draft: {'LLM' if use_llm else 'template'}. "
            f"Processed {len(df)} messages\n"
        )

    rows: list[dict] = []
    total = len(df)
    show_progress = RICH_AVAILABLE and total > 0

    def process_one(idx: int, row) -> None:
        msg_id = row.get("message_id", "")
        text = str(row.get("text", ""))
        redacted = redact(text, patterns)
        res = classify(
            redacted,
            messages_path,
            message_id=str(msg_id),
            backend=backend,
            model_path=model_path if backend == "mtl" else None,
        )
        draft, used_fallback = draft_from_policy(
            res, kb, use_llm=use_llm, redacted_message=redacted
        )
        ok, failures = run_draft_checks(draft)
        status = "OK" if ok else f"FAIL:{','.join(failures)}"
        conf = res.confidence if res.confidence is not None else 0.0
        draft_preview = (draft[:80] + "…") if len(draft) > 80 else draft
        rows.append(
            {
                "msg_id": str(msg_id),
                "intent": res.intent,
                "queue": res.suggested_queue,
                "confidence": conf,
                "fallback": used_fallback,
                "checks_ok": ok,
                "status": status,
                "draft_preview": draft_preview,
            }
        )

    if show_progress:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            task = progress.add_task("Processing messages…", total=total)
            for idx, (_, row) in enumerate(df.iterrows()):
                progress.update(
                    task, description=f"Message {idx + 1}/{total}", completed=idx
                )
                process_one(idx, row)
            progress.update(task, completed=total)
    else:
        for idx, (_, row) in enumerate(df.iterrows()):
            process_one(idx, row)

    if RICH_AVAILABLE:
        table = Table(show_header=True, header_style="bold cyan", border_style="dim")
        table.add_column("ID", style="dim", width=10)
        table.add_column("Intent", width=12)
        table.add_column("Queue", width=28)
        table.add_column("Conf", justify="right", width=5)
        table.add_column("Fallback", width=8)
        table.add_column("Checks", width=22)
        table.add_column("Draft preview", max_width=50, overflow="ellipsis")
        for r in rows:
            checks_cell = (
                _status_style(r["checks_ok"])
                if r["checks_ok"]
                else f'[fail]{r["status"]}[/fail]'
            )
            table.add_row(
                r["msg_id"],
                r["intent"],
                r["queue"],
                f"{r['confidence']:.2f}",
                str(r["fallback"]),
                checks_cell,
                r["draft_preview"],
            )
        console.print(table)
    else:
        sep = "─" * 72
        for r in rows:
            print(
                f"  {r['msg_id']} intent={r['intent']} queue={r['queue']} confidence={r['confidence']:.2f} fallback={r['fallback']} checks={r['status']}"
            )
            print(f"    draft: {r['draft_preview']}")
            print(sep)


def cmd_redact(text: str, data_dir: Path) -> None:
    """Redact only: input → redacted text (pretty output)."""
    pii_path = data_dir / "pii_patterns.yaml"
    patterns = load_patterns(pii_path)
    redacted = redact(text, patterns)
    if RICH_AVAILABLE:
        console.print(Panel(text, title="[cyan]Input[/cyan]", border_style="dim"))
        console.print(
            Panel(redacted, title="[green]Redacted[/green]", border_style="green")
        )
    else:
        print("Input:", text)
        print("Redacted:", redacted)


def cmd_predict(text: str, data_dir: Path, messages_path: Path) -> None:
    """Redact + classify only: input → intent, queue, confidence (pretty output)."""
    pii_path = data_dir / "pii_patterns.yaml"
    patterns = load_patterns(pii_path)
    model_path = Path(__file__).resolve().parent.parent / DEFAULT_MODEL_DIR / MODEL_FILE
    backend = "mtl" if model_path.exists() else "stub"
    redacted = redact(text, patterns)
    res = classify(
        redacted,
        messages_path,
        message_id=None,
        backend=backend,
        model_path=model_path if backend == "mtl" else None,
    )
    conf = res.confidence if res.confidence is not None else 0.0
    if RICH_AVAILABLE:
        console.print(Panel(text, title="[cyan]Input[/cyan]", border_style="dim"))
        console.print(Panel(redacted, title="[dim]Redacted[/dim]", border_style="dim"))
        result_lines = [
            f"[bold]Intent[/bold]: {res.intent}",
            f"[bold]Queue[/bold]: {res.suggested_queue}",
            f"[bold]Confidence[/bold]: {conf:.2f}",
            f"[bold]Backend[/bold]: {backend}",
        ]
        console.print(
            Panel(
                "\n".join(result_lines),
                title="[cyan]Prediction[/cyan]",
                border_style="cyan",
            )
        )
    else:
        print("Input:", text[:120], "..." if len(text) > 120 else "")
        print("Redacted:", redacted[:120], "..." if len(redacted) > 120 else "")
        print(
            f"Intent: {res.intent}  Queue: {res.suggested_queue}  Confidence: {conf:.2f}  Backend: {backend}"
        )


def run_single_message(text: str, data_dir: Path, messages_path: Path) -> None:
    """Run pipeline on one custom message (no message_id; classifier uses MTL or stub default)."""
    pii_path = data_dir / "pii_patterns.yaml"
    kb = load_kb(data_dir / "kb")
    patterns = load_patterns(pii_path)
    model_path = Path(__file__).resolve().parent.parent / DEFAULT_MODEL_DIR / MODEL_FILE
    backend = "mtl" if model_path.exists() else "stub"
    use_llm = os.environ.get("USE_LLM", "").strip().lower() in ("1", "true", "yes")

    redacted = redact(text, patterns)
    res = classify(
        redacted,
        messages_path,
        message_id=None,
        backend=backend,
        model_path=model_path if backend == "mtl" else None,
    )
    draft, used_fallback = draft_from_policy(
        res, kb, use_llm=use_llm, redacted_message=redacted
    )
    ok, failures = run_draft_checks(draft)
    status = "OK" if ok else f"FAIL:{','.join(failures)}"
    conf = res.confidence if res.confidence is not None else 0.0

    if RICH_AVAILABLE:
        header = (
            f"[bold]Backend[/bold]: {backend}  [bold]Draft[/bold]: "
            f"{'LLM (GPT-4o-mini)' if use_llm else 'template'}"
        )
        console.print(Panel(header, title="[cyan]Config[/cyan]", border_style="dim"))
        console.print(
            Panel(text, title="[cyan]Input Message[/cyan]", border_style="dim")
        )
        console.print(
            Panel(redacted, title="[cyan]Redaction[/cyan]", border_style="yellow")
        )
        checks_display = _status_style(ok) if ok else f"[fail]{status}[/fail]"
        result_lines = [
            f"[bold]Intent[/bold]: {res.intent}",
            f"[bold]Queue[/bold]: {res.suggested_queue}",
            f"[bold]Confidence[/bold]: {conf:.2f}",
            f"[bold]Fallback[/bold]: {used_fallback}",
            f"[bold]Checks[/bold]: {checks_display}",
        ]
        if use_llm and conf < 0.7:
            result_lines.append("[dim](LLM skipped: confidence < 0.7)[/dim]")
        console.print(
            Panel(
                "\n".join(result_lines),
                title="[cyan]Intent/Queue Prediction[/cyan]",
                border_style="cyan",
            )
        )
        console.print(Panel(draft, title="[cyan]Draft[/cyan]", border_style="green"))
    else:
        print(f"Backend: {backend}. Draft: {'LLM' if use_llm else 'template'}.\n")
        print(f"  Input message: {text[:120]}{'...' if len(text) > 120 else ''}\n")
        print(f"  Redaction: {redacted[:120]}{'...' if len(redacted) > 120 else ''}\n")
        print(
            f"  Intent/Queue Prediction: intent={res.intent}  queue={res.suggested_queue}  confidence={conf:.2f}  fallback={used_fallback}  checks={status}"
        )
        if use_llm and conf < 0.7:
            print("  (LLM skipped: confidence < 0.7)")
        print(f"  draft: {draft}")


def _get_message_from_args_or_prompt(
    args_message: str | None,
    prompt_enter_csv: bool = False,
) -> str:
    """Get message from positional arg, MSG env, or prompt. If prompt_enter_csv, prompt allows Enter for CSV run."""
    msg = (args_message or os.environ.get("MSG") or "").strip()
    if msg:
        return msg
    if prompt_enter_csv:
        prompt_text = (
            "[cyan]Enter message (or press Enter to run 5 from CSV)[/cyan]"
            if RICH_AVAILABLE
            else "Enter message (or press Enter to run 5 from CSV): "
        )
    else:
        prompt_text = (
            "[cyan]Enter message[/cyan]" if RICH_AVAILABLE else "Enter message: "
        )
    out = Prompt.ask(prompt_text, default="") if RICH_AVAILABLE else input(prompt_text)
    return (out or "").strip()


def main() -> None:
    base = Path(__file__).resolve().parent.parent
    data_dir_default = base / "assignment" / "data"

    p = argparse.ArgumentParser(
        description="Message routing pipeline (CLI). Use: app [run|redact|predict|draft] [message]",
    )
    p.add_argument(
        "--data-dir",
        type=Path,
        default=data_dir_default,
        help="Data directory (default: assignment/data)",
    )
    p.add_argument(
        "arg1",
        nargs="?",
        default=None,
        help="Command (run|redact|predict|draft) or message for run",
    )
    p.add_argument(
        "arg2",
        nargs="?",
        default=None,
        help="Message when first arg is a command",
    )
    args = p.parse_args()
    commands = ("run", "redact", "predict", "draft")
    if args.arg1 in commands:
        cmd, message_arg = args.arg1, args.arg2
    else:
        cmd, message_arg = "run", args.arg1
    data_dir = args.data_dir
    messages_path = data_dir / "messages.csv"

    if RICH_AVAILABLE:
        console.print("[bold cyan]Intelligent message routing[/bold cyan]")
        console.print(f"[dim]Data directory: {data_dir}[/dim]\n")
    else:
        print("Intelligent message routing")
        print(f"Data directory: {data_dir}\n")

    if cmd == "run":
        single_msg = _get_message_from_args_or_prompt(
            message_arg,
            prompt_enter_csv=True,
        )
        if single_msg:
            run_single_message(single_msg, data_dir, messages_path)
        else:
            run_pipeline(messages_path, data_dir, limit=5)
    elif cmd == "redact":
        msg = _get_message_from_args_or_prompt(message_arg)
        if msg:
            cmd_redact(msg, data_dir)
        else:
            (console or print)("No message provided.")
    elif cmd == "predict":
        msg = _get_message_from_args_or_prompt(message_arg)
        if msg:
            cmd_predict(msg, data_dir, messages_path)
        else:
            (console or print)("No message provided.")
    elif cmd == "draft":
        msg = _get_message_from_args_or_prompt(message_arg)
        if msg:
            run_single_message(msg, data_dir, messages_path)
        else:
            (console or print)("No message provided.")


if __name__ == "__main__":
    main()
