"""
Lorem Ipsum Generator Tool
Generate placeholder text for various languages
"""
from ..categories import ToolCategory
from django import forms
import random
from apps.tools.base_tool import BaseTool


class LoremForm(forms.Form):
    TYPE_CHOICES = [
        ('paragraphs', 'Paragraphs'),
        ('sentences', 'Sentences'),
        ('words', 'Words'),
        ('list', 'List Items'),
    ]
    
    text_type = forms.ChoiceField(
        choices=TYPE_CHOICES,
        initial='paragraphs',
        label='Type'
    )
    count = forms.IntegerField(
        min_value=1,
        max_value=50,
        initial=3,
        label='Count'
    )
    start_with_lorem = forms.BooleanField(
        required=False,
        initial=True,
        label='Start with "Lorem ipsum"'
    )
    language = forms.ChoiceField(
        choices=[
            ('la', 'Latin'),
            ('en', 'English'),
            ('zh', 'Chinese (pseudo)'),
        ],
        initial='la',
        label='Language'
    )


# Latin words for Lorem Ipsum
LATIN_WORDS = [
    'lorem', 'ipsum', 'dolor', 'sit', 'amet', 'consectetur', 'adipiscing', 'elit',
    'sed', 'do', 'eiusmod', 'tempor', 'incididunt', 'ut', 'labore', 'et', 'dolore',
    'magna', 'aliqua', 'enim', 'ad', 'minim', 'veniam', 'quis', 'nostrud',
    'exercitation', 'ullamco', 'laboris', 'nisi', 'aliquip', 'ex', 'ea', 'commodo',
    'consequat', 'duis', 'aute', 'irure', 'in', 'reprehenderit', 'voluptate',
    'velit', 'esse', 'cillum', 'fugiat', 'nulla', 'pariatur', 'excepteur', 'sint',
    'occaecat', 'cupidatat', 'non', 'proident', 'sunt', 'culpa', 'qui', 'officia',
    'deserunt', 'mollit', 'anim', 'id', 'est', 'laborum'
]

ENGLISH_WORDS = [
    'the', 'quick', 'brown', 'fox', 'jumps', 'over', 'lazy', 'dog',
    'hello', 'world', 'this', 'is', 'sample', 'text', 'for', 'testing',
    'lorem', 'ipsum', 'dolor', 'amet', 'consectetur', 'adipiscing', 'elit',
    'sed', 'eiusmod', 'tempor', 'incididunt', 'labore', 'dolore', 'magna',
    'aliqua', 'enim', 'minim', 'veniam', 'quis', 'nostrud', 'exercitation',
    'ullamco', 'laboris', 'nisi', 'aliquip', 'commodo', 'consequat',
    'duis', 'aute', 'irure', 'reprehenderit', 'voluptate', 'velit', 'esse',
    'cillum', 'fugiat', 'nulla', 'pariatur', 'excepteur', 'sint', 'occaecat'
]

CHINESE_WORDS = [
    '的', '是', '在', '了', '和', '有', '我', '不', '人', '都',
    '一', '个', '上', '也', '很', '到', '说', '要', '去', '你',
    '会', '着', '没有', '看', '好', '自己', '这', '那', '他', '她',
    '来', '什么', '能', '对', '就', '为', '可以', '没', '让', '还',
    '把', '但', '被', '已', '之', '以', '所', '而', '或', '如'
]


def generate_word(language='la'):
    """Generate a random word"""
    if language == 'en':
        return random.choice(ENGLISH_WORDS)
    elif language == 'zh':
        return random.choice(CHINESE_WORDS)
    else:
        return random.choice(LATIN_WORDS)


def generate_sentence(min_words=8, max_words=15, start_with_lorem=True, language='la', first_sentence=False):
    """Generate a sentence"""
    if start_with_lorem and first_sentence and language == 'la':
        return 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'
    
    word_count = random.randint(min_words, max_words)
    words = [generate_word(language) for _ in range(word_count)]
    
    # Capitalize first word
    if words:
        words[0] = words[0].capitalize()
    
    sentence = ' '.join(words) + '.'
    return sentence


def generate_paragraph(min_sentences=4, max_sentences=7, start_with_lorem=True, language='la', first_paragraph=False):
    """Generate a paragraph"""
    sentence_count = random.randint(min_sentences, max_sentences)
    sentences = []
    
    for i in range(sentence_count):
        is_first = first_paragraph and i == 0
        sentences.append(generate_sentence(start_with_lorem=start_with_lorem, language=language, first_sentence=is_first))
    
    return ' '.join(sentences)


def process(form):
    """Process the form and return result"""
    if not form.is_valid():
        return {'error': 'Invalid input', 'text': ''}
    
    cleaned = form.cleaned_data
    text_type = cleaned.get('text_type', 'paragraphs')
    count = cleaned.get('count', 3)
    start_with_lorem = cleaned.get('start_with_lorem', True)
    language = cleaned.get('language', 'la')
    
    result = []
    
    if text_type == 'paragraphs':
        for i in range(count):
            para = generate_paragraph(
                start_with_lorem=start_with_lorem, 
                language=language, 
                first_paragraph=(i == 0)
            )
            result.append(para)
        text = '\n\n'.join(result)
        
    elif text_type == 'sentences':
        for i in range(count):
            sent = generate_sentence(
                start_with_lorem=start_with_lorem, 
                language=language, 
                first_sentence=(i == 0)
            )
            result.append(sent)
        text = ' '.join(result)
        
    elif text_type == 'words':
        words = [generate_word(language) for _ in range(count)]
        text = ' '.join(words)
        
    elif text_type == 'list':
        for _ in range(count):
            item = generate_sentence(min_words=5, max_words=10, start_with_lorem=False, language=language)
            result.append(item)
        text = '\n'.join([f'• {item}' for item in result])
    
    else:
        text = ''
    
    return {
        'text': text,
        'type': text_type,
        'count': count,
        'word_count': len(text.split()),
        'char_count': len(text),
    }


# Tool class for registry


class LoremGeneratorTool(BaseTool):
    name = "文本生成器"
    slug = "lorem"
    description = "生成占位文本，支持多种语言"
    icon = "text"
    category = ToolCategory.TEXT
    form_class = LoremForm

    def handle(self, request, form):
        return process(form)
