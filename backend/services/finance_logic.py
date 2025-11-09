from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import json
from collections import defaultdict
import statistics
from services.landing_ai_ade import ADEClient
from services.schema_templates import get_schema_for_document_type

def safe_float(value):
    """Convert string values like '5,000,000' or '$2M' into float safely."""
    if value is None:
        return 0.0
    try:
        return float(str(value).replace(",", "").replace("$", "").strip())
    except Exception:
        return 0.0
    

class CreditCardStatementPipeline:
    """Pipeline for processing credit card statements"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = ADEClient(api_key)
        self.schema = self._get_credit_card_schema()
    
    def _get_credit_card_schema(self) -> Dict:
        """Define the JSON schema for credit card statement extraction"""
        credit_card_schema = get_schema_for_document_type("credit_card")
        return credit_card_schema
    
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
        structured_data = extract_result.get("extraction", {}) # return empty json if no structured data found
        
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
    
    def load_markdown_file(self, markdown_path: str) -> str:
        """
        Load a previously saved markdown file
        
        Args:
            markdown_path: Path to the markdown file to load
            
        Returns:
            String containing the markdown content
            
        Raises:
            FileNotFoundError: If the markdown file doesn't exist
            UnicodeDecodeError: If the file cannot be decoded as UTF-8
        """
        markdown_path = Path(markdown_path)
        
        if not markdown_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {markdown_path}")
        
        if not markdown_path.suffix.lower() == '.md':
            raise ValueError(f"File is not a markdown file: {markdown_path}")
        
        try:
            with open(markdown_path, "r", encoding="utf-8") as f:
                markdown_content = f.read()
            
            print(f"✅ Loaded markdown file: {markdown_path}")
            return markdown_content
            
        except UnicodeDecodeError as e:
            raise UnicodeDecodeError(f"Could not decode markdown file as UTF-8: {markdown_path}") from e
        
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
            total_debits = sum(safe_float(t["amount"]) for t in transactions if safe_float(t["amount"]) > 0)
            total_credits = sum(abs(safe_float(t["amount"])) for t in transactions if safe_float(t["amount"]) < 0)

            data["transaction_summary"] = {
                "total_transactions": len(transactions),
                "total_debits": round(total_debits, 2),
                "total_credits": round(total_credits, 2),
                "net_change": round(total_debits - total_credits, 2)
            }
        
        return data
    
    def analyze_monthly_trends(
        self,
        statements_data: List[Dict[str, Any]],
        analysis_months: int = 12,
        output_dir: Optional[str] = None,
        save_json: bool = False,
    ) -> Dict[str, Any]:
        """
        Perform comprehensive monthly trend analysis on credit card statements
        
        Args:
            statements_data: List of structured statement data (JSON format)
            analysis_months: Number of months to analyze (default: 12)
            output_dir: Directory to save analysis output (default: None)
            save_json: Whether to save the analysis result as a JSON file (default: False)

        Returns:
            Dict containing comprehensive trend analysis including:
            - Monthly spending patterns
            - Category analysis
            - Financial health indicators
            - Seasonal trends
            - Recommendations for budgeting and investing
        """
        if not statements_data:
            return {"error": "No statement data provided"}
        
        # Initialize analysis containers
        monthly_data = defaultdict(lambda: {
            'total_spending': 0.0,
            'total_payments': 0.0,
            'balance': 0.0,
            'transactions': [],
            'categories': defaultdict(float),
            'transaction_count': 0
        })
        
        all_transactions = []
        balances = []
        payment_amounts = []
        spending_amounts = []
        
        # Process each statement
        for statement in statements_data:
            statement_date = statement.get('statement_date', '')
            if not statement_date:
                continue
                
            try:
                stmt_date = datetime.strptime(statement_date, '%Y-%m-%d')
                month_key = stmt_date.strftime('%Y-%m')
            except ValueError:
                continue
            
            # Extract key financial metrics
            current_balance = safe_float(statement.get('current_balance', '0').replace('CNY', '').strip())
            payments_made = safe_float(statement.get('payments_made', '0'))
            
            monthly_data[month_key]['balance'] = current_balance
            monthly_data[month_key]['total_payments'] = payments_made
            
            balances.append(current_balance)
            if payments_made > 0:
                payment_amounts.append(payments_made)
            
            # Process transactions
            transactions = statement.get('transactions', [])
            for transaction in transactions:
                amount = safe_float(transaction.get('amount', '0'))
                description = transaction.get('description', '').lower()
                
                all_transactions.append({
                    'date': transaction.get('transaction_date', ''),
                    'amount': amount,
                    'description': description,
                    'month': month_key
                })
                
                monthly_data[month_key]['transactions'].append(transaction)
                monthly_data[month_key]['transaction_count'] += 1
                
                # Categorize spending (positive amounts are debits/spending)
                if amount > 0:
                    monthly_data[month_key]['total_spending'] += amount
                    spending_amounts.append(amount)
                    
                    # Categorize transactions
                    category = self._categorize_transaction(description)
                    monthly_data[month_key]['categories'][category] += amount
        
        # Sort months chronologically
        sorted_months = sorted(monthly_data.keys())
        
        # Calculate trend analysis
        analysis = {
            'analysis_period': {
                'start_month': sorted_months[0] if sorted_months else None,
                'end_month': sorted_months[-1] if sorted_months else None,
                'total_months': len(sorted_months)
            },
            'monthly_summary': dict(monthly_data),
            'spending_trends': self._analyze_spending_trends(monthly_data, sorted_months),
            'category_analysis': self._analyze_categories(monthly_data),
            'financial_health_score': self._calculate_financial_health_score(monthly_data, balances, payment_amounts),
            'seasonal_patterns': self._analyze_seasonal_patterns(monthly_data),
            'recommendations': self._generate_recommendations(monthly_data, balances, payment_amounts, spending_amounts)
        }

        if save_json:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            analysis_file_path = output_dir / "analysis.json"
            with open(analysis_file_path, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)
            print(f"\n✅ Analysis result saved to: {analysis_file_path}")
        
        return analysis
    
    def _categorize_transaction(self, description: str) -> str:
        """Categorize transactions based on description"""
        description = description.lower()
        
        # Payment platforms
        if any(platform in description for platform in ['tenpay', 'alipay', 'unionpay']):
            if any(food_term in description for food_term in ['restaurant', 'food', 'dining']):
                return 'dining'
            elif any(shop_term in description for shop_term in ['shop', 'mall', 'store']):
                return 'shopping'
            else:
                return 'digital_payments'
        
        # Common categories
        if any(term in description for term in ['grocery', 'supermarket', 'food']):
            return 'groceries'
        elif any(term in description for term in ['gas', 'fuel', 'petrol']):
            return 'transportation'
        elif any(term in description for term in ['restaurant', 'dining', 'cafe']):
            return 'dining'
        elif any(term in description for term in ['shopping', 'retail', 'store']):
            return 'shopping'
        elif any(term in description for term in ['entertainment', 'movie', 'game']):
            return 'entertainment'
        elif any(term in description for term in ['medical', 'hospital', 'pharmacy']):
            return 'healthcare'
        elif any(term in description for term in ['payment', 'repayment', '自扣还款']):
            return 'payments'
        else:
            return 'other'
    
    def _analyze_spending_trends(self, monthly_data: Dict, sorted_months: List[str]) -> Dict:
        """Analyze spending trends over time"""
        if len(sorted_months) < 2:
            return {'trend': 'insufficient_data'}
        
        spending_by_month = [monthly_data[month]['total_spending'] for month in sorted_months]
        
        # Calculate trend
        if len(spending_by_month) >= 3:
            recent_avg = statistics.mean(spending_by_month[-3:])
            earlier_avg = statistics.mean(spending_by_month[:-3]) if len(spending_by_month) > 3 else spending_by_month[0]
            trend_direction = 'increasing' if recent_avg > earlier_avg * 1.1 else 'decreasing' if recent_avg < earlier_avg * 0.9 else 'stable'
        else:
            trend_direction = 'increasing' if spending_by_month[-1] > spending_by_month[0] else 'decreasing'
        
        return {
            'trend_direction': trend_direction,
            'average_monthly_spending': statistics.mean(spending_by_month) if spending_by_month else 0,
            'median_monthly_spending': statistics.median(spending_by_month) if spending_by_month else 0,
            'highest_spending_month': {
                'month': sorted_months[spending_by_month.index(max(spending_by_month))],
                'amount': max(spending_by_month)
            } if spending_by_month else None,
            'lowest_spending_month': {
                'month': sorted_months[spending_by_month.index(min(spending_by_month))],
                'amount': min(spending_by_month)
            } if spending_by_month else None,
            'spending_volatility': statistics.stdev(spending_by_month) if len(spending_by_month) > 1 else 0
        }
    
    def _analyze_categories(self, monthly_data: Dict) -> Dict:
        """Analyze spending patterns by category"""
        total_category_spending = defaultdict(float)
        category_months = defaultdict(int)
        
        for month_data in monthly_data.values():
            for category, amount in month_data['categories'].items():
                total_category_spending[category] += amount
                if amount > 0:
                    category_months[category] += 1
        
        total_spending = sum(total_category_spending.values())
        
        category_analysis = {}
        for category, amount in total_category_spending.items():
            percentage = (amount / total_spending * 100) if total_spending > 0 else 0
            category_analysis[category] = {
                'total_amount': round(amount, 2),
                'percentage_of_total': round(percentage, 2),
                'average_monthly': round(amount / len(monthly_data), 2) if monthly_data else 0,
                'months_active': category_months[category]
            }
        
        # Sort by total amount
        sorted_categories = sorted(category_analysis.items(), key=lambda x: x[1]['total_amount'], reverse=True)
        
        return {
            'category_breakdown': dict(sorted_categories),
            'top_spending_category': sorted_categories[0][0] if sorted_categories else None,
            'most_frequent_category': max(category_months.items(), key=lambda x: x[1])[0] if category_months else None
        }
    
    def _calculate_financial_health_score(self, monthly_data: Dict, balances: List[float], payment_amounts: List[float]) -> Dict:
        """Calculate a financial health score based on various metrics"""
        if not monthly_data:
            return {'score': 0, 'rating': 'insufficient_data'}
        
        score = 100  # Start with perfect score
        
        # Balance trend analysis
        if len(balances) >= 2:
            balance_trend = (balances[-1] - balances[0]) / len(balances)
            if balance_trend > 0:
                score -= 20  # Increasing balance is concerning
            elif balance_trend < -100:
                score += 10  # Significant balance reduction is good
        
        # Payment consistency
        if payment_amounts:
            payment_regularity = len(payment_amounts) / len(monthly_data)
            if payment_regularity < 0.8:
                score -= 15  # Irregular payments
            elif payment_regularity == 1.0:
                score += 10  # Perfect payment record
        
        # Spending stability
        spending_amounts = [data['total_spending'] for data in monthly_data.values()]
        if len(spending_amounts) > 1:
            spending_volatility = statistics.stdev(spending_amounts) / statistics.mean(spending_amounts) if statistics.mean(spending_amounts) > 0 else 0
            if spending_volatility > 0.5:
                score -= 10  # High volatility is concerning
            elif spending_volatility < 0.2:
                score += 5  # Low volatility is good
        
        # Credit utilization (assuming average balance vs typical spending patterns)
        if balances and spending_amounts:
            avg_balance = statistics.mean(balances)
            avg_spending = statistics.mean(spending_amounts)
            if avg_balance > avg_spending * 2:
                score -= 15  # High utilization
        
        # Ensure score is within bounds
        score = max(0, min(100, score))
        
        # Rating classification
        if score >= 85:
            rating = 'excellent'
        elif score >= 70:
            rating = 'good'
        elif score >= 55:
            rating = 'fair'
        elif score >= 40:
            rating = 'poor'
        else:
            rating = 'critical'
        
        return {
            'score': round(score, 1),
            'rating': rating,
            'factors': {
                'balance_management': 'good' if len(balances) < 2 or balances[-1] <= balances[0] else 'needs_improvement',
                'payment_consistency': 'good' if not payment_amounts or len(payment_amounts) / len(monthly_data) >= 0.8 else 'needs_improvement',
                'spending_stability': 'good' if len(spending_amounts) <= 1 or (statistics.stdev(spending_amounts) / statistics.mean(spending_amounts) < 0.3) else 'needs_improvement'
            }
        }
    
    def _analyze_seasonal_patterns(self, monthly_data: Dict) -> Dict:
        """Analyze seasonal spending patterns"""
        seasonal_spending = defaultdict(list)
        
        for month_key, data in monthly_data.items():
            try:
                month_num = int(month_key.split('-')[1])
                if month_num in [12, 1, 2]:
                    season = 'winter'
                elif month_num in [3, 4, 5]:
                    season = 'spring'
                elif month_num in [6, 7, 8]:
                    season = 'summer'
                else:
                    season = 'autumn'
                
                seasonal_spending[season].append(data['total_spending'])
            except (ValueError, IndexError):
                continue
        
        seasonal_analysis = {}
        for season, amounts in seasonal_spending.items():
            if amounts:
                seasonal_analysis[season] = {
                    'average_spending': round(statistics.mean(amounts), 2),
                    'total_spending': round(sum(amounts), 2),
                    'months_data': len(amounts)
                }
        
        # Find highest spending season
        highest_season = max(seasonal_analysis.items(), key=lambda x: x[1]['average_spending']) if seasonal_analysis else None
        
        return {
            'seasonal_breakdown': seasonal_analysis,
            'highest_spending_season': highest_season[0] if highest_season else None
        }
    
    def _generate_recommendations(self, monthly_data: Dict, balances: List[float], payment_amounts: List[float], spending_amounts: List[float]) -> Dict:
        """Generate personalized financial recommendations"""
        recommendations = {
            'budgeting': [],
            'investing': [],
            'debt_management': [],
            'general': []
        }
        
        if not monthly_data:
            return recommendations
        
        avg_spending = statistics.mean(spending_amounts) if spending_amounts else 0
        avg_balance = statistics.mean(balances) if balances else 0
        
        # Budgeting recommendations
        if spending_amounts and len(spending_amounts) > 1:
            spending_volatility = statistics.stdev(spending_amounts) / statistics.mean(spending_amounts)
            if spending_volatility > 0.3:
                recommendations['budgeting'].append("Consider creating a monthly budget to reduce spending volatility")
        
        # Category-based recommendations
        category_totals = defaultdict(float)
        for data in monthly_data.values():
            for category, amount in data['categories'].items():
                category_totals[category] += amount
        
        total_spending = sum(category_totals.values())
        if total_spending > 0:
            for category, amount in category_totals.items():
                percentage = amount / total_spending
                if percentage > 0.3:
                    recommendations['budgeting'].append(f"Consider reducing {category} expenses - currently {percentage:.1%} of total spending")
        
        # Investment recommendations
        if avg_balance < avg_spending * 0.5:
            recommendations['investing'].append("Your low balance suggests focusing on emergency savings before investing")
        elif avg_balance > avg_spending * 3:
            recommendations['investing'].append("Consider investing excess funds in diversified portfolios for long-term growth")
            recommendations['investing'].append("Look into index funds or ETFs for steady, long-term returns")
        
        # Debt management
        if balances and balances[-1] > avg_spending * 2:
            recommendations['debt_management'].append("Consider paying more than the minimum to reduce high balance")
            recommendations['debt_management'].append("Look into balance transfer options if interest rates are high")
        
        # Payment consistency
        if payment_amounts and len(payment_amounts) < len(monthly_data) * 0.8:
            recommendations['debt_management'].append("Set up automatic payments to ensure consistent payment history")
        
        # General recommendations
        recommendations['general'].append("Review statements monthly to track spending patterns")
        recommendations['general'].append("Consider using budgeting apps to monitor expenses in real-time")
        
        if avg_spending > 0:
            recommendations['general'].append(f"Your average spending per transaction is {avg_spending:.2f} CNY - track this against your income")
        
        return recommendations
    
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
        file_path="../uploads/credit_card_statements/0001.pdf",
        output_dir="../output/credit_card_statements/",
        save_markdown=False,
        save_json=False
    )
    
    print("\n" + "="*60)
    print("PROCESSING SUMMARY")
    print("="*60)
    print(f"Card: {result['structured_data'].get('cardholder_name', 'N/A')}")
    print(f"Balance: {result['structured_data'].get('current_balance', 0)}")
    print(f"Transactions: {len(result['structured_data'].get('transactions', []))}")
    
    
    # Batch processing example (uncomment to use)
    # results = pipeline.batch_process(
    #     file_paths=["statement1.pdf", "statement2.pdf", "statement3.pdf"],
    #     output_dir="./batch_output"
    # )


    # Monthly trend analysis example
    # Load multiple months of statement data for trend analysis
    sample_file = Path(__file__).parent.parent / 'output' / 'credit_card_statements' / '0001_extracted.json'
    
    if not sample_file.exists():
        print(f"Sample file not found: {sample_file}")
    
    with open(sample_file, 'r', encoding='utf-8') as f:
        sample_data = json.load(f)
    statements_data = [sample_data]  # Add more statements here for comprehensive analysis
    
    print("\n" + "="*60)
    print("MONTHLY TREND ANALYSIS")
    print("="*60)
    trend_analysis = pipeline.analyze_monthly_trends(statements_data,
                                                     output_dir="../output/credit_card_statements/",
                                                     save_json=True)

    if 'error' not in trend_analysis:
        print(f"Analysis Period: {trend_analysis['analysis_period']['start_month']} to {trend_analysis['analysis_period']['end_month']}")
        print(f"Financial Health Score: {trend_analysis['financial_health_score']['score']}/100 ({trend_analysis['financial_health_score']['rating']})")
        print(f"Spending Trend: {trend_analysis['spending_trends']}")

        if trend_analysis['recommendations']['budgeting']:
            print("\nBudgeting Recommendations:")
            for rec in trend_analysis['recommendations']['budgeting'][:3]:  # Show top 3
                print(f"  • {rec}")
