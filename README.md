# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

**macOS / Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Tool Inventory

Your README submission must document each tool's name, inputs, and return value. **These must exactly match your actual function signatures in `tools.py`.** Your documented interfaces will be checked against your actual function signatures in `tools.py` — if the parameter count or types contradict what's in the code, you may not receive full credit for that tool.

---
Tool 1 : search_listings(description: str,size: str | None = None,max_price: float | None = None) -> list[dict]:

Tool 2: suggest_outfit(new_item: dict, wardrobe: dict) -> str:

Tool 3: create_fit_card(outfit: str, new_item: dict) -> str:

## Interaction Walkthrough

<!-- Walk through a complete interaction step by step: natural language query → each tool call (and why) → final fit card.
     Walk through this carefully — it's how graders follow your agent's reasoning without a live demo.
     Use a specific example — do not leave this as a template. -->

**User query:**

**Step 1 — Tool called:**
- Tool: search_listings
- Input: (description: str,size: str | None = None,max_price: float | None = None)
- Why this tool: This tool will provide the user with a listing that best matches its' query. Not only is this neccessary for the next tool, it is neccessary for the entire pipeline as a whole.
- Output: list[dict] containing three dictionary objects holding information about the three listings most aligned with the description

**Step 2 — Tool called:**
- Tool: suggest_outfit
- Input: (new_item: dict, wardrobe: dict) 
- Why this tool: The string produced by this is neccessary for tool three since it provides the neccessary context for it to create the best hit_card based on the users' input.
- Output: A string with a description of the entire outfit based on the new_item

**Step 3 — Tool called:**
- Tool: create_fit_card
- Input: (outfit: str, new_item: dict) 
- Why this tool: This tool builds upon the outputs from step 1 and 2, utilizing them as context so it can create the best and most accurate fit card for the user. 
- Output: A string, the fit card to be returned to the user

**Final output to user:**
The state of the session is returned to the user, if there is an error then it'll be presented to the user. Otherwise, the user will be presented with description of the object found, the outfit or outfit suggestion created in step 2, and the fit card based on the entire outfit with a greater focus on the found object.

---

## Error Handling and Fail Points

<!-- For each tool, describe the specific failure mode and what your agent does in response.
     This maps to the error handling section of the rubric (F5-C1). -->

| Tool | Failure mode | Agent response |
|------|-------------|----------------|

| search_listings | No results match the query | immediately return an error string that can then be allocated to the error variable in the session state dictionary |
(example: 
  query: designer ballgown size XXS under $5
  Error message: There are no items matching your specified sizing or pricing within the listings)

| suggest_outfit | Wardrobe is empty | Suggest an outfit without the influence of a wardrobe |
(example: Found: Vintage Graphic Hoodie — Faded Black

Outfit: With your faded black pullover hoodie, a pair of distressed black jeans would complement the worn-in look, while some black and white Vans sneakers would add a touch of casual cool. A silver chain necklace with a small pendant would subtly elevate the outfit, adding a hint of edginess. The overall vibe would be laid-back and effortless, perfect for a relaxed day out. The cozy interior of the hoodie and the softness of the jeans would also ensure a comfortable outfit.

Fit card: I just scored the coolest Vintage Graphic Hoodie on Depop for $26 and I'm obsessed - the faded black color and barely-visible graphic give it this perfect worn-in, grunge vibe that's literally all I've been wearing lately. The fact that it's got some pilling just adds to the vintage feel, you know? I got it in a large, and I think it's the perfect addition to my streetwear rotation. Highly recommend checking out Depop for unique finds like this one!)



| create_fit_card | Outfit input is missing | If the outfit input is missing, then create a fit card based solely on the selected piece of clothing. |
(example:
   Query:90s track jacket in size M

Found: 90s Track Jacket — Navy/White Stripe

Outfit: To complement the Authentic 90s track jacket, I'd pair it with a white graphic t-shirt and some high-waisted black leggings or joggers, which will create a sporty-chic look. The bold stripe detail on the jacket will be balanced by the simplicity of the leggings and tee. Adding a pair of sleek black and white sneakers will tie the whole outfit together, giving off a fresh and nostalgic vibe. A simple silver chain necklace will add a touch of elegance to the overall athletic-inspired ensemble.

(outfit input is empty here)
Fit card: I just scored the cutest 90s Track Jacket from Champion on Poshmark for $45, and I'm obsessed with the vintage vibe it's giving me - the navy and white stripes are everything. The fact that it's lightweight makes it perfect for layering, and I can already imagine wearing it over a graphic tee for a chill streetwear look. I've been searching for a jacket like this for ages, and I'm so glad I found it on Poshmark - it's definitely a staple piece for my athletic-inspired wardrobe.)



| create_fit_card | Outfit input is incomplete | If outfit input is incomplete in certain areas, create a fit card without including those categories of clothing in it.|

(example: Found: 90s Silk Slip Dress — Floral, Midi Length [Does not utilize outerwear]

Outfit: Style the slip dress on its own and add chunky white sneakers for a sporty-chic look, finishing with a brown leather belt to add a touch of earthy elegance

Fit card: I'm obsessing over this effortless, cottagecore vibe I've got going on today, and it's all thanks to this stunning 90s Silk Slip Dress - Floral, Midi Length that I scored on Depop for $30. I paired the dress with some chunky white sneakers to add a sporty touch and a brown leather belt to bring in an earthy tone, but let's be real, the dress is the real star of the show - I mean, who can resist a vintage, floral midi dress with adjustable straps and a romantic, feminine feel?)


---


## Spec Reflection

<!-- Answer both questions with at least 2–3 sentences each. -->

**One way planning.md helped during implementation:**
Since there are so many different ways to tackle this project, writing out the planning.md prior to implementation kept me much more grounded in my approach. I was able to isolate the different functions and their responsibilities prior to programming thus making implimentation much more easier. Planning also helped me establish how to handle errors in the most applicable way possible for the pipeline.

**One divergence from your spec, and why:**
There was no bm25 shortcut where I could ask for the top entries that have the most keywords in common with the query, instead I just used a tuple containing the scores and the listings to then sort by the included scores. Although this was useful, it consumed more storage which would be terrible if there were more listings.

---

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

1.) I'll give Chatgpt an example of a query and what I hope to receive from llama. I'll ask it how I can utilize the settings in my query to receive only JSON and how can I parse this JSON upon its' return. I'll give it an example of a query, what I hope to receive in a specific JSON format. I hope to receive a small change to my setting when sending the query through groq. Before trusting this change, I'll test it out against many queries to ensure that JSON is consistently returned and that it can be parsed quickly. I received some programming, what I took away from it was setting the option of "response_format={"type": "json_object"}" and utilizing json.loads(). I used these insights and applied them to my programming.

2.) I'll give Chatgpt the spec of tool1 and explain that I want to find which listing description has the most keywords in common with the query. I'll show it an example of a listing description and an example of a query. I'll also advise it to use bm25 since I am most familiar with it. I hope to receive a single line of programming on what to run after training bm25 and fetching listings against the query, to then see if there's a single line of programming where I can receive top k entries in a similar way to how vector db functions. This didn't produce a one line program line or a option like in the first case. So I then asked how I can use the scores provided, it later informed me that since the scores are in order, I can simply used them for indexing. So I later used zip and a lambda function to sort the tuple with the scores and the dictionary objects together.
