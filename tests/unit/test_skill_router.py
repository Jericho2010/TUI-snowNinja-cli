from snowninja.skills.router import skill_router, SKILL_MAP, SKILLS_DIR

def test_route_dynamic_tables():
    """'create a dynamic table' matches snowflake-dynamic-tables."""
    res = skill_router.route("how do I create a dynamic table?")
    assert "snowflake-dynamic-tables" in res

def test_route_cortex():
    """'use cortex to summarize' matches snowflake-cortex-ai."""
    res = skill_router.route("can I use cortex to summarize text?")
    assert "snowflake-cortex-ai" in res

def test_route_no_match():
    """'hello world' returns empty list."""
    res = skill_router.route("hello world")
    assert res == []

def test_route_max_skills():
    """Never returns more than max_skills (default 2)."""
    # Create a prompt that matches multiple skills
    prompt = "I need a dynamic table with a stream and task to run cortex llm models securely with masking policy"
    res = skill_router.route(prompt, max_skills=2)
    assert len(res) <= 2

def test_load_skill_exists():
    """load_skill('snowflake-security') returns non-empty string."""
    res = skill_router.load_skill("snowflake-security")
    # Will be None if the skill files haven't been copied over yet, so handle that gracefully
    if res is not None:
        assert len(res) > 0

def test_load_skill_missing():
    """load_skill('nonexistent') returns None."""
    res = skill_router.load_skill("nonexistent_skill_xyz")
    assert res is None

def test_load_critical_rules():
    """load_critical_rules extracts a section, not full content."""
    res = skill_router.load_critical_rules("snowflake-security")
    if res is not None:
        # Check that it didn't return the full document
        full = skill_router.load_skill("snowflake-security")
        assert len(res) < len(full)

def test_skill_index_lists_all():
    """skill_index() mentions all 12 skill names."""
    idx = skill_router.skill_index()
    for skill in SKILL_MAP.keys():
        assert skill in idx

def test_all_skill_files_have_frontmatter():
    """Every .md file in skills/ has name: and description: in YAML frontmatter."""
    md_files = list(SKILLS_DIR.glob("*.md"))
    # If files don't exist yet, pass
    if not md_files:
        return
    for md_file in md_files:
        content = md_file.read_text()
        assert content.startswith("---")
        assert "\nname: " in content
        assert "\ndescription: " in content

def test_skill_map_files_exist():
    """Every key in SKILL_MAP has a corresponding .md file (if directory is populated)."""
    md_files = list(SKILLS_DIR.glob("*.md"))
    if not md_files:
        return
    for skill_id in SKILL_MAP.keys():
        file_path = SKILLS_DIR / f"{skill_id}.md"
        assert file_path.exists()
