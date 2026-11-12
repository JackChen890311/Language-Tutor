import streamlit as st

_FLAG = "_lt_scroll_to_top"

# The app's main scroll container is Streamlit's
# section[data-testid="stAppScrollToBottomContainer"]. We also scroll the
# document for safety, and repeat after a short delay because Streamlit may
# restore its chat scroll position after a rerun.
_SCROLL_SCRIPT = """
<script>
(function () {
  const toTop = () => {
    const main = document.querySelector(
      'section[data-testid="stAppScrollToBottomContainer"]'
    );
    if (main) main.scrollTo({ top: 0, behavior: "smooth" });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };
  requestAnimationFrame(toTop);
  setTimeout(toTop, 150);
  setTimeout(toTop, 500);
})();
</script>
"""


def scroll_to_top_button(key: str = "scroll_to_top") -> None:
    """Render a compact button that asks the next render to scroll to the top."""
    if st.button("⬆️", key=key, help="Back to top", type="tertiary"):
        st.session_state[_FLAG] = True
        st.rerun()


def apply_pending_scroll_to_top() -> None:
    """Run the scroll script once after a scroll-to-top button click."""
    if st.session_state.pop(_FLAG, False):
        st.html(_SCROLL_SCRIPT, unsafe_allow_javascript=True)
