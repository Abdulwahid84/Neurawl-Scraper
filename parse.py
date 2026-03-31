from dotenv import load_dotenv
import os
import requests
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

load_dotenv()

# Configuration
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

try:
    from langchain_ollama import OllamaLLM
    from langchain_core.prompts import ChatPromptTemplate
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    OllamaLLM = None
    ChatPromptTemplate = None

# Initialize model
USE_FALLBACK = os.getenv("USE_FALLBACK", "false").lower() == "true"
model = None

if not USE_FALLBACK and OLLAMA_AVAILABLE:
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        if response.status_code == 200:
            model = OllamaLLM(model=OLLAMA_MODEL, base_url=OLLAMA_URL)
            print(f"✓ Ollama connected at {OLLAMA_URL}")
        else:
            USE_FALLBACK = True
    except Exception as e:
        print(f"⚠️  Ollama unavailable: {e}. Using fallback.")
        USE_FALLBACK = True


def parse_properties(dom_chunks, parse_description):
    """
    Universal intelligent parsing that works with ANY website and ANY query.
    Automatically determines the best output format.
    """
    
    # Step 1: Determine what format the user wants
    if model and not USE_FALLBACK:
        suggested_format = determine_format_with_ai(parse_description)
        print(f"[Parser] Suggested format: {suggested_format}")
        
        if "TABLE" in suggested_format:
            return parse_as_table(dom_chunks, parse_description)
        elif "LIST" in suggested_format:
            return parse_as_list(dom_chunks, parse_description)
        else:
            return parse_as_text(dom_chunks, parse_description)
    else:
        return parse_with_fallback(dom_chunks, parse_description)


def determine_format_with_ai(query):
    """Use AI to determine if results should be TABLE, LIST, or TEXT"""
    if not model:
        return "TEXT"
    
    try:
        template = (
            "The user asked: {query}\n\n"
            "Should the answer be:\n"
            "- TABLE (for structured data like prices, products, listings)\n"
            "- LIST (for multiple unrelated items)\n"
            "- TEXT (for explanations or descriptions)\n\n"
            "Respond with ONLY the word: TABLE or LIST or TEXT"
        )
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | model
        
        result = chain.invoke({"query": query})
        return str(result).strip().upper()
    except:
        return "TEXT"


def parse_as_table(dom_chunks, parse_description):
    """Parse and return data as a table"""
    print(f"[Table Parser] Extracting tabular data...")
    
    if model and not USE_FALLBACK:
        # Use AI to extract structured data
        results = []
        
        template = (
            "Extract data matching: {query}\n"
            "Format each item as: Key1: Value1 | Key2: Value2 | ...\n"
            "Content: {content}\n\n"
            "Return ONLY the formatted data."
        )
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | model
        
        # Process chunks concurrently
        def process_chunk(chunk):
            try:
                result = chain.invoke({
                    "query": parse_description,
                    "content": chunk[:2000]  # Limit chunk size for speed
                })
                return str(result).strip()
            except:
                return None
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(process_chunk, c) for c in dom_chunks[:3]]
            for future in as_completed(futures):
                result = future.result()
                if result and result not in results:
                    results.append(result)
        
        if results:
            return {
                'type': 'table_text',
                'data': '\n'.join(results),
                'count': len(results)
            }
    
    # Fallback: pattern-based extraction
    return extract_structured_data(dom_chunks, parse_description)


def parse_as_list(dom_chunks, parse_description):
    """Parse and return data as a list"""
    print(f"[List Parser] Extracting as list...")
    
    results = extract_with_search(dom_chunks, parse_description)
    
    return {
        'type': 'list',
        'data': '\n'.join(results) if results else "No results found",
        'count': len(results)
    }


def parse_as_text(dom_chunks, parse_description):
    """Parse and return explanatory text"""
    print(f"[Text Parser] Generating analysis...")
    
    if model and not USE_FALLBACK:
        try:
            template = (
                "{query}\n\n"
                "Based on this content, provide a clear answer:\n{content}\n\n"
                "Answer:"
            )
            
            prompt = ChatPromptTemplate.from_template(template)
            chain = prompt | model
            
            # Use first chunk only for speed
            result = chain.invoke({
                "query": parse_description,
                "content": dom_chunks[0][:2000]
            })
            
            text = str(result).strip()
            return {
                'type': 'text',
                'data': text,
                'count': 1
            }
        except Exception as e:
            print(f"[Text Parser] AI failed: {e}")
    
    # Fallback
    results = extract_with_search(dom_chunks, parse_description)
    return {
        'type': 'text',
        'data': '\n'.join(results) if results else "No results found",
        'count': len(results)
    }


def extract_structured_data(dom_chunks, parse_description):
    """Extract structured data using patterns and search"""
    print(f"[Structure Extractor] Finding structured data...")
    
    items = []
    keywords = parse_description.lower().split()
    
    for chunk in dom_chunks[:5]:
        lines = chunk.split('\n')
        for line in lines:
            line = line.strip()
            if not line or len(line) < 15:
                continue
            
            # Check if line contains structured data indicators
            if any(sep in line for sep in ['|', '-', ':', '•', ',']):
                if any(kw in line.lower() for kw in keywords):
                    items.append(line)
    
    if items:
        unique_items = list(dict.fromkeys(items))[:50]
        return {
            'type': 'table_text',
            'data': '\n'.join(unique_items),
            'count': len(unique_items)
        }
    
    return {
        'type': 'text',
        'data': "No structured data found",
        'count': 0
    }


def extract_with_search(dom_chunks, parse_description):
    """Extract relevant content using keyword search"""
    print(f"[Searcher] Searching for relevant content...")
    
    keywords = parse_description.lower().split()
    results = []
    
    for chunk in dom_chunks[:5]:
        lines = chunk.split('\n')
        scored_lines = []
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 5:
                continue
            
            # Score line by keyword matches
            score = sum(1 for kw in keywords if kw in line.lower())
            
            if score > 0:
                scored_lines.append((score, line))
        
        # Sort and get top results from this chunk
        scored_lines.sort(reverse=True, key=lambda x: x[0])
        for _, line in scored_lines[:5]:
            if line not in results:
                results.append(line)
    
    return results[:50]


def parse_with_fallback(dom_chunks, parse_description):
    """Fallback parser using pattern matching and search"""
    print(f"[Fallback Parser] Using pattern matching...")
    
    desc_lower = parse_description.lower()
    
    # Common patterns
    patterns = {
        "email": r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}',
        "phone": r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        "price": r'\$?\d+(?:,\d{3})*(?:\.\d{2})?',
        "url": r'https?://[^\s<>"{}]*',
    }
    
    # Check for specific data types
    results = []
    
    if any(w in desc_lower for w in ["email", "mail"]):
        for chunk in dom_chunks:
            matches = re.findall(patterns["email"], chunk)
            results.extend(list(set(matches)))
    
    if any(w in desc_lower for w in ["phone", "number"]):
        for chunk in dom_chunks:
            matches = re.findall(patterns["phone"], chunk)
            results.extend(list(set(matches)))
    
    if any(w in desc_lower for w in ["price", "cost", "$"]):
        for chunk in dom_chunks:
            matches = re.findall(patterns["price"], chunk)
            results.extend(list(set(matches)))
    
    if any(w in desc_lower for w in ["link", "url", "http"]):
        for chunk in dom_chunks:
            matches = re.findall(patterns["url"], chunk)
            results.extend(list(set(matches)))
    
    # If no specific pattern matched, do semantic search
    if not results:
        results = extract_with_search(dom_chunks, parse_description)
    
    # Determine return type
    if len(results) > 10:
        return {
            'type': 'list',
            'data': '\n'.join(results[:50]),
            'count': len(results)
        }
    elif len(results) > 0:
        return {
            'type': 'text',
            'data': '\n'.join(results),
            'count': len(results)
        }
    else:
        return {
            'type': 'text',
            'data': f"No matches found for: {parse_description}",
            'count': 0
        }




def parse_with_ollama(dom_chunks, parse_description):
    """Direct Ollama parsing (for backward compatibility)"""
    return parse_properties(dom_chunks, parse_description)
