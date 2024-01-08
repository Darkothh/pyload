import os
import io
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import subprocess

SCOPES_DRIVE = ["https://www.googleapis.com/auth/drive"]

def download_files(folder_id, creds):
    try:
        service = build("drive", "v3", credentials=creds)
        results = (
            service.files()
            .list(
                q=f"'{folder_id}' in parents",
                pageSize=100,
                fields="nextPageToken, files(id, name, mimeType)",
            )
            .execute()
        )
        items = results.get("files", [])

        if not items:
            print(f"No se encontraron archivos en la carpeta con el ID: {folder_id}")
            return

        download_folder = "datos"
        os.makedirs(download_folder, exist_ok=True)

        print("Descargando archivos en la carpeta 'datos':")
        for item in items:
            file_id = item["id"]
            file_name = item["name"]
            file_mime_type = item["mimeType"]
            if file_mime_type == "text/plain" or file_mime_type == "text/csv":
                download_file(service, file_id, file_name, download_folder)

    except HttpError as error:
        print(f"Ocurrio un error: {error}")

    call_second_program()


def call_second_program():
    print("Ejecutando el segundo programa...")
    subprocess.run(["python", "sheets.py"])


def download_file(service, file_id, file_name, download_folder):
    request = service.files().get_media(fileId=file_id)
    file_path = os.path.join(download_folder, file_name)

    with open(file_path, "wb") as file:
        downloader = io.FileIO(file_path, "wb")
        downloader.write(request.execute())
    print(f"Archivo '{file_name}' descargado en: '{download_folder}'")

def get_folder_id():
    folder_id = input("Ingresa el folder_id de Google Drive: ")
    with open("folder_id.txt", "w") as file:
        file.write(folder_id)
    return folder_id

def get_sheets_id():
    sheets_id = input("Ingresa el folder_id de la hoja de Google Sheets: ")
    with open("sheets_id.txt", "w") as file:
        file.write(sheets_id)
    return sheets_id

def main():
    creds = None

    if os.path.exists("token_leer.json"):
        creds = Credentials.from_authorized_user_file("token_leer.json", SCOPES_DRIVE)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES_DRIVE
            )
            creds = flow.run_local_server(port=0)
        with open("token_leer.json", "w") as token:
            token.write(creds.to_json())

    try:
        with open("folder_id.txt", "r") as file:
            folder_id = file.read().strip()
            print("ID de la carpeta de Google Drive:", folder_id)
    except FileNotFoundError:
        print("No se encontro ID de Google drive...")
        folder_id = get_folder_id()
    try:
        with open("sheets_id.txt", "r") as file:
            sheets_id = file.read().strip()
            print("ID de Google Sheets:", sheets_id)
    except FileNotFoundError:
        print("no se encontro ID de Google Sheets...")
        sheets_id = get_sheets_id()
    download_files(folder_id, creds)

if __name__ == "__main__":
    main()
