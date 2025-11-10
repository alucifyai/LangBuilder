"""
Unit tests for RBAC initialization during application startup.

These tests verify that RBAC data initialization is properly integrated
into the application startup sequence in main.py. They validate the code
structure and ensure the initialize_rbac_data function is called in the
correct location within the lifespan function.
"""

import inspect

import pytest

from langbuilder.main import get_lifespan


@pytest.mark.asyncio
async def test_rbac_initialization_present_in_lifespan():
    """Test that RBAC initialization code is present in the lifespan function."""
    # Get the lifespan function source code
    lifespan_func = get_lifespan()
    source = inspect.getsource(lifespan_func)

    # Check that initialize_rbac_data is imported and called
    assert "from langbuilder.initial_setup.rbac_setup import initialize_rbac_data" in source
    assert "await initialize_rbac_data(session)" in source


@pytest.mark.asyncio
async def test_rbac_initialization_after_super_user():
    """Test that RBAC initialization comes after super user initialization."""
    lifespan_func = get_lifespan()
    source = inspect.getsource(lifespan_func)

    # Find positions of key initialization steps
    super_user_pos = source.find("initialize_super_user_if_needed")
    rbac_init_pos = source.find("initialize_rbac_data")

    # RBAC should come after super user initialization
    assert super_user_pos > 0, "Super user initialization not found"
    assert rbac_init_pos > 0, "RBAC initialization not found"
    assert rbac_init_pos > super_user_pos, "RBAC initialization should come after super user initialization"


@pytest.mark.asyncio
async def test_rbac_initialization_before_bundle_loading():
    """Test that RBAC initialization comes before bundle loading."""
    lifespan_func = get_lifespan()
    source = inspect.getsource(lifespan_func)

    # Find positions
    rbac_init_pos = source.find("initialize_rbac_data")
    bundle_loading_pos = source.find("load_bundles_with_error_handling")

    # RBAC should come before bundle loading
    assert rbac_init_pos > 0, "RBAC initialization not found"
    assert bundle_loading_pos > 0, "Bundle loading not found"
    assert rbac_init_pos < bundle_loading_pos, "RBAC initialization should come before bundle loading"


@pytest.mark.asyncio
async def test_rbac_initialization_after_services():
    """Test that RBAC initialization comes after services initialization."""
    lifespan_func = get_lifespan()
    source = inspect.getsource(lifespan_func)

    # Find positions
    services_init_pos = source.find("initialize_services")
    rbac_init_pos = source.find("initialize_rbac_data")

    # RBAC should come after services initialization
    assert services_init_pos > 0, "Services initialization not found"
    assert rbac_init_pos > 0, "RBAC initialization not found"
    assert rbac_init_pos > services_init_pos, "RBAC initialization should come after services initialization"


@pytest.mark.asyncio
async def test_rbac_initialization_uses_db_service():
    """Test that RBAC initialization uses get_db_service() correctly."""
    lifespan_func = get_lifespan()
    source = inspect.getsource(lifespan_func)

    # Check that get_db_service().with_session() is used
    assert "get_db_service().with_session()" in source
    assert "async with get_db_service().with_session() as session:" in source


@pytest.mark.asyncio
async def test_rbac_initialization_has_logging():
    """Test that RBAC initialization has debug logging."""
    lifespan_func = get_lifespan()
    source = inspect.getsource(lifespan_func)

    # Check for logging statements
    assert 'logger.debug("Initializing RBAC data")' in source
    assert 'logger.debug(f"RBAC data initialized in' in source


@pytest.mark.asyncio
async def test_rbac_initialization_tracks_timing():
    """Test that RBAC initialization tracks and logs timing."""
    lifespan_func = get_lifespan()
    source = inspect.getsource(lifespan_func)

    # Check for timing tracking
    lines = source.split("\n")

    # Find RBAC initialization section
    rbac_section_found = False
    has_current_time = False
    has_timing_log = False

    for i, line in enumerate(lines):
        if "Initializing RBAC data" in line:
            rbac_section_found = True
            # Check previous lines for current_time assignment
            for j in range(max(0, i - 3), i):
                if "current_time = asyncio.get_event_loop().time()" in lines[j]:
                    has_current_time = True
                    break
            # Check following lines for timing log
            for j in range(i, min(len(lines), i + 10)):
                if "RBAC data initialized in" in lines[j] and "current_time" in lines[j]:
                    has_timing_log = True
                    break
            break

    assert rbac_section_found, "RBAC initialization section not found"
    assert has_current_time, "Timing measurement (current_time) not found before RBAC init"
    assert has_timing_log, "Timing log not found after RBAC init"


@pytest.mark.asyncio
async def test_get_db_service_imported_in_main():
    """Test that get_db_service is imported in main.py."""
    import langbuilder.main as main_module

    # Check that get_db_service is available in main module
    assert hasattr(main_module, "get_db_service"), "get_db_service should be imported in main.py"


@pytest.mark.asyncio
async def test_rbac_setup_importable():
    """Test that initialize_rbac_data can be imported."""
    from langbuilder.initial_setup.rbac_setup import initialize_rbac_data

    # Check it's a coroutine function
    assert inspect.iscoroutinefunction(initialize_rbac_data), "initialize_rbac_data should be async"


@pytest.mark.asyncio
async def test_lifespan_function_structure():
    """Test that the lifespan function maintains proper structure with RBAC init."""
    lifespan_func = get_lifespan()
    source = inspect.getsource(lifespan_func)

    # Check key structural elements are present in order
    elements = [
        "initialize_services",
        "setup_llm_caching",
        "initialize_super_user_if_needed",
        "initialize_rbac_data",  # Our addition
        "load_bundles_with_error_handling",
        "get_and_cache_all_types_dict",
        "create_or_update_starter_projects",
        "telemetry_service.start",
        "load_flows_from_directory",
        "init_mcp_servers",
    ]

    last_pos = 0
    for element in elements:
        pos = source.find(element)
        assert pos > 0, f"{element} not found in lifespan"
        assert pos > last_pos, f"{element} should come after previous elements"
        last_pos = pos


@pytest.mark.asyncio
async def test_rbac_initialization_session_management():
    """Test that RBAC initialization properly uses async session context manager."""
    lifespan_func = get_lifespan()
    source = inspect.getsource(lifespan_func)

    # Extract RBAC initialization section
    lines = source.split("\n")
    rbac_section = []
    in_rbac_section = False

    for line in lines:
        if "Initializing RBAC data" in line:
            in_rbac_section = True
        if in_rbac_section:
            rbac_section.append(line)
            if "RBAC data initialized in" in line:
                break

    rbac_code = "\n".join(rbac_section)

    # Verify async context manager usage
    assert "async with get_db_service().with_session() as session:" in rbac_code
    assert "await initialize_rbac_data(session)" in rbac_code


@pytest.mark.asyncio
async def test_rbac_initialization_follows_existing_patterns():
    """Test that RBAC initialization follows the same pattern as other initializations."""
    lifespan_func = get_lifespan()
    source = inspect.getsource(lifespan_func)

    # RBAC init should follow the same pattern:
    # 1. current_time assignment
    # 2. logger.debug message
    # 3. actual initialization
    # 4. logger.debug timing message

    lines = source.split("\n")
    pattern_elements = []

    for i, line in enumerate(lines):
        if "Initializing RBAC data" in line:
            # Check pattern
            # Previous line should have current_time
            if i > 0 and "current_time = asyncio.get_event_loop().time()" in lines[i - 1]:
                pattern_elements.append("timing_start")
            # Current line is debug message
            pattern_elements.append("debug_start")
            # Next few lines should have initialization
            for j in range(i + 1, min(len(lines), i + 10)):
                if "await initialize_rbac_data" in lines[j]:
                    pattern_elements.append("init_call")
                if "RBAC data initialized in" in lines[j]:
                    pattern_elements.append("debug_end")
            break

    # Verify all pattern elements are present
    assert "timing_start" in pattern_elements, "Missing timing start"
    assert "debug_start" in pattern_elements, "Missing debug start message"
    assert "init_call" in pattern_elements, "Missing initialization call"
    assert "debug_end" in pattern_elements, "Missing debug end message"


@pytest.mark.asyncio
async def test_rbac_initialization_import_location():
    """Test that initialize_rbac_data import is in the correct location (inline)."""
    lifespan_func = get_lifespan()
    source = inspect.getsource(lifespan_func)

    # The import should be inline (within the function), not at module level
    # This is the pattern used in the codebase
    lines = source.split("\n")

    import_found = False
    import_is_inline = False

    for i, line in enumerate(lines):
        if "from langbuilder.initial_setup.rbac_setup import initialize_rbac_data" in line:
            import_found = True
            # Check if it's indented (inline)
            if line.startswith("        ") or line.startswith("\t"):
                import_is_inline = True
            break

    assert import_found, "initialize_rbac_data import not found"
    assert import_is_inline, "initialize_rbac_data import should be inline (within function)"
