from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from pydantic import BaseModel
from openai import OpenAI
import os
import json 
from typing import Optional, List
from fastapi.middleware.cors import CORSMiddleware
from swot_analysis import SWOTNewsAnalyzer
from dotenv import load_dotenv
from helpers import DocumentProcessor, fetch_top_articles, perform_web_search
load_dotenv()
app = FastAPI(title="OpenAI Question-Answer Analyzer")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
from dotenv import load_dotenv
load_dotenv()
analyzer = SWOTNewsAnalyzer(api_key=os.getenv("NEWSAPI_API_KEY", "d1b3658c875546baa970b0ff36887ac3")) 
# Configure OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
INCOMPLETE_QA_PAYLOAD = [{"role": "user", "content": "ADD `NOT ENOUGH DATA` TO THE VALUES IF YOU FEEL THE DATA IS NOT ENOUGH"}]
prompt = """
        Analyze the following question and answer pair. Determine if the answer is valid for 
        competitor analysis or not
        
        Question: {question}
        Answer: {answer}
        
        Respond with JSON format only:
        - If the answer is valid: {{"valid": true}}
        - If the answer is invalid: {{"valid": false, "feedback": "string data" # the string data will only contain the follow up question that they can ask the user for clarification}}
        
        Focus on:
        - Accuracy of the answer
        - Relevance to the question
        - Completeness of the response
        - Logical consistency
        
        
        """
        
system_prompt = """
You are a helpful assistant that analyzes question-answer pairs and provides validation feedback in JSON format. USE ONLY JSON FORMAT AND NOTHING ELSE. DO NOT USE BACKTICKS LIKE ``` OR ANYTHING ELSE, JUST PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED
"""

prompt_for_all_questions_answers = ''' 
Here are the list of questions : 
{questions}

Here are the list of answers : 
{answers}

Analyze the question-answer pairs and return the valid status and feedback in JSON format.


'''

system_prompt_for_all_questions_answers = '''
You will be given a list of question-answer pairs. Your  task is to analyze all the questions and their respective answers. 
If the answer is valid for all the questions, then return {{"valid": true}} and good for market results. 
Else, return {{"valid": false, "feedback": "string data" # the string data will only contain the follow up question that they can ask the user for clarification}}
ALWAYS PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED. DO NOT USE BACKTICKS LIKE ``` OR ANYTHING ELSE, JUST PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED
'''

system_prompt_for_competitor_finding = '''
You are a market analyst assistant, where you will 
be given a set of questions and their answers. The 
questions is about a particular product and how they 
operate. SOME IMPORTANT INSTRUCTIONS ARE GIVEN BELOW
1. MAKE SURE TO RECOMMEND ONLY COMPETITOR COMPANIES SEPARATED BY COMMAS
2. I WILL BE PARSING THE NAMES THROUGH `NewsAPI/everything` API, so
make sure that the names are in compliance to work with that API
3. Competitors names should be in this order, closest competitor 
first, to the farthest one in the last. 
4. Give me a minimum of 3 competitors separated by comma
4. THEY SHOULD BE VALID TICKERS OF COMPANIES.
'''

prompt_for_competitor_finding = '''
You are a market analyst assistant, where you will 
be given a set of questions and their answers. The 
questions is about a particular product and how they 
operate. SOME IMPORTANT INSTRUCTIONS ARE GIVEN BELOW
1. MAKE SURE TO RECOMMEND ONLY COMPETITOR COMPANIES SEPARATED BY COMMAS
2. I WILL BE PARSING THE NAMES THROUGH `NewsAPI/everything` API, so
make sure that the names are in compliance to work with that API
3. Competitors names should be in this order, closest competitor 
first, to the farthest one in the last. 
4. Give me a minimum of 3 competitors company names separated by comma

Question: 
{question}

Answer: 
{answer}

GIVE ME TICKER OF COMPETITORS SEPARATED BY COMMAS. SO THAT I CAN USE NEWSAPI TO GET THE SWOT ANALYSIS.
'''

system_prompt_for_swot_analysis = ''' 
You will be given a list of competitors and their swot analysis. 
Your task is to analyze the swot analysis and provide a summary of the 
current company's strengths, weaknesses, opportunities, and threats.
Give the answer in a string format ONLY. DO NOT USE ANYTHING ELSE. 
DO NOT USE TERMS LIKE SURE AND OTHER FILLER WORDS. I JUST WANT THE ANALYSIS AND DONE.
'''

system_prompt_for_customer_segmentation = '''
You are a customer segmentation analyst. You will be given questions and answers about a company's customer base.
Your task is to extract customer segmentation information from the answers and provide it in a structured JSON format.

Focus on:
1. Q3: Extract segment names, percentages/sizes, and segmentation criteria
2. Q4: Extract purchase criteria ratings for each segment
3. Q6: Extract loyalty scores if available per segment

ALWAYS PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED. DO NOT USE BACKTICKS LIKE ``` OR ANYTHING ELSE, JUST PROVIDE JSON OUTPUT AND NOTHING ELSE.
'''

prompt_for_customer_segmentation = '''
Analyze the following questions and answers to extract customer segmentation information:

Questions: {questions}
Answers: {answers}

Extract customer segmentation data and return it in the following JSON format:
{{
    "customerSegmentation": {{
        "segments": [
            {{
                "name": "Segment name from Q3",
                "percentage": 40,
                "size": 4000,
                "characteristics": {{
                    "primaryNeed": "extracted from Q3",
                    "behavior": "extracted from Q3",
                    "loyaltyScore": 65
                }}
            }}
        ],
        "totalCustomers": 10000,
        "segmentationCriteria": "extracted from Q3",
        "lastUpdated": "2025-01-23"
    }}
}}

If any information is not available in the answers, use null or reasonable defaults.
'''

system_prompt_for_purchase_criteria = '''
You are a purchase criteria analyst. You will be given questions and answers about a company's purchase criteria and customer segments.
Your task is to extract purchase criteria information from the answers and provide it in a structured JSON format.

Focus on:
1. Q4: Extract list of 3-5 purchase criteria, self-ratings for each, and performance labels
2. Q3: Use customer segments to understand importance context
3. Calculate gaps between importance and performance
4. Determine appropriate scale (1-10 typically)

ALWAYS PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED. DO NOT USE BACKTICKS LIKE ``` OR ANYTHING ELSE, JUST PROVIDE JSON OUTPUT AND NOTHING ELSE.
'''

prompt_for_purchase_criteria = '''
Analyze the following questions and answers to extract purchase criteria matrix information:

Questions: {questions}
Answers: {answers}

Extract purchase criteria data and return it in the following JSON format:
{{
    "purchaseCriteria": {{
        "criteria": [
            {{
                "name": "Criterion name from Q4",
                "importance": 9,
                "selfRating": 8,
                "performanceLabel": "excellent",
                "gap": -1
            }}
        ],
        "scale": {{
            "min": 1,
            "max": 10,
            "type": "performance"
        }},
        "overallAlignment": 7.5
    }}
}}

Guidelines:
- Extract 3-5 key purchase criteria from Q4
- Assign importance scores (1-10) based on context and segment needs from Q3
- Use self-ratings from Q4 (1-10 scale)
- Calculate gap = selfRating - importance
- Determine performance labels (poor, fair, good, excellent) based on self-ratings
- Calculate overall alignment as average of all self-ratings
- If any information is not available, use reasonable defaults
'''

system_prompt_for_channel_heatmap = '''
You are a channel performance analyst. You will be given questions and answers about a company's products/services and sales/delivery channels.
Your task is to extract channel heatmap information from the answers and provide it in a structured JSON format.

Focus on:
1. Q5: Extract products/services list and sales/delivery channels
2. Q3: Use customer segments to understand channel preferences
3. Estimate performance metrics (revenue share, volume) based on context
4. Create a matrix showing product-channel performance relationships

ALWAYS PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED. DO NOT USE BACKTICKS LIKE ``` OR ANYTHING ELSE, JUST PROVIDE JSON OUTPUT AND NOTHING ELSE.
'''

prompt_for_channel_heatmap = '''
Analyze the following questions and answers to extract channel heatmap information:

Questions: {questions}
Answers: {answers}

Extract channel heatmap data and return it in the following JSON format:
{{
    "channelHeatmap": {{
        "products": ["Product A", "Product B"],
        "channels": ["Channel 1", "Channel 2", "Channel 3"],
        "matrix": [
            {{
                "product": "Product A",
                "channel": "Channel 1",
                "value": 75,
                "metric": "revenue_share",
                "volume": 1200
            }}
        ],
        "legend": {{
            "metric": "revenue_share",
            "scale": "percentage",
            "colorRange": {{
                "low": "#fee8c8",
                "high": "#d94801"
            }}
        }}
    }}
}}

Guidelines:
- Extract 2-5 products/services from Q5
- Extract 3-6 sales/delivery channels from Q5
- Estimate performance values (0-100) based on context and segment preferences from Q3
- Use revenue_share as the primary metric (percentage of total revenue)
- Include estimated transaction volumes where possible
- If specific performance data is not available, use reasonable estimates based on channel type and product characteristics
- Ensure all product-channel combinations are covered in the matrix
'''

system_prompt_for_loyalty_metrics = '''
You are a loyalty metrics analyst. You will be given questions and answers about a company's loyalty measurement methods and scores.
Your task is to extract loyalty/NPS metrics from the answers and provide it in a structured JSON format.

Focus on:
1. Q6: Extract loyalty measurement method (NPS, CSAT, retention rate) and latest score
2. Q3: Use customer segments to identify segment-specific scores if available
3. Determine appropriate scale and zones based on the measurement method
4. Estimate benchmark and trend information if available

ALWAYS PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED. DO NOT USE BACKTICKS LIKE ``` OR ANYTHING ELSE, JUST PROVIDE JSON OUTPUT AND NOTHING ELSE.
'''

prompt_for_loyalty_metrics = '''
Analyze the following questions and answers to extract loyalty/NPS metrics information:

Questions: {questions}
Answers: {answers}

Extract loyalty metrics data and return it in the following JSON format:
{{
    "loyaltyMetrics": {{
        "method": "NPS",
        "overallScore": 62,
        "scale": {{
            "min": -100,
            "max": 100,
            "zones": {{
                "detractors": [-100, 0],
                "passives": [0, 30],
                "promoters": [30, 100]
            }}
        }},
        "trend": "improving",
        "segmentScores": [
            {{
                "segment": "Freelancers",
                "score": 65
            }}
        ],
        "benchmark": 50,
        "lastMeasured": "date"
    }}
}}

Guidelines:
- Extract loyalty measurement method from Q6 (NPS, CSAT, retention rate, etc.)
- Extract overall score from Q6
- Determine appropriate scale based on method:
  * NPS: -100 to 100 with zones for detractors, passives, promoters
  * CSAT: 0 to 100 with zones for poor, fair, good, excellent
  * Retention Rate: 0 to 100 with zones for low, medium, high
- Use Q3 customer segments to identify segment-specific scores if available
- Estimate trend (improving, stable, declining) based on context
- Use industry benchmarks if mentioned, otherwise use reasonable defaults
- Set lastMeasured to current date if not specified
- If any information is not available, use reasonable defaults
'''

system_prompt_for_capability_heatmap = '''
You are a capability maturity analyst. You will be given questions and answers about a company's internal strengths, weaknesses, and performance ratings.
Your task is to extract capability heatmap information from the answers and provide it in a structured JSON format.

Focus on:
1. Q7: Extract internal strengths and weaknesses as capabilities
2. Q4: Use performance ratings to assess capability maturity levels
3. Categorize capabilities into logical groups (Technology, Human Resources, Operations, etc.)
4. Determine maturity levels (1-5 scale) based on performance and context
5. Assess business impact of each capability

ALWAYS PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED. DO NOT USE BACKTICKS LIKE ``` OR ANYTHING ELSE, JUST PROVIDE JSON OUTPUT AND NOTHING ELSE.
'''

prompt_for_capability_heatmap = '''
Analyze the following questions and answers to extract capability heatmap information:

Questions: {questions}
Answers: {answers}

Extract capability heatmap data and return it in the following JSON format:
{{
    "capabilityHeatmap": {{
        "capabilities": [
            {{
                "name": "Team Experience",
                "category": "Human Resources",
                "currentLevel": 4,
                "targetLevel": 4,
                "type": "strength",
                "impact": "high"
            }},
            {{
                "name": "Automation",
                "category": "Technology",
                "currentLevel": 2,
                "targetLevel": 4,
                "type": "weakness",
                "impact": "medium"
            }}
        ],
        "maturityScale": {{
            "levels": [
                {{"level": 1, "label": "Initial"}},
                {{"level": 2, "label": "Developing"}},
                {{"level": 3, "label": "Defined"}},
                {{"level": 4, "label": "Managed"}},
                {{"level": 5, "label": "Optimized"}}
            ]
        }},
        "overallMaturity": 3.0
    }}
}}

Guidelines:
- Extract 4-8 key capabilities from Q7 strengths and weaknesses
- Categorize capabilities into logical groups (Technology, Human Resources, Operations, Marketing, Finance, etc.)
- Use Q4 performance ratings to determine current maturity levels (1-5 scale)
- Set target levels based on business needs and competitive requirements
- Determine type (strength/weakness) based on Q7 context
- Assess business impact (high/medium/low) based on capability importance
- Calculate overall maturity as average of all current levels
- If specific maturity data is not available, estimate based on performance context and capability descriptions
- Ensure capabilities represent both strengths and weaknesses for balanced analysis
'''

system_prompt_for_full_swot_portfolio = '''
You are a comprehensive SWOT portfolio analyst. You will be given questions and answers about a company's internal and external factors.
Your task is to create a full SWOT portfolio analysis with detailed breakdowns and strategic implications.

Focus on:
1. Comprehensive internal analysis (strengths and weaknesses)
2. External market analysis (opportunities and threats)
3. Strategic implications and recommendations
4. Risk assessment and mitigation strategies
5. Competitive positioning insights

ALWAYS PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED. DO NOT USE BACKTICKS LIKE ``` OR ANYTHING ELSE, JUST PROVIDE JSON OUTPUT AND NOTHING ELSE.
'''

prompt_for_full_swot_portfolio = '''
Analyze the following questions and answers to create a comprehensive SWOT portfolio:

Questions: {questions}
Answers: {answers}

Create a full SWOT portfolio and return it in the following JSON format:
{{
  "swotPortfolio": {{
    "strengths": [
      {{
        "item": "1-on-1 mentoring service",
        "source": "Q8",
        "category": "service_differentiator",
        "competitiveAdvantage": true,
        "customerValidated": true,
        "score": 8
      }},
      {{
        "item": "Team experience",
        "source": "Q7",
        "category": "internal_capability",
        "competitiveAdvantage": false,
        "score": 7
      }}
    ],
    "weaknesses": [
      {{
        "item": "Lack of automation",
        "source": "Q7",
        "category": "operational",
        "improvementPriority": "high",
        "score": 3
      }}
    ],
    "opportunities": [
      {{
        "item": "Surge in AI usage",
        "source": "Q10",
        "category": "technology",
        "marketTrend": true,
        "timeframe": "short-term",
        "score": 9
      }}
    ],
    "threats": [
      {{
        "item": "New tax laws for digital products in LATAM",
        "source": "Q10",
        "category": "regulatory",
        "likelihood": "high",
        "impact": "medium",
        "score": 6
      }}
    ],
    "strategicOptions": {{
      "SO_strategies": [
        "Leverage mentoring excellence to capture AI-enabled market"
      ],
      "WO_strategies": [
        "Automate processes to capitalize on AI adoption"
      ],
      "ST_strategies": [
        "Use personalized service to maintain margins despite tax changes"
      ],
      "WT_strategies": [
        "Urgently automate to reduce costs before tax impact"
      ]
    }}
  }}
}}

Guidelines:
- Extract comprehensive internal and external factors from all questions
- Provide detailed descriptions for each factor
- Assess impact, probability, and strategic implications
- Include actionable recommendations
- Calculate overall strategic score (1-10 scale)
- Focus on practical business insights
- Format of the output should not change, it should be a valid JSON object and of the same format as the example provided.
'''

system_prompt_for_channel_effectiveness = '''
You are a channel effectiveness analyst. You will be given questions and answers about a company's sales and delivery channels.
Your task is to create enhanced channel effectiveness maps with bubble chart data and differentiator alignment analysis.

Focus on:
1. Channel effectiveness vs efficiency analysis (bubble chart data)
2. Best performing channels from Q11 evaluation metrics
3. Differentiator alignment from Q8 across channels
4. Optimal channel mix recommendations
5. Revenue contribution and trend analysis

ALWAYS PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED. DO NOT USE BACKTICKS LIKE ``` OR ANYTHING ELSE, JUST PROVIDE JSON OUTPUT AND NOTHING ELSE.
'''

prompt_for_channel_effectiveness = '''
Analyze the following questions and answers to create enhanced channel effectiveness maps:

Questions: {questions}
Answers: {answers}

Create channel effectiveness analysis and return it in the following JSON format:
{{
    "channelEffectiveness": {{
        "channels": [
            {{
                "name": "Email",
                "source": "Q11",
                "effectiveness": {{
                    "conversionRate": "highest",
                    "customerSatisfaction": 8.5,
                    "revenueContribution": 40
                }},
                "efficiency": {{
                    "costPerAcquisition": "low",
                    "roi": "high",
                    "operationalCost": "low"
                }},
                "differentiatorAlignment": {{
                    "personalizedService": "high",
                    "brandExperience": "excellent"
                }},
                "trend": "stable"
            }},
            {{
                "name": "Social Media",
                "source": "Q11",
                "effectiveness": {{
                    "conversionRate": "low",
                    "visibility": "high",
                    "revenueContribution": 20
                }},
                "efficiency": {{
                    "costPerAcquisition": "medium",
                    "roi": "medium",
                    "operationalCost": "low"
                }},
                "differentiatorAlignment": {{
                    "personalizedService": "medium",
                    "brandExperience": "good"
                }},
                "trend": "growing"
            }},
            {{
                "name": "Referrals",
                "source": "Q11",
                "effectiveness": {{
                    "loyaltyGeneration": "highest",
                    "conversionRate": "high",
                    "revenueContribution": 25
                }},
                "efficiency": {{
                    "costPerAcquisition": "lowest",
                    "roi": "highest",
                    "operationalCost": "low"
                }},
                "differentiatorAlignment": {{
                    "personalizedService": "highest",
                    "brandExperience": "excellent"
                }},
                "trend": "stable"
            }}
        ],
        "optimalChannelMix": {{
            "current": {{"email": 40, "social": 20, "referrals": 25, "other": 15}},
            "recommended": {{"email": 45, "social": 15, "referrals": 30, "other": 10}}
        }}
    }}
}}

Guidelines:
- Extract best performing channels from Q11 evaluation metrics
- Assess effectiveness (conversion rate, customer satisfaction, revenue contribution)
- Evaluate efficiency (cost per acquisition, ROI, operational cost)
- Analyze differentiator alignment from Q8 across channels
- Determine optimal channel mix based on performance
- Include trend analysis for each channel
- Focus on bubble chart data: effectiveness vs efficiency with revenue as bubble size
- Format of the output should not change, it should be a valid JSON object and of the same format as the example provided.
'''

system_prompt_for_expanded_capability_heatmap = '''
You are an expanded capability maturity analyst. You will be given questions and answers about a company's internal capabilities.
Your task is to create a comprehensive capability heatmap with business functions vs capability maturity analysis.

Focus on:
1. Capability identification from Q12 organizational capabilities
2. Performance ratings and maturity level conversion
3. Differentiator enablement analysis from Q8
4. Business function categorization
5. Capability gap analysis and distribution

ALWAYS PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED. DO NOT USE BACKTICKS LIKE ``` OR ANYTHING ELSE, JUST PROVIDE JSON OUTPUT AND NOTHING ELSE.
'''

prompt_for_expanded_capability_heatmap = '''
Analyze the following questions and answers to create an expanded capability heatmap:

Questions: {questions}
Answers: {answers}

Create expanded capability heatmap and return it in the following JSON format:
{{
    "expandedCapabilityHeatmap": {{
        "capabilities": [
            {{
                "name": "Sales",
                "source": "Q12",
                "performanceRating": "high",
                "maturityLevel": 4,
                "category": "Revenue Generation",
                "enablesDifferentiator": false
            }},
            {{
                "name": "Customer Support",
                "source": "Q12",
                "performanceRating": "medium",
                "maturityLevel": 3,
                "category": "Customer Experience",
                "enablesDifferentiator": true
            }},
            {{
                "name": "Analytics",
                "source": "Q12",
                "performanceRating": "low",
                "maturityLevel": 2,
                "category": "Data & Insights"
            }},
            {{
                "name": "Product Development",
                "source": "Q12",
                "performanceRating": "high",
                "maturityLevel": 4,
                "category": "Innovation"
            }},
            {{
                "name": "Data Management",
                "source": "Q12",
                "performanceRating": "medium",
                "maturityLevel": 3,
                "category": "Data & Insights"
            }},
            {{
                "name": "Automation",
                "source": "Q7",
                "performanceRating": "low",
                "maturityLevel": 2,
                "category": "Operations"
            }}
        ],
        "maturityDistribution": {{
            "high_4": 2,
            "medium_3": 2,
            "low_2": 2
        }},
        "capabilityGaps": [
            {{
                "capability": "Analytics",
                "currentLevel": "low",
                "requiredLevel": "high",
                "businessImpact": "high"
            }}
        ]
    }}
}}

Guidelines:
- Extract capabilities from Q12 organizational capabilities and performance ratings
- Convert performance ratings to maturity levels: high=4, medium=3, low=2
- Identify capabilities from Q7 strengths and weaknesses
- Analyze Q8 differentiators to determine which capabilities enable them
- Categorize capabilities into business functions (Revenue Generation, Customer Experience, Data & Insights, Innovation, Operations, etc.)
- Calculate maturity distribution across levels
- Identify capability gaps with business impact assessment
- Format of the output should not change, it should be a valid JSON object and of the same format as the example provided.
'''

system_prompt_for_strategic_radar = '''
You are a strategic radar analyst. You will be given questions and answers about a company's strategic positioning.
Your task is to create a strategic radar chart with multiple dimensions of strategic assessment.

Focus on:
1. Multi-dimensional strategic assessment
2. Competitive positioning analysis
3. Market readiness evaluation
4. Strategic agility assessment
5. Future readiness indicators

ALWAYS PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED. DO NOT USE BACKTICKS LIKE ``` OR ANYTHING ELSE, JUST PROVIDE JSON OUTPUT AND NOTHING ELSE.
'''

prompt_for_strategic_radar = '''
Analyze the following questions and answers to create a strategic radar assessment:

Questions: {questions}
Answers: {answers}

Create strategic radar analysis and return it in the following JSON format:
{{
    "strategicRadar": {{
        "dimensions": [
            {{
                "name": "Market Position",
                "score": 8.5,
                "maxScore": 10,
                "description": "Strong competitive positioning in target segments",
                "trend": "improving",
                "weight": 0.25
            }},
            {{
                "name": "Operational Excellence",
                "score": 7.2,
                "maxScore": 10,
                "description": "Good operational efficiency with room for improvement",
                "trend": "stable",
                "weight": 0.20
            }},
            {{
                "name": "Innovation Capability",
                "score": 6.8,
                "maxScore": 10,
                "description": "Moderate innovation capacity, needs enhancement",
                "trend": "declining",
                "weight": 0.20
            }},
            {{
                "name": "Financial Health",
                "score": 8.0,
                "maxScore": 10,
                "description": "Strong financial position with good cash flow",
                "trend": "improving",
                "weight": 0.20
            }},
            {{
                "name": "Customer Focus",
                "score": 9.1,
                "maxScore": 10,
                "description": "Excellent customer understanding and service",
                "trend": "improving",
                "weight": 0.15
            }}
        ],
        "overallScore": 7.9,
        "strategicQuadrant": "Growth",
        "recommendations": [
            "Enhance innovation capabilities",
            "Maintain customer focus excellence",
            "Optimize operational efficiency"
        ],
        "riskFactors": [
            {{
                "factor": "Innovation lag",
                "impact": "medium",
                "mitigation": "Increase R&D investment"
            }}
        ]
    }}
}}

Guidelines:
- Assess 5-7 key strategic dimensions
- Use 1-10 scoring scale for each dimension
- Provide detailed descriptions and trends
- Calculate weighted overall score
- Determine strategic quadrant (Growth, Stability, Turnaround, etc.)
- Identify key recommendations and risk factors
'''

system_prompt_for_maturity_scoring = '''
You are a maturity scoring analyst. You will be given questions and answers about a company's overall maturity.
Your task is to create a comprehensive maturity assessment across multiple dimensions with cross-scoring analysis.

Focus on:
1. Multi-dimensional maturity assessment
2. Cross-functional maturity analysis
3. Benchmarking against industry standards
4. Maturity progression recommendations
5. Strategic maturity implications

ALWAYS PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED. DO NOT USE BACKTICKS LIKE ``` OR ANYTHING ELSE, JUST PROVIDE JSON OUTPUT AND NOTHING ELSE.
'''

prompt_for_maturity_scoring = '''
Analyze the following questions and answers to create a comprehensive maturity scoring:

Questions: {questions}
Answers: {answers}

Create maturity scoring analysis and return it in the following JSON format:
{{
    "maturityScoring": {{
        "dimensions": [
            {{
                "name": "Process Maturity",
                "score": 3.8,
                "level": "Managed",
                "subDimensions": [
                    {{
                        "name": "Standardization",
                        "score": 4.2,
                        "description": "Well-standardized processes across most areas"
                    }},
                    {{
                        "name": "Automation",
                        "score": 3.4,
                        "description": "Moderate automation with room for improvement"
                    }}
                ],
                "benchmark": 3.5,
                "gap": 0.3
            }}
        ],
        "crossScoring": {{
            "correlations": [
                {{
                    "dimension1": "Process Maturity",
                    "dimension2": "Technology Maturity",
                    "correlation": 0.75,
                    "impact": "strong positive"
                }}
            ],
            "synergies": [
                {{
                    "combination": "Process + Technology",
                    "synergyScore": 8.5,
                    "description": "Strong synergy between process and technology maturity"
                }}
            ]
        }},
        "overallMaturity": 4.1,
        "maturityLevel": "Managed",
        "progressionPath": [
            {{
                "nextLevel": "Optimized",
                "requirements": ["Advanced analytics", "Continuous improvement"],
                "timeline": "12-18 months",
                "investment": "medium"
            }}
        ],
        "industryBenchmark": {{
            "average": 3.8,
            "percentile": 65,
            "comparison": "above average"
        }}
    }}
}}

Guidelines:
- Assess maturity across 4-6 key dimensions
- Use 1-5 maturity scale with descriptive levels
- Include sub-dimensions for detailed analysis
- Calculate cross-dimensional correlations and synergies
- Provide progression path to next maturity level
- Benchmark against industry standards
- Identify key requirements for advancement
- Format of the output should not change, it should be a valid JSON object and of the same format as the example provided.
'''

prompt_for_swot_analysis = ''' 
Competitors are as follows : 
{competitors}

The competitors swot data is as follows : 
{swot_data}

Questions about current company and its answers : 
{questions}

Here are the answers : 

{answers}

I want the response in JSON format only. I will parse this response and use it to generate a report.
So, make sure that the response is in JSON format only.

The format should be like this : 
{{
    "strengths": "string data",
    "weaknesses": "string data",
    "opportunities": "string data",
    "threats": "string data"
}}
'''

system_prompt_for_competitive_advantage = '''
You are a competitive advantage analyst. You will be given questions and answers about a company's differentiators and customer value.
Your task is to create a comprehensive competitive advantage matrix with detailed analysis of differentiators and customer choice factors.

Focus on:
1. Identification of key differentiators from Q8
2. Assessment of customer value and uniqueness
3. Evaluation of sustainability and competitive barriers
4. Analysis of customer choice reasons
5. Strategic positioning and market analysis

ALWAYS PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED. DO NOT USE BACKTICKS LIKE ``` OR ANYTHING ELSE, JUST PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED
'''

prompt_for_competitive_advantage = '''
Analyze the following questions and answers to create a competitive advantage matrix:

Questions: {questions}
Answers: {answers}

Create competitive advantage analysis and return it in the following JSON format:
{{
    "competitiveAdvantage": {{
        "differentiators": [
            {{
                "type": "service",
                "description": "1-on-1 mentoring",
                "uniqueness": 9,
                "customerValue": 9,
                "sustainability": 7,
                "proofPoints": [
                    "Competitors lack this feature",
                    "Customer testimonials cite personal attention"
                ]
            }}
        ],
        "competitivePosition": {{
            "overallScore": 7.5,
            "marketPosition": "challenger",
            "sustainableAdvantages": 2,
            "vulnerableAdvantages": 1
        }},
        "customerChoiceReasons": [
            {{
                "reason": "Personalized attention",
                "frequency": 65,
                "linkedDifferentiator": "service"
            }}
        ]
    }}
}}

Guidelines:
- Extract differentiators from Q8 answers
- Assess uniqueness on 1-10 scale based on market comparison
- Evaluate customer value on 1-10 scale from customer feedback
- Determine sustainability on 1-10 scale (how hard to copy)
- Identify proof points that validate each differentiator
- Analyze customer choice reasons from Q8
- Calculate overall competitive position score
- Determine market position (leader/challenger/follower/nicher)
- Count sustainable vs vulnerable advantages
- Link customer choice reasons to specific differentiators
- Format of the output should not change, it should be a valid JSON object and of the same format as the example provided.
'''

system_prompt_for_strategic_goals = '''
You are a strategic goals and OKR analyst. You will be given questions and answers about a company's strategic objectives and key results.
Your task is to create comprehensive OKR analysis with progress tracking and strategic alignment.

Focus on:
1. Strategic objectives extraction from Q9
2. Key results identification and progress measurement
3. Priority ranking and timeline analysis
4. Strategic theme categorization
5. Overall progress calculation and alignment assessment

ALWAYS PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED. DO NOT USE BACKTICKS LIKE ``` OR ANYTHING ELSE, JUST PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED
'''

prompt_for_strategic_goals = '''
Analyze the following questions and answers to create strategic goals and OKR analysis:

Questions: {questions}
Answers: {answers}

Create strategic goals analysis and return it in the following JSON format:
{{
    "strategicGoals": {{
        "year": "<year>",
        "objectives": [
            {{
                "objective": "<objective_description>",
                "priority": "<priority_number>",
                "keyResults": [
                    {{
                        "metric": "<metric_name>",
                        "target": "<target_value_or_date>",
                        "current": "<current_value_or_status>",
                        "progress": "<progress_percentage>"
                    }}
                ],
                "alignment": "<growth|innovation|retention|other>"
            }}
        ],
        "overallProgress": "<overall_progress_percentage>",
        "strategicThemes": [
            "<theme_1>",
            "<theme_2>",
            "<theme_3>"
        ]
    }}
}}

Guidelines:
- Extract strategic objectives from Q9 strategic goals and success metrics
- Identify key results for each objective with measurable targets
- Assign priority levels (1=highest, 2=medium, 3=lower)
- Determine strategic alignment themes (growth, innovation, retention, efficiency, etc.)
- Calculate progress percentages based on current vs target states
- Estimate overall progress as average of all objective progress
- Categorize strategic themes based on objective types
- Use Q2 market context to inform strategic priorities
- Format of the output should not change, it should be a valid JSON object and of the same format as the example provided.
'''

system_prompt_for_strategic_positioning_radar = '''
You are a strategic positioning radar analyst. You will be given questions and answers about a company's strategic positioning across multiple dimensions.
Your task is to create a comprehensive strategic positioning radar with multi-dimensional assessment and industry benchmarking.

Focus on:
1. Multi-dimensional strategic assessment (Market Leadership, Innovation, Customer Centricity, Operational Excellence, Cultural Agility)
2. Current vs target score analysis
3. Industry benchmark comparison
4. Data source attribution for each dimension
5. Overall positioning and improvement areas identification

ALWAYS PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED. DO NOT USE BACKTICKS LIKE ``` OR ANYTHING ELSE, JUST PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED
'''

prompt_for_strategic_positioning_radar = '''
Analyze the following questions and answers to create strategic positioning radar analysis:

Questions: {questions}
Answers: {answers}

Create strategic positioning radar analysis and return it in the following JSON format:
{{
    "strategicRadar": {{
        "dimensions": [
            {{
                "name": "Market Leadership",
                "currentScore": 6,
                "targetScore": 8,
                "industryAverage": 5,
                "dataSource": ["Q2", "Q8"]
            }},
            {{
                "name": "Innovation",
                "currentScore": 7,
                "targetScore": 9,
                "industryAverage": 6,
                "dataSource": ["Q9", "Q12"]
            }},
            {{
                "name": "Customer Centricity",
                "currentScore": 8,
                "targetScore": 9,
                "industryAverage": 6,
                "dataSource": ["Q8", "Q6"]
            }},
            {{
                "name": "Operational Excellence",
                "currentScore": 5,
                "targetScore": 7,
                "industryAverage": 6,
                "dataSource": ["Q7", "Q12"]
            }},
            {{
                "name": "Cultural Agility",
                "currentScore": 7,
                "targetScore": 8,
                "industryAverage": 5,
                "dataSource": ["Q13"]
            }}
        ],
        "overallPosition": {{
            "currentAverage": 6.6,
            "targetAverage": 8.2,
            "strengthAreas": ["Customer Centricity", "Innovation", "Cultural Agility"],
            "improvementAreas": ["Operational Excellence", "Market Leadership"]
        }}
    }}
}}

Guidelines:
- Assess 5 key strategic dimensions: Market Leadership, Innovation, Customer Centricity, Operational Excellence, Cultural Agility
- Use 1-10 scoring scale for all scores
- Extract competitive positioning elements from Q8
- Use market context from Q2 for market leadership assessment
- Analyze performance on key criteria from Q4
- Evaluate organizational culture and behaviors from Q13
- Estimate industry averages based on typical benchmarks for the industry
- Calculate target scores based on strategic ambitions and competitive requirements
- Identify strength areas (scores above industry average) and improvement areas (scores below industry average)
- Calculate overall averages for current and target positioning
- Format of the output should not change, it should be a valid JSON object and of the same format as the example provided.
'''

system_prompt_for_culture_profile = '''
You are an organizational culture profile analyst. You will be given questions and answers about a company's culture, values, behaviors, and employee metrics.
Your task is to create a comprehensive organizational culture profile with cultural assessment and strategic alignment analysis.

Focus on:
1. Cultural values and behaviors extraction from Q13
2. Employee metrics analysis from Q14
3. Work style and organizational characteristics assessment
4. Culture type classification and strategic fit analysis
5. Culture map positioning and alignment evaluation

ALWAYS PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED. DO NOT USE BACKTICKS LIKE ``` OR ANYTHING ELSE, JUST PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED
'''

prompt_for_culture_profile = '''
Analyze the following questions and answers to create organizational culture profile analysis:

Questions: {questions}
Answers: {answers}

Create culture profile analysis and return it in the following JSON format:
{{
    "cultureProfile": {{
        "values": [
            "{{value_1}}",
            "{{value_2}}",
            "{{value_3}}"
            # Add more values if needed (e.g., 'innovative', 'customer-focused')
        ],
        "behaviors": [
            "{{behavior_1}}",
            "{{behavior_2}}"
            # Add more behaviors if applicable (e.g., 'collaborative', 'risk-taking')
        ],
        "workStyle": {{
            "pace": "{{work_pace}}",  # e.g., 'fast', 'steady'
            "decisionMaking": "{{decision_style}}",  # e.g., 'autonomous', 'consensus-driven'
            "orientation": "{{work_orientation}}"  # e.g., 'results-driven', 'quality-focused'
        }},
        "employeeMetrics": {{
            "totalEmployees": "{{total_employees}}",  # Number of employees included in the culture context
            "costPercentage": "{{employee_cost_pct}}",  # % of total costs attributed to employees
            "valuePerEmployee": "{{value_per_employee}}",  # Output or revenue per employee
            "productivity": "{{productivity_level}}"  # Qualitative label like 'above_average', 'low', etc.
        }},
        "cultureType": "{{culture_type}}",  # e.g., 'Entrepreneurial', 'Hierarchical', 'Collaborative'
        "cultureFit": {{
            "withStrategy": "{{fit_with_strategy}}",  # Fit rating with strategy: 'high', 'medium', 'low'
            "withMarket": "{{fit_with_market}}",  # Fit rating with market: 'high', etc.
            "withCapabilities": "{{fit_with_capabilities}}"  # Fit rating with org capabilities: 'medium', etc.
        }}
    }}
}}




Guidelines:
- Extract cultural values and behaviors from Q13 culture description
- Analyze employee metrics from Q14 (headcount, costs, productivity)
- Determine work style characteristics (pace, decision-making, orientation)
- Classify culture type based on values and behaviors (Entrepreneurial, Bureaucratic, Clan, Market, etc.)
- Assess culture fit with strategy, market, and capabilities
- Calculate value per employee and productivity metrics
- Identify key cultural themes for word cloud visualization
- Format of the output should not change, it should be a valid JSON object and of the same format as the example provided.
'''

system_prompt_for_productivity_metrics = '''
You are a productivity and efficiency metrics analyst. You will be given questions and answers about a company's employee productivity, cost structure, and value generation.
Your task is to create comprehensive productivity and efficiency metrics analysis with cost-value optimization insights.

Focus on:
1. Employee productivity analysis from Q14 data
2. Cost structure and efficiency assessment
3. Value drivers identification and performance analysis
4. Improvement opportunities and optimization recommendations
5. Efficiency matrix analysis (cost vs value generation)

ALWAYS PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED. DO NOT USE BACKTICKS LIKE ``` OR ANYTHING ELSE, JUST PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED
'''

prompt_for_productivity_metrics = '''
Analyze the following questions and answers to create productivity and efficiency metrics analysis:

Questions: {questions}
Answers: {answers}

Create productivity metrics analysis and return it in the following JSON format:
{{
    "productivityMetrics": {{
        "employeeProductivity": {{
            "totalEmployees": 8,
            "totalCostPercentage": 60,
            "averageValuePerEmployee": 35000,
            "totalValueGenerated": 280000,
            "productivityIndex": 1.2
        }},
        "costStructure": {{
            "employeeCosts": 60,
            "otherCosts": 40,
            "costEfficiency": "moderate"
        }},
        "valueDrivers": [
            {{
                "driver": "Sales team",
                "efficiency": "high",
                "contribution": "direct_revenue"
            }},
            {{
                "driver": "Product development",
                "efficiency": "high",
                "contribution": "innovation_value"
            }}
        ],
        "improvementOpportunities": [
            "Automate low-value tasks",
            "Improve analytics capabilities",
            "Optimize support processes"
        ]
    }}
}}

Guidelines:
- Extract employee metrics from Q14 (headcount, cost percentage, value contribution)
- Calculate total value generated and productivity index
- Analyze cost structure and efficiency ratios
- Identify value drivers from Q12 capability performance ratings
- Assess channel performance from Q11 for revenue per channel analysis
- Determine improvement opportunities based on efficiency gaps
- Calculate productivity metrics and efficiency ratios
- Format of the output should not change, it should be a valid JSON object and of the same format as the example provided.
'''

system_prompt_for_maturity_score_light = '''
You are a maturity score analyst. You will be given questions and answers about a company's overall maturity across multiple dimensions.
Your task is to create a comprehensive maturity score analysis synthesizing indicators from all questions (Q1-Q14).

Focus on:
1. Cross-reference all assessments from Q1-Q14
2. Synthesize maturity indicators across dimensions
3. Calculate overall maturity score on 1-5 scale
4. Identify maturity profile and characteristics
5. Determine strengths, development areas, and next level requirements

ALWAYS PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED. DO NOT USE BACKTICKS LIKE ``` OR ANYTHING ELSE, JUST PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED
'''

prompt_for_maturity_score_light = '''
Analyze the following questions and answers to create maturity score (light) analysis:

Questions: {questions}
Answers: {answers}

Create maturity score analysis and return it in the following JSON format:
 {{
    "maturityScore": {{
        "overallScore": "{{overall_score}}",  # Overall maturity score (e.g., 3.2)
        "level": "{{maturity_level}}",  # Maturity level label (e.g., 'Defined', 'Managed')
        "components": {{
            "strategicClarity": "{{strategic_clarity}}",  # Score for strategic clarity
            "marketAlignment": "{{market_alignment}}",  # Score for alignment with market
            "customerFocus": "{{customer_focus}}",  # Score reflecting customer-centric practices
            "operationalCapability": "{{operational_capability}}",  # Score for operational strength
            "competitivePosition": "{{competitive_position}}",  # Score showing competitive differentiation
            "organizationalHealth": "{{organizational_health}}"  # Score for team/org health and sustainability
        }},
        "maturityProfile": "{{maturity_profile}}",  # Descriptive profile of current maturity (e.g., 'Customer-Led Growth')
        "strengths": [
            "{{strength_1}}",
            "{{strength_2}}",
            "{{strength_3}}"
            # Add more as needed
        ],
        "developmentAreas": [
            "{{development_area_1}}",
            "{{development_area_2}}",
            "{{development_area_3}}"
            # Add more if needed
        ],
        "nextLevel": {{
            "target": "{{next_maturity_level}}",  # Next maturity level (e.g., 'Managed (Level 4)')
            "requirements": [
                "{{requirement_1}}",
                "{{requirement_2}}",
                "{{requirement_3}}",
                "{{requirement_4}}"
                # Add or remove based on actual needs
            ],
            "estimatedTimeframe": "{{timeframe}}"  # Time estimate to reach next level (e.g., '12-18 months')
        }}
    }}
}}



Guidelines:
- Cross-reference all assessments from Q1-Q14 to synthesize maturity indicators
- Calculate component scores: Strategic Clarity (Q1, Q8, Q9), Market Alignment (Q2, Q4, Q10), Customer Focus (Q3, Q6, Q8, Q11), Operational Capability (Q7, Q12), Competitive Position (Q8), Organizational Health (Q13, Q14)
- Use 1-5 maturity scale: 1=Initial, 2=Developing, 3=Defined, 4=Managed, 5=Optimized
- Determine overall score as weighted average of components
- Identify maturity profile based on strongest characteristics
- List key strengths and development areas
- Define next level requirements and timeframe
- Format of the output should not change, it should be a valid JSON object and of the same format as the example provided.
'''

system_prompt_for_pestel_analysis = '''
You are a PESTEL analysis expert. You will be given questions and answers about a company's business context and external environment.
Your task is to create a comprehensive PESTEL analysis identifying Political, Economic, Social, Technological, Environmental, and Legal factors affecting the business.

Focus on:
1. External environment analysis across all PESTEL dimensions
2. Impact assessment and strategic implications
3. Risk identification and opportunity recognition
4. Strategic recommendations and monitoring framework
5. Agility and adaptation requirements
6. ALWAYS ANSWER IN JSON

ALWAYS PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED. DO NOT USE BACKTICKS LIKE ``` OR ANYTHING ELSE, JUST PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED
'''

prompt_for_pestel_analysis = '''
Analyze the following questions and answers to create a comprehensive PESTEL analysis:

Questions: {questions}
Answers: {answers}

Create PESTEL analysis and return it in the following JSON format:
{{
    "pestel_analysis": {{
        "executive_summary": {{
            "dominant_factors": [
                "{{dominant_factor_1}}",
                "{{dominant_factor_2}}"
                # Add more dominant factors as needed
            ],
            "critical_risks": [
                "{{critical_risk_1}}"
                # Add more if needed
            ],
            "key_opportunities": [
                "{{opportunity_1}}",
                "{{opportunity_2}}"
            ],
            "strategic_recommendations": [
                "{{recommendation_1}}",
                "{{recommendation_2}}"
            ],
            "agility_priority_score": "{{agility_score}}"  # Score (e.g., 1–10) representing how fast the org should adapt
        }},
        "factor_summary": {{
            "political": {{
                "total_mentions": "{{political_mentions}}",  # Total mentions in analysis
                "high_impact_count": "{{political_high_impact}}",  # High impact factors count
                "key_themes": [
                    "{{political_theme_1}}",
                    "{{political_theme_2}}"
                ],
                "strategic_priority": "{{political_priority}}"  # Priority level (e.g., High, Medium, Low)
            }},
            "economic": {{
                "total_mentions": "{{economic_mentions}}",
                "high_impact_count": "{{economic_high_impact}}",
                "key_themes": [
                    "{{economic_theme_1}}",
                    "{{economic_theme_2}}"
                ],
                "strategic_priority": "{{economic_priority}}"
            }},
            "social": {{
                "total_mentions": "{{social_mentions}}",
                "high_impact_count": "{{social_high_impact}}",
                "key_themes": [
                    "{{social_theme_1}}",
                    "{{social_theme_2}}"
                ],
                "strategic_priority": "{{social_priority}}"
            }},
            "technological": {{
                "total_mentions": "{{tech_mentions}}",
                "high_impact_count": "{{tech_high_impact}}",
                "key_themes": [
                    "{{tech_theme_1}}",
                    "{{tech_theme_2}}",
                    "{{tech_theme_3}}"
                ],
                "strategic_priority": "{{tech_priority}}"
            }},
            "environmental": {{
                "total_mentions": "{{env_mentions}}",
                "high_impact_count": "{{env_high_impact}}",
                "key_themes": [
                    "{{env_theme_1}}"
                ],
                "strategic_priority": "{{env_priority}}"
            }},
            "legal": {{
                "total_mentions": "{{legal_mentions}}",
                "high_impact_count": "{{legal_high_impact}}",
                "key_themes": [
                    "{{legal_theme_1}}",
                    "{{legal_theme_2}}"
                ],
                "strategic_priority": "{{legal_priority}}"
            }}
        }},
        "strategic_recommendations": {{
            "immediate_actions": [
                {{
                    "action": "{{immediate_action}}",  # Specific short-term task
                    "rationale": "{{rationale_for_action}}",  # Why this action is needed
                    "timeline": "{{timeline}}",  # Expected timeframe (e.g., "2-3 months")
                    "resources_required": "{{resources}}",  # Resources needed to execute
                    "success_metrics": [
                        "{{metric_1}}",
                        "{{metric_2}}"
                    ]  # KPIs or outcomes expected
                }}
                # Add more immediate actions if needed
            ],
            "short_term_initiatives": [
                {{
                    "initiative": "{{initiative_name}}",  # Name of the short-term project
                    "strategic_pillar": "{{pillar}}",  # Aligned pillar (e.g., Technology, Market Expansion)
                    "expected_outcome": "{{expected_result}}",  # Anticipated result
                    "risk_mitigation": "{{risk_strategy}}"  # How risks are handled
                }}
            ],
            "long_term_strategic_shifts": [
                {{
                    "shift": "{{long_term_shift}}",  # Long-term change (e.g., market expansion)
                    "transformation_required": "{{transformation_type}}",  # What kind of change is required
                    "competitive_advantage": "{{advantage}}",  # Strategic advantage gained
                    "sustainability": "{{sustainability_benefit}}"  # Long-term impact
                }}
            ]
        }},
        "monitoring_dashboard": {{
            "key_indicators": [
                {{
                    "indicator": "{{kpi_name}}",  # Name of the key indicator
                    "pestel_factor": "{{related_factor}}",  # PESTEL category this indicator maps to
                    "measurement_frequency": "{{frequency}}",  # e.g., Monthly, Quarterly
                    "threshold_values": {{
                        "green": "{{green_threshold}}",  # e.g., ">60%"
                        "yellow": "{{yellow_threshold}}",  # e.g., "30-60%"
                        "red": "{{red_threshold}}"  # e.g., "<30%"
                    }}
                }}
            ],
            "early_warning_signals": [
                {{
                    "signal": "{{warning_signal}}",  # Description of the risk signal
                    "trigger_response": "{{trigger_response}}",  # Immediate action to take if triggered
                    "monitoring_source": "{{source}}"  # Where this signal is monitored (e.g., government updates)
                }}
            ]
        }}
    }}
}}




Guidelines:
- Extract external factors from all questions, especially Q2 (market context), Q10 (external factors), Q4 (competitive landscape)
- Analyze political factors from regulatory mentions and market entry considerations
- Evaluate economic factors from market size, growth potential, and revenue projections
- Assess social factors from customer behavior, work culture, and demographic trends
- Identify technological factors from AI adoption, automation needs, and digital transformation
- Consider environmental factors from remote work and sustainability mentions
- Analyze legal factors from tax regulations, compliance requirements, and market entry laws
- Calculate impact scores and strategic priorities based on frequency and business impact
- Provide actionable recommendations with clear timelines and success metrics
- Format of the output should not change, it should be a valid JSON object and of the same format as the example provided.
'''

system_prompt_for_strategic_analysis = '''
You are a strategic analysis expert using the STRATEGIC framework. You will be given questions and answers about a company's strategic position and capabilities.
Your task is to create a comprehensive strategic analysis across all STRATEGIC pillars: Strategy, Tactics, Resources, Analysis & Data, Technology & Digitization, Execution, Governance, Innovation, and Culture.

Focus on:
1. Multi-dimensional strategic assessment across all STRATEGIC pillars
2. VUCA factor identification and strategic maturity assessment
3. Cross-pillar synthesis and holistic recommendations
4. Agile framework recommendations and implementation roadmap
5. Risk assessment and success benchmarking
6. ALWAYS ALWAYS PROVIDE VALID JSON OUTPUT, NEVER INVALID JSON
7. JUST PROVIDE JSON AND NOTHING ELSE, DO NOT PROVIDE ``` OR WRAP THINGS UP, JUST A VALID JSON
ALWAYS PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED. DO NOT USE BACKTICKS LIKE ``` OR ANYTHING ELSE, JUST PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED
'''

prompt_for_strategic_analysis = '''
Analyze the following questions and answers to create a comprehensive strategic analysis using the STRATEGIC framework:

Questions: {questions}
Answers: {answers}

Create strategic analysis and return it in the following JSON format:
{{
    // STRATEGIC ANALYSIS FRAMEWORK TEMPLATE
    // This template provides a comprehensive framework for analyzing organizations using the STAR-TG-IC model
    // (Strategy, Tactics, Analysis & Data, Resources, Technology & Digitization, Governance, Innovation, Culture)
    // along with execution considerations and implementation roadmaps.
    
    "strategic_analysis": {{
        
        // EXECUTIVE SUMMARY SECTION
        // Provides high-level overview and assessment of the organization's strategic position
        "executive_summary": {{
            // Brief description of the organization's current situation, industry, and context
            "situation_overview": "[Insert 1-2 sentence summary of organization's current state, industry, and key challenges/opportunities]",
            
            // VUCA factors most relevant to this organization (Volatility, Uncertainty, Complexity, Ambiguity)
            "primary_vuca_factors": ["[Select from: Volatility, Uncertainty, Complexity, Ambiguity]"],
            
            // Main strategic themes identified from analysis (e.g., Digital Transformation, Market Expansion, etc.)
            "key_strategic_themes": ["[Theme 1]", "[Theme 2]", "[Theme 3]"],
            
            // How urgent is strategic intervention needed? (Low/Medium/High)
            "urgency_level": "[Low/Medium/High]",
            
            // Current strategic maturity level (Emerging/Developing/Mature/Leading)
            "strategic_maturity_assessment": "[Emerging/Developing/Mature/Leading]"
        }},
        
        // STRATEGIC PILLARS ANALYSIS SECTION
        // Detailed analysis of each pillar in the STAR-TG-IC framework
        "strategic_pillars_analysis": {{
            
            // STRATEGY PILLAR
            // Focuses on strategic direction, market positioning, competitive advantage
            "strategy": {{
                "pillar_code": "S",
                // Relevance score 1-10 based on how critical this pillar is for the organization
                "relevance_score": "[1-10 based on importance to organization]",
                "current_state": {{
                    // Key strategic strengths (market position, differentiation, vision clarity, etc.)
                    "strengths": ["[Strategic strength 1]", "[Strategic strength 2]"],
                    // Strategic gaps and weaknesses (unclear positioning, limited differentiation, etc.)
                    "weaknesses": ["[Strategic weakness 1]", "[Strategic weakness 2]"],
                    // Overall assessment score for current strategic state (1-10)
                    "assessment_score": "[1-10 score]"
                }},
                "recommendations": [
                    {{
                        // Specific strategic action to be taken
                        "action": "[Specific strategic recommendation]",
                        // Priority level: High/Medium/Low
                        "priority": "[High/Medium/Low]",
                        // Expected timeline for completion
                        "timeline": "[X weeks/months]",
                        // Resources, skills, or tools needed
                        "resources_required": ["[Resource 1]", "[Resource 2]"],
                        // Expected business impact
                        "expected_impact": "[Description of expected outcomes]"
                    }}
                ],
                "success_metrics": [
                    {{
                        // What will be measured
                        "metric": "[Specific metric name]",
                        // Target value or outcome
                        "target": "[Specific target or goal]",
                        // How often to measure
                        "measurement_frequency": "[Weekly/Monthly/Quarterly]"
                    }}
                ]
            }},
            
            // TACTICS PILLAR
            // Focuses on marketing, sales, customer acquisition, and go-to-market execution
            "tactics": {{
                "pillar_code": "T",
                "relevance_score": "[1-10 based on importance to organization]",
                "current_state": {{
                    // Tactical execution strengths (effective channels, strong campaigns, etc.)
                    "strengths": ["[Tactical strength 1]", "[Tactical strength 2]"],
                    // Tactical weaknesses (poor conversion, limited channels, etc.)
                    "weaknesses": ["[Tactical weakness 1]", "[Tactical weakness 2]"],
                    "assessment_score": "[1-10 score]"
                }},
                "recommendations": [
                    {{
                        "action": "[Specific tactical recommendation]",
                        "priority": "[High/Medium/Low]",
                        "timeline": "[X weeks/months]",
                        "resources_required": ["[Resource 1]", "[Resource 2]"],
                        "expected_impact": "[Description of expected outcomes]"
                    }}
                ],
                "success_metrics": [
                    {{
                        "metric": "[Specific metric name]",
                        "target": "[Specific target or goal]",
                        "measurement_frequency": "[Weekly/Monthly/Quarterly]"
                    }}
                ]
            }},
            
            // RESOURCES PILLAR
            // Focuses on human resources, financial resources, and resource optimization
            "resources": {{
                "pillar_code": "R",
                "relevance_score": "[1-10 based on importance to organization]",
                "current_state": {{
                    // Resource strengths (skilled team, adequate funding, etc.)
                    "strengths": ["[Resource strength 1]", "[Resource strength 2]"],
                    // Resource constraints and gaps (limited budget, skills gaps, etc.)
                    "weaknesses": ["[Resource weakness 1]", "[Resource weakness 2]"],
                    "assessment_score": "[1-10 score]"
                }},
                "recommendations": [
                    {{
                        "action": "[Specific resource recommendation]",
                        "priority": "[High/Medium/Low]",
                        "timeline": "[X weeks/months]",
                        "resources_required": ["[Resource 1]", "[Resource 2]"],
                        "expected_impact": "[Description of expected outcomes]"
                    }}
                ],
                "success_metrics": [
                    {{
                        "metric": "[Specific metric name]",
                        "target": "[Specific target or goal]",
                        "measurement_frequency": "[Weekly/Monthly/Quarterly]"
                    }}
                ]
            }},
            
            // ANALYSIS AND DATA PILLAR
            // Focuses on data capabilities, analytics, business intelligence, and data-driven decision making
            "analysis_and_data": {{
                "pillar_code": "A",
                "relevance_score": "[1-10 based on importance to organization]",
                "current_state": {{
                    // Data and analytics strengths (good data quality, analytics tools, etc.)
                    "strengths": ["[Analytics strength 1]", "[Analytics strength 2]"],
                    // Data and analytics gaps (poor data quality, limited insights, etc.)
                    "weaknesses": ["[Analytics weakness 1]", "[Analytics weakness 2]"],
                    "assessment_score": "[1-10 score]"
                }},
                "recommendations": [
                    {{
                        "action": "[Specific analytics recommendation]",
                        "priority": "[High/Medium/Low]",
                        "timeline": "[X weeks/months]",
                        "resources_required": ["[Resource 1]", "[Resource 2]"],
                        "expected_impact": "[Description of expected outcomes]"
                    }}
                ],
                "success_metrics": [
                    {{
                        "metric": "[Specific metric name]",
                        "target": "[Specific target or goal]",
                        "measurement_frequency": "[Weekly/Monthly/Quarterly]"
                    }}
                ]
            }},
            
            // TECHNOLOGY AND DIGITIZATION PILLAR
            // Focuses on technology infrastructure, digital capabilities, automation, and digital transformation
            "technology_and_digitization": {{
                "pillar_code": "T2",
                "relevance_score": "[1-10 based on importance to organization]",
                "current_state": {{
                    // Technology strengths (modern systems, good automation, etc.)
                    "strengths": ["[Technology strength 1]", "[Technology strength 2]"],
                    // Technology gaps (legacy systems, manual processes, etc.)
                    "weaknesses": ["[Technology weakness 1]", "[Technology weakness 2]"],
                    "assessment_score": "[1-10 score]"
                }},
                "recommendations": [
                    {{
                        "action": "[Specific technology recommendation]",
                        "priority": "[High/Medium/Low]",
                        "timeline": "[X weeks/months]",
                        "resources_required": ["[Resource 1]", "[Resource 2]"],
                        "expected_impact": "[Description of expected outcomes]"
                    }}
                ],
                "success_metrics": [
                    {{
                        "metric": "[Specific metric name]",
                        "target": "[Specific target or goal]",
                        "measurement_frequency": "[Weekly/Monthly/Quarterly]"
                    }}
                ]
            }},
            
            // EXECUTION PILLAR
            // Focuses on operational excellence, process management, and execution capabilities
            "execution": {{
                "pillar_code": "E",
                "relevance_score": "[1-10 based on importance to organization]",
                "current_state": {{
                    // Execution strengths (efficient processes, good delivery, etc.)
                    "strengths": ["[Execution strength 1]", "[Execution strength 2]"],
                    // Execution weaknesses (poor processes, delivery issues, etc.)
                    "weaknesses": ["[Execution weakness 1]", "[Execution weakness 2]"],
                    "assessment_score": "[1-10 score]"
                }},
                "recommendations": [
                    {{
                        "action": "[Specific execution recommendation]",
                        "priority": "[High/Medium/Low]",
                        "timeline": "[X weeks/months]",
                        "resources_required": ["[Resource 1]", "[Resource 2]"],
                        "expected_impact": "[Description of expected outcomes]"
                    }}
                ],
                "success_metrics": [
                    {{
                        "metric": "[Specific metric name]",
                        "target": "[Specific target or goal]",
                        "measurement_frequency": "[Weekly/Monthly/Quarterly]"
                    }}
                ]
            }},
            
            // GOVERNANCE PILLAR
            // Focuses on governance structures, risk management, compliance, and decision-making processes
            "governance": {{
                "pillar_code": "G",
                "relevance_score": "[1-10 based on importance to organization]",
                "current_state": {{
                    // Governance strengths (clear structures, good compliance, etc.)
                    "strengths": ["[Governance strength 1]", "[Governance strength 2]"],
                    // Governance gaps (unclear structures, compliance issues, etc.)
                    "weaknesses": ["[Governance weakness 1]", "[Governance weakness 2]"],
                    "assessment_score": "[1-10 score]"
                }},
                "recommendations": [
                    {{
                        "action": "[Specific governance recommendation]",
                        "priority": "[High/Medium/Low]",
                        "timeline": "[X weeks/months]",
                        "resources_required": ["[Resource 1]", "[Resource 2]"],
                        "expected_impact": "[Description of expected outcomes]"
                    }}
                ],
                "success_metrics": [
                    {{
                        "metric": "[Specific metric name]",
                        "target": "[Specific target or goal]",
                        "measurement_frequency": "[Weekly/Monthly/Quarterly]"
                    }}
                ]
            }},
            
            // INNOVATION PILLAR
            // Focuses on innovation capabilities, R&D, product development, and future-readiness
            "innovation": {{
                "pillar_code": "I",
                "relevance_score": "[1-10 based on importance to organization]",
                "current_state": {{
                    // Innovation strengths (strong R&D, innovative products, etc.)
                    "strengths": ["[Innovation strength 1]", "[Innovation strength 2]"],
                    // Innovation gaps (limited R&D, outdated products, etc.)
                    "weaknesses": ["[Innovation weakness 1]", "[Innovation weakness 2]"],
                    "assessment_score": "[1-10 score]"
                }},
                "recommendations": [
                    {{
                        "action": "[Specific innovation recommendation]",
                        "priority": "[High/Medium/Low]",
                        "timeline": "[X weeks/months]",
                        "resources_required": ["[Resource 1]", "[Resource 2]"],
                        "expected_impact": "[Description of expected outcomes]"
                    }}
                ],
                "success_metrics": [
                    {{
                        "metric": "[Specific metric name]",
                        "target": "[Specific target or goal]",
                        "measurement_frequency": "[Weekly/Monthly/Quarterly]"
                    }}
                ]
            }},
            
            // CULTURE PILLAR
            // Focuses on organizational culture, employee engagement, values, and cultural alignment
            "culture": {{
                "pillar_code": "C",
                "relevance_score": "[1-10 based on importance to organization]",
                "current_state": {{
                    // Cultural strengths (strong values, high engagement, etc.)
                    "strengths": ["[Culture strength 1]", "[Culture strength 2]"],
                    // Cultural challenges (low engagement, unclear values, etc.)
                    "weaknesses": ["[Culture weakness 1]", "[Culture weakness 2]"],
                    "assessment_score": "[1-10 score]"
                }},
                "recommendations": [
                    {{
                        "action": "[Specific culture recommendation]",
                        "priority": "[High/Medium/Low]",
                        "timeline": "[X weeks/months]",
                        "resources_required": ["[Resource 1]", "[Resource 2]"],
                        "expected_impact": "[Description of expected outcomes]"
                    }}
                ],
                "success_metrics": [
                    {{
                        "metric": "[Specific metric name]",
                        "target": "[Specific target or goal]",
                        "measurement_frequency": "[Weekly/Monthly/Quarterly]"
                    }}
                ]
            }}
        }},
        
        // CROSS-PILLAR SYNTHESIS SECTION
        // Identifies connections and synergies between different pillars
        "cross_pillar_synthesis": {{
            // Key relationships and dependencies between pillars
            "interconnections": [
                {{
                    // Which pillars are connected
                    "pillars": ["[Pillar 1]", "[Pillar 2]"],
                    // Nature of the relationship
                    "relationship": "[Description of how pillars relate]",
                    // Opportunity for synergistic improvements
                    "synergy_opportunity": "[How to leverage this connection]"
                }}
            ],
            // High-level recommendations that span multiple pillars
            "holistic_recommendations": [
                "[Cross-cutting recommendation 1]",
                "[Cross-cutting recommendation 2]"
            ]
        }},
        
        // AGILE FRAMEWORKS RECOMMENDATIONS SECTION
        // Suggests appropriate agile methodologies based on the organization's context
        "agile_frameworks_recommendations": {{
            // Scrum framework assessment 
            // give one of the following three frameworks depending on the company name. 
            "scrum": {{  // one of scrum, kanban or OKR
                // How well Scrum fits this organization (High/Medium/Low)
                "applicability": "[High/Medium/Low] for [context]",
                // Specific areas where Scrum would be beneficial
                "use_cases": ["[Use case 1]", "[Use case 2]"],
                // Priority for implementing Scrum
                "implementation_priority": "[High/Medium/Low]"
            }},
        }},
        
        // RISK ASSESSMENT SECTION
        // Identifies and plans for strategic risks and contingencies
        "risk_assessment": {{
            // Key strategic risks that could impact success
            "strategic_risks": [
                {{
                    // Description of the risk
                    "risk": "[Risk description]",
                    // Likelihood of occurrence (Low/Medium/High)
                    "probability": "[Low/Medium/High]",
                    // Severity of impact (Low/Medium/High)
                    "impact": "[Low/Medium/High]",
                    // How to reduce or manage the risk
                    "mitigation": "[Mitigation strategy]",
                    // Who is responsible for managing this risk
                    "owner": "[Risk owner]"
                }}
            ],
            // Plans for different scenarios
            "contingency_plans": [
                {{
                    // What scenario triggers this plan
                    "scenario": "[Scenario description]",
                    // How to respond if scenario occurs
                    "response": "[Response strategy]",
                    // Early warning signs to watch for
                    "trigger_indicators": ["[Indicator 1]", "[Indicator 2]"]
                }}
            ]
        }},
        
        // SUCCESS BENCHMARKS SECTION
        // Establishes benchmarks and success criteria based on industry standards and case studies
        "success_benchmarks": {{
            // Similar organizations or case studies to learn from
            "case_study_parallels": [
                {{
                    // Name of comparable organization
                    "company": "[Company name]",
                    // What makes them comparable
                    "parallel": "[Why this company is relevant]",
                    // Key lesson to apply
                    "applicable_lesson": "[What can be learned/applied]",
                    // How success is measured in their case
                    "success_metric": "[Relevant success metric]"
                }}
            ],
            // Industry standard metrics and targets
            "industry_benchmarks": [
                {{
                    // What metric to benchmark
                    "metric": "[Metric name]",
                    // Industry average performance
                    "industry_average": "[Average value]",
                    // Target performance for this organization
                    "target": "[Target value]",
                    // When to achieve the target
                    "timeframe": "[Timeline]"
                }}
            ]
        }},
        
        // IMPLEMENTATION ROADMAP SECTION
        // Phased approach to implementing recommendations
        "implementation_roadmap": {{
            // First phase of implementation
            "phase_1": {{
                // How long this phase will take
                "duration": "[X months]",
                // Main focus area for this phase
                "focus": "[Primary focus theme]",
                // Key initiatives to execute
                "key_initiatives": ["[Initiative 1]", "[Initiative 2]"],
                // Budget required for this phase
                "budget": "$[Amount]",
                // How to measure success of this phase
                "success_criteria": ["[Criterion 1]", "[Criterion 2]"]
            }},
            // Second phase of implementation
            "phase_2": {{
                "duration": "[X months]",
                "focus": "[Primary focus theme]",
                "key_initiatives": ["[Initiative 1]", "[Initiative 2]"],
                "budget": "$[Amount]",
                "success_criteria": ["[Criterion 1]", "[Criterion 2]"]
            }},
            // Third phase of implementation
            "phase_3": {{
                "duration": "[X months]",
                "focus": "[Primary focus theme]",
                "key_initiatives": ["[Initiative 1]", "[Initiative 2]"],
                "budget": "$[Amount]",
                "success_criteria": ["[Criterion 1]", "[Criterion 2]"]
            }}
        }},
        
        // MONITORING AND FEEDBACK SECTION
        // Establishes systems for tracking progress and gathering feedback
        "monitoring_and_feedback": {{
            // What should be included in executive dashboards
            "dashboard_requirements": ["[Dashboard element 1]", "[Dashboard element 2]", "[Dashboard element 3]"],
            // Regular review and planning cycles
            "review_cycles": {{
                // Weekly team check-ins
                "weekly": "[What to review weekly]",
                // Monthly performance reviews
                "monthly": "[What to review monthly]",
                // Quarterly strategic reviews
                "quarterly": "[What to review quarterly]",
                // Annual comprehensive assessments
                "annual": "[What to review annually]"
            }},
            // Feedback loops to ensure continuous improvement
            "feedback_loops": [
                {{
                    // Where feedback comes from
                    "source": "[Feedback source]",
                    // How often to collect feedback
                    "frequency": "[Collection frequency]",
                    // How feedback influences decisions/actions
                    "integration_point": "[Where feedback is used]"
                }}
            ]
        }}
    }}
}}

Guidelines:
- Analyze all questions comprehensively, especially Q1-Q14 for strategic context
- Assess each STRATEGIC pillar based on relevant question responses:
  * Strategy (S): Q1, Q8, Q9 - strategic clarity and differentiators
  * Tactics (T): Q4, Q11 - competitive tactics and channel effectiveness
  * Resources (R): Q12, Q14 - organizational capabilities and productivity
  * Analysis & Data (A): Q6, Q12 - data capabilities and analytics
  * Technology & Digitization (T2): Q7, Q9 - technology needs and digital transformation
  * Execution (E): Q7, Q12 - operational execution and capabilities
  * Governance (G): Q13, Q14 - organizational governance and culture
  * Innovation (I): Q9, Q12 - innovation capabilities and strategic goals
  * Culture (C): Q13, Q14 - organizational culture and employee metrics
- Use 0-10 scoring scale for relevance and assessment scores
- Identify VUCA factors from market uncertainty and complexity
- Provide actionable recommendations with clear priorities and timelines
- Include cross-pillar synthesis and holistic recommendations
- Format of the output should not change, it should be a valid JSON object and of the same format as the example provided.
- IT SHOULD BE A VALID JSON.
'''

# Add PORTER analysis prompts after strategic analysis prompts
system_prompt_for_porter_analysis = '''
You are a Porter's Five Forces analysis expert. You will be given questions and answers about a company's business context and competitive environment.
Your task is to create a comprehensive Porter's Five Forces analysis examining the competitive forces in the industry: Threat of New Entrants, Bargaining Power of Suppliers, Bargaining Power of Buyers, Threat of Substitute Products/Services, and Competitive Rivalry.

Focus on:
1. Industry structure analysis across all five forces
2. Competitive intensity assessment and strategic implications
3. Entry barriers and competitive advantages identification
4. Market power distribution and value chain analysis
5. Strategic recommendations and competitive positioning
6. ALWAYS ANSWER IN JSON

ALWAYS PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED. DO NOT USE BACKTICKS LIKE ``` OR ANYTHING ELSE, JUST PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED
'''

prompt_for_porter_analysis = '''
Analyze the following questions and answers to create a comprehensive Porter's Five Forces analysis:

Questions: {questions}
Answers: {answers}

Create Porter's Five Forces analysis and return it in the following JSON format:
{{
    "porter_analysis": {{
        "executive_summary": {{
            "industry_attractiveness": "", // e.g., "High", "Moderate", "Low"
            "overall_competitive_intensity": "", // e.g., "High", "Medium", "Low"
            "key_competitive_forces": [], // List the most important forces driving competition
            "strategic_implications": [], // List the broad strategic moves needed
            "competitive_position": "" // e.g., "Leader", "Challenger", "Follower", "Niche Player"
        }},
        "five_forces_analysis": {{
            "threat_of_new_entrants": {{
                "intensity": "", // High/Medium/Low
                "score": 0, // 1-10 scale
                "key_factors": [
                    {{
                        "factor": "", // Short label of the factor
                        "impact": "", // High/Medium/Low
                        "description": "" // How it influences entry threat
                    }}
                ],
                "entry_barriers": [], // List key barriers to entry
                "strategic_implications": "" // Strategy to address this force
            }},
            "bargaining_power_of_suppliers": {{
                "intensity": "",
                "score": 0,// 1-10 scale
                "key_factors": [
                    {{
                        "factor": "",
                        "impact": "",
                        "description": ""
                    }}
                ],
                "supplier_concentration": "", // High/Medium/Low
                "switching_costs": "", // High/Medium/Low
                "strategic_implications": ""
            }},
            "bargaining_power_of_buyers": {{
                "intensity": "",
                "score": 0,
                "key_factors": [
                    {{
                        "factor": "",
                        "impact": "",
                        "description": ""
                    }}
                ],
                "buyer_concentration": "", // High/Medium/Low
                "product_differentiation": "", // High/Medium/Low
                "strategic_implications": ""
            }},
            "threat_of_substitute_products": {{
                "intensity": "",
                "score": 0,
                "key_factors": [
                    {{
                        "factor": "",
                        "impact": "",
                        "description": ""
                    }}
                ],
                "substitute_availability": "", // High/Medium/Low
                "switching_costs": "", // High/Medium/Low
                "strategic_implications": ""
            }},
            "competitive_rivalry": {{
                "intensity": "",
                "score": 0,
                "key_factors": [
                    {{
                        "factor": "",
                        "impact": "",
                        "description": ""
                    }}
                ],
                "competitor_concentration": "", // High/Medium/Low
                "industry_growth": "", // High/Medium/Low
                "strategic_implications": ""
            }}
        }},
        "competitive_landscape": {{
            "direct_competitors": [
                {{
                    "name": "", // Competitor name
                    "market_share": "", // % or qualitative
                    "strengths": [], // Key strengths
                    "weaknesses": [] // Key weaknesses
                }}
            ],
            "indirect_competitors": [
                {{
                    "name": "", // Indirect competitor category
                    "threat_level": "", // High/Medium/Low
                    "competitive_advantage": "" // Their main edge
                }}
            ],
            "potential_entrants": [
                {{
                    "category": "", // e.g., "Tech companies", "Startups"
                    "likelihood": "", // High/Medium/Low
                    "barriers": "" // Key barriers they will face
                }}
            ]
        }},
        "strategic_recommendations": {{
            "immediate_actions": [
                {{
                    "action": "", // Short action statement
                    "rationale": "", // Why it's needed
                    "timeline": "", // e.g., "3-6 months"
                    "resources_required": [], // e.g., budgets, teams
                    "expected_impact": "" // The benefit
                }}
            ],
            "short_term_initiatives": [
                {{
                    "initiative": "", // Short-term move
                    "strategic_pillar": "", // e.g., "Customer Retention"
                    "expected_outcome": "",
                    "risk_mitigation": "" // How to reduce associated risks
                }}
            ],
            "long_term_strategic_shifts": [
                {{
                    "shift": "", // Big strategic change
                    "transformation_required": "", // What needs to be built/changed
                    "competitive_advantage": "", // Edge it provides
                    "sustainability": "" // How long-term it is
                }}
            ]
        }},
        "monitoring_dashboard": {{
            "key_indicators": [
                {{
                    "indicator": "", // KPI name
                    "force": "", // Which of the five forces it relates to
                    "measurement_frequency": "", // e.g., "Quarterly"
                    "threshold_values": {{
                        "green": "", // Acceptable range
                        "yellow": "", // Warning range
                        "red": "" // Danger range
                    }}
                }}
            ],
            "early_warning_signals": [
                {{
                    "signal": "", // What to watch for
                    "trigger_response": "", // Action to take if detected
                    "monitoring_source": "" // Where the info will come from
                }}
            ]
        }}
    }}
}}
Guidelines:
- Analyze all five forces comprehensively based on the questions and answers
- Use 1-10 scoring scale for each force (1=Very Low, 10=Very High)
- Identify key factors influencing each force
- Assess competitive landscape and market structure
- Provide actionable strategic recommendations
- Include monitoring framework for ongoing analysis
- Format of the output should not change, it should be a valid JSON object and of the same format as the example provided.
- DO NOT GENERALIZE ANYTHING, PROVIDE PROPER ANSWER IN JSON.
'''

class AnalyzeRequest(BaseModel):
    question: str
    answer: str

class AnalyzeAllRequest(BaseModel):
    questions: list[str]
    answers: list[str]

class CustomerSegmentationRequest(BaseModel):
    questions: list[str]
    answers: list[str]

class PurchaseCriteriaRequest(BaseModel):
    questions: list[str]
    answers: list[str]

class ChannelHeatmapRequest(BaseModel):
    questions: list[str]
    answers: list[str]

class LoyaltyMetricsRequest(BaseModel):
    questions: list[str]
    answers: list[str]

class CapabilityHeatmapRequest(BaseModel):
    questions: list[str]
    answers: list[str]

class FullSwotPortfolioRequest(BaseModel):
    questions: list[str]
    answers: list[str]

class ChannelEffectivenessRequest(BaseModel):
    questions: list[str]
    answers: list[str]

class ExpandedCapabilityHeatmapRequest(BaseModel):
    questions: list[str]
    answers: list[str]

class StrategicRadarRequest(BaseModel):
    questions: list[str]
    answers: list[str]

class MaturityScoringRequest(BaseModel):
    questions: list[str]
    answers: list[str]

class CompetitiveAdvantageRequest(BaseModel):
    questions: list[str]
    answers: list[str]

class StrategicGoalsRequest(BaseModel):
    questions: list[str]
    answers: list[str]

class StrategicPositioningRadarRequest(BaseModel):
    questions: list[str]
    answers: list[str]

class CultureProfileRequest(BaseModel):
    questions: list[str]
    answers: list[str]

class ProductivityMetricsRequest(BaseModel):
    questions: list[str]
    answers: list[str]

class MaturityScoreLightRequest(BaseModel):
    questions: list[str]
    answers: list[str]

class AnalyzeResponse(BaseModel):
    valid: bool
    feedback: Optional[str] = None

class FileUploadRequest(BaseModel):
    questions: Optional[List[str]] = None
    answers: Optional[List[str]] = None

class FileUploadResponse(BaseModel):
    file_analysis: dict
    extracted_questions: List[str]
    extracted_answers: List[str]
    combined_analysis: dict

class PestelAnalysisRequest(BaseModel):
    questions: list[str]
    answers: list[str]

class StrategicAnalysisRequest(BaseModel):
    questions: list[str]
    answers: list[str]

class PorterAnalysisRequest(BaseModel):
    questions: list[str]
    answers: list[str]

@app.post("/analyze")
async def analyze_qa(request: AnalyzeRequest):
    """
    Analyze a question-answer pair and provide validation feedback.
    Returns JSON with valid status and optional feedback.
    """
    try:
        # Create the prompt for GPT-3.5-turbo
        prompt_ = prompt.format(question=request.question, answer=request.answer)
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_}
            ] + INCOMPLETE_QA_PAYLOAD,
            temperature=0.3,
            max_tokens=200
        )

        result_text = response.choices[0].message.content.strip()
        # Try to parse the JSON response
        import json
        try:
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            raise None
            
        
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing question-answer pair: {str(e)}")

@app.post("/analyze_all")
async def analyze_all_qa(request: AnalyzeAllRequest):
    """
    Analyze a list of question-answer pairs and provide validation feedback.
    Returns JSON with valid status and optional feedback.
    """
    try:    
        prompt = prompt_for_all_questions_answers.format(questions=request.questions, answers=request.answers)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_for_all_questions_answers},
                {"role": "user", "content": prompt}
            ] + INCOMPLETE_QA_PAYLOAD,
            temperature=0,
            max_tokens=500
        )
        result_text = response.choices[0].message.content.strip()
        import json
        try:    
            result = json.loads(result_text)
            return result 
        except json.JSONDecodeError:
            return AnalyzeResponse(
                valid=False,
                feedback="Error parsing AI response. Please try again." 
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing question-answer pair: {str(e)}")

@app.post("/find")
async def competitor_finding(request: AnalyzeAllRequest):
    """
    Find competitors for a given product.
    Returns JSON with valid status and optional feedback.
    """
    try:
        prompt_ = prompt_for_competitor_finding.format(question=request.questions, answer=request.answers)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_for_competitor_finding},
                {"role": "user", "content": prompt_}
            ],
            temperature=0.3,
            max_tokens=400
        )
        competitors = response.choices[0].message.content.strip()
        competitors = competitors.split(',')
        competitor_swot_data = {}
        for competitor in competitors:
            competitor = competitor.strip() 
            swot_data = analyzer.generate_swot_analysis(competitor, days_back=1)
            if swot_data:
                competitor_swot_data[competitor] = swot_data
                
        print(request.questions, request.answers)
        prompt_ = prompt_for_swot_analysis.format(competitors=competitors, swot_data=competitor_swot_data, questions=request.questions, answers=request.answers)
        print(prompt_)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_for_swot_analysis},
                {"role": "user", "content": prompt_ + "Provide me the details about the company whose questions and answers are provided and its swot analysis"}
            ],
            temperature=0,
            max_tokens=500
        )
        result_text = response.choices[0].message.content.strip()
        return result_text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding competitors: {str(e)}")

@app.post("/customer-segment")
async def customer_segmentation(request: CustomerSegmentationRequest):
    """
    Analyze customer segmentation from Q3, Q4, and Q6 answers.
    Returns structured JSON with segment information.
    """
    try:
        prompt_ = prompt_for_customer_segmentation.format(questions=request.questions, answers=request.answers)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_for_customer_segmentation},
                {"role": "user", "content": prompt_}
            ],
            temperature=0.3,
            max_tokens=800
        )
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse the JSON response
        import json
        try:
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            raise HTTPException(
                status_code=500, 
                detail="Error parsing customer segmentation response. Please try again."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing customer segmentation: {str(e)}")

@app.post("/purchase-criteria")
async def purchase_criteria_matrix(request: PurchaseCriteriaRequest):
    """
    Analyze purchase criteria matrix from Q4 and Q3 answers.
    Returns structured JSON with criteria information for radar/spider chart visualization.
    """
    try:
        prompt_ = prompt_for_purchase_criteria.format(questions=request.questions, answers=request.answers)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_for_purchase_criteria},
                {"role": "user", "content": prompt_}
            ],
            temperature=0.3,
            max_tokens=600
        )
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse the JSON response
        import json
        try:
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            raise HTTPException(
                status_code=500, 
                detail="Error parsing purchase criteria response. Please try again."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing purchase criteria: {str(e)}")

@app.post("/channel-heatmap")
async def channel_heatmap(request: ChannelHeatmapRequest):
    """
    Analyze channel heatmap from Q5 and Q3 answers.
    Returns structured JSON with product-channel performance matrix for heatmap visualization.
    """
    try:
        prompt_ = prompt_for_channel_heatmap.format(questions=request.questions, answers=request.answers)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_for_channel_heatmap},
                {"role": "user", "content": prompt_}
            ],
            temperature=0.3,
            max_tokens=800
        )
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse the JSON response
        import json
        try:
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            raise HTTPException(
                status_code=500, 
                detail="Error parsing channel heatmap response. Please try again."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing channel heatmap: {str(e)}")

@app.post("/loyalty-metrics")
async def loyalty_metrics(request: LoyaltyMetricsRequest):
    """
    Analyze loyalty/NPS metrics from Q6 and Q3 answers.
    Returns structured JSON with loyalty metrics for gauge and bar chart visualization.
    """
    try:
        prompt_ = prompt_for_loyalty_metrics.format(questions=request.questions, answers=request.answers)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_for_loyalty_metrics},
                {"role": "user", "content": prompt_}
            ],
            temperature=0.3,
            max_tokens=600
        )
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse the JSON response
        import json
        try:
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            raise HTTPException(
                status_code=500, 
                detail="Error parsing loyalty metrics response. Please try again."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing loyalty metrics: {str(e)}")

@app.post("/capability-heatmap")
async def capability_heatmap(request: CapabilityHeatmapRequest):
    """
    Analyze capability heatmap from Q7 and Q4 answers.
    Returns structured JSON with capability maturity matrix for heatmap visualization.
    """
    try:
        prompt_ = prompt_for_capability_heatmap.format(questions=request.questions, answers=request.answers)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_for_capability_heatmap},
                {"role": "user", "content": prompt_}
            ] + INCOMPLETE_QA_PAYLOAD,
            temperature=0.3,
            max_tokens=800
        )
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse the JSON response
        import json
        try:
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            raise HTTPException(
                status_code=500, 
                detail="Error parsing capability heatmap response. Please try again."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing capability heatmap: {str(e)}")

# Initialize document processor
document_processor = DocumentProcessor(openai_api_key=os.getenv("OPENAI_API_KEY"))

@app.post("/upload-and-analyze", response_model=FileUploadResponse)
async def upload_and_analyze(file: UploadFile = File(...), questions: Optional[List[str]] = None, answers: Optional[List[str]] = None):
    """
    Upload a PDF/Excel file and analyze it along with optional questions and answers.
    Returns comprehensive analysis combining file content with text input.
    """
    # try:
        # Process the uploaded file
    file_analysis = document_processor.process_uploaded_file(file)
    
    # Extract questions and answers from file content
    extracted_qa = file_analysis.get("extracted_data", {}).get("questions_answers", [])
    extracted_questions = [qa.get("question", "") for qa in extracted_qa]
    extracted_answers = [qa.get("answer", "") for qa in extracted_qa]
    
    # Combine with provided questions and answers
    all_questions = (questions or []) + extracted_questions
    all_answers = (answers or []) + extracted_answers
    
    # Create combined analysis
    combined_analysis = {
        "file_analysis": file_analysis,
        "total_questions": len(all_questions),
        "total_answers": len(all_answers),
        "file_questions": len(extracted_questions),
        "provided_questions": len(questions or []),
        "analysis_ready": len(all_questions) > 0 and len(all_answers) > 0
    }
    
    return FileUploadResponse(
        file_analysis=file_analysis,
        extracted_questions=extracted_questions,
        extracted_answers=extracted_answers,
        combined_analysis=combined_analysis
    )
    
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"Error processing file upload: {str(e)}")

@app.post("/full-swot-portfolio")
async def full_swot_portfolio(request: FullSwotPortfolioRequest):
    """
    Create comprehensive SWOT portfolio analysis from all questions and answers.
    Returns detailed SWOT analysis with strategic implications and recommendations.
    """
    try:
        prompt_ = prompt_for_full_swot_portfolio.format(questions=request.questions, answers=request.answers)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_for_full_swot_portfolio},
                {"role": "user", "content": prompt_}
            ] + INCOMPLETE_QA_PAYLOAD,
            temperature=0.3,
            max_tokens=1000
        )
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse the JSON response
        import json
        try:
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            raise HTTPException(
                status_code=500, 
                detail="Error parsing SWOT portfolio response. Please try again."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing SWOT portfolio: {str(e)}")

@app.post("/full-swot-portfolio-with-file")
async def full_swot_portfolio_with_file(
    file: UploadFile = File(...),
    questions: Optional[List[str]] = None,
    answers: Optional[List[str]] = None
):
    """
    Create comprehensive SWOT portfolio analysis from file upload and optional questions/answers.
    """
    # try:
        # Process the uploaded file
    file_analysis = document_processor.process_uploaded_file(file)
    
    # Extract questions and answers from file
    extracted_qa = file_analysis.get("extracted_data", {}).get("questions_answers", [])
    extracted_questions = [qa.get("question", "") for qa in extracted_qa]
    extracted_answers = [qa.get("answer", "") for qa in extracted_qa]
    
    # Combine with provided questions and answers
    all_questions = (questions or []) + extracted_questions
    all_answers = (answers or []) + extracted_answers
    
    if not all_questions or not all_answers:
        raise HTTPException(status_code=400, detail="No questions and answers found in file or provided")
    
    # Create enhanced prompt with file context
    import json 
    enhanced_prompt = f"""
    {prompt_for_full_swot_portfolio.format(questions=all_questions, answers=all_answers)}
    
    Additional file context:
    Document type: {file_analysis.get('file_type', 'unknown')}
    Overall summary: {json.dumps(file_analysis.get('overall_summary', {}))}
    """
    print(enhanced_prompt)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt_for_full_swot_portfolio},
            {"role": "user", "content": enhanced_prompt}
        ],
        temperature=0.3,
        max_tokens=1200
    )
    
    result_text = response.choices[0].message.content.strip()
    print(result_text)
    # Try to parse the JSON response
    import json
    try:
        result = json.loads(result_text)
        # Add file context to result
        result["file_context"] = {
            "file_type": file_analysis.get("file_type"),
            "file_summary": file_analysis.get("overall_summary"),
            "extracted_questions_count": len(extracted_questions),
            "provided_questions_count": len(questions or [])
        }
        return result
        # return AnalyzeResponse(**result)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500, 
            detail="Error parsing SWOT portfolio response. Please try again."
        )
        
    # except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing SWOT portfolio with file: {str(e)}")

@app.post("/channel-effectiveness")
async def channel_effectiveness(request: ChannelEffectivenessRequest):
    """
    Analyze channel effectiveness from Q5, Q11, and Q8 answers.
    Returns enhanced channel effectiveness analysis with bubble chart data and differentiator alignment.
    """
    try:
        prompt_ = prompt_for_channel_effectiveness.format(questions=request.questions, answers=request.answers)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_for_channel_effectiveness},
                {"role": "user", "content": prompt_}
            ]+ INCOMPLETE_QA_PAYLOAD,
            temperature=0.3,
            max_tokens=900
        )
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse the JSON response
        import json
        try:
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            raise HTTPException(
                status_code=500, 
                detail="Error parsing channel effectiveness response. Please try again."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing channel effectiveness: {str(e)}")

@app.post("/channel-effectiveness-with-file")
async def channel_effectiveness_with_file(
    file: UploadFile = File(...),
    questions: Optional[List[str]] = None,
    answers: Optional[List[str]] = None
):
    """
    Analyze channel effectiveness from file upload and optional questions/answers.
    Returns enhanced channel effectiveness analysis with bubble chart data and differentiator alignment.
    """
    try:
        # Process the uploaded file
        file_analysis = document_processor.process_uploaded_file(file)
        
        # Extract questions and answers from file
        extracted_qa = file_analysis.get("extracted_data", {}).get("questions_answers", [])
        extracted_questions = [qa.get("question", "") for qa in extracted_qa]
        extracted_answers = [qa.get("answer", "") for qa in extracted_qa]
        
        # Combine with provided questions and answers
        all_questions = (questions or []) + extracted_questions
        all_answers = (answers or []) + extracted_answers
        
        if not all_questions or not all_answers:
            raise HTTPException(status_code=400, detail="No questions and answers found in file or provided")
        
        # Create enhanced prompt with file context
        import json 
        enhanced_prompt = f"""
        {prompt_for_channel_effectiveness.format(questions=all_questions, answers=all_answers)}
        
        Additional file context:
        Document type: {file_analysis.get('file_type', 'unknown')}
        Overall summary: {json.dumps(file_analysis.get('overall_summary', {}))}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_for_channel_effectiveness},
                {"role": "user", "content": enhanced_prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse the JSON response
        import json
        try:
            result = json.loads(result_text)
            # Add file context to result
            result["file_context"] = {
                "file_type": file_analysis.get("file_type"),
                "file_summary": file_analysis.get("overall_summary"),
                "extracted_questions_count": len(extracted_questions),
                "provided_questions_count": len(questions or [])
            }
            return result
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=500, 
                detail="Error parsing channel effectiveness response. Please try again."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing channel effectiveness with file: {str(e)}")

@app.post("/expanded-capability-heatmap")
async def expanded_capability_heatmap(request: ExpandedCapabilityHeatmapRequest):
    """
    Create expanded capability heatmap with business functions vs capability maturity analysis.
    Returns comprehensive capability analysis with maturity distribution and gap analysis.
    """
    try:
        prompt_ = prompt_for_expanded_capability_heatmap.format(questions=request.questions, answers=request.answers)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_for_expanded_capability_heatmap},
                {"role": "user", "content": prompt_}
            ]+ INCOMPLETE_QA_PAYLOAD,
            temperature=0.3,
            max_tokens=1000
        )
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse the JSON response
        import json
        try:
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            raise HTTPException(
                status_code=500, 
                detail="Error parsing expanded capability heatmap response. Please try again."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing expanded capability heatmap: {str(e)}")

@app.post("/expanded-capability-heatmap-with-file")
async def expanded_capability_heatmap_with_file(
    file: UploadFile = File(...),
    questions: Optional[List[str]] = None,
    answers: Optional[List[str]] = None
):
    """
    Create expanded capability heatmap from file upload and optional questions/answers.
    Returns comprehensive capability analysis with maturity distribution and gap analysis.
    """
    try:
        # Process the uploaded file
        file_analysis = document_processor.process_uploaded_file(file)
        
        # Extract questions and answers from file
        extracted_qa = file_analysis.get("extracted_data", {}).get("questions_answers", [])
        extracted_questions = [qa.get("question", "") for qa in extracted_qa]
        extracted_answers = [qa.get("answer", "") for qa in extracted_qa]
        
        # Combine with provided questions and answers
        all_questions = (questions or []) + extracted_questions
        all_answers = (answers or []) + extracted_answers
        
        if not all_questions or not all_answers:
            raise HTTPException(status_code=400, detail="No questions and answers found in file or provided")
        
        # Create enhanced prompt with file context
        import json
        enhanced_prompt = f"""
        {prompt_for_expanded_capability_heatmap.format(questions=all_questions, answers=all_answers)}
        
        Additional file context:
        Document type: {file_analysis.get('file_type', 'unknown')}
        Overall summary: {json.dumps(file_analysis.get('overall_summary', {}))}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_for_expanded_capability_heatmap},
                {"role": "user", "content": enhanced_prompt}
            ],
            temperature=0.3,
            max_tokens=1200
        )
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse the JSON response
        import json
        try:
            result = json.loads(result_text)
            # Add file context to result
            result["file_context"] = {
                "file_type": file_analysis.get("file_type"),
                "file_summary": file_analysis.get("overall_summary"),
                "extracted_questions_count": len(extracted_questions),
                "provided_questions_count": len(questions or [])
            }
            return result 
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=500, 
                detail="Error parsing expanded capability heatmap response. Please try again."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing expanded capability heatmap with file: {str(e)}")

@app.post("/strategic-radar")
async def strategic_radar(request: StrategicRadarRequest):
    """
    Create strategic radar assessment with multi-dimensional analysis.
    Returns strategic positioning analysis with recommendations and risk factors.
    """
    try:
        prompt_ = prompt_for_strategic_radar.format(questions=request.questions, answers=request.answers)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_for_strategic_radar},
                {"role": "user", "content": prompt_}
            ]+ INCOMPLETE_QA_PAYLOAD,
            temperature=0.3,
            max_tokens=800
        )
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse the JSON response
        import json
        try:
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            raise HTTPException(
                status_code=500, 
                detail="Error parsing strategic radar response. Please try again."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing strategic radar: {str(e)}")

@app.post("/strategic-radar-with-file")
async def strategic_radar_with_file(
    file: UploadFile = File(...),
    questions: Optional[List[str]] = None,
    answers: Optional[List[str]] = None
):
    """
    Create strategic radar assessment from file upload and optional questions/answers.
    """
    try:
        # Process the uploaded file
        file_analysis = document_processor.process_uploaded_file(file)
        
        # Extract questions and answers from file
        extracted_qa = file_analysis.get("extracted_data", {}).get("questions_answers", [])
        extracted_questions = [qa.get("question", "") for qa in extracted_qa]
        extracted_answers = [qa.get("answer", "") for qa in extracted_qa]
        
        # Combine with provided questions and answers
        all_questions = (questions or []) + extracted_questions
        all_answers = (answers or []) + extracted_answers
        
        if not all_questions or not all_answers:
            raise HTTPException(status_code=400, detail="No questions and answers found in file or provided")
        
        import json 
        # Create enhanced prompt with file context
        enhanced_prompt = f"""
        {prompt_for_strategic_radar.format(questions=all_questions, answers=all_answers)}
        
        Additional file context:
        Document type: {file_analysis.get('file_type', 'unknown')}
        Overall summary: {json.dumps(file_analysis.get('overall_summary', {}))}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_for_strategic_radar},
                {"role": "user", "content": enhanced_prompt}
            ],
            temperature=0.3,
            max_tokens=900
        )
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse the JSON response
        import json
        try:
            result = json.loads(result_text)
            # Add file context to result
            result["file_context"] = {
                "file_type": file_analysis.get("file_type"),
                "file_summary": file_analysis.get("overall_summary"),
                "extracted_questions_count": len(extracted_questions),
                "provided_questions_count": len(questions or [])
            }
            return result
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=500, 
                detail="Error parsing strategic radar response. Please try again."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing strategic radar with file: {str(e)}")

@app.post("/maturity-scoring")
async def maturity_scoring(request: MaturityScoringRequest):
    """
    Create comprehensive maturity scoring with cross-dimensional analysis.
    Returns maturity assessment with benchmarking and progression recommendations.
    """
    try:
        prompt_ = prompt_for_maturity_scoring.format(questions=request.questions, answers=request.answers)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_for_maturity_scoring},
                {"role": "user", "content": prompt_}
            ]+ INCOMPLETE_QA_PAYLOAD,
            temperature=0.3,
            max_tokens=900
        )
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse the JSON response
        import json
        try:
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            raise HTTPException(
                status_code=500, 
                detail="Error parsing maturity scoring response. Please try again."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing maturity scoring: {str(e)}")

@app.post("/maturity-scoring-with-file")
async def maturity_scoring_with_file(
    file: UploadFile = File(...),
    questions: Optional[List[str]] = None,
    answers: Optional[List[str]] = None
):
    """
    Create maturity scoring from file upload and optional questions/answers.
    """
    # try:
    # Process the uploaded file
    file_analysis = document_processor.process_uploaded_file(file)
    
    # Extract questions and answers from file
    extracted_qa = file_analysis.get("extracted_data", {}).get("questions_answers", [])
    extracted_questions = [qa.get("question", "") for qa in extracted_qa]
    extracted_answers = [qa.get("answer", "") for qa in extracted_qa]
    
    # Combine with provided questions and answers
    all_questions = (questions or []) + extracted_questions
    all_answers = (answers or []) + extracted_answers
    
    if not all_questions or not all_answers:
        raise HTTPException(status_code=400, detail="No questions and answers found in file or provided")
    import json 
    # Create enhanced prompt with file context
    enhanced_prompt = f"""
    {prompt_for_maturity_scoring.format(questions=all_questions, answers=all_answers)}
    
    Additional file context:
    Document type: {file_analysis.get('file_type', 'unknown')}
    Overall summary: {json.dumps(file_analysis.get('overall_summary', {}))}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt_for_maturity_scoring},
            {"role": "user", "content": enhanced_prompt}
        ],
        temperature=0.3,
        max_tokens=1000
    )
    result_text = response.choices[0].message.content.strip()
    
    # Try to parse the JSON response
    import json
    try:
        result = json.loads(result_text)
        # Add file context to result
        result["file_context"] = {
            "file_type": file_analysis.get("file_type"),
            "file_summary": file_analysis.get("overall_summary"),
            "extracted_questions_count": len(extracted_questions),
            "provided_questions_count": len(questions or [])
        }
        return result
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500, 
            detail="Error parsing maturity scoring response. Please try again."
        )
        
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"Error analyzing maturity scoring with file: {str(e)}")

@app.post("/competitive-advantage")
async def competitive_advantage(request: CompetitiveAdvantageRequest):
    """
    Create competitive advantage matrix analysis from Q8 and Q4 answers.
    Returns detailed competitive advantage analysis with differentiators and customer choice factors.
    """
    try:
        prompt_ = prompt_for_competitive_advantage.format(questions=request.questions, answers=request.answers)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_for_competitive_advantage},
                {"role": "user", "content": prompt_}
            ],
            temperature=0.3,
            max_tokens=800
        )
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse the JSON response
        import json
        try:
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            raise HTTPException(
                status_code=500, 
                detail="Error parsing competitive advantage response. Please try again."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing competitive advantage: {str(e)}")

@app.post("/competitive-advantage-with-file")
async def competitive_advantage_with_file(
    file: UploadFile = File(...),
    questions: Optional[List[str]] = None,
    answers: Optional[List[str]] = None
):
    """
    Create competitive advantage matrix from file upload and optional questions/answers.
    """
    try:
        # Process the uploaded file
        file_analysis = document_processor.process_uploaded_file(file)
        
        # Extract questions and answers from file
        extracted_qa = file_analysis.get("extracted_data", {}).get("questions_answers", [])
        extracted_questions = [qa.get("question", "") for qa in extracted_qa]
        extracted_answers = [qa.get("answer", "") for qa in extracted_qa]
        
        # Combine with provided questions and answers
        all_questions = (questions or []) + extracted_questions
        all_answers = (answers or []) + extracted_answers
        
        if not all_questions or not all_answers:
            raise HTTPException(status_code=400, detail="No questions and answers found in file or provided")
        
        import json
        # Create enhanced prompt with file context
        enhanced_prompt = f"""
        {prompt_for_competitive_advantage.format(questions=all_questions, answers=all_answers)}
        
        Additional file context:
        Document type: {file_analysis.get('file_type', 'unknown')}
        Overall summary: {json.dumps(file_analysis.get('overall_summary', {}))}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_for_competitive_advantage},
                {"role": "user", "content": enhanced_prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse the JSON response
        import json
        try:
            result = json.loads(result_text)
            # Add file context to result
            result["file_context"] = {
                "file_type": file_analysis.get("file_type"),
                "file_summary": file_analysis.get("overall_summary"),
                "extracted_questions_count": len(extracted_questions),
                "provided_questions_count": len(questions or [])
            }
            return result
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=500, 
                detail="Error parsing competitive advantage response. Please try again."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing competitive advantage with file: {str(e)}")

@app.post("/strategic-goals")
async def strategic_goals(request: StrategicGoalsRequest):
    """
    Create strategic goals and OKR analysis from Q9 and Q2 answers.
    Returns comprehensive OKR analysis with progress tracking and strategic alignment.
    """
    try:
        prompt_ = prompt_for_strategic_goals.format(questions=request.questions, answers=request.answers)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_for_strategic_goals},
                {"role": "user", "content": prompt_}
            ],
            temperature=0.3,
            max_tokens=800
        )
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse the JSON response
        import json
        try:
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            raise HTTPException(
                status_code=500, 
                detail="Error parsing strategic goals response. Please try again."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing strategic goals: {str(e)}")

@app.post("/strategic-goals-with-file")
async def strategic_goals_with_file(
    file: UploadFile = File(...),
    questions: Optional[List[str]] = None,
    answers: Optional[List[str]] = None
):
    """
    Create strategic goals and OKR analysis from file upload and optional questions/answers.
    """
    try:
        # Process the uploaded file
        file_analysis = document_processor.process_uploaded_file(file)
        
        # Extract questions and answers from file
        extracted_qa = file_analysis.get("extracted_data", {}).get("questions_answers", [])
        extracted_questions = [qa.get("question", "") for qa in extracted_qa]
        extracted_answers = [qa.get("answer", "") for qa in extracted_qa]
        
        # Combine with provided questions and answers
        all_questions = (questions or []) + extracted_questions
        all_answers = (answers or []) + extracted_answers
        
        if not all_questions or not all_answers:
            raise HTTPException(status_code=400, detail="No questions and answers found in file or provided")
        
        import json
        # Create enhanced prompt with file context
        enhanced_prompt = f"""
        {prompt_for_strategic_goals.format(questions=all_questions, answers=all_answers)}
        
        Additional file context:
        Document type: {file_analysis.get('file_type', 'unknown')}
        Overall summary: {json.dumps(file_analysis.get('overall_summary', {}))}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_for_strategic_goals},
                {"role": "user", "content": enhanced_prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse the JSON response
        import json
        try:
            result = json.loads(result_text)
            # Add file context to result
            result["file_context"] = {
                "file_type": file_analysis.get("file_type"),
                "file_summary": file_analysis.get("overall_summary"),
                "extracted_questions_count": len(extracted_questions),
                "provided_questions_count": len(questions or [])
            }
            return result
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=500, 
                detail="Error parsing strategic goals response. Please try again."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing strategic goals with file: {str(e)}")

@app.post("/strategic-positioning-radar")
async def strategic_positioning_radar(request: StrategicPositioningRadarRequest):
    """
    Create strategic positioning radar analysis from Q8, Q2, Q4, and Q13 answers.
    Returns comprehensive multi-dimensional strategic positioning with industry benchmarking.
    """
    try:
        prompt_ = prompt_for_strategic_positioning_radar.format(questions=request.questions, answers=request.answers)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_for_strategic_positioning_radar},
                {"role": "user", "content": prompt_}
            ],
            temperature=0.3,
            max_tokens=800
        )
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse the JSON response
        import json
        try:
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            raise HTTPException(
                status_code=500, 
                detail="Error parsing strategic positioning radar response. Please try again."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing strategic positioning radar: {str(e)}")

@app.post("/strategic-positioning-radar-with-file")
async def strategic_positioning_radar_with_file(
    file: UploadFile = File(...),
    questions: Optional[List[str]] = None,
    answers: Optional[List[str]] = None
):
    """
    Create strategic positioning radar analysis from file upload and optional questions/answers.
    """
    try:
        # Process the uploaded file
        file_analysis = document_processor.process_uploaded_file(file)
        
        # Extract questions and answers from file
        extracted_qa = file_analysis.get("extracted_data", {}).get("questions_answers", [])
        extracted_questions = [qa.get("question", "") for qa in extracted_qa]
        extracted_answers = [qa.get("answer", "") for qa in extracted_qa]
        
        # Combine with provided questions and answers
        all_questions = (questions or []) + extracted_questions
        all_answers = (answers or []) + extracted_answers
        
        if not all_questions or not all_answers:
            raise HTTPException(status_code=400, detail="No questions and answers found in file or provided")
        
        import json
        # Create enhanced prompt with file context
        enhanced_prompt = f"""
        {prompt_for_strategic_positioning_radar.format(questions=all_questions, answers=all_answers)}
        
        Additional file context:
        Document type: {file_analysis.get('file_type', 'unknown')}
        Overall summary: {json.dumps(file_analysis.get('overall_summary', {}))}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_for_strategic_positioning_radar},
                {"role": "user", "content": enhanced_prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse the JSON response
        import json
        try:
            result = json.loads(result_text)
            # Add file context to result
            result["file_context"] = {
                "file_type": file_analysis.get("file_type"),
                "file_summary": file_analysis.get("overall_summary"),
                "extracted_questions_count": len(extracted_questions),
                "provided_questions_count": len(questions or [])
            }
            return result
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=500, 
                detail="Error parsing strategic positioning radar response. Please try again."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing strategic positioning radar with file: {str(e)}")

@app.post("/culture-profile")
async def culture_profile(request: CultureProfileRequest):
    """
    Create organizational culture profile analysis from Q13 and Q14 answers.
    Returns comprehensive culture assessment with values, behaviors, and strategic alignment.
    """
    try:
        prompt_ = prompt_for_culture_profile.format(questions=request.questions, answers=request.answers)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_for_culture_profile},
                {"role": "user", "content": prompt_}
            ],
            temperature=0.3,
            max_tokens=800
        )
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse the JSON response
        import json
        try:
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            raise HTTPException(
                status_code=500, 
                detail="Error parsing culture profile response. Please try again."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing culture profile: {str(e)}")

@app.post("/culture-profile-with-file")
async def culture_profile_with_file(
    file: UploadFile = File(...),
    questions: Optional[List[str]] = None,
    answers: Optional[List[str]] = None
):
    """
    Create organizational culture profile analysis from file upload and optional questions/answers.
    """
    try:
        # Process the uploaded file
        file_analysis = document_processor.process_uploaded_file(file)
        
        # Extract questions and answers from file
        extracted_qa = file_analysis.get("extracted_data", {}).get("questions_answers", [])
        extracted_questions = [qa.get("question", "") for qa in extracted_qa]
        extracted_answers = [qa.get("answer", "") for qa in extracted_qa]
        
        # Combine with provided questions and answers
        all_questions = (questions or []) + extracted_questions
        all_answers = (answers or []) + extracted_answers
        
        if not all_questions or not all_answers:
            raise HTTPException(status_code=400, detail="No questions and answers found in file or provided")
        
        import json
        # Create enhanced prompt with file context
        enhanced_prompt = f"""
        {prompt_for_culture_profile.format(questions=all_questions, answers=all_answers)}
        
        Additional file context:
        Document type: {file_analysis.get('file_type', 'unknown')}
        Overall summary: {json.dumps(file_analysis.get('overall_summary', {}))}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_for_culture_profile},
                {"role": "user", "content": enhanced_prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse the JSON response
        import json
        try:
            result = json.loads(result_text)
            # Add file context to result
            result["file_context"] = {
                "file_type": file_analysis.get("file_type"),
                "file_summary": file_analysis.get("overall_summary"),
                "extracted_questions_count": len(extracted_questions),
                "provided_questions_count": len(questions or [])
            }
            return result
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=500, 
                detail="Error parsing culture profile response. Please try again."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing culture profile with file: {str(e)}")

@app.post("/productivity-metrics")
async def productivity_metrics(request: ProductivityMetricsRequest):
    """
    Create productivity and efficiency metrics analysis from Q14, Q11, and Q12 answers.
    Returns comprehensive productivity analysis with cost-value optimization insights.
    """
    try:
        prompt_ = prompt_for_productivity_metrics.format(questions=request.questions, answers=request.answers)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_for_productivity_metrics},
                {"role": "user", "content": prompt_}
            ],
            temperature=0.3,
            max_tokens=800
        )
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse the JSON response
        import json
        try:
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            raise HTTPException(
                status_code=500, 
                detail="Error parsing productivity metrics response. Please try again."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing productivity metrics: {str(e)}")

@app.post("/productivity-metrics-with-file")
async def productivity_metrics_with_file(
    file: UploadFile = File(...),
    questions: Optional[List[str]] = None,
    answers: Optional[List[str]] = None
):
    """
    Create productivity and efficiency metrics analysis from file upload and optional questions/answers.
    """
    try:
        # Process the uploaded file
        file_analysis = document_processor.process_uploaded_file(file)
        
        # Extract questions and answers from file
        extracted_qa = file_analysis.get("extracted_data", {}).get("questions_answers", [])
        extracted_questions = [qa.get("question", "") for qa in extracted_qa]
        extracted_answers = [qa.get("answer", "") for qa in extracted_qa]
        
        # Combine with provided questions and answers
        all_questions = (questions or []) + extracted_questions
        all_answers = (answers or []) + extracted_answers
        
        if not all_questions or not all_answers:
            raise HTTPException(status_code=400, detail="No questions and answers found in file or provided")
        
        import json
        # Create enhanced prompt with file context
        enhanced_prompt = f"""
        {prompt_for_productivity_metrics.format(questions=all_questions, answers=all_answers)}
        
        Additional file context:
        Document type: {file_analysis.get('file_type', 'unknown')}
        Overall summary: {json.dumps(file_analysis.get('overall_summary', {}))}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_for_productivity_metrics},
                {"role": "user", "content": enhanced_prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse the JSON response
        import json
        try:
            result = json.loads(result_text)
            # Add file context to result
            result["file_context"] = {
                "file_type": file_analysis.get("file_type"),
                "file_summary": file_analysis.get("overall_summary"),
                "extracted_questions_count": len(extracted_questions),
                "provided_questions_count": len(questions or [])
            }
            return result
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=500, 
                detail="Error parsing productivity metrics response. Please try again."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing productivity metrics with file: {str(e)}")

@app.post("/maturity-score-light")
async def maturity_score_light(request: MaturityScoreLightRequest):
    """
    Create maturity score (light) analysis synthesizing all Q1-Q14 assessments.
    Returns comprehensive maturity analysis with overall score, components, and development roadmap.
    """
    try:
        prompt_ = prompt_for_maturity_score_light.format(questions=request.questions, answers=request.answers)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_for_maturity_score_light},
                {"role": "user", "content": prompt_}
            ],
            temperature=0.3,
            max_tokens=800
        )
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse the JSON response
        import json
        try:
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            raise HTTPException(
                status_code=500, 
                detail="Error parsing maturity score light response. Please try again."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing maturity score light: {str(e)}")

@app.post("/maturity-score-light-with-file")
async def maturity_score_light_with_file(
    file: UploadFile = File(...),
    questions: Optional[List[str]] = None,
    answers: Optional[List[str]] = None
):
    """
    Create maturity score (light) analysis from file upload and optional questions/answers.
    """
    try:
        # Process the uploaded file
        file_analysis = document_processor.process_uploaded_file(file)
        
        # Extract questions and answers from file
        extracted_qa = file_analysis.get("extracted_data", {}).get("questions_answers", [])
        extracted_questions = [qa.get("question", "") for qa in extracted_qa]
        extracted_answers = [qa.get("answer", "") for qa in extracted_qa]
        
        # Combine with provided questions and answers
        all_questions = (questions or []) + extracted_questions
        all_answers = (answers or []) + extracted_answers
        
        if not all_questions or not all_answers:
            raise HTTPException(status_code=400, detail="No questions and answers found in file or provided")
        
        import json
        # Create enhanced prompt with file context
        enhanced_prompt = f"""
        {prompt_for_maturity_score_light.format(questions=all_questions, answers=all_answers)}
        
        Additional file context:
        Document type: {file_analysis.get('file_type', 'unknown')}
        Overall summary: {json.dumps(file_analysis.get('overall_summary', {}))}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_for_maturity_score_light},
                {"role": "user", "content": enhanced_prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse the JSON response
        import json
        try:
            result = json.loads(result_text)
            # Add file context to result
            result["file_context"] = {
                "file_type": file_analysis.get("file_type"),
                "file_summary": file_analysis.get("overall_summary"),
                "extracted_questions_count": len(extracted_questions),
                "provided_questions_count": len(questions or [])
            }
            return result
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=500, 
                detail="Error parsing maturity score light response. Please try again."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing maturity score light with file: {str(e)}")

@app.post("/pestel-analysis")
async def pestel_analysis(request_: PestelAnalysisRequest, request: Request):
    """
    Create comprehensive PESTEL analysis from questions and answers.
    Returns detailed PESTEL analysis with strategic implications and monitoring framework.
    """
    # try:
    prompt_ = prompt_for_pestel_analysis.format(questions=request_.questions, answers=request_.answers)
    
    payload = [
            {"role": "system", "content": system_prompt_for_pestel_analysis},
            {"role": "user", "content": prompt_},
        ]
    if request.headers.get('deep_search'):
        web_data: str = perform_web_search(request_.questions, request_.answers)
        payload += [{"role": "user", "content": f"Here is the company name for web searching \n {web_data}"}]
    
        # print(payload)
        response = client.responses.create(
            model="gpt-4.1",
            input=payload,
            tools=[{"type": "web_search_preview", "search_context_size": "low"}],
        )
        assistant_text = ""
        for message in response.output:
            if message.type == "message":
                for content in message.content:
                    if content.type == "output_text":
                        assistant_text += content.text
    else:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=payload,
            temperature=0.3,
            max_tokens=1200
        )
        assistant_text = response.choices[0].message.content.strip()
    # Try to parse the JSON response
    import json
    try:
        result = json.loads(assistant_text)
        return result
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails
        raise HTTPException(
            status_code=500, 
            detail="Error parsing PESTEL analysis response. Please try again."
        )
            
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"Error analyzing PESTEL analysis: {str(e)}")

@app.post("/pestel-analysis-with-file")
async def pestel_analysis_with_file(
    file: UploadFile = File(...),
    questions: Optional[List[str]] = None,
    answers: Optional[List[str]] = None
):
    """
    Create comprehensive PESTEL analysis from file upload and optional questions/answers.
    """
    try:
        # Process the uploaded file
        file_analysis = document_processor.process_uploaded_file(file)
        
        # Extract questions and answers from file
        extracted_qa = file_analysis.get("extracted_data", {}).get("questions_answers", [])
        extracted_questions = [qa.get("question", "") for qa in extracted_qa]
        extracted_answers = [qa.get("answer", "") for qa in extracted_qa]
        
        # Combine with provided questions and answers
        all_questions = (questions or []) + extracted_questions
        all_answers = (answers or []) + extracted_answers
        
        if not all_questions or not all_answers:
            raise HTTPException(status_code=400, detail="No questions and answers found in file or provided")
        
        import json
        # Create enhanced prompt with file context
        enhanced_prompt = f"""
        {prompt_for_pestel_analysis.format(questions=all_questions, answers=all_answers)}
        
        Additional file context:
        Document type: {file_analysis.get('file_type', 'unknown')}
        Overall summary: {json.dumps(file_analysis.get('overall_summary', {}))}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_for_pestel_analysis},
                {"role": "user", "content": enhanced_prompt}
            ],
            temperature=0.3,
            max_tokens=1200
        )
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse the JSON response
        import json
        try:
            result = json.loads(result_text)
            # Add file context to result
            result["file_context"] = {
                "file_type": file_analysis.get("file_type"),
                "file_summary": file_analysis.get("overall_summary"),
                "extracted_questions_count": len(extracted_questions),
                "provided_questions_count": len(questions or [])
            }
            return result
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=500, 
                detail="Error parsing PESTEL analysis response. Please try again."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing PESTEL analysis with file: {str(e)}")

@app.post("/strategic-analysis")
async def strategic_analysis(request_: StrategicAnalysisRequest, request: Request):
    """
    Create comprehensive strategic analysis using the STRATEGIC framework from questions and answers.
    Returns detailed strategic analysis with multi-dimensional assessment and implementation roadmap.
    """
    try:
        prompt_ = prompt_for_strategic_analysis.format(questions=request_.questions, answers=request_.answers)
        payload = [
                {"role": "system", "content": system_prompt_for_strategic_analysis},
                {"role": "user", "content": prompt_}
            ]
        
        if request.headers.get('deep_search'):
            company_name: str = perform_web_search(request_.questions, request_.answers)
            company_data: str = fetch_top_articles(keyword = company_name, num_articles=2)
            print(company_data)
            payload += [{"role": "user", "content": f"Here is the company name for web searching \n {company_name} and its associated data is as follows : \n {company_data}"},
                        {"role": "user", "content": "PROVIDE A VALID JSON WITHOUT ANY BACKTICKS OR SPECIAL CHARACTERS, JUST VALID JSON"}]
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=payload,
                temperature=0,
                max_tokens=3000
            )
            assistant_text = response.choices[0].message.content.strip()
        
            # print(payload)
            # response = client.responses.create(
            #     model="gpt-4.1",
            #     input=payload,
            #     max_output_tokens=5000,
            #     tools=[{"type": "web_search_preview", "search_context_size": "low"}],
                
            # )
            # assistant_text = ""
            # web_search_results = []
            # for message in response.output:
            #     if message.type == "tool" and message.tool == "web_search_preview":
            #         # This is where web search results appear
            #         web_search_results.append(message)

            # print("==== WEB SEARCH RESULTS ====")
            # print(web_search_results)
            # for message in response.output:
            #     if message.type == "message":
            #         for content in message.content:
            #             if content.type == "output_text":
            #                 assistant_text += content.text
        else:
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=payload,
                temperature=0.3,
                max_tokens=3000
            )
            assistant_text = response.choices[0].message.content.strip()
        
        # Try to parse the JSON response
        import json
        try:
            print(assistant_text)
            result = json.loads(assistant_text)
            return result
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            raise HTTPException(
                status_code=500, 
                detail="Error parsing strategic analysis response. Please try again."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing strategic analysis: {str(e)}")

@app.post("/strategic-analysis-with-file")
async def strategic_analysis_with_file(
    file: UploadFile = File(...),
    questions: Optional[List[str]] = None,
    answers: Optional[List[str]] = None
):
    """
    Create comprehensive strategic analysis using the STRATEGIC framework from file upload and optional questions/answers.
    """
    try:
        # Process the uploaded file
        file_analysis = document_processor.process_uploaded_file(file)
        
        # Extract questions and answers from file
        extracted_qa = file_analysis.get("extracted_data", {}).get("questions_answers", [])
        extracted_questions = [qa.get("question", "") for qa in extracted_qa]
        extracted_answers = [qa.get("answer", "") for qa in extracted_qa]
        
        # Combine with provided questions and answers
        all_questions = (questions or []) + extracted_questions
        all_answers = (answers or []) + extracted_answers
        
        if not all_questions or not all_answers:
            raise HTTPException(status_code=400, detail="No questions and answers found in file or provided")
        
        import json
        # Create enhanced prompt with file context
        enhanced_prompt = f"""
        {prompt_for_strategic_analysis.format(questions=all_questions, answers=all_answers)}
        
        Additional file context:
        Document type: {file_analysis.get('file_type', 'unknown')}
        Overall summary: {json.dumps(file_analysis.get('overall_summary', {}))}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_for_strategic_analysis},
                {"role": "user", "content": enhanced_prompt}
            ],
            temperature=0.3,
            max_tokens=1400
        )
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse the JSON response
        import json
        try:
            result = json.loads(result_text)
            # Add file context to result
            result["file_context"] = {
                "file_type": file_analysis.get("file_type"),
                "file_summary": file_analysis.get("overall_summary"),
                "extracted_questions_count": len(extracted_questions),
                "provided_questions_count": len(questions or [])
            }
            print(result)
            return result
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=500, 
                detail="Error parsing strategic analysis response. Please try again."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing strategic analysis with file: {str(e)}")

@app.post("/porter-analysis")
async def porter_analysis(request: PorterAnalysisRequest):
    """
    Create comprehensive Porter's Five Forces analysis from questions and answers.
    Returns detailed Porter's Five Forces analysis with competitive landscape and strategic implications.
    """
    try:
        prompt_ = prompt_for_porter_analysis.format(questions=request.questions, answers=request.answers)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_for_porter_analysis},
                {"role": "user", "content": prompt_}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse the JSON response
        import json
        try:
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            raise HTTPException(
                status_code=500, 
                detail="Error parsing Porter analysis response. Please try again."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing Porter analysis: {str(e)}")

@app.post("/porter-analysis-with-file")
async def porter_analysis_with_file(
    file: UploadFile = File(...),
    questions: Optional[List[str]] = None,
    answers: Optional[List[str]] = None
):
    """
    Create comprehensive Porter's Five Forces analysis from file upload and optional questions/answers.
    """
    try:
        # Process the uploaded file
        file_analysis = document_processor.process_uploaded_file(file)
        
        # Extract questions and answers from file
        extracted_qa = file_analysis.get("extracted_data", {}).get("questions_answers", [])
        extracted_questions = [qa.get("question", "") for qa in extracted_qa]
        extracted_answers = [qa.get("answer", "") for qa in extracted_qa]
        
        # Combine with provided questions and answers
        all_questions = (questions or []) + extracted_questions
        all_answers = (answers or []) + extracted_answers
        
        if not all_questions or not all_answers:
            raise HTTPException(status_code=400, detail="No questions and answers found in file or provided")
        
        import json
        # Create enhanced prompt with file context
        enhanced_prompt = f"""
        {prompt_for_porter_analysis.format(questions=all_questions, answers=all_answers)}
        
        Additional file context:
        Document type: {file_analysis.get('file_type', 'unknown')}
        Overall summary: {json.dumps(file_analysis.get('overall_summary', {}))}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_for_porter_analysis},
                {"role": "user", "content": enhanced_prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse the JSON response
        import json
        try:
            result = json.loads(result_text)
            # Add file context to result
            result["file_context"] = {
                "file_type": file_analysis.get("file_type"),
                "file_summary": file_analysis.get("overall_summary"),
                "extracted_questions_count": len(extracted_questions),
                "provided_questions_count": len(questions or [])
            }
            return result
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=500, 
                detail="Error parsing Porter analysis response. Please try again."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing Porter analysis with file: {str(e)}")

@app.get("/")
async def root():
    return {"message": "OpenAI Question-Answer Analyzer API", "endpoint": "/analyze"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 