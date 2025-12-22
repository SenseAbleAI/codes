from core.detection.sensory_detector import detect_sensory_spans

class DetectorAgent:
    def run(self, text, language):
        return detect_sensory_spans(text, language)
