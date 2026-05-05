from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

creds = Credentials.from_service_account_file(
    "google_creds.json",
    scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
)
service = build("sheets", "v4", credentials=creds)

# ID CORRETO que você enviou
SPREADSHEET_ID = "1QxdoXoWCMyv-j-G6WAy6Ji5OClsp8NkU1cCfTdEZD9g"

try:
    spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    print(f"✅ SUCESSO! Planilha: {spreadsheet.get('properties', {}).get('title')}")
    print(f"📋 Abas: {[s['properties']['title'] for s in spreadsheet.get('sheets', [])]}")
except Exception as e:
    print(f"❌ Erro: {e}")