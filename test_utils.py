import io

import mock
from google.api_core.exceptions import NotFound

import utils


def test_delete_photos_from_bucket():
    mock_storage_client = mock.MagicMock()
    mock_bucket = mock.MagicMock()
    mock_storage_client.get_bucket.return_value = mock_bucket

    utils.delete_photos_from_bucket(
        mock_storage_client,
        "manuvic/photos/transporteur-de-personne-trapu020",
        "foo"
    )

    mock_bucket.delete_blob.assert_called_once_with(
        "manuvic/photos/transporteur-de-personne-trapu020"
    )


def test_delete_photos_from_bucket_when_bucket_not_found():
    mock_storage_client = mock.MagicMock()
    mock_bucket = mock.MagicMock()
    mock_storage_client.get_bucket.return_value = mock_bucket
    mock_bucket.delete_blob.side_effect = NotFound("message")

    with mock.patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
        utils.delete_photos_from_bucket(
            mock_storage_client,
            "manuvic/photos/transporteur-de-personne-trapu020",
            "not-existing-bucket"
        )

    assert "manuvic/photos/transporteur-de-personne-trapu020 not found" in mock_stdout.getvalue()
