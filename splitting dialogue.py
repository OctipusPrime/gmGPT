text = """

Narrator: 

Hours pass peacefully until near dawn when Chubby suddenly perks up, her ears twitching nervously. You feel her tense under your hand as she sniffs at the air anxiously. Something seems off but you can't quite place what it is yet. 

Player: 

Ram perks up as Chubby nudges him. Immediately he looks around for whatever Chubby has spotted. 

`Perception: 17 + 5 = 23`

Narrator: 

Your keen dwarven eyes, enhanced by years of serving in the military, quickly scan the surroundings. The early morning light seeping through reveals nothing out of ordinary at first, but then you spot it - a faint shimmering in the air near one of the ruins' entrance. 

It's a subtle distortion, like heat rising off hot stone, but there's an unnatural hue to it - one that speaks of arcane energy.


Player: 

Ram gets up slowly, almost afraid to disturb whatever he is seeing. While having his eyes peeled at the dancing lights, he shakes Rolan and Elara awake while making it clear that they should stay quiet. 

He stands up and carefully walk toward the strange sight. 

Narrator:

From behind you hear Rolen stirring awake and Pippin gasping lightly. Elara is up as well. All the while Morthos is peacefully dozing off, with peaceful low snores leaving her mouth. 

You step closer to the magical dust inspecting it. 

Suddenly, it feels like something or someone is watching from within this shimmering energy. A chill runs down your spine as a low hum begins to resonate from within the ruins.

As you near the shimmering energy, its undulating glow intensifies, casting an eerie light over the ancient ruins. Faint whispers seem to echo amid the stillness like a long-lost melody carried by the wind.

Suddenly a figure steps out from amidst the arcane glow - a presence composed of the deepest void coated with stars like gem stones, shining in the night. It forms into a female body, nebula for her hair. 

Player:

Ram’s mouth gapes open as he loses a sense of himself. *Such beauty…* he thinks as his eyes move across the smooth midnight coloured body. The eyes are 
"""

import re

def split_to_paragraphs(content):
    pattern = r"(Narrator:|Player:)"
    paragraphs = re.split(pattern, content)[1:]
    paragraphs = [paragraphs[i] + paragraphs[i+1] for i in range(0, len(paragraphs), 2)]
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    return paragraphs

for item in split_to_paragraphs(text):
    print("---")
    print(item)
    print("---")