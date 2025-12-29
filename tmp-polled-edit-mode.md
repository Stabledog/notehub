## Plan: Continuous save for edit command

Transform the `edit` command from a blocking wait-for-exit model to an interactive polling loop that monitors both the editor process and file changes, allowing users to save updates to GitHub without closing their editor.

### Steps

1. **Add file change monitoring loop** to `edit_in_temp_file` (src/notehub/commands/edit.py#L64-L118): Replace the blocking `subprocess.run()` with `subprocess.Popen()`, then poll both the process state (`poll()`) and file mtime in a loop with ~500ms sleep intervals.

2. **Implement console input handler** using `msvcrt.kbhit()` on Windows (or `select.select()` on Unix) to check for keypress without blocking, watching for a trigger key (like `s` or `Enter`) to signal "save now".

3. **Extract save logic** from `_run_edit` (src/notehub/commands/edit.py#L125-L175) into a reusable helper function that reads the temp file, compares to last-saved content (not just original), handles empty-body confirmation, and calls `gh_wrapper.gh_issue_edit()`.

4. **Update main flow** in `_run_edit` (src/notehub/commands/edit.py#L125-L175): Call the new polling version of `edit_in_temp_file` which returns when editor exits, then perform final save if any unsaved changes remain.

5. **Extend tests** in test_commands.py and test_commands_extended.py: Mock `subprocess.Popen` and add test cases for mid-edit saves, multiple saves, no-change scenarios, and cleanup behavior.

### Further Considerations

1. **Polling interval**: 500ms balances responsiveness vs CPU usage—adjust if needed based on user feedback or performance testing.
2. **User feedback during polling**: Should the tool print "Saved to GitHub" each time, or maintain silence? Could add a `--verbose` flag or always show feedback for clarity.
3. **Cross-platform console input**: Windows (`msvcrt`) and Unix (`select`/`termios`) require different implementations—consider abstracting into a utility function or using a library like `readchar` to simplify.
