"""
THÉRÈSE v2 - Google Sheets Service

Client for Google Sheets API operations.
Used for CRM sync from Google Sheets.
"""

import logging

import httpx
from app.services.http_client import get_http_client
from fastapi import HTTPException

logger = logging.getLogger(__name__)


# ============================================================
# Google Sheets API Constants
# ============================================================


SHEETS_API_BASE = "https://sheets.googleapis.com/v4/spreadsheets"


# ============================================================
# Google Sheets Service
# ============================================================


class GoogleSheetsService:
    """
    Google Sheets API client.

    Handles reading data from Google Sheets.
    Supports both OAuth tokens and API keys.
    """

    def __init__(self, access_token: str | None = None, api_key: str | None = None):
        """
        Initialize Sheets service.

        Args:
            access_token: Valid OAuth access token with Sheets scope
            api_key: Google API key (for public/shared spreadsheets)

        Note: At least one of access_token or api_key must be provided.
        """
        self.access_token = access_token
        self.api_key = api_key
        self.headers = {'Accept': 'application/json'}

        if access_token:
            self.headers['Authorization'] = f'Bearer {access_token}'

        if not access_token and not api_key:
            raise ValueError("Either access_token or api_key must be provided")

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict | None = None,
        json_body: dict | None = None,
    ) -> dict:
        """Make authenticated request to Sheets API."""
        url = f"{SHEETS_API_BASE}/{endpoint}"

        # Add API key to params if using API key auth
        if params is None:
            params = {}
        if self.api_key and not self.access_token:
            params['key'] = self.api_key

        client = await get_http_client()
        try:
            kwargs: dict = {
                "headers": self.headers,
                "params": params,
                "timeout": 30.0,
            }
            if json_body is not None:
                kwargs["json"] = json_body

            response = await client.request(method, url, **kwargs)

            if response.status_code == 401:
                logger.error("Sheets API: Access token expired or invalid")
                raise HTTPException(
                    status_code=401,
                    detail="Google Sheets access token expired. Please reconnect."
                )

            if response.status_code == 403:
                logger.error("Sheets API: Permission denied")
                raise HTTPException(
                    status_code=403,
                    detail="Permission denied. Make sure the spreadsheet is shared with your Google account."
                )

            if response.status_code == 404:
                logger.error("Sheets API: Spreadsheet not found")
                raise HTTPException(
                    status_code=404,
                    detail="Spreadsheet not found. Check the spreadsheet ID."
                )

            if response.status_code not in (200, 201):
                logger.error(f"Sheets API error: {response.status_code} {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Google Sheets API error: {response.text}"
                )

            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling Sheets API: {e}")
            raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")

    async def get_spreadsheet_info(self, spreadsheet_id: str) -> dict:
        """
        Get spreadsheet metadata (title, sheets list).

        Args:
            spreadsheet_id: The spreadsheet ID from URL

        Returns:
            Spreadsheet metadata including sheets list
        """
        return await self._request("GET", spreadsheet_id, params={"fields": "properties,sheets.properties"})

    async def get_sheet_data(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        range_notation: str | None = None,
    ) -> list[list[str]]:
        """
        Get data from a specific sheet.

        Args:
            spreadsheet_id: The spreadsheet ID
            sheet_name: Name of the sheet (tab)
            range_notation: Optional A1 notation (e.g., "A1:Z100")

        Returns:
            List of rows (each row is a list of cell values)
        """
        if range_notation:
            range_str = f"{sheet_name}!{range_notation}"
        else:
            range_str = sheet_name

        endpoint = f"{spreadsheet_id}/values/{range_str}"
        result = await self._request("GET", endpoint)

        return result.get("values", [])

    async def get_all_data_as_dicts(
        self,
        spreadsheet_id: str,
        sheet_name: str,
    ) -> list[dict]:
        """
        Get all data from a sheet as list of dictionaries.

        First row is used as headers (keys).

        Args:
            spreadsheet_id: The spreadsheet ID
            sheet_name: Name of the sheet

        Returns:
            List of dictionaries with header keys
        """
        rows = await self.get_sheet_data(spreadsheet_id, sheet_name)

        if not rows or len(rows) < 2:
            return []

        headers = rows[0]
        data = []

        for row in rows[1:]:
            # Pad row to match headers length
            padded_row = row + [""] * (len(headers) - len(row))
            row_dict = {headers[i]: padded_row[i] for i in range(len(headers))}
            data.append(row_dict)

        return data

    async def create_spreadsheet(self, title: str, sheets: list[dict]) -> dict:
        """
        Crée un nouveau spreadsheet avec les onglets spécifiés.

        Args:
            title: Titre du spreadsheet
            sheets: Liste de dicts avec 'title' (nom de l'onglet) et 'headers' (liste des colonnes)

        Returns:
            Réponse API avec spreadsheetId et spreadsheetUrl
        """
        body = {
            "properties": {"title": title},
            "sheets": [
                {
                    "properties": {"title": s["title"], "index": i},
                    "data": [
                        {
                            "startRow": 0,
                            "startColumn": 0,
                            "rowData": [
                                {
                                    "values": [
                                        {"userEnteredValue": {"stringValue": h}}
                                        for h in s["headers"]
                                    ]
                                }
                            ],
                        }
                    ],
                }
                for i, s in enumerate(sheets)
            ],
        }

        client = await get_http_client()
        response = await client.post(
            SHEETS_API_BASE,
            headers=self.headers,
            json=body,
            timeout=30.0,
        )

        if response.status_code not in (200, 201):
            logger.error(f"Sheets API create error: {response.status_code} {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Impossible de créer le spreadsheet : {response.text}",
            )

        return response.json()

    async def append_row(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        values: list[str],
    ) -> dict:
        """
        Append a row to a sheet.

        Args:
            spreadsheet_id: The spreadsheet ID
            sheet_name: Name of the sheet (tab)
            values: List of cell values for the new row

        Returns:
            API response with updated range info
        """
        endpoint = f"{spreadsheet_id}/values/{sheet_name}:append"
        body = {
            "values": [values],
        }
        return await self._request(
            "POST",
            endpoint,
            params={"valueInputOption": "USER_ENTERED", "insertDataOption": "INSERT_ROWS"},
            json_body=body,
        )
