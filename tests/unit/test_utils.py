"""Unit tests for notehub.utils module."""

from notehub.context import StoreContext
from notehub.gh_wrapper import GhError
from notehub.utils import format_note_header, resolve_note_ident


class TestResolveNoteIdent:
    """Tests for resolve_note_ident function."""

    def test_direct_issue_number(self):
        """Should return issue number directly when ident is numeric."""
        context = StoreContext(host="github.com", org="testorg", repo="testrepo")

        issue_num, error = resolve_note_ident(context, "123")

        assert issue_num == 123
        assert error is None

    def test_title_regex_single_match(self, mocker):
        """Should resolve title regex to issue number when single match found."""
        context = StoreContext(host="github.com", org="testorg", repo="testrepo")

        # Mock list_issues to return sample issues
        mock_issues = [
            {"number": 10, "title": "Bug in login form"},
            {"number": 11, "title": "Feature request for dashboard"},
        ]
        mocker.patch("notehub.utils.list_issues", return_value=mock_issues)

        issue_num, error = resolve_note_ident(context, "bug.*login")

        assert issue_num == 10
        assert error is None

    def test_title_regex_multiple_matches(self, mocker, capsys):
        """Should return first match and warn when regex matches multiple issues."""
        context = StoreContext(host="github.com", org="testorg", repo="testrepo")

        # Mock list_issues to return sample issues
        mock_issues = [
            {"number": 10, "title": "Bug in login form"},
            {"number": 12, "title": "Bug in signup form"},
        ]
        mocker.patch("notehub.utils.list_issues", return_value=mock_issues)

        issue_num, error = resolve_note_ident(context, "bug")

        assert issue_num == 10
        assert error is None

        # Check warning was printed to stderr
        captured = capsys.readouterr()
        assert "matched 2 issues" in captured.err

    def test_title_regex_no_match(self, mocker):
        """Should return error when regex doesn't match any issues."""
        context = StoreContext(host="github.com", org="testorg", repo="testrepo")

        # Mock list_issues to return sample issues
        mock_issues = [
            {"number": 10, "title": "Bug in login form"},
        ]
        mocker.patch("notehub.utils.list_issues", return_value=mock_issues)

        issue_num, error = resolve_note_ident(context, "nonexistent")

        assert issue_num is None
        assert "No issues found matching 'nonexistent'" in error

    def test_title_regex_case_insensitive(self, mocker):
        """Should match title regex case-insensitively."""
        context = StoreContext(host="github.com", org="testorg", repo="testrepo")

        # Mock list_issues to return sample issues
        mock_issues = [
            {"number": 10, "title": "Bug in Login Form"},
        ]
        mocker.patch("notehub.utils.list_issues", return_value=mock_issues)

        issue_num, error = resolve_note_ident(context, "bug.*login")

        assert issue_num == 10
        assert error is None

    def test_gh_error_handling(self, mocker):
        """Should return error message when list_issues raises GhError."""
        context = StoreContext(host="github.com", org="testorg", repo="testrepo")

        # Mock list_issues to raise GhError
        gh_error = GhError(1, "API rate limit exceeded\n")
        mocker.patch("notehub.utils.list_issues", side_effect=gh_error)

        issue_num, error = resolve_note_ident(context, "bug")

        assert issue_num is None
        assert "Failed to list issues: API rate limit exceeded" in error


class TestFormatNoteHeader:
    """Tests for format_note_header function."""

    def test_format_basic_issue(self):
        """Should format issue with number and title."""
        issue = {"number": 42, "title": "Test Issue Title"}

        result = format_note_header(issue)

        assert result == "[#42] Test Issue Title"

    def test_format_issue_with_special_chars(self):
        """Should handle special characters in title."""
        issue = {"number": 123, "title": "Bug: Login fails with @special & <chars>"}

        result = format_note_header(issue)

        assert result == "[#123] Bug: Login fails with @special & <chars>"

    def test_format_issue_with_long_title(self):
        """Should format issue with long title without truncation."""
        issue = {
            "number": 1,
            "title": (
                "This is a very long title that exceeds normal length expectations"
            ),
        }

        result = format_note_header(issue)

        assert (
            result
            == "[#1] This is a very long title that exceeds normal length expectations"
        )
