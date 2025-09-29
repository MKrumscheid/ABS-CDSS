#!/usr/bin/env python3
"""
Deployment preparation script for ABS-CDSS on Koyeb
This script helps prepare the application for cloud deployment
"""

import os
import subprocess
import json
from pathlib import Path
import shutil

class KoyebDeploymentPrep:
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.backend_dir = self.root_dir / "backend"
        self.frontend_dir = self.root_dir / "frontend"
        
    def check_prerequisites(self):
        """Check if all prerequisites are met"""
        print("🔍 Checking prerequisites...")
        
        issues = []
        
        # Check Node.js
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Node.js: {result.stdout.strip()}")
            else:
                issues.append("Node.js not found")
        except FileNotFoundError:
            issues.append("Node.js not installed")
        
        # Check Python
        try:
            result = subprocess.run(["python", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Python: {result.stdout.strip()}")
            else:
                issues.append("Python not found")
        except FileNotFoundError:
            issues.append("Python not installed")
        
        # Check Docker
        try:
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Docker: {result.stdout.strip()}")
            else:
                issues.append("Docker not found")
        except FileNotFoundError:
            issues.append("Docker not installed or not in PATH")
        
        # Check required files
        required_files = [
            "Dockerfile",
            "koyeb.toml", 
            "backend/requirements-prod.txt",
            "frontend/package.json"
        ]
        
        for file_path in required_files:
            full_path = self.root_dir / file_path
            if full_path.exists():
                print(f"✅ {file_path}")
            else:
                issues.append(f"Missing file: {file_path}")
        
        if issues:
            print("\n❌ Issues found:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        else:
            print("\n✅ All prerequisites met!")
            return True
    
    def test_local_build(self):
        """Test the Docker build locally"""
        print("\n🐳 Testing Docker build...")
        
        try:
            # Build the Docker image
            cmd = ["docker", "build", "-t", "abs-cdss-test", "."]
            result = subprocess.run(cmd, cwd=self.root_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Docker build successful!")
                
                # Test running the container
                print("🚀 Testing container startup...")
                cmd = ["docker", "run", "--rm", "-p", "8000:8000", "-d", "--name", "abs-cdss-test-run", "abs-cdss-test"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    container_id = result.stdout.strip()
                    print(f"✅ Container started: {container_id}")
                    
                    # Wait a bit and test health
                    import time
                    time.sleep(10)
                    
                    # Test health endpoint
                    try:
                        import requests
                        response = requests.get("http://localhost:8000/health", timeout=10)
                        if response.status_code == 200:
                            print("✅ Health check passed!")
                        else:
                            print(f"⚠️  Health check failed: {response.status_code}")
                    except Exception as e:
                        print(f"⚠️  Health check error: {e}")
                    
                    # Stop container
                    subprocess.run(["docker", "stop", "abs-cdss-test-run"], capture_output=True)
                    print("🛑 Test container stopped")
                    
                else:
                    print(f"❌ Container startup failed: {result.stderr}")
                    return False
                    
            else:
                print(f"❌ Docker build failed:")
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Docker test failed: {e}")
            return False
        
        return True
    
    def generate_env_template(self):
        """Generate environment variables template for Koyeb"""
        print("\n📝 Generating environment variables template...")
        
        env_template = {
            "secrets": {
                "NOVITA_API_KEY": "your_novita_api_key_here",
                "DATABASE_URL": "postgresql://user:pass@host:port/dbname"
            },
            "public": {
                "ENVIRONMENT": "production",
                "API_HOST": "0.0.0.0",
                "API_PORT": "8000",
                "USE_ONLINE_EMBEDDINGS": "true",
                "EMBEDDING_REQUESTS_PER_MINUTE": "45",
                "EMBEDDING_MAX_RETRIES": "3",
                "EMBEDDING_RETRY_DELAY": "2",
                "NOVITA_EMBEDDING_URL": "https://api.novita.ai/openai/v1/embeddings",
                "NOVITA_EMBEDDING_MODEL": "qwen/qwen3-embedding-8b",
                "NOVITA_API_BASE_URL": "https://api.novita.ai/openai",
                "NOVITA_MODEL": "openai/gpt-oss-120b",
                "NOVITA_MAX_TOKENS": "32768",
                "NOVITA_TEMPERATURE": "0.7",
                "CHUNK_SIZE": "512",
                "CHUNK_OVERLAP": "50",
                "DEFAULT_TOP_K": "5",
                "FAISS_INDEX_TYPE": "IndexFlatIP",
                "LOG_LEVEL": "INFO"
            }
        }
        
        with open(self.root_dir / "koyeb-env-template.json", "w") as f:
            json.dump(env_template, f, indent=2)
        
        print("✅ Environment template created: koyeb-env-template.json")
        print("\nℹ️  Configure these in your Koyeb dashboard:")
        print("   Secrets (sensitive): NOVITA_API_KEY, DATABASE_URL")
        print("   Public: All other variables")
    
    def create_deployment_checklist(self):
        """Create a deployment checklist"""
        print("\n📋 Creating deployment checklist...")
        
        checklist = """
# Koyeb Deployment Checklist for ABS-CDSS

## Pre-deployment (Local)
- [ ] All tests pass locally
- [ ] Docker build succeeds locally
- [ ] Environment variables configured
- [ ] Code committed to main branch

## Koyeb Setup
- [ ] Create new Koyeb app
- [ ] Connect GitHub repository
- [ ] Set environment variables:
  - [ ] NOVITA_API_KEY (secret)
  - [ ] DATABASE_URL (secret) 
  - [ ] All public variables from template
- [ ] Configure build settings:
  - [ ] Build type: Docker
  - [ ] Dockerfile: Dockerfile
  - [ ] Auto-deploy: Enabled (main branch)
- [ ] Set instance type: nano (free tier)

## Database Setup
- [ ] Create PostgreSQL database (recommend: Supabase/Neon)
- [ ] Update DATABASE_URL in Koyeb secrets
- [ ] Test database connection

## Domain & SSL
- [ ] Configure custom domain (optional)
- [ ] SSL automatically provisioned by Koyeb

## Post-deployment
- [ ] Test health endpoint: /health
- [ ] Test admin frontend: /admin
- [ ] Test enduser frontend: /
- [ ] Test API functionality: /docs
- [ ] Upload test guidelines
- [ ] Verify RAG functionality

## Monitoring
- [ ] Check application logs in Koyeb dashboard
- [ ] Monitor resource usage
- [ ] Set up alerts for errors

## URLs after deployment
- Health Check: https://your-app.koyeb.app/health
- API Docs: https://your-app.koyeb.app/docs
- Admin UI: https://your-app.koyeb.app/admin
- End User: https://your-app.koyeb.app/

## Troubleshooting
- Check logs in Koyeb dashboard
- Verify environment variables
- Test database connectivity
- Check Docker build logs
"""
        
        with open(self.root_dir / "DEPLOYMENT_CHECKLIST.md", "w") as f:
            f.write(checklist)
        
        print("✅ Deployment checklist created: DEPLOYMENT_CHECKLIST.md")
    
    def run_preparation(self):
        """Run the complete preparation process"""
        print("🚀 ABS-CDSS Koyeb Deployment Preparation")
        print("=" * 50)
        
        # Step 1: Check prerequisites
        if not self.check_prerequisites():
            print("\n❌ Prerequisites not met. Please fix issues and try again.")
            return False
        
        # Step 2: Generate templates
        self.generate_env_template()
        self.create_deployment_checklist()
        
        # Step 3: Test build (optional, can be slow)
        test_build = input("\n🤔 Test Docker build locally? (y/N): ").lower().strip()
        if test_build == 'y':
            if not self.test_local_build():
                print("\n⚠️  Local build test failed, but you can still proceed with deployment")
        
        print("\n" + "=" * 50)
        print("✅ Deployment preparation complete!")
        print("\nNext steps:")
        print("1. Review DEPLOYMENT_CHECKLIST.md")
        print("2. Configure environment variables in Koyeb")
        print("3. Push to main branch to trigger deployment")
        print("\n🚀 Ready for Koyeb deployment!")
        
        return True

if __name__ == "__main__":
    prep = KoyebDeploymentPrep()
    prep.run_preparation()