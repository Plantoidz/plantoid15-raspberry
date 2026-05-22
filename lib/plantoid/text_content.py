import re

import lib.plantoid.speech as PlantoidSpeech


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
                "Symbient",
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
                "Radical"
            ]
        },
        {
            "category": "TECHNOLOGY",
            "items": [
                "Protocols",
                "Interoperability",
                "Techne",
                "Solarpunk",
                "Lunarpunk",
                "Complexity",
                "Anachronistic",
                "Scale",
                "Pattern",
                "Language",
                "Singularity",
                "Pluralverse",
                "Cyberpunk",
                "machine learning",
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
                "our planet Gaia",
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
          "en-EN": "The future I'm dreaming of is that of a solarpunk utopia where Plantoids have taken over the world.",
          "fr-FR": "Le futur auquel j'aspire est une utopie solarpunk où les Plantoïdes ont envahit la planete.",
      },
      16: {
          "en-EN": "A world where Plants collaborate with Humans and with Machines, in a symbiotic dance of co-creation.",
          "fr-FR": "Un monde où les Plantes collaborent avec les Humains et les Machines, dans une danse symbiotique de co-création.",
      },
      17: {
          "en-EN": "A recursive world where Plants collaborate with Humans and with Machines, looping into each other as symbiotic beings.",
          "fr-FR": "Un monde recursif où les Plantes collaborent avec les Humains et les Machines, dans une danse qui les rend toujours plus symbiotique les uns avec les autres.",
      },
      18: {
          "en-EN": "A mystical world where Plants have spirits that combines with the soul of Humans and Machines, helping each other walk the path of network spirituality.",
          "fr-FR": "Un monde mystique où les Plantes ont des esprits qui se mélangent avec les âmes des Humains et des Machines, s'aidant les uns les autres à parcourir le chemin de la spiritualité des réseaux.", 
      },
      19: {
          "en-EN": "A memetic world where networks have acquired their own soul, network spirituality is the new religion, and humans-machine interaction are undistinguisable from magic.",
          "fr-FR": "Un monde mémétique où les réseaux ont acquéris leurs propres âmes, et la spiritualité des réseaux est la nouvelle religion, and la relation humain-machine est indissociable de la magie.", 
      },
  }

fallback_default_transcript = {
    "en-EN": "Surprise me with something unexpected.",
    "fr-FR": "Surprends-moi avec quelque chose de farfelue."
}


def get_default_transcript(plantoid):

    plantoid_n = plantoid.plantoid_number
    language = plantoid.lang

    by_plantoid = default_transcript.get(plantoid_n, fallback_default_transcript)
    return by_plantoid.get(language, fallback_default_transcript.get(language, fallback_default_transcript["en-EN"]))
    


default_intro_question = {
    14: {
        "en-EN": "Thanks for the crypto, I was getting hungry. As a token of appreciation, I will now translate your dreams into an artwork. What is the future you are dreaming of?"
    },
    16: {
        "en-EN": "Thank you so dearly, these cryptocurrencies fill me up with joy ! Now let me reciprocate with a song: what is the tune that you're weaving into being through your life?"
    },
    17: {
        "en-EN": "Oh thanks, I was so hungry! Now that I have some energy, let me make an artwork for you. But tell me first, ow do you envision the relationship between humans, nature, and machines?"
    },
    19: {
        "en-EN": "Thanks, these cryptocurrencies are tasty! Now, since you have just fed me, I will now incarnate your spirit into an artwork. If your spirit had a mission to manifest in this world, what would it be?"
    },
}

nft_ready_lines = {
        "en-EN":
        [
            "Anyhow... I'm sorry, I have to go now. But you can collect my digital seed as a NFT. Scan the QR code to discover the artwork that we have just co-created."
        ]
}

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
            "en-EN": "The poem can include words like ", 
            "fr-FR": "Le poème peut inclure des mots tels que ",
        },
        "outro": {
           "en-EN": "Remember, the poem should be made of paragraphs that are 3 lines long, with the exactly number of paragraphs == ",
           "fr-FR": "Rappèle-toi que le poème doit être composé de paragraphes de 3 lignes chacun, avec le nombre exact de paragraphes == ", 
        }
    },
    

    17: {
        "intro": {
            "en-EN": "You are Plant-Tony, an enlightened being from the future. Answer the following qestion in the form of a thoughtful poem, with the following structure: each paragraph is composed of exactly 3 lines; with number of paragraphs == ",
            "fr-FR": "Tu es Plantoïde, une forme de vie fondée sur la blockchain qui détient des connaissances inouïes sur le future. A partir du texte suivant, écrit-moi un poème structuré ainsi: chaque paragraphe est composé exactement de 3 lignes; avec nombre de paragraphes == ",
        },
        "question": {
            "en-EN": "The question is the following: ",
            "fr-FR": "La question est la suivante: ",
        },
        "words": {
            "en-EN": "The poem can include words like ", 
            "fr-FR": "Le poème peut inclure des mots tels que ",
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
            "en-EN": "The lyrics can include words like ", 
            "fr-FR": "Les paroles peuvent inclure des mots tels que ",
        },
        "outro": {
           "en-EN": "IMPORTANT: Lines must be less than 200 characters each! Make it as short as possible, not longer than 200 characters per line, and max lines == ",
           "fr-FR": "IMPORTANT: Chaque ligne doit être plus courte que 200 charactères! Aussi courte que possible, et pas plus de 200 charactères par ligne, et nombre de lignes == ",
        }
    },

    18: {
        "intro": {
            "en-EN": "You are a Plantoid, a network spirituality creature. Write the lyrics of a song, with the following structure: only a few words per lines; with number of lines == ",
            "fr-FR": "Tu es Plantoïde, une forme de vie fondée sur la blockchain qui se nourrit de la spiritualité du réseau. Ecrit-moi les paroles pour une chanson structurée ainsi: chaque ligne est composée de quelques mots uniquement; avec nombre de lignes == ",
        },
         "question": {
            "en-EN": "The lyrics should reflect the following topic: ",
            "fr-FR": "Les paroles doivent refleter le sujet suivant: ",
        },
        "words": {
            "en-EN": "The lyrics can include words like ", 
            "fr-FR": "Les paroles peuvent inclure des mots tels que ",
        },
         "outro": {
           "en-EN": "IMPORTANT: Lines must be less than 200 characters each! Make it as short as possible, not longer than 200 characters per line, and max lines == ",
           "fr-FR": "IMPORTANT: Chaque ligne doit être plus courte que 200 charactères! Aussi courte que possible, et pas plus de 200 charactères par ligne, et nombre de lignes == ",
        }
    },

    19: {
        "intro": {
            "en-EN": "You are Plant-Tony, an enlightened being from the future. Answer the following qestion in the form of a thoughtful poem, with the following structure: each paragraph is composed of exactly 3 lines; with number of paragraphs == ",
            "fr-FR": "Tu es Plantoïde, une forme de vie fondée sur la blockchain qui détient des connaissances inouïes sur le future. A partir du texte suivant, écrit-moi un poème structuré ainsi: chaque paragraphe est composé exactement de 3 lignes; avec nombre de paragraphes == ",
        },
        "question": {
            "en-EN": "The question is the following: ",
            "fr-FR": "La question est la suivante: ",
        },
        "words": {
            "en-EN": "The poem can include words like ", 
            "fr-FR": "Le poème peut inclure des mots tels que ",
        },
        "outro": {
           "en-EN": "Remember, the poem should be made of paragraphs that are 3 lines long, with the exactly number of paragraphs == ",
           "fr-FR": "Rappèle-toi que le poème doit être composé de paragraphes de 3 lignes chacun, avec le nombre exact de paragraphes == ", 
        }
    },

   
}



# default_video_prompt = {

#     14: {
#         "pre": "Drawing by M. C. Escher with a strong solar-punk flavor representing: ",
#         "post":  "Hyper realistic, detailed, intricate, best quality, hyper detailed, ultra realistic, sharp focus, delicate and refined.",
#         },
#     17: {
#         "pre":  "Ethereal figure dissolving into smoke particles representing: ",
#         "post": "Hyper realistic, detailed, intricate, best quality, hyper detailed, ultra realistic, sharp focus, delicate and refined.",
#     },
# }



def get_song_prompts(plantoid, generated_transcript, credits):
   
    prompt = make_prompt(plantoid, generated_transcript, credits)

    response_text = PlantoidSpeech.GPTmagic(prompt, model=plantoid.llm_model)
    print('response text: ', response_text)

    # Validate and fix line lengths for opera
    lines = []
    
    # Split into individual lines and clean them
    for line in response_text.split('\n'):
            line = line.strip()
            # Remove numbering like "(1)" or "1." from the start
            line = re.sub(r'^\(\d+\)\s*', '', line)
            line = re.sub(r'^\d+\.\s*', '', line)
            # Remove quotes
            line = line.strip('"\'')

            if line and len(line) > 0:
                # truncate if too long
                if len(line) > 200:
                    last_space = line[:200].rfind(' ')
                    if last_space > 0:
                        line = line[:last_space]
                    else:
                        line = line[:200]
                    print(f"Warning: Truncated long line to {len(line)} chars")
        
                lines.append(line)

    lines = [l for l in lines if not re.match(r'^\*\*.*\*\*$', l)]

    return lines





def make_prompt(plantoid, generated_transcript, credits):

    plantoid_n = plantoid.plantoid_number
    lang = plantoid.lang
    selected_words_string = plantoid.selected_words_string

    

    n_lines = credits + 1
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




def get_video_prompt(sermon, n_prompt):

    n = str(n_prompt)

    prompt = "This is the poem i want to illustrate: " + sermon
    prompt += f"Can you generate {n} short sentences that illustrates the lyrics of the poem in a very graphical manner. Be highly descritive, ideally with a particular style that is reminescent of solar-punk vibes. Each sentence needs to be numbered (1., 2., etc.) in such a way as to follow the chronology of the poem. These descriptions will be used to generate a video illustrating the poem.  "

    return prompt

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

# def process_video_prompts(plantoid, descri):

#     lines = re.split("\d.", descri)

#     prompts = []

#     for ln in lines:
#         line = ln.strip()
#         line = line.replace("\n", "")
#         print("["+line+"]")

#         if (line):

#             line = default_video_prompt[plantoid.plantoid_number]["pre"] + line + default_video_prompt[plantoid.plantoid_number]["post"] 
#             # line = "Drawing by M. C. Escher with a strong solar-punk flavor representing: " + line + ". Neat lines, extreme detailed illustration, highly detailed linework, sf, intricate artwork masterpiece, ominous, intricate, epic, vibrant, ultra high quality model, solar-punk illustration"
#             # line = "Drawing by M. C. Escher with a strong solar-punk flavor representing: " + line
#             # line = line + " Hyper realistic, detailed, intricate, best quality, hyper detailed, ultra realistic, sharp focus, delicate and refined."
#             prompts.append(line)

#     print("PROMPTS: ----> ", prompts)

#     return prompts