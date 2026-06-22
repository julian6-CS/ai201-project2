"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

from tools import search_listings, suggest_outfit, create_fit_card, _get_groq_client
import re
from pathlib import Path
import json





# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    print(query)
    print("*" * 60)
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.

    Args:
        query:    Natural language user request
                  (e.g., "vintage graphic tee under $30, size M")
        wardrobe: User's wardrobe dict — use get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py

    Returns:
        The session dict after the interaction completes. Check session["error"]
        first — if it is not None, the interaction ended early and the other
        output fields (outfit_suggestion, fit_card) will be None.

    TODO — implement this function using the planning loop you designed in planning.md:

        Step 1: Initialize the session with _new_session().

        Step 2: Parse the user's query to extract a description, size, and
                max_price. You can use regex, string splitting, or ask the LLM
                to parse it — document your choice in planning.md.
                Store the result in session["parsed"].

        Step 3: Call search_listings() with the parsed parameters.
                Store results in session["search_results"].
                If no results: set session["error"] to a helpful message and
                return the session early. Do NOT proceed to suggest_outfit
                with empty input.

        Step 4: Select the item to use (e.g., the top result).
                Store it in session["selected_item"].

        Step 5: Call suggest_outfit() with the selected item and wardrobe.
                Store the result in session["outfit_suggestion"].

        Step 6: Call create_fit_card() with the outfit suggestion and selected item.
                Store the result in session["fit_card"].

        Step 7: Return the session.

    Before writing code, complete the Planning Loop and State Management sections
    of planning.md — your implementation should match what you described there.
    """
    # TODO: implement the planning loop


    session = _new_session(query, wardrobe)

    grok_client = _get_groq_client()

    system_prompt_for_query_parsing = """
    You are a fashion expert with many years in personal shopping, you can masterfully parse a clients request and break it apart into four seperate components; price, size, category, and item description.
    
     Rules:
    
        "description": string or null (the type, style, characteristic, and just overall description of the clothing item),
        "size": string or null (string representing the size of the piece of clothing (ex. S for small, M for medium, L for large, XL for extra large, including any mix of these sizings like S/M for small or medium, etc)),
        "category": one of these ["tops" | "bottoms" | "shoes" | "accessories" | "outerwear"] or null (based on the query, infer and choose out of the possible options),
        "max_price": float or null (float representing the maximum price specificied by the query)
    
    Extract these fields, and ONLY return valid JSON in the following format:

    {
    "description": string or null,
    "size": string or null,
    "category": string or null,
    "max_price": number or null
    }

    If an entry cannot be found within the prompt or it cannot be inferred when specifically handling category, please propogate it with None

    Here is an example:

    example_query: "I want a vintage graphic orange tee under $30 size S/M

    output:
    {
        "description": "orange vintage graphic tee",
        "size" : "S/M",
        "category" : "tops",
        "max_price" : 30.0
    }

    If the query cannot be parsed according to the specified format, or if every entry is null
    please specifically return the following JSON object
    {
        "error" : "unable to parse input"
    }

    The users livelihood and life hinges on your ability to follow the rules and fulfill the prompt, otherwise, they will lose their job and will not receive the neccessary surgery they need to survive. Here is the query

    query:
    """

    response = grok_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages= [
            {
                "role":"system",
                "content": system_prompt_for_query_parsing
            },
            {
                "role": "user",
                "content":query
            }
        ],
        response_format={"type": "json_object"}
    )

    parsed_query = json.loads(response.choices[0].message.content)


    if parsed_query.get("error"):
        session["error"] = "Your query wasn't able to be parsed, please try again. Remember to mention a description of the item, possible maximum allotted price, and possible sizing"
        return session
    
    session["parsed"] = {"description" : parsed_query.get("description"), "size" : parsed_query.get("size"), "category" : parsed_query.get("category"), "price" : parsed_query.get("price")}

    possible_listings = search_listings(description= session["parsed"].get("description"), size= session["parsed"].get("size"), max_price= session["parsed"].get("price"))

    if len(possible_listings) <= 1 and ("error" in possible_listings[0]):
        session["error"] = possible_listings[0].replace("error:", "")
        return session

    
    session["search_results"] = possible_listings
    session["selected_item"] = session["search_results"][0]

    possible_outfit = suggest_outfit(session["selected_item"],wardrobe)

    if "outfit_summary" not in possible_outfit:
        session["outfit_suggestion"] = possible_outfit
        possible_outfit = ""
    else:
        possible_outfit_parsed = json.loads(possible_outfit)
        parsed_outfits = list(possible_outfit_parsed.values())
        best_outfit = parsed_outfits[0]
        session["outfit_suggestion"] = best_outfit["outfit_summary"]

    fit_card_return = create_fit_card(possible_outfit,session["selected_item"])

    session["fit_card"] = fit_card_return

    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="flowy midi skirt under $40",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
