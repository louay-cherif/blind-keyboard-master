import random
import csv
import os
import time

# words for week 1
w1words = [
    "sad", "dad", "fad", "lad", "jam", "ham", "mad", "had", "gas", "lag",
    "dash", "lash", "gash", "hash", "slam", "sham", "jash", "fash", "galm", "hald",
    "jams", "lags", "gads", "dams", "shad", "shag", "slag", "flag", "glad", "slam",
    "flam", "sham", "jamd", "gald", "halm", "jald", "dhal", "gash", "lash", "shaj",
    "fadh", "dalf", "jalf", "salg", "gafl", "dlag", "jash", "shaf", "lash", "dham"
]
# words for week 2
w2words = [
    "AIDE", "AIMER", "AILE", "AIR", "AMI", "ARRET", "ARME", "ART", "ASTRE",
"AUTEUR", "AUTRE", "DAME", "DATE", "DIRE", "DROIT", "DURER", "FAIRE",
"FAIT", "FIER", "FILE", "FILLE", "FORME", "GARE", "GELER", "GUIDE",
"HAIE", "HEURE", "HIER", "JETER", "JOLIE", "JOUR", "LAIT", "LAME",
"LIRE", "LISTE", "LOGER", "LOI", "MAIRE", "MARE", "MARI", "MATIERE",
"MODE", "MOTEUR", "MUR", "PAR", "PAREIL", "PART", "PARLER", "PAYER",
"PEUR", "PLUIE", "POIRE", "POIDS", "PORTE", "POSER", "QUAI", "QUALITE",
"RARE", "RIRE", "ROLE", "ROUE", "SALE", "SAUT", "SEUIL", "SOIF",
"SOIR", "SOL", "SORT", "SUITE", "TAIRE", "TARD", "TASSE", "TERRE",
"TITRE", "TOILE", "TOUR", "TRAIT", "UTILISE", "USAGE", "ZESTE",
"ADIEU", "AFRIQUE", "AGIR", "AIL", "AIME", "AIRE", "ALORS", "AMOUR",
"APRES", "ARRIERE", "ATOUT", "AURORE", "AUTEL", "AZUR", "DEGAT",
"DELAI", "DETOUR", "DIEU", "DIGUE", "DIODE", "DROLE",
"DUEL", "EAU", "EFFET", "EGAL", "ELFE", "ELLE", "EMEU",
"EMILE", "EMPIRE", "EPAULE", "EPEE", "EPOQUE", "EQUIPE", "ERREUR",
"ESSAI", "ESSAIM", "ETAGE", "ETOILE", "ETUDE", "EURO", "FALAISE",
"FAUTEUIL", "FEE", "FETE", "FEU", "FEUTRE", "FIGURE",
"FILET", "FLEUR", "FOLIE", "FOUET", "FRAISE", "FRERE", "FROMAGE",
"FUMEE", "GAGE", "GALA", "GARAGE", "GAZ", "GELULE", "GESTE",
"GLOIRE", "GOMME", "GORGE", "GOUJAT", "GOURDE", "GRILLE", "GUERRE",
"HARDE", "HAUT", "HORDE", "HORS", "HOTEL", "HUILE",
"HUMEUR", "JAUGE", "JAZZ", "JOLI", "JOUET", "JUGE", "JULES",
"JURISTE", "LARGE", "LARME", "LAURIE", "LEGUME", "LEUR", "LIER",
"LITRE", "LOURD", "LUIRE", "LUMIERE", "MADAME", "MAGIE", "MALADE",
"MARQUE", "MARTEAU", "MERE", "MESURE", "METAL",
"MIEL", "MILIEU", "MOI", "MOIS", "MOT", "MOULE", "MOURIR",
"MUSIQUE", "PARADIS", "PARURE", "PATE", "PATIO", "PAUSE", "PELOTE",
"PERE", "PERLE", "PETIT", "PHARE", "PIED", "PIERRE", "PILOTE",
"PLAIRE", "PLEUR", "PLUME", "POLE", "POMPE", "POSTE", "POT", "POTE",
"POUDRE", "POULE", "POUR", "POURSUITE", "POUSSE", "POUTRE", "PRES",
"PRET", "PRIERE", "PRISE", "PROIE", "PUIS", "PUR", "PURE", "QUART",
"QUATRE", "QUE", "QUEL", "QUITTER", "QUOI", "RADIO", "RAIE", 
"RATE", "REALITE", "REDUIRE", "REFUS", "REGARD", "REGLE", 
"REJET", "RELAIS", "REPAS", "REPERE", "REPOS", "RESEAU",
"RESTE", "RETARD", "REUSSIR", "RIGOLE", "RIME", "RISQUE", "RITE",
"RODE", "ROI", "ROSE", "ROUGE", "ROULE", "RUE",
"RUMEUR", "SAGE", "SAISIR", "SALADE", "SALIR", "SALUT",
"SEL", "SERIE", "SERRE", "SEUL", "SIEGE",
"SIESTE", "SITOT", "SITUER", "SOEUR", "SOLEIL", "SOLIDE", "SOLO",
"SORTIE", "SOUFFLE", "SOUHAIT", "SOUPLE", "SOURIRE",
"SOUS", "SOUTE", "SUD", "SUER", "SUJET", "SUPER", "SUR",
"SURETE", "SURGI", "SURPRISE", "TARTE", "TAS",
"TASSER", "TAUDIS", "TAUPE", "TEMPLE", "TEST",
"TETE", "TISSU", "TOILETTE", "TOIT", "TOURTE", "TOUT", 
"TRAITE", "TRAME", "TRAPEZE", "TRAQUE", 
"TREFLE", "TREIZE", "TREMPER", "TRES", "TRESOR", "TRETEAU", "TRI",
"TRIER", "TRIO", "TRISTE", "TROIS", "TROMPE", "TROP", "TROU",
"TROUPE", "TUER", "TUILERIE", "TUMEUR", "TUTELAIRE", "TUTTI", "TYPE",
"TYPIQUE", "USE", "USURE", "UTILE", "UTOPIE", "YAOURT", "YOGOURT"
]
# words for week 3
w3words = [
    "chat","chien","maison","table","porte","fenetre","route","ville","arbre","plage",
"soleil","lune","etoile","ciel","terre","mer","vent","pluie","neige","orage",
"feu","eau","pain","fromage","lait","sucre","sel","poivre","riz","pate",
"fruit","pomme","poire","peche","banane","orange","citron","fraise","raisin","melon",
"legume","carotte","tomate","salade","oignon","ail","haricot","pomme","terreau","radis",
"ecole","classe","prof","eleve","livre","stylo","cahier","tableau","cours","devoir",
"bureau","chaise","ordinateur","clavier","souris","ecran","fenetre","porte","mur","plafond",
"jardin","fleur","herbe","arbre","branche","racine","feuille","fruitier","rose","tulipe",
"animal","cheval","vache","mouton","chevre","poule","canard","lapin","singe","tigre",
"lion","ours","loup","renard","cerf","biche","poisson","requin","baleine","dauphin",
"voiture","train","avion","velo","moto","bus","route","gare","aeroport","station",
"hotel","chambre","lit","drap","oreiller","couverture","serviette","douche","bain","savon",
"travail","metier","emploi","salaire","bureau","chef","collegue","reunion","projet","rapport",
"temps","heure","minute","seconde","jour","semaine","mois","annee","matin","soir",
"amour","ami","famille","pere","mere","frere","soeur","enfant","voisin","relation",
"musique","chanson","danse","film","theatre","livre","histoire","conte","roman","poeme"
]
# week 1 structure
week1 = {
                "name": "Semaine 1: Ligne de Base",
                "steps": ["QSDF", "GHJ", "KLM", "QSDFGHJKLM"],
                "practice_letters": ["QSDFGHJKLM"],
                "words": w1words,
                "learning_flow": [
                    {"mode": "learn", "chars": "QSDF"},
                    {"mode": "random", "chars": "QSDF", "duration": 300},
                    {"mode": "learn", "chars": "GHJ"},
                    {"mode": "random", "chars": "GHJ", "count": 40},
                    {"mode": "random", "chars": "QSDFGHJ", "duration": 300},
                    {"mode": "learn", "chars": "KLM"},
                    {"mode": "random", "chars": "KLM", "count": 40},
                    {"mode": "random", "chars": "QSDFGHJKLM", "count": 250},
                ],
            }
# week 2 structure
week2 = {
                "name": "Semaine 2: Ligne Supérieure",
                        "steps": ["AZER", "TYU", "IOP", "AZERTYUIOP"],
                "letters": "AZERTYUIOP",
                "practice_letters": ["AZERTYUIOP", "AZERTYUIOPQSDFGHJKLM"],
                "words": w2words,
                "learning_flow": [
                    {"mode": "random", "chars": "QSDFGHJKLM", "duration": 300},
                    {"mode": "learn", "chars": "AZER"},
                    {"mode": "random", "chars": "AZER", "count": 20},
                    {"mode": "learn", "chars": "TYU"},
                    {"mode": "random", "chars": "TYU", "count": 20},
                    {"mode": "learn", "chars": "IOP"},
                    {"mode": "random", "chars": "IOP", "count": 20},
                    {"mode": "random", "chars": "AZERTYUIOP", "count": 40},
                    {"mode": "random", "chars": "AZERTYUIOPQSDFGHJKLM", "count": 60},
                ],
            }
# week 3 structure
week3 = {
                "name": "Semaine 3: Ligne Inférieure",
                "steps": ["WXC", "VBN", "WXCVBN"],
                "letters": "WXCVBN",
                "practice_letters": ["WXCVBN", "AZERTYUIOPQSDFGHJKLMWXCVBN"],
                "words": w3words,
                "learning_flow": [
                    {"mode": "random", "chars": "QSDFGHJKLM", "duration": 300},
                    {"mode": "random", "chars": "AZERTYUIOP", "duration": 300},
                    {"mode": "random", "chars": "AZERTYUIOPQSDFGHJKLM", "count": 100},
                    {"mode": "learn", "chars": "WXC"},
                    {"mode": "random", "chars": "WXC", "count": 20},
                    {"mode": "random", "chars": "AZERTYUIOPWXC", "duration": 180},
                    {"mode": "learn", "chars": "VBN"},
                    {"mode": "random", "chars": "VBN", "duration": 120},
                    {"mode": "random", "chars": "WXCVBN", "duration": 180},
                    {"mode": "random", "chars": "AZERTYUIOPQSDFGHJKLMWXCVBN", "duration": 600},
                ],
            }

# week 4 structure
week4 = {
    "name": "Semaine 4: Mixage des Lignes",
    "steps": ["QSDFGHJKLM", "AZERTYUIOP", "WXCVBN", "AZERTYUIOPQSDFGHJKLMWXCVBN"],
    "practice_letters": ["QSDFGHJKLM", "AZERTYUIOP", "WXCVBN", "AZERTYUIOPQSDFGHJKLMWXCVBN"],
    "words": [],
    "learning_flow": [
        {"mode": "random", "chars": "QSDFGHJKLM", "duration": 180},
        {"mode": "random", "chars": "AZERTYUIOP", "duration": 180},
        {"mode": "random", "chars": "WXCVBN", "duration": 180},
        {"mode": "random", "chars": "AZERTYUIOPQSDFGHJKLMWXCVBN", "duration": 300},
    ],
}

# week 5 structure
week5 = {
    "name": "Semaine 5: Majuscules et Symboles",
    "steps": ["ABCDEFGHIJKLMNOPQRSTUVWXYZ", ",;:!?", "./§", "ALL_COMBINED"],
    "practice_letters": ["ABCDEFGHIJKLMNOPQRSTUVWXYZ"],
    "words": [],
    "learning_flow": [
        {"mode": "learn", "chars": "ABCDEFGHIJKLMNOPQRSTUVWXYZ"},
        {"mode": "random", "chars": "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "duration": 300},
    ],
}

# ====== WEEK 4: MASTERY MODE ======

import time


class LetterStatus:
    """Model for tracking individual letter mastery status."""
    
    def __init__(self, letter):
        self.letter = letter
        self.time = 2.0
        self.last_time = 2.0
        self.status = "unmastered"
        self.appearance_count = 0
        self.recent_results = []  # Track last 20 results: True (correct), False (error/timeout)
        self.correct_count = 0
        self.timeout_count = 0
        self.adaptation_phase_started = False
    
    def add_result(self, is_correct):
        """Add result to recent tracking."""
        self.recent_results.append(is_correct)
        if is_correct:
            self.correct_count += 1
        else:
            self.timeout_count += 1
        self.appearance_count += 1
        
        # Keep only last 20
        if len(self.recent_results) > 20:
            self.recent_results.pop(0)
    
    def update_time(self):
        """Update time based on performance."""
        if len(self.recent_results) < 20:
            return
        
        timeout_rate = self.timeout_count / len(self.recent_results) if self.recent_results else 0
        
        if timeout_rate < 0.1:
            self.last_time = self.time
            self.time = max(1.0, self.time - 0.33)
    
    def reset_counters(self):
        """Reset counters after 20 appearances."""
        self.appearance_count = 0
        self.recent_results = []
        self.correct_count = 0
        self.timeout_count = 0
    
    def update_status(self):
        """Mark as mastered if criteria met: time ≤ 1.33s AND error_rate < 15% AND timeout_rate < 10%"""
        if len(self.recent_results) < 20:
            return False
        
        # Criterion 1: Time must be ≤ 1.33s
        if self.time > 1.33:
            return False
        
        # Criterion 2: Error rate < 15% (at most 2-3 errors in 20 attempts)
        error_count = len(self.recent_results) - sum(self.recent_results)
        error_rate = error_count / len(self.recent_results)
        if error_rate >= 0.15:
            return False
        
        # Criterion 3: Timeout rate < 10% (at most 1-2 timeouts in 20 attempts)
        timeout_rate = self.timeout_count / len(self.recent_results)
        if timeout_rate >= 0.1:
            return False
        
        # All criteria met
        self.status = "mastered"
        return True



class Week4Logic:
    """Mastery Mode System for Week 4 - inherits from AppBackend pattern."""
    
    def __init__(self, parent_logic):
        """Initialize Week4, inheriting from parent logic."""
        # Inherit essential properties from parent
        self.user_name = parent_logic.user_name
        self.speaker = parent_logic.speaker
        self.base_dir = parent_logic.base_dir
        self.data_dir = parent_logic.data_dir
        self.weeks = parent_logic.weeks
        
        self.current_week_idx = 3  # Week 4 is index 3
        self.mode = ""
        self.target = ""
        self.score = 0
        
        # Letter mastery tracking
        all_letters = "AZERTYUIOPQSDFGHJKLMWXCVBN"
        self.letters_pool = {letter: LetterStatus(letter) for letter in all_letters}
        
        # Mode tracking
        self.current_mode = None
        self.mode_start_time = None
        self.current_couple = []
        self.last_attempt_status = None  # Track last attempt: "correct", "error", "timeout"
        self.newly_mastered_letters = []  # Track letters that just became mastered
        
        # Phase tracking
        self.phases = [
            {"mode": "STANDARD", "duration": 300, "name": "Phase 1: STANDARD"},
            {"mode": "STANDARD_ADAPTIVE", "duration": None, "name": "Phase 2: STANDARD Adaptive"},
            {"mode": "COUPLE", "duration": 180, "name": "Phase 3: COUPLE"},
            {"mode": "STANDARD", "duration": 600, "name": "Phase 4: STANDARD"},
            {"mode": "WORDS", "duration": None, "count": 50, "name": "Phase 5: WORDS"},
            {"mode": "STANDARD", "duration": 300, "name": "Phase 6: STANDARD"},
            {"mode": "COUPLE", "duration": None, "count": 20, "name": "Phase 7: COUPLE"},
            {"mode": "STANDARD_MASTERY", "duration": None, "name": "Phase 8: STANDARD (Mastery)"},
            {"mode": "SPEED", "duration": 180, "name": "Phase 9: SPEED"},
        ]
        self.current_phase_idx = 0
        self.phase_item_count = 0
        self.adaptation_timer_start = None
        self.adaptation_phase_started = False
    
    def get_clean_username(self):
        """Return cleaned username."""
        return "".join(c for c in self.user_name if c.isalnum() or c in (' ', '_')).rstrip()
    
    def get_user_csv_path(self):
        """Get Week 4 specific CSV path."""
        clean_name = self.get_clean_username()
        user_dir = os.path.join(self.data_dir, clean_name)
        os.makedirs(user_dir, exist_ok=True)
        return os.path.join(user_dir, f"{clean_name}_Week_4.csv")
    
    def log_data(self, target, mode, status, offered_time):
        """Override CSV logging for Week 4 format."""
        if not self.user_name:
            return
        
        file_path = self.get_user_csv_path()
        file_exists = os.path.isfile(file_path)
        
        try:
            with open(file_path, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["mode", "target", "status", "offered_time"])
                writer.writerow([mode, target, status, offered_time])
        except:
            pass
    
    def get_current_phase(self):
        """Get current phase config."""
        if self.current_phase_idx < len(self.phases):
            return self.phases[self.current_phase_idx]
        return None
    
    def advance_phase(self):
        """Move to next phase."""
        self.current_phase_idx += 1
        self.phase_item_count = 0
        self.mode_start_time = time.time()
        if self.current_phase_idx == 2:
            self.adaptation_timer_start = time.time()
            self.adaptation_phase_started = True
    
    def generate_target(self):
        """Generate next target based on current mode."""
        phase = self.get_current_phase()
        if not phase:
            return None
        
        mode = phase["mode"]
        
        if mode == "STANDARD" or mode == "STANDARD_ADAPTIVE" or mode == "STANDARD_MASTERY":
            unmastered = [l for l, s in self.letters_pool.items() if s.status == "unmastered"]
            if not unmastered:
                self.advance_phase()
                return self.generate_target()
            
            if mode == "STANDARD_ADAPTIVE":
                # Weight by performance (higher time = needs more practice)
                weights = [self.letters_pool[l].time for l in unmastered]
                target = random.choices(unmastered, weights=weights, k=1)[0]
            else:
                target = random.choice(unmastered)
            
            self.target = target
            return target
        
        elif mode == "COUPLE":
            unmastered = [l for l, s in self.letters_pool.items() if s.status == "unmastered"]
            if len(unmastered) < 2:
                self.advance_phase()
                return self.generate_target()
            
            couple = random.sample(unmastered, 2)
            self.target = "".join(couple)
            self.current_couple = couple
            return self.target
        
        elif mode == "WORDS":
            words = w3words
            if not words:
                self.advance_phase()
                return self.generate_target()
            
            self.target = random.choice(words).upper()
            return self.target
        
        elif mode == "SPEED":
            unmastered = [l for l, s in self.letters_pool.items() if s.status == "unmastered"]
            if not unmastered:
                self.advance_phase()
                return self.generate_target()
            
            self.target = random.choice(unmastered)
            return self.target
        
        return None
    
    def get_target_display_time(self):
        """Calculate display time for target in seconds."""
        if self.target is None:
            return 2.0
        
        phase = self.get_current_phase()
        if not phase:
            return 2.0
        
        mode = phase["mode"]
        
        if mode == "SPEED":
            return 1.0
        
        if mode == "COUPLE":
            couple_time = sum(self.letters_pool[l].time for l in self.current_couple)
            return couple_time
        
        if mode == "WORDS":
            word_time = sum(self.letters_pool[l].time for l in self.target)
            return word_time
        
        # STANDARD modes
        if self.target in self.letters_pool:
            return self.letters_pool[self.target].time
        
        return 2.0
    
    def check_input(self, user_input, target):
        """Validate user input against target. Returns True if correct."""
        is_correct = user_input.upper() == target.upper()
        return is_correct
    
    def record_attempt(self, target, status_type, offered_time):
        """
        Record attempt and update letter status.
        status_type: "correct", "error", or "timeout"
        Returns: list of newly mastered letters (if any)
        """
        phase = self.get_current_phase()
        if not phase:
            return []
        
        mode = phase["mode"]
        is_correct = (status_type == "correct")
        newly_mastered = []
        
        # Log to CSV with distinct status
        self.log_data(target, mode, status_type, offered_time)
        self.last_attempt_status = status_type
        
        # Update letter status only if correct; any error/timeout moves to next
        if is_correct:
            if mode == "COUPLE":
                for letter in self.current_couple:
                    if letter in self.letters_pool:
                        self.letters_pool[letter].add_result(True)
            elif mode == "WORDS":
                for letter in target:
                    if letter in self.letters_pool:
                        self.letters_pool[letter].add_result(True)
            elif target in self.letters_pool:
                self.letters_pool[target].add_result(True)
            
            # Check for mastery after correct attempt
            for letter, status_obj in self.letters_pool.items():
                if status_obj.status == "unmastered":
                    if len(status_obj.recent_results) >= 20:
                        status_obj.update_time()
                        if status_obj.update_status():  # Returns True if just became mastered
                            newly_mastered.append(letter)
                        status_obj.reset_counters()
        else:
            # Error or timeout: record negative result
            if mode == "COUPLE":
                for letter in self.current_couple:
                    if letter in self.letters_pool:
                        self.letters_pool[letter].add_result(False)
            elif mode == "WORDS":
                for letter in target:
                    if letter in self.letters_pool:
                        self.letters_pool[letter].add_result(False)
            elif target in self.letters_pool:
                self.letters_pool[target].add_result(False)
        
        # Store newly mastered letters for UI display
        self.newly_mastered_letters = newly_mastered
        
        # Always move to next round
        self.phase_item_count += 1
        
        return newly_mastered
    
    def is_all_mastered(self):
        """Check if all letters are mastered."""
        return all(s.status == "mastered" for s in self.letters_pool.values())
    
    def should_advance_phase(self):
        """Check if current phase should be advanced."""
        phase = self.get_current_phase()
        if not phase:
            return False
        
        if phase.get("duration"):
            if self.mode_start_time:
                elapsed = time.time() - self.mode_start_time
                if elapsed >= phase["duration"]:
                    return True
        
        if phase.get("count"):
            if self.phase_item_count >= phase["count"]:
                return True
        
        return False
    
    def is_session_complete(self):
        """Check if mastery session is complete (all phases done or all mastered)."""
        return self.current_phase_idx >= len(self.phases) or self.is_all_mastered()
    
    def get_word_pronunciation(self):
        """Get the pronunciation details for current word target (WORDS mode)."""
        target = self.target
        spelling = ", ".join(list(target))
        
        spelling_delay = len(target) * 150 + 400
        word_audio_delay = len(target) * 100 + 300
        total_delay = spelling_delay + word_audio_delay
        wait_time = len(target) * 2000
        
        return {
            "spelling": spelling,
            "spelling_delay": spelling_delay,
            "word_audio_delay": word_audio_delay,
            "total_delay": total_delay,
            "wait_time": wait_time
        }
    
    def reset(self):
        """Reset all state for next week or session."""
        self.current_phase_idx = 0
        self.phase_item_count = 0
        self.target = ""
        self.score = 0
        self.adaptation_phase_started = False
        self.last_attempt_status = None
