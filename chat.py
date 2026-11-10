from langchain_core.runnables import Runnable

class Chat():
    def __init__(
            self,
            chain: Runnable,
        ):
        self.chain = chain

    def get_chain(self, interest: str):
        return self.chain.invoke(input={"interest": interest})

    def chat(self, interest: str):
        response = self.get_chain(interest=interest)
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
    )
    print(chat.chat(interest="puppies").model_dump(mode='json')["usernames"])
