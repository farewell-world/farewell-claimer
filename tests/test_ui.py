"""
Tests for UI helper functions.
"""

import pytest
from unittest.mock import patch, MagicMock
from io import StringIO

import farewell_claimer
from farewell_claimer import (
    print_banner,
    print_section,
    print_success,
    print_error,
    print_warning,
    print_info,
    prompt,
    confirm,
    select_option,
)


class TestPrintFunctions:
    """Tests for print helper functions."""

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_banner_outputs_text(self, mock_stdout):
        """Test that print_banner outputs something."""
        print_banner()
        output = mock_stdout.getvalue()
        # Should contain the banner text
        assert "FAREWELL" in output or len(output) > 100

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_section_outputs_title(self, mock_stdout):
        """Test that print_section outputs the title."""
        print_section("Test Section")
        output = mock_stdout.getvalue()
        assert "Test Section" in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_success_outputs_message(self, mock_stdout):
        """Test that print_success outputs the message."""
        print_success("Operation successful")
        output = mock_stdout.getvalue()
        assert "Operation successful" in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_error_outputs_message(self, mock_stdout):
        """Test that print_error outputs the message."""
        print_error("Something went wrong")
        output = mock_stdout.getvalue()
        assert "Something went wrong" in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_warning_outputs_message(self, mock_stdout):
        """Test that print_warning outputs the message."""
        print_warning("Be careful")
        output = mock_stdout.getvalue()
        assert "Be careful" in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_info_outputs_message(self, mock_stdout):
        """Test that print_info outputs the message."""
        print_info("Here's some information")
        output = mock_stdout.getvalue()
        assert "Here's some information" in output


class TestPromptFunction:
    """Tests for the prompt function."""

    @patch('builtins.input', return_value="test input")
    def test_prompt_returns_user_input(self, mock_input):
        """Test that prompt returns user input."""
        result = prompt("Enter value")
        assert result == "test input"

    @patch('builtins.input', return_value="")
    def test_prompt_returns_default_when_empty(self, mock_input):
        """Test that prompt returns default when input is empty."""
        result = prompt("Enter value", default="default_value")
        assert result == "default_value"

    @patch('builtins.input', return_value="custom")
    def test_prompt_returns_input_over_default(self, mock_input):
        """Test that prompt returns input even when default exists."""
        result = prompt("Enter value", default="default_value")
        assert result == "custom"


class TestConfirmFunction:
    """Tests for the confirm function."""

    @patch('builtins.input', return_value="y")
    def test_confirm_yes(self, mock_input):
        """Test confirm returns True for 'y'."""
        result = confirm("Continue?")
        assert result is True

    @patch('builtins.input', return_value="yes")
    def test_confirm_yes_full(self, mock_input):
        """Test confirm returns True for 'yes'."""
        result = confirm("Continue?")
        assert result is True

    @patch('builtins.input', return_value="n")
    def test_confirm_no(self, mock_input):
        """Test confirm returns False for 'n'."""
        result = confirm("Continue?")
        assert result is False

    @patch('builtins.input', return_value="")
    def test_confirm_default_true(self, mock_input):
        """Test confirm returns default True when empty."""
        result = confirm("Continue?", default=True)
        assert result is True

    @patch('builtins.input', return_value="")
    def test_confirm_default_false(self, mock_input):
        """Test confirm returns default False when empty."""
        result = confirm("Continue?", default=False)
        assert result is False

    @patch('builtins.input', return_value="Y")
    def test_confirm_case_insensitive(self, mock_input):
        """Test confirm is case insensitive."""
        result = confirm("Continue?")
        assert result is True


class TestSelectOptionFunction:
    """Tests for the select_option function."""

    @patch('builtins.input', return_value="1")
    @patch('sys.stdout', new_callable=StringIO)
    def test_select_option_first(self, mock_stdout, mock_input):
        """Test selecting first option."""
        options = ["Option A", "Option B", "Option C"]
        result = select_option(options)
        assert result == 0

    @patch('builtins.input', return_value="2")
    @patch('sys.stdout', new_callable=StringIO)
    def test_select_option_second(self, mock_stdout, mock_input):
        """Test selecting second option."""
        options = ["Option A", "Option B", "Option C"]
        result = select_option(options)
        assert result == 1

    @patch('builtins.input', return_value="3")
    @patch('sys.stdout', new_callable=StringIO)
    def test_select_option_last(self, mock_stdout, mock_input):
        """Test selecting last option."""
        options = ["Option A", "Option B", "Option C"]
        result = select_option(options)
        assert result == 2

    @patch('builtins.input', side_effect=["invalid", "1"])
    @patch('sys.stdout', new_callable=StringIO)
    def test_select_option_retry_on_invalid(self, mock_stdout, mock_input):
        """Test that invalid input prompts retry."""
        options = ["Option A", "Option B"]
        result = select_option(options)
        # Should have called input twice (invalid, then valid)
        assert mock_input.call_count == 2
        assert result == 0

    @patch('builtins.input', side_effect=["0", "5", "2"])
    @patch('sys.stdout', new_callable=StringIO)
    def test_select_option_retry_out_of_range(self, mock_stdout, mock_input):
        """Test that out of range input prompts retry."""
        options = ["Option A", "Option B"]
        result = select_option(options)
        assert mock_input.call_count == 3
        assert result == 1

    @patch('builtins.input', return_value="1")
    @patch('sys.stdout', new_callable=StringIO)
    def test_select_option_displays_options(self, mock_stdout, mock_input):
        """Test that options are displayed."""
        options = ["First Option", "Second Option"]
        select_option(options, "Choose one:")
        output = mock_stdout.getvalue()
        assert "First Option" in output
        assert "Second Option" in output
        assert "Choose one:" in output


class TestClearScreen:
    """Tests for clear_screen function."""

    @patch('os.system')
    def test_clear_screen_unix(self, mock_system):
        """Test clear_screen on Unix."""
        with patch('os.name', 'posix'):
            farewell_claimer.clear_screen()
            mock_system.assert_called_with('clear')

    @patch('os.system')
    def test_clear_screen_windows(self, mock_system):
        """Test clear_screen on Windows."""
        with patch('os.name', 'nt'):
            farewell_claimer.clear_screen()
            mock_system.assert_called_with('cls')
