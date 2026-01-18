from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/healthcheck")
def health():
    return {"status": "healthy"}
