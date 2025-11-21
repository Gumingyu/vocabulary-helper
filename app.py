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

# --- CUSTOM CSS FOR "PRETTY" UI ---
st.markdown("""
<style>
    /* General App Styling */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Card Container Styling */
    .vocab-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        border-left: 5px solid #6366f1; /* Indigo accent */
        transition: transform 0.2s;
    }
    .vocab-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px rgba(0,0,0,0.1);
    }

    /* Text Styling */
    .word-title {
        font-size: 28px;
        font-weight: 800;
        color: #1e293b;
        margin-bottom: 5px;
    }
    .phonetic {
        font-family: monospace;
        color: #64748b;
        font-size: 16px;
    }
    .meaning {
        font-size: 20px;
        color: #4f46e5;
        font-weight: 600;
        margin-top: 10px;
    }
    .funny-sentence {
        background-color: #e0e7ff; /* Light indigo bg */
        color: #3730a3;
        padding: 10px;
        border-radius: 8px;
        font-style: italic;
        margin-top: 10px;
        border: 1px dashed #818cf8;
    }
    .tag {
        display: inline-block;
        background: #f1f5f9;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
        color: #475569;
        margin-right: 5px;
    }
    
    /* Hide default Streamlit elements we don't need */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---

def extract_text(uploaded_file):
    """Extracts text from PDF or DOCX."""
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
    """Sends text to Gemini and asks for structured JSON vocabulary."""
    genai.configure(api_key=api_key)
    
    # Use a model optimized for speed and JSON structure
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
    You are an expert English teacher for Chinese Senior High School students. 
    
    TASK: 
    1. Analyze the following text and identify the top 10-15 most important/difficult vocabulary words suitable for the 'Gaokao' (Chinese College Entrance Exam) level.
    2. For each word, provide:
       - The Word itself.
       - IPA Phonetic symbol (optional but good).
       - Chinese Definition (Accurate Gaokao standard).
       - 2 Common Phrases/Collocations.
       - 1 "Gen Z" Example Sentence. This sentence MUST be funny, relatable to teenagers (homework, gaming, sleep deprivation), or reference pop culture (Marvel, Taylor Swift, Anime). It should NOT be a boring textbook sentence.

    TEXT TO ANALYZE:
    {text_content[:8000]}  # Limiting text length for safety

    OUTPUT FORMAT:
    Return ONLY valid JSON. The structure should be a list of objects:
    [
        {{
            "word": "English Word",
            "phonetic": "/.../",
            "chinese_meaning": "中文意思",
            "phrases": ["phrase 1", "phrase 2"],
            "fun_sentence": "The funny sentence here."
        }},
        ...
    ]
    """
    
    try:
        with st.spinner("🤖 AI is reading your file and writing jokes..."):
            response = model.generate_content(prompt)
            # Clean up JSON if Gemini adds markdown backticks
            json_text = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(json_text)
            return data
    except Exception as e:
        st.error(f"AI Error: {e}")
        return []

# --- MAIN APP LOGIC ---

def main():
    # Sidebar
    with st.sidebar:
        st.title("📚 Teacher Setup")
        
        # Try to get key from secrets, otherwise ask for it
        if "GOOGLE_API_KEY" in st.secrets:
            api_key = st.secrets["GOOGLE_API_KEY"]
        else:
            api_key = st.text_input("Enter Google Gemini API Key", type="password")
        st.caption("[Get a free key here](https://aistudio.google.com/app/apikey)")
        
        uploaded_file = st.file_uploader("Upload Lesson Material", type=['pdf', 'docx'])
        
        if st.button("🚀 Generate Flashcards", type="primary"):
            if not api_key:
                st.warning("Please enter an API Key first.")
            elif not uploaded_file:
                st.warning("Please upload a file.")
            else:
                # Process
                raw_text = extract_text(uploaded_file)
                if raw_text:
                    vocab_data = get_gemini_response(api_key, raw_text)
                    st.session_state['vocab_data'] = vocab_data
                    st.session_state['show_answers'] = {} # Reset quiz states
                    st.success("Vocabulary extracted successfully!")

    # Main Content
    st.title("⚡ English Power-Up")
    st.caption("Designed for Senior High Students")

    if 'vocab_data' not in st.session_state or not st.session_state['vocab_data']:
        # Welcome Screen
        st.info("👈 Teachers: Upload a file on the left to start.")
        st.markdown("""
        ### How it works:
        1. **Upload** a reading passage or word list.
        2. **AI** extracts key words and creates funny examples.
        3. **Students** study with interactive cards or take a quiz.
        """)
    else:
        # Mode Selection
        tab1, tab2 = st.tabs(["📖 Study Mode", "🧠 Quiz Mode"])

        # --- STUDY MODE ---
        with tab1:
            st.write(f"Found {len(st.session_state['vocab_data'])} key words.")
            
            # Grid layout for cards
            for idx, item in enumerate(st.session_state['vocab_data']):
                # HTML Card
                card_html = f"""
                <div class="vocab-card">
                    <div class="word-title">{item['word']} <span class="phonetic">{item.get('phonetic', '')}</span></div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
                
                # Native Streamlit Expander for the "Reveal" interaction
                with st.expander(f"Show Meaning for **{item['word']}**"):
                    st.markdown(f"### {item['chinese_meaning']}")
                    st.markdown("**Common Phrases:**")
                    for p in item['phrases']:
                        st.markdown(f"- *{p}*")
                    
                    st.markdown("**💡 Example:**")
                    st.markdown(f"<div class='funny-sentence'>{item['fun_sentence']}</div>", unsafe_allow_html=True)

        # --- QUIZ MODE ---
        with tab2:
            st.write("Guess the word based on the funny sentence!")
            
            for idx, item in enumerate(st.session_state['vocab_data']):
                word = item['word']
                sentence = item['fun_sentence']
                
                # Create a blanked-out sentence (case insensitive replacement)
                import re
                blanked_sentence = re.sub(re.escape(word), "_______", sentence, flags=re.IGNORECASE)
                
                st.markdown("---")
                st.markdown(f"**Q{idx+1}:** {blanked_sentence}")
                
                # Use session state to toggle individual answers
                key = f"quiz_reveal_{idx}"
                if key not in st.session_state:
                    st.session_state[key] = False
                
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button(f"Reveal Answer #{idx+1}"):
                        st.session_state[key] = True
                
                with col2:
                    if st.session_state[key]:
                        st.success(f"**{word}** ({item['chinese_meaning']})")
                    else:
                        st.markdown("waiting...")

if __name__ == "__main__":
    main()
