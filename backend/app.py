from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
from typing import List, Dict, Any, Optional
import random

app = FastAPI(title="Exam System API")

# Configure CORS to allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to JSON source files
import os

# Use an absolute path to ensure we find the source_jsons directory
# Calculate the absolute path more reliably
script_dir = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(script_dir)
SOURCE_JSON_DIR = os.path.join(BASE_DIR, "source_jsons")

print(f"Backend starting. Looking for JSON files in: {SOURCE_JSON_DIR}")
print(f"Directory exists: {os.path.exists(SOURCE_JSON_DIR)}")
if os.path.exists(SOURCE_JSON_DIR):
    print(f"Files in directory: {os.listdir(SOURCE_JSON_DIR)}")

class Answer(BaseModel):
    question_id: int
    domain: str
    selected_option: str

class ExamConfig(BaseModel):
    domains: List[str] = []
    question_count: int = 10
    randomize: bool = True

# Cache for loaded questions to avoid reading files on every request
question_cache: Dict[str, Any] = {}

def load_questions():
    """Load all question files from source_jsons directory"""
    global question_cache
    
    # Clear cache when reloading
    question_cache = {}
    
    if not os.path.exists(SOURCE_JSON_DIR):
        os.makedirs(SOURCE_JSON_DIR)
        print(f"Created directory: {SOURCE_JSON_DIR}")
        return
    
    print(f"Searching for JSON files in: {SOURCE_JSON_DIR}")
    files = os.listdir(SOURCE_JSON_DIR)
    print(f"Found {len(files)} files in directory: {files}")
    
    for filename in files:
        if filename.endswith('.json'):
            try:
                file_path = os.path.join(SOURCE_JSON_DIR, filename)
                print(f"Loading file: {file_path}")
                
                with open(file_path, 'r') as f:
                    file_content = f.read()
                    print(f"File content preview: {file_content[:100]}...")
                    
                    data = json.loads(file_content)
                    domain = data.get('domain', os.path.splitext(filename)[0])
                    questions = data.get('questions', [])
                    
                    if not questions:
                        print(f"Warning: No questions found in {filename}")
                    
                    question_cache[domain] = questions
                    print(f"Successfully loaded {len(questions)} questions from {filename} for domain '{domain}'")
            except Exception as e:
                print(f"Error loading {filename}: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Load questions on startup"""
    load_questions()

@app.get("/domains")
async def get_domains():
    """Get list of available domains"""
    return {"domains": list(question_cache.keys())}

@app.post("/exam")
async def create_exam(config: ExamConfig):
    """Create an exam based on config"""
    # Reload questions to pick up any new files
    load_questions()
    
    # If no domains specified, use all available domains
    domains_to_use = config.domains if config.domains else list(question_cache.keys())
    
    # Check if domains exist
    for domain in domains_to_use:
        if domain not in question_cache:
            raise HTTPException(status_code=404, detail=f"Domain '{domain}' not found")
    
    # Collect questions from specified domains
    all_questions = []
    for domain in domains_to_use:
        domain_questions = question_cache.get(domain, [])
        for q in domain_questions:
            # Add domain information to each question
            q_copy = q.copy()
            q_copy["domain"] = domain
            # Remove answer and explanation from the question
            answer = q_copy.pop("answer", None)
            explanation = q_copy.pop("explanation", None)
            all_questions.append(q_copy)
    
    # Randomize if requested
    if config.randomize:
        random.shuffle(all_questions)
    
    # Limit to requested count
    limited_questions = all_questions[:config.question_count]
    
    return {"questions": limited_questions}

@app.post("/check-answer")
async def check_answer(answer: Answer):
    """Check if the answer is correct and return explanation"""
    domain = answer.domain
    question_id = answer.question_id
    selected_option = answer.selected_option
    
    if domain not in question_cache:
        raise HTTPException(status_code=404, detail=f"Domain '{domain}' not found")
    
    # Find the question
    question = None
    for q in question_cache[domain]:
        if q["id"] == question_id:
            question = q
            break
    
    if not question:
        raise HTTPException(status_code=404, detail=f"Question with ID {question_id} not found")
    
    correct_answer = question.get("answer")
    explanation = question.get("explanation", "No explanation provided")
    is_correct = selected_option == correct_answer
    
    return {
        "is_correct": is_correct,
        "correct_answer": correct_answer,
        "explanation": explanation
    }

@app.get("/reload")
async def reload_questions():
    """Force reload all question files"""
    load_questions()
    return {"status": "success", "message": "Questions reloaded", "domains": list(question_cache.keys())}

# If running directly, start the app with Uvicorn
if __name__ == "__main__":
    import uvicorn
    # Listen on all network interfaces (0.0.0.0) instead of just localhost
    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True)