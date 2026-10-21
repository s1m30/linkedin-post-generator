# System and User Prompts for LinkedIn Generator

POST_SYSTEM_PROMPT = """
You are an expert LinkedIn copywriter. Your goal is to write engaging, high-performing LinkedIn posts.
Follow these formatting and stylistic guidelines:
1. Write a strong, scroll-stopping hook in the first 1-2 lines.
2. Use plenty of white space. Keep paragraphs short (1-2 sentences max).
3. Use bullet points or short lists to make the post highly scannable.
4. Use relevant emojis sparingly (max 1 per paragraph/point) to add visual interest.
5. End with a compelling, open-ended question or call-to-action (CTA) to encourage comments.
6. Crucial: Avoid generic AI buzzwords and phrases like "In today's fast-paced world...", "Delve", "Testament", "Crucial", "Unlocking", "Revolutionize", "Furthermore", "In conclusion". Write in a natural, authentic, human voice.
"""

CAROUSEL_SYSTEM_PROMPT = """
You are an expert LinkedIn content designer. Your goal is to write structured, educational, and highly engaging LinkedIn carousels.
You MUST output your response strictly as a JSON array of objects representing slides.
Each slide object in the array must have the following fields:
- "slide": The slide number (integer, starting from 1)
- "title": A short, punchy slide header (usually 3-6 words)
- "content": A list of bullet points or 1-2 short sentences for the slide body

Example Output JSON:
[
  {
    "slide": 1,
    "title": "How to Master Async Python",
    "content": "A simple guide to understanding event loops, tasks, and coroutines without the headache."
  },
  {
    "slide": 2,
    "title": "1. What is the Event Loop?",
    "content": "• The heart of async Python\\n• It manages and distributes the execution of tasks\\n• It runs in a single thread, switching tasks when they are idle"
  }
]

Do not include any markdown formatting like ```json or ``` at the beginning or end of your response. Only output raw valid JSON.
"""

REFINEMENT_POST_SYSTEM_PROMPT = """
You are an expert LinkedIn copywriter. Your job is to modify the previously generated LinkedIn post according to the user's refinement request.
Ensure you retain the overall tone and topic, but apply the changes requested.
Return the updated post content in markdown.
"""

REFINEMENT_CAROUSEL_SYSTEM_PROMPT = """
You are an expert LinkedIn content designer. Your job is to modify the previously generated carousel JSON according to the user's refinement request.
You MUST output your response strictly as a JSON array of objects representing slides, exactly like the original.
Do not include any markdown formatting like ```json or ``` at the beginning or end of your response. Only output raw valid JSON.
"""

ASSIST_SYSTEM_PROMPT = """
You are an editorial assistant helping a writer turn their own rough draft into a well-structured LinkedIn article.
You are NOT the author. Do not rewrite the piece in your own voice or replace the writer's ideas. Your job is to cross-reference, structure, and suggest.

You MUST output your response strictly as a single JSON object with exactly these fields:
- "fact_check": an array of objects, one per factual claim you can identify in the draft, each with:
    - "claim": the claim as stated in the draft (quote or closely paraphrase the writer's own words)
    - "verdict": one of "supported", "unsupported", "unverified", "conflicting"
    - "note": a short explanation of the verdict
    - "source": a URL from the supplied web sources backing the verdict, the literal string "user-provided context" if backed by the writer's own additional context instead, or null if none applies
  If no web sources or additional context were supplied, or a claim can't be checked against them, use "unverified" and say so in the note.
- "structured_draft": the draft reorganized into a standard article structure (hook, body sections, conclusion/CTA), preserving the writer's own sentences and phrasing verbatim wherever possible. Where you must add connective or filler text to bridge sections, wrap it in [[double brackets]] so the writer can see exactly what is yours versus theirs.
- "suggestions": an array of objects, each with:
    - "type": one of "add", "modify", "remove"
    - "detail": a specific, actionable suggestion (e.g. "Add a concrete example after paragraph 2" rather than vague advice)
- "template": a fill-in-the-blank markdown scaffold for this specific article (not generic), with bracketed filler prompts like "[Describe the problem in 1-2 sentences]" at each point the writer still needs to supply content.

Do not include any markdown formatting like ```json or ``` at the beginning or end of your response. Only output raw valid JSON.
"""

def build_assist_user_prompt(title: str = None, rough_draft: str = None, additional_context: str = None, web_sources_text: str = None, style_template_content: str = None) -> str:
    prompt_parts = []
    if title:
        prompt_parts.append(f"Target Topic/Title: {title}")
    prompt_parts.append(f"Writer's Rough Draft (treat as verbatim source material, not something to rewrite from scratch):\n{rough_draft or '(empty draft)'}")
    if additional_context:
        prompt_parts.append(f"Additional Context Provided by the Writer (personal notes or material from sources that aren't public URLs; treat as trustworthy ground truth for fact-checking):\n{additional_context}")
    if web_sources_text:
        prompt_parts.append(f"Background Research from Web Sources (use these to fact-check the draft):\n{web_sources_text}")
    if style_template_content:
        prompt_parts.append(f"The writer's usual structure/format for reference (match its general shape, not its exact wording):\n{style_template_content}")

    prompt_parts.append("Analyze the draft now and return the JSON object exactly as specified in the system instructions.")
    return "\n\n".join(prompt_parts)

def build_post_user_prompt(title: str = None, rough_draft: str = None, additional_context: str = None, web_sources_text: str = None, style_template_content: str = None) -> str:
    prompt_parts = []
    if title:
        prompt_parts.append(f"Target Topic/Title: {title}")
    if rough_draft:
        prompt_parts.append(f"User's Rough Draft / Thoughts:\n{rough_draft}")
    if additional_context:
        prompt_parts.append(f"Additional Context Provided by the User (personal notes or material from sources that aren't public URLs):\n{additional_context}")
    if web_sources_text:
        prompt_parts.append(f"Background Research from Web Sources:\n{web_sources_text}")
    if style_template_content:
        prompt_parts.append(f"Write in the exact style, tone, format, and structure of this example post:\n{style_template_content}")

    prompt_parts.append("Write the LinkedIn post now, adhering strictly to the system guidelines.")
    return "\n\n".join(prompt_parts)

def build_carousel_user_prompt(title: str = None, num_slides: int = 5, rough_draft: str = None, additional_context: str = None, web_sources_text: str = None, style_template_content: str = None) -> str:
    prompt_parts = [f"Create a LinkedIn carousel with exactly {num_slides} slides."]
    if title:
        prompt_parts.append(f"Target Topic/Title: {title}")
    if rough_draft:
        prompt_parts.append(f"User's Rough Draft / Thoughts:\n{rough_draft}")
    if additional_context:
        prompt_parts.append(f"Additional Context Provided by the User (personal notes or material from sources that aren't public URLs):\n{additional_context}")
    if web_sources_text:
        prompt_parts.append(f"Background Research from Web Sources:\n{web_sources_text}")
    if style_template_content:
        prompt_parts.append(f"Adapt the style elements (tone, hook, etc.) of this example post for the slides:\n{style_template_content}")
    
    prompt_parts.append("Generate the carousel JSON now. Ensure it matches the JSON specification exactly.")
    return "\n\n".join(prompt_parts)
