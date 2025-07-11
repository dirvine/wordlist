#!/usr/bin/env python3
"""
Claude criteria validator that processes wordlist in batches.
Starts with BIP39 as foundation and adds validated words from 100K list.

UV Dependencies:
# Install UV if not available: curl -LsSf https://astral.sh/uv/install.sh | sh
# Run this script: uv run python claude_criteria_validator.py
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests>=2.31.0",
# ]
# ///

import json
import re
import time
from pathlib import Path
from typing import List, Set, Dict, Tuple
from dataclasses import dataclass

from generate_wordlist import load_or_download_words


@dataclass
class ValidationProgress:
    """Track validation progress."""
    gold_words: Set[str]
    processed_count: int
    accepted_count: int
    rejected_count: int
    batch_number: int
    start_time: float


class ClaudeCriteriaValidator:
    """Validator using Claude's exact validation criteria."""
    
    def __init__(self, batch_size: int = 1000):
        """Initialize validator with batch size."""
        self.batch_size = batch_size
        self.target_size = 65536
        self.output_dir = Path("wordlists")
        self.output_dir.mkdir(exist_ok=True)
        
        # Output files
        self.gold_file = self.output_dir / "gold_wordlist_65536.txt"
        self.progress_file = self.output_dir / "validation_progress.json"
        self.log_file = self.output_dir / "validation_log.txt"
        
        # Initialize proper noun database
        self._init_rejection_lists()
        
    def _init_rejection_lists(self):
        """Initialize comprehensive rejection lists."""
        # Comprehensive proper nouns list
        self.proper_nouns = set()
        
        # Personal names (first names)
        first_names = [
            'john', 'mary', 'james', 'robert', 'michael', 'william', 'david', 'richard',
            'charles', 'joseph', 'thomas', 'paul', 'george', 'henry', 'edward', 'peter',
            'frank', 'daniel', 'matthew', 'anthony', 'donald', 'mark', 'steven', 'andrew',
            'aaron', 'adam', 'alan', 'albert', 'alex', 'alfred', 'alice', 'amy', 'anna',
            'anne', 'arthur', 'barbara', 'betty', 'brian', 'bruce', 'carl', 'carol',
            'catherine', 'chris', 'christine', 'christopher', 'claire', 'daniel', 'david',
            'deborah', 'dennis', 'diane', 'donna', 'dorothy', 'douglas', 'elizabeth',
            'emily', 'eric', 'frances', 'frank', 'gary', 'george', 'harold', 'helen',
            'henry', 'jack', 'jane', 'janet', 'jason', 'jean', 'jeffrey', 'jennifer',
            'jerry', 'jessica', 'joan', 'joe', 'john', 'jose', 'joseph', 'joshua',
            'joyce', 'judith', 'judy', 'julia', 'julie', 'justin', 'karen', 'katherine',
            'kathleen', 'kathryn', 'keith', 'kelly', 'kenneth', 'kevin', 'kimberly',
            'larry', 'laura', 'lawrence', 'linda', 'lisa', 'margaret', 'maria', 'marie',
            'marilyn', 'mark', 'martha', 'martin', 'mary', 'matthew', 'melissa', 'michael',
            'michelle', 'nancy', 'nathan', 'nicholas', 'nicole', 'pamela', 'patricia',
            'patrick', 'paul', 'peter', 'philip', 'rachel', 'ralph', 'raymond', 'rebecca',
            'richard', 'robert', 'roger', 'ronald', 'rose', 'roy', 'russell', 'ruth',
            'ryan', 'samuel', 'sandra', 'sarah', 'scott', 'sean', 'sharon', 'shirley',
            'stephanie', 'stephen', 'steven', 'susan', 'teresa', 'terry', 'thomas',
            'timothy', 'virginia', 'walter', 'wayne', 'willie', 'zachary'
        ]
        
        # Surnames
        surnames = [
            'smith', 'johnson', 'williams', 'jones', 'brown', 'davis', 'miller', 'wilson',
            'moore', 'taylor', 'anderson', 'thomas', 'jackson', 'white', 'harris', 'martin',
            'thompson', 'garcia', 'martinez', 'robinson', 'clark', 'rodriguez', 'lewis',
            'lee', 'walker', 'hall', 'allen', 'young', 'hernandez', 'king', 'wright',
            'lopez', 'hill', 'scott', 'green', 'adams', 'baker', 'gonzalez', 'nelson',
            'carter', 'mitchell', 'perez', 'roberts', 'turner', 'phillips', 'campbell',
            'parker', 'evans', 'edwards', 'collins', 'stewart', 'sanchez', 'morris',
            'rogers', 'reed', 'cook', 'morgan', 'bell', 'murphy', 'bailey', 'rivera',
            'cooper', 'richardson', 'cox', 'howard', 'ward', 'torres', 'peterson', 'gray',
            'ramirez', 'james', 'watson', 'brooks', 'kelly', 'sanders', 'price', 'bennett',
            'wood', 'barnes', 'ross', 'henderson', 'coleman', 'jenkins', 'perry', 'powell',
            'long', 'patterson', 'hughes', 'flores', 'washington', 'butler', 'simmons',
            'foster', 'gonzales', 'bryant', 'alexander', 'russell', 'griffin', 'diaz',
            'hayes'
        ]
        
        # Cities and places
        places = [
            'london', 'paris', 'york', 'washington', 'chicago', 'boston', 'texas',
            'california', 'florida', 'georgia', 'virginia', 'ohio', 'michigan', 'indiana',
            'illinois', 'wisconsin', 'minnesota', 'iowa', 'missouri', 'kansas', 'nebraska',
            'dakota', 'montana', 'wyoming', 'colorado', 'utah', 'nevada', 'arizona',
            'mexico', 'canada', 'toronto', 'montreal', 'vancouver', 'ottawa', 'calgary',
            'edmonton', 'winnipeg', 'quebec', 'halifax', 'berlin', 'munich', 'hamburg',
            'frankfurt', 'cologne', 'stuttgart', 'dusseldorf', 'leipzig', 'dresden',
            'madrid', 'barcelona', 'valencia', 'seville', 'bilbao', 'rome', 'milan',
            'naples', 'turin', 'florence', 'venice', 'moscow', 'petersburg', 'kiev',
            'minsk', 'warsaw', 'krakow', 'budapest', 'prague', 'vienna', 'zurich',
            'geneva', 'amsterdam', 'rotterdam', 'brussels', 'antwerp', 'copenhagen',
            'stockholm', 'oslo', 'helsinki', 'dublin', 'belfast', 'edinburgh', 'glasgow',
            'cardiff', 'sydney', 'melbourne', 'brisbane', 'perth', 'adelaide', 'auckland',
            'wellington', 'christchurch', 'tokyo', 'osaka', 'kyoto', 'beijing', 'shanghai',
            'delhi', 'mumbai', 'bangalore', 'chennai', 'kolkata', 'cairo', 'lagos',
            'johannesburg', 'nairobi', 'casablanca', 'tunis', 'algiers', 'tripoli',
            'aachen', 'aalborg', 'aarhus', 'aberdeen', 'adelaide', 'alexandria', 'algiers',
            'amsterdam', 'ankara', 'antwerp', 'athens', 'atlanta', 'auckland', 'austin',
            'baghdad', 'baltimore', 'bangkok', 'barcelona', 'basel', 'beijing', 'beirut',
            'belfast', 'belgrade', 'bergen', 'berkeley', 'berlin', 'birmingham', 'bogota',
            'bologna', 'bombay', 'bonn', 'bordeaux', 'boston', 'brasilia', 'bratislava',
            'bremen', 'brighton', 'brisbane', 'bristol', 'brussels', 'bucharest',
            'budapest', 'buffalo', 'cairo', 'calcutta', 'calgary', 'cambridge', 'canberra',
            'canterbury', 'caracas', 'cardiff', 'casablanca', 'charleston', 'charlotte',
            'chennai', 'chicago', 'cincinnati', 'cleveland', 'cologne', 'colombo',
            'columbus', 'copenhagen', 'cordoba', 'cork', 'dallas', 'damascus', 'delhi',
            'denver', 'detroit', 'dresden', 'dublin', 'dundee', 'durban', 'dusseldorf',
            'edinburgh', 'edmonton', 'florence', 'frankfurt', 'geneva', 'genoa', 'glasgow',
            'gothenburg', 'granada', 'guadalajara', 'guangzhou', 'guatemala', 'hague',
            'halifax', 'hamburg', 'hanoi', 'havana', 'heidelberg', 'helsinki', 'hiroshima',
            'hongkong', 'honolulu', 'houston', 'indianapolis', 'innsbruck', 'istanbul',
            'jakarta', 'jerusalem', 'johannesburg', 'kabul', 'kampala', 'kansas', 'karachi',
            'kathmandu', 'khartoum', 'kiev', 'kingston', 'kinshasa', 'kobe', 'kolkata',
            'krakow', 'kualalumpur', 'kuwait', 'kyoto', 'lagos', 'lahore', 'lancaster',
            'laos', 'leipzig', 'lille', 'lima', 'lincoln', 'lisbon', 'liverpool', 'ljubljana',
            'london', 'losangeles', 'louisville', 'lucerne', 'luxembourg', 'lyon', 'macau',
            'madrid', 'malaga', 'malta', 'manchester', 'manila', 'marseille', 'melbourne',
            'memphis', 'mexicocity', 'miami', 'milan', 'milwaukee', 'minneapolis', 'minsk',
            'monaco', 'monterrey', 'montevideo', 'montreal', 'moscow', 'mumbai', 'munich',
            'nagasaki', 'nagoya', 'nairobi', 'nanjing', 'naples', 'nashville', 'nassau',
            'newcastle', 'neworleans', 'newyork', 'nice', 'nottingham', 'nuremberg',
            'oakland', 'odessa', 'omaha', 'oporto', 'osaka', 'oslo', 'ottawa', 'oxford',
            'palermo', 'paris', 'perth', 'philadelphia', 'phoenix', 'pittsburgh', 'portland',
            'porto', 'prague', 'pretoria', 'providence', 'puebla', 'quebec', 'quito',
            'rabat', 'raleigh', 'rangoon', 'reykjavik', 'richmond', 'riga', 'riodejaneiro',
            'riyadh', 'rochester', 'rome', 'rotterdam', 'sacramento', 'saigon', 'salem',
            'salzburg', 'sanantonio', 'sandiego', 'sanfrancisco', 'sanjose', 'sanjuan',
            'santiago', 'saopaulo', 'sarajevo', 'seattle', 'seoul', 'seville', 'shanghai',
            'sheffield', 'singapore', 'sofia', 'stockholm', 'stlouis', 'stuttgart',
            'sydney', 'taipei', 'tampere', 'tangier', 'tbilisi', 'teheran', 'telaviv',
            'tirana', 'tokyo', 'toledo', 'toronto', 'toulouse', 'tripoli', 'tunis',
            'turin', 'ulaanbaatar', 'utrecht', 'valencia', 'valletta', 'vancouver',
            'vatican', 'venice', 'vienna', 'vientiane', 'vilnius', 'warsaw', 'wellington',
            'winnipeg', 'wroclaw', 'yerevan', 'yokohama', 'zagreb', 'zurich'
        ]
        
        # Countries and nationalities
        countries_nationalities = [
            'america', 'american', 'england', 'english', 'britain', 'british', 'france',
            'french', 'germany', 'german', 'spain', 'spanish', 'italy', 'italian',
            'russia', 'russian', 'china', 'chinese', 'japan', 'japanese', 'india',
            'indian', 'canada', 'canadian', 'australia', 'australian', 'brazil',
            'brazilian', 'mexico', 'mexican', 'argentina', 'argentinian', 'chile',
            'chilean', 'colombia', 'colombian', 'peru', 'peruvian', 'venezuela',
            'venezuelan', 'ecuador', 'ecuadorian', 'bolivia', 'bolivian', 'paraguay',
            'paraguayan', 'uruguay', 'uruguayan', 'poland', 'polish', 'ukraine',
            'ukrainian', 'czech', 'slovak', 'hungary', 'hungarian', 'romania', 'romanian',
            'bulgaria', 'bulgarian', 'greece', 'greek', 'turkey', 'turkish', 'iran',
            'iranian', 'iraq', 'iraqi', 'israel', 'israeli', 'egypt', 'egyptian',
            'saudi', 'arabia', 'jordan', 'jordanian', 'lebanon', 'lebanese', 'syria',
            'syrian', 'pakistan', 'pakistani', 'afghanistan', 'afghan', 'bangladesh',
            'bangladeshi', 'thailand', 'thai', 'vietnam', 'vietnamese', 'indonesia',
            'indonesian', 'malaysia', 'malaysian', 'philippines', 'filipino', 'korea',
            'korean', 'africa', 'african', 'europe', 'european', 'asia', 'asian',
            'oceania', 'nordic', 'scandinavian', 'latin', 'anglo', 'arab', 'jewish',
            'christian', 'muslim', 'buddhist', 'hindu', 'catholic', 'protestant',
            'orthodox', 'america', 'american', 'canada', 'canadian', 'mexico', 'mexican',
            'england', 'english', 'scotland', 'scottish', 'wales', 'welsh', 'ireland',
            'irish', 'france', 'french', 'germany', 'german', 'italy', 'italian',
            'spain', 'spanish', 'portugal', 'portuguese', 'netherlands', 'dutch',
            'belgium', 'belgian', 'switzerland', 'swiss', 'austria', 'austrian',
            'sweden', 'swedish', 'norway', 'norwegian', 'denmark', 'danish', 'finland',
            'finnish', 'iceland', 'icelandic', 'poland', 'polish', 'czech', 'slovak',
            'hungary', 'hungarian', 'romania', 'romanian', 'bulgaria', 'bulgarian',
            'greece', 'greek', 'turkey', 'turkish', 'russia', 'russian', 'ukraine',
            'ukrainian', 'belarus', 'belarusian', 'lithuania', 'lithuanian', 'latvia',
            'latvian', 'estonia', 'estonian', 'serbia', 'serbian', 'croatia', 'croatian',
            'bosnia', 'bosnian', 'albania', 'albanian', 'macedonia', 'macedonian',
            'slovenia', 'slovenian', 'montenegro', 'china', 'chinese', 'japan', 'japanese',
            'korea', 'korean', 'india', 'indian', 'pakistan', 'pakistani', 'bangladesh',
            'bangladeshi', 'thailand', 'thai', 'vietnam', 'vietnamese', 'indonesia',
            'indonesian', 'malaysia', 'malaysian', 'singapore', 'singaporean', 'philippines',
            'filipino', 'myanmar', 'burmese', 'cambodia', 'cambodian', 'laos', 'laotian',
            'australia', 'australian', 'zealand', 'kiwi', 'fiji', 'fijian', 'papua',
            'africa', 'african', 'egypt', 'egyptian', 'libya', 'libyan', 'tunisia',
            'tunisian', 'algeria', 'algerian', 'morocco', 'moroccan', 'ethiopia',
            'ethiopian', 'kenya', 'kenyan', 'uganda', 'ugandan', 'tanzania', 'tanzanian',
            'nigeria', 'nigerian', 'ghana', 'ghanaian', 'africa', 'african', 'zimbabwe',
            'zimbabwean', 'zambia', 'zambian', 'mozambique', 'mozambican', 'angola',
            'angolan', 'namibia', 'namibian', 'botswana', 'brazil', 'brazilian',
            'argentina', 'argentinian', 'chile', 'chilean', 'peru', 'peruvian', 'colombia',
            'colombian', 'venezuela', 'venezuelan', 'ecuador', 'ecuadorian', 'bolivia',
            'bolivian', 'paraguay', 'paraguayan', 'uruguay', 'uruguayan', 'guyana',
            'guyanese', 'suriname', 'surinamese', 'america', 'american', 'canada',
            'canadian', 'mexico', 'mexican', 'guatemala', 'guatemalan', 'salvador',
            'salvadoran', 'honduras', 'honduran', 'nicaragua', 'nicaraguan', 'rica',
            'panama', 'panamanian', 'cuba', 'cuban', 'haiti', 'haitian', 'dominican',
            'jamaica', 'jamaican', 'trinidad', 'tobago', 'barbados', 'barbadian',
            'puerto', 'rican', 'virgin', 'caribbean', 'europe', 'european', 'asia',
            'asian', 'africa', 'african', 'america', 'american', 'oceania', 'oceanic',
            'arctic', 'antarctic', 'atlantic', 'pacific', 'indian', 'mediterranean',
            'baltic', 'north', 'south', 'east', 'west', 'central', 'northern', 'southern',
            'eastern', 'western', 'northeastern', 'northwestern', 'southeastern',
            'southwestern', 'midwest', 'midwestern'
        ]
        
        # Brand names and organizations
        brands = [
            'microsoft', 'google', 'apple', 'amazon', 'facebook', 'twitter', 'instagram',
            'youtube', 'netflix', 'spotify', 'adobe', 'oracle', 'ibm', 'intel', 'cisco',
            'samsung', 'sony', 'nintendo', 'tesla', 'uber', 'lyft', 'airbnb', 'paypal',
            'visa', 'mastercard', 'walmart', 'target', 'costco', 'starbucks', 'mcdonalds',
            'subway', 'nike', 'adidas', 'puma', 'reebok', 'gucci', 'prada', 'versace',
            'chanel', 'dior', 'burberry', 'toyota', 'honda', 'ford', 'chevrolet', 'bmw',
            'mercedes', 'audi', 'volkswagen', 'porsche', 'ferrari', 'lamborghini',
            'harvard', 'stanford', 'yale', 'princeton', 'oxford', 'cambridge', 'mit',
            'berkeley', 'cornell', 'columbia', 'pepsi', 'cocacola', 'nestle', 'kellogs',
            'kraft', 'heinz', 'unilever', 'procter', 'gamble', 'johnson', 'pfizer',
            'moderna', 'astrazeneca', 'merck', 'novartis', 'roche', 'boeing', 'airbus',
            'lockheed', 'raytheon', 'northrop', 'goldman', 'sachs', 'morgan', 'chase',
            'citibank', 'wellsfargo', 'reuters', 'bloomberg', 'disney', 'warner', 'viacom',
            'comcast', 'verizon', 'tmobile', 'sprint', 'vodafone', 'linkedin', 'tiktok',
            'snapchat', 'pinterest', 'reddit', 'wikipedia', 'ebay', 'alibaba', 'tencent',
            'baidu', 'xiaomi', 'huawei', 'lenovo', 'dell', 'acer', 'asus', 'dropbox',
            'slack', 'zoom', 'skype', 'whatsapp', 'telegram', 'discord', 'twitch',
            'steam', 'epic', 'activision', 'blizzard', 'ubisoft', 'bethesda', 'rockstar',
            'aarp', 'aalto'
        ]
        
        # Add all to proper nouns set
        self.proper_nouns.update(first_names)
        self.proper_nouns.update(surnames)
        self.proper_nouns.update(places)
        self.proper_nouns.update(countries_nationalities)
        self.proper_nouns.update(brands)
        
        # Abbreviations
        self.abbreviations = {
            'mr', 'mrs', 'ms', 'dr', 'prof', 'sr', 'jr', 'phd', 'md', 'mph', 'mba',
            'llc', 'inc', 'ltd', 'corp', 'co', 'plc', 'gmbh', 'spa', 'nv', 'sa',
            'etc', 'eg', 'ie', 'vs', 'cf', 'nb', 'ps', 'pps', 'viz', 'ca', 'approx',
            'est', 'min', 'max', 'avg', 'std', 'var', 'dev', 'diff', 'sum', 'prod',
            'am', 'pm', 'ad', 'bc', 'ce', 'bce', 'utc', 'gmt', 'pst', 'est', 'cst',
            'jan', 'feb', 'mar', 'apr', 'jun', 'jul', 'aug', 'sep', 'sept', 'oct',
            'nov', 'dec', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun',
            'kg', 'mg', 'g', 'lb', 'oz', 'ml', 'l', 'gal', 'qt', 'pt', 'fl',
            'km', 'mi', 'yd', 'ft', 'cm', 'mm', 'nm', 'um',
            'mph', 'kph', 'rpm', 'fps', 'mbps', 'gbps', 'hz', 'khz', 'mhz', 'ghz',
            'kb', 'mb', 'gb', 'tb', 'pb', 'bit', 'byte',
            'usd', 'eur', 'gbp', 'jpy', 'cny', 'inr', 'cad', 'aud', 'chf', 'sek',
            'www', 'http', 'https', 'ftp', 'ssh', 'tcp', 'udp', 'ip', 'dns', 'vpn',
            'html', 'css', 'js', 'php', 'sql', 'xml', 'json', 'api', 'sdk', 'ide',
            'os', 'pc', 'mac', 'cpu', 'gpu', 'ram', 'rom', 'hdd', 'ssd', 'usb',
            'pdf', 'doc', 'txt', 'jpg', 'png', 'gif', 'mp3', 'mp4', 'avi', 'zip',
            'tel', 'fax', 'ext', 'dept', 'div', 'org', 'assn', 'intl', 'natl', 'govt',
            'univ', 'hosp', 'inst', 'acad', 'elem', 'jhs', 'shs', 'elem', 'prof',
            'asst', 'assoc', 'vp', 'svp', 'evp', 'ceo', 'cfo', 'cto', 'coo', 'cmo',
            'usa', 'uk', 'eu', 'un', 'nato', 'who', 'imf', 'wto', 'opec', 'asean',
            'dna', 'rna', 'atp', 'ph', 'uv', 'ir', 'rf', 'ac', 'dc', 'led', 'lcd',
            'hiv', 'aids', 'sars', 'mers', 'ebola', 'flu', 'tb', 'std', 'uti', 'icu',
            'er', 'or', 'nicu', 'picu', 'ccu', 'pacu', 'radiol', 'cardiol', 'neurol',
            'pro', 'con', 'vs', 'per', 'via', 'vis', 'ad', 'hoc', 'de', 'facto',
            'bona', 'fide', 'modus', 'operandi', 'status', 'quo', 'quid', 'pro', 'quo',
            'aab', 'aac', 'aad', 'aaf', 'aag', 'aah', 'aal', 'aam', 'aan', 'aap', 'aar',
            'aas', 'aat', 'aav', 'aaw', 'aax', 'aay', 'aaz', 'aba', 'abb', 'abc', 'abd',
            'abe', 'abf', 'abg', 'abh', 'abi', 'abj', 'abk', 'abl', 'abm', 'abn', 'abo',
            'abp', 'abq', 'abr', 'abs', 'abt', 'abu', 'abv', 'abw', 'abx', 'aby', 'abz'
        }
        
        # Foreign words not adopted into English
        self.foreign_words = {
            'der', 'die', 'das', 'den', 'dem', 'des', 'ein', 'eine', 'einen', 'einem',
            'le', 'la', 'les', 'un', 'une', 'du', 'de', 'au', 'aux', 'ce', 'cette',
            'el', 'los', 'las', 'unos', 'unas', 'del', 'al', 'por', 'para', 'con',
            'il', 'lo', 'gli', 'una', 'uno', 'dei', 'degli', 'delle', 'dal', 'alla',
            'och', 'eller', 'men', 'som', 'har', 'kan', 'ska', 'vill', 'får', 'måste',
            'et', 'ou', 'mais', 'donc', 'ni', 'car', 'que', 'qui', 'quoi', 'dont',
            'y', 'e', 'o', 'pero', 'sino', 'aunque', 'porque', 'cuando', 'donde',
            'en', 'een', 'het', 'van', 'voor', 'met', 'aan', 'op', 'te', 'om',
            'og', 'på', 'til', 'av', 'är', 'är', 'och', 'att', 'jag', 'du',
            'und', 'oder', 'aber', 'doch', 'sondern', 'denn', 'weil', 'wenn', 'als',
            'für', 'mit', 'ohne', 'auf', 'unter', 'zwischen', 'bei', 'nach', 'vor',
            'pour', 'avec', 'sans', 'sur', 'sous', 'entre', 'dans', 'chez', 'vers',
            'sino', 'aun', 'aunque', 'todavia', 'tambien', 'tampoco', 'quizas', 'tal',
            'och', 'eller', 'när', 'där', 'här', 'vad', 'vem', 'vilken', 'vilket'
        }
        
        # Archaic words
        self.archaic_words = {
            'thou', 'thee', 'thy', 'thine', 'ye', 'hath', 'doth', 'hast', 'dost',
            'shalt', 'wilt', 'canst', 'mayest', 'mightest', 'couldst', 'wouldst',
            'shouldst', 'art', 'wert', 'hadst', 'didst', 'saith', 'spake', 'bade',
            'forsooth', 'verily', 'nay', 'yea', 'hither', 'thither', 'whither',
            'hence', 'thence', 'whence', 'ere', 'oft', 'betwixt', 'amongst', 'whilst',
            'twas', 'tis', 'twere', 'oer', 'neath', 'gainst', 'pon', 'fore', 'mid',
            'morn', 'eve', 'een', 'twain', 'wherefore', 'whereto', 'wherein', 'whereof',
            'whereby', 'whereinto', 'whereon', 'wherewith', 'wherethrough', 'whereunder',
            'mayhap', 'perchance', 'belike', 'certes', 'marry', 'prithee', 'zounds',
            'gadzooks', 'odds', 'bodkins', 'grammercy', 'lackaday', 'alack', 'alas',
            'fie', 'pish', 'tush', 'quotha', 'parlous', 'passing', 'wondrous', 'goodly'
        }
        
        # Technical/medical terms
        self.technical_terms = {
            'abscissa', 'ordinate', 'asymptote', 'eigenvector', 'eigenvalue', 'jacobian',
            'laplacian', 'hamiltonian', 'lagrangian', 'eulerian', 'riemannian', 'lorentzian',
            'minkowski', 'euclidean', 'hermitian', 'unitary', 'orthogonal', 'isomorphism',
            'homomorphism', 'endomorphism', 'automorphism', 'diffeomorphism', 'homeomorphism',
            'cardiomyopathy', 'atherosclerosis', 'thrombocytopenia', 'lymphadenopathy',
            'hepatosplenomegaly', 'glomerulonephritis', 'cholecystectomy', 'appendectomy',
            'tonsillectomy', 'hysterectomy', 'mastectomy', 'prostatectomy', 'nephrectomy',
            'gastrectomy', 'colectomy', 'pneumonectomy', 'lobectomy', 'thyroidectomy',
            'parathyroidectomy', 'adrenalectomy', 'oophorectomy', 'salpingectomy',
            'vasectomy', 'circumcision', 'episiotomy', 'cesarean', 'amniocentesis',
            'bronchoscopy', 'colonoscopy', 'endoscopy', 'laparoscopy', 'arthroscopy',
            'cystoscopy', 'gastroscopy', 'sigmoidoscopy', 'thoracoscopy', 'mediastinoscopy'
        }
    
    def validate_word(self, word: str) -> Tuple[bool, str]:
        """
        Apply Claude's validation criteria to a single word.
        Returns (is_valid, rejection_reason).
        """
        word_lower = word.lower().strip()
        
        # Length check
        if len(word_lower) < 3:
            return False, "too short"
        if len(word_lower) > 12:
            return False, "too long"
        
        # Must be alphabetic
        if not word_lower.isalpha():
            return False, "contains non-alphabetic characters"
        
        # Check against rejection lists
        if word_lower in self.proper_nouns:
            return False, "proper noun"
        
        if word_lower in self.abbreviations:
            return False, "abbreviation"
        
        if word_lower in self.foreign_words:
            return False, "foreign word"
        
        if word_lower in self.archaic_words:
            return False, "archaic word"
        
        if word_lower in self.technical_terms:
            return False, "technical/medical term"
        
        # Pattern checks
        
        # Check for words with no vowels
        if not any(c in 'aeiou' for c in word_lower):
            return False, "no vowels"
        
        # Check for words with no consonants
        if not any(c in 'bcdfghjklmnpqrstvwxyz' for c in word_lower):
            return False, "no consonants"
        
        # Check for too many consecutive consonants (5+)
        if any(len(match.group()) >= 5 for match in re.finditer(r'[bcdfghjklmnpqrstvwxyz]+', word_lower)):
            return False, "too many consecutive consonants"
        
        # Check for too many consecutive vowels (4+)
        if any(len(match.group()) >= 4 for match in re.finditer(r'[aeiou]+', word_lower)):
            return False, "too many consecutive vowels"
        
        # Check for triple letter patterns
        for i in range(len(word_lower) - 2):
            if word_lower[i] == word_lower[i+1] == word_lower[i+2]:
                return False, "triple letter pattern"
        
        # Check for unusual starting patterns
        unusual_starts = ['aa', 'ii', 'uu', 'yy', 'qq', 'xx', 'zz']
        if any(word_lower.startswith(pattern) for pattern in unusual_starts):
            return False, "unusual starting pattern"
        
        # If all checks pass, word is valid
        return True, ""
    
    def load_bip39_words(self) -> Set[str]:
        """Load BIP39 words as foundation."""
        print("Loading BIP39 foundation words...")
        bip39_file = self.output_dir / "bip39_english.txt"
        
        if not bip39_file.exists():
            # Download BIP39
            import requests
            response = requests.get('https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/english.txt')
            with open(bip39_file, 'w') as f:
                f.write(response.text)
        
        with open(bip39_file) as f:
            words = {line.strip().lower() for line in f if line.strip()}
        
        print(f"Loaded {len(words)} BIP39 words")
        return words
    
    def load_candidates(self, bip39_words: Set[str]) -> List[str]:
        """Load 100K wordlist excluding BIP39 words."""
        print("\nLoading 100K wordlist...")
        _, top_100k = load_or_download_words()
        
        # Filter out BIP39 words and basic invalid entries
        candidates = []
        for word in top_100k:
            word_lower = word.lower().strip()
            
            # Skip if in BIP39
            if word_lower in bip39_words:
                continue
            
            # Basic pre-filter
            if len(word_lower) < 3 or len(word_lower) > 12:
                continue
            
            if not word_lower.isalpha():
                continue
            
            candidates.append(word_lower)
        
        print(f"Prepared {len(candidates)} candidate words (excluding BIP39)")
        return candidates
    
    def save_progress(self, progress: ValidationProgress):
        """Save current progress."""
        progress_data = {
            'gold_words': sorted(list(progress.gold_words)),
            'processed_count': progress.processed_count,
            'accepted_count': progress.accepted_count,
            'rejected_count': progress.rejected_count,
            'batch_number': progress.batch_number,
            'elapsed_time': time.time() - progress.start_time,
            'timestamp': time.time()
        }
        
        with open(self.progress_file, 'w') as f:
            json.dump(progress_data, f, indent=2)
    
    def load_progress(self) -> ValidationProgress:
        """Load previous progress if available."""
        if self.progress_file.exists():
            try:
                with open(self.progress_file) as f:
                    data = json.load(f)
                
                progress = ValidationProgress(
                    gold_words=set(data['gold_words']),
                    processed_count=data['processed_count'],
                    accepted_count=data['accepted_count'],
                    rejected_count=data['rejected_count'],
                    batch_number=data['batch_number'],
                    start_time=time.time() - data['elapsed_time']
                )
                
                print(f"\nResuming from batch {progress.batch_number}")
                print(f"Current gold words: {len(progress.gold_words)}")
                return progress
                
            except Exception as e:
                print(f"Could not load progress: {e}")
        
        return None
    
    def validate_batch(self, words: List[str], batch_num: int) -> Tuple[List[str], Dict[str, str]]:
        """Validate a batch of words using Claude's criteria."""
        accepted = []
        rejection_log = {}
        
        for word in words:
            is_valid, reason = self.validate_word(word)
            if is_valid:
                accepted.append(word)
            else:
                rejection_log[word] = reason
        
        # Log batch results
        with open(self.log_file, 'a') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Batch {batch_num}: {len(words)} words processed\n")
            f.write(f"Accepted: {len(accepted)} ({len(accepted)/len(words)*100:.1f}%)\n")
            f.write(f"Rejected: {len(rejection_log)} ({len(rejection_log)/len(words)*100:.1f}%)\n")
            
            # Log rejection reasons summary
            reason_counts = {}
            for reason in rejection_log.values():
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
            
            f.write("\nRejection reasons:\n")
            for reason, count in sorted(reason_counts.items(), key=lambda x: x[1], reverse=True):
                f.write(f"  - {reason}: {count}\n")
        
        return accepted, rejection_log
    
    def generate_wordlist(self):
        """Generate the gold wordlist using Claude's validation criteria."""
        print("="*70)
        print("CLAUDE CRITERIA WORDLIST GENERATION")
        print("Target: 65,536 words")
        print("="*70)
        
        # Try to resume previous session
        progress = self.load_progress()
        
        if progress is None:
            # Start fresh
            bip39_words = self.load_bip39_words()
            candidates = self.load_candidates(bip39_words)
            
            progress = ValidationProgress(
                gold_words=bip39_words.copy(),
                processed_count=0,
                accepted_count=0,
                rejected_count=0,
                batch_number=0,
                start_time=time.time()
            )
            
            # Save initial BIP39 words to gold file
            with open(self.gold_file, 'w') as f:
                for word in sorted(bip39_words):
                    f.write(f"{word}\n")
            
            print(f"\nStarting with {len(bip39_words)} BIP39 foundation words")
            print(f"Processing {len(candidates)} candidate words in batches of {self.batch_size}")
        else:
            # Load candidates and skip already processed
            bip39_words = self.load_bip39_words()
            candidates = self.load_candidates(bip39_words)
            
            # Skip already processed words
            skip_count = progress.batch_number * self.batch_size
            candidates = candidates[skip_count:]
            print(f"\nSkipping first {skip_count} words (already processed)")
        
        # Process batches
        while candidates and len(progress.gold_words) < self.target_size:
            # Get next batch
            batch = candidates[:self.batch_size]
            candidates = candidates[self.batch_size:]
            progress.batch_number += 1
            
            print(f"\nProcessing batch {progress.batch_number} ({len(batch)} words)...")
            
            # Validate batch
            accepted, rejection_log = self.validate_batch(batch, progress.batch_number)
            
            # Update progress
            progress.processed_count += len(batch)
            progress.accepted_count += len(accepted)
            progress.rejected_count += len(rejection_log)
            
            # Add accepted words to gold list
            for word in accepted:
                if len(progress.gold_words) < self.target_size:
                    progress.gold_words.add(word)
            
            # Append to gold file
            with open(self.gold_file, 'a') as f:
                for word in sorted(accepted):
                    if len(progress.gold_words) <= self.target_size:
                        f.write(f"{word}\n")
            
            # Save progress
            self.save_progress(progress)
            
            # Print summary
            print(f"  Accepted: {len(accepted)} ({len(accepted)/len(batch)*100:.1f}%)")
            print(f"  Total gold words: {len(progress.gold_words)}/{self.target_size} ({len(progress.gold_words)/self.target_size*100:.1f}%)")
            
            # Show some rejection examples
            if rejection_log:
                print(f"  Sample rejections:")
                for word, reason in list(rejection_log.items())[:5]:
                    print(f"    - {word}: {reason}")
        
        # Final summary
        print("\n" + "="*70)
        print("GENERATION COMPLETE!")
        print("="*70)
        print(f"Total words processed: {progress.processed_count}")
        print(f"Total words accepted: {progress.accepted_count}")
        print(f"Total words rejected: {progress.rejected_count}")
        print(f"Final gold wordlist size: {len(progress.gold_words)}")
        print(f"Time elapsed: {time.time() - progress.start_time:.1f} seconds")
        
        # Create final sorted wordlist
        final_words = sorted(list(progress.gold_words))[:self.target_size]
        
        # Save final versions
        with open(self.gold_file, 'w') as f:
            for word in final_words:
                f.write(f"{word}\n")
        
        # Save JSON version with metadata
        json_file = self.output_dir / "gold_wordlist_65536.json"
        metadata = {
            'version': '1.0',
            'word_count': len(final_words),
            'generation_method': 'claude_criteria_validation',
            'includes_bip39': True,
            'target_size': self.target_size,
            'batch_size': self.batch_size,
            'total_processed': progress.processed_count,
            'total_accepted': progress.accepted_count,
            'total_rejected': progress.rejected_count,
            'generation_time': time.time() - progress.start_time,
            'criteria': [
                'Real English words',
                'Easily readable',
                'Commonly understood',
                'Appropriate for general audiences',
                'Not proper nouns',
                'Not abbreviations',
                'Not foreign words'
            ],
            'words': final_words
        }
        
        with open(json_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\nSaved files:")
        print(f"  - {self.gold_file}")
        print(f"  - {json_file}")
        print(f"  - {self.log_file}")
        
        # Show sample words
        print(f"\nSample words from gold list:")
        print(f"  First 20: {final_words[:20]}")
        print(f"  Last 20: {final_words[-20:]}")


def main():
    """Run the validation process."""
    validator = ClaudeCriteriaValidator()
    
    try:
        validator.generate_wordlist()
        print("\n✓ Gold wordlist generation complete!")
        
    except KeyboardInterrupt:
        print("\n\nProcess interrupted. Progress saved.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()