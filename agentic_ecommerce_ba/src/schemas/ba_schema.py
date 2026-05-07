from pydantic import BaseModel, Field
from typing import List, Optional

class SRSTerm(BaseModel):
    term: str = Field(description="Term or acronym")
    definition: str = Field(description="Definition or explanation")

class UserClass(BaseModel):
    name: str = Field(description="Name of the user class (e.g., Admin, Guest)")
    characteristics: str = Field(description="Description of the user class characteristics")

class AlternativeFlow(BaseModel):
    condition: str = Field(description="Condition triggering the alternative flow")
    steps: List[str] = Field(description="Steps taken in this alternative flow")

class FunctionalRequirement(BaseModel):
    id: str = Field(description="Requirement ID, e.g., FR-001")
    name: str = Field(description="Name of the feature")
    actor: str = Field(description="Primary actor executing this feature")
    description: str = Field(description="Standard description: 'The system shall...'")
    pre_conditions: List[str] = Field(description="Pre-conditions before execution")
    post_conditions: List[str] = Field(description="Post-conditions after successful execution")
    main_flow: List[str] = Field(description="Main success scenario steps")
    alternative_flows: List[AlternativeFlow] = Field(description="Alternative or exception flows")
    priority: str = Field(description="Priority: High / Medium / Low")

class NonFunctionalRequirement(BaseModel):
    id: str = Field(description="NFR ID, e.g., NFR-001")
    type: str = Field(description="Category: Performance, Security, Usability, etc.")
    description: str = Field(description="Description of the non-functional requirement")
    metric: str = Field(description="Measurable metric (if any)")
    
class BusinessRule(BaseModel):
    id: str = Field(description="Rule ID, e.g., BR-001")
    name: str = Field(description="Rule Name")
    description: str = Field(description="Rule description")

class SRSIntroduction(BaseModel):
    purpose: str = Field(description="Purpose of this document")
    glossary: List[SRSTerm] = Field(description="Glossary of terms and acronyms")
    intended_audience: str = Field(description="Intended audience and reading suggestions")
    project_scope: str = Field(description="Scope of the software project")

class SRSOverallDescription(BaseModel):
    product_perspective: str = Field(description="Product perspective and context")
    product_functions: List[str] = Field(description="High-level summary of major product functions")
    user_classes: List[UserClass] = Field(description="User classes and characteristics")
    operating_environment: str = Field(description="Operating environment constraints")
    design_constraints: List[str] = Field(description="Design and implementation constraints")
    assumptions_dependencies: List[str] = Field(description="Assumptions and dependencies")

class SRSDocument(BaseModel):
    system_name: str = Field(description="System Name")
    version: str = Field(description="Document Version (e.g., 1.0.0)")
    introduction: SRSIntroduction = Field(description="Section 1: Introduction")
    overall_description: SRSOverallDescription = Field(description="Section 2: Overall Description")
    functional_requirements: List[FunctionalRequirement] = Field(description="Section 3: Detailed Functional Requirements")
    non_functional_requirements: List[NonFunctionalRequirement] = Field(description="Section 4: Non-Functional Requirements")
    business_rules: List[BusinessRule] = Field(description="Section 5: Business Rules")
