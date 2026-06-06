from pydantic import BaseModel, Field

class DiagramOutput(BaseModel):
    flowchart_diagram: str = Field(description="Mermaid.js source code for the Flowchart diagram describing the branching logical flow")
    sequence_diagram: str = Field(description="Mermaid.js source code for the Sequence Diagram describing the interaction between Actors and the System")
    diagram_explanation: str = Field(description="A short paragraph (1-2 sentences) explaining the diagrams above")
