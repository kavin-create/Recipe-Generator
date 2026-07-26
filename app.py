import streamlit as st
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
from PIL import Image
import io
import base64
import re


load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

recipe_prompt = """
Based on these ingredients:

ignore non food items

do not add any other text

Suggest exactly 4 different delicious recipes. For each recipe, provide:

1. Recipe Name
2. Cuisine Type
3. Difficulty Level (Easy/Medium/Hard)
4. Prep Time (in minutes)
5. Cook Time (in minutes)
6. Step-by-step instructions (numbered list, be detailed)
7. Optional ingredients that could enhance the dish

Separate each recipe with "---RECIPE_BREAK---"

Make the recipes practical and achievable with the given ingredients."""

# Page configuration
st.set_page_config(
    page_title="🧑‍🍳 Recipe Suggester",
    page_icon="🍳",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    .recipe-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin-bottom: 15px;
    }
    .ingredient-badge {
        display: inline-block;
        background-color: #667eea;
        color: white;
        padding: 5px 12px;
        border-radius: 20px;
        margin: 5px 5px 5px 0;
        font-size: 0.9em;
    }
    .instruction-step {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        border-left: 4px solid #764ba2;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "ingredients" not in st.session_state:
    st.session_state.ingredients = None
if "recipes" not in st.session_state:
    st.session_state.recipes = None
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

# Header
st.markdown("""
<div class="main-header">
    <h1>🍳 AI Recipe Suggester</h1>
    <p>Upload a photo of your ingredients and get delicious recipe suggestions!</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
#  st.title("📸 Image Upload")
st.write("Choose how you want to provide an image:")
    
upload_option = st.radio(
    "Select image source:",
    ["Upload File", "Use Camera"],
    label_visibility="collapsed"
)
    
image = None
    
if upload_option == "Upload File":
    uploaded_file = st.file_uploader(
        "Choose an image of your ingredients",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=False
    )
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.session_state.uploaded_image = image
        st.write("[LOG] User uploaded an image file")
        st.success("✅ Image uploaded successfully!")
    
else:
    camera_image = st.camera_input("Take a picture of your ingredients")
    if camera_image is not None:
        image = Image.open(camera_image)
        st.session_state.uploaded_image = image
        st.success("✅ Photo captured successfully!")

if(st.session_state.uploaded_image!=None):
    st.subheader("📷 Your Image")
    st.image(st.session_state.uploaded_image)
        
    if st.button("🔄 Clear Image", use_container_width=True):
        st.session_state.uploaded_image = None
        st.session_state.ingredients = None
        st.session_state.recipes = None
        st.rerun()
    
    
    if st.session_state.ingredients is None:
        # Analyze image for ingredients
        with st.spinner("🤖 Using AI to identify ingredients..."):
            st.subheader("🔍 Analyzing Image...")
            st.write("[LOG] Starting ingredient analysis with Gemini")
            # Convert image to bytes
            img_byte_arr = io.BytesIO()
            st.session_state.uploaded_image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
                        
            st.write("[LOG] Sending image to Gemini for ingredient detection")
            raw_bytes = img_byte_arr.getvalue()

            b64_string = base64.b64encode(raw_bytes).decode("utf-8")

            client = genai.Client(api_key=API_KEY)

            MODEL_ID = "gemini-3.1-flash-lite"


            interaction = client.interactions.create(
                model=MODEL_ID,
                input=[
                        {
                            "type": "text", 
                            "text": "Analyze this image and list ONLY the ingredients visible. Return the response as a simple comma-separated list with no additional text, explanations, or labels.Example format: tomatoes, potatoes, onions, carrots"
                        },
                        {
                            "type": "image", 
                            "data": b64_string,       # Your base64 data string
                            "mime_type": "image/png"   # Explicitly set to image/png since you saved as PNG
                        }
                    ]
            )
            print(f"Number of steps: {len(interaction.steps)}")
            for j, step in enumerate(interaction.steps):
                print(f"  Step {j}: type={step.type}")
            st.session_state.ingredients = interaction.output_text.strip().split(",") if interaction.output_text.strip() else []
            st.write(interaction.output_text)        

                    
    if "No food ingredients detected" in st.session_state.ingredients:
        st.warning("⚠️ No food ingredients detected in the image. Please upload an image with food items.")
        st.session_state.ingredients = []
    else:
        st.success("✅ Ingredients identified!")
        ingredients_text = st.text_area("Raw Gemini Response", value= " ".join(st.session_state.ingredients), height=150)
        st.session_state.ingredients = [ing.strip() for ing in ingredients_text.split('\n') if ing.strip()]
        print(f"[LOG] Ingredients detected: {st.session_state.ingredients}")
        if st.button("Done"):
            with st.spinner("curating recipes"):
                st.write("the ingredients are: ", st.session_state.ingredients[0])
                client = genai.Client(api_key=API_KEY)
                MODEL_ID = "gemini-3.1-flash-lite"
                interaction = client.interactions.create(
                model=MODEL_ID,
                input=[
                        {
                            "type": "text", 
                            "text": st.session_state.ingredients[0]+recipe_prompt
                        
                        }
                    ]
            )
                st.session_state.recipes = interaction.output_text.strip().split("---RECIPE_BREAK---") if interaction.output_text.strip() else []
                st.session_state.recipes = [r.strip() for r in st.session_state.recipes if r.strip()]
                # st.write(interaction.output_text)
                tabs = st.tabs([f"Recipe {i+1}" for i in range(len(st.session_state.recipes))])
 
                for idx, tab in enumerate(tabs):
                    with tab:
                        st.markdown(st.session_state.recipes[idx])
    
st.divider()
    
    # Show example usage
st.subheader("💡 Example")
st.info("Try uploading a photo of ingredients like tomatoes, onions, and garlic to get pasta or curry recipes!")

# Footer
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🍳 Recipe Suggester v1.0")
with col2:
    st.caption("Powered by Google Gemini AI")
with col3:
    st.caption("Happy Cooking! 👨‍🍳")