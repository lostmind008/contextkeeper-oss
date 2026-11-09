#!/usr/bin/env python3
"""Minimal fix script for vector search isolation issue"""

# Read the file
with open('rag_agent.py', 'r') as f:
    content = f.read()

# Apply fixes
content = content.replace(
    "path = data.get('path', '')",
    "path = data.get('path', '')\n            project_id = data.get('project_id')  # CRITICAL: Extract project_id"
)

content = content.replace(
    "if not path or not os.path.exists(path):\n                return jsonify({'error': 'Valid path required'}), 400",
    """if not path or not os.path.exists(path):
                return jsonify({'error': 'Valid path required'}), 400
            
            # CRITICAL: Enforce project isolation - require project_id for security
            if not project_id:
                return jsonify({'error': 'project_id required for secure ingestion'}), 400
            
            # Validate project exists
            if project_id not in self.agent.collections:
                # Try to initialize collections in case project was just created
                self.agent._init_project_collections()
                if project_id not in self.agent.collections:
                    return jsonify({'error': f'Project {project_id} not found or not accessible'}), 404"""
)

content = content.replace(
    "self._run_async(self.agent.ingest_file(path))",
    "self._run_async(self.agent.ingest_file(path, project_id))"
)

content = content.replace(
    "self._run_async(self.agent.ingest_directory(path))",
    "self._run_async(self.agent.ingest_directory(path, project_id))"
)

content = content.replace(
    "async def ingest_directory(self, directory: str) -> int:",
    "async def ingest_directory(self, directory: str, project_id: str = None) -> int:"
)

content = content.replace(
    "chunks = await self.ingest_file(file_path)",
    "chunks = await self.ingest_file(file_path, project_id)  # FIXED: Pass project_id"
)

# Write the fixed file
with open('rag_agent.py', 'w') as f:
    f.write(content)

print("✅ Applied vector search isolation fixes")
print("   - Ingestion endpoint now requires project_id")  
print("   - Directory ingestion passes project_id")
print("   - Added project validation")
print("\n🧪 Test with: python test_isolation_advanced.py")