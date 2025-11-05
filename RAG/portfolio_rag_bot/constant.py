SIMILARITY_SEARCH_QUERY = """
        SELECT content
        FROM portfolio_rag_bot_document
        ORDER BY embedding <=> %s::vector
        LIMIT 4;
    """
