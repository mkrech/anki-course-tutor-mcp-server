## 1. Core Implementation
- [x] 1.1 Rewrite `SessionManager` to use in-memory `dict[str, Session]`
- [x] 1.2 Remove file I/O operations from `SessionManager`
- [x] 1.3 Rewrite `ProgressTracker` to use in-memory dictionaries
- [x] 1.4 Add `deepcopy()` to prevent object mutation bugs
- [x] 1.5 Fix import: move `CardProgress` from models.card to models.session

## 2. Configuration
- [x] 2.1 Embed `default_config.yaml` in package
- [x] 2.2 Update `pyproject.toml` with shared-data section
- [x] 2.3 Add `importlib.resources` fallback in `ConfigLoader`
- [x] 2.4 Set empty strings for storage paths in default config

## 3. Server Integration
- [x] 3.1 Update `mcp_server.initialize_managers()` signature
- [x] 3.2 Remove `sessions_dir` and `progress_dir` parameters
- [x] 3.3 Remove directory creation from `__main__.py`
- [x] 3.4 Update logging to reflect in-memory storage

## 4. Testing
- [x] 4.1 Fix `test_session_manager.py` for in-memory behavior
- [x] 4.2 Fix `test_progress_tracker.py` for in-memory behavior
- [x] 4.3 Remove file-system specific tests (backups, JSON corruption)
- [x] 4.4 Fix duplicate function definitions in test files
- [x] 4.5 Update `test_anki_client.py` API signature test
- [x] 4.6 Verify all 101 tests pass

## 5. Deployment
- [x] 5.1 Update `.vscode/mcp.json` for uvx with GitHub URLs
- [x] 5.2 Test with `uvx --from git+https://github.com/...`
- [x] 5.3 Commit and push all changes to GitHub
