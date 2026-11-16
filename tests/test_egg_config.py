import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class EggConfigTests(unittest.TestCase):
 def setUp(self):
  self.egg=json.loads((ROOT/'eggs/pterodactyl/egg-wolkehost-afk-bot.json').read_text())
  self.vars={v['env_variable']:v for v in self.egg['variables']}
  self.bot=(ROOT/'bot.js').read_text()
  self.panel=(ROOT/'templates/bot_new.html').read_text()
 def test_all_egg_environment_variables_are_consumed(self):
  expected={'SERVER_HOST','SERVER_PORT','MC_VERSION','AFK_ENABLED','AFK_COMMAND','AUTO_RECONNECT','RECONNECT_DELAY'}
  self.assertEqual(set(self.vars),expected)
  for name in expected:self.assertIn(name,self.bot)
 def test_fixed_settings_are_not_editable_in_egg(self):
  self.assertFalse(self.vars['AFK_COMMAND']['user_editable'])
  self.assertFalse(self.vars['RECONNECT_DELAY']['user_editable'])
  self.assertIn('/afk on',self.panel)
  self.assertIn('10 Sekunden (fest)',self.panel)
 def test_supported_versions_match_panel_and_egg(self):
  rules=self.vars['MC_VERSION']['rules']
  for version in ('auto','1.21.1','1.20.4','1.19.4'):
   self.assertIn(version,rules);self.assertIn(version,self.panel)
if __name__=='__main__':unittest.main()
