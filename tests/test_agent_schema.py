import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class AgentSchemaTests(unittest.TestCase):
    def test_agent_has_reconciliation_loop_and_separate_service(self):
        source = (ROOT / 'node_agent.py').read_text()
        ast.parse(source)
        self.assertIn('POLL_SECONDS = 5', source)
        self.assertIn("desired_state == 'restart'", source)
        self.assertTrue((ROOT / 'deploy/wolkehost-agent.service').exists())

    def test_worker_only_sets_desired_state(self):
        source = (ROOT / 'worker.py').read_text()
        self.assertIn("desired_state = 'running'", source)
        self.assertIn("desired_state = 'stopped'", source)
        self.assertNotIn('subprocess.Popen', source)

if __name__ == '__main__':
    unittest.main()
