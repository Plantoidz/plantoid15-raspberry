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


def get_default_sermon_transcript(lang):

    generated_transcript = {
            "en-EN": "I don't know what the future looks like. Describe a solarkpunk utopia where Plantoids have taken over the world.",
            "fr-FR": "Le futur auquel j'aspire est une utopie solarpunk où les Plantoïdes ont envahit la planete."
            }
    return generated_transcript[lang]

def get_sermon_prompt(
    generated_transcript,
    selected_words_string,
    n_lines,
    lang
):

    prompt = {
            "en-EN": f"You are Plant-Tony, an enlightened being from the future. Answer the following qestion in the form of a thoughtful poem structured around {n_lines} short paragraph, each paragraph is composed of exactly 3 lines:\n\n{generated_transcript}\n\nInclude the following words in your poem: {selected_words_string}. Remember, the poem should be exactly {n_lines} paragraphs long, with {n_lines} lines per paragraph.",
            "fr-FR": f"Tu es Plantoïde, une forme de vie fondée sur la blockchain qui détient des connaissances inouïes sur le future. A partir du texte suivant, écrit-moi un poème structuré en {n_lines} courts paragraphes, chaque paragraphe est composé de exactement 4 lignes:\n\n{generated_transcript}\n\nInclut les mots suivant dans ton poème: {selected_words_string}. Le poème doit être strictement en français, avec {n_lines} paragraphes de 4 lignes chacun."
            }

    return prompt[lang]

def get_plantoid_sig(network, tID, lang):
    
    plantoid_sig = {
            "en-EN" : "\n\nYou can reclaim your NFT by connecting to " + network.reclaim_url + " and pressing the Reveal button for seed #" + tID + " \n",
            "fr-FR" : "\n\nCe poeme est une oeuvre de Plantoid 15, une forme de vie sur la blockchain. Reclamez votre NFT sur " + network.reclaim_url + " and appuyez sur le bouton Reveal pour la grained #" + tID + " \n"
            }

    return plantoid_sig[lang]
