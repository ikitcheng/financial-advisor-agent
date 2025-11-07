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


class CreditCardStatementPipeline:
    """Pipeline for processing credit card statements"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = ADEClient(api_key)
        self.schema = self._get_credit_card_schema()
    
    def _get_credit_card_schema(self) -> Dict:
        """Define the JSON schema for credit card statement extraction"""
        return {
            "type": "object",
            "properties": {
                "card_info": {
                    "type": "object",
                    "properties": {
                        "card_number": {"type": "string", "description": "Last 4 digits or masked card number"},
                        "cardholder_name": {"type": "string"},
                        "statement_date": {"type": "string", "format": "date"},
                        "payment_due_date": {"type": "string", "format": "date"},
                        "address": {"type": "string"}
                    },
                    "required": ["card_number", "cardholder_name", "statement_date"]
                },
                "account_summary": {
                    "type": "object",
                    "properties": {
                        "currency": {"type": "string"},
                        "credit_limit": {"type": "number"},
                        "cash_advance_limit": {"type": "number"},
                        "current_balance": {"type": "number"},
                        "minimum_payment": {"type": "number"},
                        "previous_balance": {"type": "number"},
                        "payments_received": {"type": "number"},
                        "new_charges": {"type": "number"},
                        "adjustments": {"type": "number"},
                        "finance_charges": {"type": "number"},
                        "total_points": {"type": "integer"}
                    },
                    "required": ["currency", "current_balance", "minimum_payment"]
                },
                "transactions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "transaction_date": {"type": "string", "format": "date"},
                            "posting_date": {"type": "string", "format": "date"},
                            "description": {"type": "string"},
                            "amount": {"type": "number"},
                            "card_last_four": {"type": "string"}
                        },
                        "required": ["transaction_date", "description", "amount"]
                    }
                }
            },
            "required": ["card_info", "account_summary", "transactions"]
        }
    
    def process_statement(
        self,
        file_path: str,
        output_dir: Optional[str] = None,
        save_markdown: bool = True,
        save_json: bool = True
    ) -> Dict[str, Any]:
        """
        Process a credit card statement through the full pipeline
        
        Args:
            file_path: Path to the statement PDF/image
            output_dir: Directory to save outputs (default: same as input)
            save_markdown: Whether to save markdown output
            save_json: Whether to save JSON output
            
        Returns:
            Dict with markdown and structured_data keys
        """
        file_path = Path(file_path)
        if output_dir is None:
            output_dir = file_path.parent
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📄 Parsing document to markdown: {file_path.name}")
        parse_result = self.client.parse_document(str(file_path))
        markdown = parse_result.get("markdown", "") # return empty string if no markdown parsed
        
        if save_markdown:
            markdown_path = output_dir / f"{file_path.stem}_parsed.md"
            with open(markdown_path, "w", encoding="utf-8") as f:
                f.write(markdown)
            print(f"✅ Markdown saved to: {markdown_path}")
        
        print(f"🔍 Extracting structured data...")
        extract_result = self.client.extract_structured_data(markdown, self.schema)
        structured_data = extract_result.get("data", {}) # return empty json if no structured data found
        
        # Post-process and validate
        print(f"🔍 Post-processing structured data to get transaction summary...")
        structured_data = self._post_process(structured_data)
        
        if save_json:
            json_path = output_dir / f"{file_path.stem}_extracted.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(structured_data, f, indent=2, ensure_ascii=False)
            print(f"✅ JSON saved to: {json_path}")
        
        return {
            "markdown": markdown,
            "structured_data": structured_data,
            "metadata": {
                "source_file": str(file_path),
                "processed_at": datetime.now().isoformat()
            }
        }
    
    def _post_process(self, data: Dict) -> Dict:
        """Post-process extracted json data for consistency"""
        # Sort transactions by date (descending)
        if "transactions" in data and data["transactions"]:
            data["transactions"].sort(
                key=lambda x: x.get("transaction_date", ""),
                reverse=True
            )
        
        # Calculate transaction statistics
        if "transactions" in data:
            transactions = data["transactions"]
            total_debits = sum(t["amount"] for t in transactions if t["amount"] > 0)
            total_credits = sum(abs(t["amount"]) for t in transactions if t["amount"] < 0)
            
            data["transaction_summary"] = {
                "total_transactions": len(transactions),
                "total_debits": round(total_debits, 2),
                "total_credits": round(total_credits, 2),
                "net_change": round(total_debits - total_credits, 2)
            }
        
        return data
    
    def batch_process(
        self,
        file_paths: List[str],
        output_dir: str,
        continue_on_error: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Process multiple statements in batch
        
        Args:
            file_paths: List of file paths to process
            output_dir: Directory to save all outputs
            continue_on_error: Continue processing if one file fails
            
        Returns:
            List of results for each file
        """
        results = []
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for i, file_path in enumerate(file_paths, 1):
            print(f"\n{'='*60}")
            print(f"Processing {i}/{len(file_paths)}: {Path(file_path).name}")
            print(f"{'='*60}")
            
            try:
                result = self.process_statement(file_path, output_dir=output_dir)
                results.append({
                    "file": file_path,
                    "status": "success",
                    "data": result
                })
            except Exception as e:
                error_msg = f"Error processing {file_path}: {str(e)}"
                print(f"❌ {error_msg}")
                results.append({
                    "file": file_path,
                    "status": "error",
                    "error": error_msg
                })
                if not continue_on_error:
                    raise
        
        # Save batch summary
        summary_path = output_dir / "batch_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump({
                "processed_at": datetime.now().isoformat(),
                "total_files": len(file_paths),
                "successful": sum(1 for r in results if r["status"] == "success"),
                "failed": sum(1 for r in results if r["status"] == "error"),
                "results": results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Batch summary saved to: {summary_path}")
        return results


# Example usage
if __name__ == "__main__":
    # Initialize pipeline
    pipeline = CreditCardStatementPipeline()
    
    # Process single statement
    result = pipeline.process_statement(
        file_path="0001.pdf",
        output_dir="./output",
        save_markdown=True,
        save_json=True
    )
    
    print("\n" + "="*60)
    print("PROCESSING SUMMARY")
    print("="*60)
    print(f"Card: {result['structured_data'].get('card_info', {}).get('cardholder_name', 'N/A')}")
    print(f"Balance: {result['structured_data'].get('account_summary', {}).get('current_balance', 0)} "
          f"{result['structured_data'].get('account_summary', {}).get('currency', 'N/A')}")
    print(f"Transactions: {len(result['structured_data'].get('transactions', []))}")
    
    # Batch processing example (uncomment to use)
    # results = pipeline.batch_process(
    #     file_paths=["statement1.pdf", "statement2.pdf", "statement3.pdf"],
    #     output_dir="./batch_output"
    # )