import re


class XMLParser:
    def __init__(self):
        pass

    def _extract_first(self, pattern, text, required=True):
        m = re.search(pattern, text, flags=re.DOTALL | re.IGNORECASE)
        if not m:
            if required:
                raise ValueError(f"Missing required element for pattern: {pattern}")
            return None
        return m.group(1).strip()

    def parse_summary(self, xml_text: str) -> dict:
        if not re.search(
            r"<summary[\s\S]*?>[\s\S]*</summary>", xml_text, flags=re.IGNORECASE
        ):
            raise ValueError("Missing <summary> root")

        title = (
            self._extract_first(r"<title>(.*?)</title>", xml_text, required=False) or ""
        )

        # keyObligations
        ko_block = (
            self._extract_first(
                r"<keyObligations>(.*?)</keyObligations>", xml_text, required=False
            )
            or ""
        )
        key_obligations = re.findall(
            r"<obligation>(.*?)</obligation>", ko_block, flags=re.DOTALL | re.IGNORECASE
        )
        key_obligations = [o.strip() for o in key_obligations]

        # rights
        rights_block = (
            self._extract_first(r"<rights>(.*?)</rights>", xml_text, required=False)
            or ""
        )
        rights = re.findall(
            r"<right>(.*?)</right>", rights_block, flags=re.DOTALL | re.IGNORECASE
        )
        rights = [r.strip() for r in rights]

        # suggestedEdits
        edits_block = (
            self._extract_first(
                r"<suggestedEdits>(.*?)</suggestedEdits>", xml_text, required=False
            )
            or ""
        )
        suggested_edits = re.findall(
            r"<edit>(.*?)</edit>", edits_block, flags=re.DOTALL | re.IGNORECASE
        )
        suggested_edits = [e.strip() for e in suggested_edits]

        # risks
        risks_block = (
            self._extract_first(r"<risks>(.*?)</risks>", xml_text, required=False) or ""
        )
        risk_blocks = re.findall(
            r"<risk>(.*?)</risk>", risks_block, flags=re.DOTALL | re.IGNORECASE
        )
        risks = []
        for rb in risk_blocks:
            rid = self._extract_first(r"<id>(.*?)</id>", rb, required=False)
            rtitle = self._extract_first(r"<title>(.*?)</title>", rb, required=False)
            rdesc = self._extract_first(
                r"<description>(.*?)</description>", rb, required=False
            )
            rsev = self._extract_first(
                r"<severity>(.*?)</severity>", rb, required=False
            )
            risk_obj = {
                "id": rid if rid else None,
                "title": rtitle if rtitle else None,
                "description": rdesc if rdesc else None,
                "severity": rsev if rsev else None,
            }
            if any(v for v in risk_obj.values()):
                risks.append(risk_obj)

        return {
            "title": title,
            "keyObligations": key_obligations,
            "risks": risks,
            "suggestedEdits": suggested_edits,
            "rights": rights,
        }
