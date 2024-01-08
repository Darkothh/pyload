from __future__ import print_function
import os
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def readText(file_path):
    items = []
    with open(file_path, 'r') as f:
        lines = f.readlines()
        for item in lines:
            items.append([item.replace('\n', '')])
    # print(items)
    return items
def send_to_sheets(creds, spreadsheet_id, sheet_name, values):
    try:
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()
        sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = sheet_metadata.get('sheets', [])

        sheet_id = None

        for s in sheets:
            if s['properties']['title'] == sheet_name:
                sheet_id = s['properties']['sheetId']
                break

        if not sheet_id:
            new_sheet = sheet.batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': [{'addSheet': {'properties': {'title': sheet_name}}}]},
            ).execute()
            sheet_id = new_sheet['replies'][0]['addSheet']['properties']['sheetId']
            print("Se ha creado una nueva hoja", sheet_name)

        range_name = f"{sheet_name}!A1"
        result = sheet.values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            body={"values": values}
        ).execute()

        print(f"Datos enviados correctamente a Google Sheets en la hoja: '{sheet_name}'")
    except HttpError as err:
        print(err)

def get_sheets_id():
    sheets_id = input("Ingresa el folder_id de la hoja de Google Sheets: ")
    with open("sheets_id.txt", "w") as file:
        file.write(sheets_id)
    return sheets_id

def get_credentials(token_file, scopes):
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", scopes
            )
            creds = flow.run_local_server(port=0)
        with open(token_file, "w") as token:
            token.write(creds.to_json())
    return creds



def main():
    # Obtener credenciales para Google Sheets
    creds_sheets = get_credentials("token_s.json", SCOPES)

    # Intenta cargar el spreadsheet_id desde el archivo
    try:
        with open("sheets_id.txt", "r") as file:
            spreadsheet_id = file.read().strip()
    except FileNotFoundError:
        # Si el archivo no existe, pide al usuario que ingrese el spreadsheet_id
        spreadsheet_id = get_sheets_id()

    folder_path = 'datos'
    file_list = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

    for file_name in file_list:
        sheet_name = os.path.splitext(file_name)[0]
        file_path = os.path.join(folder_path, file_name)
        value_data = readText(file_path)
        send_to_sheets(creds_sheets, spreadsheet_id, sheet_name, value_data)


if __name__ == '__main__':
    main()
