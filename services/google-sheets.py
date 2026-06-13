"""
ТЗ 9.0: Google Sheets API-мен нақты уақыт режимінде асинхронды синхронизациялау.
Деректердің қауіпсіз әрі жоғалмай жазылуын қамтамасыз етеді.
"""
from datetime import datetime
import gspread_asyncio
from google.oauth2.service_account import Credentials
from config.settings import settings

def get_creds():
    # Google Cloud Console-дан жүктелген service_account.json файлының жолы
    # Нақты өндірісте (production) бұл файл жоба түбірінде орналасуы керек
    creds = Credentials.from_service_account_file("service_account.json")
    scoped = creds.with_scopes([
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ])
    return scoped

# Асинхронды клиент менеджерін құру
agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)

class GoogleSheetsService:
    def __init__(self):
        self.sheet_id = settings.GOOGLE_SHEET_ID

    async def _get_worksheet(self, sheet_name: str):
        """Лист атауы бойынша жұмыс парағын асинхронды алу"""
        agc = await agcm.authorize()
        spreadsheet = await agc.open_by_key(self.sheet_id)
        try:
            return await spreadsheet.worksheet(sheet_name)
        except Exception:
            # Егер лист жоқ болса, қателікті өңдеу немесе жаңадан құру логикасы
            return await spreadsheet.add_worksheet(title=sheet_name, rows="1000", cols="20")

    async def sync_applicant(self, data: dict, status: str = "Новый"):
        """ТЗ 9.2: 1. Кандидаты (Applicants) листіне жаңа жол қосу немесе жаңарту"""
        sheet = await self._get_worksheet("Applicants")
        row_data = [
            data.get("id", "-"),
            data.get("name", "-"),
            data.get("age", "-"),
            data.get("city", "-"),
            data.get("position", "-"),
            data.get("experience", "-"),
            data.get("salary", "-"),
            data.get("schedule", "-"),
            data.get("contact", "-"),
            status,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]
        await sheet.append_row(row_data)

    async def sync_vacancy(self, data: dict, status: str = "Активна"):
        """ТЗ 9.2: 3. Вакансии (Vacancies) листіне жаңа жол қосу"""
        sheet = await self._get_worksheet("Vacancies")
        row_data = [
            data.get("id", "-"),
            data.get("company_name", "-"),
            data.get("position", "-"),
            data.get("salary", "-"),
            data.get("schedule", "-"),
            data.get("address", "-"),
            data.get("requirements", "-"),
            status,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]
        await sheet.append_row(row_data)

    async def sync_interview(self, cand_name: str, vacancy_title: str, company: str, date_str: str, time_str: str, status: str = "Приглашен"):
        """ТЗ 9.2: 4. Собеседования (Interviews) листіне жазба енгізу"""
        sheet = await self._get_worksheet("Interviews")
        row_data = [
            f"INT-{int(datetime.timestamp(datetime.now()))}", # Бірегей ID
            cand_name,
            vacancy_title,
            company,
            date_str,
            time_str,
            status
        ]
        await sheet.append_row(row_data)

# Сервистің жаһандық объектісі
sheets_sync = GoogleSheetsService()