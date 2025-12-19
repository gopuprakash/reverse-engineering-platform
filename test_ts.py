try:
    from tree_sitter_language_pack import get_language, get_parser
    
    identifiers = ["c_sharp", "csharp", "c-sharp", "cs"]
    
    print("Testing identifiers...")
    for lang in identifiers:
        try:
            parser = get_parser(lang)
            print(f"[SUCCESS] '{lang}' loaded successfully.")
        except Exception as e:
            print(f"[FAILED] '{lang}': {e}")

except ImportError:
    print("tree_sitter_language_pack not installed.")
