from fastapi import FastAPI
from mangum import Mangum

app = FastAPI()

@app.get("/")
def read_root():
    # We add "(Deployed with SAM)" so you know the new code is live
    return {"message": "Hello from Aleena! (Deployed with SAM)"}

@app.get("/cakes")
def list_cakes():
    return {"cakes": ["Chocolate", "Vanilla", "Red Velvet"]}

# This is the handler that SAM and Lambda will run
handler = Mangum(app)