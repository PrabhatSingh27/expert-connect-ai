from fastapi import FastAPI

app = FastAPI(
    title="Expert Connect AI",
    version="1.0.0"
)

@app.get("/")
def root():
    return {
        "message": "Expert Connect AI Backend Running"
    }