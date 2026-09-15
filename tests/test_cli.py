from strategic_surprise_bench.legacy_cli import build_parser


def test_release_check_defaults_to_private_gate_report():
    args = build_parser().parse_args(["release-check"])
    assert args.calibration_report == "calibration/private/gate-report.json"
