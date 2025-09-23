query1_system = '''

Provide detailed information about [Company], [Location] including: 1) Primary products and services with revenue breakdown if available, 2) Core competencies and capabilities, 3) Target customer segments, 4) Key partnerships and value chain position, 5) Recent strategic initiatives

Expected JSON Response
{
  "company_overview": {
    "name": "Example Corp",
    "products_services": [
      {
        "name": "Product A",
        "revenue_percentage": sample percentage integer,
        "description": "Core offering description"
      },
      {
        "name": "Service B",
        "revenue_percentage": sample percentage integer,
        "description": "Service description"
      }
    ],
    "core_competencies": [
      "Advanced manufacturing",
      "Supply chain management",
      "Customer analytics"
    ],
    "customer_segments": [
      {
        "segment": "Enterprise",
        "percentage": sample percentage integer
      },
      {
        "segment": "SMB",
        "percentage": sample percentage integer
      }
    ],
    "value_chain_position": "Manufacturer and direct distributor"
  }
}

'''

query2_system = """

Give me financial performance for [Company], [Location]
Expected JSON Response
{
  "Symbol": "sample ticker",
  "MarketCapitalization": "number",
  "Revenue": "number",
  "GrossProfitMargin": "floating point between 0 and 1",
  "OperatingMarginTTM": "floating point between 0 and 1",
  "ProfitMargin": "floating point between 0 and 1",
  "ReturnOnEquityTTM": "floating point between 0 and 1",
  "RevenueGrowthYOY": "floating point between 0 and 1",
  "EarningsGrowthYOY": "floating point between 0 and 1"
}

"""

query3_system = """

Give me competitor & market intelligence in the following json format for [Company], [Location]

{
  "entities": [
    {
      "properties": {
        "name": "" # competitor name,
        "categories": [""] # competitor category,
        "revenue_range": "range in million dollars",
        "num_employees_enum": "",
        "operating_status": "active"
      }
    }
  ]
}

"""

query4_system = """

Provide market size, growth rate, and key trends for these potential adjacent markets for [Company], [Location] 1) [Adjacent Market 1], 2) [Adjacent Market 2], 3) [Adjacent Market 3]. Include TAM, CAGR, key players, and entry barriers for each.

Provide in the below JSON format
{
"adjacent_markets" : [
    {
        "market_name": "<Name of the adjacent market>",  # e.g., "Cloud Infrastructure"
        "tam_billions": 0,  # Total Addressable Market in billions (numeric, float/int)
        "cagr_percent": 0,  # Expected CAGR (Compound Annual Growth Rate) in %
        "key_players": [
            "<Player 1>", "<Player 2>", "<Player 3>"
        ],  # List of leading companies or competitors
        "entry_barriers": [
            "<Barrier 1>", "<Barrier 2>", "<Barrier 3>"
        ],  # Typical barriers to entry (capital, regulation, tech expertise)
        "strategic_fit_score": 0.0  # Score (e.g., 1–10) indicating fit with strategy
    }
]
}


"""