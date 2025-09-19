import json
import pandas as pd
import numpy as np

from helpers import get_threshold_metrics

class SimpleFinancialAnalysisAdapter:
    """
    Adapter class to analyze financial data from a DataFrame and return results as dictionaries
    Handles simpler financial data structure with basic P&L items
    """
    
    def __init__(self, df):
        """
        Initialize the adapter with a financial DataFrame
        
        Args:
            df (pd.DataFrame): DataFrame containing financial data with 'Category' column
        """
        self.df = df
        self.monthly_columns = ["January", "February", "March", "April", "May", "June",
                               "July", "August", "September", "October", "November", "December"]
    
    def get_row(self, category):
        """Helper to fetch row values by category"""
        row = self.df[self.df["Category"] == category]
        if row.empty:
            return None
        return row.iloc[0]
    
    @staticmethod
    def clean_value(value):
        """Convert NaN values to None for JSON compatibility"""
        if pd.isna(value):
            return None
        if isinstance(value, (int, float, np.number)):
            if np.isnan(value) or np.isinf(value):
                return None
            return float(value)
        return value
    
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
    
    def calculate_profitability(self):
        """Calculate and return profitability metrics as dictionary"""
        revenue = self.get_row("Revenue")
        gross_profit = self.get_row("Gross Profit")
        op_expenses = self.get_row("Operating Expenses")
        net_profit = self.get_row("Net Profit")
        
        results = {}
        
        # Gross Margin
        if (revenue is not None and gross_profit is not None and 
            revenue["Year Total"] > 0):
            results["gross_margin"] = gross_profit["Year Total"] / revenue["Year Total"]
        else:
            results["gross_margin"] = None
        
        # Operating Margin
        if (revenue is not None and gross_profit is not None and 
            op_expenses is not None and revenue["Year Total"] > 0):
            operating_profit = gross_profit["Year Total"] - op_expenses["Year Total"]
            results["operating_margin"] = operating_profit / revenue["Year Total"]
        else:
            results["operating_margin"] = None
        
        # EBITDA not possible (no depreciation/amortization in data)
        results["ebitda_margin"] = None
        
        # Net Margin
        if (revenue is not None and net_profit is not None and 
            revenue["Year Total"] > 0):
            results["net_margin"] = net_profit["Year Total"] / revenue["Year Total"]
        else:
            results["net_margin"] = None
        
        return self.clean_dict(results)
    
    def calculate_growth(self):
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
        
        return self.clean_dict(results)
    
    def calculate_liquidity(self):
        """Calculate and return liquidity metrics as dictionary"""
        # Current Ratio, Quick Ratio, CCC not possible 
        # (we don't have balance sheet items like current assets/liabilities/inventory)
        results = {
            "current_ratio": None, 
            "quick_ratio": None, 
        }
        
        return self.clean_dict(results)
    
    def calculate_investment(self):
        """Calculate and return investment performance metrics as dictionary"""
        # ROA, ROE, ROIC not possible 
        # (we don't have assets, equity, capital invested)
        results = {
            "roa": None, 
            "roe": None, 
            "roic": None
        }
        
        return self.clean_dict(results)
    
    def calculate_leverage(self):
        """Calculate and return leverage and risk metrics as dictionary"""
        # Debt-to-Equity, Interest Coverage not possible 
        # (no debt/equity/interest expense data in sheet)
        results = {
            "debt_to_equity": None, 
            "interest_coverage": None
        }
        
        return self.clean_dict(results)
    
    def get_profitability_metrics(self):
        """Alias for calculate_profitability for consistency"""
        return self.calculate_profitability()
    
    def get_growth_trends(self):
        """Alias for calculate_growth for consistency"""
        return self.calculate_growth()
    
    def get_liquidity_metrics(self):
        """Alias for calculate_liquidity for consistency"""
        return self.calculate_liquidity()
    
    def get_investment_metrics(self):
        """Alias for calculate_investment for consistency"""
        return self.calculate_investment()
    
    def get_leverage_metrics(self):
        """Alias for calculate_leverage for consistency"""
        return self.calculate_leverage()
    
    def get_all_metrics(self):
        """Get all financial metrics in a single dictionary"""
        text_result, citations = get_threshold_metrics('kasnet')
        result = json.loads(text_result)
        return {
            "profitability": self.calculate_profitability(),
            "growth_trends": self.calculate_growth(),
            "liquidity": self.calculate_liquidity(),
            "investment": self.calculate_investment(),
            "leverage": self.calculate_leverage(),
            "threshold": result,
            "citations": citations
        }


# Example usage:
if __name__ == "__main__":
    # Load your DataFrame
    # input_file = "Traxxia_Financial_Template_Filled.xlsx"
    # df = pd.read_excel(input_file)
    
    # Initialize the adapter
    # analyzer = SimpleFinancialAnalysisAdapter(df)
    
    # Get individual metric groups
    # profitability = analyzer.get_profitability_metrics()
    # growth = analyzer.get_growth_trends()
    # liquidity = analyzer.get_liquidity_metrics()
    # investment = analyzer.get_investment_metrics()
    # leverage = analyzer.get_leverage_metrics()
    
    # Or get all metrics at once (matches your original structure)
    # all_metrics = analyzer.get_all_metrics()
    
    # Print results (same format as your original code)
    # print("===== Metrics Extracted =====")
    # for section, values in all_metrics.items():
    #     print(f"\n{section}:")
    #     for k, v in values.items():
    #         print(f"  {k}: {v}")
    
    pass