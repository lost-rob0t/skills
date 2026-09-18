import os
import pathlib
import subprocess
import tempfile
import textwrap
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
REMOTE = ROOT / "skills" / "llm-worker" / "scripts" / "llm-worker-exec"
INSTALL = ROOT / "skills" / "llm-worker" / "scripts" / "install-opencode-bash-tool"
NIX_REMOTE = ROOT / "skills" / "nix-remote-build" / "scripts" / "nix-remote-build"


def write_exe(path: pathlib.Path, content: str) -> None:
    path.write_text(content)
    path.chmod(0o755)


class LlmWorkerSkillTests(unittest.TestCase):
    def test_remote_shell_requires_mapping(self):
        env = os.environ.copy()
        env.pop("LLM_WORKER_HOST", None)
        env.pop("LLM_WORKER_PROJECT", None)
        result = subprocess.run(
            [str(REMOTE), "--", "true"],
            env=env,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 64)
        self.assertIn("LLM_WORKER_HOST is required", result.stderr)

    def test_remote_shell_routes_to_project_identity_and_preserves_status(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            args_file = root / "args"
            stdin_file = root / "stdin"
            write_exe(
                bin_dir / "ssh",
                textwrap.dedent(
                    f"""\
                    #!/usr/bin/env bash
                    printf '%s\\n' "$@" > {args_file}
                    cat > {stdin_file}
                    exit 7
                    """
                ),
            )
            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}:{env['PATH']}"
            env["LLM_WORKER_HOST"] = "worker.example"
            env["LLM_WORKER_PROJECT"] = "demo"
            result = subprocess.run(
                [str(REMOTE), "--", "printf remote-ok"],
                env=env,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 7)
            self.assertEqual(
                args_file.read_text().splitlines(),
                ["-T", "demo@worker.example", "bash", "-s"],
            )
            payload = stdin_file.read_text()
            self.assertIn('cd -- "$HOME"/repo', payload)
            self.assertIn("printf remote-ok", payload)

    def test_installer_refuses_existing_bash_override(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            tools = root / "tools"
            tools.mkdir()
            (tools / "bash.ts").write_text("// existing\n")
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = str(root)
            result = subprocess.run(
                [str(INSTALL)],
                env=env,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 73)
            self.assertIn("already exists", result.stderr)


class NixRemoteBuildSkillTests(unittest.TestCase):
    def _fake_nix(self, root: pathlib.Path, build_status: int = 0):
        bin_dir = root / "bin"
        bin_dir.mkdir()
        log = root / "nix.log"
        write_exe(
            bin_dir / "nix",
            textwrap.dedent(
                f"""\
                #!/usr/bin/env bash
                printf '%s\\n' "$*" >> {log}
                case "$1" in
                  build)
                    printf '%s\\n' /nix/store/fixture-output
                    exit {build_status}
                    ;;
                  path-info)
                    [[ "$2" == /nix/store/fixture-output ]]
                    ;;
                  *)
                    exit 0
                    ;;
                esac
                """
            ),
        )
        return bin_dir, log

    def test_build_disables_local_jobs_and_realizes_output_locally(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            bin_dir, log = self._fake_nix(root)
            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}:{env['PATH']}"
            env["LLM_WORKER_HOST"] = "worker.example"
            env["LLM_WORKER_PROJECT"] = "demo"
            result = subprocess.run(
                [str(NIX_REMOTE), "build", ".#fixture"],
                env=env,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "/nix/store/fixture-output")
            calls = log.read_text()
            self.assertIn(
                "build --builders ssh-ng://demo@worker.example x86_64-linux - 8 2 --max-jobs 0",
                calls,
            )
            self.assertIn("path-info /nix/store/fixture-output", calls)

    def test_build_preserves_nix_failure_status(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            bin_dir, _ = self._fake_nix(root, build_status=42)
            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}:{env['PATH']}"
            env["LLM_WORKER_HOST"] = "worker.example"
            env["LLM_WORKER_PROJECT"] = "demo"
            result = subprocess.run(
                [str(NIX_REMOTE), "build", ".#fixture"],
                env=env,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 42)


if __name__ == "__main__":
    unittest.main()
