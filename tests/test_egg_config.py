import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class EggConfigTests(unittest.TestCase):
 def test_egg_environment_variables_are_consumed_by_worker(self):
  egg=json.loads((ROOT/'eggs/pterodactyl/egg-wolkehost-afk-bot.json').read_text())
  variables={v['env_variable']:v for v in egg['variables']}
  expected={'SERVER_HOST','SERVER_PORT','MC_VERSION','AFK_ENABLED','AFK_COMMAND','AUTO_RECONNECT','RECONNECT_DELAY'}
  self.assertEqual(set(variables),expected)
  bot=(ROOT/'bot.js').read_text()
  for name in expected:self.assertIn(name,bot)
 def test_supported_versions_are_in_egg_and_panel(self):
  egg=json.loads((ROOT/'eggs/pterodactyl/egg-wolkehost-afk-bot.json').read_text())
  rules=next(v['rules'] for v in egg['variables'] if v['env_variable']=='MC_VERSION')
  app=(ROOT/'app.py').read_text()
  for version in ('auto','1.21.1','1.20.4','1.19.4'):
   self.assertIn(version,rules);self.assertIn(version,app)
if __name__=='__main__':unittest.main()
