#!/usr/bin/env python3
"""
Self-validated wordlist generator using Claude's validation criteria.
Processes 1000 words at a time with strict validation.

UV Dependencies:
# Install UV if not available: curl -LsSf https://astral.sh/uv/install.sh | sh
# Run this script: uv run python self_validated_generator.py
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests>=2.31.0",
# ]
# ///

import json
import time
from pathlib import Path
from typing import List, Set, Dict, Optional, Tuple
from dataclasses import dataclass
import re

from generate_wordlist import load_or_download_words


@dataclass
class ValidationState:
    """Track validation progress."""
    validated_words: Set[str]
    rejected_words: Set[str]
    remaining_candidates: List[str]
    batches_processed: int
    start_time: float


class SelfValidatedGenerator:
    """Generator that validates words using Claude's criteria internally."""
    
    def __init__(self, batch_size: int = 1000):
        """Initialize with batch size for processing."""
        self.batch_size = batch_size
        self.target_size = 65536
        self.output_dir = Path("wordlists")
        self.output_dir.mkdir(exist_ok=True)
        
        self.state_file = self.output_dir / "self_validation_state.json"
        self.log_file = self.output_dir / "self_validation_log.json"
        
        # Initialize validation sets
        self.proper_nouns = self._load_proper_nouns()
        self.abbreviations = self._load_abbreviations()
        self.foreign_words = self._load_foreign_words()
        
    def _load_proper_nouns(self) -> Set[str]:
        """Load comprehensive list of proper nouns to reject."""
        proper_nouns = set()
        
        # Personal names
        names = [
            'john', 'mary', 'james', 'robert', 'michael', 'william', 'david', 'richard',
            'charles', 'joseph', 'thomas', 'paul', 'george', 'henry', 'edward', 'peter',
            'frank', 'daniel', 'matthew', 'anthony', 'donald', 'mark', 'steven', 'andrew',
            'christopher', 'joshua', 'kenneth', 'kevin', 'brian', 'larry', 'justin', 'scott',
            'benjamin', 'samuel', 'frank', 'alexander', 'jacob', 'gary', 'nicholas', 'eric',
            'stephen', 'jonathan', 'ronald', 'albert', 'timothy', 'jason', 'jeffrey', 'ryan',
            'jacob', 'gary', 'nicholas', 'eric', 'jonathan', 'stephen', 'larry', 'justin',
            'sarah', 'elizabeth', 'jennifer', 'linda', 'barbara', 'susan', 'jessica', 'helen',
            'nancy', 'betty', 'dorothy', 'lisa', 'karen', 'donna', 'michelle', 'carol',
            'emily', 'ashley', 'kimberly', 'donna', 'carol', 'michelle', 'ruth', 'sharon',
            'laura', 'cynthia', 'amy', 'angela', 'brenda', 'anna', 'rebecca', 'kathleen',
            'amanda', 'stephanie', 'carolyn', 'christine', 'janet', 'catherine', 'samantha',
            'deborah', 'virginia', 'maria', 'julia', 'victoria', 'kelly', 'lauren', 'christina',
            'joan', 'evelyn', 'judith', 'nicole', 'diane', 'alice', 'julie', 'joyce',
            'aaron', 'adam', 'alan', 'albert', 'alex', 'alfred', 'allan', 'allen',
            'alvin', 'amos', 'andre', 'andy', 'angelo', 'antonio', 'arnold', 'arthur',
            'austin', 'barry', 'ben', 'bernard', 'bert', 'bill', 'billy', 'bob',
            'bobby', 'brad', 'brandon', 'bruce', 'bryan', 'carl', 'carlos', 'chad',
            'charlie', 'chris', 'clarence', 'clark', 'claude', 'clifford', 'clinton', 'colin',
            'craig', 'curtis', 'dale', 'dan', 'danny', 'darrell', 'dave', 'dean',
            'dennis', 'derek', 'dick', 'don', 'donald', 'douglas', 'duane', 'earl',
            'eddie', 'edgar', 'edwin', 'elmer', 'ernest', 'eugene', 'evan', 'felix',
            'floyd', 'francis', 'fred', 'frederick', 'gabriel', 'gary', 'gene', 'geoffrey',
            'gerald', 'gilbert', 'glen', 'glenn', 'gordon', 'greg', 'gregory', 'harold',
            'harry', 'harvey', 'hector', 'herbert', 'herman', 'howard', 'hugh', 'ian',
            'isaac', 'ivan', 'jack', 'jackson', 'jacob', 'jake', 'jamie', 'jason',
            'jay', 'jeff', 'jeffrey', 'jeremy', 'jerome', 'jerry', 'jesse', 'jesus',
            'jim', 'jimmy', 'joe', 'joel', 'joey', 'johnny', 'jon', 'jonathan',
            'jordan', 'jorge', 'jose', 'joseph', 'joshua', 'juan', 'julian', 'julio',
            'justin', 'karl', 'keith', 'kelly', 'ken', 'kenneth', 'kent', 'kevin',
            'kirk', 'kurt', 'kyle', 'lance', 'larry', 'lawrence', 'lee', 'leo',
            'leon', 'leonard', 'leroy', 'leslie', 'lester', 'lewis', 'lloyd', 'logan',
            'louis', 'lucas', 'luis', 'luke', 'manuel', 'marc', 'marcus', 'mario',
            'marvin', 'mason', 'matt', 'matthew', 'maurice', 'max', 'melvin', 'michael',
            'mike', 'miguel', 'mitchell', 'morris', 'nathan', 'neil', 'nelson', 'nicholas',
            'nick', 'noah', 'norman', 'oliver', 'oscar', 'patrick', 'pedro', 'perry',
            'pete', 'peter', 'philip', 'phillip', 'ralph', 'ramon', 'randall', 'randy',
            'raul', 'ray', 'raymond', 'reginald', 'ricardo', 'richard', 'rick', 'ricky',
            'robert', 'roberto', 'rodney', 'roger', 'roland', 'ron', 'ronald', 'roy',
            'ruben', 'russell', 'ryan', 'salvador', 'sam', 'samuel', 'scott', 'sean',
            'sergio', 'seth', 'shane', 'shawn', 'sidney', 'simon', 'stanley', 'stephen',
            'steve', 'steven', 'ted', 'terry', 'theodore', 'thomas', 'tim', 'timothy',
            'todd', 'tom', 'tommy', 'tony', 'tracy', 'travis', 'troy', 'tyler',
            'vernon', 'victor', 'vincent', 'wallace', 'walter', 'warren', 'wayne', 'wesley',
            'willard', 'willie', 'zachary'
        ]
        
        # Surnames
        surnames = [
            'smith', 'johnson', 'williams', 'jones', 'brown', 'davis', 'miller', 'wilson',
            'moore', 'taylor', 'anderson', 'thomas', 'jackson', 'white', 'harris', 'martin',
            'thompson', 'garcia', 'martinez', 'robinson', 'clark', 'rodriguez', 'lewis', 'lee',
            'walker', 'hall', 'allen', 'young', 'hernandez', 'king', 'wright', 'lopez',
            'hill', 'scott', 'green', 'adams', 'baker', 'gonzalez', 'nelson', 'carter',
            'mitchell', 'perez', 'roberts', 'turner', 'phillips', 'campbell', 'parker', 'evans',
            'edwards', 'collins', 'stewart', 'sanchez', 'morris', 'rogers', 'reed', 'cook',
            'morgan', 'bell', 'murphy', 'bailey', 'rivera', 'cooper', 'richardson', 'cox',
            'howard', 'ward', 'torres', 'peterson', 'gray', 'ramirez', 'james', 'watson',
            'brooks', 'kelly', 'sanders', 'price', 'bennett', 'wood', 'barnes', 'ross',
            'henderson', 'coleman', 'jenkins', 'perry', 'powell', 'long', 'patterson', 'hughes',
            'flores', 'washington', 'butler', 'simmons', 'foster', 'gonzales', 'bryant', 'alexander',
            'russell', 'griffin', 'diaz', 'hayes', 'myers', 'ford', 'hamilton', 'graham',
            'sullivan', 'wallace', 'woods', 'cole', 'west', 'jordan', 'owens', 'reynolds',
            'fisher', 'ellis', 'harrison', 'gibson', 'mcdonald', 'cruz', 'marshall', 'ortiz',
            'gomez', 'murray', 'freeman', 'wells', 'webb', 'simpson', 'stevens', 'tucker',
            'porter', 'hunter', 'hicks', 'crawford', 'henry', 'boyd', 'mason', 'morales',
            'kennedy', 'warren', 'dixon', 'ramos', 'reyes', 'burns', 'gordon', 'shaw',
            'holmes', 'rice', 'robertson', 'hunt', 'black', 'daniels', 'palmer', 'mills',
            'nichols', 'grant', 'knight', 'ferguson', 'rose', 'stone', 'hawkins', 'dunn',
            'perkins', 'hudson', 'spencer', 'gardner', 'stephens', 'payne', 'pierce', 'berry',
            'matthews', 'arnold', 'wagner', 'willis', 'ray', 'watkins', 'olson', 'carroll',
            'duncan', 'snyder', 'hart', 'cunningham', 'bradley', 'lane', 'andrews', 'ruiz',
            'harper', 'fox', 'riley', 'armstrong', 'carpenter', 'weaver', 'greene', 'lawrence',
            'elliott', 'chavez', 'sims', 'austin', 'peters', 'kelley', 'franklin', 'lawson'
        ]
        
        # Places
        places = [
            'london', 'paris', 'york', 'washington', 'chicago', 'boston', 'texas', 'california',
            'america', 'europe', 'asia', 'africa', 'china', 'india', 'france', 'germany',
            'england', 'spain', 'italy', 'russia', 'japan', 'mexico', 'canada', 'australia',
            'brazil', 'argentina', 'egypt', 'israel', 'ireland', 'scotland', 'wales', 'korea',
            'vietnam', 'thailand', 'philippines', 'indonesia', 'malaysia', 'singapore', 'belgium',
            'netherlands', 'switzerland', 'austria', 'poland', 'greece', 'turkey', 'sweden',
            'norway', 'denmark', 'finland', 'portugal', 'romania', 'hungary', 'ukraine', 'berlin',
            'madrid', 'rome', 'moscow', 'beijing', 'tokyo', 'delhi', 'mumbai', 'shanghai',
            'sydney', 'melbourne', 'toronto', 'vancouver', 'montreal', 'dubai', 'cairo', 'athens',
            'amsterdam', 'brussels', 'vienna', 'prague', 'budapest', 'warsaw', 'lisbon', 'dublin',
            'edinburgh', 'glasgow', 'manchester', 'birmingham', 'liverpool', 'oxford', 'cambridge',
            'miami', 'seattle', 'denver', 'atlanta', 'detroit', 'philadelphia', 'phoenix', 'dallas',
            'houston', 'austin', 'portland', 'sacramento', 'oakland', 'berkeley', 'stanford',
            'princeton', 'harvard', 'yale', 'columbia', 'cornell', 'dartmouth', 'pennsylvania',
            'florida', 'georgia', 'virginia', 'maryland', 'ohio', 'michigan', 'illinois', 'indiana',
            'wisconsin', 'minnesota', 'iowa', 'missouri', 'kansas', 'nebraska', 'colorado', 'utah',
            'nevada', 'arizona', 'oregon', 'idaho', 'montana', 'wyoming', 'alaska', 'hawaii',
            'alabama', 'mississippi', 'tennessee', 'kentucky', 'louisiana', 'arkansas', 'oklahoma',
            'bangladesh', 'pakistan', 'afghanistan', 'iran', 'iraq', 'syria', 'jordan', 'lebanon',
            'saudi', 'arabia', 'yemen', 'oman', 'qatar', 'kuwait', 'bahrain', 'cyprus',
            'jamaica', 'cuba', 'haiti', 'dominican', 'puerto', 'rico', 'panama', 'costa',
            'nicaragua', 'honduras', 'guatemala', 'salvador', 'belize', 'venezuela', 'colombia',
            'peru', 'ecuador', 'chile', 'uruguay', 'paraguay', 'bolivia', 'guyana', 'suriname',
            'kenya', 'nigeria', 'ghana', 'ethiopia', 'uganda', 'tanzania', 'zimbabwe', 'zambia',
            'morocco', 'tunisia', 'libya', 'sudan', 'somalia', 'madagascar', 'mauritius',
            'manhattan', 'brooklyn', 'queens', 'bronx', 'staten', 'jersey', 'newark', 'atlantic',
            'pacific', 'indian', 'arctic', 'antarctic', 'mediterranean', 'caribbean', 'baltic',
            'caspian', 'himalayas', 'alps', 'rockies', 'andes', 'amazon', 'nile', 'mississippi',
            'thames', 'seine', 'rhine', 'danube', 'volga', 'ganges', 'yangtze', 'mekong'
        ]
        
        # Nationalities and languages
        nationalities = [
            'american', 'british', 'french', 'german', 'chinese', 'japanese', 'russian',
            'english', 'spanish', 'italian', 'canadian', 'mexican', 'african', 'asian',
            'european', 'indian', 'australian', 'brazilian', 'argentinian', 'egyptian',
            'israeli', 'irish', 'scottish', 'welsh', 'korean', 'vietnamese', 'thai',
            'filipino', 'indonesian', 'malaysian', 'singaporean', 'belgian', 'dutch',
            'swiss', 'austrian', 'polish', 'greek', 'turkish', 'swedish', 'norwegian',
            'danish', 'finnish', 'portuguese', 'romanian', 'hungarian', 'ukrainian',
            'czech', 'slovak', 'croatian', 'serbian', 'bulgarian', 'albanian', 'lithuanian',
            'latvian', 'estonian', 'icelandic', 'maltese', 'cypriot', 'lebanese', 'syrian',
            'jordanian', 'palestinian', 'iraqi', 'iranian', 'afghan', 'pakistani', 'bangladeshi',
            'nepalese', 'bhutanese', 'mongolian', 'kazakh', 'uzbek', 'turkmen', 'tajik',
            'kyrgyz', 'georgian', 'armenian', 'azerbaijani', 'saudi', 'yemeni', 'omani',
            'qatari', 'kuwaiti', 'bahraini', 'emirati', 'moroccan', 'tunisian', 'libyan',
            'algerian', 'sudanese', 'ethiopian', 'kenyan', 'ugandan', 'tanzanian', 'nigerian',
            'ghanaian', 'senegalese', 'malian', 'burkinabe', 'nigerien', 'chadian', 'cameroonian',
            'congolese', 'angolan', 'mozambican', 'zimbabwean', 'zambian', 'malawian', 'namibian',
            'botswanan', 'malagasy', 'mauritian', 'seychellois', 'jamaican', 'cuban', 'haitian',
            'dominican', 'barbadian', 'trinidadian', 'guyanese', 'surinamese', 'venezuelan',
            'colombian', 'peruvian', 'ecuadorian', 'bolivian', 'chilean', 'uruguayan', 'paraguayan'
        ]
        
        # Religious and cultural terms
        religious = [
            'christian', 'jewish', 'muslim', 'catholic', 'protestant', 'buddhist', 'hindu',
            'islamic', 'judaism', 'christianity', 'islam', 'buddhism', 'hinduism', 'jesus',
            'christ', 'muhammad', 'buddha', 'moses', 'abraham', 'allah', 'yahweh', 'jehovah'
        ]
        
        # Companies and brands (common ones)
        brands = [
            'microsoft', 'apple', 'google', 'amazon', 'facebook', 'twitter', 'instagram',
            'youtube', 'netflix', 'spotify', 'uber', 'airbnb', 'tesla', 'ford', 'toyota',
            'honda', 'nissan', 'bmw', 'mercedes', 'audi', 'volkswagen', 'ferrari', 'porsche',
            'coca', 'cola', 'pepsi', 'mcdonalds', 'burger', 'starbucks', 'subway', 'nike',
            'adidas', 'puma', 'reebok', 'samsung', 'sony', 'panasonic', 'philips', 'siemens',
            'intel', 'amd', 'nvidia', 'cisco', 'oracle', 'ibm', 'dell', 'lenovo', 'asus',
            'walmart', 'target', 'costco', 'kroger', 'walgreens', 'cvs', 'fedex', 'ups',
            'disney', 'warner', 'universal', 'paramount', 'columbia', 'dreamworks', 'pixar'
        ]
        
        # Historical figures
        historical = [
            'napoleon', 'caesar', 'alexander', 'cleopatra', 'churchill', 'roosevelt', 'lincoln',
            'washington', 'jefferson', 'adams', 'madison', 'monroe', 'jackson', 'kennedy',
            'nixon', 'reagan', 'clinton', 'obama', 'trump', 'biden', 'elizabeth', 'victoria',
            'shakespeare', 'newton', 'einstein', 'darwin', 'galileo', 'columbus', 'magellan',
            'mozart', 'beethoven', 'bach', 'chopin', 'wagner', 'verdi', 'brahms', 'handel',
            'plato', 'aristotle', 'socrates', 'kant', 'hegel', 'marx', 'freud', 'jung',
            'picasso', 'monet', 'rembrandt', 'michelangelo', 'leonardo', 'raphael', 'dali'
        ]
        
        # Add all to set
        proper_nouns.update(names)
        proper_nouns.update(surnames)
        proper_nouns.update(places)
        proper_nouns.update(nationalities)
        proper_nouns.update(religious)
        proper_nouns.update(brands)
        proper_nouns.update(historical)
        
        return proper_nouns
    
    def _load_abbreviations(self) -> Set[str]:
        """Load abbreviations and non-standard words."""
        return {
            'der', 'des', 'les', 'del', 'von', 'per', 'non', 'pre', 'sub', 'anti', 'pro',
            'ibid', 'vol', 'fig', 'sec', 'med', 'trans', 'inter', 'semi', 'multi', 'uni',
            'para', 'cit', 'min', 'tel', 'sci', 'proc', 'res', 'com', 'ltd', 'inc', 'corp',
            'usa', 'dna', 'rna', 'hiv', 'aids', 'con', 'vis', 'das', 'une', 'sur', 'los',
            'las', 'san', 'biol', 'chem', 'phys', 'math', 'comp', 'eng', 'med', 'psych',
            'soc', 'econ', 'phil', 'hist', 'geog', 'pol', 'rel', 'edu', 'mil', 'gov',
            'intl', 'natl', 'assn', 'dept', 'univ', 'hosp', 'inst', 'acad', 'lab', 'lib',
            'mus', 'natl', 'org', 'pub', 'soc', 'assoc', 'bros', 'co', 'est', 'jr', 'sr',
            'phd', 'md', 'jd', 'mba', 'ma', 'ba', 'bs', 'ms', 'llb', 'llm', 'esq',
            'rev', 'dr', 'mr', 'mrs', 'ms', 'prof', 'gen', 'col', 'maj', 'capt', 'lt',
            'sgt', 'cpl', 'pvt', 'adm', 'cmdg', 'comdr', 'ens', 'lcdr', 'vadm', 'radm'
        }
    
    def _load_foreign_words(self) -> Set[str]:
        """Load foreign words that haven't been fully adopted into English."""
        return {
            'der', 'die', 'das', 'den', 'dem', 'des', 'ein', 'eine', 'einen', 'einem', 'eines',
            'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'au', 'aux',
            'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'del', 'al',
            'il', 'lo', 'la', 'gli', 'le', 'un', 'uno', 'una', 'dei', 'degli', 'delle',
            'der', 'das', 'den', 'dem', 'des', 'von', 'zu', 'bei', 'mit', 'nach',
            'et', 'ou', 'mais', 'donc', 'or', 'ni', 'car', 'que', 'qui', 'quoi',
            'y', 'e', 'o', 'pero', 'sino', 'aunque', 'porque', 'cuando', 'donde',
            'och', 'eller', 'men', 'så', 'om', 'när', 'där', 'här', 'vad', 'vem',
            'en', 'een', 'de', 'het', 'van', 'voor', 'met', 'aan', 'op', 'in',
            'og', 'eller', 'men', 'så', 'om', 'når', 'hvor', 'hvad', 'hvem', 'hvilken',
            'para', 'por', 'con', 'sin', 'sobre', 'bajo', 'entre', 'hasta', 'desde',
            'pour', 'avec', 'sans', 'sur', 'sous', 'entre', 'dans', 'chez', 'vers',
            'per', 'con', 'senza', 'su', 'sotto', 'tra', 'fra', 'presso', 'verso',
            'für', 'mit', 'ohne', 'auf', 'unter', 'zwischen', 'bei', 'nach', 'vor'
        }
    
    def validate_word(self, word: str) -> Tuple[bool, str]:
        """
        Validate a single word according to Claude's criteria.
        Returns (is_valid, rejection_reason).
        """
        word_lower = word.lower().strip()
        
        # Check length
        if len(word_lower) < 3:
            return False, "too short"
        if len(word_lower) > 12:
            return False, "too long"
        
        # Must be alphabetic
        if not word_lower.isalpha():
            return False, "contains non-alphabetic characters"
        
        # Check against proper nouns
        if word_lower in self.proper_nouns:
            return False, "proper noun"
        
        # Check against abbreviations
        if word_lower in self.abbreviations:
            return False, "abbreviation"
        
        # Check against foreign words
        if word_lower in self.foreign_words:
            return False, "foreign word"
        
        # Check for archaic words
        archaic = {'thou', 'thee', 'thy', 'thine', 'hath', 'hast', 'doth', 'dost', 
                   'shalt', 'wilt', 'art', 'unto', 'ye', 'yea', 'nay', 'wherefore',
                   'whence', 'whither', 'thence', 'thither', 'hither', 'betwixt'}
        if word_lower in archaic:
            return False, "archaic word"
        
        # Check for offensive/inappropriate words
        offensive = {'damn', 'hell', 'bastard', 'bitch', 'shit', 'fuck', 'ass', 'piss',
                    'crap', 'dick', 'cock', 'pussy', 'tit', 'whore', 'slut', 'fag',
                    'nigger', 'kike', 'spic', 'chink', 'gook', 'wop', 'kraut'}
        if word_lower in offensive:
            return False, "inappropriate/offensive"
        
        # Check for unusual letter patterns
        # Too many consecutive vowels
        if re.search(r'[aeiou]{4,}', word_lower):
            return False, "too many consecutive vowels"
        
        # Too many consecutive consonants
        if re.search(r'[bcdfghjklmnpqrstvwxyz]{5,}', word_lower):
            return False, "too many consecutive consonants"
        
        # Weird starting patterns
        if re.search(r'^[xz][^aeiou]', word_lower):
            return False, "unusual starting pattern"
        
        # Triple letters (except for a few valid cases)
        if re.search(r'(.)\1\1', word_lower) and word_lower not in ['committee', 'balloon', 'success']:
            return False, "triple letter pattern"
        
        # All consonants or all vowels
        if not any(c in 'aeiou' for c in word_lower):
            return False, "no vowels"
        if not any(c in 'bcdfghjklmnpqrstvwxyz' for c in word_lower):
            return False, "no consonants"
        
        # Check if it starts with a number when spelled out
        number_words = {'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 
                       'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen',
                       'sixteen', 'seventeen', 'eighteen', 'nineteen', 'twenty', 'thirty',
                       'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety', 'hundred',
                       'thousand', 'million', 'billion', 'trillion'}
        # Number words are actually OK - they're common English words
        
        return True, ""
    
    def load_bip39_words(self) -> Set[str]:
        """Load BIP39 words as validated foundation."""
        bip39_file = self.output_dir / "bip39_english.txt"
        if not bip39_file.exists():
            # Download if needed
            import requests
            response = requests.get('https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/english.txt')
            with open(bip39_file, 'w') as f:
                f.write(response.text)
        
        with open(bip39_file) as f:
            words = {line.strip().lower() for line in f if line.strip()}
        
        return words
    
    def prepare_candidates(self, bip39_words: Set[str]) -> List[str]:
        """Prepare candidate words from 100K corpus."""
        # Load 100K words
        _, top_100k = load_or_download_words()
        
        # Filter candidates
        candidates = []
        for word in top_100k:
            word_lower = word.lower().strip()
            
            # Skip if in BIP39
            if word_lower in bip39_words:
                continue
            
            # Basic length check
            if len(word_lower) < 3 or len(word_lower) > 12:
                continue
            
            # Must be alphabetic
            if not word_lower.isalpha():
                continue
            
            candidates.append(word_lower)
        
        return candidates
    
    def process_batch(self, words: List[str], batch_num: int) -> Tuple[List[str], Dict[str, str]]:
        """Process a batch of words through validation."""
        valid_words = []
        rejection_log = {}
        
        for word in words:
            is_valid, reason = self.validate_word(word)
            if is_valid:
                valid_words.append(word)
            else:
                rejection_log[word] = reason
        
        # Log results
        log_entry = {
            'batch': batch_num,
            'total': len(words),
            'accepted': len(valid_words),
            'rejected': len(rejection_log),
            'acceptance_rate': len(valid_words) / len(words) if words else 0,
            'rejection_summary': {}
        }
        
        # Summarize rejections
        for word, reason in rejection_log.items():
            if reason not in log_entry['rejection_summary']:
                log_entry['rejection_summary'][reason] = 0
            log_entry['rejection_summary'][reason] += 1
        
        # Append to log file
        logs = []
        if self.log_file.exists():
            with open(self.log_file) as f:
                logs = json.load(f)
        logs.append(log_entry)
        with open(self.log_file, 'w') as f:
            json.dump(logs, f, indent=2)
        
        return valid_words, rejection_log
    
    def save_state(self, state: ValidationState):
        """Save current state for resumption."""
        state_data = {
            'validated_words': list(state.validated_words),
            'rejected_words': list(state.rejected_words),
            'remaining_candidates': state.remaining_candidates,
            'batches_processed': state.batches_processed,
            'start_time': state.start_time,
            'timestamp': time.time()
        }
        with open(self.state_file, 'w') as f:
            json.dump(state_data, f, indent=2)
    
    def load_state(self) -> Optional[ValidationState]:
        """Load saved state if available."""
        if not self.state_file.exists():
            return None
        
        try:
            with open(self.state_file) as f:
                data = json.load(f)
            return ValidationState(
                validated_words=set(data['validated_words']),
                rejected_words=set(data['rejected_words']),
                remaining_candidates=data['remaining_candidates'],
                batches_processed=data['batches_processed'],
                start_time=data['start_time']
            )
        except:
            return None
    
    def generate_wordlist(self) -> List[str]:
        """Generate the complete validated wordlist."""
        print("\n" + "="*70)
        print("SELF-VALIDATED WORDLIST GENERATION")
        print("Using Claude's strict validation criteria")
        print("="*70)
        
        # Try to load existing state
        state = self.load_state()
        
        if state is None:
            # Start fresh
            print("\nStarting fresh generation...")
            
            # Load BIP39
            bip39_words = self.load_bip39_words()
            print(f"Loaded {len(bip39_words)} BIP39 words")
            
            # Prepare candidates
            candidates = self.prepare_candidates(bip39_words)
            print(f"Prepared {len(candidates)} candidate words")
            
            state = ValidationState(
                validated_words=bip39_words.copy(),
                rejected_words=set(),
                remaining_candidates=candidates,
                batches_processed=0,
                start_time=time.time()
            )
        else:
            print(f"\nResuming from batch {state.batches_processed}")
            print(f"Current validated words: {len(state.validated_words)}")
        
        # Process batches
        while len(state.validated_words) < self.target_size and state.remaining_candidates:
            # Get next batch
            batch_size = min(self.batch_size, len(state.remaining_candidates))
            batch = state.remaining_candidates[:batch_size]
            state.remaining_candidates = state.remaining_candidates[batch_size:]
            
            # Process batch
            print(f"\nProcessing batch {state.batches_processed + 1} ({len(batch)} words)...")
            valid_words, rejections = self.process_batch(batch, state.batches_processed + 1)
            
            # Update state
            state.validated_words.update(valid_words)
            state.rejected_words.update(rejections.keys())
            state.batches_processed += 1
            
            # Show progress
            print(f"  Accepted: {len(valid_words)} ({len(valid_words)/len(batch)*100:.1f}%)")
            print(f"  Total validated: {len(state.validated_words)}/{self.target_size} ({len(state.validated_words)/self.target_size*100:.1f}%)")
            
            # Show rejection summary
            if rejections:
                reason_counts = {}
                for reason in rejections.values():
                    reason_counts[reason] = reason_counts.get(reason, 0) + 1
                print("  Rejection reasons:")
                for reason, count in sorted(reason_counts.items(), key=lambda x: -x[1]):
                    print(f"    - {reason}: {count}")
            
            # Save state
            self.save_state(state)
            
            # Stop if we have enough
            if len(state.validated_words) >= self.target_size:
                break
        
        # Get final list
        final_words = sorted(list(state.validated_words))[:self.target_size]
        
        # Summary
        elapsed = time.time() - state.start_time
        print(f"\n{'='*70}")
        print(f"GENERATION COMPLETE!")
        print(f"{'='*70}")
        print(f"Total validated words: {len(final_words)}")
        print(f"Total rejected words: {len(state.rejected_words)}")
        print(f"Batches processed: {state.batches_processed}")
        print(f"Time elapsed: {elapsed:.1f} seconds")
        
        return final_words
    
    def save_wordlist(self, words: List[str]):
        """Save the final wordlist."""
        # Save text version
        txt_file = self.output_dir / "self_validated_65536.txt"
        with open(txt_file, 'w') as f:
            for word in words:
                f.write(f"{word}\n")
        
        # Save JSON with metadata
        metadata = {
            'version': '1.0',
            'word_count': len(words),
            'generation_method': 'self_validated',
            'validation_criteria': 'Claude strict criteria',
            'includes_bip39': True,
            'target_size': self.target_size,
            'batch_size': self.batch_size,
            'timestamp': time.time(),
            'words': words
        }
        
        json_file = self.output_dir / "self_validated_65536.json"
        with open(json_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\nSaved wordlists:")
        print(f"  - {txt_file}")
        print(f"  - {json_file}")


def main():
    """Run the self-validated wordlist generation."""
    generator = SelfValidatedGenerator(batch_size=1000)
    
    try:
        # Generate wordlist
        words = generator.generate_wordlist()
        
        # Save results
        generator.save_wordlist(words)
        
        # Show samples
        print(f"\nSample words from final list:")
        print(f"  First 20: {words[:20]}")
        print(f"  Last 20: {words[-20:]}")
        
        # Clean up state file
        if generator.state_file.exists():
            generator.state_file.unlink()
        
    except KeyboardInterrupt:
        print("\n\nInterrupted! State saved for resumption.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()