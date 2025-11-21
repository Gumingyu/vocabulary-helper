import streamlit as st
import google.generativeai as genai
import json
import PyPDF2
from docx import Document
import io

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Vocab Master 3000",
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
    
    # UPDATED MODEL NAME HERE:
    try:
        model = genai.GenerativeModel('gemini-2.5-flash') 
    except:
        # Fallback if 2.5 isn't available in your region yet, try 1.5-pro
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
            if not api_key or not uploaded_file:
                st.warning("Missing API Key or File")
            else:
                raw_text = extract_text(uploaded_file)
                if raw_text:
                    st.session_state['vocab_data'] = get_gemini_response(api_key, raw_text)
                    st.session_state['show_answers'] = {}

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
            for idx, item in enumerate(st.session_state['vocab_data']):
                import re
                blank = re.sub(re.escape(item['word']), "_______", item['fun_sentence'], flags=re.I)
                st.markdown(f"**Q{idx+1}:** {blank}")
                if st.button(f"Check Answer {idx+1}"):
                    st.success(f"{item['word']} - {item['chinese_meaning']}")

if __name__ == "__main__":
    main()
```[[2](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQFcXLxArErFj0DjwMgPXmzjOJjEyRBXzxb3JAN6lo6y7Z9JENGkt8eSkXVwwx1g7I7bWTwJ0yeUnMMnV-Kz3lNC62EUwtjqPVFEeOFBvzfmCnGleAtsy-vLqb6G7CzmS2xGpoBxJiI7tm085iGS5as2Mn9WxDLdP2tvQULBUS2K3IEgc1wbQUexSbpwMAyg01bnfFjR08FM_CJpwiAFckRDKhBEW_EChT2qgJh3RPH3TRbLQq-fh2T1)]
