import html

import streamlit as st

from ui import theme
from ui.components.audio_controls import autoplay_audio_html
from ui.state import get

_SORT_OPTIONS = {
    "Newest first": "newest",
    "Oldest first": "oldest",
    "A → Z": "az",
    "Z → A": "za",
    "Most reviewed": "most_reviewed",
}

_REVIEW_OPTIONS = {
    "All": "all",
    "Due": "due",
    "Never reviewed": "never",
    "Reviewed": "reviewed",
}


def _has_kanji(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" or "\u3400" <= ch <= "\u4dbf" for ch in text)


def _esc(text: object) -> str:
    return html.escape(str(text))


def render() -> None:
    language_svc = get("language_svc")
    native_lang, target_lang = language_svc.get_language_pair()
    word_svc = get("word_svc")

    theme.page_header(
        "📚",
        "Word List",
        "Everything you saved, enriched with readings, examples and review stats.",
    )

    section = st.segmented_control(
        "Section",
        ["Browse", "Add Word", "Review"],
        default="Browse",
        key="wordlist_section",
        label_visibility="collapsed",
    )
    if section is None:
        section = "Browse"

    if section == "Browse":
        _render_browse(word_svc, target_lang, native_lang)
    elif section == "Add Word":
        _render_add(word_svc, target_lang, native_lang)
    else:
        _render_review(word_svc, target_lang, native_lang)


def _render_browse(word_svc, target_lang: str, native_lang: str) -> None:
    all_words = word_svc.get_all_words(target_lang)
    if not all_words:
        theme.empty_state(
            "🌱",
            "No words saved yet",
            "Save suggestions from Chat or Lesson, or add a word manually.",
        )
        return

    all_tags = sorted({tag for w in all_words for tag in w.get("tags", [])})
    levels = sorted(
        {
            w["proficiency_level"]
            for w in all_words
            if w.get("proficiency_level") and w["proficiency_level"] != "-"
        }
    )

    with st.container(key="ltcard_filters"):
        search_col, sort_col = st.columns([2, 1])
        with search_col:
            query = st.text_input("Search", placeholder="🔍  Search words…", key="wordlist_search")
        with sort_col:
            sort_label = st.selectbox(
                "Sort by",
                list(_SORT_OPTIONS),
                key="wordlist_sort",
                help="Alphabetical order follows the reading when one exists.",
            )

        if len(levels) > 1:
            filter_col1, filter_col2 = st.columns(2)
            with filter_col1:
                status_label = st.pills(
                    "Review status",
                    list(_REVIEW_OPTIONS),
                    default="All",
                    key="wordlist_status",
                    help="Due = never reviewed or not reviewed in the last 7 days.",
                )
            with filter_col2:
                level_label = st.pills(
                    "Level", ["All"] + levels, default="All", key="wordlist_level"
                )
        else:
            status_label = st.pills(
                "Review status",
                list(_REVIEW_OPTIONS),
                default="All",
                key="wordlist_status",
                help="Due = never reviewed or not reviewed in the last 7 days.",
            )
            level_label = "All"

        selected_tag = "All"
        if all_tags:
            picked = st.pills("Tags", ["All"] + all_tags, default="All", key="wordlist_tag")
            selected_tag = picked or "All"

    words = word_svc.browse(
        target_lang,
        query=query or "",
        tag=selected_tag,
        level=level_label or "All",
        review_status=_REVIEW_OPTIONS.get(status_label or "All", "all"),
        sort=_SORT_OPTIONS.get(sort_label or "Newest first", "newest"),
    )

    if not words:
        theme.empty_state(
            "🔍",
            "No matches",
            "Try a different search, tag, level or review filter.",
        )
        return

    total = len(all_words)
    caption = (
        f"{len(words)} word{'s' if len(words) != 1 else ''}"
        if len(words) == total
        else f"{len(words)} of {total} words"
    )
    theme.section_header("Your words", caption=caption, icon="📖")

    mm = get("mm")
    tts_available = mm.is_model_available("tts")
    for start in range(0, len(words), 3):
        row = words[start : start + 3]
        columns = st.columns(3)
        for column, word in zip(columns, row):
            with column:
                _render_word_card(word, word_svc, target_lang, tts_available, mm)


def _render_word_card(word, word_svc, target_lang, tts_available, mm) -> None:
    word_id = word["id"]
    reading = word.get("reading", "")
    reading_html = (
        f'<span class="lt-reading">{_esc(reading)}</span>'
        if _has_kanji(word["word"]) and reading
        else ""
    )
    translation = word.get("translation", "")
    translation_html = (
        f'<div class="lt-translation">{_esc(translation)}</div>' if translation else ""
    )

    with st.container(key=f"ltcardhover_word_{word_id}"):
        head_col, audio_col = st.columns([6, 1], vertical_alignment="center")
        with head_col:
            st.markdown(
                f'<div class="lt-word">{_esc(word["word"])}{reading_html}</div>{translation_html}',
                unsafe_allow_html=True,
            )
        with audio_col:
            if tts_available and st.button(
                "🔊", key=f"tts_{word_id}", help="Play audio", type="tertiary"
            ):
                with st.spinner(""):
                    tts = mm.get_tts()
                    audio_bytes = tts.synthesize(word["word"], lang=target_lang)
                st.html(autoplay_audio_html(audio_bytes))

        pills = _pills_html(word)
        if pills:
            st.html(pills)

        definition = word.get("definition", "")
        if definition:
            st.markdown(f'<div class="lt-muted">{_esc(definition)}</div>', unsafe_allow_html=True)

        examples = word.get("examples") or []
        if examples:
            st.markdown(
                f'<div class="lt-example">“{_esc(examples[0])}”</div>',
                unsafe_allow_html=True,
            )

        _render_details(word, examples[1:])

        st.markdown('<div class="lt-divider"></div>', unsafe_allow_html=True)
        _render_card_actions(word, word_svc, target_lang)


def _pills_html(word: dict) -> str:
    labels = [
        word.get("part_of_speech"),
        word.get("formality"),
        word.get("proficiency_level"),
    ]
    pills = [theme.tag(label) for label in labels if label and label != "-"]
    pills += [theme.tag(f"#{tag}", accent=True) for tag in word.get("tags", [])]
    return f'<div class="lt-tagrow">{"".join(pills)}</div>' if pills else ""


def _render_details(word: dict, extra_examples: list[str]) -> None:
    sections = []
    if word.get("synonyms"):
        sections.append(("Synonyms", ", ".join(word["synonyms"])))
    if word.get("collocations"):
        sections.append(("Collocations", ", ".join(word["collocations"])))
    if word.get("related_words"):
        sections.append(("Related", ", ".join(word["related_words"])))
    conj = word.get("conjugations")
    if conj:
        sections.append(("Conjugations", " · ".join(f"{k}: {v}" for k, v in conj.items())))
    ls = word.get("language_specific", {})
    extras = {k: v for k, v in ls.items() if v} if ls else {}
    if extras:
        sections.append(("Language info", " · ".join(f"{k}: {v}" for k, v in extras.items())))
    if word.get("grammar_notes"):
        sections.append(("Grammar", word["grammar_notes"]))

    if not sections and not extra_examples:
        return

    with st.expander("More details"):
        for label, value in sections:
            st.markdown(f"**{label}:** {value}")
        if extra_examples:
            st.markdown("**Examples:**")
            for example in extra_examples:
                st.markdown(f"- {example}")


def _render_card_actions(word, word_svc, target_lang) -> None:
    word_id = word["id"]
    stats = word.get("review_stats", {})
    last_reviewed = stats.get("last_reviewed")
    is_reviewed = last_reviewed is not None

    st.caption(
        f"✅ {stats.get('correct', 0)} · ❌ {stats.get('incorrect', 0)} · "
        f"Last: {last_reviewed or 'never'}"
    )

    confirm_key = f"confirm_delete_{word_id}"
    if st.session_state.get(confirm_key):
        st.caption(f"Delete **{word['word']}**?")
        dcol1, dcol2 = st.columns(2)
        with dcol1:
            if st.button(
                "Yes, delete", key=f"yes_del_{word_id}", use_container_width=True, type="primary"
            ):
                word_svc.delete_word(target_lang, word_id)
                del st.session_state[confirm_key]
                st.rerun()
        with dcol2:
            if st.button("Cancel", key=f"no_del_{word_id}", use_container_width=True):
                del st.session_state[confirm_key]
                st.rerun()
        return

    action_col1, action_col2 = st.columns([1.7, 1])
    with action_col1:
        if is_reviewed:
            if st.button("Mark not reviewed", key=f"unreview_{word_id}", use_container_width=True):
                word_svc.set_review_status(target_lang, word_id, False)
                st.rerun()
        else:
            if st.button("Mark reviewed", key=f"review_{word_id}", use_container_width=True):
                word_svc.set_review_status(target_lang, word_id, True)
                st.rerun()
    with action_col2:
        if st.button("🗑️", key=f"del_{word_id}", use_container_width=True, help="Delete word"):
            st.session_state[confirm_key] = True
            st.rerun()


def _render_add(word_svc, target_lang: str, native_lang: str) -> None:
    with st.container(key="ltcard_add_word"):
        theme.section_header("Add a word manually", icon="➕")
        word_input = st.text_input("Word")
        reading_input = st.text_input("Reading / pronunciation (optional)")
        tags_input = st.text_input("Tags (comma-separated, optional)")

        if st.button("➕  Add & enrich", type="primary", disabled=not word_input.strip()):
            tags = [t.strip() for t in tags_input.split(",") if t.strip()]
            with st.spinner(f"Enriching “{word_input}”…"):
                entry = word_svc.add_word(
                    target_lang,
                    native_lang,
                    word_input,
                    reading=reading_input,
                    source="manual",
                    tags=tags,
                )
            st.success(f"Added: **{entry['word']}** — {entry.get('definition', '')}")
            st.rerun()


def _render_review(word_svc, target_lang: str, native_lang: str) -> None:
    stale = word_svc.get_stale_words(target_lang)

    if not stale:
        theme.empty_state(
            "✅",
            "All caught up",
            "Every saved word has been reviewed recently. Come back later!",
        )
        return

    theme.section_header("Review session", caption=f"{len(stale)} words due", icon="🔁")
    mode = st.pills(
        "Review mode",
        ["Flashcard", "Fill-in-the-blank", "Sentence construction"],
        default="Flashcard",
        key="review_mode",
        label_visibility="collapsed",
    )
    if mode is None:
        mode = "Flashcard"

    if "review_queue" not in st.session_state:
        st.session_state.review_queue = list(stale)
        st.session_state.review_idx = 0
        st.session_state.review_revealed = False

    queue = st.session_state.review_queue
    idx = st.session_state.review_idx

    if idx >= len(queue):
        theme.empty_state("🎉", "Review session complete!", "Nice work — queue cleared.")
        if st.button("Start another session", type="primary"):
            for key in ("review_queue", "review_idx", "review_revealed"):
                st.session_state.pop(key, None)
            st.rerun()
        return

    word = queue[idx]
    st.progress(idx / len(queue), text=f"{idx} / {len(queue)} reviewed")

    if mode == "Flashcard":
        _render_flashcard(word, word_svc, target_lang)
    elif mode == "Fill-in-the-blank":
        _render_fill_blank(word, word_svc, target_lang, idx)
    else:
        _render_sentence(word, word_svc, target_lang, native_lang, idx)


def _render_flashcard(word, word_svc, target_lang: str) -> None:
    with st.container(key="ltcard_flashcard"):
        reading = word.get("reading", "")
        reading_html = (
            f'<div class="lt-flash-reading">{_esc(reading)}</div>'
            if _has_kanji(word["word"]) and reading
            else ""
        )
        audio_col1, audio_col2, audio_col3 = st.columns([1, 2, 1])
        with audio_col2:
            st.html(
                f'<div class="lt-flash"><div class="lt-flash-word">{_esc(word["word"])}</div>'
                f"{reading_html}</div>"
            )

        mm = get("mm")
        if mm.is_model_available("tts") and st.button("🔊  Hear it", key=f"rev_tts_{word['id']}"):
            with st.spinner(""):
                tts = mm.get_tts()
                audio_bytes = tts.synthesize(word["word"], lang=target_lang)
            st.html(autoplay_audio_html(audio_bytes))

        if st.session_state.review_revealed:
            if word.get("translation"):
                st.html(f'<div class="lt-flash-translation">{_esc(word["translation"])}</div>')
            st.markdown(f"**{word.get('definition', '')}**")
            if word.get("grammar_notes"):
                st.caption(word["grammar_notes"])
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅  Got it", use_container_width=True, type="primary"):
                    word_svc.update_review_stats(target_lang, word["id"], correct=True)
                    _next_review()
            with col2:
                if st.button("❌  Missed", use_container_width=True):
                    word_svc.update_review_stats(target_lang, word["id"], correct=False)
                    _next_review()
        else:
            if st.button("👁️  Reveal answer", use_container_width=True, type="primary"):
                st.session_state.review_revealed = True
                st.rerun()


def _render_fill_blank(word, word_svc, target_lang: str, idx: int) -> None:
    with st.container(key="ltcard_flashcard"):
        example = (word.get("examples") or [""])[0]
        blanked = (
            example.replace(word["word"], "______")
            if word["word"] in example
            else f"______ ({word.get('reading', '')})"
        )
        st.markdown("**Fill in the blank**")
        st.markdown(f"### {blanked}")
        answer = st.text_input("Your answer:", key=f"fib_{word['id']}_{idx}")
        if st.button("Check", type="primary", use_container_width=True):
            if word["word"] in answer:
                st.success("✅ Correct!")
                word_svc.update_review_stats(target_lang, word["id"], correct=True)
            else:
                st.error(f"❌ Answer: **{word['word']}**")
                word_svc.update_review_stats(target_lang, word["id"], correct=False)
            _next_review()


def _render_sentence(word, word_svc, target_lang: str, native_lang: str, idx: int) -> None:
    with st.container(key="ltcard_flashcard"):
        st.markdown(f"**Use {word['word']} in a sentence**")
        st.caption(word.get("definition", ""))
        user_sentence = st.text_area("Your sentence:", key=f"sc_{word['id']}_{idx}")
        if st.button("Submit for feedback", type="primary", use_container_width=True):
            chat_svc = get("chat_svc")
            language_svc = get("language_svc")
            native_lang_local, target_lang_local = language_svc.get_language_pair()
            store = get("store")
            tmp_session = store.create_chat_session(target_lang, "_review_tmp")
            result = chat_svc.send_message(
                lang=target_lang,
                session_id=tmp_session,
                native_lang=native_lang_local,
                user_text=(
                    f"Please evaluate this sentence using the word {word['word']}: {user_sentence}"
                ),
                image_path=None,
            )
            store.delete_chat_session(target_lang, tmp_session)
            st.write(result["response"])
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Mark correct", use_container_width=True):
                    word_svc.update_review_stats(target_lang, word["id"], correct=True)
                    _next_review()
            with col2:
                if st.button("❌ Mark missed", use_container_width=True):
                    word_svc.update_review_stats(target_lang, word["id"], correct=False)
                    _next_review()


def _next_review() -> None:
    st.session_state.review_idx += 1
    st.session_state.review_revealed = False
    st.rerun()
