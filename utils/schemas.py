from typing import Optional, List
from pydantic import BaseModel

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
