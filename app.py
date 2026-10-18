"""
Dead-State Pruner: DFA Optimization & State Pruning Engine
College TAE Project - Theory of Automata and Formal Languages

Backend: Python Flask
Features:
- Complete DFA Graph Parsing & Determinism Validation
- Forward BFS/DFS Reachability Analysis (Unreachable State Detection)
- Reverse Graph BFS/DFS Analysis from Accepting States (Dead/Trap State Detection)
- Safe State & Transition Elimination without altering language acceptance L(M) = L(M')
- Step-by-Step String Simulation Traversal
- Empirical Language Preservation Test Suite
"""

import os
import json
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Predefined Preset DFAs for Demonstrations & Viva
PRESETS = {
    "viva_demo": {
        "id": "viva_demo",
        "name": "College Viva Showcase (Unreachable + Trap State)",
        "description": "Contains an unreachable state (q5) and a classic dead/trap state (q4) with self-loops, plus productive paths.",
        "states": ["q0", "q1", "q2", "q3", "q4", "q5"],
        "alphabet": ["0", "1"],
        "initial_state": "q0",
        "final_states": ["q2"],
        "transitions": [
            {"from_state": "q0", "symbol": "0", "to_state": "q1"},
            {"from_state": "q0", "symbol": "1", "to_state": "q4"},
            {"from_state": "q1", "symbol": "0", "to_state": "q2"},
            {"from_state": "q1", "symbol": "1", "to_state": "q4"},
            {"from_state": "q2", "symbol": "0", "to_state": "q2"},
            {"from_state": "q2", "symbol": "1", "to_state": "q2"},
            {"from_state": "q3", "symbol": "0", "to_state": "q4"},
            {"from_state": "q3", "symbol": "1", "to_state": "q4"},
            {"from_state": "q4", "symbol": "0", "to_state": "q4"},
            {"from_state": "q4", "symbol": "1", "to_state": "q4"},
            {"from_state": "q5", "symbol": "0", "to_state": "q1"},
            {"from_state": "q5", "symbol": "1", "to_state": "q2"}
        ]
    },
    "spec_example": {
        "id": "spec_example",
        "name": "Specification Example DFA (Unreachable q4)",
        "description": "Standard prompt specification example where q4 is completely disconnected from initial state q0.",
        "states": ["q0", "q1", "q2", "q3", "q4"],
        "alphabet": ["0", "1"],
        "initial_state": "q0",
        "final_states": ["q3"],
        "transitions": [
            {"from_state": "q0", "symbol": "0", "to_state": "q1"},
            {"from_state": "q0", "symbol": "1", "to_state": "q2"},
            {"from_state": "q1", "symbol": "0", "to_state": "q1"},
            {"from_state": "q1", "symbol": "1", "to_state": "q3"},
            {"from_state": "q2", "symbol": "0", "to_state": "q2"},
            {"from_state": "q2", "symbol": "1", "to_state": "q3"},
            {"from_state": "q3", "symbol": "0", "to_state": "q3"},
            {"from_state": "q3", "symbol": "1", "to_state": "q3"},
            {"from_state": "q4", "symbol": "0", "to_state": "q4"},
            {"from_state": "q4", "symbol": "1", "to_state": "q4"}
        ]
    },
    "multiple_traps": {
        "id": "multiple_traps",
        "name": "Multiple Trap States & Chain",
        "description": "Demonstrates interconnected trap states q3 and q4 cycling indefinitely without reaching final state q2.",
        "states": ["q0", "q1", "q2", "q3", "q4"],
        "alphabet": ["0", "1"],
        "initial_state": "q0",
        "final_states": ["q2"],
        "transitions": [
            {"from_state": "q0", "symbol": "0", "to_state": "q1"},
            {"from_state": "q0", "symbol": "1", "to_state": "q3"},
            {"from_state": "q1", "symbol": "0", "to_state": "q2"},
            {"from_state": "q1", "symbol": "1", "to_state": "q4"},
            {"from_state": "q2", "symbol": "0", "to_state": "q2"},
            {"from_state": "q2", "symbol": "1", "to_state": "q2"},
            {"from_state": "q3", "symbol": "0", "to_state": "q4"},
            {"from_state": "q3", "symbol": "1", "to_state": "q3"},
            {"from_state": "q4", "symbol": "0", "to_state": "q3"},
            {"from_state": "q4", "symbol": "1", "to_state": "q4"}
        ]
    },
    "self_loop_safe": {
        "id": "self_loop_safe",
        "name": "Mathematical Safety Test (Productive Self-Loops)",
        "description": "Demonstrates that productive states with self-loops are preserved, proving the safety rule.",
        "states": ["q0", "q1", "q2", "q3"],
        "alphabet": ["a", "b"],
        "initial_state": "q0",
        "final_states": ["q2"],
        "transitions": [
            {"from_state": "q0", "symbol": "a", "to_state": "q0"},
            {"from_state": "q0", "symbol": "b", "to_state": "q1"},
            {"from_state": "q1", "symbol": "a", "to_state": "q1"},
            {"from_state": "q1", "symbol": "b", "to_state": "q2"},
            {"from_state": "q2", "symbol": "a", "to_state": "q2"},
            {"from_state": "q2", "symbol": "b", "to_state": "q2"},
            {"from_state": "q3", "symbol": "a", "to_state": "q3"},
            {"from_state": "q3", "symbol": "b", "to_state": "q3"}
        ]
    }
}


def validate_dfa(data):
    """
    Validates DFA inputs:
    - Non-empty states, alphabet, initial state, final states
    - Initial state in states
    - Final states subset of states
    - Determinism (at most one next state for each state + symbol)
    - Valid state and symbol references
    """
    errors = []
    warnings = []

    states = [s.strip() for s in data.get("states", []) if s.strip()]
    alphabet = [a.strip() for a in data.get("alphabet", []) if a.strip()]
    initial_state = str(data.get("initial_state", "")).strip()
    final_states = [f.strip() for f in data.get("final_states", []) if f.strip()]
    transitions = data.get("transitions", [])

    if not states:
        errors.append("Please define at least one state.")
    else:
        # Check uniqueness
        if len(states) != len(set(states)):
            errors.append("State names must be distinct.")

    if not alphabet:
        errors.append("Please define at least one alphabet symbol.")
    else:
        if len(alphabet) != len(set(alphabet)):
            errors.append("Alphabet symbols must be distinct.")

    if not initial_state:
        errors.append("Initial state is missing.")
    elif initial_state not in states:
        errors.append(f"Initial state '{initial_state}' does not belong to the DFA states.")

    if not final_states:
        errors.append("No accepting/final state has been selected. (L(M) would be empty).")
    else:
        invalid_final = [f for f in final_states if f not in states]
        if invalid_final:
            errors.append(f"Final state(s) {invalid_final} are not part of defined states.")

    # Validate Transitions
    seen_transitions = {}
    valid_transitions = []
    states_set = set(states)
    alphabet_set = set(alphabet)

    for idx, t in enumerate(transitions):
        u = str(t.get("from_state", "")).strip()
        sym = str(t.get("symbol", "")).strip()
        v = str(t.get("to_state", "")).strip()

        if not u or not sym or not v:
            errors.append(f"Row {idx + 1} has incomplete fields.")
            continue

        if u not in states_set:
            errors.append(f"Transition {idx + 1}: Source state '{u}' does not exist.")
        if v not in states_set:
            errors.append(f"Transition {idx + 1}: Destination state '{v}' does not exist.")
        if sym not in alphabet_set:
            errors.append(f"Transition {idx + 1}: Symbol '{sym}' is not part of alphabet {alphabet}.")

        pair = (u, sym)
        if pair in seen_transitions:
            errors.append(f"Non-deterministic or duplicate transition detected for state '{u}' on symbol '{sym}'.")
        else:
            seen_transitions[pair] = v
            valid_transitions.append({"from_state": u, "symbol": sym, "to_state": v})

    # Check for missing transitions
    total_expected = len(states) * len(alphabet)
    if len(seen_transitions) < total_expected:
        missing_count = total_expected - len(seen_transitions)
        warnings.append(
            f"The DFA is partially defined ({missing_count} transition(s) missing). Unspecified transitions act as implicit rejection sinks."
        )

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "states": sorted(list(set(states))),
        "alphabet": sorted(list(set(alphabet))),
        "initial_state": initial_state,
        "final_states": sorted(list(set(final_states))),
        "transitions": valid_transitions
    }


def analyze_dfa_structure(dfa):
    """
    Performs dual-direction graph traversal:
    1. Forward BFS from initial_state to find Reachable States
    2. Reverse Graph BFS from all final_states to find states that Can Reach Final States
    3. Categorizes states:
       - Reachable
       - Unreachable
       - Dead/Trap
       - Useful
       - States to Prune
    """
    states = dfa["states"]
    alphabet = dfa["alphabet"]
    initial_state = dfa["initial_state"]
    final_states = set(dfa["final_states"])
    transitions = dfa["transitions"]

    # Build adjacency maps
    forward_adj = {s: [] for s in states}
    reverse_adj = {s: [] for s in states}
    delta = {}

    for t in transitions:
        u = t["from_state"]
        sym = t["symbol"]
        v = t["to_state"]
        forward_adj[u].append((sym, v))
        reverse_adj[v].append((sym, u))
        delta[(u, sym)] = v

    # 1. Forward BFS from initial_state
    reachable = set()
    forward_trace = []
    if initial_state in states:
        queue = [initial_state]
        reachable.add(initial_state)
        forward_trace.append({"step": 1, "state": initial_state, "action": "Start at initial state"})

        while queue:
            curr = queue.pop(0)
            for sym, nxt in forward_adj[curr]:
                if nxt not in reachable:
                    reachable.add(nxt)
                    queue.append(nxt)
                    forward_trace.append({
                        "step": len(forward_trace) + 1,
                        "state": nxt,
                        "action": f"Discovered from '{curr}' on symbol '{sym}'"
                    })

    all_states_set = set(states)
    unreachable = all_states_set - reachable

    # 2. Reverse BFS from Final States
    can_reach_final = set()
    reverse_trace = []
    # Seed queue with all final states
    rev_queue = []
    for f in final_states:
        if f in states:
            can_reach_final.add(f)
            rev_queue.append(f)
            reverse_trace.append({
                "step": len(reverse_trace) + 1,
                "state": f,
                "action": "Seed from accepting final state"
            })

    while rev_queue:
        curr = rev_queue.pop(0)
        for sym, pred in reverse_adj[curr]:
            if pred not in can_reach_final:
                can_reach_final.add(pred)
                rev_queue.append(pred)
                reverse_trace.append({
                    "step": len(reverse_trace) + 1,
                    "state": pred,
                    "action": f"Can reach '{curr}' via transition on symbol '{sym}'"
                })

    # 3. Classifications
    # Useful states = Reachable AND can reach at least one final state
    useful = reachable.intersection(can_reach_final)

    # Dead/Trap states = Reachable states that CANNOT reach ANY final state
    dead = reachable - can_reach_final

    # Unreachable states that also cannot reach final
    unreachable_dead = unreachable - can_reach_final

    # Unreachable states that COULD reach final if entered (still invalid because unreachable from start)
    unreachable_with_final_path = unreachable.intersection(can_reach_final)

    # Total States to Prune = Unreachable UNION Dead
    states_to_prune = unreachable.union(dead)

    # Detailed justification for each state
    state_verdicts = {}
    for s in states:
        is_init = (s == initial_state)
        is_fin = (s in final_states)
        is_reach = (s in reachable)
        can_fin = (s in can_reach_final)

        if not is_reach:
            category = "unreachable"
            reason = f"State '{s}' cannot be reached by any sequence of symbols starting from '{initial_state}'."
        elif not can_fin:
            category = "dead"
            reason = f"State '{s}' is reachable from '{initial_state}', but no directed path exists from '{s}' to any accepting state. It is a dead/trap state."
        else:
            category = "useful"
            reason = f"State '{s}' is reachable from '{initial_state}' and has a valid path leading to an accepting state."

        state_verdicts[s] = {
            "state": s,
            "is_initial": is_init,
            "is_final": is_fin,
            "is_reachable": is_reach,
            "can_reach_final": can_fin,
            "category": category,
            "reason": reason,
            "should_prune": s in states_to_prune
        }

    return {
        "total_states_count": len(states),
        "reachable_states": sorted(list(reachable)),
        "unreachable_states": sorted(list(unreachable)),
        "dead_states": sorted(list(dead)),
        "useful_states": sorted(list(useful)),
        "states_to_prune": sorted(list(states_to_prune)),
        "final_states": sorted(list(final_states)),
        "initial_state": initial_state,
        "state_verdicts": state_verdicts,
        "forward_trace": forward_trace,
        "reverse_trace": reverse_trace
    }


def prune_dfa_model(dfa, analysis):
    """
    Creates the optimized DFA by removing:
    1. Unreachable states
    2. Dead/Trap states
    3. Any transitions originating from or leading to pruned states
    """
    states_to_prune = set(analysis["states_to_prune"])
    useful_states = set(analysis["useful_states"])

    # If the entire language is empty (no useful states)
    if not useful_states:
        # Minimal empty automaton
        new_states = [dfa["initial_state"]] if dfa["initial_state"] in dfa["states"] else ["q0"]
        new_final = []
        new_transitions = []
    else:
        new_states = sorted(list(useful_states))
        new_final = [f for f in dfa["final_states"] if f in useful_states]
        new_transitions = [
            t for t in dfa["transitions"]
            if t["from_state"] in useful_states and t["to_state"] in useful_states
        ]

    # Initial state retention: if original initial state was useful, keep it.
    new_initial = dfa["initial_state"] if dfa["initial_state"] in useful_states else (new_states[0] if new_states else "")

    optimized_dfa = {
        "states": new_states,
        "alphabet": dfa["alphabet"],
        "initial_state": new_initial,
        "final_states": new_final,
        "transitions": new_transitions
    }

    reduction = {
        "original_states_count": len(dfa["states"]),
        "optimized_states_count": len(new_states),
        "states_removed": len(dfa["states"]) - len(new_states),
        "state_reduction_percent": round(((len(dfa["states"]) - len(new_states)) / len(dfa["states"])) * 100, 1) if dfa["states"] else 0,
        "original_transitions_count": len(dfa["transitions"]),
        "optimized_transitions_count": len(new_transitions),
        "transitions_removed": len(dfa["transitions"]) - len(new_transitions),
        "transition_reduction_percent": round(((len(dfa["transitions"]) - len(new_transitions)) / len(dfa["transitions"])) * 100, 1) if dfa["transitions"] else 0,
    }

    return optimized_dfa, reduction


def simulate_string(dfa, input_string):
    """
    Simulates string execution on a given DFA.
    Returns step-by-step path trace and acceptance verdict.
    """
    states = set(dfa.get("states", []))
    alphabet = set(dfa.get("alphabet", []))
    initial_state = dfa.get("initial_state", "")
    final_states = set(dfa.get("final_states", []))
    transitions = dfa.get("transitions", [])

    delta = {}
    for t in transitions:
        delta[(t["from_state"], t["symbol"])] = t["to_state"]

    if not initial_state or initial_state not in states:
        return {
            "accepted": False,
            "error": "Initial state is missing or not in DFA states.",
            "trace": [],
            "final_state": None
        }

    # Handle epsilon (empty string)
    clean_string = input_string.strip()
    if clean_string in ["ε", "eps", "epsilon", ""]:
        symbols = []
    else:
        symbols = list(clean_string)

    # Check alphabet symbols
    for s in symbols:
        if s not in alphabet:
            return {
                "accepted": False,
                "error": f"Symbol '{s}' is not part of the DFA alphabet {list(alphabet)}.",
                "trace": [],
                "final_state": None
            }

    curr_state = initial_state
    trace = [{"step": 0, "symbol": "ε (Start)", "from_state": "", "to_state": curr_state, "is_final": curr_state in final_states}]

    halted_early = False
    halt_reason = ""

    for idx, sym in enumerate(symbols):
        prev = curr_state
        if (curr_state, sym) in delta:
            curr_state = delta[(curr_state, sym)]
            trace.append({
                "step": idx + 1,
                "symbol": sym,
                "from_state": prev,
                "to_state": curr_state,
                "is_final": curr_state in final_states
            })
        else:
            # Undefined transition in partial/pruned DFA
            halted_early = True
            halt_reason = f"No transition defined from '{curr_state}' on symbol '{sym}' (Trap was pruned)."
            trace.append({
                "step": idx + 1,
                "symbol": sym,
                "from_state": prev,
                "to_state": "∅ (Trap Pruned)",
                "is_final": False,
                "halted": True
            })
            break

    accepted = (not halted_early) and (curr_state in final_states)

    return {
        "accepted": accepted,
        "halted_early": halted_early,
        "halt_reason": halt_reason,
        "final_state": curr_state if not halted_early else "∅",
        "is_final": accepted,
        "trace": trace
    }


def generate_batch_tests(alphabet, max_length=3):
    """Generates standard binary/alphabet strings for empirical testing."""
    tests = ["ε"]
    current_level = [""]

    for _ in range(max_length):
        next_level = []
        for prefix in current_level:
            for char in alphabet:
                word = prefix + char
                tests.append(word)
                next_level.append(word)
        current_level = next_level

    # Keep unique ordered
    seen = set()
    result = []
    for t in tests:
        if t not in seen:
            seen.add(t)
            result.append(t)
    return result


# --- ROUTES ---

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/presets", methods=["GET"])
def get_presets():
    return jsonify({"success": True, "presets": PRESETS})


@app.route("/api/analyze", methods=["POST"])
def analyze_endpoint():
    try:
        raw_data = request.get_json(force=True)
        validation = validate_dfa(raw_data)
        if not validation["is_valid"]:
            return jsonify({
                "success": False,
                "errors": validation["errors"],
                "warnings": validation["warnings"]
            }), 400

        analysis = analyze_dfa_structure(validation)
        return jsonify({
            "success": True,
            "dfa": validation,
            "analysis": analysis,
            "warnings": validation["warnings"]
        })
    except Exception as e:
        return jsonify({"success": False, "errors": [str(e)]}), 500


@app.route("/api/prune", methods=["POST"])
def prune_endpoint():
    try:
        raw_data = request.get_json(force=True)
        validation = validate_dfa(raw_data)
        if not validation["is_valid"]:
            return jsonify({"success": False, "errors": validation["errors"]}), 400

        analysis = analyze_dfa_structure(validation)
        optimized_dfa, reduction = prune_dfa_model(validation, analysis)

        return jsonify({
            "success": True,
            "original_dfa": validation,
            "analysis": analysis,
            "optimized_dfa": optimized_dfa,
            "reduction": reduction
        })
    except Exception as e:
        return jsonify({"success": False, "errors": [str(e)]}), 500


@app.route("/api/simulate", methods=["POST"])
def simulate_endpoint():
    try:
        data = request.get_json(force=True)
        original_dfa = data.get("original_dfa")
        optimized_dfa = data.get("optimized_dfa")
        test_string = data.get("test_string", "")

        orig_result = simulate_string(original_dfa, test_string)
        opt_result = simulate_string(optimized_dfa, test_string)

        match = (orig_result.get("accepted") == opt_result.get("accepted"))

        return jsonify({
            "success": True,
            "test_string": test_string,
            "original_result": orig_result,
            "optimized_result": opt_result,
            "match": match,
            "verdict_text": "Language acceptance preserved ✓" if match else "Verdict mismatch ⚠"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/batch-test", methods=["POST"])
def batch_test_endpoint():
    try:
        data = request.get_json(force=True)
        original_dfa = data.get("original_dfa")
        optimized_dfa = data.get("optimized_dfa")
        custom_strings = data.get("custom_strings", [])

        alphabet = original_dfa.get("alphabet", ["0", "1"])
        standard_strings = generate_batch_tests(alphabet, max_length=3)

        combined_strings = []
        for s in standard_strings + custom_strings:
            s_clean = s.strip()
            if s_clean not in combined_strings:
                combined_strings.append(s_clean)

        test_results = []
        all_matched = True

        for string_val in combined_strings:
            orig = simulate_string(original_dfa, string_val)
            opt = simulate_string(optimized_dfa, string_val)
            matched = (orig.get("accepted") == opt.get("accepted"))
            if not matched:
                all_matched = False

            test_results.append({
                "string": string_val,
                "original_accepted": orig.get("accepted"),
                "optimized_accepted": opt.get("accepted"),
                "matched": matched,
                "orig_trace_summary": " → ".join([step["to_state"] for step in orig.get("trace", []) if step.get("to_state")]),
                "opt_trace_summary": " → ".join([step["to_state"] for step in opt.get("trace", []) if step.get("to_state")])
            })

        return jsonify({
            "success": True,
            "total_tested": len(test_results),
            "all_matched": all_matched,
            "results": test_results
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Dead-State Pruner on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
