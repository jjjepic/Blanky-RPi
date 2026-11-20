import unittest

from blanky.operator_events import operator_message, pending_message, summarize_events


def event(number, reason, *, request_id=None, command="MOTOR_1_OFF", source="opcua", **fields):
    return {"id": number, "time": f"10:00:{number:02}", "request_id": request_id,
            "command": command, "source": source, "reason": reason, **fields}


class OperatorEventTests(unittest.TestCase):
    def test_technical_stages_are_collapsed_without_mutating_history(self):
        queued = event(1, "queued", request_id=7, source="button")
        written = event(2, "written", request_id=7)
        raw_return = event(3, "state_change", request_id=7, command="PLC_STATE", source="plc",
                           plc_key="motor_1", plc_value=0)
        confirmation = event(4, "state_observed", request_id=7, source="plc")
        self.assertEqual(summarize_events([queued, written])[0]["reason"], "written")
        history = [queued, written, raw_return, confirmation]
        rows = summarize_events(history)
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0]["time"], rows[0]["source"]), (queued["time"], "button"))
        self.assertEqual(operator_message(rows[0], "pt"), "Saída do motor 1 desligada.")
        self.assertEqual([item["reason"] for item in history], ["queued", "written", "state_change", "state_observed"])

    def test_timeout_does_not_consume_later_plc_change_or_new_request(self):
        history = [event(1, "queued", request_id=1), event(2, "timeout", request_id=1),
                   event(3, "state_change", command="PLC_STATE", plc_key="motor_1", plc_value=0),
                   event(4, "queued", request_id=2)]
        rows = summarize_events(history)
        self.assertEqual([item["reason"] for item in rows], ["timeout", "state_change", "queued"])
        self.assertEqual(operator_message(rows[0], "pt"), "Sem confirmação: desligar o motor 1.")
        self.assertEqual(operator_message(rows[1], "en"), "Motor 1 output off.")

    def test_no_physical_claim_for_robot_or_failed_write(self):
        robot = event(1, "state_observed", command="ROBOT_TO_METAL")
        self.assertEqual(operator_message(robot, "pt"), "Pedido de recolha ativo no tapete 2.")
        self.assertEqual(operator_message(event(1, "write_error"), "en"), "Send not completed: turn off motor 1.")
        self.assertEqual(pending_message("CYL_A_RETRACT", "pt"), "Recuar o cilindro A · A confirmar")
