"""
Development Bible Reader

This module provides functionality to read and process the development bible
documentation for the AI Agent Automation Hub.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class DevBibleReader:
    """Reader for development bible documentation."""
    
    def __init__(self, bible_path: str):
        """
        Initialize the DevBibleReader.
        
        Args:
            bible_path: Path to the dev_bible directory
        """
        self.bible_path = Path(bible_path)
        self.documentation = {}
        self.sections = {}
        
        if not self.bible_path.exists():
            logger.warning(f"Dev bible path does not exist: {bible_path}")
    
    def load_all_documentation(self) -> Dict[str, str]:
        """
        Load all markdown documentation from the dev bible.
        
        Returns:
            Dictionary mapping file names to content
        """
        documentation = {}
        
        if not self.bible_path.exists():
            logger.error(f"Dev bible directory not found: {self.bible_path}")
            return documentation
        
        # Find all markdown files
        for md_file in self.bible_path.rglob("*.md"):
            try:
                relative_path = md_file.relative_to(self.bible_path)
                file_key = str(relative_path).replace(os.sep, "/")
                
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    documentation[file_key] = content
                    
                logger.debug(f"Loaded documentation: {file_key}")
                
            except Exception as e:
                logger.error(f"Failed to read {md_file}: {e}")
        
        self.documentation = documentation
        return documentation
    
    def get_section(self, section_name: str) -> Optional[str]:
        """
        Get a specific documentation section by name.
        
        Args:
            section_name: Name of the section to retrieve
            
        Returns:
            Section content or None if not found
        """
        if not self.documentation:
            self.load_all_documentation()
        
        # Look for exact file match first
        for file_path, content in self.documentation.items():
            if section_name.lower() in file_path.lower():
                return content
        
        # Look for section headers within files
        for file_path, content in self.documentation.items():
            sections = self._extract_sections(content)
            for section_title, section_content in sections.items():
                if section_name.lower() in section_title.lower():
                    return section_content
        
        return None
    
    def _extract_sections(self, content: str) -> Dict[str, str]:
        """
        Extract sections from markdown content based on headers.
        
        Args:
            content: Markdown content
            
        Returns:
            Dictionary mapping section titles to content
        """
        sections = {}
        current_section = None
        current_content = []
        
        for line in content.split('\n'):
            # Check for headers (# ## ### etc.)
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            if header_match:
                # Save previous section if exists
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                current_section = header_match.group(2)
                current_content = [line]
            else:
                if current_section:
                    current_content.append(line)
        
        # Save final section
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def search_documentation(self, query: str) -> List[Tuple[str, str, str]]:
        """
        Search for a query across all documentation.
        
        Args:
            query: Search query
            
        Returns:
            List of tuples (file_path, section, matching_content)
        """
        if not self.documentation:
            self.load_all_documentation()
        
        results = []
        query_lower = query.lower()
        
        for file_path, content in self.documentation.items():
            # Search in file content
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if query_lower in line.lower():
                    # Get context around the match
                    start = max(0, i - 2)
                    end = min(len(lines), i + 3)
                    context = '\n'.join(lines[start:end])
                    
                    results.append((file_path, f"Line {i+1}", context))
        
        return results
    
    def get_agent_specific_docs(self, agent_type: str) -> Dict[str, str]:
        """
        Get documentation specific to an agent type.
        
        Args:
            agent_type: Type of agent (backend, testing, orchestrator)
            
        Returns:
            Dictionary of relevant documentation
        """
        if not self.documentation:
            self.load_all_documentation()
        
        relevant_docs = {}
        agent_keywords = {
            'backend': ['backend', 'api', 'database', 'server'],
            'testing': ['testing', 'test', 'qa', 'validation'],
            'orchestrator': ['orchestrator', 'workflow', 'coordination', 'management']
        }
        
        keywords = agent_keywords.get(agent_type.lower(), [agent_type.lower()])
        
        for file_path, content in self.documentation.items():
            content_lower = content.lower()
            file_path_lower = file_path.lower()
            
            # Check if file path or content mentions the agent type
            if any(keyword in file_path_lower or keyword in content_lower for keyword in keywords):
                relevant_docs[file_path] = content
        
        return relevant_docs
    
    def get_coding_standards(self) -> Optional[str]:
        """Get coding standards documentation."""
        return self.get_section("coding_standards") or self.get_section("standards")
    
    def get_architecture_docs(self) -> Optional[str]:
        """Get architecture documentation."""
        return self.get_section("architecture") or self.get_section("arch")
    
    def get_agent_roles(self) -> Optional[str]:
        """Get agent roles documentation."""
        return self.get_section("agent_roles") or self.get_section("roles")
    
    def get_workflow_docs(self) -> Optional[str]:
        """Get workflow documentation."""
        return self.get_section("workflow") or self.get_section("process")
    
    def prepare_context_for_agent(self, agent_type: str, task_description: str) -> str:
        """
        Prepare contextual documentation for an agent based on task.
        
        Args:
            agent_type: Type of agent
            task_description: Description of the task
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        # Always include coding standards
        standards = self.get_coding_standards()
        if standards:
            context_parts.append("## Coding Standards\n" + standards[:1000] + "...")
        
        # Include agent-specific documentation
        agent_docs = self.get_agent_specific_docs(agent_type)
        for file_path, content in list(agent_docs.items())[:2]:  # Limit to first 2 files
            context_parts.append(f"## {file_path}\n" + content[:800] + "...")
        
        # Include architecture if relevant
        if any(word in task_description.lower() for word in ['architecture', 'design', 'structure']):
            arch_docs = self.get_architecture_docs()
            if arch_docs:
                context_parts.append("## Architecture\n" + arch_docs[:800] + "...")
        
        # Include workflow if relevant
        if any(word in task_description.lower() for word in ['workflow', 'process', 'deploy']):
            workflow_docs = self.get_workflow_docs()
            if workflow_docs:
                context_parts.append("## Workflow\n" + workflow_docs[:800] + "...")
        
        return "\n\n".join(context_parts)
    
    def validate_documentation_coverage(self) -> Dict[str, bool]:
        """
        Validate that all expected documentation sections exist.
        
        Returns:
            Dictionary mapping section names to existence status
        """
        expected_sections = [
            'architecture',
            'agent_roles', 
            'coding_standards',
            'workflow_process',
            'communication',
            'security_rules'
        ]
        
        coverage = {}
        
        for section in expected_sections:
            coverage[section] = self.get_section(section) is not None
        
        return coverage
    
    def get_summary_stats(self) -> Dict[str, int]:
        """
        Get summary statistics about the documentation.
        
        Returns:
            Dictionary with statistics
        """
        if not self.documentation:
            self.load_all_documentation()
        
        total_files = len(self.documentation)
        total_chars = sum(len(content) for content in self.documentation.values())
        total_lines = sum(content.count('\n') for content in self.documentation.values())
        
        # Count sections across all files
        total_sections = 0
        for content in self.documentation.values():
            sections = self._extract_sections(content)
            total_sections += len(sections)
        
        return {
            'total_files': total_files,
            'total_characters': total_chars,
            'total_lines': total_lines,
            'total_sections': total_sections,
            'average_file_size': total_chars // max(total_files, 1)
        }