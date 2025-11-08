"""
Document Extraction Schema Templates
Provides pre-built schemas for different document types
"""

# ===================================================================
# CREDIT CARD STATEMENT SCHEMA
# ===================================================================
CREDIT_CARD_SCHEMA = {
    "type": "object",
    "properties": {
        "card_number": {
            "type": "string",
            "description": "Credit card number (full or masked)"
        },
        "cardholder_name": {
            "type": "string",
            "description": "Name of the credit card holder"
        },
        "statement_date": {
            "type": "string",
            "description": "Statement date or billing period"
        },
        "payment_due_date": {
            "type": "string",
            "description": "Payment due date"
        },
        "credit_limit": {
            "type": "string",
            "description": "Total credit limit with currency"
        },
        "cash_advance_limit": {
            "type": "string",
            "description": "Cash advance limit with currency"
        },
        "current_balance": {
            "type": "string",
            "description": "Current balance or amount due"
        },
        "minimum_payment": {
            "type": "string",
            "description": "Minimum payment required"
        },
        "previous_balance": {
            "type": "string",
            "description": "Previous balance"
        },
        "payments_made": {
            "type": "string",
            "description": "Payments received this period"
        },
        "new_charges": {
            "type": "string",
            "description": "New charges this period"
        },
        "adjustments": {
            "type": "string",
            "description": "Account adjustments"
        },
        "finance_charges": {
            "type": "string",
            "description": "Interest or finance charges"
        },
        "total_points": {
            "type": "string",
            "description": "Total reward points available"
        },
        "points_earned": {
            "type": "string",
            "description": "Points earned this period"
        },
        "transactions": {
            "type": "array",
            "description": "List of transactions",
            "items": {
                "type": "object",
                "properties": {
                    "transaction_date": {
                        "type": "string",
                        "description": "Transaction date"
                    },
                    "posting_date": {
                        "type": "string",
                        "description": "Posting date"
                    },
                    "description": {
                        "type": "string",
                        "description": "Merchant or transaction description"
                    },
                    "amount": {
                        "type": "string",
                        "description": "Amount (positive=charge, negative=credit/refund)"
                    }
                }
            }
        }
    }
}


# ===================================================================
# INVOICE SCHEMA
# ===================================================================
INVOICE_SCHEMA = {
    "type": "object",
    "properties": {
        "invoice_number": {
            "type": "string",
            "description": "Invoice number or ID"
        },
        "invoice_date": {
            "type": "string",
            "description": "Date invoice was issued"
        },
        "due_date": {
            "type": "string",
            "description": "Payment due date"
        },
        "seller_name": {
            "type": "string",
            "description": "Name of seller/vendor/supplier"
        },
        "seller_address": {
            "type": "string",
            "description": "Seller's address"
        },
        "seller_tax_id": {
            "type": "string",
            "description": "Seller's tax ID or registration number"
        },
        "buyer_name": {
            "type": "string",
            "description": "Name of buyer/customer"
        },
        "buyer_address": {
            "type": "string",
            "description": "Buyer's address"
        },
        "subtotal": {
            "type": "string",
            "description": "Subtotal before tax"
        },
        "tax_amount": {
            "type": "string",
            "description": "Total tax amount"
        },
        "total_amount": {
            "type": "string",
            "description": "Total amount due including tax"
        },
        "currency": {
            "type": "string",
            "description": "Currency code (USD, EUR, CNY, etc.)"
        },
        "line_items": {
            "type": "array",
            "description": "List of items or services",
            "items": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Item or service description"
                    },
                    "quantity": {
                        "type": "string",
                        "description": "Quantity"
                    },
                    "unit_price": {
                        "type": "string",
                        "description": "Price per unit"
                    },
                    "amount": {
                        "type": "string",
                        "description": "Line total amount"
                    }
                }
            }
        }
    }
}


# ===================================================================
# BANK STATEMENT SCHEMA
# ===================================================================
BANK_STATEMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "account_holder": {
            "type": "string",
            "description": "Account holder name"
        },
        "account_number": {
            "type": "string",
            "description": "Bank account number"
        },
        "statement_period": {
            "type": "string",
            "description": "Statement period (e.g., 'Jan 1 - Jan 31, 2025')"
        },
        "opening_balance": {
            "type": "string",
            "description": "Beginning balance"
        },
        "closing_balance": {
            "type": "string",
            "description": "Ending balance"
        },
        "total_deposits": {
            "type": "string",
            "description": "Total deposits for period"
        },
        "total_withdrawals": {
            "type": "string",
            "description": "Total withdrawals for period"
        },
        "transactions": {
            "type": "array",
            "description": "List of transactions",
            "items": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Transaction date"
                    },
                    "description": {
                        "type": "string",
                        "description": "Transaction description"
                    },
                    "amount": {
                        "type": "string",
                        "description": "Amount (positive=deposit, negative=withdrawal)"
                    },
                    "balance": {
                        "type": "string",
                        "description": "Balance after transaction"
                    }
                }
            }
        }
    }
}

# ===================================================================
# RECEIPT SCHEMA
# ===================================================================
RECEIPT_SCHEMA = {
    "type": "object",
    "properties": {
        "merchant_name": {
            "type": "string",
            "description": "Name of merchant or store"
        },
        "merchant_address": {
            "type": "string",
            "description": "Store address"
        },
        "transaction_date": {
            "type": "string",
            "description": "Date of purchase"
        },
        "transaction_time": {
            "type": "string",
            "description": "Time of purchase"
        },
        "receipt_number": {
            "type": "string",
            "description": "Receipt or transaction number"
        },
        "subtotal": {
            "type": "string",
            "description": "Subtotal before tax"
        },
        "tax": {
            "type": "string",
            "description": "Tax amount"
        },
        "total": {
            "type": "string",
            "description": "Total amount paid"
        },
        "payment_method": {
            "type": "string",
            "description": "Payment method used (cash, card, etc.)"
        },
        "items": {
            "type": "array",
            "description": "List of purchased items",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Item name or description"
                    },
                    "quantity": {
                        "type": "string",
                        "description": "Quantity purchased"
                    },
                    "unit_price": {
                        "type": "string",
                        "description": "Price per unit"
                    },
                    "total_price": {
                        "type": "string",
                        "description": "Total price for item"
                    }
                }
            }
        }
    }
}


# ===================================================================
# UTILITY FUNCTION
# ===================================================================
def get_schema_for_document_type(doc_type: str):
    """
    Get the appropriate schema for a document type
    
    Args:
        doc_type: Type of document ('credit_card', 'invoice', 'bank_statement', 
                  'receipt')
    
    Returns:
        JSON schema dictionary
    """
    schemas = {
        'credit_card': CREDIT_CARD_SCHEMA,
        'invoice': INVOICE_SCHEMA,
        'bank_statement': BANK_STATEMENT_SCHEMA,
        'receipt': RECEIPT_SCHEMA
    }
    
    if doc_type not in schemas:
        raise ValueError(f"Unknown document type: {doc_type}. "
                        f"Available types: {list(schemas.keys())}")
    
    return schemas[doc_type]


# ===================================================================
# EXAMPLE USAGE
# ===================================================================
if __name__ == "__main__":
    import json
    
    # Get schema for credit card statement
    schema = get_schema_for_document_type('credit_card')
    print("Credit Card Schema:")
    print(json.dumps(schema, indent=2))
    
    # List all available schemas
    print("\n\nAvailable document types:")
    for doc_type in ['credit_card', 'invoice', 'bank_statement', 'receipt']:
        schema = get_schema_for_document_type(doc_type)
        field_count = len(schema['properties'])
        print(f"  - {doc_type}: {field_count} fields")