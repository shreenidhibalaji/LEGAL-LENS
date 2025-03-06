import streamlit as st
from dotenv import load_dotenv
import os
import requests
import speech_recognition as sr
from deep_translator import GoogleTranslator  
from gtts import gTTS
import base64
import fitz  # PyMuPDF for PDF processing
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Set API Key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "YOUR_GOOGLE_API_KEY_HERE")
genai.configure(api_key=GOOGLE_API_KEY)

import google.api_core.exceptions  # Ensure this is imported

def get_gemini_response(question, lang="en"):
    try:
        model = genai.GenerativeModel("gemini-1.5-pro")
        response = model.generate_content(question)
        answer = response.text if response else "Error fetching response."
        return GoogleTranslator(source="auto", target=lang).translate(answer)
    except google.api_core.exceptions.ResourceExhausted:
        return "API quota exceeded. Please try again later."
    except Exception as e:
        return f"Error: {str(e)}"



def summarize_text(text, lang="en"):
    prompt = f"Please summarize the following text into bullet points:\n\n{text}"
    return get_gemini_response(prompt, lang)

def summarize_pdf(pdf_file, lang="en"):
    with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
        pdf_text = "\n".join(page.get_text() for page in doc)
    return summarize_text(pdf_text, lang)

def recognize_speech():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    
    with mic as source:
        st.info("Listening... Please speak now.")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    
    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        return "Could not understand audio."
    except sr.RequestError:
        return "Speech recognition service unavailable."

def text_to_speech(text, lang="en"):
    try:
        tts = gTTS(text=text, lang=lang)
        tts.save("response.mp3")
        with open("response.mp3", "rb") as audio_file:
            audio_bytes = audio_file.read()
            return base64.b64encode(audio_bytes).decode()
    except Exception as e:
        return f"Speech Synthesis Error: {str(e)}"

st.title("LEGAL LENS")
st.sidebar.header("Select Feature")
selected_tab = st.sidebar.radio("Choose a feature:", ["Ask a question", "Voice assistant", "Summarize PDF & Ask Questions", "Translate Text"])

# Navigate to Selected Feature
if selected_tab == "Ask a question":
    st.subheader("Ask a Question")
    user_query = st.text_area("Enter your question:")
    target_lang = st.selectbox("Select language for answer:", ["en", "hi", "fr", "es", "de", "ta", "te"])
    if st.button("Get Answer"):
        if user_query:
            answer = get_gemini_response(user_query, target_lang)
            st.subheader("Answer")
            st.markdown(answer)
        else:
            st.warning("Please enter a question.")

elif selected_tab == "Voice assistant":
    st.subheader("Voice Assistant")
    if st.button("Start Listening"):
        voice_input = recognize_speech()
        st.text(f"You said: {voice_input}")
        if voice_input:
            answer = get_gemini_response(voice_input)
            st.subheader("Answer")
            st.markdown(answer)
            b64_audio = text_to_speech(answer, "en")
            audio_html = f'<audio controls><source src="data:audio/mp3;base64,{b64_audio}" type="audio/mp3"></audio>'
            st.markdown(audio_html, unsafe_allow_html=True)

elif selected_tab == "Summarize PDF & Ask Questions":
    st.subheader("Upload a PDF for Summarization & Q&A")
    uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
    target_lang = st.selectbox("Select language for summary:", ["en", "hi", "fr", "es", "de", "ta", "te"])
    if uploaded_file:
        if st.button("Summarize PDF"):
            summarized_points = summarize_pdf(uploaded_file, target_lang)
            st.session_state["summarized_points"] = summarized_points
            st.subheader("Summarized Points")
            st.markdown(summarized_points)

elif selected_tab == "Translate Text":
    st.subheader("Translate Text")
    text_to_translate = st.text_area("Enter text to translate:")
    target_lang = st.selectbox("Select target language:", ["en", "hi", "fr", "es", "de", "ta", "te"])
    if st.button("Translate"):
        if text_to_translate:
            translated_text = GoogleTranslator(source="auto", target=target_lang).translate(text_to_translate)
            st.subheader("Translated Text")
            st.markdown(translated_text)
        else:
            st.warning("Please enter text to translate.")
