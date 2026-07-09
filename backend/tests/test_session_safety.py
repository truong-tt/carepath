from app import session as session_module
from app.config import Settings
from app.providers.base import CriticalEntity, Review
from app.providers.mock import MockASRProvider, MockMTProvider, MockReviewerProvider
from app.providers.registry import ProviderSet
from app.risk import RiskResult


def test_high_risk_reviewer_failure_blocks_turn(db_session, monkeypatch) -> None:
    created = session_module.crud.create_session(db_session, {"ai_disclosure": True})
    monkeypatch.setattr(
        session_module,
        "classify_risk",
        lambda *args: RiskResult(tier="high", spans=[{"kind": "dose"}]),
    )
    providers = ProviderSet(
        asr=MockASRProvider(),
        mt=MockMTProvider(),
        reviewer=MockReviewerProvider(fail=True),
    )

    turn = session_module.process_text_turn(
        db_session,
        providers,
        Settings(),
        session_id=created.id,
        speaker="doctor",
        lang="vi",
        text="Uống nửa viên",
        asr_confidence=1,
    )

    assert turn.status == "blocked"
    assert turn.readback_json is not None
    assert "reviewer_failed" in turn.readback_json


def test_high_risk_readback_stores_entity_text(db_session, monkeypatch) -> None:
    created = session_module.crud.create_session(db_session, {"ai_disclosure": True})
    monkeypatch.setattr(
        session_module,
        "classify_risk",
        lambda *args: RiskResult(tier="high", spans=[{"kind": "dose"}]),
    )
    providers = ProviderSet(
        asr=MockASRProvider(),
        mt=MockMTProvider(),
        reviewer=MockReviewerProvider(
            canned={
                (
                    "vi",
                    "en",
                    "Uống 0.5 viên",
                    "[vi->en] Uống 0.5 viên",
                ): Review(
                    back_translation="Uống nửa viên",
                    entities=[
                        CriticalEntity(
                            kind="dose",
                            source_text="nửa viên",
                            translated_text="half a tablet",
                        )
                    ],
                    flags=[],
                )
            }
        ),
    )

    turn = session_module.process_text_turn(
        db_session,
        providers,
        Settings(),
        session_id=created.id,
        speaker="doctor",
        lang="vi",
        text="Uống nửa viên",
        asr_confidence=1,
    )

    assert turn.readback_json is not None
    assert "source_text" in turn.readback_json
    assert "nửa viên" in turn.readback_json
    assert "source_span" not in turn.readback_json
