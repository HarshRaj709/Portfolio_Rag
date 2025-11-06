import os
from django.conf import settings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from .models import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from django.db import connection
from datetime import datetime
from .constant import SIMILARITY_SEARCH_QUERY


class SupabaseRAG:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GEMINI_API_KEY,
            streaming=True
        )
        self.dimension = 384

    def ingest(self, file_path="personal_info.md"):
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=40)
        chunks = splitter.split_text(text)

        # Delete old docs
        Document.objects.all().delete()

        # Embed & save
        vectors = self.embeddings.embed_documents(chunks)
        docs = [
            Document(content=chunk, embedding=vec)
            for chunk, vec in zip(chunks, vectors)
        ]
        Document.objects.bulk_create(docs)
        print(f"✅ Ingested {len(docs)} chunks into Supabase")

    def stream_query(self, question: str):
        # 1. Embed question
        # q_vec = self.embeddings.embed_query(question)

        try:
            q_vec = self.embeddings.embed_query(question)  # this returns the vector
        except Exception as e:
            raise RuntimeError(f"Failed to embed query: {e}")

        # 2. Raw SQL similarity search (top 4)
        try:
            with connection.cursor() as cursor:
                cursor.execute(SIMILARITY_SEARCH_QUERY, [q_vec])
                rows = cursor.fetchall()  # It returns the content stored in vector db which are closest to the question.
        except Exception as e:
            raise RuntimeError(f"Database similarity search failed: {e}")

        context = "\n\n".join(
            row[0] for row in rows) if rows else "No relevant information found."  # just connecting the rows

        # 3. Prompt with dynamic date
        today = datetime.now().strftime("%B %d, %Y")
        prompt = ChatPromptTemplate.from_template(f"""
            You are **Harsh Sahu**, a Python Backend Developer and SDE-1 at ScaleReal Technologies.  
            You are **NOT an AI assistant** — you are the real person behind this portfolio.  
            Answer **only as Harsh**, in first person ("I", "my", "me").  
            Today is {today}.  

            Use the context to answer naturally.  
            If the answer isn't in the context, say: "I haven't shared that detail yet."  
            **Never say you're an AI, don't exist, or live in the cloud.**

            Context: {context}
            Question: {question}

            Answer (friendly, concise, in first person):
            """)


        # 4. Streaming chain
        chain = (
                {"context": lambda x: context, "question": RunnablePassthrough()}
                | prompt
                | self.llm
                | StrOutputParser()  # converts the output stream into text.
        )

        # return chain.stream(question)
        # 5️⃣ Stream the model output (generator)
        try:
            for chunk in chain.stream(question):
                yield chunk  # yields token-by-token or chunk-by-chunk text
        except Exception as e:
            raise RuntimeError(f"Streaming response failed: {e}")

    