#!/usr/bin/env python3
"""
Refined wordlist generator that eliminates non-words while keeping legitimate English words.

UV Dependencies:
# Install UV if not available: curl -LsSf https://astral.sh/uv/install.sh | sh
# Run this script: uv run python refined_generator.py
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests>=2.31.0",
#     "nltk>=3.8.1",
# ]
# ///

from pathlib import Path
from typing import List, Set, Dict, Tuple
import json
import re
from collections import Counter

from word_scorer import WordScorer
from generate_wordlist import load_or_download_words, save_wordlist


TARGET_SIZE = 65536  # 2^16


class RefinedWordFilter:
    """Focused filtering to remove non-words while keeping legitimate English words."""
    
    def __init__(self):
        self.scorer = WordScorer()
        
        # Specific problematic patterns to exclude
        self.exclude_patterns = [
            # Repetitive letters like aaa, bbb, etc.
            r'^(.)\1+$',  # All same letter: aaa, bbb, etc.
            r'^(.)\1(.)\2+$',  # Alternating pairs: abab, cdcd, etc.
            r'^(.)\1\1',  # Three of same letter at start: aaab, bbbc, etc.
            
            # Non-English letter combinations
            r'^[aeiou]{2}[bcdfghjklmnpqrstvwxz]$',  # aab, eef, oox pattern
            r'^[bcdfghjklmnpqrstvwxz][aeiou]{2}$',  # baa, cee, doo pattern
            r'^[aeiou][bcdfghjklmnpqrstvwxz]{2}$',  # abb, ecc, off pattern
            
            # Obvious abbreviations or codes
            r'^[a-z]{2,3}$',  # Very short sequences that might be codes
            r'^[aeiou]$',  # Single vowels
            r'^[bcdfghjklmnpqrstvwxz]$',  # Single consonants
        ]
        
        # Specific words to exclude (obvious non-words and proper nouns)
        self.excluded_words = {
            # Obvious non-words
            'aaa', 'aab', 'aac', 'aad', 'aae', 'aaf', 'aag', 'aah', 'aai', 'aaj',
            'aak', 'aal', 'aam', 'aan', 'aao', 'aap', 'aaq', 'aar', 'aas', 'aat',
            'aau', 'aav', 'aaw', 'aax', 'aay', 'aaz',
            'aba', 'abb', 'abc', 'abd', 'abe', 'abf', 'abg', 'abh', 'abi', 'abj',
            'abk', 'abl', 'abm', 'abn', 'abo', 'abp', 'abq', 'abr', 'abs', 'abt',
            'abu', 'abv', 'abw', 'abx', 'aby', 'abz',
            'bbb', 'ccc', 'ddd', 'eee', 'fff', 'ggg', 'hhh', 'iii', 'jjj', 'kkk',
            'lll', 'mmm', 'nnn', 'ooo', 'ppp', 'qqq', 'rrr', 'sss', 'ttt', 'uuu',
            'vvv', 'www', 'xxx', 'yyy', 'zzz',
            
            # Place names and proper nouns (common ones)
            'aalborg', 'aalto', 'aachen', 'aarhus', 'aaron', 'aaronson', 'aarp',
            'abbott', 'abdul', 'abdullah', 'abe', 'abel', 'abelard', 'abelson',
            'aberdeen', 'abernathy', 'abernethy', 'abidjan', 'abilene', 'abner',
            'abraham', 'abram', 'abrams', 'abramson', 'abreu', 'abriel', 'abril',
            'abuja', 'abyssinia', 'acadia', 'acapulco', 'accra', 'acheson',
            'acme', 'acorn', 'acres', 'acton', 'ada', 'adair', 'adam', 'adams',
            'addison', 'adelaide', 'aden', 'adler', 'adolf', 'adrian', 'adrienne',
            'aegean', 'aesop', 'afghanistan', 'africa', 'agatha', 'agnes', 'ahmed',
            'aida', 'aids', 'aiken', 'aimee', 'ajax', 'akron', 'alabama', 'alan',
            'alaska', 'albania', 'albany', 'albert', 'alberta', 'alberto', 'albion',
            'albuquerque', 'alcott', 'alden', 'alex', 'alexander', 'alexandra',
            'alexandria', 'alexis', 'alfonso', 'alfred', 'algeria', 'alice', 'alicia',
            'alison', 'allan', 'allen', 'alley', 'allison', 'alma', 'almond', 'alps',
            'alvin', 'amanda', 'amazon', 'amber', 'amelia', 'america', 'american',
            'ames', 'amherst', 'amigo', 'amsterdam', 'amy', 'ana', 'anaconda',
            'anarchy', 'anastasia', 'anatole', 'anchor', 'anchorage', 'anders',
            'anderson', 'andre', 'andrea', 'andreas', 'andrew', 'andrews', 'andy',
            'angel', 'angela', 'angeles', 'angelo', 'angie', 'angus', 'anita',
            'ankara', 'ann', 'anna', 'anne', 'annie', 'anthony', 'antoine',
            'antonio', 'antwerp', 'apache', 'apollo', 'april', 'arabia', 'arabic',
            'aramco', 'arch', 'archer', 'archie', 'arctic', 'argentina', 'aries',
            'arizona', 'arkansas', 'arlen', 'arlene', 'arlington', 'arm', 'armand',
            'armenia', 'armstrong', 'arnold', 'art', 'arthur', 'ascii', 'asia',
            'aspen', 'astoria', 'athens', 'atlanta', 'atlantic', 'atlas', 'atomic',
            'audrey', 'august', 'augusta', 'augustus', 'aurora', 'austin', 'australia',
            'austria', 'autumn', 'avalon', 'avenue', 'avery', 'avon', 'aweekly',
            'aztec', 'azure', 'babe', 'babel', 'babylon', 'bach', 'bacon', 'badge',
            'baghdad', 'bahama', 'bailey', 'baker', 'baldwin', 'ball', 'baltimore',
            'bamboo', 'banana', 'bangkok', 'bangladesh', 'bangor', 'bank', 'banks',
            'barbara', 'barber', 'barclay', 'bare', 'barge', 'bark', 'barlow',
            'barn', 'barnes', 'baron', 'barrett', 'barron', 'barry', 'bart',
            'barton', 'baseball', 'basement', 'basic', 'basin', 'basis', 'basket',
            'bass', 'bat', 'batch', 'baton', 'battle', 'baxter', 'bay', 'beach',
            'bean', 'bear', 'beard', 'beat', 'beatrice', 'beauty', 'beck',
            'becky', 'bed', 'bee', 'beef', 'been', 'beer', 'bell', 'belle',
            'belly', 'belt', 'ben', 'bench', 'bend', 'benjamin', 'bennett',
            'benny', 'bent', 'berg', 'berkeley', 'berlin', 'berry', 'bert',
            'bertha', 'beth', 'betty', 'beverly', 'bias', 'bible', 'bicycle',
            'bid', 'big', 'bike', 'bill', 'billy', 'bind', 'bird', 'birth',
            'bishop', 'bit', 'black', 'blade', 'blake', 'blame', 'blank',
            'blanket', 'blast', 'blaze', 'blend', 'bless', 'blind', 'block',
            'bloom', 'blow', 'blue', 'board', 'boat', 'bob', 'bobby', 'body',
            'bone', 'book', 'boom', 'boost', 'boot', 'border', 'born', 'boss',
            'boston', 'both', 'bottle', 'bottom', 'bow', 'bowl', 'box', 'boy',
            'boyd', 'brain', 'branch', 'brand', 'brass', 'brave', 'bread',
            'break', 'breast', 'breath', 'breed', 'brick', 'bridge', 'brief',
            'bright', 'bring', 'broad', 'broke', 'brook', 'brooks', 'brother',
            'brown', 'bruce', 'brush', 'buck', 'buddy', 'budget', 'buffalo',
            'bug', 'build', 'bulb', 'bulk', 'bull', 'bunch', 'bundle', 'burn',
            'burst', 'bus', 'bush', 'business', 'busy', 'but', 'butter',
            'button', 'buy', 'buzz', 'by', 'bye', 'cabin', 'cable', 'cage',
            'cake', 'call', 'calm', 'came', 'camp', 'can', 'canal', 'candy',
            'cap', 'cape', 'card', 'care', 'career', 'carl', 'carlo', 'carol',
            'caroline', 'carry', 'cart', 'case', 'cash', 'cast', 'cat', 'catch',
            'cattle', 'caught', 'cause', 'cave', 'cell', 'cent', 'center',
            'central', 'century', 'chain', 'chair', 'chance', 'change', 'channel',
            'chapter', 'charge', 'charlie', 'chart', 'chase', 'cheap', 'check',
            'cheek', 'cheese', 'chef', 'cherry', 'chest', 'chicago', 'chicken',
            'chief', 'child', 'china', 'chinese', 'choice', 'choose', 'chord',
            'chosen', 'chris', 'christ', 'christian', 'christmas', 'church',
            'circle', 'citizen', 'city', 'civil', 'claim', 'clan', 'clap',
            'clark', 'class', 'classic', 'clay', 'clean', 'clear', 'clerk',
            'click', 'client', 'cliff', 'climb', 'clip', 'clock', 'close',
            'cloth', 'cloud', 'club', 'clue', 'cluster', 'coach', 'coal',
            'coast', 'coat', 'code', 'coffee', 'coin', 'cold', 'cole',
            'collect', 'college', 'colonel', 'color', 'column', 'combat',
            'come', 'comfort', 'comic', 'command', 'comment', 'common',
            'company', 'compare', 'complete', 'computer', 'concept', 'concern',
            'concert', 'conduct', 'confirm', 'congress', 'connect', 'consider',
            'consist', 'console', 'constant', 'contact', 'contain', 'content',
            'contest', 'context', 'continue', 'contract', 'control', 'cook',
            'cool', 'copper', 'copy', 'cord', 'core', 'corn', 'corner',
            'correct', 'cost', 'cotton', 'could', 'council', 'count', 'country',
            'county', 'couple', 'course', 'court', 'cousin', 'cover', 'cow',
            'crack', 'craft', 'crash', 'crazy', 'cream', 'create', 'credit',
            'crew', 'crime', 'crisis', 'crop', 'cross', 'crowd', 'crown',
            'cruel', 'cruise', 'cry', 'crystal', 'cube', 'culture', 'cup',
            'curious', 'current', 'curve', 'custom', 'cut', 'cute', 'cycle',
            'dad', 'daily', 'damage', 'dame', 'damn', 'dance', 'danger',
            'daniel', 'danny', 'dare', 'dark', 'data', 'date', 'daughter',
            'dave', 'david', 'dawn', 'day', 'dead', 'deal', 'dean', 'dear',
            'death', 'debate', 'debt', 'decade', 'december', 'decide', 'deck',
            'declare', 'deep', 'deer', 'defeat', 'defend', 'degree', 'deliver',
            'demand', 'democratic', 'den', 'density', 'deny', 'department',
            'depend', 'depth', 'describe', 'desert', 'design', 'desk', 'detail',
            'detect', 'determine', 'develop', 'device', 'devil', 'diamond',
            'dick', 'did', 'die', 'diet', 'differ', 'digital', 'dinner',
            'direct', 'dirt', 'dirty', 'discover', 'discuss', 'disease',
            'disk', 'display', 'distance', 'divide', 'dizzy', 'do', 'doctor',
            'dog', 'doll', 'dollar', 'domain', 'don', 'done', 'door', 'dot',
            'double', 'doubt', 'douglas', 'down', 'dozen', 'draft', 'drag',
            'drama', 'draw', 'dream', 'dress', 'drew', 'dried', 'drill',
            'drink', 'drive', 'drop', 'drove', 'drug', 'drum', 'dry', 'duck',
            'due', 'duke', 'dull', 'dumb', 'during', 'dust', 'duty', 'each',
            'eager', 'ear', 'early', 'earn', 'earth', 'ease', 'east', 'easy',
            'eat', 'echo', 'edge', 'edit', 'education', 'edward', 'effect',
            'effort', 'egg', 'eight', 'either', 'electric', 'element', 'eleven',
            'else', 'emily', 'emotion', 'employ', 'empty', 'end', 'enemy',
            'energy', 'engine', 'english', 'enjoy', 'enough', 'enter', 'entire',
            'entry', 'equal', 'equipment', 'eric', 'error', 'escape', 'essay',
            'essential', 'establish', 'estate', 'estimate', 'ethnic', 'europe',
            'european', 'even', 'evening', 'event', 'ever', 'every', 'everyone',
            'everything', 'evidence', 'exact', 'example', 'except', 'exchange',
            'excited', 'excuse', 'execute', 'executive', 'exercise', 'exist',
            'exit', 'expect', 'expensive', 'experience', 'experiment', 'expert',
            'explain', 'explore', 'export', 'expose', 'express', 'extend',
            'extra', 'eye', 'face', 'fact', 'factor', 'factory', 'fail',
            'fair', 'faith', 'fall', 'false', 'family', 'famous', 'fan',
            'fancy', 'far', 'farm', 'fast', 'fat', 'father', 'fault',
            'favor', 'fear', 'feature', 'federal', 'fee', 'feed', 'feel',
            'feet', 'fell', 'fellow', 'felt', 'female', 'fence', 'few',
            'field', 'fifteen', 'fifth', 'fifty', 'fight', 'figure', 'file',
            'fill', 'film', 'final', 'finance', 'find', 'fine', 'finger',
            'finish', 'fire', 'firm', 'first', 'fish', 'fit', 'five',
            'fix', 'flag', 'flame', 'flat', 'flesh', 'flight', 'float',
            'floor', 'flow', 'flower', 'fly', 'focus', 'folk', 'follow',
            'food', 'foot', 'football', 'for', 'force', 'foreign', 'forest',
            'forget', 'form', 'formal', 'former', 'fort', 'fortune', 'forty',
            'forward', 'found', 'four', 'fourth', 'fox', 'frame', 'france',
            'frank', 'free', 'freedom', 'french', 'fresh', 'friend', 'front',
            'fruit', 'fuel', 'full', 'fun', 'function', 'fund', 'funny',
            'future', 'gain', 'game', 'gang', 'gap', 'garage', 'garden',
            'gas', 'gate', 'gather', 'gave', 'gay', 'gear', 'gene',
            'general', 'generate', 'gentle', 'george', 'german', 'germany',
            'get', 'gift', 'girl', 'give', 'given', 'glad', 'glass',
            'global', 'go', 'goal', 'god', 'gold', 'golf', 'gone',
            'good', 'government', 'grab', 'grade', 'grain', 'grand', 'grant',
            'grass', 'grave', 'gray', 'great', 'green', 'grew', 'grid',
            'ground', 'group', 'grow', 'growth', 'guard', 'guess', 'guest',
            'guide', 'gun', 'guy', 'had', 'hair', 'half', 'hall',
            'hand', 'handle', 'hang', 'happen', 'happy', 'hard', 'harry',
            'hat', 'hate', 'have', 'he', 'head', 'health', 'hear',
            'heard', 'heart', 'heat', 'heavy', 'held', 'hell', 'hello',
            'help', 'henry', 'her', 'here', 'hero', 'hers', 'herself',
            'hi', 'hide', 'high', 'hill', 'him', 'himself', 'his',
            'history', 'hit', 'hold', 'hole', 'home', 'honest', 'honor',
            'hope', 'horn', 'horse', 'hospital', 'host', 'hot', 'hotel',
            'hour', 'house', 'how', 'however', 'huge', 'human', 'hundred',
            'hung', 'hunt', 'hurt', 'husband', 'i', 'ice', 'idea',
            'identify', 'if', 'ill', 'image', 'imagine', 'impact', 'implement',
            'important', 'improve', 'in', 'inch', 'include', 'income',
            'increase', 'indeed', 'independent', 'index', 'indicate', 'individual',
            'industrial', 'industry', 'information', 'initial', 'injury',
            'inner', 'input', 'inside', 'install', 'instance', 'instead',
            'institution', 'instruction', 'instrument', 'insurance', 'intelligent',
            'intend', 'interest', 'internal', 'international', 'internet',
            'interview', 'into', 'introduce', 'investment', 'invite', 'involve',
            'iron', 'is', 'island', 'issue', 'it', 'item', 'its',
            'itself', 'jack', 'jackson', 'james', 'jane', 'january', 'japan',
            'japanese', 'jazz', 'jean', 'jeff', 'jennifer', 'jerry', 'jim',
            'job', 'joe', 'john', 'johnson', 'join', 'joint', 'joke',
            'jones', 'joseph', 'joy', 'judge', 'july', 'jump', 'june',
            'junior', 'jury', 'just', 'justice', 'keep', 'kelly', 'ken',
            'kennedy', 'kept', 'key', 'keyboard', 'kick', 'kid', 'kill',
            'kind', 'king', 'kiss', 'kitchen', 'knee', 'knew', 'knife',
            'knock', 'know', 'knowledge', 'known', 'lab', 'labor', 'lack',
            'lady', 'laid', 'lake', 'land', 'language', 'large', 'last',
            'late', 'later', 'laugh', 'launch', 'law', 'lawyer', 'lay',
            'lead', 'leader', 'league', 'lean', 'learn', 'least', 'leather',
            'leave', 'led', 'left', 'leg', 'legal', 'length', 'less',
            'lesson', 'let', 'letter', 'level', 'library', 'license', 'lie',
            'life', 'lift', 'light', 'like', 'likely', 'limit', 'line',
            'link', 'lion', 'lip', 'list', 'listen', 'little', 'live',
            'loan', 'local', 'lock', 'log', 'long', 'look', 'lord',
            'lose', 'loss', 'lost', 'lot', 'loud', 'love', 'low',
            'lucky', 'lunch', 'machine', 'mad', 'made', 'magic', 'mail',
            'main', 'maintain', 'major', 'make', 'male', 'mall', 'man',
            'manage', 'manner', 'many', 'map', 'march', 'mark', 'market',
            'marriage', 'married', 'marry', 'mass', 'master', 'match',
            'material', 'math', 'matter', 'may', 'maybe', 'me', 'meal',
            'mean', 'meaning', 'measure', 'meat', 'media', 'medical', 'meet',
            'meeting', 'member', 'memory', 'men', 'mental', 'mention',
            'menu', 'mess', 'message', 'metal', 'method', 'middle', 'might',
            'mile', 'military', 'milk', 'mind', 'mine', 'minor', 'minute',
            'mirror', 'miss', 'mission', 'mistake', 'mix', 'model', 'modern',
            'moment', 'money', 'monitor', 'month', 'mood', 'moon', 'more',
            'morning', 'most', 'mother', 'motor', 'mount', 'mountain', 'mouse',
            'mouth', 'move', 'movement', 'movie', 'mr', 'mrs', 'much',
            'multiple', 'muscle', 'music', 'must', 'my', 'myself', 'name',
            'nation', 'national', 'native', 'natural', 'nature', 'near',
            'nearly', 'necessary', 'neck', 'need', 'negative', 'neighbor',
            'neither', 'nerve', 'net', 'network', 'never', 'new', 'news',
            'newspaper', 'next', 'nice', 'night', 'nine', 'no', 'nobody',
            'nod', 'noise', 'none', 'noon', 'nor', 'normal', 'north',
            'nose', 'not', 'note', 'nothing', 'notice', 'now', 'number',
            'nurse', 'object', 'observe', 'obtain', 'obvious', 'occur',
            'ocean', 'october', 'odd', 'of', 'off', 'offer', 'office',
            'officer', 'official', 'often', 'oh', 'oil', 'ok', 'old',
            'on', 'once', 'one', 'only', 'onto', 'open', 'operate',
            'operation', 'opinion', 'opportunity', 'opposite', 'option', 'or',
            'oral', 'orange', 'order', 'ordinary', 'organ', 'organization',
            'organize', 'origin', 'original', 'other', 'others', 'our',
            'out', 'outcome', 'outside', 'over', 'overall', 'own', 'owner',
            'pace', 'pack', 'package', 'page', 'pain', 'paint', 'pair',
            'pale', 'pan', 'panel', 'paper', 'parent', 'park', 'part',
            'particular', 'particularly', 'partner', 'party', 'pass', 'passage',
            'past', 'pat', 'path', 'patient', 'pattern', 'paul', 'pay',
            'payment', 'peace', 'peak', 'pen', 'people', 'per', 'percent',
            'perfect', 'perform', 'performance', 'perhaps', 'period', 'person',
            'personal', 'pet', 'phase', 'phone', 'photo', 'phrase', 'physical',
            'piano', 'pick', 'picture', 'piece', 'pin', 'pink', 'pipe',
            'pitch', 'place', 'plan', 'plane', 'plant', 'plastic', 'plate',
            'play', 'player', 'please', 'pleasure', 'plenty', 'plot', 'plus',
            'pm', 'pocket', 'poem', 'poet', 'poetry', 'point', 'police',
            'policy', 'political', 'politics', 'poll', 'poor', 'pop',
            'popular', 'population', 'port', 'position', 'positive', 'possible',
            'post', 'pot', 'potential', 'pound', 'pour', 'poverty', 'power',
            'powerful', 'practical', 'practice', 'pray', 'predict', 'prefer',
            'prepare', 'present', 'president', 'press', 'pressure', 'pretty',
            'prevent', 'previous', 'price', 'pride', 'primary', 'prime',
            'print', 'prior', 'priority', 'prison', 'private', 'probably',
            'problem', 'procedure', 'process', 'produce', 'product', 'production',
            'professional', 'professor', 'program', 'project', 'promise',
            'promote', 'proof', 'proper', 'property', 'protect', 'prove',
            'provide', 'public', 'pull', 'purpose', 'push', 'put', 'quality',
            'question', 'quick', 'quickly', 'quiet', 'quite', 'race',
            'radio', 'rail', 'rain', 'raise', 'range', 'rank', 'rapid',
            'rate', 'rather', 'rating', 'raw', 'reach', 'read', 'ready',
            'real', 'reality', 'realize', 'really', 'reason', 'receive',
            'recent', 'recently', 'recognize', 'recommend', 'record', 'recover',
            'red', 'reduce', 'refer', 'reflect', 'region', 'regular',
            'relate', 'relation', 'relationship', 'relative', 'release',
            'relevant', 'reliable', 'religion', 'religious', 'remain', 'remember',
            'remove', 'repeat', 'replace', 'reply', 'report', 'represent',
            'republican', 'reputation', 'request', 'require', 'research',
            'resource', 'respond', 'response', 'responsibility', 'rest',
            'result', 'return', 'reveal', 'revenue', 'review', 'rich',
            'rid', 'ride', 'right', 'ring', 'rise', 'risk', 'river',
            'road', 'rob', 'rock', 'role', 'roll', 'room', 'root',
            'rose', 'round', 'route', 'row', 'rule', 'run', 'running',
            'safe', 'safety', 'said', 'sale', 'same', 'sample', 'save',
            'say', 'scale', 'scene', 'schedule', 'scheme', 'school', 'science',
            'scientific', 'score', 'screen', 'sea', 'search', 'season',
            'seat', 'second', 'secret', 'section', 'sector', 'security',
            'see', 'seed', 'seek', 'seem', 'seen', 'select', 'sell',
            'senate', 'senator', 'send', 'senior', 'sense', 'sent', 'sentence',
            'separate', 'september', 'series', 'serious', 'serve', 'service',
            'session', 'set', 'setting', 'seven', 'several', 'sex',
            'sexual', 'shake', 'shall', 'shape', 'share', 'sharp', 'she',
            'sheet', 'shelf', 'shell', 'shelter', 'shift', 'shine', 'ship',
            'shirt', 'shock', 'shoe', 'shoot', 'shop', 'shopping', 'shore',
            'short', 'shot', 'should', 'shoulder', 'shout', 'show', 'shut',
            'sick', 'side', 'sight', 'sign', 'significant', 'significantly',
            'silence', 'silver', 'similar', 'simple', 'simply', 'since',
            'sing', 'single', 'sink', 'sir', 'sister', 'sit', 'site',
            'situation', 'six', 'size', 'skill', 'skin', 'sky', 'sleep',
            'slide', 'slight', 'slightly', 'slip', 'slow', 'small', 'smart',
            'smile', 'smoke', 'smooth', 'snap', 'snow', 'so', 'soap',
            'social', 'society', 'soft', 'software', 'soil', 'solar',
            'sold', 'soldier', 'solid', 'solution', 'solve', 'some',
            'somebody', 'somehow', 'someone', 'something', 'sometimes', 'somewhat',
            'somewhere', 'son', 'song', 'soon', 'sort', 'soul', 'sound',
            'soup', 'source', 'south', 'southern', 'space', 'speak', 'special',
            'specific', 'specifically', 'speech', 'speed', 'spend', 'spent',
            'spirit', 'spoke', 'sport', 'spot', 'spread', 'spring', 'staff',
            'stage', 'stand', 'standard', 'star', 'start', 'state', 'statement',
            'station', 'stay', 'steal', 'step', 'stick', 'still', 'stock',
            'stomach', 'stone', 'stood', 'stop', 'storage', 'store', 'storm',
            'story', 'straight', 'strange', 'stranger', 'strategy', 'street',
            'strength', 'stress', 'stretch', 'strike', 'string', 'strip',
            'strong', 'structure', 'struggle', 'stuck', 'student', 'studio',
            'study', 'stuff', 'stupid', 'style', 'subject', 'success',
            'successful', 'such', 'sudden', 'suddenly', 'suffer', 'sugar',
            'suggest', 'suit', 'summer', 'sun', 'sunday', 'super', 'supply',
            'support', 'suppose', 'sure', 'surface', 'surgery', 'surprise',
            'survey', 'survive', 'sweet', 'swim', 'swing', 'switch', 'system',
            'table', 'take', 'talk', 'tall', 'tank', 'tape', 'target',
            'task', 'taste', 'tax', 'teach', 'teacher', 'team', 'tear',
            'technology', 'tell', 'ten', 'tend', 'term', 'test', 'text',
            'than', 'thank', 'thanks', 'that', 'the', 'their', 'them',
            'themselves', 'then', 'theory', 'there', 'these', 'they',
            'thick', 'thin', 'thing', 'think', 'third', 'thirty', 'this',
            'those', 'though', 'thought', 'thousand', 'threat', 'three',
            'through', 'throughout', 'throw', 'thumb', 'thus', 'tie',
            'tight', 'time', 'tiny', 'tip', 'tired', 'title', 'to',
            'today', 'toe', 'together', 'told', 'tomato', 'tomorrow', 'tone',
            'tongue', 'tonight', 'too', 'took', 'tool', 'tooth', 'top',
            'topic', 'total', 'touch', 'tough', 'tour', 'toward', 'town',
            'toy', 'track', 'trade', 'traditional', 'traffic', 'train',
            'training', 'transfer', 'transform', 'transport', 'trap', 'travel',
            'treat', 'treatment', 'tree', 'trial', 'tribe', 'trick',
            'tried', 'trip', 'trouble', 'truck', 'true', 'truth', 'try',
            'trying', 'turn', 'twelve', 'twenty', 'twice', 'twin', 'two',
            'type', 'typical', 'ugly', 'ultimate', 'unable', 'uncle',
            'under', 'understand', 'understanding', 'union', 'unique', 'unit',
            'united', 'universal', 'university', 'unless', 'unlike', 'until',
            'unusual', 'up', 'upon', 'upper', 'urban', 'urge', 'us',
            'use', 'used', 'useful', 'user', 'usual', 'usually', 'value',
            'van', 'various', 'vast', 'vegetable', 'vehicle', 'version',
            'versus', 'very', 'via', 'victim', 'video', 'view', 'village',
            'violence', 'violent', 'virtual', 'virus', 'visit', 'visual',
            'vital', 'voice', 'volume', 'vote', 'wait', 'wake', 'walk',
            'wall', 'want', 'war', 'warm', 'warn', 'wash', 'waste',
            'watch', 'water', 'wave', 'way', 'we', 'weak', 'wealth',
            'weapon', 'wear', 'weather', 'web', 'website', 'wedding', 'week',
            'weekend', 'weekly', 'weight', 'welcome', 'well', 'west',
            'western', 'what', 'whatever', 'wheel', 'when', 'whenever',
            'where', 'whereas', 'wherever', 'whether', 'which', 'while',
            'white', 'who', 'whole', 'whom', 'whose', 'why', 'wide',
            'widely', 'wife', 'wild', 'will', 'willing', 'win', 'wind',
            'window', 'wine', 'wing', 'winner', 'winter', 'wire', 'wise',
            'wish', 'with', 'within', 'without', 'woman', 'women', 'won',
            'wonder', 'wonderful', 'wood', 'wooden', 'word', 'work', 'worker',
            'working', 'world', 'worry', 'worse', 'worst', 'worth', 'would',
            'write', 'writer', 'writing', 'written', 'wrong', 'yard',
            'yeah', 'year', 'yellow', 'yes', 'yesterday', 'yet', 'you',
            'young', 'your', 'yours', 'yourself', 'youth', 'zone'
        }
    
    def is_valid_word(self, word: str) -> bool:
        """Check if word is valid using refined criteria."""
        word = word.lower().strip()
        
        # Basic length check
        if len(word) < 3 or len(word) > 10:
            return False
        
        # Must be alphabetic
        if not word.isalpha():
            return False
        
        # Check excluded words
        if word in self.excluded_words:
            return False
        
        # Check problematic patterns
        for pattern in self.exclude_patterns:
            if re.search(pattern, word):
                return False
        
        # Must have at least one vowel
        if not any(c in 'aeiou' for c in word):
            return False
        
        # Must have at least one consonant
        if not any(c in 'bcdfghjklmnpqrstvwxyz' for c in word):
            return False
        
        # Check for reasonable vowel/consonant ratio
        vowels = sum(1 for c in word if c in 'aeiou')
        vowel_ratio = vowels / len(word)
        if vowel_ratio < 0.15 or vowel_ratio > 0.75:  # 15% to 75% vowels
            return False
        
        # Use basic word scorer for final validation
        score = self.scorer.score_word(word)
        return score.total_score >= 0.6  # Lower threshold to keep more real words
    
    def categorize_word(self, word: str) -> Tuple[str, float]:
        """Categorize word by quality."""
        score = self.scorer.score_word(word)
        
        if score.total_score >= 0.9:
            return "excellent", score.total_score
        elif score.total_score >= 0.8:
            return "very_good", score.total_score
        elif score.total_score >= 0.7:
            return "good", score.total_score
        elif score.total_score >= 0.6:
            return "acceptable", score.total_score
        else:
            return "poor", score.total_score


def generate_refined_wordlist() -> List[str]:
    """Generate refined wordlist with better quality control."""
    filter = RefinedWordFilter()
    
    # Load source wordlists
    print("Loading source wordlists...")
    bip39_words, top_english = load_or_download_words()
    
    # Start with BIP39 words, but filter them too
    print("Filtering BIP39 words...")
    final_words = set()
    excluded_bip39 = []
    
    for word in bip39_words:
        if filter.is_valid_word(word):
            final_words.add(word)
        else:
            excluded_bip39.append(word)
    
    print(f"Kept {len(final_words)} BIP39 words, excluded {len(excluded_bip39)}")
    if excluded_bip39:
        print(f"Excluded BIP39 words: {excluded_bip39[:10]}...")
    
    # Process top English words
    print("\nProcessing top English words...")
    categorized = {
        "excellent": [],
        "very_good": [],
        "good": [],
        "acceptable": []
    }
    
    processed = 0
    for word in top_english:
        word = word.lower().strip()
        
        if word in final_words:
            continue
        
        if filter.is_valid_word(word):
            category, score = filter.categorize_word(word)
            if category != "poor":
                categorized[category].append((word, score))
        
        processed += 1
        if processed % 10000 == 0:
            print(f"Processed {processed} words...")
    
    # Sort each category by score
    for category in categorized:
        categorized[category].sort(key=lambda x: x[1], reverse=True)
    
    # Add words by quality
    print("\nAdding words by quality category...")
    for category in ["excellent", "very_good", "good", "acceptable"]:
        added = 0
        for word, score in categorized[category]:
            if len(final_words) >= TARGET_SIZE:
                break
            final_words.add(word)
            added += 1
        
        print(f"Added {added} {category} words (total: {len(final_words)})")
        
        if len(final_words) >= TARGET_SIZE:
            break
    
    # Convert to sorted list
    wordlist = sorted(list(final_words))[:TARGET_SIZE]
    
    return wordlist


def analyze_refined_quality(words: List[str]) -> Dict:
    """Analyze the quality of the refined wordlist."""
    filter = RefinedWordFilter()
    
    # Quality distribution
    quality_dist = Counter()
    for word in words:
        category, _ = filter.categorize_word(word)
        quality_dist[category] += 1
    
    # Sample words from each quality tier
    samples = {"excellent": [], "very_good": [], "good": [], "acceptable": []}
    for word in words:
        category, score = filter.categorize_word(word)
        if len(samples[category]) < 10:
            samples[category].append((word, score))
    
    return {
        "quality_distribution": dict(quality_dist),
        "length_distribution": dict(Counter(len(word) for word in words)),
        "sample_words": samples
    }


def main():
    """Generate refined wordlist."""
    print("Refined Wordlist Generator")
    print("Eliminating non-words while keeping real English words")
    print("=" * 60)
    
    wordlist = generate_refined_wordlist()
    
    print(f"\nGenerated {len(wordlist)} words")
    
    # Analyze quality
    analysis = analyze_refined_quality(wordlist)
    
    print("\nQuality Distribution:")
    for category, count in analysis["quality_distribution"].items():
        percentage = (count / len(wordlist)) * 100
        print(f"  {category}: {count} ({percentage:.1f}%)")
    
    print(f"\nFirst 50 words: {wordlist[:50]}")
    print(f"Length distribution: {analysis['length_distribution']}")
    
    # Show sample words
    print("\nSample words by quality:")
    for category in ["excellent", "very_good", "good", "acceptable"]:
        if analysis["sample_words"][category]:
            print(f"\n{category.title()}:")
            for word, score in analysis["sample_words"][category][:5]:
                print(f"  {word}: {score:.3f}")
    
    # Save results
    output_dir = Path("wordlists")
    output_dir.mkdir(exist_ok=True)
    
    # Save wordlist
    save_wordlist(wordlist, "../wordlists/refined_wordlist_65536.txt")
    
    # Save with analysis
    metadata = {
        "version": "4.0",
        "word_count": len(wordlist),
        "generation_method": "refined_filtering",
        "includes_bip39": True,
        "quality_analysis": analysis,
        "description": "Refined wordlist eliminating non-words while preserving real English words",
        "words": wordlist
    }
    
    with open(output_dir / "refined_wordlist_65536.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✓ Saved refined wordlist to wordlists/refined_wordlist_65536.txt")
    print("✓ Saved analysis to wordlists/refined_wordlist_65536.json")


if __name__ == "__main__":
    main()