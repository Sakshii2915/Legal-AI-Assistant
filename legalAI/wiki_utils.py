import requests
import re

def search_wikipedia(query):
    # Renamed internally to use duckduckgo for better snippets
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        res = requests.get(f"https://html.duckduckgo.com/html/?q={query} Indian Law Supreme Court", headers=headers, timeout=5)
        # Regex to extract snippets from DuckDuckGo HTML
        snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', res.text)
        # Remove bold tags and other HTML
        clean_snippets = [re.sub(r'<[^>]+>', '', s) for s in snippets]
        return "\n".join(clean_snippets[:5])
    except Exception as e:
        print(f"Web Search Error: {e}")
    return ""
