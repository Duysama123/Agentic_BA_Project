from pydantic import BaseModel, Field
from typing import List, Optional

class UIElement(BaseModel):
    id: str = Field(description="Unique ID in snake_case (e.g., btn_checkout, input_email)")
    type: str = Field(description="Component type (Supported: button, text_input, image, dropdown, text_label)")
    label: Optional[str] = Field(description="Text written on the component if readable (e.g., 'Checkout', 'Add to cart')")
    description: str = Field(description="Detailed description of the purpose, shape, or position of this component on the screen")

class WireframeAnalysis(BaseModel):
    page_name: str = Field(description="Predicted name of the interface page (e.g., Checkout Details Page)")
    elements: List[UIElement] = Field(description="List containing all distinct UI components appearing on the sketch")
    detected_user_flows: List[str] = Field(description="Predicted user behavior flows when interacting with the elements on this page")
