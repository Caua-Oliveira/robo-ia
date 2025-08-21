import os
import speech_recognition as sr
import google.generativeai as genai

GEMINI_API_KEY = "AIzaSyAegDM89dCDTPw5Io07nOoowKr9TaYWXw4"

genai.configure(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-2.5-flash-lite"

rec = sr.Recognizer()
language = 'pt-BR'