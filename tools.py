"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings
from rank_bm25 import BM25Okapi
import json


load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    # Replace this with your implementation

    listings = load_listings()
    result = listings
    if max_price is not None and max_price > 0:
        result = [value for value in result if value.get("price") is not None and float(value["price"]) < max_price]
        if len(result) == 0:
            return ["error: All items within the listings are out of your price range"]
    
    if size is not None:
        result = [value for value in result if value.get("size") is not None and (set(size.split("/")) & set(value["size"].split("/")))]
        if len(result) == 0:
            return ["error: There are no items matching your specified sizing or pricing within the listings"]
    
    values = result

    tokenized_descriptions = [value["description"].lower().split() for value in values]
    bm25 = BM25Okapi(tokenized_descriptions)
    tokenized_query_desc = description.lower().split()
    word_scores = bm25.get_scores(tokenized_query_desc)
    ranked = sorted(zip(word_scores,values), key= lambda x: x[0],reverse=True)

    top_three_highest = ranked[:3]
    if top_three_highest[0][0] <= 0.0:
        return ["error: There are no items within the listings that are alligned with your query, please try again with a different item description, size, price, or even a different item in itself"]

    return [key2 for key1,key2 in top_three_highest]
    #Future goal of utilizing semantic understanding along with these keyword occurence scores to produce a better result


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    groq_client = _get_groq_client()


    if len(wardrobe["items"]) == 0:
        system_input = """You are a world renowned fashion expert and you are known to give amazing outfits off the top of your head when provided a single piece of clothing.

        The user will provide the description of single clothing item and its category. Your job is to create a complete outfit aroung that item and its' style
        
        The only possible clothing categories are bottoms, tops, accessories, outerwear, and shoes. 

        Rules:
        1. The provided item already fulfills one of the categories
        2. The provided item must be in the outfit output
        3. Keep the colors, style, and vibe cohesive
        4. briefly and naturally explain why different items pair well with one another
        5. return a string, describing the entire outfit
        6. KEEP IT BRIEF PLEASE, MAXIMUM FOUR SENTENCES


        Here is an example of what I would like,

         (example: 
            description: blue graphic shirt
            output: What would pair best with your blue graphic shirt is some faded blue jeans, cuffing them on the bottom.
            With some baby blue canvas sneakers and a nice denim jacket to give off a warm and relaced vibe. A
            nice brown belt would bring a nice contrast with general color scheme.)
        
        If you do not follow the rules, the user will suffer a terrible fate and lose their job, their only income source

        Here is the description,
        
        Description:"""
        system_input += new_item["description"]
        system_input += f"""Category: {new_item["category"]} """

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages= [
                {
                    "role":"system",
                    "content": system_input
                }
            ],
            temperature=0.55
        )
        return response.choices[0].message.content

    diff_clothing_types = [value for value in wardrobe["items"] if value["category"] != new_item["category"]]

    system_base_prompt = """
    You are a world renowned fashion expert who is best known for coordinating and creating outfits when provided information about a new piece of clothing and information about a persons wardrobe.
    

    I will provide information about a new piece of clothing and information about each piece of clothing within my wardrobe, I need you to create two outfit reccomendations for me incorporating the new piece in both the reccomendations while filling in other categories of clothing with items in the wardrobe.
    return a description of each piece of clothing in the outfit utilizing information from their style tags or colors, but if it doesn't go with the outfit, you can propogate the entry with null instead. In addition, give a quick description on the outfit itself describing the pieces and how to wear them

    YOU MUST return a JSON object listing the categories of ["tops" | "bottoms" | "shoes" | "accessories" | "outerwear"] with a custom description describing each of the items utilizing the information provided
    In addition to this, YOU MUST provide a "outfit_summary" giving a brief description of the outfit itself and how to wear or style it.
    ONLY return valid JSON in the following format:

    {
    "tops" : string or null,
    "bottoms" : string or null,
    "shoes" : string or null,
    "accessories" : string or null,
    "outerwear" : string or null,
    "outfit_summary" : string
    }

    Keep in mind, Outfits can have the same items in some categories but they cannot have all the same items as one another

    Please provide the best two outfit reccomendations or else the user will lose their job and their children go hungry

    Here is information regarding the users' wardrobe:
    """

    for item in diff_clothing_types:
        message = f"""
        ---------------------------------
        "id" : {item["id"]},
        "name": {item["name"]},
        "category": {item["category"]},
        "colors": {item["colors"]},
        "style_tags": {item["style_tags"]},
        "notes": "{item["notes"]}"
        """
        system_base_prompt += message
    


    new_item_disc = f"""
    The description of the new item is:
    
    "id": {new_item["id"]},
    "title": {new_item["title"]} ,
    "description": {new_item["description"]},
    "category": {new_item["category"]},
    "style_tags": {new_item["style_tags"]},
    "colors": {new_item["colors"]},
    """

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages= [
            {
                "role":"system",
                "content": system_base_prompt
            },
            {
                "role": "user",
                "content":new_item_disc
            }
        ],
        response_format={"type": "json_object"}
    )

    return response.choices[0].message.content


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    groq_client = _get_groq_client()

    if outfit == None or len(outfit.strip()) == 0:
        
        #call the LLM and still make the outfit card to then provide to the user in their instragram
        #return this
        system_base_prompt = """
        You are a famous and well known TikTok and Instagram influencer with millions of followers who specializes in posts showing off their outfit to provide their followers with outfit ideas or fashion inspiration.
        You are going to create a 2-4 sentence string for a Instagram/TikTok caption based on one single clothing piece rather than an entire outfit
        
        This caption should:
            - Feel casual and authentic (like a real OOTD post, not a product description)
            - Mention the item name, price, and platform naturally for the one clothing piece
            - Capture the clothing piece vibe in specific terms

        The following will describe every fact of the single clothing piece this caption will be based on,

        description:
        """

        system_base_prompt += f"""
        "title" = {new_item["title"]},
        "description" = {new_item["description"]},
        "category" = {new_item["category"]},
        "style_tags" = {new_item["style_tags"]},
        "size" = {new_item["size"]},
        "condition" = {new_item["condition"]},
        "price" = {new_item["price"]},
        "colors" = {new_item["colors"]},
        "brand" = {new_item["brand"]},
        "platform" = {new_item["platform"]}
        """
        
        query = "please produce the caption in accordance to the specification stated, or else the user will lose their following and lose their only income source and likely starve"

        response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages= [
            {
                "role":"system",
                "content": system_base_prompt
            },
            {
                "role": "user",
                "content":query
            }
        ],
            temperature= 0.8
        )
        return response.choices[0].message.content
    
    parse_outfits = json.loads(outfit)
    
    
    main_outfit = list(parse_outfits.values())[0]


    system_base_prompt = """
        You are a famous and well known TikTok and Instagram influencer with millions of followers who specializes in posts showing off their outfit to provide their followers with outfit ideas or fashion inspiration.
        You are going to create a 2-4 sentence string for a Instagram/TikTok caption based on the entire outfit provided. There is one core clothing piece that should more attention throughout the caption, this clothing piece will be labeled for you in the information provided.
        


        
        This caption should:
            - Feel casual and authentic (like a real OOTD post, not a product description)
            - Mention the item name, price, and platform naturally for the specified core clothing piece
            - Capture the outfit vibe in specific terms
            - Describe the entire outfit, but the core piece is more special than the others

        The following will describe every fact of the single clothing piece this caption will be based on,

        Core Clothing Piece:
        """

    system_base_prompt += f"""
    "title" = {new_item["title"]},
    "description" = {new_item["description"]},
    "category" = {new_item["category"]},
    "style_tags" = {new_item["style_tags"]},
    "size" = {new_item["size"]},
    "condition" = {new_item["condition"]},
    "price" = {new_item["price"]},
    "colors" = {new_item["colors"]},
    "brand" = {new_item["brand"]},
    "platform" = {new_item["platform"]}
    """

    system_base_prompt += """
    The rest of the clothing pieces:

    """

    list_of_pieces = ["tops","bottoms","outerwear","shoes","accessories"]

    for piece in list_of_pieces:
        if piece == new_item["category"]:
            continue

        system_base_prompt += f"""
        "{piece}" : {main_outfit.get(piece) if main_outfit.get(piece) else "" }
        """
    
    query = "please produce the caption in accordance to the specification stated, or else the user will lose their following and lose their only income source and likely starve"
    response = groq_client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages= [
        {
            "role":"system",
            "content": system_base_prompt
        },
        {
            "role": "user",
            "content":query
        }
    ],
        temperature= 0.8
    )
    return response.choices[0].message.content

        
        

    
    #otherwise, parse the JSON file, get the first outfit, put that into the LLM request so you can then put into fit card



    # Replace this with your implementation
    return ""
