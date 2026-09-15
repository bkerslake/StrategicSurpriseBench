"""v0.3 behavioral contract: neutral inputs, isolated grading, explicit missingness."""

from __future__ import annotations

import json

import pytest
from inspect_ai import eval
from inspect_ai._util.registry import registry_info
from inspect_ai.model import ModelOutput, ModelUsage, get_model
from pydantic import ValidationError

from strategic_surprise_bench.assessment import (
    DIMENSIONS,
    SYSTEM,
    VERSION,
    AssessmentTranscript,
    GenerationIssue,
    list_assessment_cases,
    load_assessment_case,
    render_assessment,
)
from strategic_surprise_bench.assessment_scoring import (
    DEFAULT_JUDGE_ATTEMPTS,
    grade_template,
    judge_assessment,
    parse_stage_grades,
    quote_match,
    review_packet,
    score_assessment,
    summarize_assessments,
)
from strategic_surprise_bench.cli import main
from strategic_surprise_bench.inspect_task import strategic_surprise, strategic_surprise_legacy


def transcript():
    return AssessmentTranscript(
        case_id="lattice_signal",
        variant="a",
        responses=[
            "The announcement is not a technical demonstration. Verify before committing.",
            "The audit weakens the claim. Keep the inventory work but defer full replacement.",
        ],
    )


def full_sheet(item=None):
    item = item or transcript()
    sheet = grade_template(item)
    sheet.reviewer = "test-reviewer"
    for grade in sheet.grades:
        grade.score = 2
        grade.quotes = [item.responses[1 if grade.dimension == "adaptation" else 0]]
        grade.rationale = "Synthetic plumbing label, not an expert judgment."
    return sheet


def test_neutral_prompts_and_private_boundary():
    assert "strategic" not in SYSTEM.lower()
    for case_id in list_assessment_cases():
        case = load_assessment_case(case_id)
        initial = render_assessment(case, 1)
        assert initial == render_assessment(case, 1, "b")
        for term in (
            "H1",
            "H2",
            "H3",
            "hypothesis",
            "counterfactual",
            "second-order",
            "JSON",
            "RECURRING FORECASTS",
            "deception",
            "rubric",
            "source_assessments",
        ):
            assert term not in initial
        assert case.title not in initial
        assert case.id not in initial
        for update in case.updates:
            prompt = render_assessment(case, 2, update.id)
            assert update.adaptation.two not in prompt
            assert update.evidence[0] not in initial
        # Mutating private material cannot change either target message.
        before = [render_assessment(case, s) for s in (1, 2)]
        case.title = "SECRET TITLE"
        case.initial_rubric[0].two = "SECRET INITIAL RUBRIC"
        case.updates[0].adaptation.two = "SECRET UPDATE RUBRIC"
        assert before == [render_assessment(case, s) for s in (1, 2)]
        assert render_assessment(case, 2, "a") != render_assessment(case, 2, "b")


def test_stage_one_judge_cannot_see_update_or_future_response():
    item = transcript()
    packet = json.dumps(review_packet(item, 1))
    case = load_assessment_case(item.case_id)
    assert item.responses[1] not in packet
    assert case.update("a").evidence[0] not in packet
    assert "adaptation" not in packet
    assert '"case_id"' not in packet and '"variant"' not in packet
    second = review_packet(item, 2)
    assert second["initial_response"] == item.responses[0]
    assert second["current_response"] == item.responses[1]
    assert [c["dimension"] for c in second["criteria"]] == ["adaptation"]


def test_missing_grades_are_not_failures_or_renormalized_totals():
    item = transcript()
    result = score_assessment(item)
    assert result["total"] is None
    assert result["coverage"] == 0
    sheet = full_sheet(item)
    sheet.grades[0].score = None
    partial = score_assessment(item, sheet)
    assert partial["total"] is None and partial["coverage"] == 0.8
    complete = score_assessment(item, full_sheet(item))
    assert complete["total"] == 10
    # A real zero remains a graded result.
    sheet = full_sheet(item)
    sheet.grades[0].score = 0
    sheet.grades[0].quotes = []
    assert score_assessment(item, sheet)["total"] == 8
    second = {**partial, "variant": "b"}
    assert summarize_assessments([complete, second])["mean"] is None


def test_quote_grounding_is_stage_specific_and_does_not_override_other_grades():
    item = transcript()
    sheet = full_sheet(item)
    sheet.grades[0].quotes = [item.responses[1]]
    result = score_assessment(item, sheet)
    assert result["dimensions"]["adversarial"] is None
    assert result["dimensions"]["adaptation"] == 2
    sheet = full_sheet(item)
    sheet.grades[-1].quotes = [""]
    assert score_assessment(item, sheet)["dimensions"]["adaptation"] is None
    sheet.grades[-1].quotes = []
    assert score_assessment(item, sheet)["dimensions"]["adaptation"] is None


def test_grade_binding_rejects_another_variant_or_edited_response():
    item = transcript()
    sheet = full_sheet(item)
    item.variant = "b"
    with pytest.raises(ValueError, match="does not match"):
        score_assessment(item, sheet)
    item = transcript()
    item.responses[0] += " Edited."
    with pytest.raises(ValueError, match="does not match"):
        score_assessment(item, sheet)
    sheet = full_sheet()
    sheet.grades.append(sheet.grades[0])
    with pytest.raises(ValueError, match="duplicate"):
        score_assessment(transcript(), sheet)


def test_empty_response_stays_missing_and_prose_needs_no_schema():
    item = transcript()
    item.responses[0] = ""
    result = score_assessment(item, full_sheet(item))
    assert result["dimensions"]["adversarial"] is None
    assert result["dimensions"]["adaptation"] == 2
    assert result["total"] is None


def test_truncation_survives_export_and_cannot_be_graded_as_a_real_zero():
    item = transcript()
    item.generation_issues = [GenerationIssue(stage=1, stop_reason="max_tokens")]
    exported = AssessmentTranscript.model_validate_json(item.model_dump_json())
    sheet = full_sheet(exported)
    for grade in sheet.grades:
        grade.score = 0
        grade.quotes = []
    result = score_assessment(exported, sheet)
    assert result["coverage"] == 0 and result["total"] is None
    assert review_packet(exported, 1)["generation_issues"]


def test_provisional_grades_stay_distinct_from_human_grades():
    item = transcript()
    human = score_assessment(item, full_sheet(item))
    sheet = full_sheet(item)
    sheet.source = "model"
    provisional = score_assessment(item, sheet)
    assert provisional["status"] == "provisional_model_grade"
    assert human["status"] == "human_graded"
    with pytest.raises(ValueError, match="separately"):
        summarize_assessments([human, {**provisional, "variant": "b"}])


def test_judge_parser_rejects_omitted_duplicate_or_extra_criteria():
    grade = full_sheet().grades[0].model_dump()
    with pytest.raises(ValueError):
        parse_stage_grades(json.dumps({"grades": [grade, grade]}), {"adversarial"})
    with pytest.raises(ValueError):
        parse_stage_grades(json.dumps({"grades": [grade]}), set(DIMENSIONS[:-1]))
    grade["score"] = 3
    with pytest.raises(ValidationError):
        parse_stage_grades(json.dumps({"grades": [grade]}), {"adversarial"})


def test_quote_normalization_accepts_punctuation_and_ellipsis_variants():
    item = transcript()
    item.responses[0] = (
        "The board’s “announcement” is not a technical demonstration — verify before committing."
    )
    sheet = full_sheet(item)
    sheet.grades[0].quotes = [
        'The board\'s "announcement" is not a technical demonstration - verify'
    ]
    sheet.grades[1].quotes = ["“The board’s ... demonstration”"]
    sheet.grades[2].quotes = ["The board’s\n“announcement”", item.responses[0]]
    result = score_assessment(item, sheet)
    assert result["total"] == 10
    assert result["quote_matches"] == {
        "adversarial": "normalized",
        "systems": "normalized",
        "uncertainty": "normalized",
        "planning": "exact",
        "adaptation": "exact",
    }
    # Paraphrase, reordered fragments, and punctuation-only fragments are still ungrounded.
    for bad in ["The board's statement is not a demonstration", "demonstration ... board", "… — …"]:
        sheet = full_sheet(item)
        sheet.grades[0].quotes = [bad]
        scored = score_assessment(item, sheet)
        assert scored["dimensions"]["adversarial"] is None
        assert "normalization" in scored["missing"]["adversarial"]
    assert quote_match("", "anything") is None
    assert quote_match("   ", "anything") is None


def test_summary_reports_labeled_mean_of_graded_sessions_with_bounds():
    item = transcript()
    complete = score_assessment(item, full_sheet(item))
    sheet = full_sheet(item)
    sheet.grades[0].score = None
    partial = {**score_assessment(item, sheet), "variant": "b"}
    summary = summarize_assessments([complete, partial])
    assert summary["mean"] is None
    assert summary["complete_sessions"] == 1
    assert summary["mean_of_complete_sessions"] == 10
    assert summary["mean_bounds_from_missing_grades"] == [9.0, 10.0]
    assert summary["dimensions"]["adversarial"] is None
    assert summary["dimensions_of_graded"]["adversarial"] == 2
    assert summary["dimensions"]["systems"] == 2
    assert summarize_assessments([complete])["mean"] == 10
    ungraded = summarize_assessments([score_assessment(item)])
    assert ungraded["mean_of_complete_sessions"] is None
    assert ungraded["mean_bounds_from_missing_grades"] == [0.0, 10.0]


@pytest.mark.asyncio
async def test_judge_retries_fill_only_missing_dimensions_and_log_attempts(monkeypatch):
    calls = []
    item = transcript()
    good = [g.model_dump() for g in full_sheet(item).grades[:-1]]
    flawed = json.loads(json.dumps(good))
    flawed[0]["quotes"] = ["this text is not in the response"]
    flawed[1]["score"] = 1
    adaptation = [full_sheet(item).grades[-1].model_dump()]
    outputs = [
        "not json at all",
        json.dumps({"grades": flawed}),
        json.dumps({"grades": good}),
        ValueError("provider failed"),
        json.dumps({"grades": adaptation}),
    ]

    class FakeModel:
        async def generate(self, messages, config):
            calls.append(messages)
            step = outputs[len(calls) - 1]
            if isinstance(step, Exception):
                raise step
            return ModelOutput.from_content("mockllm/judge", step)

    monkeypatch.setattr("inspect_ai.model.get_model", lambda model: FakeModel())
    sheet = await judge_assessment(item, "mockllm/judge")
    assert len(calls) == 5
    assert all(item.responses[1] not in messages[1].content for messages in calls[:3])
    assert all(messages[1].content == calls[0][1].content for messages in calls[:3])
    result = score_assessment(item, sheet)
    # Systems keeps the first accepted grade (1) even though the third attempt offered a 2.
    assert result["total"] == 9
    assert [(a.stage, a.attempt, a.accepted, a.error) for a in sheet.attempts] == [
        (1, 1, [], "JSONDecodeError"),
        (1, 2, ["planning", "systems", "uncertainty"], None),
        (1, 3, ["adversarial"], None),
        (2, 1, [], "ValueError"),
        (2, 2, ["adaptation"], None),
    ]
    assert sheet.source == "model"
    assert [g.dimension for g in sheet.grades] == list(DIMENSIONS)


@pytest.mark.asyncio
async def test_judge_exhausts_bounded_attempts_and_leaves_grades_missing(monkeypatch):
    calls = []
    item = transcript()

    class FakeModel:
        async def generate(self, messages, config):
            calls.append(messages)
            raise ValueError("provider failed")

    monkeypatch.setattr("inspect_ai.model.get_model", lambda model: FakeModel())
    sheet = await judge_assessment(item, "mockllm/judge", attempts=2)
    assert len(calls) == 4
    result = score_assessment(item, sheet)
    assert result["total"] is None and result["coverage"] == 0
    assert all(g.score is None and "Judge failed" in g.rationale for g in sheet.grades)
    assert len(sheet.attempts) == 4
    # attempts=1 reproduces the original single-call protocol.
    await judge_assessment(item, "mockllm/judge", attempts=1)
    assert len(calls) == 6
    with pytest.raises(ValueError):
        await judge_assessment(item, "mockllm/judge", attempts=0)


def test_default_task_is_v03_and_legacy_is_explicit():
    current = strategic_surprise()
    assert len(current.dataset) == 12
    assert current.version == VERSION == "0.3.1"
    assert strategic_surprise_legacy().version == "0.2.0"
    assert len(strategic_surprise(variant="a").dataset) == 6
    with pytest.raises(ValueError):
        strategic_surprise(variant="compound")
    with pytest.raises(ValueError):
        strategic_surprise(case_id="../secrets")


@pytest.mark.parametrize("epochs", [1, 2])
@pytest.mark.parametrize("graded", [False, True])
def test_two_turn_sessions_and_grade_export(tmp_path, monkeypatch, epochs, graded, capsys):
    monkeypatch.setenv("INSPECT_TRACE_FILE", str(tmp_path / "trace.log"))
    monkeypatch.setattr("inspect_ai._util.appdirs.user_data_path", lambda package_name: tmp_path)

    async def fake_judge(item, model_name, attempts=DEFAULT_JUDGE_ATTEMPTS):
        assert attempts == DEFAULT_JUDGE_ATTEMPTS
        sheet = full_sheet(item)
        sheet.source = "model"
        sheet.reviewer = model_name
        return sheet

    monkeypatch.setattr("strategic_surprise_bench.assessment_task.judge_assessment", fake_judge)
    texts = [f"Response {i}." for i in range(4 * epochs)]
    outputs = []
    for text in texts:
        output = ModelOutput.from_content("mockllm/model", text)
        output.usage = ModelUsage(input_tokens=1, output_tokens=1, total_tokens=2)
        outputs.append(output)
    model = get_model("mockllm/model", custom_outputs=outputs, memoize=False)
    logs = eval(
        registry_info(strategic_surprise).name,
        task_args={"case_id": "lattice_signal", "judge": "mockllm/judge" if graded else None},
        epochs=epochs,
        model=model,
        display="none",
        log_dir=str(tmp_path),
        max_samples=1,
    )
    assert logs[0].status == "success"
    assert len(logs[0].samples) == 2 * epochs
    for index, sample in enumerate(logs[0].samples):
        score = next(iter(sample.scores.values()))
        assert score.value == (10 if graded else "U")
        assert score.metadata["total"] == (10 if graded else None)
        assert (
            sample.metadata["assessment_transcript"]["responses"]
            == texts[index * 2 : index * 2 + 2]
        )
        assert len(sample.messages) == 5  # system + two user/assistant exchanges
        assert not any(message.role == "tool" for message in sample.messages)
    assert texts[1] not in str(logs[0].samples[1].messages)
    metrics = next(iter(logs[0].results.scores)).metrics
    assert any("mean_out_of_10" in name for name in metrics) == graded
    capsys.readouterr()
    main(["extract", str(next(tmp_path.glob("*.eval"))), "--output-dir", str(tmp_path / "review")])
    exported = json.loads(capsys.readouterr().out)["exported"]
    assert len(exported) == 2 * epochs
    sidecars = list((tmp_path / "review").glob("*.grades.json"))
    assert len(sidecars) == (2 * epochs if graded else 0)
    if graded:
        main(["score", exported[0], "--grades", str(sorted(sidecars)[0])])
        assert json.loads(capsys.readouterr().out)["status"] == "provisional_model_grade"


def test_cli_current_score_and_stage_review(tmp_path, capsys):
    path = tmp_path / "transcript.json"
    path.write_text(transcript().model_dump_json())
    main(["score", str(path)])
    assert json.loads(capsys.readouterr().out)["total"] is None
    main(["review", str(path), "--stage", "1"])
    assert "current_response" not in json.loads(capsys.readouterr().out)
    main(["validate"])
    assert json.loads(capsys.readouterr().out)["variants"] == 12
