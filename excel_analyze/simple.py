import pandas as pd
import numpy as np

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
            results["Gross Margin"] = gross_profit["Year Total"] / revenue["Year Total"]
        else:
            results["Gross Margin"] = None
        
        # Operating Margin
        if (revenue is not None and gross_profit is not None and 
            op_expenses is not None and revenue["Year Total"] > 0):
            operating_profit = gross_profit["Year Total"] - op_expenses["Year Total"]
            results["Operating Margin"] = operating_profit / revenue["Year Total"]
        else:
            results["Operating Margin"] = None
        
        # EBITDA not possible (no depreciation/amortization in data)
        results["EBITDA Margin"] = None
        
        # Net Margin
        if (revenue is not None and net_profit is not None and 
            revenue["Year Total"] > 0):
            results["Net Margin"] = net_profit["Year Total"] / revenue["Year Total"]
        else:
            results["Net Margin"] = None
        
        return self.clean_dict(results)
    
    def calculate_growth(self):
        """Calculate and return growth trends as dictionary"""
        revenue = self.get_row("Revenue")
        net_profit = self.get_row("Net Profit")
        
        if revenue is None or net_profit is None:
            return {"Revenue Trend": None, "Net Income Trend": None}
        
        # Extract monthly data
        revenue_trend = []
        net_profit_trend = []
        
        for month in self.monthly_columns:
            if month in revenue.index:
                revenue_trend.append(revenue[month])
            else:
                revenue_trend.append(None)
        
        for month in self.monthly_columns:
            if month in net_profit.index:
                net_profit_trend.append(net_profit[month])
            else:
                net_profit_trend.append(None)
        
        results = {
            "Revenue Trend": revenue_trend, 
            "Net Income Trend": net_profit_trend
        }
        
        return self.clean_dict(results)
    
    def calculate_liquidity(self):
        """Calculate and return liquidity metrics as dictionary"""
        # Current Ratio, Quick Ratio, CCC not possible 
        # (we don't have balance sheet items like current assets/liabilities/inventory)
        results = {
            "Current Ratio": None, 
            "Quick Ratio": None, 
            "Cash Conversion Cycle": None
        }
        
        return self.clean_dict(results)
    
    def calculate_investment(self):
        """Calculate and return investment performance metrics as dictionary"""
        # ROA, ROE, ROIC not possible 
        # (we don't have assets, equity, capital invested)
        results = {
            "ROA": None, 
            "ROE": None, 
            "ROIC": None
        }
        
        return self.clean_dict(results)
    
    def calculate_leverage(self):
        """Calculate and return leverage and risk metrics as dictionary"""
        # Debt-to-Equity, Interest Coverage not possible 
        # (no debt/equity/interest expense data in sheet)
        results = {
            "Debt-to-Equity": None, 
            "Interest Coverage": None
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
        return {
            "Profitability": self.calculate_profitability(),
            "Growth Tracker": self.calculate_growth(),
            "Liquidity & Efficiency": self.calculate_liquidity(),
            "Investment Performance": self.calculate_investment(),
            "Leverage & Risk": self.calculate_leverage()
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