"""Real zero-model reproduction -> Prolog diagnosis -> persistent learning fixture."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/prolog-verification/scripts/prolog-verify.py'
FIXTURE = ROOT / 'tests/fixtures/prolog_kb_troubleshooting.pl'
spec = importlib.util.spec_from_file_location('verifier', SCRIPT)
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


@unittest.skipUnless(shutil.which('swipl'), 'real SWI-Prolog required')
class TroubleshootingTest(unittest.TestCase):
    def prolog(self, goal, expected=0):
        result = subprocess.run(['swipl', '-q', '-f', 'none', '-s', str(FIXTURE),
                                 '-g', goal + ',halt', '-t', 'halt(1)'],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, expected, result.stderr)
        return result.stdout

    def test_reproduce_diagnose_and_learn_across_fresh_processes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            project = root / 'project'
            project.mkdir()
            # Execute the original generated verifier, frozen as a regression fixture.
            prolog = project / '.prolog'
            (prolog / 'runs').mkdir(parents=True)
            legacy = ROOT / 'tests/fixtures/prolog_verification_v1.pl'
            shutil.copyfile(legacy, prolog / 'verify.pl')
            revision = verifier.repository_state(project)[1]
            facts = prolog / 'facts.kb'
            facts.write_text(f"task(a).\nrepo_state('no-git',{verifier.atom(revision)}).\nresearch_required(false).\n")
            (prolog / 'runs/run-no-git.pl').write_text(
                f"observation(test_a,command([test]),exit(0),output,'no-git',{verifier.atom(revision)}).\n")
            facts.write_text(facts.read_text().replace('task(a)', 'task(b)'))
            borrowed = subprocess.run(['swipl', '-q', '-f', 'none', '-s', str(prolog / 'verify.pl')],
                                      text=True, capture_output=True, cwd=prolog)
            self.assertEqual(borrowed.returncode, 0, borrowed.stderr)
            self.assertIn('runs/run-', legacy.read_text())
            def run(script, *args):
                return subprocess.run([sys.executable, str(script), '--work-dir', str(project), *args],
                                      text=True, capture_output=True)
            # The fixed helper gives task b no evidence after its explicit reset.
            run(SCRIPT, 'init', '--task', 'a', '--force')
            run(SCRIPT, 'observe', '--', sys.executable, '-c', 'print("tested")')
            run(SCRIPT, 'init', '--task', 'b', '--force')
            isolated = run(SCRIPT, 'check')
            self.assertEqual(isolated.returncode, 1, isolated.stderr)
            evidence = [
                f"observed(baseline_check, fixture, b, baseline, {verifier.atom(revision)}, task_borrowed_success)",
                f"observed(source_key, fixture, a, baseline, {verifier.atom(revision)}, head_only_run_key)",
                f"observed(fixed_check, fixture, b, corrected, {verifier.atom(revision)}, task_run_isolated)",
            ]
            observations = '[' + ','.join(evidence) + ']'
            file = root / 'learned-v1.pl'
            quoted_file = verifier.atom(str(file))
            rev = verifier.atom(revision)
            output = self.prolog(f"diagnose({observations},fixture,{rev},Finding),writeln(Finding),"
                                f"promote({observations},fixture,{rev},1,{quoted_file})")
            self.assertIn('confirmed(head_only_run_key', output)
            # Another SWI process recovers the versioned rule and evidence.
            self.prolog(f"recall({quoted_file},fixture,{rev},available(_))")
            self.prolog(f"recall({quoted_file},other,{rev},unknown(other_project))")
            self.prolog(f"recall({quoted_file},fixture,new_revision,stale(_))")
            self.prolog(f"promote({observations},fixture,{rev},1,{quoted_file})", expected=1)
            self.assertIn('learned_rule(fixture,verification_scope,1', file.read_text())

    def test_unknown_conflict_and_hypothesis_cannot_promote(self):
        with tempfile.TemporaryDirectory() as folder:
            file = verifier.atom(str(Path(folder) / 'rule.pl'))
            self.prolog('diagnose([],p,r,unknown(insufficient_current_evidence))')
            conflict = '[observed(a,p,t,x,r,task_run_isolated),observed(b,p,t,x,r,task_run_not_isolated)]'
            self.prolog(f'diagnose({conflict},p,r,conflict(task_run_isolation))')
            self.prolog(f'promote({conflict},p,r,1,{file})', expected=1)
            self.prolog(f'promote([],p,r,1,{file})', expected=1)
            stale = '[observed(a,p,t,x,old,task_borrowed_success),observed(b,p,t,x,old,head_only_run_key)]'
            self.prolog(f'diagnose({stale},p,r,unknown(insufficient_current_evidence))')


if __name__ == '__main__':
    unittest.main()
