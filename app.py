import streamlit as st
import google.generativeai as genai
import json
import PyPDF2
from docx import Document
import re

# ==========================================
# 👇 TEACHER: PASTE YOUR GENERATED DATA HERE 👇
# ==========================================
LESSON_DATA = [
    {
        "word": "Awkward",
        "phonetic": "/O:kwd/",
        "chinese_meaning": "令人尴尬的；难对付的",
        "phrases": [
            "feel awkward",
            "an awkward situation"
        ],
        "fun_sentence": "My first attempt at dancing was so awkward that I accidentally stepped on my teacher's foot!"
    },
    {
        "word": "Impression",
        "phonetic": "/Impren/",
        "chinese_meaning": "印象；感想",
        "phrases": [
            "make an impression",
            "first impression"
        ],
        "fun_sentence": "I tried to make a good impression on the cat, but it just yawned and walked away."
    },
    {
        "word": "Concentrate",
        "phonetic": "/knsntreIt/",
        "chinese_meaning": "集中（注意力）；聚精会神",
        "phrases": [
            "concentrate on",
            "concentrate on your studies"
        ],
        "fun_sentence": "I can't concentrate on my homework when there's a squirrel doing parkour outside my window!"
    },
    {
        "word": "Outgoing",
        "phonetic": "/atgIN/",
        "chinese_meaning": "爱交际的；外向的",
        "phrases": [
            "an outgoing personality",
            "outgoing and friendly"
        ],
        "fun_sentence": "My outgoing dog greets everyone at the park, even the trees!"
    },
    {
        "word": "Anxious",
        "phonetic": "/Nks/",
        "chinese_meaning": "焦虑的；不安的",
        "phrases": [
            "anxious about",
            "feel anxious"
        ],
        "fun_sentence": "I felt anxious waiting for my pizza, worried they might have run out of cheese!"
    },
    {
        "word": "Suitable",
        "phonetic": "/su:tbl/",
        "chinese_meaning": "合适的；适用的",
        "phrases": [
            "suitable for",
            "find something suitable"
        ],
        "fun_sentence": "This tiny hat is not suitable for my enormous brain, but it looks funny!"
    },
    {
        "word": "Challenge",
        "phonetic": "/tlInd/",
        "chinese_meaning": "挑战；艰巨任务 (n.) / 怀疑；向……挑战 (vt.)",
        "phrases": [
            "face a challenge",
            "take on a challenge"
        ],
        "fun_sentence": "It was a real challenge to teach my cat to fetch, but now he brings me socks!"
    },
    {
        "word": "Confusing",
        "phonetic": "/knfju:zIN/",
        "chinese_meaning": "难以理解的；不清楚的",
        "phrases": [
            "a confusing situation",
            "find something confusing"
        ],
        "fun_sentence": "The instruction manual for my new gadget was so confusing, it told me to 'turn left at the imaginary unicorn.'"
    },
    {
        "word": "Responsible",
        "phonetic": "/rIspnsbl/",
        "chinese_meaning": "负责的；有责任的",
        "phrases": [
            "be responsible for",
            "a responsible student"
        ],
        "fun_sentence": "Being responsible for watering the plants means I sometimes forget, and they give me the 'leafy silent treatment.'"
    },
    {
        "word": "Accommodation",
        "phonetic": "/kmdeIn/",
        "chinese_meaning": "住处；停留处；膳宿",
        "phrases": [
            "student accommodation",
            "book accommodation"
        ],
        "fun_sentence": "Finding cheap accommodation for my pet squirrel was a challenge, especially since he demanded a nut-filled mini-fridge."
    },
    {
        "word": "Strategy",
        "phonetic": "/strtdi/",
        "chinese_meaning": "策略；策划",
        "phrases": [
            "marketing strategy",
            "a winning strategy"
        ],
        "fun_sentence": "My strategy for avoiding chores is to pretend I'm a statue, but my mom's strategy is to tickle me until I move."
    },
    {
        "word": "Literature",
        "phonetic": "/lItrt(r)/",
        "chinese_meaning": "文学；文学作品",
        "phrases": [
            "Chinese literature",
            "study literature"
        ],
        "fun_sentence": "I tried to read classic literature to my goldfish, but he seemed more interested in chasing bubbles."
    }
] 
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
