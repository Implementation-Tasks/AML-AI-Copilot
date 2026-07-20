#!/usr/bin/env python3
"""
Quick Start Script - AML AI Copilot
Run quickly to check the system
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def check_environment():
    """Check environment and dependencies"""
    print("🔍 Checking environment...\n")
    
    issues = []
    
    # Check Python version
    import sys
    py_version = sys.version_info
    if py_version < (3, 10):
        issues.append(f"❌ Python version {py_version.major}.{py_version.minor} is too low (requires >= 3.10)")
    else:
        print(f"✅ Python {py_version.major}.{py_version.minor}.{py_version.micro}")
    
    # Check critical dependencies
    deps = {
        'numpy': 'NumPy',
        'networkx': 'NetworkX',
        'pandas': 'Pandas',
        'dotenv': 'python-dotenv',
    }
    
    for module, name in deps.items():
        try:
            __import__(module if module != 'dotenv' else 'dotenv')
            print(f"✅ {name}")
        except ImportError:
            issues.append(f"❌ {name} is not installed")
            print(f"❌ {name} - Run: py -m pip install {module if module != 'dotenv' else 'python-dotenv'}")
    
    # Check .env file
    from dotenv import load_dotenv
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        print(f"✅ .env file exists")
        load_dotenv()
        
        # Check critical keys
        keys_to_check = ['ANTHROPIC_API_KEY', 'ETHERSCAN_API_KEY']
        for key in keys_to_check:
            value = os.getenv(key, '')
            if value and value != f'your_{key.lower()}_here':
                print(f"✅ {key} is configured")
            else:
                issues.append(f"⚠️  {key} is not configured (can use DEMO_MODE)")
    else:
        issues.append("❌ .env file does not exist - Copy from .env.example")
    
    print()
    if issues:
        print("⚠️  ISSUES TO FIX:")
        for issue in issues:
            print(f"  {issue}")
        print()
    else:
        print("✨ All checks passed!\n")
    
    return len(issues) == 0


def test_qubo():
    """Test QUBO optimizer"""
    print("🧪 Test QUBO Optimizer...")
    try:
        from src.quantum.hybrid_optimizer import HybridQuantumOptimizer
        from src.data.etherscan_graph_builder import build_demo_graph
        
        # Build demo graph
        graph = build_demo_graph('0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b')
        print(f"  📊 Graph: {graph.graph.number_of_nodes()} nodes, {graph.graph.number_of_edges()} edges")
        
        # Run QUBO optimization
        optimizer = HybridQuantumOptimizer('classical')
        result = optimizer.optimize(graph)
        
        print(f"  ✅ QUBO Done:")
        print(f"     - FPR: {result.false_positive_rate:.4f}")
        print(f"     - F-β: {result.f_beta_score:.4f}")
        print(f"     - Precision: {result.precision:.4f}")
        print(f"     - Recall: {result.recall:.4f}")
        print(f"     - Runtime: {result.runtime_seconds:.2f}s")
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_pipeline():
    """Test full pipeline"""
    print("\n🚀 Test Full Pipeline...")
    try:
        from src.pipeline.handler import handler
        
        # Test with demo mode
        os.environ['DEMO_MODE'] = 'true'
        
        event = {
            "wallet_address": "0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b",
            "backend": "classical",
            "shots": 1024,
            "mode": "hybrid"
        }
        
        result = handler(event)
        
        print(f"  ✅ Pipeline Done:")
        print(f"     - Case ID: {result['case_id']}")
        print(f"     - Risk Level: {result['risk_level']}")
        print(f"     - Action: {result['recommended_action']}")
        print(f"     - QUBO Score: {result['qubo_risk_score']:.4f}")
        if 'compliance_score' in result:
            print(f"     - Compliance Score: {result.get('compliance_score', 'N/A')}")
        print(f"     - Runtime: {result['runtime_seconds']:.2f}s")
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    print("="*70)
    print("  ⚛ AML AI COPILOT - QUICK START")
    print("  SEA Quantathon 2026 · QCFinOp Team")
    print("="*70)
    print()
    
    # Step 1: Check environment
    env_ok = check_environment()
    if not env_ok:
        print("\n⚠️  Please fix the above issues before continuing.")
        print("📖 See full guide: FULL_PROJECT_GUIDE.md")
        return
    
    # Step 2: Test QUBO
    qubo_ok = test_qubo()
    if not qubo_ok:
        print("\n❌ QUBO test failed. Check the logs above.")
        return
    
    # Step 3: Test Pipeline
    pipeline_ok = test_pipeline()
    if not pipeline_ok:
        print("\n❌ Pipeline test failed. Check the logs above.")
        return
    
    # Success!
    print()
    print("="*70)
    print("  ✨ ALL TESTS PASSED!")
    print("="*70)
    print()
    print("🎯 YOU CAN:")
    print("  1. Run demo simulation:")
    print("     cd DEMOCORE")
    print("     py 03_qubo_sim.py serve 8765")
    print()
    print("  2. Analyze specific wallet:")
    print("     py analyze_wallet.py 0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b")
    print()
    print("  3. Run web server:")
    print("     py server.py")
    print()
    print("📖 See full guide: FULL_PROJECT_GUIDE.md")
    print()


if __name__ == '__main__':
    main()
