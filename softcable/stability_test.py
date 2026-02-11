import os
import time

def run_single_test(path, size_mb=20):
    """Runs one write/read test and returns speeds or error."""
    result = {"write": None, "read": None, "error": None}

    try:
        data = os.urandom(size_mb * 1024 * 1024)
        temp_file = os.path.join(path, "softcable_stability.bin")

        # WRITE
        start = time.time()
        with open(temp_file, "wb") as f:
            f.write(data)
        end = time.time()
        result["write"] = round(size_mb / (end - start), 2)

        # READ
        start = time.time()
        with open(temp_file, "rb") as f:
            f.read()
        end = time.time()
        result["read"] = round(size_mb / (end - start), 2)

        os.remove(temp_file)

    except Exception as e:
        result["error"] = str(e)

    return result


def run_stability_test(path, runs=10):
    """Runs multiple tests and computes stability score."""
    results = []
    write_speeds = []
    read_speeds = []

    for i in range(runs):
        test = run_single_test(path)

        if test["error"]:
            return {"error": test["error"]}

        results.append(test)
        write_speeds.append(test["write"])
        read_speeds.append(test["read"])

    # Compute variance
    write_var = max(write_speeds) - min(write_speeds)
    read_var = max(read_speeds) - min(read_speeds)

    # Stability score (lower variance = more stable)
    score = 100 - ((write_var + read_var) * 2)
    score = max(0, min(100, round(score, 2)))

    return {
        "error": None,
        "runs": results,
        "write_var": round(write_var, 2),
        "read_var": round(read_var, 2),
        "score": score
    }
