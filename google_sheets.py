import gspread
from oauth2client.service_account import ServiceAccountCredentials

def authenticate_gsheets(credentials_json):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_json, scope)
    client = gspread.authorize(creds)
    return client

def get_sheet_data(sheet_url):
    client = authenticate_gsheets('credentials_sheets.json')
    sheet = client.open_by_url(sheet_url).sheet1
    data = sheet.get_all_records()
    return data

def update_sheet_with_certificate_link(sheet_url, row_index, link):
    client = authenticate_gsheets('credentials_sheets.json')
    sheet = client.open_by_url(sheet_url).sheet1
    sheet.update_cell(row_index, 6, link)  # Assuming 6th column is for certificate links
