import os, logging
from dotenv import load_dotenv
load_dotenv()
from pydantic import BaseModel, Field, ConfigDict
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from chat import ChatService



class InterestInput(BaseModel):
    model_config = ConfigDict(extra="forbid") # input cannot accept any undefined fields
    interest: str = Field(description="a unique interest")

class UsernameOutput(BaseModel):
    model_config = ConfigDict(frozen=True) # output cannot be altered
    suggestions: list[str] = Field(description="List of three usernames based on interest provided.")


# initialize all values at API startup
@asynccontextmanager 
async def lifespan(app: FastAPI):
    try:
        system_prompt = """
            You are a creative username generator.
            
            INSTRUCTION:
            1. You will receive an interest from the user.
            2. Use that interest to generate three unique and creative usernames.
            3. Do not answer anything beyond generating creative usernames.
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{interest}")
        ])

        llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model="openai/gpt-oss-20b"
        )
        llm_structured_output = llm.with_structured_output(UsernameOutput)
        chain = prompt | llm_structured_output
    
        app.state.chat = ChatService(
            chain=chain
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

@app.post("/api/suggest-username", response_model=UsernameOutput)
def suggest_usernames(input: InterestInput, request: Request):
    try:
        response = app.state.chat.chat(interest=input.interest)
        return response
    
    except Exception as e:
        logging.error("suggest-username failed: %s", e)
        raise HTTPException(status_code=500, detail="internal_error")


@app.exception_handler(Exception)
async def unhandled_error(request: Request, exc: Exception):
    #traceback.print_exc()
    return JSONResponse(status_code=500, content={"detail": "internal_error"})