import os
from langchain_groq import ChatGroq

def get_answer(vector_db, question):
    """Retrieve relevant chunks and ask the LLM to answer using them."""

    # Step 1: Retrieve more chunks for richer context
    retriever = vector_db.as_retriever(search_kwargs={"k": 6})
    docs = retriever.invoke(question)

    # Step 2: Combine retrieved chunks into one labeled context block
    context = "\n\n".join(
        f"[Source: page {doc.metadata.get('page', '?')}]\n{doc.page_content}"
        for doc in docs
    )

    # Step 3: Build a stronger, more directive prompt
    prompt = f"""You are an expert research assistant helping a reader deeply understand an academic paper.

Use ONLY the context below to answer the question. Do not use outside knowledge.

Guidelines:
- Give a thorough, well-structured answer — do not just give a one-line summary.
- Explain the reasoning or details behind the answer, not just the conclusion.
- If the context includes multiple relevant points, cover all of them.
- Use bullet points or short paragraphs if that helps clarity.
- If the answer isn't fully supported by the context, say what's missing rather than guessing.
- Do not repeat the question back, and do not mention "the context" explicitly — just answer naturally as if explaining to the reader.

Context:
{context}

Question: {question}

Detailed Answer:"""

    # Step 4: Call the LLM
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        api_key=os.getenv("GROQ_API_KEY")
    )
    response = llm.invoke(prompt)

    return response.content, docs