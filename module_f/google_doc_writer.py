"""
F3 — Google Doc Writer
Uses Google Docs API to append pulse summary and fee explanation details
at the bottom of a specified Google Doc.
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

from models.schemas import PulsePayload, FeeExplainerResult

load_dotenv()
logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/documents"]

def _get_credentials():
    service_account_info = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not service_account_info:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON is not set in environment variables.")
    
    # Check if the variable contains raw JSON (starts with {) or is a file path
    if service_account_info.strip().startswith("{"):
        import json
        info = json.loads(service_account_info)
        return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    
    if not os.path.exists(service_account_info):
        raise ValueError(f"Service account file not found at path: {service_account_info}")
    
    return service_account.Credentials.from_service_account_file(
        service_account_info, scopes=SCOPES
    )

def append_to_doc(pulse: PulsePayload, fee_explainer: FeeExplainerResult = None) -> bool:
    """
    Appends the weekly pulse summary and fee explainer details to the configured Google Doc.
    Returns True on success, False otherwise.
    """
    doc_id = os.environ.get("GOOGLE_DOC_ID")
    if not doc_id:
        logger.error("GOOGLE_DOC_ID is not set in environment variables.")
        return False
        
    try:
        creds = _get_credentials()
        service = build("docs", "v1", credentials=creds)
        
        # 1. Get current document length to clear old data
        doc = service.documents().get(documentId=doc_id).execute()
        content = doc.get("body").get("content")
        end_index = content[-1].get("endIndex") - 1
        
        requests = []
        
        # Clear document if there is content
        if end_index > 1:
            requests.append({
                "deleteContentRange": {
                    "range": {
                        "startIndex": 1,
                        "endIndex": end_index
                    }
                }
            })
        
        # 2. Build the text block and track header indices for formatting
        date_str = pulse.metadata.get("generated_at", "").split(" ")[0]
        pulse_text = pulse.summary_note
        
        text_parts = []
        styles = []  # list of (start_idx, end_idx, style_name)
        
        def add_text(content, style=None):
            start = sum(len(p) for p in text_parts) + 1  # 1-indexed for body
            text_parts.append(content)
            end = sum(len(p) for p in text_parts) + 1
            if style:
                styles.append((start, end, style))

        # Add Titles and Content
        add_text("IndMoney Weekly Product Pulse\n", "HEADING_1")
        add_text(f"Date: {date_str}\n")
        IST = timezone(timedelta(hours=5, minutes=30))
        ist_now = datetime.now(IST)
        add_text(f"Last updated on {ist_now.strftime('%H:%M')} in IST\n\n")
        
        add_text("Summary\n", "HEADING_2")
        add_text(f"{pulse_text}\n\n")
        
        if fee_explainer:
            add_text(f"Fee Scenario: {fee_explainer.scenario}\n", "HEADING_2")
            for bullet in fee_explainer.bullets:
                add_text(f"• {bullet}\n")
            add_text("\n")
            
            add_text("Sources\n", "HEADING_2")
            for i, src in enumerate(fee_explainer.source_links, start=1):
                add_text(f"{i}. {src}\n")
                
        # Insert the new text
        full_text = "".join(text_parts)
        
        insert_request = {
            "insertText": {
                "location": {"index": 1},
                "text": full_text
            }
        }
        requests.append(insert_request)
        
        # 3. Apply H1/H2 styles to the designated ranges
        for start, end, style in styles:
            style_req = {
                "updateParagraphStyle": {
                    "range": {
                        "startIndex": start,
                        "endIndex": end
                    },
                    "paragraphStyle": {
                        "namedStyleType": style
                    },
                    "fields": "namedStyleType"
                }
            }
            requests.append(style_req)
        
        result = service.documents().batchUpdate(
            documentId=doc_id, body={"requests": requests}
        ).execute()
        
        logger.info(f"Successfully updated Google Doc: {doc_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update Google Doc: {e}")
        return False
