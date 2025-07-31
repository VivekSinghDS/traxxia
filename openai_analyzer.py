from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from openai import OpenAI
import os
import json 
from typing import Optional, List
from fastapi.middleware.cors import CORSMiddleware
from swot_analysis import SWOTNewsAnalyzer
from dotenv import load_dotenv
from helpers import DocumentProcessor
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

@app.post("/analyze", response_model=AnalyzeResponse)
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
            return AnalyzeResponse(**result)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return AnalyzeResponse(
                valid=False,
                feedback="Error parsing AI response. Please try again."
            )
        
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing question-answer pair: {str(e)}")

@app.post("/analyze_all", response_model=AnalyzeResponse)
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
            return AnalyzeResponse(**result)
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

@app.post("/full-swot-portfolio", response_model=AnalyzeResponse)
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
            return AnalyzeResponse(**result)
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

@app.post("/strategic-radar", response_model=AnalyzeResponse)
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
            return AnalyzeResponse(**result)
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

@app.post("/maturity-scoring", response_model=AnalyzeResponse)
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
            return AnalyzeResponse(**result)
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
            return AnalyzeResponse(**result)
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
                
@app.get("/")
async def root():
    return {"message": "OpenAI Question-Answer Analyzer API", "endpoint": "/analyze"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 