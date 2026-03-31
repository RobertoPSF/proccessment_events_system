class FanOutService:

    @staticmethod
    def get_targets(event_type: str, payload: dict) -> list[dict]:

        if event_type == "user_event":
            return [
                {"type": "email", "data": payload},
                {"type": "audit_log", "data": payload},
                {"type": "analytics", "data": payload},
            ]

        return []