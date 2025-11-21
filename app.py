import streamlit as st
import google.generativeai as genai
import json
import PyPDF2
from docx import Document
import io
import re

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Vocab Master",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    .vocab-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        border-left: 5px solid #6366f1;
        transition: transform 0.2s;
    }
    .vocab-card:hover { transform: translateY(-2px); box-shadow: 0 10px 15px rgba(0,0,0,0.1); }
    .word-title { font-size: 28px; font-weight: 800; color: #1e293b; margin-bottom: 5px; }
    .phonetic { font-family: monospace; color: #64748b; font-size: 16px; }
    .meaning { font-size: 20px; color: #4f46e5; font-weight: 600; margin-top: 10px; }
    .funny-sentence {
        background-color: #e0e7ff; color: #3730a3; padding: 10px;
        border-radius: 8px; font-style: italic; margin-top: 10px;
        border: 1px dashed #818cf8;
    }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---

def extract_text(uploaded_file):
    text = ""
    try:
        if uploaded_file.name.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
        elif uploaded_file.name.endswith('.docx'):
            doc = Document(uploaded_file)
            for para in doc.paragraphs:
                text += para.text + "\n"
    except Exception as e:
        st.error(f"Error reading file: {e}")
    return text

def get_gemini_response(api_key, text_content):
    # Configure API
    genai.configure(api_key=api_key)
    
    # USING THE LATEST STABLE MODEL FOR LATE 2025
    try:
        model = genai.GenerativeModel('gemini-2.5-flash') 
    except:
        # Fallback to 1.5 Pro if 2.5 is not active in your region yet
        model = genai.GenerativeModel('gemini-1.5-pro')

    prompt = f"""
    You are an expert English teacher for Chinese Senior High School students. 
    
    TASK: 
    1. Analyze the text and find the top 10 most difficult vocabulary words suitable for 'Gaokao'.
    2. For each word provide: Word, Phonetic, Chinese Definition, 2 Phrases, 1 Funny/Gen-Z Sentence.
    
    TEXT TO ANALYZE:
    {text_content[:10000]}

    OUTPUT FORMAT (Strict JSON):
    [
        {{
            "word": "English Word",
            "phonetic": "/.../",
            "chinese_meaning": "中文意思",
            "phrases": ["phrase 1", "phrase 2"],
            "fun_sentence": "Funny sentence here."
        }}
    ]
    """
    
    try:
        with st.spinner("🤖 AI is analyzing vocabulary..."):
            response = model.generate_content(prompt)
            # Clean JSON string
            json_text = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(json_text)
            return data
    except Exception as e:
        st.error(f"AI Error: {e}")
        return []

# --- MAIN APP ---
def main():
    with st.sidebar:
        st.title("📚 Teacher Setup")
        # Check secrets first, then ask user
        if "GOOGLE_API_KEY" in st.secrets:
            api_key = st.secrets["GOOGLE_API_KEY"]
            st.success("API Key loaded from Secrets!")
        else:
            api_key = st.text_input("Enter Gemini API Key", type="password")
            
        uploaded_file = st.file_uploader("Upload File (PDF/Word)", type=['pdf', 'docx'])
        
        if st.button("🚀 Generate", type="primary"):
            if not api_key:
                 st.warning("Please enter your API Key.")
            elif not uploaded_file:
                st.warning("Please upload a file.")
            else:
                raw_text = extract_text(uploaded_file)
                if raw_text:
                    st.session_state['vocab_data'] = get_gemini_response(api_key, raw_text)
                    # Clear old quiz answers when generating new set
                    keys_to_remove = [k for k in st.session_state.keys() if k.startswith('quiz_reveal_')]
                    for k in keys_to_remove:
                        del st.session_state[k]

    st.title("⚡ English Power-Up")
    
    if 'vocab_data' in st.session_state and st.session_state['vocab_data']:
        tab1, tab2 = st.tabs(["📖 Study", "🧠 Quiz"])
        
        with tab1:
            for item in st.session_state['vocab_data']:
                st.markdown(f"""
                <div class="vocab-card">
                    <div class="word-title">{item['word']} <span class="phonetic">{item.get('phonetic', '')}</span></div>
                </div>
                """, unsafe_allow_html=True)
                with st.expander(f"Reveal {item['word']}"):
                    st.write(f"**{item['chinese_meaning']}**")
                    st.write(f"*{', '.join(item['phrases'])}*")
                    st.info(item['fun_sentence'])

        with tab2:
            st.info("Can you guess the word based on the sentence?")
            for idx, item in enumerate(st.session_state['vocab_data']):
                # Replace word with underscores
                blank = re.sub(re.escape(item['word']), "_______", item['fun_sentence'], flags=re.I)
                st.markdown(f"**{idx+1}.** {blank}")
                
                # Button to reveal answer
                reveal_key = f"quiz_reveal_{idx}"
                if st.button(f"Check Answer {idx+1}", key=f"btn_{idx}"):
                    st.session_state[reveal_key] = True
                
                if st.session_state.get(reveal_key, False):
                    st.success(f"**{item['word']}**: {item['chinese_meaning']}")
                st.markdown("---")

if __name__ == "__main__":
    main()
```[[1](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQGrkuNGn0DaLqXd_5zn6PzJmj2kW4RE42IhMjCrLWRSdSP5PBL3dyCb8E6HkLhMOZnXU5laJxehfXm2SJxMbxD09tubXVXKI-3Soc3Vz8VG-O4XLFjoOw3E4e7StkbEdT2cJ8Obz58wkO1RgQ8xzHN_C7Mp_dznVtw0vt-j4AT3mR6FpFyV7463ryP2dGMUwsMKYIX6y3tEGfK5Wrfen9NvhD1kk9gLY5U0KPD58Qd3IsMR_g9DWi0%3D)]
