import json
import time
import random
from google import genai
from google.genai import errors as genai_errors
from flask import current_app

_MODEL = 'gemini-2.5-flash'
_MAX_RETRIES = 5
_BASE_BACKOFF_SECONDS = 1
_MAX_BACKOFF_SECONDS = 30


def _client():
    return genai.Client(api_key=current_app.config['GEMINI_API_KEY'])


def _generate(client, prompt):
    """Call Gemini with retries using exponential backoff + jitter.

    Raises the last exception if all retries fail.
    """
    for attempt in range(_MAX_RETRIES):
        try:
            return client.models.generate_content(model=_MODEL, contents=prompt)
        except genai_errors.ServerError:
            # transient server overload (503) — retry with backoff
            if attempt == _MAX_RETRIES - 1:
                raise
            backoff = min(_BASE_BACKOFF_SECONDS * (2 ** attempt), _MAX_BACKOFF_SECONDS)
            # add small jitter
            sleep_for = backoff + random.uniform(0, 1)
            time.sleep(sleep_for)
        except Exception:
            # on unexpected errors, re-raise to be handled by caller
            raise


def _local_tfidf_grade(question, answer_text):
    """Simple local fallback grader using TF-IDF cosine similarity against model answer.

    Returns dict with score, feedback, confidence.
    """
    model_answer = (question.model_answer or '').strip() if hasattr(question, 'model_answer') else ''
    if not model_answer:
        return {
            'score': 0.0,
            'feedback': 'No model answer available for automatic fallback grading; please grade manually.',
            'confidence': 'low'
        }

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        texts = [model_answer, answer_text or '']
        vec = TfidfVectorizer().fit_transform(texts)
        sim = float(cosine_similarity(vec[0], vec[1])[0][0])
    except Exception:
        # If sklearn is not available or vectorization fails, return low-confidence default
        return {
            'score': 0.0,
            'feedback': 'Fallback grading unavailable (vectorizer failed); please grade manually.',
            'confidence': 'low'
        }

    # Map similarity [0,1] to score [0, max_marks]
    raw_score = sim * float(getattr(question, 'max_marks', 10))
    score = max(0.0, min(raw_score, float(getattr(question, 'max_marks', 10))))

    # Build simple feedback
    if sim >= 0.75:
        feedback = 'Answer closely matches the model answer. Awarded full/near-full marks.'
        confidence = 'medium'
    elif sim >= 0.4:
        feedback = 'Answer partially matches the model answer; some points awarded.'
        confidence = 'low'
    else:
        feedback = 'Answer does not closely match the model answer; manual review recommended.'
        confidence = 'low'

    return {'score': score, 'feedback': feedback, 'confidence': confidence}


def grade_answer(question, answer_text):
    """Grade a student answer. Tries Gemini then falls back to a local TF-IDF grader.

    Returns dict with score, feedback, confidence.
    """
    if not answer_text or not answer_text.strip():
        return {'score': 0, 'feedback': 'No answer provided.', 'confidence': 'high'}

    prompt = (
        f"You are an exam grader. Grade the following student answer.\n"
        f"Question: {question.text}\n"
        f"Model Answer: {question.model_answer or 'Not provided'}\n"
        f"Rubric: {question.rubric or 'Not provided'}\n"
        f"Max Marks: {question.max_marks}\n"
        f"Student Answer: {answer_text}\n\n"
        f"Respond in this exact JSON format with no extra text:\n"
        f'{{\n'
        f'  "score": <number between 0 and {question.max_marks}>,\n'
        f'  "feedback": "<2-3 sentence explanation of what was correct, partially correct, and missing>",\n'
        f'  "confidence": "<high|medium|low>"\n'
        f'}}'
    )

    client = _client()
    try:
        response = _generate(client, prompt)
        result = _parse_json(response.text)
        result['score'] = max(0.0, min(float(result.get('score', 0)), question.max_marks))
        return result
    except genai_errors.ServerError:
        # Retry exhausted on server overload — fall back
        fb_result = _local_tfidf_grade(question, answer_text)
        fb_result['feedback'] = f"(Fallback) {fb_result['feedback']}"
        return fb_result
    except Exception:
        # Any other failure — fall back as well
        fb_result = _local_tfidf_grade(question, answer_text)
        fb_result['feedback'] = f"(Fallback) {fb_result['feedback']}"
        return fb_result


def detect_ai_generated(answer_text):
    """Return 0-100 probability that the text was AI-generated.

    Tries Gemini; on failure returns 0.0 as a safe default.
    """
    if not answer_text or not answer_text.strip():
        return 0.0

    prompt = (
        "Analyze the following text and estimate the probability (0-100) that it was "
        "generated by an AI language model rather than written by a human student.\n\n"
        "Consider: unusual formality, lack of personal voice, very balanced structure, "
        "suspiciously comprehensive coverage for a timed exam, generic phrasing.\n\n"
        f"Text:\n{answer_text}\n\n"
        'Respond with only this JSON and no extra text: {"ai_probability": <integer 0-100>}'
    )

    client = _client()
    try:
        response = _generate(client, prompt)
        result = _parse_json(response.text)
        return float(result.get('ai_probability', 0))
    except Exception:
        # Safe fallback when Gemini is unavailable
        return 0.0


def _parse_json(text):
    text = text.strip()
    if '```' in text:
        parts = text.split('```')
        text = parts[1] if len(parts) > 1 else text
        if text.startswith('json'):
            text = text[4:]
    return json.loads(text.strip())
