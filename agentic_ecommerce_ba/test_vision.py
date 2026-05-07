import streamlit as st
import cv2
import numpy as np
import os
import sys
import tempfile

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.vision_utils.enhancer import resize_image, binarize_image, denoise_image
from src.vision_utils.image_cropper import find_ui_components, draw_bounding_boxes
from src.agents.vision_agent import VisionAgent
from src.core.i18n import t, init_language_selector

def main():
    st.set_page_config(page_title=t("vision_page_title"), layout="wide")
    init_language_selector()
    
    st.title(t("vision_title"))
    st.write(t("vision_desc"))

    if 'vision_agent' not in st.session_state:
        try:
            st.session_state.vision_agent = VisionAgent()
        except Exception as e:
            st.error(f"{t('error_init_vision')}: {e}")
            st.stop()

    uploaded_file = st.file_uploader(t("vision_upload"), type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        image_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        img_cv2 = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
        
        resized_img = resize_image(img_cv2)
        denoised_img = denoise_image(resized_img)
        binary_img = binarize_image(denoised_img)
        
        st.markdown("---")
        st.write(t("vision_opencv_title"))
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.image(cv2.cvtColor(resized_img, cv2.COLOR_BGR2RGB), caption=t("vision_cap_original"), use_container_width=True)
        with col2:
            st.image(cv2.cvtColor(denoised_img, cv2.COLOR_BGR2RGB), caption=t("vision_cap_denoise"), use_container_width=True)
        with col3:
            st.image(binary_img, caption=t("vision_cap_binary"), use_container_width=True, channels="GRAY")
            
        min_area = st.slider(t("vision_slider_label"), min_value=50, max_value=5000, value=500, step=50)
        boxes = find_ui_components(binary_img, min_area=min_area)
        result_img = draw_bounding_boxes(resized_img, boxes)
        
        st.image(cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB), caption=t("vision_opencv_result", count=len(boxes)), use_container_width=True)
            
        st.markdown("---")
        st.write(t("vision_gemini_title"))
        user_notes = st.text_input(t("vision_notes_label"), "")
        
        if st.button(t("vision_btn_analyze"), type="primary", use_container_width=True):
            if 'vision_agent' in st.session_state:
                with st.spinner(t("vision_spinner")):
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                            tmp.write(uploaded_file.getbuffer())
                            tmp_path = tmp.name
                            
                        analysis_result = st.session_state.vision_agent.analyze_wireframe(tmp_path, user_notes)
                        
                        st.success(t("vision_success"))
                        st.write(t("vision_page_name"))
                        st.info(analysis_result.page_name)
                        
                        st.write(t("vision_components"))
                        components = [el.model_dump() for el in analysis_result.elements]
                        st.table(components)
                        
                        st.write(t("vision_flows"))
                        for flow in analysis_result.detected_user_flows:
                            st.write(f"- {flow}")
                            
                    except Exception as e:
                        st.error(f"{t('error_gemini')}: {e}")
                    finally:
                        try:
                            os.unlink(tmp_path)
                        except:
                            pass

if __name__ == "__main__":
    main()
