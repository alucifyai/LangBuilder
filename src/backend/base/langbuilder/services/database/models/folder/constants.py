DEFAULT_FOLDER_DESCRIPTION = "Manage your own flows. Download and upload projects."
DEFAULT_FOLDER_NAME = "Starter Project"


def get_starter_project_name(username: str) -> str:
    """
    Get the personalized Starter Project name for a user.

    Args:
        username: The username of the user

    Returns:
        The personalized Starter Project name (e.g., "Starter Project - arnab")
    """
    return f"{DEFAULT_FOLDER_NAME} - {username}"


def is_starter_project(folder_name: str) -> bool:
    """
    Check if a folder name indicates it's a Starter Project.

    This supports both the old naming convention ("Starter Project") and
    the new personalized naming convention ("Starter Project - username").

    Args:
        folder_name: The name of the folder to check

    Returns:
        True if the folder is a Starter Project, False otherwise
    """
    if not folder_name:
        return False

    # Check exact match for old naming convention
    if folder_name == DEFAULT_FOLDER_NAME:
        return True

    # Check if it starts with "Starter Project - " for new naming convention
    return folder_name.startswith(f"{DEFAULT_FOLDER_NAME} - ")
