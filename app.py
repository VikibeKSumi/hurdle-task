import os, traceback
import logging
from dotenv import load_dotenv
load_dotenv()
from pydantic import BaseModel, Field
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from chat import Chat



class InterestInput(BaseModel):
    interest: str = Field(description="a unique interest")

class UsernameOutput(BaseModel):
    usernames: list[str] = Field(description="List of three usernames based on interest provided.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        system_prompt = """
            Suggest three unique usernames for the given interest below.
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("history"),
            ("human", "{interest}")
        ])

        llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model="openai/gpt-oss-20b"
        )
        llm_structured_output = llm.with_structured_output(UsernameOutput)
        chain = prompt | llm_structured_output
        conversation_history = {}
        sessions = {}

        app.state.chat = Chat(
            chain=chain,
            conversation_history=conversation_history,
            sessions=sessions
        )
    except Exception as e:
        print(f"An error occured {e}")
        raise
    yield


app = FastAPI(title="Hurdle task", lifespan=lifespan)


@app.get("/")
def home():
    return  {
        "satus": "Page is live"
    }

@app.post("/api/suggest-username")
def get_usernames(input: InterestInput, request: Request):
    try:
        response = app.state.chat.chat(interest=input.interest, session_id="viki")
        return UsernameOutput(usernames=response.model_dump()['usernames'])
    
    except Exception as e:
        logging.error("suggest-username failed: %s", e)
        raise HTTPException(status_code=500, detail="internal_error")


@app.exception_handler(Exception)
async def unhandled_error(request: Request, exc: Exception):
    #traceback.print_exc()
    return JSONResponse(status_code=500, content={"detail": "internal_error"})