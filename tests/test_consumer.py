import json
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from consumer.consumer import consolidate_data, process_message


@pytest.fixture
def mock_session():
    """Fixture to create a mocked SQLAlchemy session."""
    session = MagicMock()
    session.query.return_value.filter_by.return_value.first.return_value = None
    return session


@pytest.fixture
def mock_data():
    """Sample mock data for testing."""
    return {
        "project_name": "TestService",
        "owner_team": "TeamA",
        "repository_source": "RepoA",
        "lifecycle_status": "active",
    }


def test_consolidate_data_new_entry(mock_session, mock_data):
    """Test adding a new service entry."""
    consolidate_data(mock_session, mock_data)
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


def test_consolidate_data_existing_entry(mock_session, mock_data):
    """Test updating an existing service entry."""
    mock_service = MagicMock()
    mock_service.owner_team = "TeamB"
    mock_service.repository_source = "RepoA"
    mock_service.lifecycle_status = "active"

    mock_session.query.return_value.filter_by.return_value.first.return_value = (
        mock_service
    )

    consolidate_data(mock_session, mock_data)

    assert mock_service.owner_team == mock_data["owner_team"]
    assert mock_service.lifecycle_status == mock_data["lifecycle_status"]
    mock_session.commit.assert_called_once()


def test_consolidate_data_database_error(mock_session, mock_data):
    """Test handling a database error."""
    mock_session.commit.side_effect = SQLAlchemyError("Database error")
    consolidate_data(mock_session, mock_data)
    mock_session.rollback.assert_called_once()


def test_process_message_success(mock_session, mock_data):
    """Test processing a valid message."""
    with patch("consumer.consumer.consolidate_data") as mock_consolidate:
        process_message(mock_session, json.dumps(mock_data))
        mock_consolidate.assert_called_once_with(mock_session, mock_data)


def test_process_message_invalid_json(mock_session):
    """Test processing an invalid message."""
    invalid_message = "{'invalid_json': true}"  # Invalid JSON format
    with patch("consumer.consumer.logging.error") as mock_error:
        process_message(mock_session, invalid_message)
        mock_error.assert_called_once()


def test_process_message_unexpected_error(mock_session, mock_data):
    """Test unexpected error during message processing."""
    with patch(
        "consumer.consumer.consolidate_data", side_effect=Exception("Unexpected error")
    ):
        with patch("consumer.consumer.logging.error") as mock_error:
            process_message(mock_session, json.dumps(mock_data))
            mock_error.assert_called_once()
