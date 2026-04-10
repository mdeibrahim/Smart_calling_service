from collections.abc import Mapping

from rest_framework.renderers import JSONRenderer


class StandardResponseRenderer(JSONRenderer):
    """Wrap API responses into a consistent envelope."""

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if renderer_context is None:
            return super().render(data, accepted_media_type, renderer_context)

        response = renderer_context.get("response")
        if response is None:
            return super().render(data, accepted_media_type, renderer_context)

        # Keep responses that are already wrapped.
        if isinstance(data, Mapping) and {
            "status",
            "status_code",
            "message",
            "data",
        }.issubset(data.keys()):
            return super().render(data, accepted_media_type, renderer_context)

        status_code = response.status_code
        is_error = status_code >= 400
        status_text = "error" if is_error else "sucess"

        message = ""
        payload_data = data

        if is_error:
            message = self._extract_error_message(data)
        elif isinstance(data, Mapping) and "message" in data and "data" in data:
            message = str(data.get("message") or "")
            payload_data = data.get("data")

        wrapped = {
            "status": status_text,
            "status_code": status_code,
            "message": message,
            "data": payload_data,
        }
        return super().render(wrapped, accepted_media_type, renderer_context)

    def _extract_error_message(self, data):
        if isinstance(data, Mapping):
            if "message" in data and data["message"]:
                return str(data["message"])
            if "detail" in data and data["detail"]:
                return str(data["detail"])

            for value in data.values():
                if isinstance(value, list) and value:
                    return str(value[0])
                if isinstance(value, Mapping):
                    nested = self._extract_error_message(value)
                    if nested:
                        return nested
                if isinstance(value, str) and value:
                    return value

        if isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, str):
                return first
            if isinstance(first, Mapping):
                nested = self._extract_error_message(first)
                if nested:
                    return nested

        return "Request failed"
