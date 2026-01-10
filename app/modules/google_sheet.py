"""
Google Sheets Integration Module

This module provides functionality to interact with Google Sheets using the Google Sheets API.
"""
import os
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle

logger = logging.getLogger(__name__)

# If modifying these scopes, delete the token.pickle file
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

class GoogleSheetIntegration:
    """
    A class to handle Google Sheets integration with various operations.
    
    This implementation uses the Google Sheets API v4.
    """
    
    def __init__(self, 
                 credentials_path: str = 'credentials.json',
                 token_path: str = 'token.pickle',
                 scopes: Optional[List[str]] = None):
        """
        Initialize the Google Sheets integration.
        
        Args:
            credentials_path: Path to the Google API credentials JSON file
            token_path: Path to save/load the authentication token
            scopes: List of Google API scopes to request
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.scopes = scopes or SCOPES
        self.creds = None
        self.service = None
        
        # Load or create credentials
        self._authenticate()
    
    def _authenticate(self) -> None:
        """Authenticate with Google Sheets API."""
        try:
            # The file token.pickle stores the user's access and refresh tokens
            if os.path.exists(self.token_path):
                with open(self.token_path, 'rb') as token:
                    self.creds = pickle.load(token)
            
            # If there are no (valid) credentials available, let the user log in
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_path):
                        raise FileNotFoundError(
                            f"Credentials file not found: {self.credentials_path}"
                        )
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, 
                        self.scopes
                    )
                    self.creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                with open(self.token_path, 'wb') as token:
                    pickle.dump(self.creds, token)
            
            # Build the service
            self.service = build('sheets', 'v4', credentials=self.creds)
            
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}", exc_info=True)
            raise
    
    def create_spreadsheet(self, title: str) -> Tuple[bool, str, Optional[str]]:
        """
        Create a new Google Spreadsheet.
        
        Args:
            title: Title of the new spreadsheet
            
        Returns:
            Tuple[bool, str, Optional[str]]: (success, message, spreadsheet_id)
        """
        try:
            spreadsheet = {
                'properties': {
                    'title': title
                }
            }
            
            spreadsheet = self.service.spreadsheets().create(
                body=spreadsheet,
                fields='spreadsheetId,spreadsheetUrl'
            ).execute()
            
            spreadsheet_id = spreadsheet.get('spreadsheetId')
            spreadsheet_url = spreadsheet.get('spreadsheetUrl')
            
            logger.info(f"Created new spreadsheet: {title} (ID: {spreadsheet_id})")
            return True, f"Successfully created spreadsheet: {title}", spreadsheet_id
            
        except Exception as e:
            error_msg = f"Failed to create spreadsheet: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg, None
    
    def append_data(self, 
                   spreadsheet_id: str, 
                   data: List[List[Any]], 
                   sheet_name: str = 'Sheet1',
                   value_input_option: str = 'RAW') -> Tuple[bool, str]:
        """
        Append data to a Google Sheet.
        
        Args:
            spreadsheet_id: The ID of the spreadsheet
            data: 2D list of data to append
            sheet_name: Name of the sheet to append to
            value_input_option: How the input data should be interpreted
                               ('RAW' or 'USER_ENTERED')
                               
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            if not self.service:
                raise RuntimeError("Google Sheets service not initialized")
            
            # Get the sheet ID from the sheet name
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            
            sheet_id = None
            for sheet in spreadsheet.get('sheets', []):
                if sheet['properties']['title'] == sheet_name:
                    sheet_id = sheet['properties']['sheetId']
                    break
            
            if sheet_id is None:
                # Create the sheet if it doesn't exist
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body={
                        'requests': [{
                            'addSheet': {
                                'properties': {
                                    'title': sheet_name
                                }
                            }
                        }]
                    }
                ).execute()
            
            # Append the data
            range_name = f"{sheet_name}!A1"
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                insertDataOption='INSERT_ROWS',
                body={
                    'values': data
                }
            ).execute()
            
            updates = result.get('updates', {})
            logger.info(f"Appended {updates.get('updatedCells', 0)} cells to {sheet_name}")
            
            return True, f"Successfully appended data to {sheet_name}"
            
        except HttpError as e:
            error_msg = f"Google Sheets API error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
        except Exception as e:
            error_msg = f"Failed to append data: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
    
    def read_data(self, 
                 spreadsheet_id: str, 
                 range_name: str = 'Sheet1') -> Tuple[bool, str, Optional[List[List[Any]]]]:
        """
        Read data from a Google Sheet.
        
        Args:
            spreadsheet_id: The ID of the spreadsheet
            range_name: A1 notation of the range to read (e.g., 'Sheet1!A1:C3')
            
        Returns:
            Tuple[bool, str, Optional[List[List[Any]]]]: 
                (success, message, data)
        """
        try:
            if not self.service:
                raise RuntimeError("Google Sheets service not initialized")
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                return True, "No data found", []
            
            return True, "Successfully retrieved data", values
            
        except HttpError as e:
            error_msg = f"Google Sheets API error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg, None
        except Exception as e:
            error_msg = f"Failed to read data: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg, None

# Example usage
if __name__ == "__main__":
    # Example with a service account
    sheets = GoogleSheetIntegration(
        credentials_path='path/to/credentials.json',
        token_path='token.pickle'
    )
    
    # Create a new spreadsheet
    success, message, spreadsheet_id = sheets.create_spreadsheet("Test Spreadsheet")
    if success:
        print(f"Created spreadsheet with ID: {spreadsheet_id}")
        
        # Append some data
        data = [
            ["Name", "Email", "Phone"],
            ["John Doe", "john@example.com", "123-456-7890"],
            ["Jane Smith", "jane@example.com", "098-765-4321"]
        ]
        
        success, message = sheets.append_data(spreadsheet_id, data, "Contacts")
        if success:
            print("Successfully added data")
            
            # Read the data back
            success, message, result = sheets.read_data(spreadsheet_id, "Contacts!A1:C3")
            if success:
                print("Data from sheet:")
                for row in result:
                    print(row)
    else:
        print(f"Error: {message}")
