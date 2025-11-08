import os
import json
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path


class ADEClient:
    """Client for LandingAI Agentic Document Extraction API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("LANDINGAI_API_KEY")
        if not self.api_key:
            raise ValueError("LANDINGAI_API_KEY must be provided or set in environment")
        self.base_url = "https://api.va.landing.ai/v1/ade"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
    
    def parse_document(self, file_path: str, model: str = "dpt-2-latest") -> Dict[str, Any]:
        """
        Parse a document (PDF, image, etc.) to markdown
        
        Args:
            file_path: Path to the document file
            model: Model to use for parsing (default: dpt-2-latest)
            
        Returns:
            Dict containing parsed markdown and metadata
        """
        with open(file_path, "rb") as f:
            files = {"document": f}
            data = {"model": model}
            resp = requests.post(
                f"{self.base_url}/parse",
                headers=self.headers,
                files=files,
                data=data
            )
        resp.raise_for_status()
        return resp.json()
    
    def extract_structured_data(self, markdown: str, schema: Dict) -> Dict[str, Any]:
        """
        Extract structured data from markdown using a JSON schema
        
        Args:
            markdown: Markdown text to extract from
            schema: JSON schema defining the structure to extract
            
        Returns:
            Dict containing extracted structured data
        """
        data = {
            "schema": json.dumps(schema),
            "markdown": markdown
        }
        resp = requests.post(
            f"{self.base_url}/extract",
            headers=self.headers,
            data=data
        )
        resp.raise_for_status()
        return resp.json()
