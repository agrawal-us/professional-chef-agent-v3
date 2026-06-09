from fastapi import FastAPI

app = FastAPI(title="Professional Chef Agent API")


@app.get("/")
async def root():
    return {"status": "ok", "message": "Professional Chef Agent API"}
