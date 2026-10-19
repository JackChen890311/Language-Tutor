import streamlit as st
from services.chat_service import StreamCollector

_SKELETON = '<div class="lt-skeleton"><span></span><span></span><span></span></div>'


def stream_with_thinking(collector: StreamCollector) -> None:
    """Show a shimmering placeholder, then stream tokens with a cursor."""
    placeholder = st.empty()
    placeholder.markdown(_SKELETON, unsafe_allow_html=True)

    buf = ""
    for chunk in collector:
        buf += chunk
        placeholder.markdown(buf + "▌")

    placeholder.markdown(buf)


def stream_silently(collector: StreamCollector) -> None:
    """Show a shimmer while draining the stream, without ever displaying its
    content. Use when the streamed text itself must stay hidden (e.g. it
    contains answers/spoilers), unlike stream_with_thinking."""
    placeholder = st.empty()
    placeholder.markdown(_SKELETON, unsafe_allow_html=True)

    for _ in collector:
        pass

    placeholder.empty()
