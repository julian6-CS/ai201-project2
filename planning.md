# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
The tool filters through all the listings utilizing inputs like size and max_price, then the listings that remain are then scored against the keywords present in the description.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): the description of the hypothetical item the user specified in their query.
- `size` (str): The desired size specifed by the user
- `max_price` (float): The desired maximum price specified by the user

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
returns a list containing the top three best matches for the query found in the listings, along with their bm25 keyword scoring for future uses and debugging.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->
Depending on the input used for filter purposes along all the listings, an error will be returned to the agent and stored in the session state. With this error, the pipeline cannot continue and it will return the current session state with an error.

---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Utilizing the new_item piece and wardrobe provided, the tool produces a possible outfit for the user.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): The selected item returned by the first tool which best matches the users' query
- `wardrobe` (dict): A dictionary object which includes descriptions of every piece of clothing that the user has in their wardrobe

**What it returns:**
<!-- Describe the return value -->
A dictionary object containing a description of each piece of clothing within this outfit, and a summary of the outfit as a whole. This is done to provide the next tool with better and more context to produce.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->
If an outfit is not returned, in the case that the wardrobe is empty or there's an error. The output is stored in session state since it either provides styling advice to the user or it provides context to an error case. This return value is set to an empty string so as to not propogate any error to the next tool in the pipeline.

---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
This tool utilizes the provided outfit and new_item to create a instagram fit card for the user.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str): the json string of the description of every outfit piece along with the outfit summary to provide the llama with better context for text generation
- `new_item` (dict): a dictionary object storing key information like item description, price, and platform where it was bought.

**What it returns:**
<!-- Describe the return value -->
It returns a string with a text generation from llama that is a fit card meant for use in instagram or tiktok. This string is descriptive about the outfit as a whole, while primarily speaking on the selected item.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->
If the outfit data is missing, it will instead return a fit card based solely on the single selected clothing piece. Any missing data will not be mentioned in the fit card.

---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->
The agent will first evaluate the success of parsing the users' query, if this failed it'll then display an error and prompt the user to try again with guidance on how to format their query. The first tool is then employed, if there aren't any listings found that best match the query, it'll then tell the user that there aren't any possible listings and which inputs made this success the least likely. If a listing is found, it'll then utilize the second tool. The next tool receives a wardobe and the selected item, if the wardrobe is empty, an outfit suggestion is returned with hypothetical accompanying outfit pieces. Otherwise, it'll return a outfit suggestion. The third tool is then utilized with the outfit suggestion and key information for the selected item, this tool then returns fit card as a string. All of this is then presented to the user within the terminal.

---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->

The agent stores all the neccessary and critical output within the session state dictionary object, which is then returned to the user when neccessary. The error state is returned immediately. While aspects like the parsing output, possible items or search results, selected item, outfit suggestion, etc are all stored to then be returned by the agent. Every variable with the exception of error and fit_card, is passed through a tool within the list. This is a technicality for create_fit_card since the outfit suggestion is within the json string passed through it, and the parsed variable where each of the list entries is entered in search listings.

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | immediately return an error string that can then be allocated to the error variable in the session state dictionary |
| suggest_outfit | Wardrobe is empty | Suggest an outfit without the influence of a wardrobe |
| create_fit_card | Outfit input is missing or incomplete | If outfit input is incomplete in certain areas, create a fit card without including those categories of clothing in it. If the outfit input is missing, then create a fit card based solely on the selected piece of clothing. |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     Use ASCII art or a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html).
     Do NOT embed an image — graders need to read your diagram directly in the file;
     an embedded image or screenshot cannot be evaluated.
     You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

     ```
     ---
config:
  layout: fixed
---
flowchart LR
 subgraph Agent["Agent"]
        PLAN["Planning Loop"]
        PARSE["Parse User Query"]
  end
 subgraph Tools["Tools"]
        SEARCH["Tool 1<br>search_listings"]
        SUGGEST["Tool 2<br>suggest_outfit"]
        FITCARD["Tool 3<br>create_fit_card"]
  end
    USER["User Input"] --> PLAN
    PLAN --> PARSE
    PARSE -- description, size, max_price --> SEARCH
    SEARCH -- listing1, listing2, listing3 --> RESULTS["Listings + Scores"]
    RESULTS -- store selected item --> STATE[("State / Session")]
    RESULTS -- selected item --> SUGGEST
    STATE -- wardrobe --> SUGGEST
    SUGGEST --> JSON["Outfit Suggestion JSON"]
    JSON -- extract outfit summary --> SUMMARY["Outfit string"]
    SUMMARY -- store summary --> STATE
    STATE -- selected item + outfit summary --> FITCARD
    FITCARD --> CARD["Fit Card String"]
    CARD -- store fit card --> STATE
    STATE --> OUTPUT["Return fit card, outfit suggestion,
    and selected item"]
    OUTPUT --> USER2["User"]
    PARSE -. can't parse query .-> PARSE_ERR["Prompt user to try again"]
    SEARCH -. no listings found .-> SEARCH_ERR["Prompt user to try again"]
    n2[" "] --> n1["Outfit suggestion string"]
    n1 --> SUMMARY
    n3["if wardrobe emptry"]

    n2@{ shape: anchor}
    n1@{ shape: rect}
    n3@{ shape: text}
     ```

'''
                                                                                                               ◄────────────────────────────────────┐                                                             
                                                                                                                                                    │                                                             
                                                                                                                                                    │                                                             
                                                                                                                                                    │                                                             
                                                                                                                                                    │                                                             
                                                                                                                                                    │                                                             
                                                                                                                                                    │                                                             
                                                                                                                                                    │                                                             
                                                                                                                                                    │                                                             
                                                                                                                                                    │                                                             
                                                                                                                                                                                                                  
                                                                                                                                                                                                                  
                                                                                                                                                                                                                  
                                                                                                                                                                                                                  
                                                                                                                                                                                                                  
                                                                                                                                                                                                                  
                                                                                                                                                                             ◄─                                   
                                                                                                                                                                                                                  
                                                                                                                                                                                                                  
                                                                                                                                                                                                                  
                                        ┌──────────────┐                                                                                                                                                          
                                        │agent ->state │─────────────────────────────┐                                                                                                                            
                                        └───────┬──────┘                             │                                                                                                                            
                                                │                                    │                                                                                                                            
                                                │                                  ┌─┼──────────────────┐                                                                                                         
                                                │                                  │    output          │                                                                                                         
                                                │                                  │                    │        ┌───────────────────────┐                                                                        
                                                │                                  │fit card as a string├────────┼tool3: create_fit_card │◄────┐                                                                  
                                                ▼                                  └────────────────────┘        └───────────────────────┘     │                                                                  
                                                                                                                                               │                                                                  
                                     return the stored fit card, outfit suggestion                                                             │                                                                  
                                                              ▼                                                   ▲                            │                                                                  
                                     and chosen item using terminal                                               │                            │                                                                  
                                                 │                                                                │input                       │                                                                  
                                                 │                                                                │                            │                                                                  
                                             ┌───▼───┐                                                            │                            │                                                                  
                                             │       │                                                        empty string                     │                                                                  
       ┌─────────────────────────────────────┼ User  │◄────◄──────────────┐                                                                    │                                                                  
       │                                     │       │     │              │                                          │                         │input                                                             
       │                                     └───────┘     │              │                                          │                         │                                                                  
       │                                                   │              │                             ┌────────────┼────────────────┐        │                              ┌──────────────────────┐            
       │                                                   │              │                             │ outfit suggestion as string ┼────────┼─────────────────────────────►│agent -> state_storage│            
       │                                                   │          ▼   Error:No listings             └─────────────────────────────┘        │                              └───────────────▲──────┘            
       │                                                   │              found prompt user                       │                            │                                              │                   
       │                                                   │              to try again                            │                            │                                              │                   
       │                                                   │Error:        │                                 output if wardrobe empty           │                                                                  
       │                                                   Can't parse    │                                                                    │                                     extracting the outfit summary
       │                                                   prompt user    │                                      │                             │                                                                  
       │                                                   to try again   │                                      │                             │                                     from the json string         
       │                                                   │              │             ◄─                       │                             │ output if wardobe is not empty                                   
       │                                                   │              │                              ┌───────┴─────┬──────┐               ┌┼───────────────────────────────┐            │                     
┌──────┼─────┐     ┌─────────────┐    ┌────────────────┐   │      ┌───────┼────────────────┐             │tool2:suggest outfit┼───────────────│outfit suggestion as JSON string│            │                     
│            │     │             │    │                │   │      │tool 1: Search Listings │             └─────────▲──────────┘               └────────────────────────────────┴────────────┘                     
│ User Input ┼────►│Planning Loop┼────►Parse User Query│   │      └───────▲────────────────┤                       │                                                                                              
│            │     │             │    │                │   │              │                │                       │                                                                                              
└────────────┘     └─────────────┘    └─────────┬──────┘   │              │ input          │              input: listing1, wardrobe                                                                               
                                                │          │              │                │output               │                                                                                                
                                                │ output   ├──────────────┼──────────────┐ │                     │                                                                                                
                                                └──────────┼                             │ │    ┌────────────────┼──────────────────────────────────┐                                                             
                                                           │Description, size, max_price │ └────┤listing1(scoring, dictionary object),..listing3(..]│                                                             
                                                           └─────────────────────────────┘      └────┬──────────────────────────────────────────────┘                                                             
                                                                                                     │                                                                                                            
                                                                                                     │storing listing1 as selecte item                                                                            
                                                                                                     │                                                                                                            
                                                                                                     │         ┌──────────────────────┐                                                                           
                                                                                                     └────────►│agent -> state_storage│                                                                           
                                                                                                               └──────────────────────┘                                                                           
'''
---

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

1.) I'll give Chatgpt an example of a query and what I hope to receive from llama. I'll ask it how I can utilize the settings in my query to receive only JSON and how can I parse this JSON upon its' return. I'll give it an example of a query, what I hope to receive in a specific JSON format. I hope to receive a small change to my setting when sending the query through groq. Before trusting this change, I'll test it out against many queries to ensure that JSON is consistently returned and that it can be parsed quickly.

2.) I'll give Chatgpt the spec of tool1 and explain that I want to find which listing description has the most keywords in common with the query. I'll show it an example of a listing description and an example of a query. I'll also advise it to use bm25 since I am most familiar with it. I hope to receive a single line of programming on what to run after training bm25 and fetching listings against the query, to then see if there's a single line of programming where I can receive top k entries in a similar way to how vector db functions.

**Milestone 3 — Individual tool implementations:**

**Milestone 4 — Planning loop and state management:**

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
First, the agent must parse the query for keywords concerning the size and price of the items, as well, as a general description of the item using AI tools like llama. 
If the parsing fails to harnest anything from the users' prompt it will prompt the user to try again with guidance for more specific wording. These parsed entries are then stored in the user_state and provided to the search_listings tool.

(ex. item description: vintage graphic tee, max_price: 30, size: none)

 This tool will locate the best or closest item within the listings that matches the users' query. If an item cannot be found with the specified size or price, the returned error will reflect this. In addition, if an item cannot be found according to the description provided, the error returned will let the user know and prompt them to try again. Otherwise, the top three items matching the users' query are returned along with their corresponding scores for possible future uses.

 (ex. Selected item - 
     "id": "lst_033",
    "title": "Vintage Band Tee — Faded Grey",
    "description": "Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.",
    "category": "tops",
    "style_tags": ["vintage", "grunge", "band tee", "graphic tee", "streetwear"],
    "size": "L",
    "condition": "fair",
    "price": 19.00,
    "colors": ["grey", "charcoal"],
    "brand": null,
    "platform": "depop")

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->
The top three items are stored in the search_results of the session state dictionary.
The first entry in this list of the top three items most aligned with the users' query is harvested and placed in the session state.

This selected_item, along with the wardrobe are provided to the suggest outfit tool. If an empty wardrobe is entered, then the tool will instead return advice on how to style the selected item with different possible pieces of clothing or what the clothings vibe is to be stored as an outfit suggestion. Otherwise, it will filter out items within the same category in the wardrobe and provide llama with all the clothing pieces remaining that can be used to construct the outfit suggestion. The model output a description of each piece and an overall summary of the entire outfit as a whole which is then stored as an outfit suggestion upon return.

(ex. This Vintage band tee would pair well with your dark wash jeans and your combat boots to create the perfect grundge look. The brown leather belt will elevate this combination and further compliment it while providing a darker tone.)

**Step 3:**
<!-- Continue until the full interaction is complete -->
Upon the return of an outfit suggestion, there are two possible situations. If the wardrobe was empty upon calling the previous tool, the outfit suggestion will be stored in the session state for the user to gain inspiration from but this hypothetical outfit will not be passed into the next tool. This is largely since the model lacks the grounding provided by the wardrobe and it lacks context on the users' tastes to create a fully accurate outfit. Seeing this as a possibility for error, to avoid propogating any error, it will not be provided to the next tool.

The create_fit_card tool is then used by providing it a outfit or empty string and the selected item as inputs. If an outfit is not provided, it will create the fit card solely utilizing the selected item as context. Otherwise, the entire outfit and the neccessary selected item information is provided to llama to produce a fit card largely based on the selected item. This fit card string is then returned to the agent.

(ex. I am in love with my vintage band tee today that I paired with my favorite combat boots and brown leather belt. I'm obsessed with the street-wear look and the grunge-classic feel. This band tee is the star of the show and I can't believe that I got it from Depop for only 19 dollars.)

**Final output to user:**
<!-- What does the user actually see at the end? -->
The agent takes all the outputs from every tool and the query parsing into the session state dictionary object. If the model encounters any errors when parsing the query or finding an adequate match with the query, it will show the users the error since it is stored in the session state. Otherwise, the selected item, the outfit or suggested outfit, and the fit card is displayed to the user.
