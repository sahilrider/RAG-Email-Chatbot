import os
from tqdm import tqdm
import json
import base64
import logging
from openai import OpenAI
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/gmail_fetcher.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MailClient:
    """A class to handle Gmail API operations and email processing."""
    
    # Gmail API Scope - Required for read-only access to Gmail messages
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    
    def __init__(self):
        """Initialize Mail instance with Gmail service."""
        self.service = self._get_gmail_service()
    
    def _get_gmail_service(self):
        """
        Authenticate and create Gmail API service.
        
        Returns:
            service: Authenticated Gmail API service object
        
        This method handles the OAuth2 authentication flow:
        1. Checks for existing credentials in token.json
        2. Refreshes expired credentials if possible
        3. Initiates new authentication flow if needed
        """
        logger.info("Initializing Gmail service authentication")
        creds = None
        
        # Load existing credentials if available
        if os.path.exists('token.json'):
            logger.debug("Found existing token.json file")
            creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)

        # Handle credential validation and refresh
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired credentials")
                creds.refresh(Request())
            else:
                logger.info("Initiating new authentication flow")
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for future use
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
                logger.debug("Saved new credentials to token.json")

        logger.info("Gmail service authentication successful")
        return build('gmail', 'v1', credentials=creds)
    
    def get_emails(self, query='category:primary'):
        """
        Fetch emails from Gmail using the provided query.
        
        Args:
            query: Gmail search query string (default: 'category:primary')
        
        Returns:
            list: List of dictionaries containing email data
        """
        logger.info(f"Starting email fetch with query: {query}")
        
        # Fetch message IDs matching the query
        results = self.service.users().messages().list(userId='me', q=query, maxResults=500).execute()
        messages = []
        
        # Handle pagination to get all messages
        while 'messages' in results:
            messages.extend(results['messages'])
            if 'nextPageToken' in results:
                logger.debug(f"Fetching next page of messages. Current count: {len(messages)}")
                results = self.service.users().messages().list(
                    userId='me', 
                    q=query, 
                    maxResults=500, 
                    pageToken=results['nextPageToken']
                ).execute()
            else:
                break

        logger.info(f"Found {len(messages)} messages to process")
        
        email_data = []
        for msg in tqdm(messages, desc="Processing emails"):
            try:
                msg_id = msg['id']
                message = self.service.users().messages().get(userId='me', id=msg_id).execute()
                payload = message['payload']

                # Extract email headers
                headers = payload['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')

                # Extract email body
                if 'parts' in payload and 'data' in payload['parts'][0]['body']:
                    data = payload['parts'][0]['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                else:
                    body = payload.get('body', {}).get('data', '')
                    if body:
                        body = base64.urlsafe_b64decode(body).decode('utf-8')
                    else:
                        body = 'No Body Found'
                        logger.warning(f"No body content found for message ID: {msg_id}, Skipping...")
                        continue

                # Combine email components
                email_text = f"From: {sender}\nSubject: {subject}\nBody: {body}"

                email_data.append({
                    'id': msg_id,
                    'subject': subject,
                    'sender': sender,
                    'body': body,
                    'text': email_text
                })
                
            except Exception as e:
                logger.error(f"Error processing message ID {msg_id}: {str(e)}")
                continue

        logger.info(f"Successfully processed {len(email_data)} emails")
        return email_data

# if __name__ == "__main__":
#     try:
#         # Get Gmail data
#         logger.info("Starting Gmail data extraction")
#         mail = MailClient()
#         emails = mail.get_emails(query="category:primary")
#         logger.info(f"Total emails processed: {len(emails)}")
#         if emails:
#             logger.info(f"Sample of last email processed: {emails[-1]}")
#     except Exception as e:
#         logger.error(f"Application error: {str(e)}")