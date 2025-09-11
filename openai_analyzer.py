from io import BytesIO
from fastapi import FastAPI, HTTPException, Header, Request, UploadFile, File
from openai import OpenAI
import os
import json
from typing import Optional, List
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from swot_analysis import SWOTNewsAnalyzer
from dotenv import load_dotenv
from helpers import DocumentProcessor, fetch_top_articles, perform_web_search, process_file_and_questions, perplexity_analysis
from constants import * 
from schemas import *
from dotenv import load_dotenv
from excel_analyze.medium import MediumAnalysis
from excel_analyze.simple import SimpleFinancialAnalysisAdapter
load_dotenv()


load_dotenv()
app = FastAPI(title="OpenAI Question-Answer Analyzer")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
analyzer = SWOTNewsAnalyzer(api_key=os.getenv("NEWSAPI_API_KEY", "d1b3658c875546baa970b0ff36887ac3")) 

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
INCOMPLETE_QA_PAYLOAD = [{"role": "user", "content": "ADD `NOT ENOUGH DATA` TO THE VALUES IF YOU FEEL THE DATA IS NOT ENOUGH"}]

@app.post("/analyze")
async def analyze_qa(request_: AnalyzeRequest, request: Request):
    """
    Analyze a question-answer pair and provide validation feedback.
    Returns JSON with valid status and optional feedback.
    """
    try:
        # Create the prompt for GPT-3.5-turbo
        prompt_ = prompt.format(question=request_.question, answer=request_.answer)
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_}
            ] ,# INCOMPLETE_QA_PAYLOAD,
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
            ] ,# INCOMPLETE_QA_PAYLOAD,
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
        references = {"source": list()}

        for competitor in competitors:
            competitor = competitor.strip() 
            swot_data = analyzer.generate_swot_analysis(competitor, days_back=1)
            if swot_data:
                for type_ in swot_data:
                    for list_ in (swot_data[type_]):
                        references['source'].append(list_['source'])
                    break
        prompt_ = prompt_for_swot_analysis.format(competitors=competitors, swot_data=competitor_swot_data, questions=request.questions, answers=request.answers)
        # print(prompt_)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_for_swot_analysis},
                {"role": "user", "content": prompt_ }
            ],
            temperature=0,
            max_tokens=500
        )
        result_text = response.choices[0].message.content.strip()
        import json 
        result = json.loads(result_text)
        result['reference'] = references['source'][:5]
        return result
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
            ] ,# INCOMPLETE_QA_PAYLOAD,
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
async def full_swot_portfolio(request_: FullSwotPortfolioRequest, request: Request):
    """
    Create comprehensive SWOT portfolio analysis from all questions and answers.
    Returns detailed SWOT analysis with strategic implications and recommendations.
    """
    # try:
    prompt_ = prompt_for_full_swot_portfolio.format(questions=request_.questions, answers=request_.answers)
    payload = [
            {"role": "system", "content": system_prompt_for_full_swot_portfolio},
            {"role": "user", "content": prompt_}
        ]
    # if request.headers.get('deep_search'):
    #     web_data = perform_web_search(request_.questions, request_.answers)
        
    #     payload += [{"role": "user", "content": f"Here are some of the competitors of this company on global and domestic scale. Use this as a context, to help interpret the baseline of the current company:  \n {web_data}"}]        
    
    # sample_data = {
    #     "profit_pool_insights": [
    #         {
    #         "insight_title": "Microsoft's Dominance in High-Margin Software Segments",
    #         "key_finding": "Microsoft's core software businesses (Windows, Office, Azure) generate outsized profit relative to their revenue share due to industry-leading operating margins of 44.9% and profit margin of 36.1%.",
    #         "data_points": [
    #             "RevenueTTM: $281.7B",
    #             "GrossProfitTTM: $193.9B (68.8% gross margin)",
    #             "OperatingMarginTTM: 44.9%",
    #             "ProfitMargin: 36.1%",
    #             "EBITDA: $156.5B"
    #         ],
    #         "strategic_implication": "Continued investment in core platforms and cloud infrastructure will sustain profit pool advantages; future margin expansion relies on deepening enterprise SaaS penetration and maintaining pricing power.",
    #         "visual_priority": "high"
    #         },
    #         {
    #         "insight_title": "Profit Pool Shift Toward Cloud and Infrastructure",
    #         "key_finding": "Azure and infrastructure services account for a growing share of profit pool, driven by compounded quarterly growth (+18.1% YoY revenue growth in latest quarter) and high margins compared to traditional software.",
    #         "data_points": [
    #             "Azure Revenue Growth: +18.1% YoY",
    #             "Cloud Segment Gross Margin: ~70+%",
    #             "Cloud Industry Operating Margin Benchmark: 28-38%",
    #             "MarketCapitalization: $3.76T"
    #         ],
    #         "strategic_implication": "Strategic focus on cloud expansion and hybrid solutions is vital to capturing incremental profits as software licensing growth slows.",
    #         "visual_priority": "high"
    #         },
    #         {
    #         "insight_title": "Labor Costs as Major Investment in Value Creation",
    #         "key_finding": "Microsoft's 35 employees (example answer context) represent 65% of costs, highlighting talent as a pivotal expense and value driver, especially for innovation and support.",
    #         "data_points": [
    #             "Employee costs: 65% of total costs",
    #             "Operating margins depend on efficiency of product development and support capacity"
    #         ],
    #         "strategic_implication": "Investment in recruiting and retaining top talent—especially in AI, security, and enterprise support—will directly impact profitability and innovative capability.",
    #         "visual_priority": "medium"
    #         }
    #     ],
    #     "market_map_insights": [
    #         {
    #         "insight_title": "Microsoft’s Competitive Position as Enterprise Software Leader",
    #         "key_finding": "Microsoft is differentiated by its strong enterprise focus, multi-channel distribution, and platform flexibility, with large market share in OS, cloud, and productivity software.",
    #         "market_dynamics": "Industry is consolidating around digital infrastructure, cloud, and cybersecurity. Regulatory shifts (data privacy, AI governance) and high automation demand are reshaping product strategies.",
    #         "competitive_positioning": "Top quadrant for market share and profitability; maintains premium pricing power and customer loyalty through support and integration.",
    #         "opportunity_areas": [
    #             "Accelerate AI/ML adoption for enterprise clients",
    #             "Expand cybersecurity offerings in response to growing threat",
    #             "Capture SME and mid-market SaaS demand through tailored products"
    #         ]
    #         },
    #         {
    #         "insight_title": "Emerging Market Growth Drivers: Cloud and AI",
    #         "key_finding": "Cloud and AI integration are at the steep part of the technology adoption curve, providing significant TAM expansion and above-market growth rates.",
    #         "market_dynamics": "TAM: $45.6B (2024), 12% CAGR. Cloud segment growth at 25%, software licensing at 5%. New entrants and substitutes (open source, SaaS startups) intensify competition.",
    #         "competitive_positioning": "Microsoft’s platform scale and integration capabilities give it an edge against both incumbents and disruptors.",
    #         "opportunity_areas": [
    #             "AI-powered business process automation",
    #             "Cloud migration consulting/services",
    #             "Partnerships with vertical SaaS providers"
    #         ]
    #         }
    #     ],
    #     "combined_strategic_insights": [
    #         {
    #         "insight_title": "Maintaining Margin Leadership in Rapidly Evolving Markets",
    #         "profit_opportunity": "Focus resources on high-growth, high-margin segments (cloud, AI-enabled infrastructure, enterprise SaaS).",
    #         "market_position_required": "Sustain innovation and integration to strengthen Microsoft’s position as ‘platform of choice’ for enterprises.",
    #         "investment_recommendation": "Prioritize R&D investments in AI/cloud, expand global support, and reinforce talent acquisition.",
    #         "risk_factors": [
    #             "Data privacy and cybersecurity threats",
    #             "Regulatory changes in US/EU markets",
    #             "Disruption from open-source and agile SaaS competitors"
    #         ]
    #         },
    #         {
    #         "insight_title": "Customer Experience as a Strategic Differentiator",
    #         "profit_opportunity": "Leverage superior customer support and flexible platform integration to enhance retention and cross-sell opportunities.",
    #         "market_position_required": "Deliver consistent high NPS (current: 45) and maintain premium service levels.",
    #         "investment_recommendation": "Scale support resources; invest in onboarding and self-service analytics for SME clients.",
    #         "risk_factors": [
    #             "Customer churn if onboarding delays persist",
    #             "Insufficient marketing vs. agile rivals"
    #         ]
    #         }
    #     ],
    #     "visual_recommendations": [
    #         {
    #         "chart_type": "Stacked Bar Chart",
    #         "data_to_display": "Revenue and operating margin for each business segment (Windows, Office, Azure, Gaming)",
    #         "key_message": "Microsoft’s profit pools are concentrated in core software and cloud segments, with clear margin differentials."
    #         },
    #         {
    #         "chart_type": "Bubble Chart",
    #         "data_to_display": "Market share (x), segment growth rate (y), and profitability (color) for major players including Microsoft, Amazon, Google, Salesforce.",
    #         "key_message": "Microsoft occupies the premium position—high share, high growth, and top-tier profitability in cloud and software."
    #         },
    #         {
    #         "chart_type": "Waterfall Chart",
    #         "data_to_display": "Flow of profit from gross revenue to net income across segments",
    #         "key_message": "Visualizes how each step—COGS, operating expenses, tax—affects profit retention by segment."
    #         },
    #         {
    #         "chart_type": "Tornado Chart",
    #         "data_to_display": "Sensitivity analysis of profit drivers (pricing, labor costs, R&D investment, customer churn rate)",
    #         "key_message": "Identifies which levers have the most impact on Microsoft’s profit pools and strategic flexibility."
    #         },
    #         {
    #         "chart_type": "Competitive Positioning Matrix",
    #         "data_to_display": "Profitability vs. market position, mapped for key competitors",
    #         "key_message": "Microsoft leads the quadrant for both share and margin—benchmarking highlights risk areas and differentiation."
    #         }
    #     ]
    #     }
    
    # import json 
    # payload += [{"role": "user", "content": "here is some insights :" + json.dumps(sample_data, indent=2)}]
    print(payload)
    result = perplexity_analysis(system_prompt=system_prompt_for_full_swot_portfolio, user_prompt = payload[1]['content'])
    import json 
    result = dict(json.loads(result))
    return result
    

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
            ],# INCOMPLETE_QA_PAYLOAD,
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
            ],# INCOMPLETE_QA_PAYLOAD,
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
            ],# INCOMPLETE_QA_PAYLOAD,
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
            ],# INCOMPLETE_QA_PAYLOAD,
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
        web_data = (perform_web_search(request_.questions, request_.answers))
        payload += [{"role": "user", "content": f"Here are some of the competitors of this company on global and domestic scale. Use this as a context, to help interpret the baseline of the current company:  \n {web_data}"}]        
        
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
    except json.JSONDecodeError as e:
        print(e)
        # Fallback if JSON parsing fails
        raise HTTPException(
            status_code=500, 
            detail="Error parsing PESTEL analysis response. Please try again."
        )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing PESTEL analysis: {str(e)}")

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
                {"role": "user", "content": prompt_},
            ]
        references = {}
        if request.headers.get('deep_search'):
            web_data = (perform_web_search(request_.questions, request_.answers))
            payload += [{"role": "user", "content": f"Here are some of the competitors of this company on global and domestic scale. Use this as a context, to help interpret the baseline of the current company:  \n {web_data}"}]        
        payload += [{"role": "user", "content": "ALWAYS GIVE VALID JSON AND DON'T USE BACKTICKS LIKE ```. I NEED JUST THE JSON AND NOTHING ELSE"}]
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=payload,
            temperature=0.3,
            max_tokens=3700
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
async def porter_analysis(request_: PorterAnalysisRequest, request: Request):
    """
    Create comprehensive Porter's Five Forces analysis from questions and answers.
    Returns detailed Porter's Five Forces analysis with competitive landscape and strategic implications.
    """
    try:
        prompt_ = prompt_for_porter_analysis.format(questions=request_.questions, answers=request_.answers)
        payload = [
                {"role": "system", "content": system_prompt_for_porter_analysis},
                {"role": "user", "content": prompt_},
                
            ]
        if request.headers.get('deep_search'):
            web_data = (perform_web_search(request_.questions, request_.answers))
            payload += [{"role": "user", "content": f"Here are some of the competitors of this company on global and domestic scale. Use this as a context, to help interpret the baseline of the current company:  \n {web_data}"}]        

        payload += [{"role": "user", "content": "VERY IMPORTANT RULE : ALWAYS GIVE VALID JSON AND DON'T USE BACKTICKS LIKE ```. I NEED JUST THE JSON AND NOTHING ELSE"}]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=payload,
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
            print(result_text)
            # Fallback if JSON parsing fails
            raise HTTPException(
                status_code=500, 
                detail="Error parsing Porter analysis response. Please try again."
            )
            
    except Exception as e:
        print(result_text)
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

@app.post('/cost-efficiency-competitive-position')
async def cost_efficiency_comp_position(request: Request,
    file: Optional[UploadFile] = File(None),
    questions: Optional[List[str]] = None,
    answers: Optional[List[str]] = None):
    
    result = (process_file_and_questions(file, questions, answers, reference = PHASE_3['COST_EFFICIENCY_COMPETITIVE_POSITIONING']))
    return result

@app.post('/operational-efficiency')
async def cost_efficiency_comp_position(request: Request,
    file: Optional[UploadFile] = File(None),
    questions: Optional[List[str]] = None,
    answers: Optional[List[str]] = None):
    
    result = (process_file_and_questions(file, questions, answers, reference = PHASE_3['OPERATIONAL_EFFICIENCY']))
    return result

@app.post('/financial-health')
async def cost_efficiency_comp_position(request: Request,
    file: Optional[UploadFile] = File(None),
    questions: Optional[List[str]] = None,
    answers: Optional[List[str]] = None):
    
    result = (process_file_and_questions(file, questions, answers, reference = PHASE_3['FINANCIAL_HEALTH']))
    return result

@app.post('/financial-performance')
async def cost_efficiency_comp_position(request: Request,
    file: Optional[UploadFile] = File(None),
    questions: Optional[List[str]] = None,
    answers: Optional[List[str]] = None):
    
    result = (process_file_and_questions(file, questions, answers, reference = PHASE_3['FINANCIAL_PERFORMANCE']))
    return result

@app.post('/excel-analysis')
async def excel_analysis(request: Request,
    file: Optional[UploadFile] = File(None),
    source: str = Header(default='simple')
    ):
    
    if file is None:
        return {"error": "No file uploaded"}
    
    contents = await file.read()
    
    # Load Excel file into a pandas DataFrame
    try:
        df = pd.read_excel(BytesIO(contents))
    except Exception as e:
        return {"error": f"Error loading Excel file: {str(e)}"}
    
    if source == 'medium':
        simple_analysis = MediumAnalysis(df)
        analysis = simple_analysis.get_all_metrics()
        result = analysis.copy()
        result.pop('threshold')
        result['profitability']['operating_margin_threshold'] = analysis['threshold']['operating_margin']
        result['profitability']['net_margin_threshold'] = analysis['threshold']['net_margin']
        result['profitability']['gross_margin_threshold'] = analysis['threshold']['gross_margin']
        result['profitability']['ebitda_threshold'] = analysis['threshold']['ebitda']
        result['liquidity']['quick_ratio_threshold'] = analysis['threshold']['quick_ratio']
        result['liquidity']['current_ratio_threshold'] = analysis['threshold']['current_ratio']
        result['leverage']['interest_coverage_threshold'] = analysis['threshold']['interest_coverage']
        result['leverage']['debt_to_equity_threshold'] = analysis['threshold']['debt_to_equity']
        result['investment']['roe_threshold'] = analysis['threshold']['roe']
        result['investment']['roa_threshold'] = analysis['threshold']['roa']
        result['investment']['roic_threshold'] = analysis['threshold']['roic']
        return result 
    elif source == 'simple':
        simple_analysis = SimpleFinancialAnalysisAdapter(df)
        analysis = simple_analysis.get_all_metrics()
        result = analysis.copy()
        result.pop('threshold')
        result['profitability']['operating_margin_threshold'] = analysis['threshold']['operating_margin']
        result['profitability']['gross_margin_threshold'] = analysis['threshold']['gross_margin']
        result['profitability']['ebitda_threshold'] = analysis['threshold']['ebitda']
        result['profitability']['net_margin_threshold'] = analysis['threshold']['net_margin']
        result['liquidity']['quick_ratio_threshold'] = analysis['threshold']['quick_ratio']
        result['liquidity']['current_ratio_threshold'] = analysis['threshold']['current_ratio']
        result['leverage']['interest_coverage_threshold'] = analysis['threshold']['interest_coverage']
        result['leverage']['debt_to_equity_threshold'] = analysis['threshold']['debt_to_equity']
        result['investment']['roe_threshold'] = analysis['threshold']['roe']
        result['investment']['roa_threshold'] = analysis['threshold']['roa']
        result['investment']['roic_threshold'] = analysis['threshold']['roic']
        
        return result 
    
    return ''
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 