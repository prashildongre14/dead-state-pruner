import urllib.request
import json

def test_api():
    base = "http://127.0.0.1:5000"
    
    # Test index
    req = urllib.request.urlopen(f"{base}/")
    assert req.status == 200
    print("[PASS] Index page loaded successfully (HTTP 200)")

    # Test presets
    req = urllib.request.urlopen(f"{base}/api/presets")
    presets_data = json.loads(req.read().decode('utf-8'))
    assert presets_data["success"] is True
    print(f"[PASS] Presets loaded: {list(presets_data['presets'].keys())}")

    # Test Analyze endpoint with Viva Demo
    demo_dfa = presets_data["presets"]["viva_demo"]
    payload = json.dumps(demo_dfa).encode('utf-8')
    
    req = urllib.request.Request(f"{base}/api/analyze", data=payload, headers={"Content-Type": "application/json"})
    res = urllib.request.urlopen(req)
    analysis_data = json.loads(res.read().decode('utf-8'))
    assert analysis_data["success"] is True
    an = analysis_data["analysis"]
    print(f"[PASS] Unreachable states detected: {an['unreachable_states']}")
    print(f"[PASS] Dead/Trap states detected: {an['dead_states']}")
    print(f"[PASS] Useful states detected: {an['useful_states']}")
    print(f"[PASS] States to prune: {an['states_to_prune']}")

    assert "q5" in an["unreachable_states"], "q5 should be unreachable!"
    assert "q4" in an["dead_states"], "q4 should be dead/trap!"

    # Test Prune endpoint
    req = urllib.request.Request(f"{base}/api/prune", data=payload, headers={"Content-Type": "application/json"})
    res = urllib.request.urlopen(req)
    prune_data = json.loads(res.read().decode('utf-8'))
    assert prune_data["success"] is True
    opt = prune_data["optimized_dfa"]
    red = prune_data["reduction"]
    print(f"[PASS] Original states: {red['original_states_count']}, Optimized states: {red['optimized_states_count']}")
    print(f"[PASS] State reduction: {red['state_reduction_percent']}%")
    assert "q5" not in opt["states"]
    assert "q4" not in opt["states"]

    # Test Simulate endpoint for string "00" (should reach q2, accepted in both!)
    sim_payload = json.dumps({
        "original_dfa": prune_data["original_dfa"],
        "optimized_dfa": opt,
        "test_string": "00"
    }).encode('utf-8')
    req = urllib.request.Request(f"{base}/api/simulate", data=sim_payload, headers={"Content-Type": "application/json"})
    res = urllib.request.urlopen(req)
    sim_data = json.loads(res.read().decode('utf-8'))
    print(f"[PASS] Test String '00': Orig accepted={sim_data['original_result']['accepted']}, Opt accepted={sim_data['optimized_result']['accepted']}, Match={sim_data['match']}")
    assert sim_data["match"] is True
    assert sim_data["original_result"]["accepted"] is True

    # Test Simulate endpoint for string "10" (reaches trap state q4 in original, rejected in both!)
    sim_payload2 = json.dumps({
        "original_dfa": prune_data["original_dfa"],
        "optimized_dfa": opt,
        "test_string": "10"
    }).encode('utf-8')
    req = urllib.request.Request(f"{base}/api/simulate", data=sim_payload2, headers={"Content-Type": "application/json"})
    res = urllib.request.urlopen(req)
    sim_data2 = json.loads(res.read().decode('utf-8'))
    print(f"[PASS] Test String '10': Orig accepted={sim_data2['original_result']['accepted']}, Opt accepted={sim_data2['optimized_result']['accepted']}, Match={sim_data2['match']}")
    assert sim_data2["match"] is True
    assert sim_data2["original_result"]["accepted"] is False

    # Test Batch Suite endpoint
    batch_payload = json.dumps({
        "original_dfa": prune_data["original_dfa"],
        "optimized_dfa": opt,
        "custom_strings": ["ε", "0", "1", "00", "01", "10", "11", "000", "001", "010", "011", "100", "101", "110", "111"]
    }).encode('utf-8')
    req = urllib.request.Request(f"{base}/api/batch-test", data=batch_payload, headers={"Content-Type": "application/json"})
    res = urllib.request.urlopen(req)
    batch_data = json.loads(res.read().decode('utf-8'))
    print(f"[PASS] Batch testing completed on {batch_data['total_tested']} strings. All matched: {batch_data['all_matched']}")
    assert batch_data["all_matched"] is True

    print("\nALL BACKEND API TESTS PASSED WITH 100% SUCCESS!")

if __name__ == "__main__":
    test_api()
