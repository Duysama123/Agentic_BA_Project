import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent
from schemas.ba_schema import SRSDocument

class BAAgent(BaseAgent):
    """
    Tác tử chuyên trách: Business Analyst (Kỹ sư Phân tích Nghiệp vụ).
    Nhiệm vụ: Tổng hợp SRS chuẩn công nghiệp từ Dữ liệu hình (Vision) và Dữ liệu luật (RAG).
    """
    
    def __init__(self):
        super().__init__(role_name="BA Agent", model_name="gemini-2.5-flash")

    def generate_requirements(self, ui_analysis_json: str, business_rules_context: str = "") -> SRSDocument:
        """Sinh ra tài liệu SRSDocument chuẩn IEEE 830 bằng Tiếng Anh."""
        
        system_prompt = (
            "You are an Expert Business Analyst. Your task is to write a comprehensive Software Requirements Specification (SRS) "
            "following the IEEE 830 standard based on provided UI Analysis and Business Rules Context.\n"
            "CRITICAL INSTRUCTION: You MUST output all content in ENGLISH. Do not use Vietnamese or any other language."
        )
        
        user_prompt = f"### UI COMPONENTS DETAIL (EXTRACTED BY VISION AI):\n{ui_analysis_json}\n\n"
        if business_rules_context and business_rules_context.strip() != "":
            user_prompt += f"### MANDATORY BUSINESS RULES (RETRIEVED FROM PDF VIA RAG):\n{business_rules_context}\n\n"
        else:
            user_prompt += "### BUSINESS RULES: No specific regulation provided. Complete freedom to infer standard templates.\n\n"
            
        user_prompt += (
            "Decompose this limited data into a professional comprehensive Software Requirements Specification document. "
            "Ensure you fill out every section of the required IEEE structure. "
            "For non-functional requirements and business rules, automatically append standard domain knowledge if missing."
        )
        
        result = self.call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            pydantic_schema=SRSDocument
        )
        
        return result

    def refine_requirements(self, previous_srs_json: str, qa_feedback: str, ui_analysis_json: str) -> SRSDocument:
        """
        Vòng lặp tự sửa (Self-Refinement Loop).
        """
        system_prompt = (
            "You are an Expert Business Analyst. Your task is to refine and fix an SRS document based on QA feedback.\n"
            "CRITICAL INSTRUCTION: You MUST output all content in ENGLISH."
        )
        
        user_prompt = (
            "### TASK: SRS SELF-REFINEMENT ITERATION\n\n"
            f"### PREVIOUS SRS (V1 - REJECTED BY QA):\n{previous_srs_json}\n\n"
            f"### QA DIRECTOR FEEDBACK (DISCREPANCIES):\n{qa_feedback}\n\n"
            f"### ORIGINAL VISION AI DATA:\n{ui_analysis_json}\n\n"
            "Read the QA feedback above carefully. Rewrite a complete SRS V2.0 that "
            "fixes ALL the discrepancies pointed out. Keep correct parts unchanged."
        )
        
        result = self.call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            pydantic_schema=SRSDocument
        )
        
        return result
