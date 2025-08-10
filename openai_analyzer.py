from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from pydantic import BaseModel
from openai import OpenAI
import os
import json 
from typing import Optional, List
from fastapi.middleware.cors import CORSMiddleware
from swot_analysis import SWOTNewsAnalyzer
from dotenv import load_dotenv
from helpers import DocumentProcessor, perform_web_search
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
        "year": 2025,
        "objectives": [
            {{
                "objective": "Expand into Chile",
                "priority": 1,
                "keyResults": [
                    {{
                        "metric": "Market launch date",
                        "target": "Q3 2025",
                        "current": "Planning phase",
                        "progress": 25
                    }}
                ],
                "alignment": "growth"
            }},
            {{
                "objective": "Launch mobile app",
                "priority": 2,
                "keyResults": [
                    {{
                        "metric": "App launch date",
                        "target": "Q4 2025",
                        "current": "Development",
                        "progress": 40
                    }}
                ],
                "alignment": "innovation"
            }},
            {{
                "objective": "Reduce churn below 15%",
                "priority": 3,
                "keyResults": [
                    {{
                        "metric": "Customer churn rate",
                        "target": 15,
                        "current": 22,
                        "progress": 32
                    }}
                ],
                "alignment": "retention"
            }}
        ],
        "overallProgress": 32,
        "strategicThemes": ["geographic_expansion", "digital_transformation", "customer_retention"]
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
        "values": ["collaborative", "fast-paced", "data-driven"],
        "behaviors": ["autonomy", "execution-focused"],
        "workStyle": {{
            "pace": "fast",
            "decisionMaking": "autonomous",
            "orientation": "results-driven"
        }},
        "employeeMetrics": {{
            "totalEmployees": 8,
            "costPercentage": 60,
            "valuePerEmployee": 35000,
            "productivity": "above_average"
        }},
        "cultureType": "Entrepreneurial",
        "cultureFit": {{
            "withStrategy": "high",
            "withMarket": "high",
            "withCapabilities": "medium"
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
        "overallScore": 3.2,
        "level": "Defined",
        "components": {{
            "strategicClarity": 3.8,
            "marketAlignment": 3.5,
            "customerFocus": 4.2,
            "operationalCapability": 2.8,
            "competitivePosition": 3.5,
            "organizationalHealth": 3.4
        }},
        "maturityProfile": "Customer-Led Growth",
        "strengths": [
            "Strong customer orientation",
            "Clear differentiators",
            "Agile culture"
        ],
        "developmentAreas": [
            "Operational automation",
            "Analytics capabilities",
            "Process standardization"
        ],
        "nextLevel": {{
            "target": "Managed (Level 4)",
            "requirements": [
                "Implement marketing automation",
                "Enhance data analytics capabilities",
                "Systematize competitive advantages",
                "Standardize core processes"
            ],
            "estimatedTimeframe": "12-18 months"
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
            "dominant_factors": ["AI adoption trends", "Regulatory changes in LATAM"],
            "critical_risks": ["New tax laws for digital products"],
            "key_opportunities": ["Surge in AI usage", "Market expansion in Chile"],
            "strategic_recommendations": ["Automate processes", "Expand to Chile"],
            "agility_priority_score": 7
        }},
        "factor_summary": {{
            "political": {{
                "total_mentions": 2,
                "high_impact_count": 1,
                "key_themes": ["Tax regulations", "Digital product laws"],
                "strategic_priority": "High"
            }},
            "economic": {{
                "total_mentions": 3,
                "high_impact_count": 2,
                "key_themes": ["Market expansion", "Revenue growth"],
                "strategic_priority": "High"
            }},
            "social": {{
                "total_mentions": 2,
                "high_impact_count": 1,
                "key_themes": ["Customer preferences", "Work culture"],
                "strategic_priority": "Medium"
            }},
            "technological": {{
                "total_mentions": 4,
                "high_impact_count": 3,
                "key_themes": ["AI adoption", "Automation", "Digital transformation"],
                "strategic_priority": "High"
            }},
            "environmental": {{
                "total_mentions": 1,
                "high_impact_count": 0,
                "key_themes": ["Remote work"],
                "strategic_priority": "Low"
            }},
            "legal": {{
                "total_mentions": 2,
                "high_impact_count": 1,
                "key_themes": ["Tax compliance", "Digital regulations"],
                "strategic_priority": "High"
            }}
        }},
        "strategic_recommendations": {{
            "immediate_actions": [
                {{
                    "action": "Implement automation for low-value tasks",
                    "rationale": "Address technological efficiency gap",
                    "timeline": "2-3 months",
                    "resources_required": "Development team, automation tools",
                    "success_metrics": ["Process efficiency improvement", "Cost reduction"]
                }}
            ],
            "short_term_initiatives": [
                {{
                    "initiative": "Launch mobile app development",
                    "strategic_pillar": "Technology and Digitization",
                    "expected_outcome": "Enhanced customer experience",
                    "risk_mitigation": "Addresses competitive pressure"
                }}
            ],
            "long_term_strategic_shifts": [
                {{
                    "shift": "Expand to Chile market",
                    "transformation_required": "Market entry strategy",
                    "competitive_advantage": "First-mover advantage in new market",
                    "sustainability": "Diversified revenue streams"
                }}
            ]
        }},
        "monitoring_dashboard": {{
            "key_indicators": [
                {{
                    "indicator": "AI adoption rate in target market",
                    "pestel_factor": "Technological",
                    "measurement_frequency": "Quarterly",
                    "threshold_values": {{
                        "green": ">60% adoption",
                        "yellow": "30-60% adoption",
                        "red": "<30% adoption"
                    }}
                }}
            ],
            "early_warning_signals": [
                {{
                    "signal": "New digital tax regulations",
                    "trigger_response": "Immediate compliance review",
                    "monitoring_source": "Government regulatory updates"
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

ALWAYS PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED. DO NOT USE BACKTICKS LIKE ``` OR ANYTHING ELSE, JUST PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED
'''

prompt_for_strategic_analysis = '''
Analyze the following questions and answers to create a comprehensive strategic analysis using the STRATEGIC framework:

Questions: {questions}
Answers: {answers}

Create strategic analysis and return it in the following JSON format:
{{
    "strategic_analysis": {{
        "executive_summary": {{
            "situation_overview": "Growing company in AI education space with strong customer focus but operational efficiency gaps",
            "primary_vuca_factors": ["Uncertainty", "Complexity"],
            "key_strategic_themes": ["Digital Transformation", "Market Expansion", "Operational Excellence"],
            "urgency_level": "Medium",
            "strategic_maturity_assessment": "Developing"
        }},
        "strategic_pillars_analysis": {{
            "strategy": {{
                "pillar_code": "S",
                "relevance_score": 8.5,
                "current_state": {{
                    "strengths": ["Clear differentiators", "Strong customer focus"],
                    "weaknesses": ["Limited market expansion", "Operational inefficiencies"],
                    "assessment_score": 7.0
                }},
                "recommendations": [
                    {{
                        "action": "Develop comprehensive market expansion strategy",
                        "priority": "High",
                        "timeline": "3 months",
                        "resources_required": ["Market research", "Strategic planning team"],
                        "expected_impact": "Increased market reach and revenue growth"
                    }}
                ],
                "success_metrics": [
                    {{
                        "metric": "Market expansion progress",
                        "target": "Chile market entry by Q3 2025",
                        "measurement_frequency": "Monthly"
                    }}
                ]
            }},
            "tactics": {{
                "pillar_code": "T",
                "relevance_score": 7.0,
                "current_state": {{
                    "strengths": ["Effective sales channels", "Strong referral program"],
                    "weaknesses": ["Limited automation", "Manual processes"],
                    "assessment_score": 6.5
                }},
                "recommendations": [
                    {{
                        "action": "Implement marketing automation tools",
                        "priority": "High",
                        "timeline": "2 months",
                        "resources_required": ["Automation platform", "Training"],
                        "expected_impact": "Improved efficiency and scalability"
                    }}
                ],
                "success_metrics": [
                    {{
                        "metric": "Process automation rate",
                        "target": "60% of manual tasks automated",
                        "measurement_frequency": "Weekly"
                    }}
                ]
            }},
            "resources": {{
                "pillar_code": "R",
                "relevance_score": 6.5,
                "current_state": {{
                    "strengths": ["Experienced team", "Strong customer relationships"],
                    "weaknesses": ["Limited headcount", "Resource constraints"],
                    "assessment_score": 6.0
                }},
                "recommendations": [
                    {{
                        "action": "Optimize resource allocation and hiring plan",
                        "priority": "Medium",
                        "timeline": "6 months",
                        "resources_required": ["HR support", "Budget allocation"],
                        "expected_impact": "Better resource utilization and growth capacity"
                    }}
                ],
                "success_metrics": [
                    {{
                        "metric": "Employee productivity",
                        "target": "20% improvement",
                        "measurement_frequency": "Monthly"
                    }}
                ]
            }},
            "analysis_and_data": {{
                "pillar_code": "A",
                "relevance_score": 5.5,
                "current_state": {{
                    "strengths": ["Customer feedback collection"],
                    "weaknesses": ["Limited analytics capabilities", "Data infrastructure"],
                    "assessment_score": 4.0
                }},
                "recommendations": [
                    {{
                        "action": "Implement advanced analytics and data infrastructure",
                        "priority": "Medium",
                        "timeline": "4 months",
                        "resources_required": ["Analytics tools", "Data engineer"],
                        "expected_impact": "Better decision-making and insights"
                    }}
                ],
                "success_metrics": [
                    {{
                        "metric": "Data-driven decisions",
                        "target": "80% of decisions supported by data",
                        "measurement_frequency": "Monthly"
                    }}
                ]
            }},
            "technology_and_digitization": {{
                "pillar_code": "T2",
                "relevance_score": 8.0,
                "current_state": {{
                    "strengths": ["Digital product delivery"],
                    "weaknesses": ["Limited automation", "Manual processes"],
                    "assessment_score": 5.5
                }},
                "recommendations": [
                    {{
                        "action": "Develop mobile app and enhance digital platform",
                        "priority": "High",
                        "timeline": "6 months",
                        "resources_required": ["Development team", "Mobile app platform"],
                        "expected_impact": "Enhanced customer experience and accessibility"
                    }}
                ],
                "success_metrics": [
                    {{
                        "metric": "Digital platform usage",
                        "target": "90% customer adoption",
                        "measurement_frequency": "Weekly"
                    }}
                ]
            }},
            "execution": {{
                "pillar_code": "E",
                "relevance_score": 7.5,
                "current_state": {{
                    "strengths": ["Customer service excellence", "Team execution"],
                    "weaknesses": ["Process standardization", "Operational efficiency"],
                    "assessment_score": 6.5
                }},
                "recommendations": [
                    {{
                        "action": "Standardize core processes and workflows",
                        "priority": "High",
                        "timeline": "3 months",
                        "resources_required": ["Process documentation", "Training"],
                        "expected_impact": "Improved consistency and efficiency"
                    }}
                ],
                "success_metrics": [
                    {{
                        "metric": "Process efficiency",
                        "target": "30% improvement",
                        "measurement_frequency": "Monthly"
                    }}
                ]
            }},
            "governance": {{
                "pillar_code": "G",
                "relevance_score": 6.0,
                "current_state": {{
                    "strengths": ["Clear decision-making", "Agile culture"],
                    "weaknesses": ["Limited formal governance", "Risk management"],
                    "assessment_score": 5.5
                }},
                "recommendations": [
                    {{
                        "action": "Establish formal governance framework",
                        "priority": "Medium",
                        "timeline": "4 months",
                        "resources_required": ["Governance framework", "Risk management tools"],
                        "expected_impact": "Better risk management and compliance"
                    }}
                ],
                "success_metrics": [
                    {{
                        "metric": "Governance maturity",
                        "target": "Level 3 maturity",
                        "measurement_frequency": "Quarterly"
                    }}
                ]
            }},
            "innovation": {{
                "pillar_code": "I",
                "relevance_score": 7.0,
                "current_state": {{
                    "strengths": ["Customer-centric approach", "Market responsiveness"],
                    "weaknesses": ["Limited R&D investment", "Innovation processes"],
                    "assessment_score": 6.0
                }},
                "recommendations": [
                    {{
                        "action": "Establish innovation processes and R&D investment",
                        "priority": "Medium",
                        "timeline": "6 months",
                        "resources_required": ["Innovation team", "R&D budget"],
                        "expected_impact": "Enhanced competitive advantage"
                    }}
                ],
                "success_metrics": [
                    {{
                        "metric": "Innovation pipeline",
                        "target": "3 new products/services per year",
                        "measurement_frequency": "Quarterly"
                    }}
                ]
            }},
            "culture": {{
                "pillar_code": "C",
                "relevance_score": 8.5,
                "current_state": {{
                    "strengths": ["Collaborative culture", "Fast-paced environment"],
                    "weaknesses": ["Limited formal culture programs"],
                    "assessment_score": 7.5
                }},
                "recommendations": [
                    {{
                        "action": "Formalize culture programs and values",
                        "priority": "Low",
                        "timeline": "6 months",
                        "resources_required": ["Culture programs", "Values documentation"],
                        "expected_impact": "Enhanced employee engagement and retention"
                    }}
                ],
                "success_metrics": [
                    {{
                        "metric": "Employee satisfaction",
                        "target": "85% satisfaction rate",
                        "measurement_frequency": "Quarterly"
                    }}
                ]
            }}
        }},
        "cross_pillar_synthesis": {{
            "interconnections": [
                {{
                    "pillars": ["Technology and Digitization", "Execution"],
                    "relationship": "Technology enables better execution",
                    "synergy_opportunity": "Automate execution processes"
                }}
            ],
            "holistic_recommendations": [
                "Focus on technology-enabled execution improvements",
                "Prioritize market expansion with operational excellence"
            ]
        }},
        "agile_frameworks_recommendations": {{
            "scrum": {{
                "applicability": "High for product development",
                "use_cases": ["Mobile app development", "Feature development"],
                "implementation_priority": "High"
            }},
            "kanban": {{
                "applicability": "Medium for operations",
                "use_cases": ["Process improvement", "Customer support"],
                "implementation_priority": "Medium"
            }},
            "okrs": {{
                "applicability": "High for strategic alignment",
                "use_cases": ["Strategic goal tracking", "Team alignment"],
                "implementation_priority": "High"
            }}
        }},
        "risk_assessment": {{
            "strategic_risks": [
                {{
                    "risk": "Market entry failure in Chile",
                    "probability": "Medium",
                    "impact": "High",
                    "mitigation": "Thorough market research and pilot program",
                    "owner": "Strategy team"
                }}
            ],
            "contingency_plans": [
                {{
                    "scenario": "Regulatory changes in target markets",
                    "response": "Immediate compliance review and strategy adjustment",
                    "trigger_indicators": ["New tax laws", "Digital regulations"]
                }}
            ]
        }},
        "success_benchmarks": {{
            "case_study_parallels": [
                {{
                    "company": "Duolingo",
                    "parallel": "Digital education platform expansion",
                    "applicable_lesson": "Mobile-first approach and gamification",
                    "success_metric": "User engagement and retention"
                }}
            ],
            "industry_benchmarks": [
                {{
                    "metric": "Customer retention rate",
                    "industry_average": "70%",
                    "target": "85%",
                    "timeframe": "12 months"
                }}
            ]
        }},
        "implementation_roadmap": {{
            "phase_1": {{
                "duration": "3 months",
                "focus": "Operational efficiency and automation",
                "key_initiatives": ["Process automation", "Mobile app development"],
                "budget": "$100,000",
                "success_criteria": ["30% efficiency improvement", "App beta launch"]
            }},
            "phase_2": {{
                "duration": "6 months",
                "focus": "Market expansion and analytics",
                "key_initiatives": ["Chile market entry", "Analytics implementation"],
                "budget": "$200,000",
                "success_criteria": ["Market entry success", "Data-driven decisions"]
            }},
            "phase_3": {{
                "duration": "12 months",
                "focus": "Scale and innovation",
                "key_initiatives": ["Product innovation", "Geographic expansion"],
                "budget": "$300,000",
                "success_criteria": ["3 new products", "2 new markets"]
            }}
        }},
        "monitoring_and_feedback": {{
            "dashboard_requirements": ["KPI tracking", "Progress monitoring", "Risk alerts"],
            "review_cycles": {{
                "weekly": "Team progress updates",
                "monthly": "KPI review and adjustments",
                "quarterly": "Strategic review and planning",
                "annual": "Comprehensive strategy assessment"
            }},
            "feedback_loops": [
                {{
                    "source": "Customer feedback",
                    "frequency": "Weekly",
                    "integration_point": "Product development"
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
            "industry_attractiveness": "Moderate",
            "overall_competitive_intensity": "High",
            "key_competitive_forces": ["Threat of New Entrants", "Competitive Rivalry"],
            "strategic_implications": ["Focus on differentiation", "Build entry barriers"],
            "competitive_position": "Challenger"
        }},
        "five_forces_analysis": {{
            "threat_of_new_entrants": {{
                "intensity": "Medium",
                "score": 6,
                "key_factors": [
                    {{
                        "factor": "Low capital requirements",
                        "impact": "High",
                        "description": "Digital products require minimal upfront investment"
                    }},
                    {{
                        "factor": "Brand loyalty",
                        "impact": "Medium",
                        "description": "Established customer relationships provide some protection"
                    }}
                ],
                "entry_barriers": [
                    "Brand recognition",
                    "Customer relationships",
                    "Technology expertise"
                ],
                "strategic_implications": "Focus on building strong brand and customer loyalty"
            }},
            "bargaining_power_of_suppliers": {{
                "intensity": "Low",
                "score": 3,
                "key_factors": [
                    {{
                        "factor": "Multiple supplier options",
                        "impact": "Low",
                        "description": "Technology and service providers are abundant"
                    }}
                ],
                "supplier_concentration": "Low",
                "switching_costs": "Low",
                "strategic_implications": "Maintain multiple supplier relationships for flexibility"
            }},
            "bargaining_power_of_buyers": {{
                "intensity": "High",
                "score": 8,
                "key_factors": [
                    {{
                        "factor": "Low switching costs",
                        "impact": "High",
                        "description": "Customers can easily switch to competitors"
                    }},
                    {{
                        "factor": "Price sensitivity",
                        "impact": "High",
                        "description": "Customers are price-conscious in this market"
                    }}
                ],
                "buyer_concentration": "Low",
                "product_differentiation": "Medium",
                "strategic_implications": "Focus on value proposition and customer retention"
            }},
            "threat_of_substitute_products": {{
                "intensity": "Medium",
                "score": 5,
                "key_factors": [
                    {{
                        "factor": "Alternative learning methods",
                        "impact": "Medium",
                        "description": "Traditional education and self-learning options exist"
                    }}
                ],
                "substitute_availability": "High",
                "switching_costs": "Low",
                "strategic_implications": "Emphasize unique value proposition and outcomes"
            }},
            "competitive_rivalry": {{
                "intensity": "High",
                "score": 8,
                "key_factors": [
                    {{
                        "factor": "Many competitors",
                        "impact": "High",
                        "description": "Numerous players in the education technology space"
                    }},
                    {{
                        "factor": "Low differentiation",
                        "impact": "High",
                        "description": "Similar offerings across competitors"
                    }}
                ],
                "competitor_concentration": "Medium",
                "industry_growth": "High",
                "strategic_implications": "Focus on differentiation and niche positioning"
            }}
        }},
        "competitive_landscape": {{
            "direct_competitors": [
                {{
                    "name": "Competitor A",
                    "market_share": "25%",
                    "strengths": ["Brand recognition", "Large customer base"],
                    "weaknesses": ["High costs", "Slow innovation"]
                }}
            ],
            "indirect_competitors": [
                {{
                    "name": "Traditional Education",
                    "threat_level": "Medium",
                    "competitive_advantage": "Established credibility"
                }}
            ],
            "potential_entrants": [
                {{
                    "category": "Tech companies",
                    "likelihood": "High",
                    "barriers": "Brand building, customer acquisition"
                }}
            ]
        }},
        "strategic_recommendations": {{
            "immediate_actions": [
                {{
                    "action": "Strengthen brand differentiation",
                    "rationale": "Address high competitive rivalry",
                    "timeline": "3-6 months",
                    "resources_required": ["Marketing budget", "Brand strategy"],
                    "expected_impact": "Reduced price sensitivity"
                }}
            ],
            "short_term_initiatives": [
                {{
                    "initiative": "Build customer loyalty programs",
                    "strategic_pillar": "Customer Retention",
                    "expected_outcome": "Reduced buyer bargaining power",
                    "risk_mitigation": "Addresses switching costs"
                }}
            ],
            "long_term_strategic_shifts": [
                {{
                    "shift": "Develop proprietary technology",
                    "transformation_required": "R&D investment",
                    "competitive_advantage": "Entry barrier creation",
                    "sustainability": "Long-term competitive moat"
                }}
            ]
        }},
        "monitoring_dashboard": {{
            "key_indicators": [
                {{
                    "indicator": "New competitor entry rate",
                    "force": "Threat of New Entrants",
                    "measurement_frequency": "Quarterly",
                    "threshold_values": {{
                        "green": "<2 new entrants/year",
                        "yellow": "2-5 new entrants/year",
                        "red": ">5 new entrants/year"
                    }}
                }}
            ],
            "early_warning_signals": [
                {{
                    "signal": "Major tech company entering market",
                    "trigger_response": "Immediate competitive analysis",
                    "monitoring_source": "Industry news and announcements"
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
            ],
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
            ],
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
            ],
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
            ],
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
            ],
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
            ],
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
            web_data: str = perform_web_search(request_.questions, request_.answers)
            payload += [{"role": "user", "content": f"Here is the company name for web searching \n {web_data}"}]
        
            # print(payload)
            response = client.responses.create(
                model="gpt-4.1",
                input=payload,
                max_output_tokens=5000,
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