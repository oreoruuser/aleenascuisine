# app/main.py
from fastapi import FastAPI
from mangum import Mangum

# This is your main FastAPI application
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from Aleena's Cuisine API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

# This is the 'handler' object that your template.yaml points to.
# Mangum wraps your FastAPI app so it can run on Lambda.
handler = Mangum(app)