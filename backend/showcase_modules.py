import sys
import os
import numpy as np

# Adjust path to import backend modules correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.intelligence.anomaly.evaluator import AnomalyModelEvaluator
from app.services.intelligence.embeddings import get_embedder, EmbeddingsEvaluator
from app.knowledge.mitre_mapper import MitreMapper
from app.services.processing.rule_filter import ForensicRuleFilter
from app.services.processing.feature_builder import ForensicFeatureBuilder
from app.utils.hashing import ForensicHasher
from app.utils.constants import SYSTEM_NAME, VERSION

# Global testing random seed parameter (PR suggestion 3)
SEED = 42

def run_ml_anomaly_demonstration() -> bool:
    print("\n" + "="*50)
    print("🧠 PHASE 1: UNSUPERVISED ANOMALY MODEL EVALUATIONS")
    print("="*50)
    
    # Generate some fake forensic feature matrices (25 log events, 6 feature dimensions)
    # Dimension schema: [hour, weekend, subj_freq, obj_freq, act_freq, sev_val]
    np.random.seed(SEED)
    normal_events = np.random.normal(loc=0.5, scale=0.1, size=(22, 6))
    anomaly_events = np.random.normal(loc=2.0, scale=0.5, size=(3, 6)) # Outliers are far away
    features = np.vstack([normal_events, anomaly_events])
    
    print(f"Generated feature matrix. Shape: {features.shape} samples.")
    print("Evaluating Isolation Forest, LOF, One-Class SVM, and HBOS...")
    
    reports = AnomalyModelEvaluator.compare_all(features)
    
    # Assertions to ensure models work and don't return null/zero (PR suggestion 1)
    assert len(reports) == 4, "Expected exactly 4 outlier algorithms reports"
    assert any(r["algorithm"] == "isolation_forest" for r in reports)
    assert any(r["algorithm"] == "hbos" for r in reports)
    assert all(r["status"] == "success" for r in reports), "One or more models failed execution"
    
    for report in reports:
        print(f"- Model [{report['algorithm'].upper()}] evaluation:")
        print(f"  * Inliers: {report['inliers_count']} | Outliers: {report['outliers_count']}")
        print(f"  * Silhouette Fit Coefficient: {report['silhouette_score']:.4f}")
        
        # Output correctness check
        assert report["outliers_count"] > 0, f"Algorithm {report['algorithm']} missed the outlier cluster"

    # Select best fit model based on silhouette score (PR suggestion 10)
    best_report = max(reports, key=lambda x: x["silhouette_score"])
    print(f"\n🏆 Best silhouette fit model: {best_report['algorithm'].upper()} (Score: {best_report['silhouette_score']:.4f})")
    
    return True

def run_embeddings_demonstration() -> bool:
    print("\n" + "="*50)
    print("🔤 PHASE 2: MULTI-MODEL EMBEDDINGS & PAIRWISE SIMILARITY")
    print("="*50)
    
    sentences = [
        "powershell.exe -executionpolicy bypass -file download_payload.ps1",
        "cmd.exe /c whoami",
        "explorer.exe popped gui window",
        "ntoskrnl.exe performed harmless memory lock check"
    ]
    
    print("Sample logs for embedding benchmarking:")
    for idx, s in enumerate(sentences):
        print(f" {idx+1}. {s}")
        
    print("\nLoading MiniLM, BGE, and E5 models to compute pairwise cosine similarities...")
    benchmarks = EmbeddingsEvaluator.benchmark_providers(sentences)
    
    assert len(benchmarks) == 3, "Expected 3 benchmark results"
    for b in benchmarks:
        assert b["status"] == "success", f"Embeddings benchmark failed for model: {b.get('model')}"
        # Validate embedding models dimensions (PR suggestion 5)
        assert b["embedding_dimension"] == 384, f"Unexpected dimensions size '{b['embedding_dimension']}' for {b['model']}"
        
        print(f"- Encoder [{b['model'].upper()}]:")
        print(f"  * Vector dimension: {b['embedding_dimension']}")
        print(f"  * Avg Pairwise Cosine Similarity: {b['average_pairwise_similarity']:.4f}")
        print(f"  * Standard Deviation: {b['standard_deviation']:.4f}")

    # Validate active semantic similarity pairing checks (PR suggestion 6)
    embedder = get_embedder("minilm")
    vectors = embedder.encode(sentences)
    
    # Calculate similarity between powershell and whoami (suspicious CLI command execution)
    sim_malicious = EmbeddingsEvaluator.cosine_similarity(vectors[0], vectors[1])
    # Calculate similarity between powershell and harmless kernel log
    sim_benign = EmbeddingsEvaluator.cosine_similarity(vectors[0], vectors[3])
    
    print(f"\nPairwise Semantic Checks:")
    print(f"  - PowerShell <-> Whoami (CLI overlap) Cosine Similarity: {sim_malicious:.4f}")
    print(f"  - PowerShell <-> Kernel Lock (Benign) Cosine Similarity: {sim_benign:.4f}")
    
    assert sim_malicious > sim_benign, "Semantic vector search validation failed: CLI overlap holds less similarity than benign"
    print("  ✅ Semantic validation check passed (Malicious CLI pairs are closer than benign kernel commands)")
    
    # Demonstrate get_embedder factory retrieval (PR suggestion 8)
    sample_vec = embedder.encode(["alert triggered"])
    assert sample_vec.shape == (1, 384)
    print(f"\n  ✅ get_embedder() factory retrieved MiniLM, vector test size: {sample_vec.shape}")
    
    return True

def run_mitre_mapping_demonstration() -> bool:
    print("\n" + "="*50)
    print("🛡️ PHASE 3: MITRE ATT&CK COMMAND MAPPINGS")
    print("="*50)
    
    log_events = [
        {"subject": "powershell.exe", "action": "spawn", "object": "-nop -w hidden -enc JABzAD0ATgBlAHcALQBPAGIAagBlAGMA..." },
        {"subject": "mimikatz.exe", "action": "dump", "object": "lsass.exe memory process payload"},
        {"subject": "schtasks.exe", "action": "create", "object": "/create /tn persistent_backdoor /tr mal.exe"},
        {"subject": "whoami.exe", "action": "lookup", "object": "system owner domain credentials"},
        {"subject": "normal_app.exe", "action": "read", "object": "harmless_config_file.txt"}
    ]
    
    for event in log_events:
        ttp = MitreMapper.map_event_to_ttp(event)
        print(f"- Log event: '{event['subject']} perform {event['action']} on {event['object']}'")
        
        # Verify MITRE mapping outcomes (PR suggestion 4)
        if event["subject"] in ["powershell.exe", "mimikatz.exe", "whoami.exe", "schtasks.exe"]:
            assert ttp["mapped"] is True, f"Expected {event['subject']} event to map to MITRE technique TTP"
        else:
            assert ttp["mapped"] is False, f"Expected normal log on {event['subject']} to bypass mapping filter"
            
        if ttp["mapped"]:
            print(f"  * [IDENTIFIED Tactic: {ttp['tactic']}]")
            print(f"  * Technique ID: {ttp['technique_id']} | Name: {ttp['technique_name']}")
            print(f"  * Description: {ttp['description']}")
        else:
            print(f"  * [NOT MAPPED: Recognized as safe/unknown telemetry]")
            
    return True

def run_filters_and_features_demonstration() -> bool:
    print("\n" + "="*50)
    print("🔍 PHASE 4: TELEMETRY NOISE FILTERS & FEATURE CONVERTERS")
    print("="*50)
    
    raw_logs = [
        {"subject": "explorer.exe", "action": "gui_refresh", "object": "hkey_current_user", "severity": "info"},
        {"subject": "ntoskrnl.exe", "action": "read", "object": "registry_key", "severity": "info"},
        {"subject": "powershell.exe", "action": "bypass", "object": "malicious_script.ps1", "severity": "critical"},
        {"subject": "whoami.exe", "action": "check", "object": "username", "severity": "medium"}
    ]
    
    print(f"Raw logging events received: {len(raw_logs)}")
    filtered = ForensicRuleFilter.filter_noisy_telemetry(raw_logs)
    print(f"Filtered log events output (after alert suppression): {len(filtered)}")
    
    assert len(filtered) == 2, "Expected exactly 2 events remaining after filter"
    for f_log in filtered:
        print(f"  * {f_log['subject']} -> {f_log['action']} ({f_log['severity'].upper()})")
        assert f_log["subject"] in ["powershell.exe", "whoami.exe"], "Filter incorrectly stripped malicious commands"

    # Demonstrate ForensicFeatureBuilder conversion (PR suggestion 7)
    from datetime import datetime
    formatted_logs = [
        {"subject": "powershell.exe", "action": "bypass", "object": "malicious_script.ps1", "severity": "critical", "timestamp": datetime(2026, 7, 15, 14, 30)},
        {"subject": "whoami.exe", "action": "check", "object": "username", "severity": "medium", "timestamp": datetime(2026, 7, 15, 14, 32)}
    ]
    matrix = ForensicFeatureBuilder.extract_features_matrix(formatted_logs)
    print(f"\nFeature matrix generated for filtered events: shape {matrix.shape}")
    print(f"Numeric Vector Sample (PowerShell Event): {matrix[0]}")
    
    assert matrix.shape == (2, 6), "Expected 2x6 feature matrix shape"
    assert matrix[0][5] == 1.0, "Expected critical severity weight (1.0) on PowerShell event feature index"

    print("\nHashing a dummy payload string...")
    test_data = b"Malicious PowerShell payload script payload contents."
    checksum = ForensicHasher.sha256_checksum(test_data)
    print(f"SHA-256 Checksum: {checksum}")
    assert checksum == "015d6a187ffcd799a697efee012a754a2e33e52032d9e1bcad05c649fbc87d93"
    
    return True

if __name__ == "__main__":
    print(f"==================================================")
    print(f"   🚀 Welcome to {SYSTEM_NAME} v{VERSION} Modular Showcase")
    print(f"==================================================")
    
    passed_modules = 0
    total_modules = 4
    
    if run_ml_anomaly_demonstration():
        passed_modules += 1
    if run_embeddings_demonstration():
        passed_modules += 1
    if run_mitre_mapping_demonstration():
        passed_modules += 1
    if run_filters_and_features_demonstration():
        passed_modules += 1
        
    print("\n" + "="*50)
    # Output unified modules status check (PR suggestion 8)
    print(f"✅ SHOWCASE MODULES COMPLETE: {passed_modules}/{total_modules} PASSED!")
    print("="*50)
    
    assert passed_modules == total_modules, f"Only {passed_modules}/{total_modules} modules verified successfully"
