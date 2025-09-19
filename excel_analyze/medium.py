from typing import Optional
import pandas as pd
import numpy as np
from helpers import get_threshold_metrics
import json 

class MediumAnalysis:
    """
    Adapter class to analyze financial data from a DataFrame and return results as dictionaries
    """
    
    def __init__(self, df):
        """
        Initialize the adapter with a financial DataFrame
        
        Args:
            df (pd.DataFrame): DataFrame containing financial data with 'Category' column
        """
        self.df = df
        # print(df[df['Category']])
        # self.df['Total Assets'] = self.df['Equity'] + self.df['Total Liabilities']
    def get_value(self, row_name, col="Year Total"):
        """Extract a specific value from the DataFrame"""
        row = self.df[self.df["Category"].str.strip().str.lower() == row_name.lower()]
        if not row.empty and col in self.df.columns:
            # print(row[col])
            val = row[col].values[0]
            return float(val) if pd.notnull(val) else np.nan
        return np.nan
    
    @staticmethod
    def safe_divide(numerator, denominator, percent: Optional[bool] = False):
        """Safely divide two numbers, handling zeros and NaN values"""
        if denominator in (0, np.nan, None) or pd.isna(denominator):
            return None
        if pd.isna(numerator):
            return None
        return float(numerator / denominator) if not percent else float(numerator / denominator) * 100
    
    @staticmethod
    def clean_value(value):
        """Convert NaN values to None for JSON compatibility"""
        if pd.isna(value):
            return None
        return float(value) if isinstance(value, (int, float, np.number)) else value
    
    def clean_dict(self, data_dict):
        """Recursively clean dictionary of NaN values"""
        cleaned = {}
        for key, value in data_dict.items():
            if isinstance(value, dict):
                cleaned[key] = self.clean_dict(value)
            elif isinstance(value, (list, tuple)):
                cleaned[key] = [self.clean_value(v) for v in value]
            else:
                cleaned[key] = self.clean_value(value)
        return cleaned
    
    def get_profitability_metrics(self):
        """Calculate and return profitability metrics as dictionary"""
        revenue = self.get_value("Revenue")
        cogs = self.get_value("Cost of Goods Sold")
        gross_profit = self.get_value("Gross Profit")
        operating_income = self.get_value("Operating Income (EBIT)")
        ebitda = self.get_value("EBITDA")
        net_income = self.get_value("Net Income")
        
        metrics = {
            "gross_margin": self.safe_divide(gross_profit, revenue, True),
            "operating_margin": self.safe_divide(operating_income, revenue, True),
            "ebitda_margin": self.safe_divide(ebitda, revenue, True),
            "net_margin": self.safe_divide(net_income, revenue, True)
        }
        
        return self.clean_dict(metrics)
    
    def get_liquidity_metrics(self):
        """Calculate and return liquidity metrics as dictionary"""
        current_assets = self.get_value("Total Assets")
        current_liabilities = self.get_value("Total Liabilities")
        inventory = 0
        
        metrics = {
            "current_ratio": self.safe_divide(current_assets, current_liabilities),
            "quick_ratio": self.safe_divide(current_assets - inventory, current_liabilities)
        }
        
        return self.clean_dict(metrics)
    
    def get_investment_metrics(self):
        """Calculate and return investment performance metrics as dictionary"""
        net_income = self.get_value("Net Income")
        print(net_income)
        operating_income = self.get_value("Operating Income")
        total_assets = self.get_value('Equity') + self.get_value('Total Liabilities') # equity + liabilities
        shareholder_equity = self.get_value("Shareholder Equity") if self.get_value('Shareholder Equity') is not None else 0
        debt = self.get_value("- Short-term Debt")
        
        metrics = {
            "roa": self.safe_divide(net_income, total_assets),
            "roe": self.safe_divide(net_income, shareholder_equity),
            "roic": self.safe_divide(operating_income, (debt + shareholder_equity))
        }
        
        return self.clean_dict(metrics)
    
    def get_leverage_metrics(self):
        """Calculate and return leverage and risk metrics as dictionary"""
        debt = self.get_value("Total Debt")
        shareholder_equity = self.get_value("Shareholder Equity")
        operating_income = self.get_value("Operating Income")
        interest_expense = self.get_value("Interest Expense")
        
        metrics = {
            "debt_to_equity": self.safe_divide(debt, shareholder_equity),
            "interest_coverage": self.safe_divide(operating_income, interest_expense)
        }
        
        return self.clean_dict(metrics)
    
    def get_growth_trends(self):
        """Calculate and return growth trends as dictionary"""
        monthly_cols = [c for c in self.df.columns if c not in ["Category", "Year Total"]]
        
        # Revenue trend
        revenue_row = self.df[self.df["Category"].str.strip().str.lower() == "revenue"]
        revenue_data = {}
        if not revenue_row.empty and monthly_cols:
            revenue_values = revenue_row[monthly_cols].values[0]
            revenue_series = pd.Series(revenue_values, index=monthly_cols)
            quarters = {
                "Q1": ["January", "February", "March"],
                "Q2": ["April", "May", "June"],
                "Q3": ["July", "August", "September"],
                "Q4": ["October", "November", "December"],
            }
        
        # Aggregate into quarterly totals
            quarterly_series = pd.Series({
                q: revenue_series[months].sum() for q, months in quarters.items()
            })
    
    # Calculate QoQ growth (quarter-on-quarter)
            qoq_growth = quarterly_series.pct_change().to_dict()
            # Calculate growth rates and clean NaN values
            # qoq_growth = revenue_series.pct_change().to_dict()
            # yoy_growth = revenue_series.pct_change(12).to_dict()
            
            revenue_data = {
                "values": self.clean_dict(revenue_series.to_dict()),
                "qoq_growth": self.clean_dict(qoq_growth),
                # "yoy_growth": self.clean_dict(yoy_growth)
            }
        
        # Net income trend
        net_income_row = self.df[self.df["Category"].str.strip().str.lower() == "net income"]
        net_income_data = {}
        if not net_income_row.empty and monthly_cols:
            net_income_values = net_income_row[monthly_cols].values[0]
            net_income_series = pd.Series(net_income_values, index=monthly_cols)
            quarters = {
                "Q1": ["January", "February", "March"],
                "Q2": ["April", "May", "June"],
                "Q3": ["July", "August", "September"],
                "Q4": ["October", "November", "December"],
            }
        
        # Aggregate into quarterly totals
            quarterly_series = pd.Series({
                q: net_income_series[months].sum() for q, months in quarters.items()
            })
            qoq_growth = quarterly_series.pct_change().to_dict()
            # Calculate growth rates and clean NaN values
            # qoq_growth = net_income_series.pct_change().to_dict()
            # yoy_growth = net_income_series.pct_change(12).to_dict()
            
            net_income_data = {
                "values": self.clean_dict(net_income_series.to_dict()),
                "qoq_growth": self.clean_dict(qoq_growth),
                # "yoy_growth": self.clean_dict(yoy_growth)
            }
        
        return {
            "revenue": revenue_data,
            "net_income": net_income_data
        }
    
    def get_all_metrics(self):
        text_result, citations = get_threshold_metrics('kasnet')
        result = json.loads(text_result)
        """Get all financial metrics in a single dictionary"""
        return {
            "profitability": self.get_profitability_metrics(),
            "liquidity": self.get_liquidity_metrics(),
            "investment": self.get_investment_metrics(),
            "leverage": self.get_leverage_metrics(),
            "growth_trends": self.get_growth_trends(),
            "threshold": result, 
            "citations": citations
        }


# Example usage:
if __name__ == "__main__":
    # Assuming you have your df loaded
    # df = pd.read_excel(file_path, sheet_name="Sheet1")
    
    # Initialize the adapter
    # analyzer = FinancialAnalysisAdapter(df)
    
    # Get individual metric groups
    # profitability = analyzer.get_profitability_metrics()
    # liquidity = analyzer.get_liquidity_metrics()
    # investment = analyzer.get_investment_metrics()
    # leverage = analyzer.get_leverage_metrics()
    # growth = analyzer.get_growth_trends()
    
    # Or get all metrics at once
    # all_metrics = analyzer.get_all_metrics()
    
    # Print results
    # print("Profitability:", profitability)
    # print("Liquidity:", liquidity)
    # print("Investment:", investment)
    # print("Leverage:", leverage)
    # print("Growth Trends:", growth)
    
    pass