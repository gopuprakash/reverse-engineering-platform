try:
    import tree_sitter_c_sharp
    print("[SUCCESS] Imported tree_sitter_c_sharp")
    try:
        lang = tree_sitter_c_sharp.language()
        print(f"[SUCCESS] Got language object: {lang}")
    except Exception as e:
        print(f"[FAILED] tree_sitter_c_sharp.language(): {e}")

except ImportError as e:
    print(f"[FAILED] Import tree_sitter_c_sharp: {e}")

try:
    from tree_sitter_language_pack import get_language
    print("Testing get_language('c_sharp')...")
    l = get_language('c_sharp')
    print("Found.")
except Exception as e:
    print(f"get_language error: {e}")
