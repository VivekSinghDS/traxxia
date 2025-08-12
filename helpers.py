import fitz  # PyMuPDF
import pandas as pd
import base64
import io
import os
from PIL import Image
import pytesseract
from typing import List, Dict, Any, Optional, Tuple
import logging
from fastapi import UploadFile, HTTPException
import tempfile
import json
from openai import OpenAI
import cv2
import numpy as np
from openai import OpenAI
# Configure logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def perform_web_search(questions, answers):
    response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "YOUR TASK IS TO PROVIDE ONLY COMPANY NAME FOR WHICH THIS ANSWERS ARE ABOUT. DO NOT PROVIDE ANYTHING ELSE THAN THAT"},
                {"role": "user", "content": f"{answers}"}
            ],
            temperature=0.3,
            
        )
    return response.choices[0].message.content

from googlesearch import search
import requests
import trafilatura


def fetch_top_articles(keyword, num_articles=3):
    """
    Search Google for a keyword and fetch clean main content of the top articles.
    
    Args:
        keyword (str): Search query
        num_articles (int): Number of top results to fetch
        
    Returns:
        dict: {url: clean_text}
    """
    result = ""

    # Perform Google search
    search_results = list(search(keyword, num_results=num_articles))

    for url in search_results[:num_articles]:
        try:
            print(f"Fetching: {url}")
            # response = requests.get(url, timeout=10, headers={
            #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            # })

            # Extract clean main text using trafilatura
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                text = trafilatura.extract(downloaded)
                if text:
                    result += text

        except Exception as e:
            print(f"Error fetching {url}: {e}")

    return result
class DocumentProcessor:
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
        self.supported_formats = ['.pdf', '.xlsx', '.xls', '.csv']
        
    def process_uploaded_file(self, file: UploadFile) -> Dict[str, Any]:
        """
        Main method to process uploaded files (PDF/Excel)
        Returns structured data with text and image analysis
        """
        try:
            file_extension = os.path.splitext(file.filename)[1].lower()
            
            if file_extension == '.pdf':
                return self._process_pdf(file)
            elif file_extension in ['.xlsx', '.xls']:
                return self._process_excel(file)
            elif file_extension == '.csv':
                return self._process_csv(file)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported file format: {file_extension}")
                
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    
    def _process_pdf(self, file: UploadFile) -> Dict[str, Any]:
        """
        Process PDF file: extract text and images from each page
        """
        try:
            # Read PDF content
            pdf_content = file.file.read()
            pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
            
            pages_data = []
            total_pages = len(pdf_document)
            
            for page_num in range(1):
                page = pdf_document[page_num]
                
                # Extract text from page
                page_text = page.get_text()
                
                # Extract images from page
                page_images = self._extract_images_from_page(page, page_num)
                
                # Convert page to image for visual analysis
                page_image = self._page_to_image(page)
                page_image_base64 = self._image_to_base64(page_image)
                
                # Perform OCR on page image
                ocr_text = self._perform_ocr(page_image)
                
                # Analyze page image with AI
                image_analysis = self._analyze_page_image(page_image_base64, page_num + 1, total_pages)
                
                page_data = {
                    "page_number": page_num + 1,
                    "text_content": page_text,
                    "ocr_text": ocr_text,
                    "images": page_images,
                    "page_image_base64": page_image_base64,
                    "image_analysis": image_analysis,
                    "page_summary": self._summarize_page_content(page_text, ocr_text, image_analysis)
                }
                
                pages_data.append(page_data)
            
            pdf_document.close()
            
            return {
                "file_type": "pdf",
                "total_pages": total_pages,
                "pages": pages_data,
                "overall_summary": self._create_overall_summary(pages_data),
                "extracted_data": self._extract_structured_data(pages_data)
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    
    def _process_excel(self, file: UploadFile) -> Dict[str, Any]:
        """
        Process Excel file: extract data and create visualizations
        """
        try:
            # Read Excel content
            excel_content = file.file.read()
            
            # Read all sheets
            excel_file = pd.ExcelFile(io.BytesIO(excel_content))
            sheets_data = {}
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(io.BytesIO(excel_content), sheet_name=sheet_name)
                
                # Convert DataFrame to image for visual analysis
                sheet_image = self._dataframe_to_image(df, sheet_name)
                sheet_image_base64 = self._image_to_base64(sheet_image)
                
                # Analyze sheet image with AI
                image_analysis = self._analyze_sheet_image(sheet_image_base64, sheet_name)
                
                sheet_data = {
                    "sheet_name": sheet_name,
                    "data": df.to_dict('records'),
                    "columns": df.columns.tolist(),
                    "shape": df.shape,
                    "summary_stats": self._get_dataframe_summary(df),
                    "sheet_image_base64": sheet_image_base64,
                    "image_analysis": image_analysis
                }
                
                sheets_data[sheet_name] = sheet_data
            
            return {
                "file_type": "excel",
                "total_sheets": len(sheets_data),
                "sheets": sheets_data,
                "overall_summary": self._create_excel_summary(sheets_data),
                "extracted_data": self._extract_excel_structured_data(sheets_data)
            }
            
        except Exception as e:
            logger.error(f"Error processing Excel: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing Excel: {str(e)}")
    
    def _process_csv(self, file: UploadFile) -> Dict[str, Any]:
        """
        Process CSV file: extract data and create visualizations
        """
        try:
            # Read CSV content
            csv_content = file.file.read()
            df = pd.read_csv(io.BytesIO(csv_content))
            
            # Convert DataFrame to image for visual analysis
            csv_image = self._dataframe_to_image(df, "CSV Data")
            csv_image_base64 = self._image_to_base64(csv_image)
            
            # Analyze CSV image with AI
            image_analysis = self._analyze_sheet_image(csv_image_base64, "CSV Data")
            
            return {
                "file_type": "csv",
                "data": df.to_dict('records'),
                "columns": df.columns.tolist(),
                "shape": df.shape,
                "summary_stats": self._get_dataframe_summary(df),
                "csv_image_base64": csv_image_base64,
                "image_analysis": image_analysis,
                "overall_summary": self._create_csv_summary(df),
                "extracted_data": self._extract_csv_structured_data(df)
            }
            
        except Exception as e:
            logger.error(f"Error processing CSV: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing CSV: {str(e)}")
    
    def _extract_images_from_page(self, page, page_num: int) -> List[Dict[str, Any]]:
        """
        Extract images from a PDF page
        """
        images = []
        image_list = page.get_images()
        
        for img_index, img in enumerate(image_list):
            try:
                xref = img[0]
                pix = fitz.Pixmap(page.parent, xref)
                
                if pix.n - pix.alpha < 4:  # GRAY or RGB
                    img_data = pix.tobytes("png")
                    img_base64 = base64.b64encode(img_data).decode()
                    
                    image_info = {
                        "image_index": img_index,
                        "base64_data": img_base64,
                        "width": pix.width,
                        "height": pix.height,
                        "image_analysis": self._analyze_extracted_image(img_base64, page_num, img_index)
                    }
                    
                    images.append(image_info)
                
                pix = None  # Free memory
                
            except Exception as e:
                logger.warning(f"Error extracting image {img_index} from page {page_num}: {str(e)}")
                continue
        
        return images
    
    def _page_to_image(self, page) -> Image.Image:
        """
        Convert PDF page to PIL Image
        """
        try:
            # Set zoom factor for better quality
            zoom = 2
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            return img
            
        except Exception as e:
            logger.error(f"Error converting page to image: {str(e)}")
            raise
    
    def _dataframe_to_image(self, df: pd.DataFrame, title: str) -> Image.Image:
        """
        Convert DataFrame to image for visual analysis
        """
        try:
            # Create a figure with matplotlib
            import matplotlib.pyplot as plt
            import matplotlib.patches as patches
            
            # Set style
            plt.style.use('default')
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Hide axes
            ax.axis('tight')
            ax.axis('off')
            
            # Create table
            table = ax.table(cellText=df.head(20).values,  # Show first 20 rows
                           colLabels=df.columns,
                           cellLoc='center',
                           loc='center')
            
            # Style the table
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1.2, 1.5)
            
            # Add title
            plt.title(title, fontsize=14, fontweight='bold', pad=20)
            
            # Convert to PIL Image
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            plt.close()
            
            buf.seek(0)
            img = Image.open(buf)
            
            return img
            
        except Exception as e:
            logger.error(f"Error converting DataFrame to image: {str(e)}")
            # Return a simple text image as fallback
            return self._create_fallback_image(f"Data: {title}\nShape: {df.shape}")
    
    def _create_fallback_image(self, text: str) -> Image.Image:
        """
        Create a fallback image with text
        """
        img = Image.new('RGB', (800, 400), color='white')
        from PIL import ImageDraw, ImageFont
        
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        draw.text((50, 50), text, fill='black', font=font)
        return img
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """
        Convert PIL Image to base64 string
        """
        try:
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            return img_str
        except Exception as e:
            logger.error(f"Error converting image to base64: {str(e)}")
            raise
    
    def _perform_ocr(self, image: Image.Image) -> str:
        """
        Perform OCR on image to extract text
        """
        try:
            # Preprocess image for better OCR
            img_array = np.array(image)
            
            # Convert to grayscale if needed
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            # Apply preprocessing for better OCR
            # Denoise
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Threshold
            _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Convert back to PIL Image
            processed_image = Image.fromarray(thresh)
            
            # Perform OCR
            ocr_text = pytesseract.image_to_string(processed_image)
            
            return ocr_text.strip()
            
        except Exception as e:
            logger.warning(f"OCR failed: {str(e)}")
            return ""
    
    def _analyze_page_image(self, image_base64: str, page_num: int, total_pages: int) -> Dict[str, Any]:
        """
        Analyze page image using OpenAI Vision API
        """
        try:
            prompt = f"""
            Analyze this PDF page {page_num} of {total_pages}. Extract and structure the following information:
            
            1. Document type and purpose
            2. Key content sections and headings
            3. Important data points, numbers, or metrics
            4. Tables, charts, or visual elements
            5. Business context and implications
            6. Any questions or answers that might be present
            
            Provide the analysis in JSON format with the following structure:
            {{
                "document_type": "string",
                "content_sections": ["section1", "section2"],
                "key_data_points": ["data1", "data2"],
                "visual_elements": ["table", "chart", "image"],
                "business_context": "string",
                "questions_answers": ["qa1", "qa2"],
                "confidence_score": 0.85
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                # Fallback to structured text
                return {
                    "analysis": result_text,
                    "document_type": "unknown",
                    "confidence_score": 0.5
                }
                
        except Exception as e:
            logger.error(f"Error analyzing page image: {str(e)}")
            return {
                "error": str(e),
                "document_type": "unknown",
                "confidence_score": 0.0
            }
    
    def _analyze_sheet_image(self, image_base64: str, sheet_name: str) -> Dict[str, Any]:
        """
        Analyze Excel/CSV sheet image using OpenAI Vision API
        """
        try:
            prompt = f"""
            Analyze this Excel/CSV sheet '{sheet_name}'. Extract and structure the following information:
            
            1. Data structure and columns
            2. Key metrics and data types
            3. Important trends or patterns
            4. Business insights and implications
            5. Data quality assessment
            6. Potential questions or analysis opportunities
            
            Provide the analysis in JSON format with the following structure:
            {{
                "data_structure": {{
                    "columns": ["col1", "col2"],
                    "data_types": ["string", "number"],
                    "row_count": 100
                }},
                "key_metrics": ["metric1", "metric2"],
                "trends_patterns": ["trend1", "trend2"],
                "business_insights": ["insight1", "insight2"],
                "data_quality": "good/medium/poor",
                "analysis_opportunities": ["opp1", "opp2"],
                "confidence_score": 0.85
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                # Fallback to structured text
                return {
                    "analysis": result_text,
                    "data_structure": {"columns": [], "row_count": 0},
                    "confidence_score": 0.5
                }
                
        except Exception as e:
            logger.error(f"Error analyzing sheet image: {str(e)}")
            return {
                "error": str(e),
                "data_structure": {"columns": [], "row_count": 0},
                "confidence_score": 0.0
            }
    
    def _analyze_extracted_image(self, image_base64: str, page_num: int, img_index: int) -> Dict[str, Any]:
        """
        Analyze extracted image from PDF using OpenAI Vision API
        """
        try:
            prompt = f"""
            Analyze this image extracted from PDF page {page_num}, image {img_index}. 
            Describe what you see and extract any relevant business information.
            
            Provide the analysis in JSON format:
            {{
                "image_type": "chart/table/diagram/photo",
                "content_description": "string",
                "business_relevance": "string",
                "extracted_data": ["data1", "data2"],
                "confidence_score": 0.85
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                return {
                    "analysis": result_text,
                    "image_type": "unknown",
                    "confidence_score": 0.5
                }
                
        except Exception as e:
            logger.error(f"Error analyzing extracted image: {str(e)}")
            return {
                "error": str(e),
                "image_type": "unknown",
                "confidence_score": 0.0
            }
    
    def _summarize_page_content(self, text_content: str, ocr_text: str, image_analysis: Dict) -> str:
        """
        Create a summary of page content
        """
        try:
            combined_content = f"Text: {text_content}\nOCR: {ocr_text}\nAnalysis: {json.dumps(image_analysis)}"
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": f"Summarize this page content in 10 if required, else make it 5-10 sentences. If it contains numbers, then make sure to describe them in a way that is easy to understand:\n{combined_content}"
                    }
                ],
                max_tokens=400,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error summarizing page content: {str(e)}")
            return "Summary unavailable"
    
    def _create_overall_summary(self, pages_data: List[Dict]) -> Dict[str, Any]:
        """
        Create overall summary of the document
        """
        try:
            # Combine all content
            all_text = "\n".join([page.get("text_content", "") for page in pages_data])
            all_ocr = "\n".join([page.get("ocr_text", "") for page in pages_data])
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": f"""
                        Create a comprehensive summary of this document based on the following content:
                        
                        Text Content: {all_text[:2000]}
                        OCR Content: {all_ocr[:2000]}
                        
                        Provide the summary in JSON format:
                        {{
                            "document_type": "string",
                            "main_topics": ["topic1", "topic2"],
                            "key_findings": ["finding1", "finding2"],
                            "business_implications": ["implication1", "implication2"],
                            "recommendations": ["rec1", "rec2"],
                            "confidence_score": 0.85
                        }}
                        """
                    }
                ],
                max_tokens=600,
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content.strip()
            
            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                return {
                    "summary": result_text,
                    "document_type": "unknown",
                    "confidence_score": 0.5
                }
                
        except Exception as e:
            logger.error(f"Error creating overall summary: {str(e)}")
            return {
                "error": str(e),
                "document_type": "unknown",
                "confidence_score": 0.0
            }
    
    def _extract_structured_data(self, pages_data: List[Dict]) -> Dict[str, Any]:
        """
        Extract structured data from all pages
        """
        try:
            # Combine all content for analysis
            all_content = ""
            for page in pages_data:
                all_content += page.get("text_content", "") + " "
                all_content += page.get("ocr_text", "") + " "
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": f"""
                        Extract structured data from this document content. Look for:
                        - Questions and answers
                        - Metrics and KPIs
                        - Business data
                        - Financial information
                        - Customer data
                        
                        Content: {all_content[:3000]}
                        
                        Return in JSON format:
                        {{
                            "questions_answers": [{{"question": "q1", "answer": "a1"}}],
                            "metrics": [{{"name": "metric1", "value": "value1"}}],
                            "business_data": [{{"category": "cat1", "data": "data1"}}],
                            "financial_data": [{{"type": "type1", "value": "value1"}}],
                            "customer_data": [{{"segment": "seg1", "data": "data1"}}]
                        }}
                        """
                    }
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content.strip()
            
            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                return {
                    "extracted_data": result_text,
                    "questions_answers": [],
                    "metrics": []
                }
                
        except Exception as e:
            logger.error(f"Error extracting structured data: {str(e)}")
            return {
                "error": str(e),
                "questions_answers": [],
                "metrics": []
            }
    
    def _get_dataframe_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get summary statistics for DataFrame
        """
        try:
            return {
                "shape": df.shape,
                "columns": df.columns.tolist(),
                "data_types": df.dtypes.to_dict(),
                "null_counts": df.isnull().sum().to_dict(),
                "numeric_summary": df.describe().to_dict() if df.select_dtypes(include=[np.number]).shape[1] > 0 else {},
                "unique_counts": df.nunique().to_dict()
            }
        except Exception as e:
            logger.error(f"Error getting DataFrame summary: {str(e)}")
            return {"error": str(e)}
    
    def _create_excel_summary(self, sheets_data: Dict) -> Dict[str, Any]:
        """
        Create summary for Excel file
        """
        try:
            all_data = []
            for sheet_name, sheet_data in sheets_data.items():
                all_data.append(f"Sheet: {sheet_name}")
                all_data.append(f"Columns: {sheet_data['columns']}")
                all_data.append(f"Rows: {sheet_data['shape'][0]}")
            
            combined_data = "\n".join(all_data)
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": f"""
                        Create a summary of this Excel file:
                        
                        {combined_data}
                        
                        Return in JSON format:
                        {{
                            "file_type": "excel",
                            "main_purpose": "string",
                            "key_datasets": ["dataset1", "dataset2"],
                            "business_insights": ["insight1", "insight2"],
                            "data_quality": "good/medium/poor",
                            "recommendations": ["rec1", "rec2"]
                        }}
                        """
                    }
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content.strip()
            
            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                return {
                    "summary": result_text,
                    "file_type": "excel"
                }
                
        except Exception as e:
            logger.error(f"Error creating Excel summary: {str(e)}")
            return {"error": str(e)}
    
    def _create_csv_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Create summary for CSV file
        """
        try:
            data_info = f"Columns: {df.columns.tolist()}\nRows: {df.shape[0]}\nData Types: {df.dtypes.to_dict()}"
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": f"""
                        Create a summary of this CSV file:
                        
                        {data_info}
                        
                        Return in JSON format:
                        {{
                            "file_type": "csv",
                            "main_purpose": "string",
                            "key_insights": ["insight1", "insight2"],
                            "data_quality": "good/medium/poor",
                            "recommendations": ["rec1", "rec2"]
                        }}
                        """
                    }
                ],
                max_tokens=400,
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content.strip()
            
            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                return {
                    "summary": result_text,
                    "file_type": "csv"
                }
                
        except Exception as e:
            logger.error(f"Error creating CSV summary: {str(e)}")
            return {"error": str(e)}
    
    def _extract_excel_structured_data(self, sheets_data: Dict) -> Dict[str, Any]:
        """
        Extract structured data from Excel sheets
        """
        try:
            all_data = []
            for sheet_name, sheet_data in sheets_data.items():
                all_data.append(f"Sheet: {sheet_name}")
                all_data.append(f"Data: {str(sheet_data['data'][:5])}")  # First 5 rows
            
            combined_data = "\n".join(all_data)
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": f"""
                        Extract structured data from this Excel content:
                        
                        {combined_data}
                        
                        Return in JSON format:
                        {{
                            "questions_answers": [{{"question": "q1", "answer": "a1"}}],
                            "metrics": [{{"name": "metric1", "value": "value1"}}],
                            "business_data": [{{"category": "cat1", "data": "data1"}}],
                            "financial_data": [{{"type": "type1", "value": "value1"}}]
                        }}
                        """
                    }
                ],
                max_tokens=600,
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content.strip()
            
            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                return {
                    "extracted_data": result_text,
                    "questions_answers": [],
                    "metrics": []
                }
                
        except Exception as e:
            logger.error(f"Error extracting Excel structured data: {str(e)}")
            return {
                "error": str(e),
                "questions_answers": [],
                "metrics": []
            }
    
    def _extract_csv_structured_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract structured data from CSV
        """
        try:
            # Convert first few rows to string for analysis
            data_sample = df.head(10).to_string()
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": f"""
                        Extract structured data from this CSV content:
                        
                        {data_sample}
                        
                        Return in JSON format:
                        {{
                            "questions_answers": [{{"question": "q1", "answer": "a1"}}],
                            "metrics": [{{"name": "metric1", "value": "value1"}}],
                            "business_data": [{{"category": "cat1", "data": "data1"}}],
                            "financial_data": [{{"type": "type1", "value": "value1"}}]
                        }}
                        """
                    }
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content.strip()
            
            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                return {
                    "extracted_data": result_text,
                    "questions_answers": [],
                    "metrics": []
                }
                
        except Exception as e:
            logger.error(f"Error extracting CSV structured data: {str(e)}")
            return {
                "error": str(e),
                "questions_answers": [],
                "metrics": []
            } 