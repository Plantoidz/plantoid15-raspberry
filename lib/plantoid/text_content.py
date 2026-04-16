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




def get_plantoid_sig(network, tID, lang):
    
    plantoid_sig = {
            "en-EN" : "\n\nYou can reclaim your NFT by connecting to " + network.reclaim_url + " and pressing the Reveal button for seed #" + tID + " \n",
            "fr-FR" : "\n\nCe poeme est une oeuvre de Plantoid 15, une forme de vie sur la blockchain. Reclamez votre NFT sur " + network.reclaim_url + " and appuyez sur le bouton Reveal pour la grained #" + tID + " \n"
            }

    return plantoid_sig[lang]




def get_video_prompts(sermon, n_prompt):

    n = str(n_prompt)

    prompt = "This is the poem i want to illustrate: ", sermon
    prompt += f"Can you generate {n} short sentences that illustrates the lyrics of the poem in a very graphical manner. Be highly descritive, ideally with a particular style that is reminescent of solar-punk vibes. Each sentence needs to be numbered (1., 2., etc.) in such a way as to follow the chronology of the poem. These descriptions will be used to generate a video illustrating the poem.  "

    # prompt = "I need to illustrate this poem. "
    # prompt = prompt + "Can you generate " + str_n_prompts_n + " sentences (not more than " + str_n_prompts_n + " sentences) that illustrate the poem, presented chronologically based on the phrasing of the poem. "
    # prompt = prompt + "I don't wont a summary of the plot, I want a graphical description that illustrates the statements of the poem. "
    # prompt = prompt + "These descriptions will be used to generate a video illustrating the poem. "
    # prompt = prompt + "Every sentence needs to be a self-contained descriptive illustration, that does not refer to the previous or following sentences. "
    # prompt = prompt + "Be highly descritive, ideally with a particular style that is reminescent of solar-punk vibes. "
    # prompt = prompt + "You can mention colors but only in one of these descriptions, and no reference to colors must be present in the first sentence. "
    # prompt = prompt + "Draft your answer with each line starting with the number of the line, followed by a dot, a space, and then the actual description. "
    # prompt = prompt + "Here's the poem which I'd like you to litterally illustrate: " + stri

    # print("PROOOOOOOOOOOOOOOOMPT: ", prompt)

    # response1 = openai.Completion.create(
    #         engine=model_id,
    #         prompt=prompt1,
    #         max_tokens=max_tokens
    # )

    # response = openai.Completion.create(
    #     engine=model_id,
    #     prompt=prompt,
    #     max_tokens=max_tokens
    # )
    
    # descri1 = response1.choices[0].text
    # descri = response.choices[0].text

    # generate descriptions dir
    # if not os.path.exists(path + "/descriptions"):
    #     os.makedirs(path + "/descriptions");

    # # write descriton to file
    # with open(path + "/descriptions/" + seed + "_description.txt", "w") as outfile:
    #     outfile.write(descri1)
    #     outfile.write(descri)

def process_video_prompts(descri):

    lines = re.split("\d.", descri)

    prompts = []

    for ln in lines:
        line = ln.strip()
        line = line.replace("\n", "")
        print("["+line+"]")

        if (line):
            # line = "Drawing by M. C. Escher with a strong solar-punk flavor representing: " + line + ". Neat lines, extreme detailed illustration, highly detailed linework, sf, intricate artwork masterpiece, ominous, intricate, epic, vibrant, ultra high quality model, solar-punk illustration"
            line = "Drawing by M. C. Escher with a strong solar-punk flavor representing: " + line
            line = line + " Hyper realistic, detailed, intricate, best quality, hyper detailed, ultra realistic, sharp focus, delicate and refined."
            prompts.append(line)

    print("PROMPTS: ----> ", prompts)

    return prompts