import streamlit as st
import google.generativeai as genai
import json
import PyPDF2
from docx import Document
import re

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Vocab Master", page_icon="⚡", layout="wide")

# --- CSS ---
st.markdown("""
<style>
    .vocab-card {
        background-color: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px;
        border-left: 5px solid #6366f1;
    }
    .word-title { font-size: 24px; font-weight: 800; color: #1e293b; }
    .meaning { color: #4f46e5; font-weight: 600; }
    .funny-sentence { background-color: #e0e7ff; padding: 10px; border-radius: 8px; font-style: italic; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# --- HELPER: AUTO-DETECT MODEL ---
def get_active_model_name(api_key):
    """automatically finds a working model name to avoid 404 errors"""
    genai.configure(api_key=api_key)
    try:
        # 1. Ask Google what models are available
        models = list(genai.list_models())
        
        # 2. Look for a 'generateContent' model, prefer 'flash' for speed
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name.lower():
                    return m.name
        
        # 3. If no flash, take the first available generic one (usually gemini-pro)
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                return m.name
                
        return "models/gemini-pro" # Absolute fallback
    except Exception as e:
        # If we can't list models, guess a safe standard
        return "models/gemini-1.5-flash"

# --- HELPER: EXTRACT TEXT ---
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
        st.error(f"File Read Error: {e}")
    return text

# --- MAIN AI FUNCTION ---
def get_gemini_response(api_key, text_content):
    # Auto-detect the correct model name
    model_name = get_active_model_name(api_key)
    
    # Configure
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    prompt = f"""
    Act as an English Teacher for Chinese students.
    Extract 8-10 difficult words from the text below.
    
    Return a JSON LIST. Format:
    [
      {{
        "word": "Example",
        "phonetic": "/Ig'za:mpl/",
        "chinese_meaning": "例子",
        "phrases": ["for example", "set an example"],
        "fun_sentence": "A funny sentence using the word Example."
      }}
    ]

    TEXT:
    {text_content[:5000]} 
    """
    
    try:
        response = model.generate_content(prompt)
        
        if not response.text:
            return []

        # Regex search for JSON list [...]
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        else:
            return []

    except Exception as e:
        st.error(f"AI Error ({model_name}): {e}")
        return []

# --- MAIN APP UI ---
def main():
    with st.sidebar:
        st.header("Teacher Setup")
        
        # Handle Secrets vs Input
        if "GOOGLE_API_KEY" in st.secrets:
            api_key = st.secrets["GOOGLE_API_KEY"]
            st.success("Key loaded automatically")
        else:
            api_key = st.text_input("API Key", type="password")

        uploaded_file = st.file_uploader("Upload PDF/Docx", type=['pdf', 'docx'])
        
        if st.button("Generate"):
            if not api_key or not uploaded_file:
                st.warning("Need Key and File!")
            else:
                with st.spinner("Finding best AI model & reading file..."):
                    raw_text = extract_text(uploaded_file)
                    if len(raw_text) < 10:
                        st.error("Text too short. Is this a scanned image?")
                    else:
                        data = get_gemini_response(api_key, raw_text)
                        if data:
                            st.session_state['vocab_data'] = data
                            st.success("Done!")
                        else:
                            st.error("AI failed to generate. Try again.")

    # Display Content
    if 'vocab_data' in st.session_state:
        tabs = st.tabs(["Flashcards", "Quiz"])
        
        with tabs[0]:
            for item in st.session_state['vocab_data']:
                st.markdown(f"""
                <div class="vocab-card">
                    <div class="word-title">{item.get('word','')} <span style="font-size:14px;color:#666">{item.get('phonetic','')}</span></div>
                    <div class="meaning">{item.get('chinese_meaning','')}</div>
                    <div style="margin-top:10px;color:#444">👉 {', '.join(item.get('phrases',[]))}</div>
                    <div class="funny-sentence">"{item.get('fun_sentence','')}"</div>
                </div>
                """, unsafe_allow_html=True)

        with tabs[1]:
            for i, item in enumerate(st.session_state['vocab_data']):
                word = item.get('word','')
                sent = item.get('fun_sentence','')
                blank = re.sub(re.escape(word), "_______", sent, flags=re.I)
                
                st.markdown(f"**{i+1}.** {blank}")
                if st.button(f"Reveal Answer {i+1}"):
                    st.success(f"{word} ({item.get('chinese_meaning','')})")
                st.divider()

if __name__ == "__main__":
    main()
