from legalAI.openrouter_utils import call_openrouter_free

# Supported languages dictionary
SUPPORTED_LANGUAGES = {
    'hindi': 'Hindi',
    'tamil': 'Tamil',
    'bengali': 'Bengali',
    'gujarati': 'Gujarati',
    'telugu': 'Telugu',
    'punjabi': 'Punjabi',
    'kannada': 'Kannada',
    'malayalam': 'Malayalam',
    'marathi': 'Marathi',
    'urdu': 'Urdu',
}

# ✅ Function to load translator based on language
def load_translator(target_language):
    lang_name = SUPPORTED_LANGUAGES.get(target_language.lower(), target_language)
    
    def translate_fn(text):
        system_prompt = (
            f"You are an expert Legal Document Translator. "
            f"Your task is to translate the provided text into {lang_name} accurately, preserving the legal context and meaning. "
            "Output ONLY the translated text, without any additional explanations, notes, or introductions."
        )
        prompt = f"Translate the following text to {lang_name}:\n\n{text}"
        
        return call_openrouter_free(prompt=prompt, system_prompt=system_prompt, max_tokens=2000)

    return translate_fn

def translate_text(translate_fn, text, chunk_size=2000):
    """
    Since OpenRouter handles large context, we can just translate the whole text at once,
    but we keep the chunking logic if text is extremely long.
    """
    return translate_fn(text)
