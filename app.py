import streamlit as st
import google.generativeai as genai
import json
import PyPDF2
from docx import Document
import re

# ==========================================
# 📚 UNIT DATABASE (Paste your generated lists here)
# ==========================================

UNIT_DATA = {
    
    # Example Unit (You can delete this later)
    "Demo Unit": [
        {"word": "Resilient", "phonetic": "/rɪˈzɪljənt/", "chinese_meaning": "有弹性的；能复原的", "phrases": ["remain resilient", "resilient economy"], "fun_sentence": "I thought I was resilient until I saw my math score."},
        {"word": "Ambiguous", "phonetic": "/æmˈbɪɡjuəs/", "chinese_meaning": "模棱两可的", "phrases": ["ambiguous attitude", "ambiguous answer"], "fun_sentence": "Her reply to 'do you like him' was so ambiguous even the FBI couldn't decode it."}
    ],

    # PASTE NEW UNITS BELOW THIS LINE ----------------
    
    # "Unit 1": [ ... paste code here ... ],
    # "Unit 2": [ ... paste code here ... ],

}

# ==========================================
# ⚙️ APP SETUP
# ==========================================
st.set_page_config(page_title="Vocab Master", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    .vocab-card {
        background-color: white; padding: 20px; border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 15px;
        border-left: 5px solid #6366f1;
    }
    .word-header { display: flex; justify-content: space-between; align-items: center; }
    .word-text { font-size: 26px; font-weight: 800; color: #1e293b; }
    .phonetic { font-family: monospace; color: #64748b; font-size: 16px; background: #f1f5f9; padding: 2px 8px; border-radius: 4px; }
    .meaning { color: #4f46e5; font-size: 18px; font-weight: 600; margin-top: 5px;}
    .example-box { background-color: #eef2ff; padding: 12px; border-radius: 8px; font-style: italic; margin-top: 12px; color: #3730a3; border: 1px dashed #c7d2fe; }
    .phrase-box { margin-top: 8px; color: #475569; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def get_active_model_name(api_key):
    genai.configure(api_key=api_key)
    try:
        models = list(genai.list_models())
        for m in models:
            if 'generateContent' in m.supported_generation_methods and 'flash' in m.name.lower():
                return m.name
        return "models/gemini-1.5-flash"
    except: return "models/gemini-1.5-flash"

def extract_text(uploaded_file):
    text = ""
    try:
        if uploaded_file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages: text += page.extract_text() or ""
        elif uploaded_file.name.endswith('.docx'):
            doc = Document(uploaded_file)
            for para in doc.paragraphs: text += para.text + "\n"
    except: pass
    return text

def generate_vocab(api_key, text, count):
    model_name = get_active_model_name(api_key)
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    
    prompt = f"""
    Act as a cool English teacher. Extract exactly {count} key vocabulary words from the text.
    Target Audience: Chinese Senior High School (Gaokao level).
    
    Return JSON LIST:
    [
      {{
        "word": "Word",
        "phonetic": "/IPA/",
        "chinese_meaning": "Precise Chinese Meaning",
        "phrases": ["phrase 1", "phrase 2"],
        "fun_sentence": "A funny, memorable sentence relating to student life/pop culture."
      }}
    ]
    TEXT: {text[:8000]}
    """
    try:
        response = model.generate_content(prompt)
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        return json.loads(match.group(0)) if match else []
    except: return []

# --- MAIN NAVIGATION ---
def main():
    # Sidebar Navigation
    with st.sidebar:
        st.title("📚 Library")
        mode = st.radio("Mode:", ["Student View", "Teacher Generator"])
        
        if mode == "Student View":
            selected_unit = st.selectbox("Select Unit:", list(UNIT_DATA.keys()))
        
        # KEY HANDLING (Load from secrets or ask user)
        api_key = st.secrets.get("GOOGLE_API_KEY", None)
        if not api_key:
            api_key = st.text_input("API Key (Teacher Only)", type="password")

    # --- MODE 1: STUDENT VIEW ---
    if mode == "Student View":
        data = UNIT_DATA.get(selected_unit, [])
        st.title(f"📖 {selected_unit}")
        
        if not data:
            st.error("This unit is empty.")
            return

        # TABS: Separate Reading from Testing
        tab_read, tab_quiz = st.tabs(["👀 Review Words", "📝 Quiz Mode"])

        with tab_read:
            for item in data:
                # Beautiful Card UI
                st.markdown(f"""
                <div class="vocab-card">
                    <div class="word-header">
                        <span class="word-text">{item['word']}</span>
                        <span class="phonetic">{item.get('phonetic','')}</span>
                    </div>
                    <div class="meaning">{item['chinese_meaning']}</div>
                    <div class="phrase-box">📌 {', '.join(item.get('phrases',[]))}</div>
                    <div class="example-box">"{item['fun_sentence']}"</div>
                </div>
                """, unsafe_allow_html=True)

        with tab_quiz:
            st.caption("Cover the screen and guess!")
            for i, item in enumerate(data):
                # Create blank sentence
                blank = re.sub(re.escape(item['word']), "_______", item['fun_sentence'], flags=re.I)
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{i+1}.** {blank}")
                with col2:
                    if st.button(f"Reveal #{i+1}"):
                        st.info(f"{item['word']} - {item['chinese_meaning']}")
                st.divider()

    # --- MODE 2: TEACHER GENERATOR ---
    elif mode == "Teacher Generator":
        st.title("🛠 Generate New Unit")
        st.info("Upload a file, generate the list, and paste the code into 'UNIT_DATA' in app.py")
        
        uploaded_file = st.file_uploader("Upload PDF/Word")
        word_count = st.slider("How many words?", 5, 30, 15)
        unit_name = st.text_input("Name this Unit (e.g., 'Unit 3')", "New Unit")
        
        if st.button("Generate Code"):
            if not api_key or not uploaded_file:
                st.warning("Missing API Key or File")
            else:
                with st.spinner("Analyzing text..."):
                    raw_text = extract_text(uploaded_file)
                    new_data = generate_vocab(api_key, raw_text, word_count)
                    
                    if new_data:
                        st.success("Generated! Copy the code below:")
                        # Format the output to be easily copy-pasteable
                        json_str = json.dumps(new_data, ensure_ascii=False, indent=4)
                        code_block = f'"{unit_name}": {json_str},'
                        st.code(code_block, language="python")
                        st.warning("Copy the text above and paste it inside the UNIT_DATA dictionary in app.py")
                    else:
                        st.error("AI failed. Try fewer words or a different file.")

if __name__ == "__main__":
    main()
