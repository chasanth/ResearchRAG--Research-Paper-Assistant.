import os
from langchain_groq import ChatGroq

def get_answer(vector_db, question):
    """Retrieve relevant chunks and ask the LLM to answer using them."""

    # Step 1: Retrieve the most relevant chunks for this question
    retriever = vector_db.as_retriever(search_kwargs={"k": 4})
    docs = retriever.invoke(question)

    # Step 2: Combine retrieved chunks into one context block
    context = "\n\n".join(doc.page_content for doc in docs)

    # Step 3: Build the prompt
    prompt = f"""You are a helpful research assistant. Answer the question
using ONLY the context below. If the answer isn't in the context, say so.

Context:
{context}

Question: {question}

Answer:"""

    # Step 4: Call the LLM
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        api_key=os.getenv("GROQ_API_KEY")
    )
    response = llm.invoke(prompt)

    return response.content, docs