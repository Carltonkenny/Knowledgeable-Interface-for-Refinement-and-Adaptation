#!/usr/bin/env python3
"""
Production setup script for the multi-agent system
This script ensures all production requirements are met and validates the system
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_python_version():
    """Check Python version compatibility"""
    logger.info("Checking Python version...")
    major, minor = sys.version_info.major, sys.version_info.minor
    if major < 3 or (major == 3 and minor < 11):
        logger.error("Python 3.11 or higher required")
        return False
    logger.info(f"Python {major}.{minor} is compatible")
    return True

def install_requirements():
    """Install production requirements"""
    logger.info("Installing production requirements...")
    
    # Install base requirements
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--upgrade", "pip"
        ])
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        logger.info("Base requirements installed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install requirements: {e}")
        return False
    
    # Install dev requirements for testing
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements-dev.txt"
        ])
        logger.info("Development requirements installed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install development requirements: {e}")
        return False
    
    return True

def validate_directories():
    """Validate required directories exist"""
    required_dirs = [
        "memory",
        "agents",
        "middleware",
        "routes",
        "tests",
        "docs",
        "scripts"
    ]
    
    logger.info("Validating required directories...")
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            logger.warning(f"Directory {dir_name} does not exist")
            try:
                os.makedirs(dir_name)
                logger.info(f"Created directory {dir_name}")
            except Exception as e:
                logger.error(f"Failed to create directory {dir_name}: {e}")
                return False
        else:
            logger.info(f"Directory {dir_name} exists")
    
    return True

def validate_config_files():
    """Validate configuration files"""
    required_files = [
        "config.py",
        "requirements.txt",
        "requirements-dev.txt",
        "Dockerfile",
        "docker-compose.yml"
    ]
    
    logger.info("Validating configuration files...")
    for file_name in required_files:
        if os.path.exists(file_name):
            logger.info(f"Configuration file {file_name} exists")
        else:
            logger.warning(f"Configuration file {file_name} does not exist")
    
    return True

def run_tests():
    """Run comprehensive test suite"""
    logger.info("Running comprehensive test suite...")
    
    try:
        # Run memory system tests
        subprocess.check_call([
            sys.executable, "-m", "unittest", "tests.test_memory_systems"
        ])
        logger.info("Memory system tests passed")
        
        # Run production readiness tests
        subprocess.check_call([
            sys.executable, "-m", "unittest", "tests.test_production_readiness"
        ])
        logger.info("Production readiness tests passed")
        
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Tests failed: {e}")
        return False

def setup_environment():
    """Setup production environment variables"""
    logger.info("Setting up environment variables...")
    
    # Set production environment
    os.environ['ENVIRONMENT'] = 'production'
    os.environ['LOG_LEVEL'] = 'INFO'
    
    # Set database connection if not already set
    if 'DATABASE_URL' not in os.environ:
        os.environ['DATABASE_URL'] = 'postgresql://localhost:5432/promptforge_prod'
    
    logger.info("Environment variables set")
    return True

def validate_memory_systems():
    """Validate memory systems are properly implemented"""
    logger.info("Validating memory systems...")
    
    try:
        # Import and test memory systems
        from memory.langmem import LangMem
        from memory.supermemory import SuperMemory
        from memory.hybrid_recall import HybridMemoryRecall
        
        # Test instantiations
        langmem = LangMem("./test_storage")
        supermemory = SuperMemory()
        hybrid_recall = HybridMemoryRecall()
        
        # Check for required methods
        required_methods = [
            'store', 'retrieve', 'update', 'delete', 'get_statistics',
            'store_fact', 'get_context', 'get_stats',
            'query', '_reciprocal_rank_fusion', '_maximal_margin_reranking'
        ]
        
        for method in required_methods:
            if hasattr(langmem, method) or hasattr(supermemory, method) or hasattr(hybrid_recall, method):
                logger.debug(f"Method {method} found")
            else:
                logger.warning(f"Method {method} not found")
                
        logger.info("Memory systems validation completed")
        return True
        
    except Exception as e:
        logger.error(f"Memory systems validation failed: {e}")
        return False

def main():
    """Main production setup function"""
    logger.info("Starting production setup...")
    
    # Check Python version
    if not check_python_version():
        logger.error("Python version check failed")
        return 1
    
    # Validate directories
    if not validate_directories():
        logger.error("Directory validation failed")
        return 1
    
    # Validate config files
    if not validate_config_files():
        logger.error("Configuration validation failed")
        return 1
    
    # Install requirements
    if not install_requirements():
        logger.error("Requirements installation failed")
        return 1
    
    # Setup environment
    if not setup_environment():
        logger.error("Environment setup failed")
        return 1
    
    # Validate memory systems
    if not validate_memory_systems():
        logger.error("Memory systems validation failed")
        return 1
    
    # Run tests
    if not run_tests():
        logger.error("Tests failed")
        return 1
    
    logger.info("Production setup completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())