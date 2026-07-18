import streamlit as st
# import google.generativeai as genai
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
from PIL import Image
import io
import base64

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini API
# if API_KEY:
#     genai.configure(api_key=API_KEY)
# else:
#     st.error("❌ GEMINI_API_KEY not found in .env file")
#     st.stop()

# Page configuration
st.set_page_config(
    page_title="🍳 Recipe Suggester",
    page_icon="🍳",
    layout="wide",
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
with st.sidebar:
    st.title("📸 Image Upload")
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
            st.write("[LOG] User captured an image from the camera")
            st.success("✅ Photo captured successfully!")

# Main content area
if st.session_state.uploaded_image is not None:
    # Display uploaded image
    col1, col2 = st.columns([1, 2], gap="large")
    
    with col1:
        st.subheader("📷 Your Image")
        st.image(st.session_state.uploaded_image, use_container_width=True)
        
        if st.button("🔄 Clear Image", use_container_width=True):
            st.session_state.uploaded_image = None
            st.session_state.ingredients = None
            st.session_state.recipes = None
            st.rerun()
    
    with col2:
        st.subheader("🔍 Analyzing Image...")
        
        if st.session_state.ingredients is None:
            # Analyze image for ingredients
            with st.spinner("🤖 Using AI to identify ingredients..."):
              
                st.write("[LOG] Starting ingredient analysis with Gemini")
                # Convert image to bytes
                img_byte_arr = io.BytesIO()
                st.session_state.uploaded_image.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                    
                # Call Gemini API to identify ingredients
                # model = genai.GenerativeModel('gemini-3.0-flash')
                    
                st.write("[LOG] Sending image to Gemini for ingredient detection")
                # response = model.generate_content([
                #     "Analyze this image and identify all visible food ingredients. List each ingredient on a new line. Only list the ingredients, nothing else. If this is not a food image or no ingredients are visible, respond with 'No food ingredients detected'.",
                #     {
                #         "mime_type": "image/png",
                #         "data": img_byte_arr.getvalue()
                #     }
                # ])
                    
                # ingredients_text = response.text.strip()

                raw_bytes = img_byte_arr.getvalue()

                b64_string = base64.b64encode(raw_bytes).decode("utf-8")

                client = genai.Client(api_key=API_KEY)

                MODEL_ID = "gemini-3.5-flash"


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


                st.write(interaction.output_text)

                    
                if "No food ingredients detected" in ingredients_text:
                    st.warning("⚠️ No food ingredients detected in the image. Please upload an image with food items.")
                    st.session_state.ingredients = []
                else:
                    st.session_state.ingredients = [ing.strip() for ing in ingredients_text.split('\n') if ing.strip()]
                    print(f"[LOG] Ingredients detected: {st.session_state.ingredients}")
                    st.success("✅ Ingredients identified!")
                
                
        
        # Display identified ingredients
        if st.session_state.ingredients:
            st.write("### 🥘 Identified Ingredients:")
            
            # Display ingredients as badges
            ingredient_html = ""
            for ingredient in st.session_state.ingredients:
                ingredient_html += f'<span class="ingredient-badge">{ingredient}</span>'
            
            st.markdown(ingredient_html, unsafe_allow_html=True)
            
            # Suggest recipes button
            if st.button("👨‍🍳 Suggest Recipes", use_container_width=True, type="primary"):
                st.session_state.recipes = None  # Reset recipes to fetch new ones
    
    # Recipe suggestions
    if st.session_state.ingredients and len(st.session_state.ingredients) > 0:
        st.divider()
        
        if st.session_state.recipes is None:
            with st.spinner("👨‍🍳 Generating recipe suggestions..."):
                try:
                    print("[LOG] Starting recipe generation with Gemini")
#                     model = genai.GenerativeModel('gemini-3.0-flash')
                    
#                     ingredients_list = ", ".join(st.session_state.ingredients)
                    
#                     print("[LOG] Sending ingredient list to Gemini for recipe suggestions")
#                     response = model.generate_content(f"""Based on these ingredients: {ingredients_list}

# Suggest exactly 2 delicious recipes. For each recipe, provide:

# 1. Recipe Name
# 2. Cuisine Type
# 3. Difficulty Level (Easy/Medium/Hard)
# 4. Prep Time (in minutes)
# 5. Cook Time (in minutes)
# 6. Step-by-step instructions (numbered list, be detailed)
# 7. Optional ingredients that could enhance the dish

# Format the response clearly with these exact sections for each recipe separated by "---".
# Make the recipes practical and achievable with the given ingredients.""")
                    
                    # st.session_state.recipes = response.text
                    print(f"[LOG] Recipe suggestions generated: {st.session_state.recipes[:150]}...")
                    
                except Exception as e:
                    st.error(f"❌ Error generating recipes: {str(e)}")
                    st.session_state.recipes = None
        
        # Display recipes
        if st.session_state.recipes:
            st.subheader("👨‍🍳 Recipe Suggestions")
            
            # Split recipes by separator
            recipes_list = st.session_state.recipes.split("---")
            
            # Create tabs for each recipe
            if len(recipes_list) >= 2:
                tab1, tab2 = st.tabs([f"Recipe {i+1}" for i in range(min(2, len(recipes_list)))])
                
                tabs = [tab1, tab2]
                for idx, (tab, recipe) in enumerate(zip(tabs, recipes_list[:2])):
                    with tab:
                        st.markdown(f"""
<div class="recipe-card">
{recipe}
</div>
""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
<div class="recipe-card">
{st.session_state.recipes}
</div>
""", unsafe_allow_html=True)
            
            # Download recipes button
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Download Recipes as Text", use_container_width=True):
                    st.download_button(
                        label="Click to Download",
                        data=st.session_state.recipes,
                        file_name="recipes.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
            
            with col2:
                if st.button("🔄 Get Different Recipes", use_container_width=True):
                    st.session_state.recipes = None
                    st.rerun()

else:
    # Initial state - show instructions
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.subheader("📸 How It Works")
        
        with st.container(border=True):
            st.write("""
1. **📷 Upload or Capture** - Upload an image or take a photo of your ingredients
2. **🤖 AI Analysis** - Our AI identifies all the ingredients in the image
3. **👨‍🍳 Get Recipes** - Receive 2 delicious recipe suggestions
4. **📋 Follow Steps** - Read detailed step-by-step instructions
            """)
    
    with col2:
        st.subheader("✨ Features")
        
        with st.container(border=True):
            st.write("""
✅ **Quick & Easy** - Upload in seconds
✅ **AI-Powered** - Uses advanced computer vision
✅ **Detailed Recipes** - Full instructions with tips
✅ **Multiple Options** - Get 2 different recipes
✅ **Downloadable** - Save recipes for later
            """)
    
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