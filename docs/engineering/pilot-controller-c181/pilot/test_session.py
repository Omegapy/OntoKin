import importlib
import json
from pathlib import Path
import tempfile
import unittest

from agent_loop import run
from session import digest, trial


class ControlTests(unittest.TestCase):
    def test_one_action_from_each_turn(self):
        class Fake:
            def infer(self, script, prompt, snapshot, limit):
                self.last_prompt = prompt
                return {"text": next(script)}, {"charged": 1}
        received=[]
        def tool(g, command):
            received.append(command)
            return {"exit":0,"stdout":"Sample goal" if len(received)==1 else "evidence"}
        gate=Fake()
        it=iter(["plain", "```sh\npwd\n```\n```sh\nexit 42\n```", "SUBMIT"])
        log=[]
        self.assertEqual(run(gate,it,"fixture",tool,lambda event,**kw:log.append(event)),"SUBMIT")
        self.assertEqual(len(received),2)
        self.assertEqual(received[-1],"pwd")
        self.assertIn("evidence",gate.last_prompt)
        self.assertIn("Sample goal",gate.last_prompt)
        self.assertIn("formatRejected",log)
        self.assertIn("additionalTextIgnored",log)

    def test_closed_card_creates_no_trial_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            d=Path(directory)
            card=d/"closed.json"
            card.write_text(json.dumps({"state":"held"}))
            with self.assertRaises(ValueError):
                trial(card,digest(card),"blender",d/"records")
            self.assertFalse((d/"records").exists())

    def test_wrong_digest_creates_no_trial_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            d=Path(directory)
            card=d/"card.json"
            card.write_text("{}")
            with self.assertRaises(ValueError):
                trial(card,"0"*64,"blender",d/"records")
            self.assertFalse((d/"records").exists())


if __name__=="__main__":
    unittest.main()
