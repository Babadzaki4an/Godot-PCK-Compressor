import uvicorn
from app import App

if __name__ == "__main__":
    uvicorn.run(
        App().app,
        host="127.0.0.1",
        port=2000,
        reload=False
    )