import spacy
from typing import Dict, List, Any
import re

class IntentRecognizer:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.security_intents = {
            'scan': ['scan', 'probe', 'examine', 'check', 'test'],
            'attack': ['exploit', 'attack', 'penetrate', 'break'],
            'analyze': ['analyze', 'investigate', 'review', 'assess'],
            'configure': ['setup', 'configure', 'prepare', 'initialize'],
            'monitor': ['monitor', 'watch', 'observe', 'track']
        }

    def recognize_intent(self, command: str) -> Dict[str, Any]:
        doc = self.nlp(command.lower())
        intent = self._extract_intent(doc)
        entities = self._extract_entities(doc)
        tools = self._extract_security_tools(doc)
        return {
            'intent': intent,
            'entities': entities,
            'tools': tools,
            'confidence': self._calculate_confidence(intent, entities, tools)
        }

    def _extract_intent(self, doc) -> str:
        for token in doc:
            for intent, keywords in self.security_intents.items():
                if token.lemma_ in keywords:
                    return intent
        return 'general'

    def _extract_entities(self, doc) -> Dict[str, List[str]]:
        entities = {
            'ip_addresses': [],
            'domains': [],
            'ports': [],
            'files': []
        }
        text = doc.text
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        entities['ip_addresses'] = re.findall(ip_pattern, text)
        domain_pattern = r'\b[a-zA-Z0-9-]+\.[a-zA-Z]{2,}\b'
        entities['domains'] = re.findall(domain_pattern, text)
        port_pattern = r'\bport\s+(\d+)\b'
        entities['ports'] = [int(p) for p in re.findall(port_pattern, text)]
        return entities

    def _extract_security_tools(self, doc) -> List[str]:
        # Dummy implementation for now
        return []

    def _calculate_confidence(self, intent, entities, tools) -> float:
        # Dummy confidence calculation
        return 0.9
