import streamlit as st
from services.chat_service import StreamCollector

_THINKING_CSS = """
<style>
@keyframes thinking-bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40%            { transform: scale(1.0); opacity: 1.0; }
}
.thinking-dot {
  display: inline-block;
  width: 8px; height: 8px; border-radius: 50%;
  background: #888;
  margin: 0 2px;
  animation: thinking-bounce 1.2s ease-in-out infinite;
}
.thinking-dot:nth-child(2) { animation-delay: 0.2s; }
.thinking-dot:nth-child(3) { animation-delay: 0.4s; }
</style>
<div style="padding:4px 0">
  <span class="thinking-dot"></span>
  <span class="thinking-dot"></span>
  <span class="thinking-dot"></span>
</div>
"""


def stream_with_thinking(collector: StreamCollector) -> None:
    """Show animated thinking dots, then stream tokens with a cursor."""
    placeholder = st.empty()
    placeholder.markdown(_THINKING_CSS, unsafe_allow_html=True)

    buf = ""
    for chunk in collector:
        buf += chunk
        placeholder.markdown(buf + "▌")

    placeholder.markdown(buf)
