from legalAI.openrouter_utils import call_openrouter_free

def load_summarizer():
    # Return a dummy object as OpenRouter API handles the model
    return "openrouter_summarizer"

def summarize_text(summarizer, text, max_length=500, min_length=100):
    system_prompt = (
        "You are an expert Legal Document Summarizer. "
        "Your task is to provide a concise, accurate, and highly professional summary of the provided legal text. "
        "Highlight the key points, parties involved, legal issues, and any decisions or findings. "
        "Ensure the summary is clear and easy to understand."
    )
    
    prompt = f"Please summarize the following legal document:\n\n{text}"
    
    # We use a lower max_tokens for summary, e.g., 800
    return call_openrouter_free(prompt=prompt, system_prompt=system_prompt, max_tokens=800)
