from io import BytesIO
from fastapi import FastAPI, HTTPException, Header, Request, UploadFile, File
from fastapi.responses import StreamingResponse
from langfuse.openai import OpenAI
from langfuse import get_client, observe
import os
import json
from typing import Optional, List
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from adapters.llms._groq import _Groq
from utils.swot_analysis import SWOTNewsAnalyzer
from dotenv import load_dotenv
from utils.helpers import (
    DocumentProcessor, analyze_company_async, external_company_intelligence, get_company_details, granular_strategic_analysis, 
    process_file_and_questions, perplexity_analysis
)
from utils.constants import * 
from utils.schemas import *
from utils.prompts import (
    capability_heatmap,
    channel_effectiveness,
    competitive_advantage,
    core_adjacency_matrix,
    culture_profile,
    expanded_capability_heatmap,
    maturity_score,
    maturity_scoring,
    pestel,
    porter,
    productivity_metrics,
    simple_swot,
    single_qa_analysis,
    full_qa_analysis,
    competitor_find,
    strategic_analysis,
    strategic_goals,
    strategic_positioning_radar,
    strategic_radar, 
    swot,
    customer_segmentation,
    purchase_criteria,
    channel_heatmap,
    loyalty_metrics
)
from dotenv import load_dotenv
from excel_analyze.medium import MediumAnalysis
from excel_analyze.simple import SimpleFinancialAnalysisAdapter

load_dotenv()


app = FastAPI(title="OpenAI Question-Answer Analyzer")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Langfuse middleware for session and user tracking
langfuse = get_client()

@app.middleware("http")
async def add_langfuse_session(request: Request, call_next):
    session_id = request.headers.get("X-Session-ID", f"session_{request.client.host}")
    user_id = request.headers.get("X-User-ID", "anonymous")
    request.state.session_id = session_id
    request.state.user_id = user_id
    request.state.endpoint = request.url.path
    response = await call_next(request)
    langfuse.flush()
    return response

analyzer = SWOTNewsAnalyzer(api_key=os.getenv("NEWSAPI_API_KEY", "d1b3658c875546baa970b0ff36887ac3")) 
# Initialize document processor
document_processor = DocumentProcessor(openai_api_key=str(os.getenv("OPENAI_API_KEY")))


groq_client = _Groq()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Helper function to add Langfuse metadata to OpenAI calls
def get_langfuse_metadata(endpoint: str, request: Request = None):
    """Generate metadata for Langfuse tracking"""
    metadata = {"endpoint": endpoint}
    if request:
        metadata["session_id"] = getattr(request.state, 'session_id', 'unknown')
        metadata["user_id"] = getattr(request.state, 'user_id', 'anonymous')
    return metadata

@app.post("/analyze")
observe(name="Analyze")
async def analyze_qa(request_: AnalyzeRequest, request: Request):
    """
    Analyze a question-answer pair and provide validation feedback.
    Returns JSON with valid status and optional feedback.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": single_qa_analysis.system},
                {"role": "user", "content": single_qa_analysis.user.format(question=request_.question, answer=request_.answer)}
            ],
            temperature=0.3,
            max_tokens=200,
            metadata=get_langfuse_metadata("/analyze", request)
        )

        stringified_json = str(response.choices[0].message.content).strip()
        try:
            result = json.loads(stringified_json)
            return result
        except json.JSONDecodeError:
            return {}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing question-answer pair: {str(e)}")

@app.post("/analyze_all")
@observe()
async def analyze_all_qa(request: AnalyzeAllRequest):
    """
    Analyze a list of question-answer pairs and provide validation feedback.
    Returns JSON with valid status and optional feedback.
    """
    try:    
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": full_qa_analysis.system},
                {"role": "user", "content": full_qa_analysis.user.format(questions=request.questions, answers=request.answers)}
            ] ,
            temperature=0,
            max_tokens=500
        )
        stringified_json = str(response.choices[0].message.content).strip()
        try:
            result = json.loads(stringified_json)
            return result
        except json.JSONDecodeError:
            return {}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing question-answer pair: {str(e)}")

@app.post("/find")
observe(name="SWOT")
async def competitor_finding(request: AnalyzeAllRequest):
    """
    Find competitors for a given product.
    Returns JSON with valid status and optional feedback.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": competitor_find.system},
                {"role": "user", "content": competitor_find.user.format(question=request.questions, answer=request.answers)}
            ],
            temperature=0.3,
            max_tokens=400
        )
        competitors = str(response.choices[0].message.content).strip()
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
                
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": swot.system},
                {"role": "user", "content": swot.user.format(competitors=competitors, swot_data=competitor_swot_data, questions=request.questions, answers=request.answers) }
            ],
            temperature=0,
            max_tokens=500
        )
        result_text = str(response.choices[0].message.content).strip()
        result = json.loads(result_text)
        result['reference'] = references['source'][:5]
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding competitors: {str(e)}")

@app.post("/customer-segment")
observe(name="Customer Segmentation")
async def get_customer_segmentation(request: CustomerSegmentationRequest):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": customer_segmentation.system},
                {"role": "user", "content": customer_segmentation.user.format(questions=request.questions, answers=request.answers)}
            ],
            temperature=0.3,
            max_tokens=800
        )
        stringified_json = str(response.choices[0].message.content).strip()
        try:
            result = json.loads(stringified_json)
            return result
        except json.JSONDecodeError:
            return {}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing question-answer pair: {str(e)}")

@app.post("/purchase-criteria")
observe(name="Purchase Criteria")
async def purchase_criteria_matrix(request: PurchaseCriteriaRequest):

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": purchase_criteria.system},
                {"role": "user", "content": purchase_criteria.user.format(questions=request.questions, answers=request.answers)}
            ],
            temperature=0.3,
            max_tokens=600
        )
        stringified_json = str(response.choices[0].message.content).strip()
        try:
            result = json.loads(stringified_json)
            return result
        except json.JSONDecodeError:
            return {}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing question-answer pair: {str(e)}")

@app.post("/channel-heatmap")
observe(name="Channel Heatmap")
async def get_channel_heatmap(request: ChannelHeatmapRequest):
    """
    Analyze channel heatmap from Q5 and Q3 answers.
    Returns structured JSON with product-channel performance matrix for heatmap visualization.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": channel_heatmap.system},
                {"role": "user", "content": channel_heatmap.user.format(questions=request.questions, answers=request.answers)}
            ],
            temperature=0.3,
            max_tokens=800
        )
        stringified_json = str(response.choices[0].message.content).strip()
        try:
            result = json.loads(stringified_json)
            return result
        except json.JSONDecodeError:
            return {}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing question-answer pair: {str(e)}")

@app.post("/loyalty-metrics")
observe(name="Loyalty Metrics")
async def get_loyalty_metrics(request: LoyaltyMetricsRequest):
    """
    Analyze loyalty/NPS metrics from Q6 and Q3 answers.
    Returns structured JSON with loyalty metrics for gauge and bar chart visualization.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": loyalty_metrics.system},
                {"role": "user", "content": loyalty_metrics.user.format(questions=request.questions, answers=request.answers)}
            ],
            temperature=0.3,
            max_tokens=600
        )        
        # Try to parse the JSON response
        stringified_json = str(response.choices[0].message.content).strip()
        try:
            result = json.loads(stringified_json)
            return result
        except json.JSONDecodeError:
            return {}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing question-answer pair: {str(e)}")

@app.post("/capability-heatmap")
observe(name="Capability Heatmap")
async def get_capability_heatmap(request: CapabilityHeatmapRequest):
    """
    Analyze capability heatmap from Q7 and Q4 answers.
    Returns structured JSON with capability maturity matrix for heatmap visualization.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": capability_heatmap.system},
                {"role": "user", "content": capability_heatmap.user.format(questions=request.questions, answers=request.answers)}
            ] ,
            temperature=0.3,
            max_tokens=800
        )        
        # Try to parse the JSON response
        stringified_json = str(response.choices[0].message.content).strip()
        try:
            result = json.loads(stringified_json)
            return result
        except json.JSONDecodeError:
            return {}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing question-answer pair: {str(e)}")


@app.post("/upload-and-analyze", response_model=FileUploadResponse)
async def upload_and_analyze(file: UploadFile = File(...), questions: Optional[List[str]] = None, answers: Optional[List[str]] = None):
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

@app.post("/full-swot-portfolio")
@observe(name="Full SWOT")
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
    content, citations = perplexity_analysis(system_prompt=system_prompt_for_full_swot_portfolio, user_prompt = payload[1]['content'], citations_required=True)
    result = dict(json.loads(content))
    result['citations'] = citations
    return result
    
@app.post("/simple-swot-portfolio")
@observe(name="Competitive landscape")
async def simple_swot_portfolio(request_: FullSwotPortfolioRequest, request: Request):
    """
    Create comprehensive SWOT portfolio analysis from all questions and answers.
    Returns detailed SWOT analysis with strategic implications and recommendations.
    """
    # try:
    competitor_information = perplexity_analysis(
        system_prompt=simple_swot.competitor_system, 
        user_prompt=simple_swot.user_prompt_competitor.format(questions = request_.questions, answers = request_.answers))
    
    response = groq_client.get_streaming_response(payload = [
        {
            "role": "system",
            "content": simple_swot.system,
        },
        {
            "role": "user",
            "content":simple_swot.user.format(questions = request_.questions, 
                                                                    answers = request_.answers,
                                                                    competitors = competitor_information)
        }
    ])
    def generate_stream():
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:  # only yield non-empty strings
                yield content
                
    return StreamingResponse(generate_stream(), media_type="text/plain")
    

@app.post("/full-swot-portfolio-with-file")
@observe(name="Full SWOT with File")
async def full_swot_portfolio_with_file(
    file: UploadFile = File(...),
    questions: Optional[List[str]] = None,
    answers: Optional[List[str]] = None
):
    """
    Create comprehensive SWOT portfolio analysis from file upload and optional questions/answers.
    """
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
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt_for_full_swot_portfolio},
            {"role": "user", "content": enhanced_prompt}
        ],
        temperature=0.3,
        max_tokens=1200
    )
    
    result_text = str(response.choices[0].message.content).strip()
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

@app.post("/channel-effectiveness")
@observe(name="Channel Effectiveness")
async def get_channel_effectiveness(request: ChannelEffectivenessRequest):
    """
    Analyze channel effectiveness from Q5, Q11, and Q8 answers.
    Returns enhanced channel effectiveness analysis with bubble chart data and differentiator alignment.
    """
    try:
        response = groq_client.get_streaming_response(payload = [
            {
                "role": "system",
                "content":  channel_effectiveness.system,
            },
            {
                "role": "user",
                "content":channel_effectiveness.user.format(questions=request.questions, answers=request.answers)
            }
        ])

        def generate_stream():
            for chunk in response:
                content = chunk.choices[0].delta.content
                if content:  # only yield non-empty strings
                    yield content
                    
        return StreamingResponse(generate_stream(), media_type="text/plain")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing question-answer pair: {str(e)}")


@app.post("/channel-effectiveness-with-file")
@observe(name="Channel Effectiveness with File")
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
        result_text = str(response.choices[0].message.content).strip()
        
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
@observe(name="Capability Heatmap")
async def get_expanded_capability_heatmap(request: ExpandedCapabilityHeatmapRequest):
    """
    Create expanded capability heatmap with business functions vs capability maturity analysis.
    Returns comprehensive capability analysis with maturity distribution and gap analysis.
    """
    try:
        response = groq_client.get_streaming_response(payload = [
            {
                "role": "system",
                "content":  expanded_capability_heatmap.system,
            },
            {
                "role": "user",
                "content": expanded_capability_heatmap.user.format(questions=request.questions, answers=request.answers)
            }
        ])

        def generate_stream():
            for chunk in response:
                content = chunk.choices[0].delta.content
                if content:  # only yield non-empty strings
                    yield content
                    
        return StreamingResponse(generate_stream(), media_type="text/plain")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing question-answer pair: {str(e)}")


@app.post("/expanded-capability-heatmap-with-file")
@observe(name="Expanded Capability Heatmap with File")
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
        result_text = str(response.choices[0].message.content).strip()
        
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
@observe(name="Strategic Radar")
async def get_strategic_radar(request: StrategicRadarRequest):
    """
    Create strategic radar assessment with multi-dimensional analysis.
    Returns strategic positioning analysis with recommendations and risk factors.
    """
    try:
        response = groq_client.get_streaming_response(payload = [
            {
                "role": "system",
                "content":  strategic_radar.system,
            },
            {
                "role": "user",
                "content": strategic_radar.user.format(questions=request.questions, answers=request.answers)
            }
        ])

        def generate_stream():
            for chunk in response:
                content = chunk.choices[0].delta.content
                if content:  # only yield non-empty strings
                    yield content
                    
        return StreamingResponse(generate_stream(), media_type="text/plain")

    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing question-answer pair: {str(e)}")


@app.post("/strategic-radar-with-file")
@observe(name="Strategic Radar with File")
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
        result_text = str(response.choices[0].message.content).strip()
        
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
@observe(name="Maturity Score")
async def get_maturity_scoring(request: MaturityScoringRequest):
    """
    Create comprehensive maturity scoring with cross-dimensional analysis.
    Returns maturity assessment with benchmarking and progression recommendations.
    """
    try:
        response = groq_client.get_streaming_response(payload = [
            {
                "role": "system",
                "content":  maturity_scoring.system,
            },
            {
                "role": "user",
                "content": maturity_scoring.user.format(questions=request.questions, answers=request.answers)
            }
        ])

        def generate_stream():
            for chunk in response:
                content = chunk.choices[0].delta.content
                if content:  # only yield non-empty strings
                    yield content
                    
        return StreamingResponse(generate_stream(), media_type="text/plain")
        
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing question-answer pair: {str(e)}")


@app.post("/maturity-scoring-with-file")
@observe(name="Maturity Scoring with File")
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
    result_text = str(response.choices[0].message.content).strip()
    
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
@observe(name="Competitive Advantage")
async def get_competitive_advantage(request: CompetitiveAdvantageRequest):
    """
    Create competitive advantage matrix analysis from Q8 and Q4 answers.
    Returns detailed competitive advantage analysis with differentiators and customer choice factors.
    """
    try:
        response = groq_client.get_streaming_response(payload = [
            {
                "role": "system",
                "content":  competitive_advantage.system,
            },
            {
                "role": "user",
                "content": competitive_advantage.user.format(questions=request.questions, answers=request.answers)
            }
        ])
        
        def generate_stream():
            for chunk in response:
                content = chunk.choices[0].delta.content
                if content:  # only yield non-empty strings
                    yield content
                    
        return StreamingResponse(generate_stream(), media_type="text/plain")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing question-answer pair: {str(e)}")


@app.post("/competitive-advantage-with-file")
@observe(name="Competitive Advantage with File")
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
        result_text = str(response.choices[0].message.content).strip()
        
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
@observe(name="Strategic Goals")
async def get_strategic_goals(request: StrategicGoalsRequest):
    """
    Create strategic goals and OKR analysis from Q9 and Q2 answers.
    Returns comprehensive OKR analysis with progress tracking and strategic alignment.
    """
    try:
        response = groq_client.get_streaming_response(payload = [
            {
                "role": "system",
                "content":  strategic_goals.system,
            },
            {
                "role": "user",
                "content": strategic_goals.user.format(questions=request.questions, answers=request.answers)
            }
        ])
        
        def generate_stream():
            for chunk in response:
                content = chunk.choices[0].delta.content
                if content:  # only yield non-empty strings
                    yield content
                    
        return StreamingResponse(generate_stream(), media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing question-answer pair: {str(e)}")


@app.post("/strategic-goals-with-file")
@observe(name="Strategic Goals with File")
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
        result_text = str(response.choices[0].message.content).strip()
        
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
@observe(name="Strategic Positioning Radar")
async def get_strategic_positioning_radar(request: StrategicPositioningRadarRequest):
    """
    Create strategic positioning radar analysis from Q8, Q2, Q4, and Q13 answers.
    Returns comprehensive multi-dimensional strategic positioning with industry benchmarking.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": strategic_positioning_radar.system},
                {"role": "user", "content": strategic_positioning_radar.user.format(questions=request.questions, answers=request.answers)}
            ],
            temperature=0.3,
            max_tokens=800
        )
        stringified_json = str(response.choices[0].message.content).strip()
        try:
            result = json.loads(stringified_json)
            return result
        except json.JSONDecodeError:
            return {}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing question-answer pair: {str(e)}")


@app.post("/strategic-positioning-radar-with-file")
@observe(name="Strategic Positioning Radar with File")
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
        result_text = str(response.choices[0].message.content).strip()
        
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
@observe(name="Culture Profile")
async def get_culture_profile(request: CultureProfileRequest):
    """
    Create organizational culture profile analysis from Q13 and Q14 answers.
    Returns comprehensive culture assessment with values, behaviors, and strategic alignment.
    """
    try:
        response = groq_client.get_streaming_response(payload = [
            {
                "role": "system",
                "content":  culture_profile.system,
            },
            {
                "role": "user",
                "content": culture_profile.user.format(questions=request.questions, answers=request.answers)
            }
        ])
        
        def generate_stream():
            for chunk in response:
                content = chunk.choices[0].delta.content
                if content:  # only yield non-empty strings
                    yield content
                    
        return StreamingResponse(generate_stream(), media_type="text/plain")
        
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing question-answer pair: {str(e)}")


@app.post("/culture-profile-with-file")
@observe(name="Culture Profile with File")
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
        result_text = str(response.choices[0].message.content).strip()
        
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
@observe(name="Productivity Metrics")
async def get_productivity_metrics(request: ProductivityMetricsRequest):
    """
    Create productivity and efficiency metrics analysis from Q14, Q11, and Q12 answers.
    Returns comprehensive productivity analysis with cost-value optimization insights.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": productivity_metrics.system},
                {"role": "user", "content": productivity_metrics.user.format(questions=request.questions, answers=request.answers)}
            ],
            temperature=0.3,
            max_tokens=800
        )
        stringified_json = str(response.choices[0].message.content).strip()
        try:
            result = json.loads(stringified_json)
            return result
        except json.JSONDecodeError:
            return {}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing question-answer pair: {str(e)}")


@app.post("/productivity-metrics-with-file")
@observe(name="Productivity Metrics with File")
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
        result_text = str(response.choices[0].message.content).strip()
        
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
@observe(name="Maturity Score Light")
async def get_maturity_score_light(request: MaturityScoreLightRequest):
    """
    Create maturity score (light) analysis synthesizing all Q1-Q14 assessments.
    Returns comprehensive maturity analysis with overall score, components, and development roadmap.
    """
    try:
        response = groq_client.get_streaming_response(payload = [
            {
                "role": "system",
                "content":  maturity_score.system,
            },
            {
                "role": "user",
                "content": maturity_score.user.format(questions=request.questions, answers=request.answers)
            }
        ])
        
        def generate_stream():
            for chunk in response:
                content = chunk.choices[0].delta.content
                if content:  # only yield non-empty strings
                    yield content
                    
        return StreamingResponse(generate_stream(), media_type="text/plain")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing question-answer pair: {str(e)}")


@app.post("/maturity-score-light-with-file")
@observe(name="Maturity Score Light with File")
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
        result_text = str(response.choices[0].message.content).strip()
        
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
@observe(name="PESTEL Analysis")
async def pestel_analysis(request_: PestelAnalysisRequest):
    """
    Create comprehensive PESTEL analysis from questions and answers.
    Returns detailed PESTEL analysis with strategic implications and monitoring framework.
    """
    # try:
    company_results = await analyze_company_async(str(request_.answers))
    consolidated_data = await external_company_intelligence(company_results)

    
    prompt = pestel.user.format(
        questions = request_.questions, 
        answers = request_.answers,
        consolidated_financial_insights = consolidated_data, 
        political_external_data = company_results['political_analysis'],
        economic_external_data = company_results['economic_analysis'],
        social_external_data = company_results['social_analysis'],
        technological_external_data = company_results['technological_analysis'],
        environmental_external_data = company_results['environmental_analysis'],
        legal_external_data = company_results['legal_analysis']
    )
    
    result = perplexity_analysis(system_prompt=pestel.system, user_prompt = prompt)
    result = dict(json.loads(str(result)))
    return result


@app.post("/core-adjacency-matrix")
@observe(name="Core Adjacency Matrix")
async def get_core_adjacency_matrix(request: StrategicAnalysisRequest):
    response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": core_adjacency_matrix.system},
                {"role": "user", "content":core_adjacency_matrix.user.format(questions = request.questions, 
                                                                    answers = request.answers,
                                                                    )}
            ],
            temperature=0.3,
            max_tokens=800
        )
    stringified_json = str(response.choices[0].message.content).strip()
    try:
        result = json.loads(stringified_json)
        return result
    except json.JSONDecodeError:
        return {}

@app.post("/strategic-analysis")
@observe(name="Strategic Analysis")
async def get_strategic_analysis(request_: StrategicAnalysisRequest, request: Request):
    """
    Create comprehensive strategic analysis using the STRATEGIC framework from questions and answers.
    Returns detailed strategic analysis with multi-dimensional assessment and implementation roadmap.
    """
    # try:
    analysis = await granular_strategic_analysis(questions = request_.questions, answers = request_.answers)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": strategic_analysis.consolidated_system},
            {"role": "user", "content": strategic_analysis.consolidated_user.format(
                query_1_output = analysis['forward_looking_intelligence'],
                query_2_output = analysis['risk_assessment'],
                query_3_output = analysis['substitute_and_competitiveness']
            )}
        ],
        temperature=0.3,
        max_tokens=1000,
        metadata=get_langfuse_metadata("/strategic-analysis", request)
    )
    consolidated_result = response.choices[0].message.content
    response = groq_client.get_non_streaming_response(
        payload = [
            {"role": "system", "content": strategic_analysis.system},
            {"role": "user", "content": strategic_analysis.user.format(questions = request_.questions,
                                                                       answers = request_.answers,
                                                                       consolidated_results = consolidated_result)}
        ]
    )
    try:
        result = json.loads(str(response.choices[0].message.content))
        return result
    except json.JSONDecodeError:
        print(response.choices[0].message.content)
        return {}
    
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Error analyzing question-answer pair: {str(e)}")


@app.post("/strategic-analysis-with-file")
@observe(name="Strategic Analysis with File")
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
        result_text = str(response.choices[0].message.content).strip()
        
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
@observe(name="Porter Analysis")
async def get_porter_analysis(request_: PorterAnalysisRequest, request: Request):
    """
    Create comprehensive Porter's Five Forces analysis from questions and answers.
    Returns detailed Porter's Five Forces analysis with competitive landscape and strategic implications.
    """
    
    company_details = await get_company_details(request_.questions, request_.answers)
    consolidated_answer = perplexity_analysis(porter.consolidated_query.format(
        result_query_1 = company_details['company_overview'],
        result_query_2 = company_details['company_entry_exit_dynamic'],
        result_query_3 = company_details['substitute_and_competitiveness']
    ),
                        porter.common_question.format(questions = request_.questions, answers = request_.answers))
    
    response = groq_client.get_streaming_response(payload = [
        {
            "role": "system",
            "content": porter.system,
        },
        {
            "role": "user",
            "content": porter.user.format(
                questions = request_.questions,
                answers = request_.answers,
                consolidated_data = consolidated_answer
            )
        }
    ])
    def generate_stream():
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:  # only yield non-empty strings
                yield content
                
    return StreamingResponse(generate_stream(), media_type="text/plain")



@app.post("/porter-analysis-with-file")
@observe(name="Porter Analysis with File")
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
        result_text = str(response.choices[0].message.content).strip()
        
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
async def get_operational_efficiency(request: Request,
    file: Optional[UploadFile] = File(None),
    questions: Optional[List[str]] = None,
    answers: Optional[List[str]] = None):
    
    result = (process_file_and_questions(file, questions, answers, reference = PHASE_3['OPERATIONAL_EFFICIENCY']))
    return result

@app.post('/financial-health')
async def get_financial_health(request: Request,
    file: Optional[UploadFile] = File(None),
    questions: Optional[List[str]] = None,
    answers: Optional[List[str]] = None):
    
    result = (process_file_and_questions(file, questions, answers, reference = PHASE_3['FINANCIAL_HEALTH']))
    return result

@app.post('/financial-performance')
async def get_financial_performance(request: Request,
    file: Optional[UploadFile] = File(None),
    questions: Optional[List[str]] = None,
    answers: Optional[List[str]] = None):
    
    result = (process_file_and_questions(file, questions, answers, reference = PHASE_3['FINANCIAL_PERFORMANCE']))
    return result

@app.post('/excel-analysis')
async def excel_analysis(
    request: Request,
    file: Optional[UploadFile] = File(None),
    source: str = Header(default='simple'),
    metric_type: Optional[str] = None
):
    if file is None:
        return {"error": "No file uploaded"}
    
    contents = await file.read()
    
    # Load Excel file into a pandas DataFrame
    try:
        df = pd.read_excel(BytesIO(contents))
    except Exception as e:
        return {"error": f"Error loading Excel file: {str(e)}"}
    
    available_metrics = [
        'profitability', 
        'liquidity', 
        'investment', 
        'leverage', 
        'growth_trends'
    ]
     
    if source not in ['medium', 'simple']:
        return {"error": "Invalid source. Must be 'simple' or 'medium'"}
     
    if source == 'medium':
        analysis_obj = MediumAnalysis(df)
    else:  
        analysis_obj = SimpleFinancialAnalysisAdapter(df)
     
    try:
        analysis = analysis_obj.get_all_metrics()
    except Exception as e:
        return {"error": f"Error during analysis: {str(e)}"}
     
    if metric_type:
        if metric_type not in available_metrics:
            return {
                "error": f"Invalid metric_type. Available options: {', '.join(available_metrics)}"
            }
        
        if metric_type not in analysis:
            return {"error": f"Metric type '{metric_type}' not found in analysis results"}
         
        result = {metric_type: analysis[metric_type]} 

        threshold_data = analysis.get('threshold', {})
        if metric_type == 'profitability':
            result[metric_type].update({
                'operating_margin_threshold': threshold_data.get('operating_margin'),
                'net_margin_threshold': threshold_data.get('net_margin'),
                'gross_margin_threshold': threshold_data.get('gross_margin'),
                'ebitda_threshold': threshold_data.get('ebitda')
            })
        elif metric_type == 'liquidity':
            result[metric_type].update({
                'quick_ratio_threshold': threshold_data.get('quick_ratio'),
                'current_ratio_threshold': threshold_data.get('current_ratio')
            })
        elif metric_type == 'leverage':
            result[metric_type].update({
                'interest_coverage_threshold': threshold_data.get('interest_coverage'),
                'debt_to_equity_threshold': threshold_data.get('debt_to_equity')
            })
        elif metric_type == 'investment':
            result[metric_type].update({
                'roe_threshold': threshold_data.get('roe'),
                'roa_threshold': threshold_data.get('roa'),
                'roic_threshold': threshold_data.get('roic')
            })
        
        return result
     
    result = analysis.copy()
    result.pop('threshold', None)  
     
    threshold_data = analysis.get('threshold', {})
     
    if 'profitability' in result:
        result['profitability'].update({
            'operating_margin_threshold': threshold_data.get('operating_margin'),
            'net_margin_threshold': threshold_data.get('net_margin'),
            'gross_margin_threshold': threshold_data.get('gross_margin'),
            'ebitda_threshold': threshold_data.get('ebitda')
        })
     
    if 'liquidity' in result:
        result['liquidity'].update({
            'quick_ratio_threshold': threshold_data.get('quick_ratio'),
            'current_ratio_threshold': threshold_data.get('current_ratio')
        })
     
    if 'leverage' in result:
        result['leverage'].update({
            'interest_coverage_threshold': threshold_data.get('interest_coverage'),
            'debt_to_equity_threshold': threshold_data.get('debt_to_equity')
        })
     
    if 'investment' in result:
        result['investment'].update({
            'roe_threshold': threshold_data.get('roe'),
            'roa_threshold': threshold_data.get('roa'),
            'roic_threshold': threshold_data.get('roic')
        })
    
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 