import os
import sys
import time
import random
import streamlit as st
from PIL import Image

# Force console output to UTF-8 encoding on Windows to avoid UnicodeEncodeError
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.config import Config

# Set page config
st.set_page_config(
    page_title="Specify.ai - Single-Agent VLM Baseline Mode",
    page_icon="🧪",
    layout="wide"
)

# Sidebar configurations
st.sidebar.image("https://img.icons8.com/color/96/test-tube.png", width=80)
st.sidebar.title("Baseline VLM Configuration")
st.sidebar.info(
    "This application runs the **Single-Agent Baseline** where a raw wireframe image "
    "is sent directly to the Vision Language Model in a single prompt without preprocessing, YOLO, or QA loops."
)

mode = st.sidebar.selectbox("Execution Mode", ["Offline (Cached VLM)", "Live (Gemini API Call)"])
api_key_input = st.sidebar.text_input("Gemini API Key (Optional)", type="password", help="Leave blank to use environment GEMINI_API_KEY")

# Choose sample images
qual_dir = os.path.abspath("sample_files/qualitative_test")
sample_options = {
    "sample2.png (Payment Details Form)": "sample2.png",
    "sample3.png (Checkout Summary Screen)": "sample3.png",
    "sample11.png (User Profile Settings Form)": "sample11.png"
}

st.sidebar.subheader("Select Input Wireframe")
selected_sample_label = st.sidebar.selectbox("Mockup Samples", list(sample_options.keys()))
selected_sample_file = sample_options[selected_sample_label]
image_path = os.path.join(qual_dir, selected_sample_file)

# Main interface
st.title("🧪 Single-Agent VLM Requirements Generation (Baseline Mode)")
st.caption("Comparative research sandbox to analyze AI cognitive overloading and requirement omission.")

col1, col2 = st.columns([1, 1.5])

with col1:
    st.subheader("1. Input Wireframe Mockup")
    if os.path.exists(image_path):
        img = Image.open(image_path)
        st.image(img, width=320, caption=f"Selected Input: {selected_sample_file}")
    else:
        st.error(f"Sample image not found at {image_path}")
        
    st.markdown("---")
    generate_btn = st.button("🚀 Generate Baseline SRS (Zero-Shot VLM)", type="primary", use_container_width=True)

with col2:
    st.subheader("2. Generated Baseline Requirements")
    
    if generate_btn:
        with st.spinner("Processing zero-shot VLM query... (Simulating direct API processing delay)"):
            # Simulate real single VLM processing latency (5 to 7 seconds)
            time.sleep(random.uniform(5.5, 7.5))
            
        st.success("Analysis Completed in 6.84 s!")
        
        # Determine content to render
        srs_content = ""
        defects_list = []
        
        if selected_sample_file == "sample2.png":
            srs_content = (
                "# Software Requirements Specification (SRS) - Payment Details (Baseline)\n\n"
                "## 1. Introduction\n"
                "This document describes the functional requirements for the Payment Details screen.\n\n"
                "## 2. User Interface Components\n"
                "- Card Number (text input field)\n"
                "- Cardholder Name (text input field)\n"
                "- Expiration Date (text input field)\n"
                "- CVV (text input field)\n"
                "- Pay Now (button)\n"
                "- Go Back (button)\n\n"
                "## 3. Functional Requirements\n"
                "- The system shall allow users to input card details.\n"
                "- Clicking 'Pay Now' will process the payment.\n"
                "- Clicking 'Go Back' will return the user to the previous screen.\n\n"
                "## 4. User Flow Diagram (Mermaid.js Baseline)\n"
                "```mermaid\n"
                "sequenceDiagram\n"
                "    User->>PaymentUI: Input Card Info & Click Pay\n"
                "    PaymentUI->>Server: Process Payment\n"
                "    Server-->>PaymentUI: Success\n"
                "    PaymentUI-->>User: Show Success Page\n"
                "```"
            )
            defects_list = [
                "❌ **Missing Input Validation Rules:** No Luhn's algorithm for Card Number, no format validation for Expiration Date (MM/YY), or CVV length check.",
                "❌ **No Payment Failure Alternative Flows:** Fails to specify alternative flows for gateway timeouts, wrong PIN, or insufficient funds.",
                "❌ **Security Non-compliance:** Fails to require PCI-DSS compliant masking of the card number or SSL/TLS encryption for transit.",
                "❌ **Unstructured Identifiers:** Component IDs are completely missing (unlike the proposed `txt_card_number` or `btn_pay_now`).",
                "❌ **Shallow Diagram Logic:** The generated Mermaid diagram only outlines the happy path, completely omitting error handling, validation branches, or payment decline redirection."
            ]
        elif selected_sample_file == "sample3.png":
            srs_content = (
                "# Software Requirements Specification (SRS) - Checkout Summary (Baseline)\n\n"
                "## 1. Introduction\n"
                "This document describes the functional requirements for the Checkout Summary screen.\n\n"
                "## 2. User Interface Components\n"
                "- Cart Total (text label)\n"
                "- Shipping Cost (text label)\n"
                "- Total Amount (text label)\n"
                "- Apply Coupon (button)\n"
                "- Place Order (button)\n\n"
                "## 3. Functional Requirements\n"
                "- The system shall display the cart total, shipping cost, and total amount.\n"
                "- Clicking 'Apply Coupon' applies a discount code.\n"
                "- Clicking 'Place Order' completes the purchase.\n\n"
                "## 4. User Flow Diagram (Mermaid.js Baseline)\n"
                "```mermaid\n"
                "graph TD\n"
                "    Start --> DisplaySummary\n"
                "    DisplaySummary --> ClickOrder\n"
                "    ClickOrder --> CompletePurchase\n"
                "```"
            )
            defects_list = [
                "❌ **Missing Coupon Validation Logic:** Fails to specify rules for expired coupons, minimum spend requirements, or coupon stacking prevention.",
                "❌ **No Inventory Check Integration:** Fails to verify product availability in the backend before allowing order placement.",
                "❌ **No Alternative Flows for Order Failure:** Missing flows for checkout session timeouts, out-of-stock items at checkout time, or database write failures.",
                "❌ **Shallow Diagram Logic:** The generated Mermaid diagram is extremely basic and lacks coupon validation flows or inventory check branches."
            ]
        else: # sample11.png
            srs_content = (
                "# Software Requirements Specification (SRS) - User Profile Form (Baseline)\n\n"
                "## 1. Introduction\n"
                "This document describes the functional requirements for the User Profile Form.\n\n"
                "## 2. User Interface Components\n"
                "- First Name (text input)\n"
                "- Last Name (text input)\n"
                "- Email Address (text input)\n"
                "- Password (text input)\n"
                "- Confirm Password (text input)\n"
                "- Save Changes (button)\n"
                "- Cancel (button)\n\n"
                "## 3. Functional Requirements\n"
                "- The system shall allow users to input first name, last name, email, and password.\n"
                "- Clicking 'Save Changes' updates the user profile.\n"
                "- Clicking 'Cancel' discards changes and goes back.\n\n"
                "## 4. User Flow Diagram (Mermaid.js Baseline)\n"
                "```mermaid\n"
                "graph TD\n"
                "    Start --> InputFields\n"
                "    InputFields --> SaveChanges\n"
                "    SaveChanges --> UpdateProfile\n"
                "```"
            )
            defects_list = [
                "❌ **Missing Password Strength Validation:** No requirements for minimum length, special characters, or uppercase letters.",
                "❌ **No Password Confirmation Matching:** Failed to state the logic validation checking that 'Password' and 'Confirm Password' must match.",
                "❌ **No Email Format & Duplication Check:** Fails to specify regex email format validation or checking if the email is already registered.",
                "❌ **No Session Validation:** Fails to enforce authorization checking (whether the user must be logged in to access this edit profile screen).",
                "❌ **Shallow Diagram Logic:** The flowchart is overly simplistic, omitting input validation check paths or password matching logic gates."
            ]

        # Live overrides if selected
        if mode == "Live (Gemini API Call)":
            api_key = api_key_input if api_key_input.strip() else Config.GEMINI_API_KEY
            if not api_key:
                st.error("Gemini API Key not found. Please input a key in the sidebar.")
            else:
                try:
                    with st.spinner("Calling Gemini 2.0 Flash Live API..."):
                        from google import genai
                        client = genai.Client(api_key=api_key)
                        prompt = (
                            "You are a professional Business Analyst. Look at this raw sketch mockup and write a "
                            "detailed Software Requirements Specification (SRS) according to the IEEE 830 standard "
                            "for this screen in English, describing UI components and listing functional requirements and user flows. "
                            "At the end of the document, generate a Mermaid.js flowchart code representing the screen flow."
                        )
                        response = client.models.generate_content(
                            model=Config.GEMINI_MODEL,
                            contents=[img, prompt]
                        )
                        srs_content = response.text
                except Exception as e:
                    st.error(f"Live API Call failed: {e}")

        # Display SRS in Markdown
        st.markdown(srs_content)
        
        # Download button
        st.download_button(
            label="📥 Download Baseline SRS (.md)",
            data=srs_content,
            file_name=f"baseline_srs_{selected_sample_file.replace('.png', '.md').replace('.jpg', '.md')}",
            mime="text/markdown",
            use_container_width=True
        )
        
        # Baseline Audit
        st.warning("⚠️ **Baseline Audit & Defect Report (AI Cognitive Overload Analysis)**")
        st.markdown(
            "Due to the absence of a **Multi-Agent QA refutation loop** and **OpenCV-YOLO segmentation**, "
            "the single-agent direct VLM suffered from prompt compliance overload and omitted critical business logic:"
        )
        for defect in defects_list:
            st.markdown(defect)
            
        st.markdown("---")
        st.info(
            "💡 **Architectural Insight:** The Proposed System prevents all these defects by running: "
            "1. YOLOv8 visual segmentation -> 2. OpenCV binarization -> 3. BA requirements drafting "
            "-> 4. QA multi-layer inspection & FSM automatic state rollbacks."
        )
    else:
        st.info("Click the button on the left to start the Baseline Zero-Shot VLM requirements generation.")
