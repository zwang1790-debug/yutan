from src.services.log_diagnosis_service import diagnose_log


def test_diagnoses_login_failure_with_repair_advice():
    result = diagnose_log("请求失败：403，登录态失效，请重新登录")

    assert result["status"] == "error"
    assert result["matches"][0]["category"] == "login"
    assert "登录态" in result["advice"]


def test_diagnoses_unknown_errors_without_exposing_log_content():
    result = diagnose_log("Traceback: unexpected custom failure")

    assert result["status"] == "unknown"
    assert result["matches"] == []
    assert "unexpected custom failure" not in result["advice"]


def test_reports_clean_log_as_ok():
    result = diagnose_log("任务启动成功\n本轮采集完成，共发现 3 个商品")

    assert result["status"] == "ok"
    assert result["matches"] == []
