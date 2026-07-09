from datetime import timedelta

from app import crud


def test_session_turn_feedback_round_trip(db_session) -> None:
    session = crud.create_session(db_session, {"ai_disclosure": True})
    turn = crud.create_turn(
        db_session,
        session_id=session.id,
        speaker="doctor",
        src_lang="vi",
        tgt_lang="en",
        source_text="xin chao",
        normalized_text="xin chao",
        translation="hello",
        asr_confidence=1.0,
        mt_confidence=0.99,
        risk_tier="low",
        risk_spans=[],
        status="delivered",
    )
    feedback = crud.create_feedback(db_session, turn.id, "other", "test")

    assert crud.list_turns(db_session, session.id)[0].id == turn.id
    assert feedback.turn_id == turn.id


def test_hard_delete_cascades_turns_and_feedback(db_session) -> None:
    session = crud.create_session(db_session, {"ai_disclosure": True})
    turn = crud.create_turn(
        db_session,
        session_id=session.id,
        speaker="doctor",
        src_lang="vi",
        tgt_lang="en",
        source_text="xin chao",
        normalized_text="xin chao",
        translation="hello",
        asr_confidence=1.0,
        mt_confidence=0.99,
        risk_tier="low",
        risk_spans=[],
        status="delivered",
    )
    feedback = crud.create_feedback(db_session, turn.id, "other", None)

    crud.hard_delete_session(db_session, session.id)

    assert crud.get_session(db_session, session.id) is None
    assert db_session.get(crud.TurnRecord, turn.id) is None
    assert db_session.get(crud.FeedbackRecord, feedback.id) is None


def test_retention_purge_deletes_old_sessions_and_keeps_recent(db_session) -> None:
    old = crud.create_session(db_session, {"ai_disclosure": True})
    recent = crud.create_session(db_session, {"ai_disclosure": True})
    old.created_at = crud.utc_now() - timedelta(days=31)
    db_session.add(old)
    db_session.commit()
    turn = crud.create_turn(
        db_session,
        session_id=old.id,
        speaker="doctor",
        src_lang="vi",
        tgt_lang="en",
        source_text="xin chao",
        normalized_text="xin chao",
        translation="hello",
        asr_confidence=1.0,
        mt_confidence=0.99,
        risk_tier="low",
        risk_spans=[],
        status="delivered",
    )
    feedback = crud.create_feedback(db_session, turn.id, "other", None)

    assert crud.purge_old_sessions(db_session, retention_days=30) == 1

    assert crud.get_session(db_session, old.id) is None
    assert db_session.get(crud.TurnRecord, turn.id) is None
    assert db_session.get(crud.FeedbackRecord, feedback.id) is None
    assert crud.get_session(db_session, recent.id) is not None


def test_retention_zero_keeps_all_sessions(db_session) -> None:
    old = crud.create_session(db_session, {"ai_disclosure": True})
    old.created_at = crud.utc_now() - timedelta(days=365)
    db_session.add(old)
    db_session.commit()

    assert crud.purge_old_sessions(db_session, retention_days=0) == 0
    assert crud.get_session(db_session, old.id) is not None
