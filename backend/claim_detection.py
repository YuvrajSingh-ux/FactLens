import os
import tempfile
import whisper
from typing import List, Dict, Any
from groq import Groq
from datetime import datetime
import requests
from concurrent.futures import ThreadPoolExecutor

from difflib import SequenceMatcher

def is_similar(a: str, b: str, threshold: float = 0.85):
    return SequenceMatcher(None, a, b).ratio() > threshold

SESSION_STORE = {}

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# def pretty_print_debug(claim, abs_start, abs_end, evidence, verification):
#     print("\n" + "="*50)

#     print("🧾 CLAIM:")
#     print(claim)

#     print("\n⏱️ TIME:")
#     print(f"{abs_start}s → {abs_end}s")

#     print("\n🧠 VERDICT:")
#     print(verification.get("verdict"))
#     print("Reason:", verification.get("summary"))

#     # Wikipedia
#     wiki = evidence.get("wikipedia")
#     print("\n📚 WIKIPEDIA:")
#     if wiki:
#         print("Title:", wiki.get("title"))
#         print("Summary:", (wiki.get("summary") or "")[:300])
#         print("URL:", wiki.get("url"))
#     else:
#         print("No result")

#     # arXiv
#     print("\n📄 ARXIV:")
#     arxiv = evidence.get("arxiv")
#     if arxiv:
#         print(arxiv[:300])
#     else:
#         print("No result")

#     # News
#     print("\n📰 NEWS:")
#     news = evidence.get("news")
#     if news:
#         for i, article in enumerate(news, 1):
#             print(f"{i}. [{article['source']}] {article['title']}")
#             print(f"   {article['url']}")
#     else:
#         print("No result")

#     print("="*50 + "\n")

def pretty_print_debug(claim, abs_start, abs_end, evidence, verification):
    print("\n" + "="*60)

    print("🧾 CLAIM:")
    print(claim)

    print("\n⏱️ TIME:")
    print(f"{abs_start:.2f}s → {abs_end:.2f}s")

    print("\n🧠 VERDICT:")
    print(verification.get("verdict"))
    print("Reason:", verification.get("summary"))

    print("\n📚 WIKIPEDIA:")
    wiki = evidence.get("wikipedia")
    if wiki:
        print("Title:", wiki.get("title"))
        print("Summary:", (wiki.get("summary") or "")[:300])
        print("URL:", wiki.get("url"))
    else:
        print("No result")

    print("\n🌐 SERPAPI (Top Results):")
    serp = evidence.get("serpapi")
    if serp:
        for i, r in enumerate(serp[:3], 1):
            print(f"{i}. {r.get('title')}")
            print(f"   {r.get('link')}")
            print(f"   Snippet: {r.get('snippet')}\n")
    else:
        print("No result")

    print("\n🤖 TAVILY:")
    tavily = evidence.get("tavily")
    if tavily:
        for i, r in enumerate(tavily[:3], 1):
            print(f"{i}. {r.get('title')}")
            print(f"   {r.get('url')}")
            print(f"   Summary: {r.get('content')[:200]}\n")
    else:
        print("No result")

    print("="*60 + "\n")

def search_wikipedia(query: str):
    try:
        search_url = "https://en.wikipedia.org/w/api.php"

        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json"
        }

        search_res = requests.get(search_url, params=params, timeout=5).json()

        if not search_res["query"]["search"]:
            return None

        title = search_res["query"]["search"][0]["title"]

        summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
        summary_res = requests.get(summary_url, timeout=5).json()

        return {
            "title": summary_res.get("title"),
            "summary": summary_res.get("extract"),
            "url": summary_res.get("content_urls", {}).get("desktop", {}).get("page")
        }

    except:
        return None


# def search_arxiv(query: str):
#     try:
#         url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results=1"
#         return requests.get(url, timeout=5).text[:1000]
#     except:
#         return None

def search_serpapi(query: str):
    try:
        url = "https://serpapi.com/search"

        params = {
            "q": query,
            "api_key": SERPAPI_KEY,
            "num": 3
        }

        res = requests.get(url, params=params, timeout=5).json()

        results = []
        for r in res.get("organic_results", []):
            results.append({
                "title": r.get("title"),
                "link": r.get("link"),
                "snippet": r.get("snippet")
            })

        return results

    except:
        return None

# def search_news(query: str):
#     try:
#         url = f"https://newsapi.org/v2/everything?q={query}&apiKey={NEWS_API_KEY}&pageSize=2"
#         res = requests.get(url, timeout=5).json()

#         return [
#             {
#                 "title": a["title"],
#                 "source": a["source"]["name"],
#                 "url": a["url"]
#             }
#             for a in res.get("articles", [])
#         ]
#     except:
#         return None

def search_tavily(query: str):
    try:
        url = "https://api.tavily.com/search"

        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "search_depth": "advanced",
            "max_results": 3
        }

        res = requests.post(url, json=payload, timeout=5).json()

        return res.get("results")

    except:
        return None

# def fetch_evidence_parallel(claim: str):
#     with ThreadPoolExecutor() as executor:
#         wiki = executor.submit(search_wikipedia, claim)
#         arxiv = executor.submit(search_arxiv, claim)
#         news = executor.submit(search_news, claim)

#         return {
#             "wikipedia": wiki.result(),
#             "arxiv": arxiv.result(),
#             "news": news.result()
#         }

def fetch_evidence_parallel(claim: str):
    with ThreadPoolExecutor() as executor:
        wiki = executor.submit(search_wikipedia, claim)
        serp = executor.submit(search_serpapi, claim)
        tavily = executor.submit(search_tavily, claim)

        return {
            "wikipedia": wiki.result(),
            "serpapi": serp.result(),
            "tavily": tavily.result()
        }

def verify_claim_with_llm(claim, evidence, groq_api_key, context=""):
    client = Groq(api_key=groq_api_key)

    prompt = f"""
You are a fact-checking system.

Determine if the evidence SUPPORTS, CONTRADICTS, or is INCONCLUSIVE to the claim.
Do not rely on YouTube based evidence.

Return JSON ONLY:
{{
  "verdict": "SUPPORT | CONTRADICT | INCONCLUSIVE",
  "summary": "short explanation"
}}

Do not add explanations before or after JSON.

CLAIM:
{claim}

CONTEXT:
{context}

EVIDENCE:
Wikipedia: {str(evidence.get("wikipedia"))[:500]}

SerpAPI Results:
{str(evidence.get("serpapi"))[:500]}

Tavily Results:
{str(evidence.get("tavily"))[:500]}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0.1,
        messages=[
            {"role": "system", "content": "You are a precise fact-checker."},
            {"role": "user", "content": prompt}
        ],
    )

    import json
    import re

    content = response.choices[0].message.content

    try:
        match = re.search(r'\{.*\}', content, re.DOTALL)

        if match:
            return json.loads(match.group(0))
        else:
            raise ValueError("No JSON found")

    except Exception as e:
        print("JSON PARSE ERROR:", content)

        return {
            "verdict": "INCONCLUSIVE",
            "summary": "Parsing failed"
        }

DEBUG_DIR = "debug_audio"
os.makedirs(DEBUG_DIR, exist_ok=True)

_WHISPER_MODEL = whisper.load_model("base")


def _save_audio_bytes_to_tempfile(audio_bytes: bytes, suffix=".wav") -> str:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(audio_bytes)
    tmp.close()
    return tmp.name


def process_audio_bytes_for_claims(
    audio_bytes: bytes,
    chunk_start_time: float,
    groq_api_key: str = None,
    model_name: str = "llama-3.3-70b-versatile",
    session_id: str = None
) -> Dict[str, Any]:

    if groq_api_key is None:
        groq_api_key = os.getenv("GROQ_API_KEY")

    if not groq_api_key:
        raise ValueError("GROQ_API_KEY is not set")
    
    if session_id not in SESSION_STORE:
        SESSION_STORE[session_id] = {
            "context": [],
            "claims": []   
        }

    audio_path = _save_audio_bytes_to_tempfile(audio_bytes, suffix=".wav")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    # # 🔥 Save debug copy
    # debug_wav_path = os.path.join(DEBUG_DIR, f"chunk_{timestamp}.wav")
    # with open(debug_wav_path, "wb") as f:
    #     f.write(audio_bytes)

    # print(f"Saved WAV chunk: {debug_wav_path}")

    try:
        result = _WHISPER_MODEL.transcribe(
            audio_path,
            fp16=False,
            language="en",
        )

        segments = result.get("segments", [])

        client = Groq(api_key=groq_api_key)

        claims_list: List[Dict[str, Any]] = []

        for i, seg in enumerate(segments):
            abs_start = round(chunk_start_time + float(seg["start"]), 3)
            abs_end = round(chunk_start_time + float(seg["end"]), 3)
            text = seg["text"].strip()
            SESSION_STORE[session_id]["context"].append(text)

            
            SESSION_STORE[session_id]["context"] = SESSION_STORE[session_id]["context"][-5:]

            context_text = " ".join(SESSION_STORE[session_id]["context"])
            prompt = f"""
            You are a factual claim extraction system.

            Your task is to extract statements that are:
            - Checkable (can be verified as true or false)
            - About real-world facts, events, or assertions

            IMPORTANT:
            - Mentions of public figures, countries, or organizations are allowed.
            - Even if a claim might be false, extract it if it is verifiable.

            AVOID extracting:
            - Pure opinions or personal beliefs
            - Jokes, sarcasm, or figurative language
            - Very vague or generic statements

            GUIDELINES:
            - Claims can be general statements if they can be fact-checked
            - Claims may include uncertainty (e.g., "reportedly", "allegedly")
            - Do NOT over-filter — prefer extracting a claim if unsure

            If there is NO claim, reply EXACTLY:
            NO_CLAIM

            Use CONTEXT to resolve references like "he", "she", "they", etc.
            
            CONTEXT:
            {context_text}
            CURRENT TEXT:
            "{text}"

            If there is a claim:
            - Return ONLY the cleaned claim
            - Keep it in one sentence
            - Do NOT add explanations
            """

            response = client.chat.completions.create(
                model=model_name,
                temperature=0.1,
                messages=[
                    {"role": "system", "content": "You are a precise claim detector."},
                    {"role": "user", "content": prompt}
                ],
            )

            model_reply = response.choices[0].message.content.strip()
            has_claim = not model_reply.startswith("NO_CLAIM")

            if has_claim and len(model_reply.split()) > 5:
                new_claim = model_reply.strip().lower()

                duplicate = False
                for prev in SESSION_STORE[session_id]["claims"]:
                    if is_similar(prev, new_claim):
                        duplicate = True
                        break

                if duplicate:
                    print("🔁 DUPLICATE SKIPPED:", model_reply)
                    continue

                SESSION_STORE[session_id]["claims"].append(new_claim)
                evidence = fetch_evidence_parallel(model_reply)

                verification = verify_claim_with_llm(
                    model_reply,
                    evidence,
                    groq_api_key,
                    context=context_text    
                )
                pretty_print_debug(
                    model_reply,
                    abs_start,
                    abs_end,
                    evidence,
                    verification
                )
                claims_list.append({
                    "start_time": abs_start,
                    "end_time": abs_end,
                    "claim": model_reply,
                    "verification": verification,
                    "sources": evidence
                })

        return {
            "claims": claims_list
        }

    except Exception as e:
        print("Processing error:", e)
        return {
            "chunk_start_time": chunk_start_time,
            "error": str(e),
            "segments": []
        }

    finally:
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except Exception as e:
                print(f"Cleanup warning: {e}")