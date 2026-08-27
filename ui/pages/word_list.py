import streamlit as st
from ui.state import get
from ui.components.audio_controls import autoplay_audio_html


def _has_kanji(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" or "\u3400" <= ch <= "\u4dbf" for ch in text)


def _format_word_display(word: str, reading: str = "") -> str:
    if _has_kanji(word) and reading:
        return f"{word}({reading})"
    return word


def render() -> None:
    st.title("📚 Word List")

    language_svc = get("language_svc")
    native_lang, target_lang = language_svc.get_language_pair()
    word_svc = get("word_svc")

    tab_browse, tab_add, tab_review = st.tabs(["Browse", "Add Word", "Review"])

    with tab_browse:
        _render_browse(word_svc, target_lang, native_lang)

    with tab_add:
        _render_add(word_svc, target_lang, native_lang)

    with tab_review:
        _render_review(word_svc, target_lang, native_lang)


def _render_browse(word_svc, target_lang, native_lang) -> None:
    words = word_svc.get_all_words(target_lang)
    if not words:
        st.info("No words saved yet. Start chatting or take a lesson!")
        return

    col1, col2 = st.columns(2)
    with col1:
        query = st.text_input("🔍 Search", placeholder="Search words...")
    with col2:
        all_tags = sorted({tag for w in words for tag in w.get("tags", [])})
        tag_filter = st.selectbox("Filter by tag", ["All"] + all_tags)

    if query:
        words = word_svc.search(target_lang, query)
    if tag_filter != "All":
        words = [w for w in words if tag_filter in w.get("tags", [])]

    mm = get("mm")
    tts_available = mm.is_model_available("tts")

    for word in words:
        translation = word.get("translation", "")
        display = _format_word_display(word["word"], word.get("reading", ""))
        header = f"**{display}**"
        if translation:
            header += f" — {translation}"
        with st.expander(header):
            # Word + audio button row
            word_col, audio_col = st.columns([8, 1])
            with word_col:
                st.markdown(f"### {display}")
                if translation:
                    st.markdown(f"**{translation}**")
            with audio_col:
                if tts_available and st.button("🔊", key=f"tts_{word['id']}", help="Play audio"):
                    with st.spinner(""):
                        tts = mm.get_tts()
                        audio_bytes = tts.synthesize(word["word"], lang=target_lang)
                    st.html(autoplay_audio_html(audio_bytes))

            st.divider()
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**Definition:** {word.get('definition', '-')}")
                st.write(f"**Part of speech:** {word.get('part_of_speech', '-')}")
                st.write(f"**Formality:** {word.get('formality', '-')}")
                st.write(f"**Level:** {word.get('proficiency_level', '-')}")
                if word.get("synonyms"):
                    st.write(f"**Synonyms:** {', '.join(word['synonyms'])}")
                if word.get("collocations"):
                    st.write(f"**Collocations:** {', '.join(word['collocations'])}")
                if word.get("examples"):
                    st.write("**Examples:**")
                    for ex in word["examples"]:
                        st.write(f"  • {ex}")
                if word.get("related_words"):
                    st.write(f"**Related:** {', '.join(word['related_words'])}")
                conj = word.get("conjugations")
                if conj:
                    st.write(
                        "**Conjugations:** " + " · ".join(f"{k}: {v}" for k, v in conj.items())
                    )
                ls = word.get("language_specific", {})
                if ls and any(v for v in ls.values() if v):
                    extras = {k: v for k, v in ls.items() if v}
                    st.write(
                        "**Language info:** " + " · ".join(f"{k}: {v}" for k, v in extras.items())
                    )
            with col2:
                stats = word.get("review_stats", {})
                # Ensure we have proper defaults for all fields
                last_reviewed = stats.get("last_reviewed")
                correct_count = stats.get("correct", 0)
                incorrect_count = stats.get("incorrect", 0)
                is_reviewed = last_reviewed is not None

                st.caption(
                    f"✅ {correct_count} / ❌ {incorrect_count}\nLast: {last_reviewed or 'never'}"
                )

                # Add manual review status toggle
                if is_reviewed:
                    if st.button("Mark as Not Reviewed", key=f"unreview_{word['id']}"):
                        word_svc.set_review_status(target_lang, word["id"], False)
                        st.rerun()
                else:
                    if st.button("Mark as Reviewed", key=f"review_{word['id']}"):
                        word_svc.set_review_status(target_lang, word["id"], True)
                        st.rerun()

                st.divider()
                confirm_key = f"confirm_delete_{word['id']}"
                if st.session_state.get(confirm_key):
                    st.caption(f"Delete **{word['word']}**?")
                    dcol1, dcol2 = st.columns(2)
                    with dcol1:
                        if st.button("Yes, delete", key=f"yes_del_{word['id']}"):
                            word_svc.delete_word(target_lang, word["id"])
                            del st.session_state[confirm_key]
                            st.rerun()
                    with dcol2:
                        if st.button("Cancel", key=f"no_del_{word['id']}"):
                            del st.session_state[confirm_key]
                            st.rerun()
                else:
                    if st.button("🗑️ Delete", key=f"del_{word['id']}"):
                        st.session_state[confirm_key] = True
                        st.rerun()


def _render_add(word_svc, target_lang, native_lang) -> None:
    st.subheader("Add a word manually")
    word_input = st.text_input("Word")
    reading_input = st.text_input("Reading / pronunciation (optional)")
    tags_input = st.text_input("Tags (comma-separated, optional)")

    if st.button("➕ Add & Enrich") and word_input:
        tags = [t.strip() for t in tags_input.split(",") if t.strip()]
        with st.spinner(f"Enriching '{word_input}'..."):
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


def _render_review(word_svc, target_lang, native_lang) -> None:
    stale = word_svc.get_stale_words(target_lang)

    if not stale:
        st.success("✅ All words reviewed recently!")
        return

    st.info(f"**{len(stale)} words** due for review.")
    mode = st.radio("Review mode", ["Flashcard", "Fill-in-the-blank", "Sentence construction"])

    if "review_queue" not in st.session_state:
        st.session_state.review_queue = list(stale)
        st.session_state.review_idx = 0
        st.session_state.review_revealed = False

    queue = st.session_state.review_queue
    idx = st.session_state.review_idx

    if idx >= len(queue):
        st.success("🎉 Review session complete!")
        del st.session_state.review_queue
        del st.session_state.review_idx
        del st.session_state.review_revealed
        return

    word = queue[idx]
    st.progress((idx) / len(queue), text=f"{idx}/{len(queue)}")

    if mode == "Flashcard":
        word_col, audio_col = st.columns([8, 1])
        with word_col:
            st.markdown(f"## {word['word']} {word.get('reading', '')}")
        with audio_col:
            mm = get("mm")
            if mm.is_model_available("tts") and st.button("🔊", key=f"rev_tts_{word['id']}"):
                with st.spinner(""):
                    tts = mm.get_tts()
                    audio_bytes = tts.synthesize(word["word"], lang=target_lang)
                st.html(autoplay_audio_html(audio_bytes))
        if st.session_state.review_revealed:
            if word.get("translation"):
                st.markdown(f"### {word['translation']}")
            st.write(f"**{word.get('definition', '')}**")
            st.write(word.get("grammar_notes", ""))
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Got it"):
                    word_svc.update_review_stats(target_lang, word["id"], correct=True)
                    _next_review()
            with col2:
                if st.button("❌ Missed"):
                    word_svc.update_review_stats(target_lang, word["id"], correct=False)
                    _next_review()
        else:
            if st.button("👁️ Reveal"):
                st.session_state.review_revealed = True
                st.rerun()

    elif mode == "Fill-in-the-blank":
        example = (word.get("examples") or [""])[0]
        blanked = (
            example.replace(word["word"], "______")
            if word["word"] in example
            else f"______ ({word.get('reading', '')})"
        )
        st.write(f"Fill in the blank: **{blanked}**")
        answer = st.text_input("Your answer:", key=f"fib_{word['id']}_{idx}")
        if st.button("Check"):
            if word["word"] in answer:
                st.success("✅ Correct!")
                word_svc.update_review_stats(target_lang, word["id"], correct=True)
            else:
                st.error(f"❌ Answer: **{word['word']}**")
                word_svc.update_review_stats(target_lang, word["id"], correct=False)
            _next_review()

    elif mode == "Sentence construction":
        st.write(f"Use **{word['word']}** ({word.get('definition', '')}) in a sentence:")
        user_sentence = st.text_area("Your sentence:", key=f"sc_{word['id']}_{idx}")
        if st.button("Submit for feedback"):
            chat_svc = get("chat_svc")
            language_svc = get("language_svc")
            native_lang_local, target_lang_local = language_svc.get_language_pair()
            store = get("store")
            tmp_session = store.create_chat_session(target_lang, "_review_tmp")
            result = chat_svc.send_message(
                lang=target_lang,
                session_id=tmp_session,
                native_lang=native_lang_local,
                user_text=f"Please evaluate this sentence using the word {word['word']}: {user_sentence}",
                image_path=None,
            )
            store.delete_chat_session(target_lang, tmp_session)
            st.write(result["response"])
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Mark correct"):
                    word_svc.update_review_stats(target_lang, word["id"], correct=True)
                    _next_review()
            with col2:
                if st.button("❌ Mark missed"):
                    word_svc.update_review_stats(target_lang, word["id"], correct=False)
                    _next_review()


def _next_review() -> None:
    st.session_state.review_idx += 1
    st.session_state.review_revealed = False
    st.rerun()
