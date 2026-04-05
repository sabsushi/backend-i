from datetime import date
import logging
from pathlib import Path
import sys
from typing import Callable

import typer

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core import NotFoundError, ValidationError, configure_logging, get_meeting_service
from app.core.validators import parse_iso_date
from app.domain import ActionItem, Meeting, MeetingReport


app = typer.Typer(help="Meeting Note Assistant CLI")
VALIDATION_EXIT_CODE = 2
NOT_FOUND_EXIT_CODE = 1
logger = logging.getLogger("meeting_note_assistant.cli")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    configure_logging()
    if ctx.invoked_subcommand is None:
        typer.echo("Meeting Note Assistant is ready.")


def _format_meeting(meeting: Meeting) -> str:
    lines = [
        f"ID: {meeting.id}",
        f"Title: {meeting.title}",
        f"Date: {meeting.date.isoformat()}",
        f"Owner: {meeting.owner}",
        f"Participants: {', '.join(meeting.participants) if meeting.participants else 'None'}",
        f"Action items: {len(meeting.action_items)}",
    ]
    if meeting.action_items:
        for index, action_item in enumerate(meeting.action_items, start=1):
            due_date = action_item.due_date.isoformat() if action_item.due_date else "None"
            lines.append(
                f"  {index}. {action_item.description} | owner={action_item.owner} | due={due_date} | done={action_item.is_done}"
            )
    return "\n".join(lines)


def _prompt_required_text(label: str) -> str:
    while True:
        value = typer.prompt(label).strip()
        if value:
            return value
        typer.echo("Value cannot be empty.")


def _format_report(report: MeetingReport) -> str:
    open_action_items = report.total_action_items - report.completed_action_items
    return "\n".join(
        [
            "CLI checkpoint summary",
            f"Total meetings: {report.total_meetings}",
            f"Total participants: {report.total_participants}",
            f"Total action items: {report.total_action_items}",
            f"Completed action items: {report.completed_action_items}",
            f"Open action items: {open_action_items}",
        ]
    )


def _resolve_text_option(value: str | None, label: str) -> str:
    if value is None:
        return _prompt_required_text(label)

    cleaned = value.strip()
    if cleaned:
        return cleaned

    raise typer.BadParameter(f"{label} cannot be empty.")


def _resolve_date_option(value: str | None) -> date:
    if value is not None:
        try:
            return parse_iso_date(value.strip())
        except ValidationError as exc:
            raise typer.BadParameter(str(exc)) from exc

    while True:
        typed_value = typer.prompt("Meeting date (YYYY-MM-DD)").strip()
        try:
            return parse_iso_date(typed_value)
        except ValidationError as exc:
            typer.echo(str(exc))


def _resolve_participants(values: list[str] | None, *, prompt_for_value: bool) -> list[str]:
    if values is not None:
        return values
    if not prompt_for_value:
        return []

    typed_value = typer.prompt(
        "Participants (comma-separated, leave blank for none)",
        default="",
        show_default=False,
    ).strip()
    if not typed_value:
        return []
    return [item.strip() for item in typed_value.split(",")]


def _build_action_items(
    descriptions: list[str] | None,
    owners: list[str] | None,
    due_dates: list[str] | None,
    *,
    prompt_for_value: bool,
) -> list[ActionItem]:
    if descriptions is None and owners is None and due_dates is None and prompt_for_value:
        return _prompt_action_items()

    description_list = descriptions or []
    owner_list = owners or []
    due_date_list = due_dates or []

    if not description_list and not owner_list and not due_date_list:
        return []

    if len(owner_list) != len(description_list):
        raise ValidationError("Each action item must include a matching owner.")
    if due_date_list and len(due_date_list) != len(description_list):
        raise ValidationError("Action item due dates must match the number of action items.")

    action_items: list[ActionItem] = []
    for index, description in enumerate(description_list):
        due_date = parse_iso_date(due_date_list[index]) if due_date_list else None
        action_items.append(
            ActionItem(
                description=description,
                owner=owner_list[index],
                due_date=due_date,
            )
        )
    return action_items


def _prompt_action_items() -> list[ActionItem]:
    action_items: list[ActionItem] = []
    while typer.confirm("Add an action item?", default=False):
        description = _prompt_required_text("Action item description")
        owner = _prompt_required_text("Action item owner")
        due_date_input = typer.prompt(
            "Action item due date (YYYY-MM-DD, leave blank for none)",
            default="",
            show_default=False,
        ).strip()
        due_date = parse_iso_date(due_date_input) if due_date_input else None
        action_items.append(
            ActionItem(description=description, owner=owner, due_date=due_date)
        )
    return action_items


def _run_with_cli_errors(operation: Callable[[], None]) -> None:
    try:
        operation()
    except ValidationError as exc:
        logger.error("Validation error in CLI flow: %s", exc)
        typer.echo(f"Validation error: {exc}")
        raise typer.Exit(code=VALIDATION_EXIT_CODE) from exc
    except NotFoundError as exc:
        logger.error("Not found error in CLI flow: %s", exc)
        typer.echo(str(exc))
        raise typer.Exit(code=NOT_FOUND_EXIT_CODE) from exc


@app.command("create-meeting")
def create_meeting(
    title: str | None = typer.Option(None, help="Meeting title."),
    meeting_date: str | None = typer.Option(None, "--date", help="Meeting date in ISO format."),
    owner: str | None = typer.Option(None, help="Meeting owner."),
    participants: list[str] | None = typer.Option(
        None,
        "--participant",
        help="Participant name. Repeat the option for multiple participants.",
    ),
    action_items: list[str] | None = typer.Option(
        None,
        "--action-item",
        help="Action item description. Repeat the option for multiple items.",
    ),
    action_item_owners: list[str] | None = typer.Option(
        None,
        "--action-owner",
        help="Action item owner. Repeat once per action item.",
    ),
    action_item_due_dates: list[str] | None = typer.Option(
        None,
        "--action-due-date",
        help="Action item due date in ISO format. Repeat once per action item.",
    ),
) -> None:
    def operation() -> None:
        interactive_optional_fields = (
            participants is None
            and action_items is None
            and action_item_owners is None
            and action_item_due_dates is None
            and title is None
            and meeting_date is None
            and owner is None
        )
        meeting = get_meeting_service().create_meeting(
            title=_resolve_text_option(title, "Meeting title"),
            meeting_date=_resolve_date_option(meeting_date),
            owner=_resolve_text_option(owner, "Meeting owner"),
            participants=_resolve_participants(
                participants,
                prompt_for_value=interactive_optional_fields,
            ),
            action_items=_build_action_items(
                action_items,
                action_item_owners,
                action_item_due_dates,
                prompt_for_value=interactive_optional_fields,
            ),
        )
        logger.info("Created meeting %s", meeting.id)
        typer.echo("Meeting created.")
        typer.echo(_format_meeting(meeting))

    _run_with_cli_errors(operation)


@app.command("list-meetings")
def list_meetings() -> None:
    meetings = get_meeting_service().list_meetings()
    logger.info("Listing meetings. count=%s", len(meetings))
    if not meetings:
        typer.echo("No meetings found.")
        raise typer.Exit()

    for index, meeting in enumerate(meetings):
        if index:
            typer.echo("")
        typer.echo(_format_meeting(meeting))


@app.command("show-meeting")
def show_meeting(
    meeting_id: str = typer.Option(..., "--id", help="Meeting identifier."),
) -> None:
    def operation() -> None:
        meeting = get_meeting_service().get_meeting(meeting_id)
        logger.info("Showing meeting %s", meeting.id)
        typer.echo(_format_meeting(meeting))

    _run_with_cli_errors(operation)


@app.command("delete-meeting")
def delete_meeting(
    meeting_id: str = typer.Option(..., "--id", help="Meeting identifier."),
) -> None:
    def operation() -> None:
        meeting = get_meeting_service().delete_meeting(meeting_id)
        logger.info("Deleted meeting %s", meeting.id)
        typer.echo(f"Deleted meeting: {meeting.id}")

    _run_with_cli_errors(operation)


@app.command("report-summary")
def report_summary() -> None:
    report = get_meeting_service().build_report()
    logger.info(
        "Generated summary report. meetings=%s action_items=%s",
        report.total_meetings,
        report.total_action_items,
    )
    typer.echo(_format_report(report))


if __name__ == "__main__":
    app()
