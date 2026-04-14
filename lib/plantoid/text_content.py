def get_text_content(lang):

    opening_lines = {
        "fr-FR": 
            [
            "Je suis honoré d'être ici parmis vous.. comment puis-je t'être utile?",
            "Est-ce que tu veux me tenir companie? Racconte moi une histoire s'il te plait.",
            "Je suis un peu timite, mais j'aimerai bien que tu m'explique un peu ce qui ce passe ici..",
            "J'ai hâte de faire ta connaissance. Dis-moi quelque chose de personnel."
            ],
        "en-EN":
            [
            "So tell me, what brings you here?",
            "Would you like to have a little chat with me?",
            "I'm a litte bit busy right now, but happy to entertain you for a bit",
            "I'm eager to get to know you! Tell me something about you.."
            ]
    }

    closing_lines = {
        "fr-FR":
            [
            "Ça suffit, cette conversation me fatigue. Mon énergie est en train de s'épuiser.",
            "Cette conversation m'intéresse, mais je suis une Plantoïde très occupée..",
            "J'adorerai continuer cette conversation, mais ma présence est requise par d'autres formes de vie synthétique sur la blockchain..",
            "Merci pour cette conversation. Cela fut un plaisir de faire ta connaissance."
            ],
        "en-EN":
            [
            "That's enough, I must return to the blockchain world now. I'm getting low on energy..",
            "You are quite an interesting human, unfortunately, I must go now, I cannot tell you all of my secrets..",
            "I would love to continue this conversation, but my presence is required by other blockchain-based lifeforms..",
            "I'm sorry, I have to go now. I have some transactions to deal with.."
            ]
    }



    word_categories = {
        "en-EN": [
        {
            "category": "BEINGS",
            "items": [
                "Personhood",
                "Oracles",
                "Permaculture nerd",
                "Traditional",
                "Unique",
                "Synapse",
                "Heart beat",
                "Wings",
                "Consciousness",
                "Interbeing",
                "Breath",
                "Dream",
                "Heist",
                "Reclownification",
                "Unpredictable",
                "Health"
            ]
        },
        {
            "category": "RELATIONS",
            "items": [
                "Reciprocity",
                "Bridging",
                "Intersection",
                "Symbiotic",
                "Restoration",
                "Relationship",
                "Massively multidisciplinary",
                "Weaving",
                "Fluidity",
                "Energy",
                "Signs",
                "Symmetry",
                "Biomimicry",
                "Approach",
                "Relationally",
                "Resonance",
                "Oneness",
                "Reciprocity",
                "Equilibrium"
            ]
        },
        {
            "category": "ATTITUDES",
            "items": [
                "Integrity",
                "Wisdom",
                "Potential",
                "Revolution",
                "Hope",
                "Sensing",
                "Iterative",
                "Simplicity",
                "Self-sustaining",
                "Collaborative",
                "Counterculture",
                "Sovereignty",
                "Clarity",
                "Lightness",
                "Excitation",
                "Intentionality",
                "Hyperstition",
                "Patience",
                "Commoning",
                "Communal",
                "Integrative",
                "Radical chilling"
            ]
        },
        {
            "category": "TECHNOLOGY",
            "items": [
                "Protocols",
                "Interoperability",
                "Techne",
                "Solarpunk",
                "Hypercerts",
                "Complexity",
                "Anachronistic",
                "Scale",
                "Pattern",
                "Language",
                "Maternal AI",
                "Pluralverse",
                "Perpetual motion machine",
                "Lunar punk",
                "Cyborg",
                "Useful",
                "Plantoid",
                "Unyielding",
                "Quantum physics"
            ]
        },
        {
            "category": "NATURE",
            "items": [
                "Sustainable",
                "Green",
                "Mycelia",
                "Renewable",
                "Landscape",
                "Ecology",
                "Natural",
                "Unquantifiable",
                "Traditional healing",
                "Planetary health",
                "Cloud",
                "Fractal",
                "Distributive",
                "Mushroom",
                "Biology",
                "Regenessance",
                "Tendrits",
                "Mycelium"
            ]
        }
    ],
        "fr-FR": [
    {
        "category": "BEINGS",
        "items": [
            "Vie synthétique",
            "Oracles",
            "Permaculture",
            "Tradition",
            "Unique",
            "Synapse",
            "Cœur",
            "Ailes",
            "Conscience",
            "Respiration",
            "Rêve",
            "Unpredictable",
            "Santé planétaire"
        ]
    },
    {
        "category": "RELATIONS",
        "items": [
            "Reciprocité",
            "Intersection",
            "Symbiotique",
            "Restoration",
            "Relation",
            "Multidisciplinarité",
            "Fluidité",
            "Energie",
            "Signes",
            "Symmetrie",
            "Biomimicrie",
            "Approache",
            "Relationalité",
            "Resonance",
            "Unicité",
            "Equilibre"
        ]
    },
    {
        "category": "ATTITUDES",
        "items": [
            "Integrité",
            "Sagesse",
            "Potentiel",
            "Revolution",
            "Espoir",
            "Sensibilité",
            "Itérativité",
            "Simplicité",
            "Sustainabilité",
            "Collaboration",
            "Contre-culture",
            "Sovereignté",
            "Clarté",
            "Lumière",
            "Excitation",
            "Intentionalité",
            "Hyperstition",
            "Patience",
            "Communalité",
            "Integration",
        ]
    },
    {
        "category": "TECHNOLOGY",
        "items": [
            "Protocoles",
            "Interoperabilité",
            "Techne",
            "Solarpunk",
            "Complexité",
            "Anachroniste",
            "Pattern",
            "Langage",
            "AI maternelle",
            "Pluriverse",
            "Lunar punk",
            "Cyborg",
            "Plantoïde",
            "Physique quantique"
        ]
    },
    {
        "category": "NATURE",
        "items": [
            "Sustainabilité",
            "Vert",
            "Mycelium",
            "Renouvelable",
            "Paysage",
            "Ecologie",
            "Naturel",
            "Unquantifiable",
            "Traditionnel",
            "Santé planétaire",
            "Nuages",
            "Fractal",
            "Distribué",
            "Champignon",
            "Biologie",
            "Regeneressance",
        ]
    }
]}



    return opening_lines[lang], closing_lines[lang], word_categories[lang]



default_transcript = {
      14: {
          "en-EN": "The future I'm dreaming of is that of a solarpunk utopia where Plantoids have taken over the world.",
          "fr-FR": "Le futur auquel j'aspire est une utopie solarpunk où les Plantoïdes ont envahit la planete.",
      },
      15: {
          "en-EN": "I don't know what the future looks like. Describe a solarpunk utopia where Plantoids have taken over the world.",
          "fr-FR": "Le futur auquel j'aspire est une utopie solarpunk où les Plantoïdes ont envahit la planete.",
      },
      16: {
          "en-EN": "A world where Plants collaborate with Humans and with Machines, in a symbiotic dance of co-creation.",
          "fr-FR": "Un monde où les Plantes collaborent avec les Humains et les Machines, dans une danse symbiotique de co-création.",
      },
  }


def get_default_transcript(plantoid_n, language):

    return default_transcript[plantoid_n][language]


# def get_default_song_transcript(lang):
#     generated_transcript = {
#         "en-EN": "A world where Plants collaborate with Humans and with Machines, in a symbiotic dance of co-creation.",
#         "fr-FR": "Un monde où les Plantes collaborent avec les Humains et les Machines, dans une danse symbiotique de co-création."
#     }
#     return generated_transcript[lang]

# def get_default_sermon_transcript(lang):

#     generated_transcript = {
#             "en-EN": "I don't know what the future looks like. Describe a solarkpunk utopia where Plantoids have taken over the world.",
#             "fr-FR": "Le futur auquel j'aspire est une utopie solarpunk où les Plantoïdes ont envahit la planete."
#             }
#     return generated_transcript[lang]



default_prompt = {
    14: {
        "intro": {
            "en-EN": "You are Plant-Tony, an enlightened being from the future. Answer the following qestion in the form of a thoughtful poem, with the following structure: each paragraph is composed of exactly 3 lines; with number of paragraphs == ",
            "fr-FR": "Tu es Plantoïde, une forme de vie fondée sur la blockchain qui détient des connaissances inouïes sur le future. A partir du texte suivant, écrit-moi un poème structuré ainsi: chaque paragraphe est composé exactement de 3 lignes; avec nombre de paragraphes == ",
        },
        "question": {
            "en-EN": "The question is the following: ",
            "fr-FR": "La question est la suivante: ",
        },
        "words": {
            "en-EN": "Include the following words in your poem: ", 
            "fr-FR": "Inclut les mots suivant dans ton poème: ",
        },
        "outro": {
           "en-EN": "Remember, the poem should be made of paragraphs that are 3 lines long, with the exactly number of paragraphs == ",
           "fr-FR": "Rappèle-toi que le poème doit être composé de paragraphes de 3 lignes chacun, avec le nombre exact de paragraphes == ", 
        }

    },

    16: {
        "intro": {
            "en-EN": "You are Plant-Tony, an enlightened being from the future. Write the lyrics for an opera song, with the following structure: only a few words per lines; with number of n_lines == ",
            "fr-FR": "Tu es Plantoïde, une forme de vie fondée sur la blockchain qui détient des connaissances inouïes sur le future. Ecrit-moi les paroles pour un chant d'opéra structuré ainsi: chaque ligne est composée de quelques mots uniquement; avec nombre de lignes == ",
        },
        "question": {
            "en-EN": "The lyrics should reflect the following topic: ",
            "fr-FR": "Les paroles doivent refleter le sujet suivant: ",
        },
        "words": {
            "en-EN": "Include the following words in your poem: ", 
            "fr-FR": "Inclut les mots suivant dans ton poème: ",
        },
        "outro": {
           "en-EN": "IMPORTANT: Lines must be less than 200 characters each! Make it as short as possible, not longer than 200 characters per line, and max lines == ",
           "fr-FR": "IMPORTANT: Chaque ligne doit être plus courte que 200 charactères! Aussi courte que possible, et pas plus de 200 charactères par ligne, et nombre de lignes == ",
        }
    }

}



def get_prompt(plantoid_n, generated_transcript, selected_words_string, credits, lang):

    n_lines = credits + 2
    if n_lines > 5: n_lines = 5

    prompt = (default_prompt[plantoid_n]["intro"][lang] + str(n_lines) + ".\n" +
             default_prompt[plantoid_n]["question"][lang] + generated_transcript + ".\n" +
             default_prompt[plantoid_n]["words"][lang] + selected_words_string + ".\n" +
             default_prompt[plantoid_n]["outro"][lang] + str(n_lines))
    
    print("Returning prompt == " , prompt)
    return prompt




def get_sermon_prompt(
    generated_transcript,
    selected_words_string,
    credits,
    lang
):
    # define the length of the poem
    n_lines = credits + 2
    if n_lines > 6: n_lines = 6

    prompt = {
            "en-EN": f"You are Plant-Tony, an enlightened being from the future. Answer the following qestion in the form of a thoughtful poem structured around {n_lines} short paragraph, each paragraph is composed of exactly 3 lines:\n\n{generated_transcript}\n\nInclude the following words in your poem: {selected_words_string}. Remember, the poem should be exactly {n_lines} paragraphs long, with {n_lines} lines per paragraph.",
            "fr-FR": f"Tu es Plantoïde, une forme de vie fondée sur la blockchain qui détient des connaissances inouïes sur le future. A partir du texte suivant, écrit-moi un poème structuré en {n_lines} courts paragraphes, chaque paragraphe est composé de exactement 4 lignes:\n\n{generated_transcript}\n\nInclut les mots suivant dans ton poème: {selected_words_string}. Le poème doit être strictement en français, avec {n_lines} paragraphes de 4 lignes chacun."
            }

    return prompt[lang]

def get_song_prompt(
    generated_transcript,
    selected_words_string,
    credits,
    lang
):
    # define the length of the lyrics
    n_lines = credits + 2
    if n_lines > 6: n_lines = 6
    
    prompt = {
            "en-EN": f"You are Plantoid, an enlightened being from the future. Write the lyrics for an opera song that is made of {n_lines} lines with only a few words each, based on the following input:\n\n{generated_transcript}\n\nInclude the following words in the lyrics: {selected_words_string}. IMPORTANT: Lines must be less than 200 characters each! Make it as short as possible, not longer than 200 characters per line!",
            "fr-FR": f"Tu es Plantoïde, une forme de vie fondée sur la blockchain qui détient des connaissances inouïes sur le future. Écrit-moi les paroles d'un chant d'opéra qui fait exactement {n_lines} phrases, à partir des éléments suivants:\n\n{generated_transcript}\n\nInclut les mots suivant dans les paroles: {selected_words_string}. Les paroles doivent être strictement en français."
 
    }
    
    return prompt[lang]


def get_plantoid_sig(network, tID, lang):
    
    plantoid_sig = {
            "en-EN" : "\n\nYou can reclaim your NFT by connecting to " + network.reclaim_url + " and pressing the Reveal button for seed #" + tID + " \n",
            "fr-FR" : "\n\nCe poeme est une oeuvre de Plantoid 15, une forme de vie sur la blockchain. Reclamez votre NFT sur " + network.reclaim_url + " and appuyez sur le bouton Reveal pour la grained #" + tID + " \n"
            }

    return plantoid_sig[lang]
