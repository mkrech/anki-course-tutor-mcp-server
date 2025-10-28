# In-Memory Storage Migration

## Why
The application encountered read-only filesystem errors when deployed via `uvx` from GitHub. The package installation directory is read-only, preventing creation of data directories for session and progress persistence. This blocked the primary deployment method for MCP servers.

## What Changes
- **BREAKING**: Removed file-based persistence for sessions and progress
- Migrated `SessionManager` to pure in-memory storage using dictionaries
- Migrated `ProgressTracker` to pure in-memory storage using dictionaries
- Added deep copying in `ProgressTracker.save()` to prevent object mutation
- Embedded `default_config.yaml` in package using `importlib.resources`
- Removed directory creation logic from `__main__.py`
- Updated `mcp_server.py` to initialize managers without directory paths
- Fixed all test suites to work with in-memory assumptions

## Impact
**Affected specs:**
- session-management
- progress-tracking

**Affected code:**
- `src/anki_course_tutor/session_manager.py` - Complete rewrite
- `src/anki_course_tutor/progress_tracker.py` - Complete rewrite
- `src/anki_course_tutor/mcp_server.py` - Updated initialization
- `src/anki_course_tutor/__main__.py` - Removed file operations
- `src/anki_course_tutor/config.py` - Added embedded config support
- All test files - Updated for in-memory behavior

**Benefits:**
- ✅ Works with uvx deployment from GitHub (primary use case)
- ✅ No file system permissions needed
- ✅ Simpler debugging (no file I/O overhead)
- ✅ Faster test execution
- ✅ No data corruption from incomplete writes

**Trade-offs:**
- ❌ Session data lost on server restart
- ❌ No persistence between sessions
- ❌ Cannot resume sessions after restart
- ❌ No backup/recovery from files

**Migration:**
- No user migration needed (breaking change accepted for deployment fix)
- Old session/progress JSON files in `./data/` are no longer read or written
