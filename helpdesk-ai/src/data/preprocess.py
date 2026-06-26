
import re
import unicodedata
import nltk

nltk.download('stopwords', quiet=True)
from nltk.corpus import stopwords

STOP_FR = set(stopwords.words('french'))
STOP_EN = set(stopwords.words('english'))
STOP_IT = {
    'bonjour', 'support', 'merci', 'cordialement', 'cher',
    'bonne', 'journée', 'svp', 'lors', 'suite', 'ticket',
    'demande', 'hello', 'hi', 'dear', 'team', 'please',
    'regards', 'otbs', 'one', 'tech', 'business', 'solutions'
}
STOP_WORDS = STOP_FR | STOP_EN | STOP_IT


def clean_text(text: str) -> str:
    if not isinstance(text, str) or text.strip() == '':
        return ''
    text = text.lower()
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r'http\S+|www\.\S+', ' ', text)
    text = re.sub(r'\S+@\S+', ' ', text)
    text = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', ' ', text)
    text = re.sub(r'\b[a-z]+-\d+\b', ' ', text)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\b\d+\b', ' ', text)
    tokens = text.split()
    tokens = [t for t in tokens if t not in STOP_WORDS and len(t) >= 3]
    return ' '.join(tokens)


def build_text_for_model(titre: str, description: str) -> str:
    """Feature pour le modèle ML (classification)."""
    return clean_text(str(description))


def build_text_for_rag(description: str,
                        resolution: str = '',
                        knowledge: str = '',
                        titre: str = '') -> str:
    """Feature enrichie pour le moteur RAG."""
    combined = f"{titre} {description} {resolution} {knowledge}"
    return clean_text(combined)






 