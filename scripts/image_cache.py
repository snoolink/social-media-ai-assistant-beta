"""
image_cache.py

Intelligent caching system for image analysis results.
Saves analysis results to avoid re-analyzing the same images.
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class ImageAnalysisCache:
    """
    Cache system that stores image analysis results by:
    - Image hash (content-based, not filename)
    - Query hash (expanded query description)
    
    This allows:
    1. Same image with different filenames = cached
    2. Same query phrasing = cached (via query expansion cache)
    3. Different queries on same images = separate cache entries
    """
    
    def __init__(self, cache_file: str = "image_analysis_cache.json"):
        self.cache_file = Path(__file__).parent / cache_file
        self.cache = self._load_cache()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "total_queries": 0
        }
    
    def _load_cache(self) -> Dict:
        """Load cache from JSON file"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    # Migrate old format if needed
                    if isinstance(data, dict) and "cache" in data:
                        return data["cache"]
                    return data
            except Exception as e:
                print(f"Warning: Failed to load cache: {e}")
                return {}
        return {}
    
    def _save_cache(self):
        """Save cache to JSON file"""
        try:
            # Add metadata
            data = {
                "cache": self.cache,
                "metadata": {
                    "last_updated": datetime.now().isoformat(),
                    "total_entries": len(self.cache),
                    "stats": self.stats
                }
            }
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save cache: {e}")
    
    def _get_image_hash(self, image_path: Path) -> str:
        """
        Generate content-based hash of image file.
        Uses first 1MB of file for speed (good enough for uniqueness).
        """
        try:
            with open(image_path, 'rb') as f:
                # Read first 1MB or entire file if smaller
                content = f.read(1024 * 1024)
                return hashlib.md5(content).hexdigest()
        except Exception as e:
            # Fallback to path-based hash if file can't be read
            return hashlib.md5(str(image_path).encode()).hexdigest()
    
    def _get_query_hash(self, expanded_query: str) -> str:
        """Generate hash of expanded query"""
        return hashlib.md5(expanded_query.encode()).hexdigest()
    
    def _get_cache_key(self, image_path: Path, expanded_query: str) -> str:
        """Generate unique cache key for image + query combination"""
        img_hash = self._get_image_hash(image_path)
        query_hash = self._get_query_hash(expanded_query)
        return f"{img_hash}:{query_hash}"
    
    def get(self, image_path: Path, expanded_query: str) -> Optional[Tuple[bool, str]]:
        """
        Retrieve cached analysis result.
        
        Returns:
            (is_match, explanation) if cached, None if not found
        """
        cache_key = self._get_cache_key(image_path, expanded_query)
        
        if cache_key in self.cache:
            self.stats["hits"] += 1
            entry = self.cache[cache_key]
            return (entry["is_match"], entry["explanation"])
        
        self.stats["misses"] += 1
        return None
    
    def set(self, image_path: Path, expanded_query: str, is_match: bool, explanation: str):
        """
        Store analysis result in cache.
        """
        cache_key = self._get_cache_key(image_path, expanded_query)
        
        self.cache[cache_key] = {
            "is_match": is_match,
            "explanation": explanation,
            "image_path": str(image_path),  # For reference only
            "timestamp": datetime.now().isoformat()
        }
    
    def save(self):
        """Persist cache to disk"""
        self._save_cache()
    
    def get_stats(self) -> Dict:
        """Get cache performance statistics"""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total * 100) if total > 0 else 0
        
        return {
            "total_cached_entries": len(self.cache),
            "cache_hits": self.stats["hits"],
            "cache_misses": self.stats["misses"],
            "hit_rate": f"{hit_rate:.1f}%",
            "cache_file_size": self._get_cache_file_size()
        }
    
    def _get_cache_file_size(self) -> str:
        """Get human-readable cache file size"""
        if not self.cache_file.exists():
            return "0 KB"
        
        size_bytes = self.cache_file.stat().st_size
        
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    def clear_old_entries(self, days: int = 30):
        """
        Remove cache entries older than specified days.
        Useful for preventing cache from growing too large.
        """
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        initial_count = len(self.cache)
        
        # Filter out old entries
        self.cache = {
            key: value for key, value in self.cache.items()
            if datetime.fromisoformat(value["timestamp"]) > cutoff_date
        }
        
        removed_count = initial_count - len(self.cache)
        self._save_cache()
        
        return removed_count
    
    def clear_by_query(self, expanded_query: str):
        """Remove all cache entries for a specific query"""
        query_hash = self._get_query_hash(expanded_query)
        initial_count = len(self.cache)
        
        self.cache = {
            key: value for key, value in self.cache.items()
            if not key.endswith(f":{query_hash}")
        }
        
        removed_count = initial_count - len(self.cache)
        self._save_cache()
        
        return removed_count
    
    def clear_all(self):
        """Clear entire cache"""
        count = len(self.cache)
        self.cache = {}
        self._save_cache()
        return count
    
    def get_queries_analyzed(self) -> List[str]:
        """Get list of unique queries that have been cached"""
        query_hashes = set()
        for key in self.cache.keys():
            _, query_hash = key.split(":", 1)
            query_hashes.add(query_hash)
        return list(query_hashes)


# -------------------------
# CLI Testing Interface
# -------------------------
if __name__ == "__main__":
    import sys
    
    print("📦 Image Analysis Cache - Management Tool\n")
    
    cache = ImageAnalysisCache()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "stats":
            stats = cache.get_stats()
            print("Cache Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        
        elif command == "clear":
            count = cache.clear_all()
            print(f"✅ Cleared {count} cache entries")
        
        elif command == "clean":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            count = cache.clear_old_entries(days)
            print(f"✅ Removed {count} entries older than {days} days")
        
        else:
            print(f"Unknown command: {command}")
            print("Available commands: stats, clear, clean [days]")
    
    else:
        stats = cache.get_stats()
        print("Cache Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        print("\nUsage:")
        print("  python image_cache.py stats      - Show cache statistics")
        print("  python image_cache.py clear      - Clear all cache")
        print("  python image_cache.py clean 30   - Remove entries older than 30 days")