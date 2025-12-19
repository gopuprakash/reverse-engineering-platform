from src.chunking import UniversalChunker

csharp_code = """
using System;

namespace Demo {
    public class MyClass {
        public void MyMethod() {
            Console.WriteLine("Hello");
        }
    }
}
"""

try:
    print("Testing UniversalChunker with language='cs'...")
    chunker = UniversalChunker(csharp_code, language_id="cs")
    
    if chunker.config:
        print("[SUCCESS] Config loaded for C#.")
        chunks = chunker.chunk()
        print(f"Generated {len(chunks)} chunks.")
        for c in chunks:
            print(f" - {c.type}: {c.name}")
    else:
        print("[FAILED] Config is None (Fallback failed).")

except Exception as e:
    print(f"[ERROR] {e}")
