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

# --- FUNCTIONS ---

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

def get_gemini_response(api_key, text_content):
    genai.configure(api_key=api_key)
    
    # 1. Use the most stable model currently available
    # Try 'gemini-1.5-flash' first (standard), fallback to 'gemini-pro'
    model = genai.GenerativeModel('gemini-1.5-flash')

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
        
        # 2. DEBUG: If response is empty/blocked
        if not response.text:
            st.error("AI returned an empty response. This usually means a Safety Filter triggered.")
            return []

        # 3. ROBUST PARSING (The fix for your error)
        # Instead of trusting the whole string, we use Regex to find the [...] list
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
        else:
            # If no JSON found, show the raw text to debug
            st.warning("AI didn't return valid JSON. Here is what it said:")
            st.code(response.text)
            return []

    except Exception as e:
        st.error(f"Connection Error: {e}")
        return []

# --- MAIN APP ---
def main():
    with st.sidebar:
        st.header("Teacher Setup")
        
        # API Key Handling
        if "GOOGLE_API_KEY" in st.secrets:
            api_key = st.secrets["GOOGLE_API_KEY"]
            st.success("Key loaded!")
        else:
            api_key = st.text_input("API Key", type="password")

        uploaded_file = st.file_uploader("Upload PDF/Docx", type=['pdf', 'docx'])
        
        if st.button("Generate"):
            if not api_key or not uploaded_file:
                st.warning("Need Key and File!")
            else:
                with st.spinner("Reading file..."):
                    raw_text = extract_text(uploaded_file)
                    if len(raw_text) < 50:
                        st.error("Could not read text from this file! Is it a scanned image?")
                    else:
                        data = get_gemini_response(api_key, raw_text)
                        if data:
                            st.session_state['vocab_data'] = data
                            st.success("Done!")

    # Display
    if 'vocab_data' in st.session_state:
        tabs = st.tabs(["Flashcards", "Quiz"])
        
        with tabs[0]:
            for item in st.session_state['vocab_data']:
                st.markdown(f"""
                <div class="vocab-card">
                    <div class="word-title">{item['word']} <span style="font-size:14px;color:#666">{item.get('phonetic','')}</span></div>
                    <div class="meaning">{item['chinese_meaning']}</div>
                    <div style="margin-top:10px;color:#444">👉 {', '.join(item['phrases'])}</div>
                    <div class="funny-sentence">"{item['fun_sentence']}"</div>
                </div>
                """, unsafe_allow_html=True)

        with tabs[1]:
            for i, item in enumerate(st.session_state['vocab_data']):
                blank = re.sub(re.escape(item['word']), "_______", item['fun_sentence'], flags=re.I)
                st.markdown(f"**{i+1}.** {blank}")
                if st.button(f"Reveal Answer {i+1}"):
                    st.success(f"{item['word']} ({item['chinese_meaning']})")
                st.divider()

if __name__ == "__main__":
    main()
