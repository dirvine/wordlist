#!/usr/bin/env python3
"""
Ultra-clean wordlist generator focusing on common, recognizable English words.

UV Dependencies:
# Install UV if not available: curl -LsSf https://astral.sh/uv/install.sh | sh
# Run this script: uv run python ultra_clean_generator.py
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


class UltraCleanFilter:
    """Ultra-strict filtering for common, recognizable English words only."""
    
    def __init__(self):
        self.scorer = WordScorer()
        
        # Build a comprehensive set of common English words
        self.known_good_words = self._build_known_good_words()
        
        # Simple patterns that definitely indicate non-words
        self.bad_patterns = [
            r'^[aeiou]{2,}[bcdfghjklmnpqrstvwxyz]$',  # aab, eef, etc.
            r'^[bcdfghjklmnpqrstvwxyz][aeiou]{2,}$',  # baa, cee, etc.
            r'^[aeiou][bcdfghjklmnpqrstvwxyz]{2,}$',  # abb, ecc, etc.
            r'^(.)\1+$',  # aaa, bbb, etc.
            r'^[a-z]{2}$',  # Two letter words (mostly)
            r'^[bcdfghjklmnpqrstvwxyz]{4,}',  # 4+ consonants at start
            r'[bcdfghjklmnpqrstvwxyz]{5,}',  # 5+ consonants anywhere
            r'^[aeiou]{3,}',  # 3+ vowels at start
            r'[aeiou]{4,}',  # 4+ vowels anywhere
        ]
        
        # Words that are definitely not common English (proper nouns, foreign words, etc.)
        self.definitely_bad = {
            # Obvious non-words and abbreviations
            'aaa', 'aab', 'aac', 'aad', 'aae', 'aaf', 'aag', 'aah', 'aai', 'aaj', 'aak', 'aal', 'aam', 'aan', 'aao', 'aap', 'aaq', 'aar', 'aas', 'aat', 'aau', 'aav', 'aaw', 'aax', 'aay', 'aaz',
            'aba', 'abb', 'abc', 'abd', 'abe', 'abf', 'abg', 'abh', 'abi', 'abj', 'abk', 'abl', 'abm', 'abn', 'abo', 'abp', 'abq', 'abr', 'abs', 'abt', 'abu', 'abv', 'abw', 'abx', 'aby', 'abz',
            'bbb', 'ccc', 'ddd', 'eee', 'fff', 'ggg', 'hhh', 'iii', 'jjj', 'kkk', 'lll', 'mmm', 'nnn', 'ooo', 'ppp', 'qqq', 'rrr', 'sss', 'ttt', 'uuu', 'vvv', 'www', 'xxx', 'yyy', 'zzz',
            
            # Organizations and acronyms
            'aage', 'aashto', 'aaup', 'ababa', 'abaca', 'abacha', 'abad', 'abadan', 'abaft', 'abajo', 'abalone',
            'aalborg', 'aalto', 'aachen', 'aarhus', 'aaron', 'aaronson', 'aarp', 'abbott', 'abdul', 'abdullah',
            'abe', 'abel', 'abelard', 'abelson', 'aberdeen', 'abernathy', 'abernethy', 'abidjan', 'abilene',
            'abner', 'abraham', 'abram', 'abrams', 'abramson', 'abreu', 'abriel', 'abril', 'abuja', 'abyssinia',
            'acadia', 'acapulco', 'accra', 'acheson', 'acme', 'acorn', 'acres', 'acton', 'ada', 'adair',
            'adam', 'adams', 'addison', 'adelaide', 'aden', 'adler', 'adolf', 'adrian', 'adrienne', 'aegean',
            'aesop', 'afghanistan', 'africa', 'agatha', 'agnes', 'ahmed', 'aida', 'aids', 'aiken', 'aimee',
            'ajax', 'akron', 'alabama', 'alan', 'alaska', 'albania', 'albany', 'albert', 'alberta', 'alberto',
            'albion', 'albuquerque', 'alcott', 'alden', 'alex', 'alexander', 'alexandra', 'alexandria', 'alexis',
            'alfonso', 'alfred', 'algeria', 'alice', 'alicia', 'alison', 'allan', 'allen', 'alley', 'allison',
            'alma', 'almond', 'alps', 'alvin', 'amanda', 'amazon', 'amber', 'amelia', 'america', 'american',
            'ames', 'amherst', 'amigo', 'amsterdam', 'amy', 'ana', 'anaconda', 'anarchy', 'anastasia', 'anatole',
            'anchor', 'anchorage', 'anders', 'anderson', 'andre', 'andrea', 'andreas', 'andrew', 'andrews',
            'andy', 'angel', 'angela', 'angeles', 'angelo', 'angie', 'angus', 'anita', 'ankara', 'ann',
            'anna', 'anne', 'annie', 'anthony', 'antoine', 'antonio', 'antwerp', 'apache', 'apollo', 'april',
            'arabia', 'arabic', 'aramco', 'arch', 'archer', 'archie', 'arctic', 'argentina', 'aries', 'arizona',
            'arkansas', 'arlen', 'arlene', 'arlington', 'armand', 'armenia', 'armstrong', 'arnold', 'arthur',
            'ascii', 'asia', 'aspen', 'astoria', 'athens', 'atlanta', 'atlantic', 'atlas', 'atomic', 'audrey',
            'august', 'augusta', 'augustus', 'aurora', 'austin', 'australia', 'austria', 'autumn', 'avalon',
            'avenue', 'avery', 'avon', 'aweekly', 'aztec', 'azure'
        }
    
    def _build_known_good_words(self) -> Set[str]:
        """Build a comprehensive set of known good English words."""
        good_words = set()
        
        # Core vocabulary by category
        categories = {
            # Basic nouns - everyday objects
            'objects': [
                'table', 'chair', 'desk', 'bed', 'door', 'window', 'wall', 'floor', 'ceiling', 'roof',
                'house', 'home', 'room', 'kitchen', 'bathroom', 'bedroom', 'office', 'garage', 'garden',
                'yard', 'fence', 'gate', 'path', 'road', 'street', 'bridge', 'building', 'store',
                'shop', 'market', 'school', 'library', 'hospital', 'church', 'bank', 'hotel', 'restaurant',
                'book', 'paper', 'pen', 'pencil', 'crayon', 'marker', 'brush', 'paint', 'picture', 'photo',
                'mirror', 'clock', 'watch', 'calendar', 'map', 'globe', 'computer', 'phone', 'television',
                'radio', 'camera', 'music', 'song', 'movie', 'game', 'toy', 'ball', 'doll', 'puzzle',
                'card', 'letter', 'package', 'box', 'bag', 'basket', 'bucket', 'bottle', 'jar', 'can',
                'cup', 'mug', 'glass', 'plate', 'bowl', 'spoon', 'fork', 'knife', 'napkin', 'towel',
                'soap', 'shampoo', 'toothbrush', 'toothpaste', 'medicine', 'bandage', 'pillow', 'blanket',
                'sheet', 'mattress', 'closet', 'drawer', 'shelf', 'cabinet', 'counter', 'sink', 'faucet',
                'stove', 'oven', 'microwave', 'refrigerator', 'freezer', 'dishwasher', 'washing', 'dryer',
                'vacuum', 'broom', 'mop', 'bucket', 'trash', 'garbage', 'recycling', 'compost'
            ],
            
            # Body parts
            'body': [
                'head', 'hair', 'face', 'forehead', 'eyebrow', 'eyelash', 'eye', 'eyelid', 'pupil',
                'nose', 'nostril', 'mouth', 'lip', 'tongue', 'tooth', 'teeth', 'gums', 'jaw', 'chin',
                'cheek', 'ear', 'earlobe', 'neck', 'throat', 'shoulder', 'chest', 'breast', 'back',
                'spine', 'waist', 'hip', 'stomach', 'belly', 'navel', 'arm', 'elbow', 'wrist', 'hand',
                'palm', 'finger', 'thumb', 'nail', 'knuckle', 'leg', 'thigh', 'knee', 'shin', 'calf',
                'ankle', 'foot', 'heel', 'toe', 'sole', 'skin', 'muscle', 'bone', 'joint', 'blood',
                'vein', 'artery', 'heart', 'lung', 'liver', 'kidney', 'brain', 'nerve', 'voice'
            ],
            
            # Animals
            'animals': [
                'dog', 'puppy', 'cat', 'kitten', 'bird', 'fish', 'horse', 'pony', 'cow', 'calf', 'bull',
                'pig', 'piglet', 'sheep', 'lamb', 'goat', 'kid', 'chicken', 'chick', 'rooster', 'hen',
                'duck', 'duckling', 'goose', 'turkey', 'rabbit', 'bunny', 'hamster', 'guinea', 'mouse',
                'rat', 'squirrel', 'chipmunk', 'beaver', 'raccoon', 'skunk', 'possum', 'fox', 'wolf',
                'coyote', 'bear', 'deer', 'elk', 'moose', 'buffalo', 'bison', 'lion', 'tiger', 'leopard',
                'cheetah', 'panther', 'jaguar', 'lynx', 'bobcat', 'elephant', 'rhino', 'hippo', 'giraffe',
                'zebra', 'antelope', 'gazelle', 'monkey', 'ape', 'gorilla', 'chimpanzee', 'orangutan',
                'snake', 'lizard', 'turtle', 'tortoise', 'frog', 'toad', 'salamander', 'newt', 'fish',
                'shark', 'whale', 'dolphin', 'seal', 'walrus', 'otter', 'penguin', 'eagle', 'hawk',
                'owl', 'falcon', 'vulture', 'crow', 'raven', 'robin', 'sparrow', 'cardinal', 'blue',
                'wren', 'finch', 'canary', 'parrot', 'peacock', 'swan', 'pelican', 'flamingo', 'crane',
                'heron', 'stork', 'ostrich', 'emu', 'bee', 'wasp', 'hornet', 'ant', 'termite', 'fly',
                'mosquito', 'gnat', 'moth', 'butterfly', 'caterpillar', 'worm', 'spider', 'tick',
                'scorpion', 'lobster', 'crab', 'shrimp', 'oyster', 'clam', 'mussel', 'snail', 'slug'
            ],
            
            # Colors
            'colors': [
                'red', 'orange', 'yellow', 'green', 'blue', 'purple', 'pink', 'brown', 'black', 'white',
                'gray', 'grey', 'tan', 'beige', 'cream', 'ivory', 'gold', 'silver', 'bronze', 'copper',
                'maroon', 'crimson', 'scarlet', 'coral', 'salmon', 'peach', 'apricot', 'amber', 'lime',
                'olive', 'forest', 'mint', 'teal', 'turquoise', 'aqua', 'cyan', 'navy', 'royal', 'sky',
                'indigo', 'violet', 'lavender', 'plum', 'magenta', 'fuchsia', 'rose', 'burgundy', 'wine'
            ],
            
            # Common actions/verbs
            'actions': [
                'walk', 'run', 'jog', 'sprint', 'march', 'skip', 'hop', 'jump', 'leap', 'bound', 'crawl',
                'creep', 'slide', 'slip', 'fall', 'trip', 'stumble', 'climb', 'ascend', 'descend',
                'sit', 'stand', 'lie', 'rest', 'sleep', 'nap', 'doze', 'wake', 'rise', 'get', 'move',
                'go', 'come', 'arrive', 'depart', 'leave', 'stay', 'remain', 'wait', 'hurry', 'rush',
                'eat', 'drink', 'swallow', 'chew', 'bite', 'lick', 'taste', 'smell', 'sniff', 'breathe',
                'inhale', 'exhale', 'sigh', 'yawn', 'cough', 'sneeze', 'hiccup', 'burp', 'vomit',
                'look', 'see', 'watch', 'observe', 'stare', 'gaze', 'glance', 'peek', 'blink', 'wink',
                'hear', 'listen', 'whisper', 'talk', 'speak', 'say', 'tell', 'ask', 'answer', 'reply',
                'call', 'shout', 'yell', 'scream', 'sing', 'hum', 'whistle', 'laugh', 'giggle', 'chuckle',
                'smile', 'grin', 'frown', 'cry', 'weep', 'sob', 'moan', 'groan', 'sigh', 'gasp',
                'touch', 'feel', 'hold', 'grab', 'grasp', 'grip', 'squeeze', 'pinch', 'poke', 'pat',
                'rub', 'scratch', 'tickle', 'hug', 'embrace', 'kiss', 'push', 'pull', 'lift', 'carry',
                'drag', 'drop', 'throw', 'toss', 'catch', 'pick', 'choose', 'select', 'take', 'give',
                'hand', 'pass', 'offer', 'receive', 'accept', 'refuse', 'reject', 'keep', 'save',
                'lose', 'find', 'search', 'hunt', 'seek', 'hide', 'cover', 'uncover', 'reveal', 'show',
                'make', 'create', 'build', 'construct', 'assemble', 'install', 'repair', 'fix', 'mend',
                'break', 'crack', 'split', 'tear', 'rip', 'cut', 'slice', 'chop', 'stab', 'pierce',
                'open', 'close', 'shut', 'lock', 'unlock', 'turn', 'twist', 'spin', 'rotate', 'flip',
                'fold', 'unfold', 'wrap', 'unwrap', 'tie', 'untie', 'knot', 'bind', 'release', 'free',
                'clean', 'wash', 'scrub', 'wipe', 'dry', 'polish', 'dust', 'vacuum', 'sweep', 'mop',
                'cook', 'bake', 'roast', 'fry', 'boil', 'steam', 'grill', 'toast', 'heat', 'cool',
                'freeze', 'melt', 'pour', 'spill', 'splash', 'drip', 'leak', 'flow', 'stream', 'flood',
                'read', 'write', 'draw', 'paint', 'color', 'sketch', 'erase', 'type', 'print', 'copy',
                'cut', 'paste', 'delete', 'save', 'load', 'download', 'upload', 'send', 'receive',
                'work', 'labor', 'toil', 'effort', 'try', 'attempt', 'practice', 'rehearse', 'perform',
                'play', 'game', 'sport', 'compete', 'race', 'win', 'lose', 'tie', 'draw', 'score',
                'teach', 'learn', 'study', 'remember', 'forget', 'think', 'ponder', 'wonder', 'imagine',
                'dream', 'hope', 'wish', 'want', 'need', 'like', 'love', 'hate', 'enjoy', 'prefer',
                'help', 'assist', 'aid', 'support', 'encourage', 'comfort', 'console', 'protect', 'defend',
                'attack', 'fight', 'battle', 'war', 'peace', 'agree', 'disagree', 'argue', 'debate',
                'buy', 'sell', 'trade', 'exchange', 'pay', 'spend', 'cost', 'price', 'value', 'worth',
                'own', 'have', 'possess', 'belong', 'share', 'divide', 'split', 'separate', 'join',
                'connect', 'link', 'attach', 'detach', 'remove', 'add', 'include', 'exclude', 'contain'
            ],
            
            # Common adjectives
            'adjectives': [
                'big', 'large', 'huge', 'giant', 'enormous', 'massive', 'tiny', 'small', 'little', 'mini',
                'tall', 'high', 'short', 'low', 'long', 'brief', 'wide', 'narrow', 'broad', 'thin',
                'thick', 'fat', 'skinny', 'lean', 'heavy', 'light', 'dense', 'sparse', 'full', 'empty',
                'deep', 'shallow', 'flat', 'steep', 'smooth', 'rough', 'bumpy', 'sharp', 'dull', 'pointed',
                'round', 'square', 'oval', 'circular', 'straight', 'curved', 'bent', 'twisted', 'crooked',
                'hot', 'warm', 'cool', 'cold', 'freezing', 'boiling', 'burning', 'icy', 'frozen', 'melted',
                'wet', 'dry', 'damp', 'moist', 'humid', 'arid', 'soaked', 'soggy', 'muddy', 'dusty',
                'clean', 'dirty', 'filthy', 'spotless', 'stained', 'pure', 'fresh', 'stale', 'rotten',
                'new', 'old', 'ancient', 'modern', 'current', 'recent', 'past', 'future', 'early', 'late',
                'fast', 'quick', 'rapid', 'swift', 'slow', 'sluggish', 'gradual', 'sudden', 'instant',
                'loud', 'noisy', 'quiet', 'silent', 'soft', 'gentle', 'harsh', 'rough', 'smooth', 'calm',
                'peaceful', 'violent', 'angry', 'mad', 'furious', 'happy', 'glad', 'joyful', 'cheerful',
                'sad', 'unhappy', 'miserable', 'depressed', 'excited', 'thrilled', 'bored', 'interested',
                'curious', 'surprised', 'shocked', 'amazed', 'confused', 'clear', 'obvious', 'hidden',
                'secret', 'private', 'public', 'open', 'closed', 'locked', 'free', 'busy', 'occupied',
                'available', 'empty', 'full', 'complete', 'finished', 'done', 'ready', 'prepared',
                'easy', 'simple', 'hard', 'difficult', 'complex', 'complicated', 'tough', 'challenging',
                'safe', 'dangerous', 'risky', 'secure', 'protected', 'vulnerable', 'weak', 'strong',
                'powerful', 'mighty', 'gentle', 'kind', 'nice', 'mean', 'cruel', 'evil', 'good', 'bad',
                'right', 'wrong', 'correct', 'incorrect', 'true', 'false', 'real', 'fake', 'artificial',
                'natural', 'wild', 'tame', 'domestic', 'foreign', 'local', 'native', 'strange', 'weird',
                'normal', 'regular', 'usual', 'common', 'rare', 'special', 'unique', 'ordinary', 'plain',
                'fancy', 'elegant', 'beautiful', 'pretty', 'handsome', 'ugly', 'attractive', 'cute',
                'lovely', 'gorgeous', 'stunning', 'amazing', 'wonderful', 'awesome', 'terrible', 'awful',
                'horrible', 'pleasant', 'unpleasant', 'comfortable', 'uncomfortable', 'cozy', 'spacious',
                'cramped', 'tight', 'loose', 'relaxed', 'tense', 'stressed', 'calm', 'nervous', 'scared',
                'afraid', 'fearful', 'brave', 'bold', 'shy', 'timid', 'confident', 'proud', 'humble',
                'polite', 'rude', 'friendly', 'unfriendly', 'helpful', 'unhelpful', 'generous', 'selfish',
                'honest', 'dishonest', 'loyal', 'faithful', 'trustworthy', 'reliable', 'responsible',
                'smart', 'intelligent', 'clever', 'wise', 'stupid', 'foolish', 'silly', 'funny', 'serious',
                'important', 'unimportant', 'necessary', 'unnecessary', 'useful', 'useless', 'valuable',
                'worthless', 'expensive', 'cheap', 'affordable', 'costly', 'rich', 'wealthy', 'poor',
                'broke', 'healthy', 'sick', 'ill', 'well', 'fine', 'tired', 'exhausted', 'energetic',
                'active', 'lazy', 'busy', 'idle', 'working', 'resting', 'sleeping', 'awake', 'alert'
            ],
            
            # Food and drink
            'food': [
                'bread', 'toast', 'sandwich', 'burger', 'pizza', 'pasta', 'spaghetti', 'noodles', 'rice',
                'cereal', 'oatmeal', 'pancakes', 'waffles', 'eggs', 'bacon', 'sausage', 'ham', 'chicken',
                'turkey', 'beef', 'pork', 'lamb', 'fish', 'salmon', 'tuna', 'shrimp', 'lobster', 'crab',
                'cheese', 'butter', 'milk', 'cream', 'yogurt', 'ice', 'soup', 'stew', 'salad', 'vegetables',
                'fruit', 'apple', 'banana', 'orange', 'grape', 'strawberry', 'blueberry', 'raspberry',
                'blackberry', 'cherry', 'peach', 'pear', 'plum', 'pineapple', 'mango', 'kiwi', 'lemon',
                'lime', 'grapefruit', 'melon', 'watermelon', 'cantaloupe', 'honeydew', 'coconut', 'avocado',
                'tomato', 'potato', 'carrot', 'onion', 'garlic', 'pepper', 'cucumber', 'lettuce', 'spinach',
                'broccoli', 'cauliflower', 'cabbage', 'celery', 'corn', 'peas', 'beans', 'mushrooms',
                'nuts', 'peanuts', 'almonds', 'walnuts', 'pecans', 'cashews', 'seeds', 'raisins', 'dates',
                'honey', 'sugar', 'salt', 'pepper', 'spices', 'herbs', 'vanilla', 'chocolate', 'candy',
                'cookies', 'cake', 'pie', 'donuts', 'muffins', 'brownies', 'pudding', 'jelly', 'jam',
                'peanut', 'ketchup', 'mustard', 'mayonnaise', 'sauce', 'dressing', 'oil', 'vinegar',
                'water', 'juice', 'soda', 'coffee', 'tea', 'beer', 'wine', 'alcohol', 'cocktail'
            ],
            
            # Time and weather
            'time_weather': [
                'time', 'second', 'minute', 'hour', 'day', 'week', 'month', 'year', 'decade', 'century',
                'morning', 'afternoon', 'evening', 'night', 'midnight', 'noon', 'dawn', 'dusk', 'twilight',
                'sunrise', 'sunset', 'today', 'yesterday', 'tomorrow', 'now', 'then', 'soon', 'later',
                'before', 'after', 'during', 'while', 'until', 'since', 'always', 'never', 'sometimes',
                'often', 'rarely', 'seldom', 'usually', 'normally', 'frequently', 'occasionally',
                'early', 'late', 'on', 'prompt', 'delayed', 'quick', 'slow', 'fast', 'rapid', 'gradual',
                'weather', 'climate', 'temperature', 'hot', 'warm', 'cool', 'cold', 'freezing', 'mild',
                'sunny', 'bright', 'clear', 'cloudy', 'overcast', 'gray', 'dark', 'light', 'shade',
                'shadow', 'rain', 'drizzle', 'shower', 'downpour', 'storm', 'thunder', 'lightning',
                'snow', 'sleet', 'hail', 'ice', 'frost', 'fog', 'mist', 'wind', 'breeze', 'gust',
                'calm', 'still', 'humid', 'dry', 'wet', 'damp', 'moist', 'soaked', 'drought', 'flood',
                'season', 'spring', 'summer', 'fall', 'autumn', 'winter', 'january', 'february', 'march',
                'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december',
                'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'weekend',
                'weekday', 'holiday', 'vacation', 'birthday', 'anniversary', 'celebration', 'party'
            ],
            
            # Nature and environment
            'nature': [
                'nature', 'environment', 'earth', 'world', 'planet', 'globe', 'land', 'ground', 'soil',
                'dirt', 'mud', 'sand', 'rock', 'stone', 'pebble', 'boulder', 'mountain', 'hill', 'valley',
                'canyon', 'cliff', 'cave', 'tunnel', 'hole', 'pit', 'crater', 'volcano', 'earthquake',
                'water', 'ocean', 'sea', 'lake', 'pond', 'river', 'stream', 'creek', 'brook', 'waterfall',
                'rapids', 'wave', 'tide', 'current', 'flow', 'island', 'peninsula', 'continent', 'country',
                'state', 'province', 'city', 'town', 'village', 'neighborhood', 'area', 'region', 'zone',
                'forest', 'woods', 'jungle', 'tree', 'branch', 'trunk', 'root', 'leaf', 'leaves', 'bark',
                'flower', 'bloom', 'bud', 'petal', 'stem', 'seed', 'fruit', 'vegetable', 'plant', 'herb',
                'grass', 'lawn', 'field', 'meadow', 'pasture', 'farm', 'crop', 'harvest', 'garden',
                'park', 'playground', 'beach', 'shore', 'coast', 'desert', 'oasis', 'swamp', 'marsh',
                'sky', 'air', 'atmosphere', 'space', 'universe', 'galaxy', 'star', 'sun', 'moon',
                'planet', 'comet', 'meteor', 'asteroid', 'satellite', 'cloud', 'rainbow', 'horizon'
            ],
            
            # Numbers and math
            'numbers': [
                'zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
                'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen',
                'nineteen', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety',
                'hundred', 'thousand', 'million', 'billion', 'trillion', 'first', 'second', 'third',
                'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth', 'last', 'final',
                'number', 'count', 'amount', 'quantity', 'total', 'sum', 'difference', 'product',
                'quotient', 'fraction', 'decimal', 'percent', 'ratio', 'proportion', 'average', 'mean',
                'plus', 'minus', 'times', 'divided', 'equals', 'add', 'subtract', 'multiply', 'divide',
                'calculate', 'compute', 'solve', 'answer', 'result', 'solution', 'problem', 'equation',
                'formula', 'math', 'mathematics', 'arithmetic', 'algebra', 'geometry', 'measurement',
                'length', 'width', 'height', 'depth', 'distance', 'area', 'volume', 'weight', 'mass',
                'size', 'scale', 'dimension', 'meter', 'inch', 'foot', 'yard', 'mile', 'gram', 'pound',
                'ounce', 'ton', 'gallon', 'quart', 'pint', 'cup', 'tablespoon', 'teaspoon', 'liter'
            ],
            
            # Common function words
            'function_words': [
                'the', 'and', 'or', 'but', 'if', 'then', 'else', 'when', 'where', 'why', 'how', 'what',
                'who', 'which', 'that', 'this', 'these', 'those', 'here', 'there', 'everywhere', 'somewhere',
                'anywhere', 'nowhere', 'everyone', 'someone', 'anyone', 'no', 'all', 'some', 'any',
                'many', 'few', 'several', 'more', 'most', 'less', 'least', 'enough', 'too', 'very',
                'quite', 'rather', 'pretty', 'really', 'truly', 'actually', 'certainly', 'probably',
                'maybe', 'perhaps', 'possibly', 'definitely', 'absolutely', 'completely', 'totally',
                'entirely', 'partly', 'mostly', 'mainly', 'generally', 'usually', 'normally', 'typically',
                'especially', 'particularly', 'specifically', 'exactly', 'precisely', 'approximately',
                'about', 'around', 'nearly', 'almost', 'just', 'only', 'even', 'still', 'yet',
                'already', 'again', 'once', 'twice', 'always', 'never', 'sometimes', 'often', 'rarely',
                'seldom', 'frequently', 'occasionally', 'constantly', 'continuously', 'forever', 'temporarily'
            ]
        }
        
        # Add all words from all categories
        for category, words in categories.items():
            good_words.update(words)
        
        return good_words
    
    def is_good_word(self, word: str) -> bool:
        """Check if word is a good English word."""
        word = word.lower().strip()
        
        # Basic checks
        if len(word) < 3 or len(word) > 10:
            return False
        
        if not word.isalpha():
            return False
        
        # Check if it's definitely bad
        if word in self.definitely_bad:
            return False
        
        # Check bad patterns
        for pattern in self.bad_patterns:
            if re.search(pattern, word):
                return False
        
        # If it's in our known good words, it's definitely good
        if word in self.known_good_words:
            return True
        
        # Additional checks for unknown words
        # Must have reasonable vowel/consonant distribution
        vowels = sum(1 for c in word if c in 'aeiou')
        consonants = len(word) - vowels
        
        if vowels == 0 or consonants == 0:
            return False
        
        vowel_ratio = vowels / len(word)
        if vowel_ratio < 0.2 or vowel_ratio > 0.7:
            return False
        
        # Check for common English patterns
        # Must not start with uncommon combinations
        if word.startswith(('xz', 'qx', 'zx', 'qq', 'kk', 'jj', 'vv', 'ww')):
            return False
        
        # Must not end with uncommon combinations
        if word.endswith(('qx', 'xz', 'zx', 'qq', 'kk', 'jj', 'vv', 'ww')):
            return False
        
        # Use scorer for final check
        score = self.scorer.score_word(word)
        return score.total_score >= 0.8  # High threshold for unknown words
    
    def categorize_word(self, word: str) -> Tuple[str, float]:
        """Categorize word by quality."""
        score = self.scorer.score_word(word)
        
        # Boost score if it's in our known good words
        if word in self.known_good_words:
            score.total_score = min(1.0, score.total_score * 1.2)
        
        if score.total_score >= 0.95:
            return "excellent", score.total_score
        elif score.total_score >= 0.85:
            return "very_good", score.total_score
        elif score.total_score >= 0.75:
            return "good", score.total_score
        else:
            return "acceptable", score.total_score


def generate_ultra_clean_wordlist() -> List[str]:
    """Generate ultra-clean wordlist with strict quality control."""
    filter = UltraCleanFilter()
    
    # Load source wordlists
    print("Loading source wordlists...")
    bip39_words, top_english = load_or_download_words()
    
    # Filter BIP39 words
    print("Filtering BIP39 words...")
    final_words = set()
    excluded_bip39 = []
    
    for word in bip39_words:
        if filter.is_good_word(word):
            final_words.add(word)
        else:
            excluded_bip39.append(word)
    
    print(f"Kept {len(final_words)} BIP39 words, excluded {len(excluded_bip39)}")
    
    # Process top English words
    print("Processing top English words...")
    candidates = []
    processed = 0
    
    for word in top_english:
        word = word.lower().strip()
        
        if word in final_words:
            continue
        
        if filter.is_good_word(word):
            category, score = filter.categorize_word(word)
            candidates.append((word, score, category))
        
        processed += 1
        if processed % 10000 == 0:
            print(f"Processed {processed} words, found {len(candidates)} candidates...")
    
    # Sort by score (highest first)
    candidates.sort(key=lambda x: x[1], reverse=True)
    
    # Add best candidates
    print(f"Adding {TARGET_SIZE - len(final_words)} more words...")
    for word, score, category in candidates:
        if len(final_words) >= TARGET_SIZE:
            break
        final_words.add(word)
    
    wordlist = sorted(list(final_words))[:TARGET_SIZE]
    
    return wordlist


def main():
    """Generate ultra-clean wordlist."""
    print("Ultra-Clean Wordlist Generator")
    print("Common, recognizable English words only")
    print("=" * 50)
    
    wordlist = generate_ultra_clean_wordlist()
    
    print(f"\nGenerated {len(wordlist)} words")
    print(f"First 50 words: {wordlist[:50]}")
    print(f"Random sample from middle: {wordlist[30000:30020]}")
    
    # Save results
    output_dir = Path("wordlists")
    output_dir.mkdir(exist_ok=True)
    
    # Save wordlist
    save_wordlist(wordlist, "../wordlists/ultra_clean_65536.txt")
    
    # Save with metadata
    metadata = {
        "version": "5.0",
        "word_count": len(wordlist),
        "generation_method": "ultra_clean_common_words",
        "includes_bip39": True,
        "description": "Ultra-clean wordlist with common, recognizable English words only",
        "words": wordlist
    }
    
    with open(output_dir / "ultra_clean_65536.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✓ Saved ultra-clean wordlist to wordlists/ultra_clean_65536.txt")
    print("✓ Saved metadata to wordlists/ultra_clean_65536.json")


if __name__ == "__main__":
    main()