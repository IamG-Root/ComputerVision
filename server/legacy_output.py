"""Public serializers preserved verbatim from baseline e057a11."""
import utils

class LegacyOutput:
    @staticmethod
    def format_array_for_unity(entities_array):
        formatted_array = []
        for _obj in entities_array:
            formatted_array.append({"id": _obj["id"], "category": _obj["class"], "position": _obj["position"], "timestamp": _obj["last_update"]})
        return formatted_array
    
    @staticmethod
    def format_array_for_fiware(entities_array):
        formatted_array = []
        for _obj in entities_array:
            posx = _obj["position"][0]
            posy = _obj["position"][1]
            time_instant = utils.unix_to_iso(_obj["last_update"])
            formatted_array.append({"ident": _obj["id"], "classe": _obj["class"], "posx": posx, "posy": posy, "TimeInstant": time_instant})
        return formatted_array