from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .models import Chat, Document
from django.contrib.auth.models import User
from .models import Profile
from .utils.get_text import get_text
from .utils.translator import load_translator, translate_text
import tempfile
import os
import random
from .forms import DocumentForm
import fitz

# Unused local summarizer removed in favor of OpenRouter
from django.conf import settings
from django.db.models import Prefetch
from django.core.mail import send_mail


def generate_otp():
    """Generate a 6-digit OTP code"""
    return str(random.randint(100000, 999999))


def send_otp_via_email(email, otp):
    """Send OTP via email"""
    subject = 'Your LegalAI Signup OTP'
    message = f'Your OTP for LegalAI signup is: {otp}\n\nThis OTP will expire soon. Do not share it with anyone.'
    from_email = 'Legal AI <' + settings.EMAIL_HOST_USER + '>'
    if not settings.EMAIL_HOST_USER:
        return False
    try:
        send_mail(subject, message, from_email, [email], fail_silently=False)
        return True
    except Exception as e:
        print(f"Email send error: {e}")
        return False


def entry(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'entry.html')

def about(request):
    return render(request, 'about.html')

def signup_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(email=email).exists():
            return render(request, 'signup.html', {'error': 'Email already registered'})


        otp = generate_otp()
        request.session['signup_data'] = {
            'name': name,
            'email': email,
            'password': password,
            'otp': otp
        }

        email_sent = send_otp_via_email(email, otp)
        if not email_sent:
            return render(request, 'signup.html', {'error': 'Failed to send OTP email. Please try again.'})
        return redirect('verify_otp')

    return render(request, 'signup.html')


def verify_otp_view(request):
    signup_data = request.session.get('signup_data')
    if not signup_data:
        return redirect('signup')

    if request.method == 'POST':
        otp_input = request.POST.get('otp')
        if otp_input == signup_data['otp']:
            # ✅ Create user only now
            user = User.objects.create_user(
                username=signup_data['email'],
                email=signup_data['email'],
                password=signup_data['password']
            )
            user.profile.name = signup_data['name']
            user.profile.otp_verified = True
            user.profile.save()

            # Cleanup session
            del request.session['signup_data']

            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'verify_otp.html', {
                'error': 'Invalid OTP'
            })

    return render(request, 'verify_otp.html', {})



def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')
from .utils.location import get_country_from_ip

from django.db.models import Count

def dashboard_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    # Get IP address from request
    ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", ""))
    if "," in ip:
        ip = ip.split(",")[0].strip()

    country = get_country_from_ip(ip)

    message_qs = ChatMessage.objects.order_by('timestamp')

    sessions = (
        ChatSession.objects.filter(user=request.user)
        .annotate(message_count=Count('messages'))       # ✅ count messages
        .filter(message_count__gt=0)                     # ✅ keep only sessions with at least 1 message
        .select_related('document')
        .prefetch_related(Prefetch('messages', queryset=message_qs))
        .order_by('-created_at')

    )

    recent_documents = Document.objects.filter(user=request.user).order_by('-uploaded_at')[:4]

    return render(request, 'dashboard.html', {
        'chat_sessions': sessions,
        'recent_documents': recent_documents,
        "country": country
    })


def translator(request):
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

                if lang:
                    translator_fn = load_translator(lang)
                    translated = translate_text(translator_fn, text)

                              # ✅ Save the document & extracted text in DB
                doc = Document.objects.create(
                    user=request.user,
                    file=file,
                    extracted_text=text
                )

            except Exception as e:
                summary = f"Error: {str(e)}"
        # Even if form is invalid, render with form errors
        return render(request, 'translate.html', {
            'form': form,
            'translated': translated,
        })

    else:  # GET
        form = DocumentForm()

    return render(request, 'translate.html', {
        'form': form,
        'translated': translated,
    })


# Indian law knowledge base (basic placeholder)
with open("law_data/indian_laws.txt", "r", encoding="utf-8") as f:
    indian_laws = f.read()



# -------------------------------
#         CHATBOT VIEW
# -------------------------------

from django.shortcuts import get_object_or_404

def attach_document_view(request, session_id):
    if not request.user.is_authenticated:
        return redirect('login')

    session = get_object_or_404(ChatSession, id=session_id, user=request.user)

    if request.method == 'POST' and 'document' in request.FILES:
        file = request.FILES['document']
        text = extract_text_from_pdf(file)

        doc = Document.objects.create(
            user=request.user,
            file=file,
            extracted_text=text
        )

        session.document = doc
        session.save()

    return redirect('chat_session', session_id=session.id)

def extract_text_from_pdf(file):
    text = ""
    pdf_doc = fitz.open(stream=file.read(), filetype="pdf")
    for page in pdf_doc:
        text += page.get_text()
    return text


import requests



from .models import ChatSession, ChatMessage

def upload_pdf_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    # Start an empty session (no document yet)
    session = ChatSession.objects.create(user=request.user)
    return redirect('chat_session', session_id=session.id)


from legalAI.openrouter_utils import call_openrouter_free
from legalAI.wiki_utils import search_wikipedia

def generate_legal_answer(context, question):
    system_prompt = (
        "You are an expert, strict, and precise AI Legal Assistant specializing in Indian Law. "
        "Provide factual, direct, and concise answers citing relevant Acts, Sections, and Precedents under Indian Law. "
        "Do not guess historical dates or facts if unsure. Avoid rambling."
    )
    
    wiki_context = ""
    # Only search if no document is uploaded, or if it's a general question
    if not context or len(context) < 100:
        wiki_context = search_wikipedia(question)
    
    prompt = f"User Question:\n{question}"
    
    if wiki_context:
        prompt = f"Factual Background Information from Wikipedia (Use this to ensure 100% accuracy, but format your answer as an expert legal assistant):\n{wiki_context}\n\n" + prompt
        
    if context:
        prompt = f"Context from uploaded document:\n{context}\n\n" + prompt
    
    return call_openrouter_free(prompt=prompt, system_prompt=system_prompt)



def chat_session_view(request, session_id):
    if not request.user.is_authenticated:
        return redirect('login')

    try:
        session = ChatSession.objects.get(id=session_id, user=request.user)
    except ChatSession.DoesNotExist:
        return render(request, '404.html', status=404)

    messages = ChatMessage.objects.filter(session=session).order_by('timestamp')
    answer = None

    if request.method == 'POST':
        question = request.POST.get('question', '').strip()
        if question:
            ChatMessage.objects.create(
                session=session,
                is_user=True,
                content=question
            )

            context = session.document.extracted_text if session.document else ""
            ai_answer = generate_legal_answer(context, question)

            ChatMessage.objects.create(
                session=session,
                is_user=False,
                content=ai_answer
            )

            answer = ai_answer  # This line must be indented at same level as ChatMessage.objects.create

    return render(request, 'chat_session.html', {
        'session': session,
        'messages': messages,
        'answer': answer
    })




#################
# Prediction AI #
#################
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def predict_appeal_view(request):
    result = None
    if request.method == 'POST' and 'casefile' in request.FILES:
        file = request.FILES['casefile']
        context = extract_text_from_pdf(file)
                # ✅ Save document & extracted text to DB
        if request.user.is_authenticated:
            Document.objects.create(
                user=request.user,
                file=file,
                extracted_text=context
            )

        question = """
Based on the case details above, predict whether the appeal is likely to be accepted or rejected.
Give your answer as:

Prediction: Accepted or Rejected
Reasons: Brief reasoning behind the prediction as per Indian law
"""

        result = generate_legal_answer(context, question)

    return render(request, 'predict_appeal.html', {'result': result})



from django.shortcuts import get_object_or_404
from .models import Document

def document_list_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    documents = Document.objects.filter(user=request.user).order_by('-uploaded_at')
    return render(request, 'documents/list.html', {
        'documents': documents
    })

def document_detail_view(request, document_id):
    if not request.user.is_authenticated:
        return redirect('login')

    document = get_object_or_404(Document, id=document_id, user=request.user)
    return render(request, 'documents/detail.html', {
        'document': document
    })



from django.contrib.auth.hashers import make_password

def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            otp = generate_otp()
            user.profile.otp = otp
            user.profile.save()

            send_otp_via_email(email, otp)
            request.session['reset_email'] = email
            return redirect('reset_password_otp')
        except User.DoesNotExist:
            return render(request, 'forgot_password.html', {'error': 'No account found with this email'})
    return render(request, 'forgot_password.html')


def reset_password_otp_view(request):
    email = request.session.get('reset_email')
    if not email:
        return redirect('forgot_password')

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return redirect('forgot_password')

    if request.method == 'POST':
        otp_input = request.POST.get('otp')
        if otp_input == user.profile.otp:
            request.session['otp_verified_for_reset'] = True
            return redirect('reset_password')
        else:
            return render(request, 'reset_password_otp.html', {'error': 'Invalid OTP'})
    return render(request, 'reset_password_otp.html')


def reset_password_view(request):
    email = request.session.get('reset_email')
    otp_verified = request.session.get('otp_verified_for_reset')

    if not email or not otp_verified:
        return redirect('forgot_password')

    if request.method == 'POST':
        new_password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            return render(request, 'reset_password.html', {'error': 'Passwords do not match'})

        user = User.objects.get(email=email)
        user.password = make_password(new_password)
        user.save()

        # Clear session
        request.session.pop('reset_email', None)
        request.session.pop('otp_verified_for_reset', None)

        return redirect('login')

    return render(request, 'reset_password.html')


from django.contrib import messages

def delete_chat_session_view(request, session_id):
    if not request.user.is_authenticated:
        return redirect('login')

    session = get_object_or_404(ChatSession, id=session_id, user=request.user)

    if request.method == 'POST':
        session.delete()
        messages.success(request, "Chat session deleted successfully.")
        return redirect('dashboard')

    return redirect('dashboard')


from django.shortcuts import render, redirect
from .forms import ProfilePicForm

def upload_profile_pic(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = request.user.profile

    if request.method == 'POST':
        form = ProfilePicForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('dashboard')  # Or wherever you want after upload
    else:
        form = ProfilePicForm(instance=profile)

    return render(request, 'upload_profile_pic.html', {'form': form})
