import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from harness.engine import ModelError
from harness.examples import make_example
from harness.store import encode, load_input, run_directory, save_run, verify_run
from harness.mcp import call


class RuntimeTests(unittest.TestCase):
    def test_run_and_fresh_verification(self):
        with tempfile.TemporaryDirectory() as work:
            run = save_run(make_example(), work)
            self.assertTrue(verify_run(work, run["run_id"])["verified"])
            directory = Path(run["directory"])
            self.assertTrue((directory / "base-cohorts.csv").exists())
            self.assertEqual(directory.stat().st_mode & 0o777, 0o700)
            self.assertEqual((directory / "input.json").stat().st_mode & 0o777, 0o600)

    def test_artifact_tampering_detected(self):
        with tempfile.TemporaryDirectory() as work:
            run = save_run(make_example(), work)
            (Path(run["directory"]) / "report.md").write_text("changed")
            with self.assertRaisesRegex(ModelError, "hash mismatch"):
                verify_run(work, run["run_id"])

    def test_run_id_traversal_rejected(self):
        for bad in ("../outside", "A" * 32, "abc", "a" * 32 + "/test"):
            with self.subTest(bad=bad), self.assertRaises(ModelError):
                run_directory("/tmp/workspace", bad)

    def test_symlink_run_rejected(self):
        with tempfile.TemporaryDirectory() as work, tempfile.TemporaryDirectory() as outside:
            root = Path(work) / "runs"
            root.mkdir()
            (root / ("a" * 32)).symlink_to(outside)
            with self.assertRaises(ModelError):
                run_directory(work, "a" * 32)

    def test_html_injection_escaped(self):
        with tempfile.TemporaryDirectory() as work:
            m = make_example()
            m["name"] = '</script><script>alert("test")</script>'
            run = save_run(m, work, "base")
            content = Path(run["report"]).read_text()
            self.assertNotIn(m["name"], content)
            self.assertIn("connect-src 'none'", content)

    def test_mcp_lifecycle_run_and_verify_over_stdio(self):
        with tempfile.TemporaryDirectory() as work:
            process = subprocess.Popen([sys.executable, "-m", "harness", "--workspace", work, "mcp"],
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            def rpc(i, method, params=None):
                process.stdin.write(json.dumps({"jsonrpc": "2.0", "id": i, "method": method, "params": params or {}}) + "\n")
                process.stdin.flush()
                return json.loads(process.stdout.readline())["result"]
            try:
                init = rpc(1, "initialize", {"protocolVersion": "2025-03-26"})
                self.assertEqual(init["protocolVersion"], "2025-03-26")
                tools = rpc(2, "tools/list")["tools"]
                self.assertEqual(len(tools), 6)
                result = rpc(3, "tools/call", {"name": "finance_run", "arguments": {"model": make_example(), "scenario": "base"}})
                run = json.loads(result["content"][0]["text"])
                verified = rpc(4, "tools/call", {"name": "finance_verify", "arguments": {"run_id": run["run_id"]}})
                self.assertTrue(json.loads(verified["content"][0]["text"])["verified"])
                error = rpc(5, "tools/call", {"name": "finance_run", "arguments": {"model": {}}})
                self.assertTrue(error["isError"])
            finally:
                process.stdin.close()
                process.wait(timeout=10)
                process.stdout.close()
                process.stderr.close()

    def test_mcp_rejects_extra_arguments(self):
        with self.assertRaises(ModelError):
            call("finance_doctor", {"shell": "cat /etc/passwd"}, "/tmp/workspace")

    def test_init_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as work:
            file = Path(work) / "model.json"
            file.write_text("owner's existing work")
            result = subprocess.run([sys.executable, "-m", "harness", "init", "--output", str(file)], capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(file.read_text(), "owner's existing work")


if __name__ == "__main__":
    unittest.main()
