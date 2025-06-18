from fastapi import FastAPI
import os
from dotenv import load_dotenv

load_dotenv()
PORT = int(os.getenv("PORT"))

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("app:app", host="0.0.0.0", port=PORT, reload=True)
