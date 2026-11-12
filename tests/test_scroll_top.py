import ui.components.scroll_top as scroll_top


def test_scroll_button_sets_pending_flag(monkeypatch):
    state = {}
    monkeypatch.setattr(scroll_top.st, "session_state", state)
    monkeypatch.setattr(scroll_top.st, "button", lambda *args, **kwargs: True)
    monkeypatch.setattr(scroll_top.st, "rerun", lambda: None)

    scroll_top.scroll_to_top_button()

    assert state[scroll_top._FLAG] is True


def test_apply_pending_scroll_renders_script_once(monkeypatch):
    state = {scroll_top._FLAG: True}
    calls = []
    monkeypatch.setattr(scroll_top.st, "session_state", state)
    monkeypatch.setattr(scroll_top.st, "html", lambda body, **kwargs: calls.append((body, kwargs)))

    scroll_top.apply_pending_scroll_to_top()

    assert scroll_top._FLAG not in state
    assert len(calls) == 1
    body, kwargs = calls[0]
    assert "stAppScrollToBottomContainer" in body
    assert kwargs["unsafe_allow_javascript"] is True

    scroll_top.apply_pending_scroll_to_top()
    assert len(calls) == 1
