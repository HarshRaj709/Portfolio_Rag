# from rest_framework.views import APIView
# from rest_framework.response import Response
# from django.http import StreamingHttpResponse
# from portfolio_rag_bot.rag_pipeline import SupabaseRAG
# import json
#
#
# class ChatStreamView(APIView):
#     def post(self, request):
#         query = request.data.get("query", "").strip()
#         if not query:
#             return Response({"error": "Query required"}, status=400)
#
#         rag = SupabaseRAG()
#
#         def event_stream():
#             for token in rag.stream_query(query):
#                 yield f"data: {json.dumps({'token': token})}\n\n"
#             yield "data: [DONE]\n\n"
#
#         return StreamingHttpResponse(
#             event_stream(),
#             content_type="text/event-stream"
#         )


from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import StreamingHttpResponse
from django.utils.encoding import smart_str
from portfolio_rag_bot.rag_pipeline import SupabaseRAG
import json
import logging

logger = logging.getLogger(__name__)


class ChatStreamView(APIView):
    """Streams AI-generated responses (token-by-token) using Server-Sent Events."""

    def post(self, request):
        query = request.data.get("query", "").strip()
        if not query:
            return Response({"error": "Query is required."}, status=400)

        try:
            rag = SupabaseRAG()
        except Exception as e:
            logger.exception("Failed to initialize RAG pipeline")
            return Response({"error": f"Initialization failed: {str(e)}"}, status=500)

        def event_stream():
            """Generator that streams AI tokens as SSE events."""
            try:
                for token in rag.stream_query(query):
                    # Ensure token is safely JSON-encoded and newline-separated
                    chunk = json.dumps({"token": smart_str(token)})
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                logger.exception("Error during streaming response")
                error_chunk = json.dumps({"error": str(e)})
                yield f"data: {error_chunk}\n\n"
                yield "data: [DONE]\n\n"

        # Create a streaming HTTP response compatible with EventSource
        response = StreamingHttpResponse(
            streaming_content=event_stream(),
            content_type="text/event-stream",
        )

        # Recommended headers for SSE
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"  # disable buffering in nginx/gunicorn
        response["Connection"] = "keep-alive"
        return response


#daphne RAG.asgi:application