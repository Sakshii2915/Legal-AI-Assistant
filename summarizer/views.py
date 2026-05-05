from django.shortcuts import render
from .forms import DocumentForm
from .utils.get_text import get_text
from .utils.summarize import load_summarizer, summarize_text
from .utils.translator import load_translator, translate_text
import tempfile
import os
from .utils.extract_citations import extract_legal_citations

# Lazy load summarizer to avoid startup errors
_summarizer = None
def get_summarizer():
    global _summarizer
    if _summarizer is None:
        _summarizer = load_summarizer()
    return _summarizer

def index(request):
    summary = None
    translated = None
    citations = None  # Define default value

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['document']
            lang = form.cleaned_data['language']

            ext = os.path.splitext(file.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                for chunk in file.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name

            try:
                text = get_text(tmp_path)
                summary = summarize_text(get_summarizer(), text)
                citations = extract_legal_citations(text)

                if lang:
                    translator_fn = load_translator(lang)
                    translated = translate_text(translator_fn, summary)

            except Exception as e:
                summary = f"Error: {str(e)}"
        # Even if form is invalid, render with form errors
        return render(request, 'index.html', {
            'form': form,
            'summary': summary,
            'translated': translated,
            'citations': citations,
        })

    else:  # GET
        form = DocumentForm()

    return render(request, 'index.html', {
        'form': form,
        'summary': summary,
        'translated': translated,
        'citations': citations,
    })
