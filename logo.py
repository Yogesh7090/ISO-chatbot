import streamlit as st
import base64
 
def add_logo():
    # Path to your logo image
    image_path = "oman_lng.png"  # Ensure this path is correct
    website_url = "https://omanlng.co.om/en/Pages/home.aspx"  # Replace with your desired URL
    catalytics_url = "https://www.linkedin.com/company/catalytics-datum/posts/?feedView=all"  # Replace with the desired URL for Catalytics Datum
 
    # Load the image and convert to base64
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode()
 
    with st.sidebar:
        # Leave space for other sidebar content above the logo
        st.markdown("<div style='height: calc(40vh - 160px);'></div>", unsafe_allow_html=True)
 
        # Create a clickable logo using an anchor tag
        logo_html = f"""
            <a href='{website_url}' target='_blank' style= 'margin-left:20%;'>
                <img src='data:image/png;base64,{encoded_image}' width='150' />
            </a>
        """
        st.markdown(logo_html, unsafe_allow_html=True)
 
        # Create a clickable text link for Catalytics Datum
        catalytics_html = f"""
                <br>
                <br><br><br><br><br><br>
                <a href='{catalytics_url}' target='_blank'>
                    <em>Powered by: Catalytics Datum Private Ltd</em>
                </a>
           
        """
        st.markdown(catalytics_html, unsafe_allow_html=True)