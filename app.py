import streamlit as st
import google.generativeai as genai
import json
import PyPDF2
from docx import Document
import re

# ==========================================
# 👇 TEACHER: PASTE YOUR GENERATED DATA HERE 👇
# ==========================================
LESSON_DATA = [] 
# (Currently empty. You will fill this in Step 3)
# ==========================================


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

# --- HELPER FUNCTIONS ---
def get_active_model_name(api_key):
    genai.configure(api_key=api_key)
    try:
        models = list(genai.list_models())
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name.lower(): return m.name
        return "models/gemini-pro"
    except: return "models/gemini-1.5-flash"

def extract_text(uploaded_file):
    text = ""
    try:
        if uploaded_file.name.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            for page in pdf_reader.pages: text += page.extract_text() or ""
        elif uploaded_file.name.endswith('.docx'):
            doc = Document(uploaded_file)
            for para in doc.paragraphs: text += para.text + "\n"
    except Exception as e: st.error(f"Error: {e}")
    return text

def get_gemini_response(api_key, text_content):
    model_name = get_active_model_name(api_key)
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    prompt = f"""
    Act as an English Teacher for Chinese students. Extract 8-12 difficult words.
    Return a JSON LIST. Format:
    [
      {{
        "word": "Word",
        "phonetic": "/.../",
        "chinese_meaning": "Meaning",
        "phrases": ["phrase 1", "phrase 2"],
        "fun_sentence": "Funny sentence."
      }}
    ]
    TEXT: {text_content[:5000]} 
    """
    try:
        response = model.generate_content(prompt)
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if match: return json.loads(match.group(0))
        return []
    except: return []

# --- MAIN APP LOGIC ---
def main():
    # CHECK: Is there data in LESSON_DATA?
    if LESSON_DATA:
        # ==========================================
        # 🎓 STUDENT VIEW (What students see)
        # ==========================================
        st.title("⚡ English Power-Up")
        st.caption("Lesson of the Week")
        
        tabs = st.tabs(["📖 Flashcards", "🧠 Quiz Mode"])
        
        with tabs[0]:
            for item in LESSON_DATA:
                st.markdown(f"""
                <div class="vocab-card">
                    <div class="word-title">{item.get('word')} <span style="font-size:14px;color:#666">{item.get('phonetic','')}</span></div>
                    <div class="meaning">{item.get('chinese_meaning')}</div>
                    <div style="margin-top:10px;color:#444">👉 {', '.join(item.get('phrases',[]))}</div>
                    <div class="funny-sentence">"{item.get('fun_sentence')}"</div>
                </div>
                """, unsafe_allow_html=True)

        with tabs[1]:
            st.info("Guess the word!")
            for i, item in enumerate(LESSON_DATA):
                blank = re.sub(re.escape(item['word']), "_______", item['fun_sentence'], flags=re.I)
                st.markdown(f"**{i+1}.** {blank}")
                if st.button(f"Check Answer {i+1}"):
                    st.success(f"{item['word']} ({item['chinese_meaning']})")
                st.divider()

    else:
        # ==========================================
        # 🛠 TEACHER VIEW (Generator)
        # ==========================================
        st.title("🛠 Teacher Generator")
        st.warning("You are in 'Generator Mode'. Students will only see what you generate here.")
        
        with st.sidebar:
            if "GOOGLE_API_KEY" in st.secrets:
                api_key = st.secrets["GOOGLE_API_KEY"]
            else:
                api_key = st.text_input("API Key", type="password")
            
            uploaded_file = st.file_uploader("Upload Lesson PDF/Docx", type=['pdf', 'docx'])

        if st.button("Generate Lesson Data", type="primary"):
            if api_key and uploaded_file:
                with st.spinner("Generating..."):
                    raw_text = extract_text(uploaded_file)
                    data = get_gemini_response(api_key, raw_text)
                    
                    if data:
                        st.success("Success! Copy the code below:")
                        st.markdown("### 👇 COPY EVERYTHING IN THIS BOX 👇")
                        
                        # Print the data formatted as Python code
                        code_to_copy = f"LESSON_DATA = {json.dumps(data, ensure_ascii=False, indent=4)}"
                        st.code(code_to_copy, language="python")
                        
                        st.markdown("### 🛑 Next Step:")
                        st.info("1. Copy the code above.\n2. Go to GitHub -> app.py.\n3. Delete 'LESSON_DATA = []'.\n4. Paste your code there.\n5. Commit changes.")
                    else:
                        st.error("AI failed. Try again.")

if __name__ == "__main__":
    main()
