
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import Runnable
class Chat():
    def __init__(
            self,
            chain: Runnable,
            conversation_history: dict,
            sessions: dict,
        ):
        self.chain = chain
        self.conversation_history = conversation_history
        self.sessions = sessions

    def get_chain(self, interest: str, session_id: str):
        self.conversation_history = self.sessions.setdefault(session_id, [])
        return self.chain.invoke({"history": self.conversation_history, "interest": interest})

    def chat(self, interest: str, session_id: str):
        response = self.get_chain(interest=interest, session_id=session_id)
        self.conversation_history.append(HumanMessage(content=interest))
        self.conversation_history.append(AIMessage(content=response.model_dump_json()))
        return response


if __name__ == "__main__":
    from pydantic import Field, BaseModel
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_openai import ChatOpenAI 
    import os
    from dotenv import load_dotenv
    load_dotenv()

    class UsernameOutput(BaseModel):
        usernames: list[str] = Field(description="List of three usernames based on interest provided.")


    system_prompt = """
        Generate three username based on the given interest.
        {interest}
    """
    prompt = ChatPromptTemplate([
        ("system", system_prompt),
        MessagesPlaceholder("history"),
        ("human", "{interest}")
    ])
    llm = ChatOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        model='gpt-5.4-mini'
    )
    llm_structured_output = llm.with_structured_output(UsernameOutput)
    chain = prompt | llm_structured_output
    chat = Chat(
        chain=chain,
        conversation_history={},
        sessions={},
    )
    print(chat.chat(interest="puppies", session_id="123").model_dump(mode='json')["usernames"])
