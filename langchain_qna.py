from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

class QNAAgent:

    def __init__(self, retriever):
        self.llm = ChatOpenAI(model='gpt-4-turbo-preview')
        self.retriever = retriever

        self.contextualize_q_system_prompt = """
        Given a chat history and the latest user question which might reference context in the chat history,
        formulate a standalone question which can be understood without the chat history.
        Do NOT answer the question, just reformulate it if needed and otherwise return it as is.
        """
        self.qa_system_prompt = """
        You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question.
        If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
        {context}
        """

    def format_docs(self, docs):
        """Format documents for display."""
        return "\n\n".join(doc.page_content for doc in docs)

    def contextualized_question(self, input: dict):
        """Contextualize the question based on the chat history."""
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.contextualize_q_system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{question}"),
            ]
        )
        contextualize_q_chain = contextualize_q_prompt | self.llm | StrOutputParser()

        if input.get("chat_history"):
            return contextualize_q_chain
        else:
            return input["question"]

    def execute_rag_chain(self, input: dict):
        """Execute the Retrieve-and-Generate (RAG) chain for answering questions."""
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.qa_system_prompt),
                ("human", "{question}"),
            ]
        )

        rag_chain = (
            RunnablePassthrough.assign(
                context=self.contextualized_question | self.retriever | self.format_docs
            )
            | qa_prompt
            | self.llm
            | StrOutputParser()
        )

        return rag_chain.stream(input)
