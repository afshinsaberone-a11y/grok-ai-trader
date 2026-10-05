"""Tests for Demo submission receipt validation."""
import pytest
from tools.validate_demo_submission_v1 import DemoSubmissionError, validate_submission


def _valid():
    return {
        "schema":"forexai.mt5_demo_execution_submission.v1","status":"PASS","account_mode":"DEMO",
        "terminal_connected":True,"order_submission_performed":True,"execution_status":"ACCEPTED",
        "full_fill":True,"trade_id":"T-DEMO-1","strategy_id":"G13-M15","symbol":"EURUSD",
        "timeframe":"M15","side":"BUY","volume":0.10,"filled_volume":0.10,"remaining_volume":0.0,
        "broker_order_id":"7001","broker_deal_id":"5001","broker_retcode":"10009","live_enabled":False,
    }


def test_valid_submission_passes():
    assert validate_submission(_valid())["status"] == "PASS"


@pytest.mark.parametrize(("field","value","error"),[
    ("account_mode","REAL","ACCOUNT_NOT_DEMO"),
    ("execution_status","PARTIAL","EXECUTION_NOT_ACCEPTED"),
    ("full_fill",False,"FILL_NOT_COMPLETE"),
    ("live_enabled",True,"LIVE_MUST_REMAIN_DISABLED"),
    ("broker_order_id","","BROKER_ORDER_ID_INVALID"),
    ("filled_volume",0.05,"NOT_FULLY_FILLED"),
])
def test_unsafe_submission_fails_closed(field,value,error):
    p=_valid(); p[field]=value
    with pytest.raises(DemoSubmissionError, match=error):
        validate_submission(p)
