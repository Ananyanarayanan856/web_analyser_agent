from fastapi import FastAPI, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
from playwright.sync_api import sync_playwright

from app.graph import build_graph
from app.database import engine
from app.models import Base

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

agent = build_graph()

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "url": ""})

@app.post("/analyze", response_class=HTMLResponse)
def analyze(request: Request, url: str = Form(...), query: str = Form(...)):

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        result = agent.invoke({
            "user_input": query,
            "url": url,
            "browser": browser,
            "conversation_history": [],
            "intent": None,
            "analysis_types": None,
            "seo_result": None,
            "accessibility_result": None,
            "content_result": None,
            "db_query": None,
            "db_result": None,
            "final_response": None,
            "error": None
        })
        
        browser.close()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "result": result["final_response"],
        "url": url
    })