"""Google Sheets integration for application tracking."""

from core.config import settings
from core.logging_config import get_logger

logger = get_logger("services.google_sheets")


def append_application_to_sheet(record: dict) -> dict[str, str | bool]:
    if not settings.google_sheets_id or not settings.google_service_account_path:
        return {
            "saved": False,
            "message": "Google Sheets is not configured.",
        }

    try:
        import gspread

        client = gspread.service_account(filename=settings.google_service_account_path)
        sheet = client.open_by_key(settings.google_sheets_id).sheet1
        sheet.append_row(
            [
                record.get("company", ""),
                record.get("role", ""),
                record.get("application_date", ""),
                record.get("status", ""),
                record.get("generated_email", ""),
                record.get("generated_cover_letter", ""),
            ],
            value_input_option="USER_ENTERED",
        )
        return {"saved": True, "message": "Saved to Google Sheets."}
    except Exception as exc:
        logger.warning("Google Sheets append failed: %s", exc)
        return {"saved": False, "message": f"Google Sheets append failed: {exc}"}