# Blind Keyboard Master - keyboard learning app accessible for visually impaired people
# Copyright (C) 2026 Louay Cherif
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import random
import csv
import os
import time

# sentences for week 6 challenge (sentence mode)
sentences_en = [
    "The bell rang softly before the first class began.",
    "She closed the window and listened to the rain.",
    "My brother found a blue pencil under the desk.",
    "We walked home because the bus was late again.",
    "The small cat jumped onto the warm sofa.",
    "Please write your name clearly at the top.",
    "He opened the book and turned the page slowly.",
    "The garden smelled fresh after the evening shower.",
    "Two birds were singing near the old tree.",
    "She carried a bottle of water to the table.",
    "The teacher asked a simple question about history.",
    "I forgot my keys inside the quiet room.",
    "Tomorrow we will visit the museum after lunch.",
    "The river looked silver in the early morning light.",
    "A soft voice came from the hallway outside.",
    "He fixed the broken chair with careful hands.",
    "The children laughed when the balloon floated away.",
    "We should leave now if we want to arrive early.",
    "The shop was crowded, but the line moved quickly.",
    "Her notebook was full of neat and tidy notes.",
    "The wind pushed the leaves across the road.",
    "Every student must bring a pen and a ruler.",
    "The screen went dark when the power failed.",
    "She baked bread that smelled amazing in the oven.",
    "His shoes were muddy after the long walk.",
    "The clock above the door showed half past six.",
    "We learned a new word during the lesson.",
    "The artist painted a yellow sky above the hills.",
    "Do not forget to lock the front gate.",
    "A gentle smile made the room feel warmer.",
    "The laptop battery lasted longer than expected.",
    "He watered the plants before sunrise today.",
    "The package arrived with a note inside.",
    "She spoke quietly so no one would wake the baby.",
    "The coffee was too hot to drink at first.",
    "We crossed the bridge and saw the boats below.",
    "The music stopped when the singer laughed.",
    "Please keep your voice low in the library.",
    "The old train moved slowly through the station.",
    "She wore a red scarf and a gray coat.",
    "He practiced typing every afternoon after school.",
    "The stars appeared one by one in the sky.",
    "We sat near the fire and told stories.",
    "The new app is easier to use than before.",
    "An orange cat slept beside the curtain.",
    "They built a small shelf for the kitchen.",
    "The homework was shorter than yesterday's assignment.",
    "She found the answer after thinking for a while.",
    "The road was empty except for one bicycle.",
    "Please turn off the light before you leave.",
    "He ran faster than anyone in the class.",
    "The soup tasted better with a little pepper.",
    "We heard thunder, then the room became silent.",
    "Her phone buzzed twice and then stopped.",
    "The window reflected the bright sunset outside.",
    "The market sold fruit, bread, and fresh cheese.",
    "She smiled because the news was finally good.",
    "The map showed a path through the forest.",
    "Do you want tea, coffee, or water?",
    "He wrote a long sentence without making a mistake.",
    "The cat stared at the fish in the bowl.",
    "We waited patiently until the doors opened.",
    "The lesson ended before the final bell rang.",
    "She put the letters into a small envelope.",
    "The camera captured the mountains perfectly.",
    "He remembered the password after three tries.",
    "The dog barked when it heard the truck.",
    "We need more time to finish this work.",
    "The book on the table belongs to Sara.",
    "She packed a jacket because the air felt cold.",
    "The candle flickered when the door opened.",
    "He washed his hands before dinner started.",
    "The keys were on the shelf all along.",
    "We should check the weather before traveling.",
    "The singer's last note echoed through the hall.",
    "She found a tiny coin in her pocket.",
    "The computer froze, so I restarted it.",
    "The soup, the bread, and the tea were ready.",
    "He answered the phone with a calm voice.",
    "We wrote the date and the title neatly.",
    "The path was narrow, but it was safe.",
    "She folded the paper into a perfect square.",
    "The alarm woke everyone before dawn.",
    "Please pass me the salt and the spoon.",
    "He studied hard and passed the exam.",
    "The river behind the house was very quiet.",
    "She paused to think before speaking again.",
    "The baker decorated the cake with fruit.",
    "We heard a knock just after midnight.",
    "The child drew a house with four windows.",
    "He carried the boxes up the stairs slowly.",
    "The flowers near the fence were bright pink.",
    "She used a flashlight to find the note.",
    "We can finish this project by Friday.",
    "The old clock still works very well.",
    "He cleaned the desk and organized the files.",
    "The storm passed, leaving the air fresh.",
    "Please remember to save your work often.",
    "The teacher wrote the answer on the board.",
    "She looked surprised when the doorbell rang.",
    "The cup slid off the table and broke.",
    "We counted the coins one by one.",
    "He answered with confidence and a clear voice.",
    "The road turned left near the old school.",
    "She waited outside until the rain stopped.",
    "The final paragraph was easy to understand."
]
sentences_fr = [
    "La cloche a sonné doucement avant le début du cours.",
    "Elle a fermé la fenêtre et a écouté la pluie.",
    "Mon frère a trouvé un crayon bleu sous le bureau.",
    "Nous sommes rentrés à pied parce que le bus était en retard.",
    "Le petit chat a sauté sur le canapé chaud.",
    "Veuillez écrire votre nom clairement en haut de la page.",
    "Il a ouvert le livre et a tourné la page lentement.",
    "Le jardin sentait bon après la pluie du soir.",
    "Deux oiseaux chantaient près du vieil arbre.",
    "Elle a porté une bouteille d'eau jusqu'à la table.",
    "Le professeur a posé une question simple sur l'histoire.",
    "J'ai oublié mes clés dans la pièce silencieuse.",
    "Demain nous irons au musée après le déjeuner.",
    "La rivière paraissait argentée dans la lumière du matin.",
    "Une voix douce venait du couloir dehors.",
    "Il a réparé la chaise cassée avec soin.",
    "Les enfants ont ri quand le ballon est parti.",
    "Nous devons partir maintenant si nous voulons arriver tôt.",
    "La boutique était pleine, mais la file avançait vite.",
    "Son cahier était rempli de notes propres et nettes.",
    "Le vent poussait les feuilles sur la route.",
    "Chaque élève doit apporter un stylo et une règle.",
    "L'écran est devenu noir quand le courant a coupé.",
    "Elle a préparé du pain qui sentait très bon au four.",
    "Ses chaussures étaient pleines de boue après la longue marche.",
    "L'horloge au dessus de la porte indiquait six heures trente.",
    "Nous avons appris un nouveau mot pendant la leçon.",
    "L'artiste a peint un ciel jaune au dessus des collines.",
    "N'oubliez pas de verrouiller le portail avant de partir.",
    "Un sourire doux a rendu la pièce plus chaleureuse.",
    "La batterie de l'ordinateur a duré plus longtemps que prévu.",
    "Il a arrosé les plantes avant le lever du soleil.",
    "Le colis est arrivé avec une note à l'intérieur.",
    "Elle a parlé doucement pour ne pas réveiller le bébé.",
    "Le café était trop chaud pour être bu au début.",
    "Nous avons traversé le pont et vu les bateaux en dessous.",
    "La musique s'est arrêtée quand le chanteur a ri.",
    "Veuillez parler doucement dans la salle de lecture.",
    "Le vieux train a avancé lentement dans la gare.",
    "Elle portait une écharpe rouge et un manteau gris.",
    "Il a pratiqué la frappe chaque après midi après l'école.",
    "Les étoiles sont apparues une par une dans le ciel.",
    "Nous nous sommes assis près du feu et avons raconté des histoires.",
    "La nouvelle application est plus facile à utiliser qu'avant.",
    "Un chat orange dormait près du rideau.",
    "Ils ont construit une petite étagère pour la cuisine.",
    "Le devoir était plus court que celui d'hier.",
    "Elle a trouvé la réponse après avoir réfléchi un moment.",
    "La route était vide sauf pour un vélo.",
    "Veuillez éteindre la lumière avant de partir.",
    "Il a couru plus vite que tout le monde dans la classe.",
    "La soupe était meilleure avec un peu de poivre.",
    "Nous avons entendu le tonnerre, puis la pièce est devenue silencieuse.",
    "Son téléphone a vibré deux fois puis s'est arrêté.",
    "La fenêtre reflétait le beau coucher du soleil dehors.",
    "Le marché vendait des fruits, du pain et du fromage frais.",
    "Elle a souri parce que la nouvelle était enfin bonne.",
    "La carte montrait un chemin à travers la campagne.",
    "Voulez vous du thé, du café ou de l'eau ?",
    "Il a écrit une longue phrase sans faire d'erreur.",
    "Le chat regardait les poissons dans le bol.",
    "Nous avons attendu patiemment jusqu'à l'ouverture des portes.",
    "Le cours s'est terminé avant la sonnerie finale.",
    "Elle a mis les lettres dans une petite enveloppe.",
    "L'appareil photo a capturé les montagnes parfaitement.",
    "Il a retrouvé le mot de passe après trois essais.",
    "Le chien a aboyé quand il a entendu le camion.",
    "Nous avons besoin de plus de temps pour finir ce travail.",
    "Le livre sur la table appartient à Sara.",
    "Elle a pris une veste parce que l'air semblait froid.",
    "La bougie a vacillé quand la porte s'est ouverte.",
    "Il s'est lavé les mains avant le repas.",
    "Les clés étaient sur l'étagère depuis le début.",
    "Nous devrions vérifier la météo avant de voyager.",
    "La dernière note du chanteur a résonné dans la salle.",
    "Elle a trouvé une petite pièce dans sa poche.",
    "L'ordinateur a bloqué, alors je l'ai redémarré.",
    "La soupe, le pain et le thé étaient prêts.",
    "Il a répondu au téléphone avec une voix calme.",
    "Nous avons écrit la date et le titre proprement.",
    "Le chemin était étroit, mais il restait facile.",
    "Elle a plié le papier en un carré parfait.",
    "L'alarme a réveillé tout le monde avant l'aube.",
    "Veuillez me passer le sel et la cuillère.",
    "Il a étudié sérieusement et a réussi l'examen.",
    "La rivière derrière la maison était très calme.",
    "Elle s'est arrêtée pour réfléchir avant de parler encore.",
    "Le boulanger a décoré le gâteau avec des fruits.",
    "Nous avons entendu frapper juste après minuit.",
    "L'enfant a dessiné une maison avec quatre fenêtres.",
    "Il a porté les boîtes dans les escaliers lentement.",
    "Les fleurs près de la clôture étaient d'un rose vif.",
    "Elle a utilisé une lampe de poche pour trouver la note.",
    "Nous pouvons terminer ce projet avant vendredi.",
    "La vieille horloge fonctionne encore très bien.",
    "Il a nettoyé le bureau et rangé les dossiers.",
    "La tempête est passée et l'air est devenu frais.",
    "Veuillez penser à enregistrer votre travail souvent.",
    "Le professeur a écrit la réponse au tableau.",
    "Le dernier paragraphe était facile à comprendre."
]

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
# words for week 4 (will be used in word phase of week challenge)
w4words = [
    "ami", "chat", "loup", "pain", "vent", "robe", "neuf", "jour", "main", "lion",
    "fleur", "table", "porte", "chien", "plage",

    "livre", "pomme", "soleil", "orange", "beurre", "maison", "papier", "vendre", "danser", "cheval",
    "bateau", "village", "musique", "fenetre", "pouvoir",

    "banane", "jardin", "tomate", "fromage", "travail", "montage", "voiture", "cuisine", "famille", "poisson",
    "lapins", "bougie", "valises", "nuages", "pirates",

    "ordinateur", "parfumee", "vacances", "chocolat", "papillon"
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

# words for week 5 (empty for now, will be populated later)
w5words = [
    "Bonjour!", "Salut!", "Merci!", "Pardon?", "Ça va?",
    "Très bien!", "École.", "Fenêtre!", "Garçon.", "Français!",
    "Clé?", "Étoile!", "Lumière.", "Forêt!", "Mystère?",
    "Équipe!", "Téléphone.", "Énergie!", "Éléphant.", "Crème!",
    "À bientôt!", "Déjà vu.", "Voilà!", "Où est-il?", "Être.",
    "Naïf!", "Façade.", "Leçon!", "Hôpital.", "Île.",
    "Noël!", "Maïs.", "Poème!", "Cœur.", "Sœur!",
    "Clavier!", "Rapide?", "Précision!", "Attention!", "Danger!",
    "Combo!", "Victoire!", "Défaite?", "Alerte!", "Mission!",
    "Ultime!", "Puissance!", "Réaction!", "Focus!", "Vitesse!",
    "Parfait!", "Excellent!", "Incroyable!", "Énorme!", "Majuscule!",
    "Symbole?", "Phrase.", "Question!", "Réponse.", "Mystère!",
    "Très vite!", "À gauche.", "À droite!", "Écran.", "Souris!",
    "Fenêtre?", "Bureau.", "Clé magique!", "Épreuve finale!",
    "Mode ultime!", "Super combo!", "Réflexe!", "Éclair!", "Tempête!",
    "Bonjour.", "Salut?", "Merci.", "Pardon!", "Ça alors!",
    "Très rapide.", "Incroyable?", "Fantastique!", "Magnifique.",
    "Silence...", "Attention.", "Prêt?", "Allez!", "Continue!",
    "Victoire.", "Défaite.", "Énergie.", "Précision.", "Réussite!"
]

# Symbol pronunciation dictionary for screen reader announcements
symbol_pronounciation = {
    ",": "virgule",
    ":": "deux-points",
    "!": "point d'exclamation",
    ".": "point",
    "?": "point d'interrogation",
    '"': "guillemet",
    "é": "e accent aigu",
    "ç": "c cedille",
    "è": "e accent grave",
    "(": "parenthese ouverte",
    "à": "a accent grave",
    ")": "parenthese fermee",
}

# week 5 structure
week5 = {
    "name": "Semaine 5: Majuscules et Symboles",
    "steps": ["QSDFGHJKLM", "AZERTYUIOP", "WXCVBN", "ABCDEFGHIJKLMNOPQRSTUVWXYZ", ",:\\!.?\"éçè(à)"],
    "practice_letters": [
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ",  # Majuscules only
        "abcdefghijklmnopqrstuvwxyz",  # Minuscules only
        ",:\\!.?\"éçè(à)",  # Symbols only
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",  # Mixed case letters
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz,:\\!.?\"éçè(à)",  # All combined
    ],
    "symbols": ",:\\!.?\"éçè(à)",
    "words": w5words,
    "learning_flow": [
        # 10 minutes random timed (1.5 secs each) for all letters across 3 rows
        {"mode": "random_timed", "chars": "qsdfghjklmazertyuiopwxcvbn", "duration": 600, "time_per_char": 1.5},
        
        # Learn capital letters from Q to M (home row)
        {"mode": "learn", "chars": "QSDFGHJKLM"},
        
        # Random for 3 minutes on home row
        {"mode": "random", "chars": "QSDFGHJKLM", "duration": 180},
        
        # Learn capital letters from Q to P (top row)
        {"mode": "learn", "chars": "AZERTYUIOP"},
        
        # Random for 3 minutes on top row
        {"mode": "random", "chars": "AZERTYUIOP", "duration": 180},
        
        # Learn capital letters in bottom row
        {"mode": "learn", "chars": "WXCVBN"},
        
        # Random for 3 minutes on bottom row
        {"mode": "random", "chars": "WXCVBN", "duration": 180},
        
        # 5 minutes random for all majuscules
        {"mode": "random", "chars": "QSDFGHJKLMAZERTYUIOPWXCVBN", "duration": 300},
        
        # Learn the punctuation symbols
        {"mode": "learn", "chars": ",:\\!.?\"éçè(à)"},
        
        # 5 minutes random on symbols
        {"mode": "random", "chars": ",:\\!.?\"éçè(à)", "duration": 300},
        
        # Final 100-count random mixing majuscules and symbols
        {"mode": "random", "chars": "QSDFGHJKLMAZERTYUIOPWXCVBN,:\\!.?\"éçè(à)", "count": 100},
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
        self.total_appearance_count = 0  # Cumulative, never resets - for phase advancement
        self.recent_results = []  # Track last 20 results: True (correct), False (error/timeout)
        self.correct_count = 0
        self.error_count = 0
        self.timeout_count = 0
        self.adaptation_phase_started = False
    
    def add_result(self, status):
        """Add result to recent tracking."""
        self.recent_results.append(status)
        
        # Increment cumulative counter (never resets)
        self.total_appearance_count += 1
        
        # Count types
        if status == "correct":
            self.correct_count += 1
        elif status == "error":
            self.error_count += 1
        elif status == "timeout":
            self.timeout_count += 1
        
        self.appearance_count += 1
        # Increment cumulative counter (never resets)
        # Note: this attribute set in LetterStatus.__init__ in parent Week4Logic
        
        # Keep only last 20
        if len(self.recent_results) > 20:
            self.recent_results.pop(0)
    
    def update_time(self):
        if len(self.recent_results) < 20:
            return
        timeout_rate = self.timeout_count / len(self.recent_results)
        if timeout_rate < 0.1:
            self.last_time = self.time
            self.time = max(1.0, self.time - 0.33)    

    def reset_counters(self):
        """Reset counters after 20 appearances."""
        self.appearance_count = 0
        self.recent_results = []
        self.correct_count = 0
        self.error_count = 0
        self.timeout_count = 0
        # NOTE: total_appearance_count never resets - used for phase advancement tracking
    
    def update_status(self):
        if len(self.recent_results) < 20:
            return False
        if self.time > 1.33:
            return False
        error_rate = self.error_count / len(self.recent_results)
        if error_rate > 0.10:
            return False
        timeout_rate = self.timeout_count / len(self.recent_results)
        if timeout_rate > 0.1:
            return False
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
        self.words = w4words.copy()  # Words for word phase
        
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
            {"mode": "PAUSE", "duration": 60, "name": "PAUSE - 1 minute break"},
            {"mode": "COUPLE", "duration": 180, "name": "Phase 3: COUPLE"},
            {"mode": "STANDARD", "duration": 600, "name": "Phase 4: STANDARD"},
            {"mode": "WORDS", "duration": None, "count": 50, "name": "Phase 5: WORDS"},
            {"mode": "PAUSE", "duration": 60, "name": "PAUSE - 1 minute break"},
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
    
    def log_data(self, target, phase_mode, status, offered_time):
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
                # Round offered_time to 2 decimal places
                rounded_time = round(offered_time, 2)
                writer.writerow([phase_mode, target, status, rounded_time])
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
        if self.current_phase_idx == 1:
            self.adaptation_timer_start = time.time()
            self.adaptation_phase_started = True
    
    def generate_target(self):
        """Generate next target based on current mode."""
        phase = self.get_current_phase()
        if not phase:
            return None
        
        mode = phase["mode"]
        
        # STANDARD (Phases 0, 3, 5): Random letters - exclude mastered letters starting from phase 3
        if mode == "STANDARD":
            # In early phases (0), show all letters; in later phases (3, 5), exclude mastered
            if self.current_phase_idx >= 3:
                # Exclude mastered letters in later STANDARD phases
                available = [l for l, s in self.letters_pool.items() if s.status != "mastered"]
            else:
                # Phase 0: show all letters
                available = list(self.letters_pool.keys())
            
            if available:
                self.target = random.choice(available)
                return self.target
            return None
        
        # STANDARD_ADAPTIVE (Phase 1): Letters disappear after 20 appearances
        elif mode == "STANDARD_ADAPTIVE":
            # Only show letters that haven't had 20+ appearances yet (cumulative counter)
            available = [l for l, s in self.letters_pool.items() if s.total_appearance_count < 20]
            
            if not available:
                # All letters have 20 appearances, move to next phase
                self.advance_phase()
                return self.generate_target()
            
            # Weight by time (letters with longer time need more practice)
            weights = [self.letters_pool[l].time for l in available]
            self.target = random.choices(available, weights=weights, k=1)[0]
            return self.target
        
        # STANDARD_MASTERY (Phase 7): Letters stay until mastered
        elif mode == "STANDARD_MASTERY":
            unmastered = [l for l, s in self.letters_pool.items() if s.status == "unmastered"]
            
            if not unmastered:
                # All letters mastered
                self.advance_phase()
                return self.generate_target()
            
            # Weight by time (longer time = needs more practice)
            weights = [self.letters_pool[l].time for l in unmastered]
            self.target = random.choices(unmastered, weights=weights, k=1)[0]
            return self.target
        
        # PAUSE mode: No target during pause
        elif mode == "PAUSE":
            return None
        
        # COUPLE (Phases 2, 6): Two-letter combinations (practice, no mastery)
        elif mode == "COUPLE":
            # Use all letters, not just unmastered (COUPLE is practice)
            all_letters = list(self.letters_pool.keys())
            if len(all_letters) < 2:
                self.advance_phase()
                return self.generate_target()
            
            couple = random.sample(all_letters, 2)
            self.target = "".join(couple)
            self.current_couple = couple
            return self.target
        
        # WORDS (Phase 4): Real word typing (practice, no mastery)
        elif mode == "WORDS":
            if not self.words:
                self.advance_phase()
                return self.generate_target()
            
            self.target = self.words.pop(0).upper()
            return self.target
        
        # SPEED (Phase 8): All letters at fixed 1.0s time
        elif mode == "SPEED":
            # ALL letters, regardless of mastery
            all_letters = list(self.letters_pool.keys())
            if all_letters:
                self.target = random.choice(all_letters)
                return self.target
            return None
        
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
        newly_mastered = []
        
        # Log to CSV with distinct status
        self.log_data(target, mode, status_type, offered_time)
        self.last_attempt_status = status_type
        
        # COUPLE and WORDS modes: Track results but DO NOT update mastery status
        # They are practice modes only
        if mode in ["COUPLE", "WORDS"]:
            if mode == "COUPLE":
                for letter in self.current_couple:
                    if letter in self.letters_pool:
                        if status_type == "correct":
                            self.letters_pool[letter].add_result("correct")
                        else:
                            self.letters_pool[letter].add_result(status_type)
            elif mode == "WORDS":
                for letter in target:
                    if letter in self.letters_pool:
                        if status_type == "correct":
                            self.letters_pool[letter].add_result("correct")
                        else:
                            self.letters_pool[letter].add_result(status_type)
            # NO mastery check for COUPLE/WORDS - they never update mastery status
            self.newly_mastered_letters = []
        else:
            # STANDARD modes (0, 1, 5, 7) and SPEED: Track and check for mastery
            if status_type == "correct":
                if target in self.letters_pool:
                    self.letters_pool[target].add_result("correct")
                    
                    # Check for mastery if 20 appearances reached
                    status_obj = self.letters_pool[target]
                    if len(status_obj.recent_results) >= 20:
                        status_obj.update_time()
                        if status_obj.update_status():  # Returns True if just became mastered
                            newly_mastered.append(target)
                        status_obj.reset_counters()
            else:
                # error/timeout: record negative result
                if target in self.letters_pool:
                    self.letters_pool[target].add_result(status_type)
                    
                    # Check for mastery if 20 appearances reached
                    status_obj = self.letters_pool[target]
                    if len(status_obj.recent_results) >= 20:
                        status_obj.update_time()
                        if status_obj.update_status():
                            newly_mastered.append(target)
                        status_obj.reset_counters()
            
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
        
        mode = phase.get("mode")
        
        # PAUSE mode: Advance after duration
        if mode == "PAUSE":
            if self.mode_start_time:
                elapsed = time.time() - self.mode_start_time
                if elapsed >= phase["duration"]:
                    return True
        
        # STANDARD_ADAPTIVE (Phase 1): Advance when all letters have appeared 20+ times (cumulative)
        if mode == "STANDARD_ADAPTIVE":
            all_appeared_20 = all(s.total_appearance_count >= 20 for s in self.letters_pool.values())
            if all_appeared_20:
                return True
        
        # STANDARD_MASTERY (Phase 7): Advance when all letters mastered
        if mode == "STANDARD_MASTERY":
            if self.is_all_mastered():
                return True
        
        # Duration-based phases (STANDARD, COUPLE, SPEED)
        if phase.get("duration"):
            if self.mode_start_time:
                elapsed = time.time() - self.mode_start_time
                if elapsed >= phase["duration"]:
                    return True
        
        # Count-based phases (WORDS, COUPLE)
        if phase.get("count"):
            if self.phase_item_count >= phase["count"]:
                return True
        
        return False
    
    def is_session_complete(self):
        """Check if mastery session is complete (all phases done)."""
        return self.current_phase_idx >= len(self.phases)
    
    def get_announcement_text(self, char):
        """Get the text to announce for a character, handling majuscules and symbols."""
        # Symbol: always return French pronunciation name
        if char in symbol_pronounciation:
            return symbol_pronounciation[char]

        # For Week 4: differentiate upper vs lower case letters
        if char.isalpha():
            if char.isupper():
                return f"{char.lower()} majuscule"   # e.g. "a majuscule" for 'A'
            else:
                return char                           # e.g. "a" for 'a'

        # Fallback
        return char

    def get_word_pronunciation(self):
        """Get the pronunciation details for current word target (WORDS mode)."""
        target = self.target
        # Use get_announcement_text for each character to properly handle majuscules
        spelling_parts = [self.get_announcement_text(char) for char in target]
        spelling = ", ".join(spelling_parts)
        
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
