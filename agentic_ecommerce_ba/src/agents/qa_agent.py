import os
import sys
import json
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent
from schemas.qa_schema import QAAuditReport, QAStructuralCheck, QAConsistencyCheck, QADomainCheck, QADecision
from core.i18n import t, get_lang
from pydantic import BaseModel, Field
from typing import List, Tuple

class QAAgent(BaseAgent):
    """
    Tác tử QA Manager (3-Layer Validation & Quality Gate).
    Layer 1: Structural Validation (Pure Python IEEE 830 Completeness)
    Layer 2: Semantic Consistency Check (Pure Python text matching RTM Traceability)
    Layer 3: Domain Rule Validation (Local Keyword/ID Match Compliance & RAG Policy Verification)
    Completely local and offline to guarantee 0-token cost.
    """

    def __init__(self):
        super().__init__(role_name="QA Agent", model_name="gemini-2.5-flash")

    def _structural_validation(self, srs_dict: dict) -> List[QAStructuralCheck]:
        """Layer 1: Pure Python structural checks on SRS only."""
        checks = []
        
        # Check SRS: each FR must have main flow and alternative flows
        reqs = srs_dict.get('functional_requirements') or []
        for r in reqs:
            r_id = r.get('id', 'Unknown UC')
            
            # Check main_flow is not empty
            main_flow = r.get('main_flow') or []
            if not main_flow or len(main_flow) == 0:
                checks.append(QAStructuralCheck(
                    type="error", 
                    path=f"{r_id}.main_flow", 
                    message="Main flow is empty or missing"
                ))

            # Check alternative_flows is not empty
            alt_flows = r.get('alternative_flows') or []
            if not alt_flows or len(alt_flows) == 0:
                checks.append(QAStructuralCheck(
                    type="warning", 
                    path=f"{r_id}.alternative_flows", 
                    message="Alternative/exception flows are empty or missing"
                ))
                
        return checks

    def _consistency_check(self, vision_dict: dict, srs_dict: dict) -> List[QAConsistencyCheck]:
        """Layer 2: Check Vision ↔ SRS alignment (RTM Traceability)."""
        checks = []
        page_name = (vision_dict.get('page_name') or '').lower()
        
        reqs = srs_dict.get('functional_requirements') or []
        req_names = [(r.get('name') or '').lower() for r in reqs]
        req_desc = [(r.get('description') or '').lower() for r in reqs]
        
        combined_text = " ".join(req_names + req_desc)
        
        # Simple string matching to see if the page name is mentioned in SRS
        if page_name and len(page_name) > 3 and page_name not in combined_text:
            checks.append(QAConsistencyCheck(
                type="warning",
                message=f"Screen '{vision_dict.get('page_name')}' from wireframe has no obvious matching use case in SRS"
            ))
        
        # Check if all UI elements are referenced somewhere in requirements
        elements = vision_dict.get('elements') or []
        for el in elements:
            el_label = (el.get('label') or '').lower() if isinstance(el, dict) else (getattr(el, 'label', None) or '').lower()
            if el_label and len(el_label) > 3 and el_label not in combined_text:
                checks.append(QAConsistencyCheck(
                    type="warning",
                    message=f"UI element '{el_label}' from wireframe not referenced in any SRS requirement"
                ))
            
        return checks

    def _policy_compliance_check(self, srs_dict: dict, rag_context: str = "") -> Tuple[List[QADomainCheck], float, bool]:
        """
        Layer 3: Local check for RAG policies compliance.
        Completely offline string matching/keyword scanning.
        Returns:
            - List of QADomainCheck results
            - compliance_rate: float (percentage out of 100)
            - critical_policy_violated: bool
        """
        domain_checks = []
        
        # Determine page context to apply correct domain policies
        srs_context_str = str(srs_dict).lower()
        is_auth_page = any(word in srs_context_str for word in ['register', 'login', 'account', 'auth', 'đăng ký', 'đăng nhập'])
        
        if is_auth_page:
            static_policies = [
                {
                    "id": "DC-01",
                    "name": "Password Security Policy",
                    "message": "Verify that user password meets minimum complexity requirements (length, special characters)",
                    "keywords": ["password", "mật khẩu", "complex", "length", "ký tự", "secure", "hash"],
                    "severity": "CRITICAL"
                },
                {
                    "id": "DC-02",
                    "name": "Email Uniqueness Validation",
                    "message": "Ensure the system checks if the email is already registered before creating an account",
                    "keywords": ["email", "unique", "tồn tại", "trùng", "already", "exist", "duplicate"],
                    "severity": "CRITICAL"
                },
                {
                    "id": "DC-03",
                    "name": "Account Verification (OTP/Email)",
                    "message": "Define account activation flow via OTP or verification email",
                    "keywords": ["otp", "verify", "xác thực", "activate", "kích hoạt", "mã", "code"],
                    "severity": "HIGH"
                },
                {
                    "id": "DC-04",
                    "name": "Data Privacy & TOS Consent",
                    "message": "User must accept Terms of Service and Privacy Policy before registration",
                    "keywords": ["terms", "privacy", "tos", "điều khoản", "chính sách", "đồng ý", "accept", "consent"],
                    "severity": "MEDIUM"
                }
            ]
        else:
            # Core static e-commerce policies (Checkout/Cart invariants)
            static_policies = [
                {
                    "id": "DC-01",
                    "name": "Cart Inventory Validation",
                    "message": "Verify that cart checkout validates item stock availability",
                    "keywords": ["stock", "inventory", "quantity", "availab"],
                    "severity": "CRITICAL"
                },
                {
                    "id": "DC-02",
                    "name": "Secure Transaction Signature",
                    "message": "Ensure transaction completing uses secure checksum or digital signature validation",
                    "keywords": ["signature", "secure", "checksum", "payment gate", "hash", "secret", "payment", "idempotent", "auth"],
                    "severity": "CRITICAL"
                },
                {
                    "id": "DC-03",
                    "name": "Order Status Management",
                    "message": "Define explicit state transitions (e.g. pending, paid, failed, success)",
                    "keywords": ["status", "pending", "paid", "success", "failed", "completed"],
                    "severity": "HIGH"
                },
                {
                    "id": "DC-04",
                    "name": "Return/Refund Constraints",
                    "message": "Handle refund or cancellation window conditions",
                    "keywords": ["refund", "cancel", "return", "policy", "day"],
                    "severity": "MEDIUM"
                }
            ]
        
        # Concatenate all SRS text for keyword checking
        reqs = srs_dict.get('functional_requirements') or []
        srs_texts = []
        for r in reqs:
            srs_texts.append((r.get('name') or '').lower())
            srs_texts.append((r.get('description') or '').lower())
            for step in (r.get('main_flow') or []):
                srs_texts.append(step.lower())
            for alt in (r.get('alternative_flows') or []):
                if isinstance(alt, dict):
                    srs_texts.append((alt.get('condition') or '').lower())
                    srs_texts.extend([s.lower() for s in (alt.get('steps') or [])])
                else:
                    srs_texts.append(str(alt).lower())
                    
        nfrs = srs_dict.get('non_functional_requirements') or []
        for nfr in nfrs:
            srs_texts.append((nfr.get('description') or '').lower())
            
        brs = srs_dict.get('business_rules') or []
        for br in brs:
            srs_texts.append((br.get('description') or '').lower())
            
        srs_combined_text = " ".join(srs_texts)
        
        # Check static policies
        for policy in static_policies:
            passed = any(kw in srs_combined_text for kw in policy["keywords"])
            domain_checks.append(QADomainCheck(
                id=policy["id"],
                severity=policy["severity"],
                message=policy["message"],
                passed=passed
            ))
            
        # 2. Dynamic checks against retrieved RAG context policies
        rag_policies = []
        if rag_context:
            chunks = [c.strip() for c in rag_context.split("---") if c.strip()]
            for chunk in chunks:
                if len(chunk) > 10:
                    rag_policies.append(chunk)
                    
        total_retrieved_policies = len(rag_policies)
        addressed_policies_count = 0
        critical_policy_violated = False
        
        stop_words = {
            "the", "a", "an", "and", "or", "but", "if", "then", "else", "when", 
            "at", "by", "for", "with", "about", "against", "between", "into", 
            "through", "during", "before", "after", "above", "below", "to", 
            "from", "up", "down", "in", "out", "on", "off", "over", "under", 
            "again", "further", "then", "once", "here", "there", "all", "any", 
            "both", "each", "few", "more", "most", "other", "some", "such", 
            "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very"
        }
        
        for idx, policy_text in enumerate(rag_policies):
            policy_id = f"RAG-BR-{idx+1:02d}"
            
            lines = [l.strip() for l in policy_text.split("\n") if l.strip()]
            display_msg = lines[0] if lines else policy_text
            if len(display_msg) > 60:
                display_msg = display_msg[:57] + "..."
            
            critical_keywords = ["signature", "bypass", "inventory", "stock", "limit", "payment", "auth", "security", "fail", "cancel", "transaction"]
            is_critical = any(kw in policy_text.lower() for kw in critical_keywords)
            severity = "CRITICAL" if is_critical else "MEDIUM"
            
            words = re.findall(r'[a-zA-Z]{4,}', policy_text.lower())
            sig_words = [w for w in words if w not in stop_words]
            
            if sig_words:
                match_count = sum(1 for w in sig_words if w in srs_combined_text)
                match_rate = match_count / len(sig_words)
            else:
                match_rate = 1.0
                
            passed = match_rate >= 0.40
            
            domain_checks.append(QADomainCheck(
                id=policy_id,
                severity=severity,
                message=f"RAG Policy: {display_msg}",
                passed=passed
            ))
            
            if passed:
                addressed_policies_count += 1
            elif severity == "CRITICAL":
                critical_policy_violated = True
                
        # Calculate Compliance Rate (across all static and dynamic checks)
        total_policies = len(static_policies) + total_retrieved_policies
        passed_policies = sum(1 for dc in domain_checks if dc.passed)
        if total_policies > 0:
            compliance_rate = (passed_policies / total_policies) * 100.0
        else:
            compliance_rate = 100.0
            
        # Check static policies for critical failure as well
        for dc in domain_checks:
            if not dc.passed and dc.severity == "CRITICAL":
                critical_policy_violated = True
                
        return domain_checks, compliance_rate, critical_policy_violated

    def audit_system(self, vision_json: str, srs_json: str, rag_context: str = "") -> QAAuditReport:
        """Run the full 3-layer QA audit (Vision + SRS + RAG Context)."""
        try:
            v_dict = json.loads(vision_json) if isinstance(vision_json, str) else vision_json
            s_dict = json.loads(srs_json) if isinstance(srs_json, str) else srs_json
        except Exception:
            v_dict, s_dict = {}, {}

        # 1. Structural Validation (Layer 1)
        struct_checks = self._structural_validation(s_dict)
        structural_errors_count = sum(1 for c in struct_checks if c.type == "error")
        
        # 2. Consistency Validation (Layer 2)
        consist_checks = self._consistency_check(v_dict, s_dict)
        warnings_count = len(consist_checks)
        
        # Calculate total UI components (elements + page_name)
        elements = v_dict.get('elements', [])
        total_ui_components = len(elements)
        if v_dict.get('page_name'):
            total_ui_components += 1
            
        if total_ui_components > 0:
            entity_consistency_score = max(0.0, ((total_ui_components - warnings_count) / total_ui_components) * 100.0)
        else:
            entity_consistency_score = 100.0
        
        # 3. Domain Policy Compliance Check (Layer 3)
        domain_checks, domain_policy_compliance_rate, critical_policy_violated = self._policy_compliance_check(s_dict, rag_context)
        
        # 4. Edge-Case Density (Layer 4)
        reqs = s_dict.get('functional_requirements') or []
        total_alt_flows = 0
        total_reqs = len(reqs)
        for r in reqs:
            alt_flows = r.get('alternative_flows') or []
            total_alt_flows += len(alt_flows)
        edge_case_density = total_alt_flows / total_reqs if total_reqs > 0 else 0.0

        # Determine Decision based on Quality Gate Rules
        if structural_errors_count > 0 or critical_policy_violated:
            is_approved = False
            action = "retry_ba"
            reasons = []
            if structural_errors_count > 0:
                reasons.append(f"{structural_errors_count} structural errors detected")
            if critical_policy_violated:
                reasons.append("critical domain policies violated")
            reason = "Failed: " + ", ".join(reasons) + "."
        else:
            is_approved = True
            action = "approve"
            reason = "Passed: All structural checks and critical domain policies satisfied."

        decision = QADecision(action=action, reason=reason)
        
        report = QAAuditReport(
            is_approved=is_approved,
            structural_checks=struct_checks,
            consistency_checks=consist_checks,
            domain_checks=domain_checks,
            decision=decision,
            feedback_for_agents=reason,
            structural_errors_count=structural_errors_count,
            entity_consistency_score=entity_consistency_score,
            domain_policy_compliance_rate=domain_policy_compliance_rate,
            edge_case_density=round(edge_case_density, 2)
        )
        
        return report
